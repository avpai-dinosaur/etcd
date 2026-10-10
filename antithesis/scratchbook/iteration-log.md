# How the etcd coverage harness and workload were built

A running, human-readable account of what was tried, what broke, and what was
changed, in the order it happened. Short-form records live elsewhere:
`coverage-setup.md` (setup facts) and `workload-ledger.md` (one row per
measured workload change). This file is the story behind them.

## 0. Starting point and prerequisites

- The repo had only `antithesis/scratchbook/api-surface.md` (60 operations,
  Tier 0 = put/range/delete_range).
- `antithesis-coverage-setup` requires a base harness from `antithesis-setup`
  (`antithesis/config/docker-compose.yaml` reaching `setup_complete`), and
  `antithesis-setup` in turn requires research output (`sut-analysis.md`,
  `deployment-topology.md`). Neither existed.
- Decision (asked the user): write a *light* version of the two research files
  from the code and `api-surface.md`, skip the property catalog, then run
  setup → coverage-setup → coverage-workload.
- Before any of that, a tooling issue: the two coverage skills were invisible
  to Claude Code because their symlinks in `~/.claude/skills/` pointed at
  themselves (`antithesis-coverage-setup -> antithesis-coverage-setup/`).
  Repointed them at `~/skills-dev/...` and reloaded skills.

Environment: 2 vCPU, 7 GB RAM, Docker 29.1 + Compose 2.40, Go 1.27.2 on the
host, snouty 0.7.2 (`snouty doctor` all green).

## 1. Base harness (antithesis-setup)

### Reusing what etcd already has

etcd ships an Antithesis harness in `tests/antithesis/`. Things learned from it:

- Its server image **clones etcd from GitHub** (`git clone --branch=$REF`), so
  it never builds the local working tree. Not usable as-is for iterating on
  this checkout; the new image builds from the local repo instead.
- It uses the legacy source-rewriting `antithesis-go-instrumentor` with a lot
  of `go.mod` fix-ups (go/toolchain directives lost by the notifier module,
  `dummy.go` package clash). The current Antithesis docs describe a newer
  `-toolexec` instrumentor (`antithesis-go-toolexec`, SDK v0.8.0) that wraps
  `go build` directly, so none of those fix-ups should be needed.
- It turns all `// gofail` comments into `assert.Reachable` and the `verify`
  package into `assert.Always`. Those are properties, so they're **not** carried
  over: the coverage workflow keeps properties out of the SUT and the workload.
  Only one bootstrap `Reachable` is added (required by `antithesis-setup`).
- The cluster settings (`SNAPSHOT_COUNT=50`, `SNAPSHOT_CATCHUP_ENTRIES=100`,
  `COMPACTION_BATCH_LIMIT=10`) are kept: they make snapshot and compaction
  paths common.

### Image and compose decisions

- **One Dockerfile, two targets** (`antithesis/Dockerfile`): `etcd` and
  `workload`, build context = repo root. The etcd stage uses
  `COPY --exclude=antithesis . .` so editing drivers never invalidates the
  (slow, ~1.5 min on 2 vCPU) etcd compile. A per-Dockerfile ignore file
  (`Dockerfile.dockerignore`) keeps `.git` and run output out of the context
  without touching etcd's own files.
- **Instrumentation**: `go build -toolexec=antithesis-go-toolexec` with
  `CGO_ENABLED=1` (upstream builds with `CGO_ENABLED=0`). It printed
  `collected 85 symbol tables into /symbols`. The go *build* cache is
  deliberately not mounted for this step: a cached package skips toolexec and
  its symbol table would silently go missing.
- **Bootstrap property**: `assert.Reachable("etcd server process started")` in
  an `init()` of package `etcdmain`, in a file the Dockerfile copies in at build
  time (`antithesis/etcd/antithesis_bootstrap.go`). No etcd source file is
  edited; the SDK (`v0.8.0`) is added with `go get` inside the build only.
- **Python client**: no official Python etcd client exists, and the HTTP
  gateway has no `RangeStream`. So the workload image generates gRPC stubs
  from the repo's own `.proto` files at build time. grpcio-tools doesn't ship
  `google/api/annotations.proto` or the OpenAPI annotations, so
  `antithesis/workload/genproto.py` strips those imports and option blocks
  first. Worked first try.
- **setup_complete** comes from the workload entrypoint (Python SDK
  `lifecycle.setup_complete`) once a linearizable `Range` succeeds on all
  three members.

### Setup issues hit

1. **Three services, one image tag → build race.** `docker compose build`
   failed with `image "docker.io/library/etcd-server:latest": already exists`
   because etcd0/1/2 all had the same `build:`. Fix: only `etcd0` has `build:`;
   etcd1/2 just reference `image:`. Compose doesn't try to pull an image that
   another service in the project builds.
2. **Go coverage is lost on SIGTERM.** etcd catches SIGTERM, runs its shutdown
   handlers, then re-raises the signal and dies by it, which skips Go's
   coverage flush. The skill's suggested fix for Go is a signal-handler patch
   (needs the user's OK). Reading `pkg/osutil/interrupt_unix.go` showed a way
   out: when etcd is **PID 1** it calls `os.Exit(0)` instead, which does flush.
   `log-tee.sh` ends in `exec "$@"`, so with `init: false` in the coverage
   override etcd becomes PID 1. Verified: `docker compose stop etcd0` → exit 0,
   `covmeta.*` + `covcounters.*` written. No SUT change needed. (The
   Antithesis build keeps `init: true`.)
3. **Coverage paths didn't match the repo.** Go profiles name files by import
   path (`go.etcd.io/etcd/server/v3/etcdserver/server.go`); the `/v3/` segment
   means no suffix of that path is a repo path (`server/etcdserver/server.go`),
   and `--strip-prefix` can only delete, not rewrite. `extract_coverage()` now
   rewrites module paths with `sed` before normalizing. Smoke run: 350 files,
   8,096 lines.
4. **GOCOVERDIR must exist.** The coverage override's command is
   `mkdir -p "$GOCOVERDIR" && exec etcd` (still an exec chain, so etcd stays
   PID 1).
5. Small: `run-local.sh` hard-coded `DURATION`/`CONCURRENCY`; made them
   overridable from the environment so short check runs don't need edits.
   The `antithesis/local/out/` ignore rule went into `antithesis/local/.gitignore`
   rather than etcd's root `.gitignore`.

Validation: `snouty validate antithesis/config` → "Setup-complete event
detected … Setup validation successful."

## 2. Workload (antithesis-coverage-workload)

### Initial Tier 0 drivers

Value menus built from the inputs tables in `api-surface.md`:

- Key pool: 16 keys `key00..key15`; `key0`/`key1` are prefixes of 10 and 6
  of them, so `--prefix` style ranges cover several keys. Plus the empty key
  now and then (`ErrGRPCEmptyKey`).
- Values: empty, 1 B … 64 KiB, 1 MiB, just inside and just outside
  `--max-request-bytes` (1.5 MiB). Big ones appear once among ~15 entries so
  disk use stays bounded.
- `range_end` forms: single key, from-key (`\x00`), prefix, whole pool, all
  keys, and an empty interval.
- `kv.range`: limit, revision (current/negative/historical/far future),
  sort order (incl. invalid value 3) and target, serializable, keys/count-only,
  min/max mod/create revision filters.
- `kv.put`: plain, `prev_kv`, `ignore_value` (+ empty value), `ignore_lease`,
  both, and two invalid combinations (`ignore_value` with a value; an unknown
  lease).

First check run (60 s, seed 1): every operation logged `ok`, and the server's
error paths for each invalid input showed up (`invalid_sort_option`,
`value_is_provided`, `requested_lease_not_found`, `request_is_too_large`,
`key_is_not_provided`, `future_revision`). Two things noted for later:

- `delete_range` had 3 non-zero exits with no traceback: they are drivers that
  `local_composer.py` SIGTERMs when the time is up (it counts -15 as a
  failure). A runner artifact, not a driver bug.
- ok rates around 50% for put and range. Puts fail mostly with `key not found`
  (`ignore_*` flags on a pool that range-deletes keep emptying); ranges fail on
  revisions 1000/10000 that are still in the future (the cluster is only at
  ~540). Left for measured iterations rather than fixed blind.

### Fixes found while taking the baseline

Three problems turned up in the measuring itself, before any workload change:

1. **`by-op` showed 0/3 functions for every operation.** Go coverage profiles
   have line ranges but no function names, so the report could only count
   "lines in the operation's files". That hides the most useful hint (which
   functions were never reached). Added `antithesis/local/gocov2lcov.py`: it
   reads each source file's top-level `func` lines and writes LCOV with
   `FN`/`FNDA` records named `Type.Method`. After that, the baseline showed
   1,115 functions reached, Tier 0 at 3/3, and a concrete "never reached" list
   for every other operation. `extract_coverage()` now writes
   `coverage.lcov`; normalize with `--format lcov`.
2. **Outcome lines were getting glued together** (`OP kv.put okOP kv.range ok`).
   With `PYTHONUNBUFFERED=1`, `print()` writes the text and the newline as two
   separate syscalls, so lines from parallel drivers interleave. About 1% of
   outcomes were lost from the counts. `log_outcome()` now does one
   `sys.stdout.write()` per line.
3. **Raft and bbolt weren't instrumented for Antithesis** (found by the
   fresh-context self-review). The toolexec instrumentor only instruments code
   in the working tree by default; raft and bbolt are downloaded modules. Set
   `ANTITHESIS_INSTRUMENT=go.etcd.io`: 85 → 93 symbol tables, including raft,
   `raft/confchange`, `raft/quorum`, and bbolt. Done *before* the first
   Antithesis run so all Antithesis numbers are comparable.

### Baseline (iter00)

Local, 3 seeds × 120 s: **8,634 lines, 1,115 functions**. All three Tier 0
operations reached every function in their code locations. ok rates:
`delete_range` 94%, `put` 52%, `range` 49%.

Antithesis baseline launched: `d827d5ee6e2901533b10185125d27a84-64-0`
(30 min).

Reading the unreached lines in Tier 0's own files (not just functions) showed
where Tier 0 alone could still grow:

- `mvcc.sliceCapWithLimit` never returned `limit`. That happens only when a
  range has *more* results than its limit, and the menu does have limits
  1/2/5. So the pool is almost always nearly empty: range-deletes (from-key,
  prefix, whole pool, all keys) run as often as puts. The same thing explains
  the `key not found` failures on puts with `ignore_*`.
- `checkRangeRequest`'s invalid *sort target* branch: the menu only had valid
  targets.
- `checkPutRequest`'s `ignore_lease` + non-zero lease branch
  (`ErrGRPCLeaseProvided`): no menu entry combined them.
- ~29% of ranges failed with "future revision". The absolute revision menu
  (1000, 10000, 2^62) is ahead of a local cluster that only reaches about
  revision 2,000 in two minutes.
- Lease attach/detach in `storeTxnWrite.put`/`delete` needs real leases
  (Tier 2), and the compaction branches need `kv.compact` (Tier 1). Not
  Tier 0's job.

### Iterations 1–3: Tier 0 menus

| # | Change | Local Δ lines / functions | What it bought |
|---|---|---|---|
| 1 | `delete_range` does 1–5 calls per run instead of 1–20 | +42 / +1 | The targeted `return limit` in `sliceCapWithLimit`. Most of the rest was rafthttp timing noise; also one proposal timeout (`v3_server.go:1128`). |
| 2 | Add invalid sort target (5) and `ignore_lease` + lease to the menus | +14 / 0 | Both targeted validation branches (`ErrGRPCInvalidSortOption` for the target, `ErrGRPCLeaseProvided`). But range ok dropped to 44%: ~30% of ranges now stopped at validation. |
| 3 | Make invalid values rare (≈1 in 10 per field), weight revision 0 | +5 / +1 | No new branches, but ok rates back up (put 59%, range 56%), so most calls reach the storage layer again. |

Lessons from these three:

- **Noise is real at this scale.** Between seeds, ±10–50 lines move in
  `rafthttp`, `raft.go` and `server.go` (probing, timeouts, leader ticks) with
  no workload change. Only lines in the operation's own files (`v3rpc/key.go`,
  `txn/*.go`, `mvcc/*.go`) were treated as signal.
- **Every invalid value costs a share of successful calls.** A menu where each
  of several fields has a 1-in-6 invalid value multiplies out to a third of
  calls dying at validation. One rare invalid value per field still reaches
  the error branch (it only needs to happen once) without starving the main
  path.
- **The pool was the real Tier 0 limit**, not the menus: a range only takes
  the `limit` branch when there are more keys than the limit, and `ignore_*`
  puts need existing keys. Fewer deletes helped, but range-deletes still clear
  the pool often (put `key not found` stayed at ~11%). Tier 1's `kv.txn` adds
  more puts and should change that balance anyway.

### First Antithesis run (baseline)

`d827d5ee6e2901533b10185125d27a84-64-0`, 30 min, Tier 0 drivers as of iter00.

Health (antithesis-triage): all 34 properties pass. `Software was
instrumented` lists 93 modules (= the 93 symbol tables, so raft and bbolt
made it in), `Thread pausing was enabled` on etcd0/1/2, `Symbols were
uploaded`, and the bootstrap `etcd server process started` was hit. Each
driver ran 11–13k times with no failing command.

**Snag: no coverage export.** The coverage-workload skill expects
`snouty --json runs show <run>` to contain `.results.coverage`. With snouty
0.7.2 (latest) on this tenant it only has `results.environment`. The docs
describe no other export, and the triage report page loads its data through
internal asset URLs, which I didn't scrape. So the Antithesis side of the
measurement (edges, new functions vs. local) **can't be done**. What remains:

- health from triage properties, and
- outcome lines via `snouty runs events <run> "<text>"`. That is capped at
  1,000 matches, and multi-term search needs an unstable flag, so it gives a
  sample and presence/absence, not totals. (The `antithesis-query-logs` skill
  needs an interactive browser login, so it wasn't used.)

What the outcome lines showed is still useful. Antithesis reaches behavior
local runs never do: `UNAVAILABLE: etcdserver: leader changed` on reads,
connection failures during partitions/pauses, `DEADLINE_EXCEEDED`,
`RST_STREAM` cancellations, and server-side `apply request took too long`
(`txn/util.go:93`, i.e. `warnOfExpensiveGenericRequest`, never reached
locally). No `database space exceeded` in 30 min, so the disk-fill worry
from the self-review didn't materialize at this length.

Because Antithesis edges can't be compared, the "move to the next tier" rule
(local growth levelled **and** the latest Antithesis run added little) can
only use its local half. Tier 0 levelled locally at iterations 1–3
(+42/+14/+5), so Tier 1 is next. A second 30-min Antithesis run with the
iter03 drivers (`5eace8bd2d445e0eec6b01e44e6a4a44-64-0`) was launched anyway,
to compare health and outcome mix.

### Iteration 5: Tier 1 (`kv.txn`, `kv.range_stream`, `kv.compact`)

All three entries in `api-surface.md` have **Requires: —** and **Enabled by: —**,
so no harness change was needed. They were drafted while Tier 0 was still
being measured, but kept out of `antithesis/test/` until then, because
`run-local.sh` rebuilds the workload image on every run, and an Antithesis
launch pushes whatever `etcd-workload:latest` holds at that moment.

Driver notes:

- `kv.txn`: compares on all five targets (VERSION/CREATE/MOD/VALUE/LEASE)
  with all four results, single-key or range compares; success/failure lists
  of 0–3 range/put/delete ops, sometimes a nested txn; 1 in 20 txns is over
  `--max-txn-ops` (128 cheap range ops, top level only, so requests don't
  balloon).
- `kv.range_stream`: same menus as `kv.range`, but sort order and revision
  filters are default 9 in 10 times (anything else is `Unimplemented`). Every
  chunk is read.
- `kv.compact`: reads the current revision from a response header **only to
  choose an argument** (not a check), then compacts at 1, rev/2, rev−100,
  rev−10, rev−1, rev or rev+1000, physical or not.

The first check run showed `kv.txn` ok only 23%: the empty `RequestOp` was 1
in 6 per op, and *any* empty op rejects the whole txn. Made it 1 in 14 before
measuring (ok → 51%).

Result: **+1,448 lines, +130 functions** (10,076 / 1,244 total). By far the
biggest step so far: txn compare/apply (`txn/txn.go`), the duplicate-key
interval tree (`pkg/adt`), RangeStream chunk adaptation (`adjustChunkLimit`),
compaction scheduling and the compaction KV hasher (`mvcc/hash.go`), and
expensive-request logging (`v3rpc/interceptor.go`). All Tier 0 and Tier 1
code locations: 3/3. Compaction also changed the Tier 0 picture: plain ranges
now get `required revision has been compacted` (~9%).

Also fixed: outcome strings included byte counts
(`RESOURCE_EXHAUSTED … (3144773 vs. 2097152)`), so every oversized txn was a
different outcome. `error_name()` now replaces digits with `N`.

Antithesis run 3 (`968fcfe06c5e1e8b3d0cc0f3bec78f0b-64-0`, 30 min) was
launched right after adding the tier, as the skill says.

### Iteration 6, and the noise floor

Change: the `kv.txn` compare menu got rare invalid values (empty key, result
4, target 5). All three targeted branches were hit, but the merged diff was
**+17 / −92 lines**. Lost: `Compare.String` and `loggableValueCompare.String`,
which only run when a txn is slow enough (>100 ms) to be logged as an
expensive request, plus some interval-tree branches.

Before blaming the change, I compared single seeds *within* an iteration
(same drivers, different seeds):

| Pair | Lines only in A / only in B | Functions |
|---|---|---|
| iter04 s1 vs s2 | 91 / 20 | 10 / 1 |
| iter04 s1 vs s3 | 77 / 40 | 6 / 1 |
| iter06 s1 vs s3 | 62 / 151 | 4 / 11 |
| iter06 s2 vs s3 | 72 / 89 | 6 / 8 |

So with Tier 1 active, ±100 lines and ±10 functions is noise, even after
merging 3 seeds (the slow-request logging alone depends on how loaded the
2-vCPU VM was). From here on, a change is judged by whether its **targeted
lines** were reached (that is deterministic: either the branch ran or it
didn't) and by losses *in the operation's own files*, not by the merged net
total. Kept.

### Input review (antithesis-review-inputs, after iteration 6)

The skill asks for an `antithesis-review-inputs` pass every 3–4 iterations.
It was run by a fresh-context agent (read-only) while iteration 6 was
measuring. Main findings, in its order:

1. **Every process has the same shape.** All drivers draw from the same
   uniform menus, so every timeline looks alike: ≤16 keys, mixed value sizes,
   short history. Since Test Composer owns the *mix* of drivers, the only
   lever left per run is a policy drawn once per process.
2. **Txn inner ops used only plain fields** (key/range_end, key/value/prev_kv),
   so inner-op checks were never reached: `checkRange`'s future/compacted
   branches (`txn/range.go:176-183`), `checkTxn`'s error exit
   (`txn/txn.go:55-57`), `checkPut`'s lease-not-found (`txn/put.go:73-74`),
   and read-only txns that are serializable *and* read something.
3. **Absolute revisions against a moving window.** ~43% of ranges/streams
   stopped at the mvcc revision checks. No menu entry reliably lands *inside*
   retained history, and what 1000/10000 mean depends on run length.
4. **The 16-key pool is too small for some structures.** The index btree
   (degree 32) never splits, RangeStream (first chunk 10 keys) never has more
   than 2 chunks, and `adjustChunkLimit`'s halving branch is never reached.
5. Others: value sizes drawn independently (3+ big values rarely land in one
   chunk); compaction keeps history short; nesting is shallow; streams are
   always read to the end (server-side `Send` failure and mid-range
   cancellation unreached).

It also noted what works: every input-table field is used, edges just past
the limits are present and kept rare, all randomness is `antithesis.random`,
and the shared pool's prefix structure makes drivers contend.

These became the candidates for the next iterations (growing-workload step 2,
"deepen"), in the order the review ranked them.

### Iterations 7–8: txn inner ops (review finding #2), and an undo

- **7, kept.** `PUT_OPTIONS` moved from the put driver into helper_common, with
  `put_fields()` and `range_fields()` helpers. The txn driver builds its inner
  puts and ranges from them, so inner ops carry the same flags, leases and
  revisions as standalone calls. All the review's targets were reached:
  `checkTxn`'s error exit, `checkRange`'s future/compacted branches,
  `checkPut`'s lease-not-found, and nested interval errors. The price: txn
  ok fell 51% → 28%, because one bad inner op rejects the whole txn.
- **8, undone.** Tried to win the ok rate back by using the full menus for
  only 1 in 3 inner ops. Result: ok 35%, nothing new, and one of iteration
  7's targeted lines (`txn/range.go:183`, a *valid* historical revision
  inside a txn) was no longer reached, because it had become rarer. The change
  also added a `full` flag to two helpers. By the skill's rule (nothing new +
  more complex → undo), reverted.

  The lesson is in the numbers: for a compound operation, "mostly ok" and
  "reaches the inner checks" pull against each other. The low ok rate *is*
  the inner checks being exercised. Txn still succeeds ~400 times per local
  measurement, which is plenty to move state.

### Iteration 9: per-process key-pool width (review finding #4), undone

Each process drew one pool width at import time (1 / 4 / 16 / 16+1,024
nested keys). Goal: index btree splits and RangeStream with 3+ chunks.
Result: +9 / −67 lines, and neither target moved:

- the index btree is `github.com/google/btree`, an **external module**, so it
  isn't in local coverage and isn't instrumented for Antithesis either
  (`ANTITHESIS_INSTRUMENT=go.etcd.io`);
- RangeStream's halving branch needs chunks over ~3 MiB, i.e. big *values*
  next to each other, not more keys.

Undone. A reviewer's hint is only as good as the coverage that can confirm
it. Here one target was outside measured code and the other needed a
different input.

### Antithesis run 2 (Tier 0 after the menu iterations)

`5eace8bd2d445e0eec6b01e44e6a4a44-64-0`, 30 min. Healthy, every property
passing. Compared with the baseline, every outcome I searched for was present
in both runs at the 1,000-match cap. With no coverage export the two runs
can't be ranked, so this run could only confirm health, not "Tier 0 has
levelled in Antithesis".

### Iteration 10: Tier 2 `lease` group

Checked `api-surface.md` first: `lease.revoke`, `lease.keepalive` and
`lease.timetolive` **require** `lease.grant`, and nothing in the group has
an **Enabled by** setting, so all five could be added together with no
harness change.

Design: a shared pool of 8 lease IDs (`LeaseGrantRequest` takes an explicit
ID). Grants, revokes, keep-alives, time-to-live lookups, and `kv.put`/
`kv.txn` puts with `lease=` all pick from it, so they collide without
coordinating: `lease already exists`, `requested lease not found`, keys
deleted when their lease is revoked or expires. TTLs include 0/1 (raised to
the 2 s minimum), a few short ones that expire mid-run, `MaxLeaseTTL`, and
one past it.

Result: **+954 lines, +102 functions** (10,894 / 1,341 total). All five lease
operations reached all their code locations. The lease group also reached
the biggest Tier 0 gap left from iteration 3: the lease attach/detach inside
`storeTxnWrite.put` and `delete` (`kvstore_txn.go:269-290`, `338-339`). The
leader's background expiry (`revokeExpiredLeases`) and follower→leader
forwarding (`leasehttp`) run too. Lost: `WAL.cut`. Lease drivers now take
~45% of the driver slots, so fewer large puts are written and the WAL doesn't
fill a 64 MB segment in 120 s. Still unreached: `lessor.Checkpoint`, which
needs the `LeaseCheckpoint` feature gate (an "Enabled by" harness change, not
done), and `Recover` (restarts; Antithesis's job).

Antithesis run 4 launched right after: `fb7e3f1fd12a5c417bfed2ecddf840dc-64-0`.

### Antithesis run 3 (Tier 0 + Tier 1): an etcd crash

`968fcfe06c5e1e8b3d0cc0f3bec78f0b-64-0`. One built-in property failed:
**`container: etcd2, exit code: 1`**. The log shows etcd2 hitting
`lg.Fatal` at `mvcc/kvstore_txn.go:128`, "range failed to find revision
pair", **while applying a committed txn**, 1.6 s after all three members
compacted at revision 50 (the current revision) with identical hashes. The
index held revision {50, 8} for a key under the `key0` prefix; the backend
had no value for it. Only etcd2 crashed. No faults were active (network
restored at 83 s). One timeline only, and none in the Tier 0-only runs.

The workload has no properties, so nothing in it "caught" this: the
built-in container-exit check did. It's written up with the moment,
timeline and hypotheses in `findings/txn-from-key-delete-crash.md` and
was not encoded in the workload (per the skill's rules). The ingredients all
came from Tier 1 drivers: compaction at the current revision, multi-key
deletes/txns at one revision, txns with inner prefix ranges.

### Wrap-up and self-review

A fresh-context agent checked the drivers against the coverage-workload
skill's self-review list: **no failures**. No assertions or `eventually_`/
`finally_`/`anytime_` commands. All drivers under 50 lines (14–48). All
randomness from `antithesis.random`. One `OP` line per call. Every system
error is caught. Only active tiers/groups have drivers, and every
**Requires** (`lease.grant`) is active. It judged the compact driver's
header-revision read to be input derivation, not a check. Follow-ups it found
and that were fixed: the compact driver's revision read was logged as
`kv.range` (now `kv.compact read_rev_error=…`), ledger rows for every
Antithesis run, and a snapshot↔row map. I also confirmed that no driver ever
crashed: the run logs include stderr and contain no tracebacks, so the
handful of non-zero exits per run are `local_composer.py` stopping drivers
that were still running at the end.

Final `snouty validate antithesis/config` on freshly built normal images:
"Found 0 first, 11 driver … Setup validation successful."

## 3. Where it ended

| Stage | Local lines / functions | Δ |
|---|---|---|
| Tier 0 baseline (iter00) | 8,634 / 1,115 | — |
| Tier 0 after 3 menu iterations (iter03) | 8,641 / 1,115 | +61 lines targeted (net small) |
| + Tier 1 (iter04) | 10,076 / 1,244 | +1,448 / +130 |
| + txn inner-op menus (iter07) | ~10,000 / 1,242 | targeted branches; net within noise |
| + Tier 2 `lease` (iter10) | 10,894 / 1,341 | +954 / +102 |

Active: Tier 0, Tier 1, Tier 2 `lease`: 11 drivers. Two changes undone
(rows 8 and 9). Four Antithesis runs (30 min each): three triaged healthy
apart from one **etcd crash** (`findings/txn-from-key-delete-crash.md`);
run 4 (`fb7e3f1fd12a5c417bfed2ecddf840dc-64-0`) not yet triaged.

What helped most, in order: **adding operations** (Tier 1, then lease) by
far; then **menu edges taken from the inputs tables**, each worth a few
deterministic branches; then **sharing state through pools** (keys, then
lease IDs), which is what made the lease group reach KV code that Tier 0
couldn't. What didn't help: rebalancing for ok rate when the failures *were*
the coverage (row 8), and pool-size changes aimed at code outside the
measured modules (row 9).

What got in the way:

- **No Antithesis coverage export** (snouty 0.7.2 / tenant 64.0): half of the
  skill's measurement loop (Antithesis edges, local vs. Antithesis diffs,
  the "Antithesis added little" half of the next-tier rule) couldn't be done.
- **Noise floor**: ±100 lines between seeds once Tier 1 is active, so
  merged-total diffs stopped meaning much. Targeted lines were the reliable
  signal.
- **2 vCPU VM**: one local measurement (3 × 120 s) takes ~8–9 min.

## 4. What I'd do next

1. Triage run 4: health, and whether the etcd2 fatal recurs with the lease
   group active.
2. Investigate the fatal with `antithesis-debug` at the recorded moment
   (`968fcfe0…`, input_hash −1643191784216122050, vtime 87.87), and with
   `antithesis-query-logs` to see if it always follows a compaction at the
   current revision.
3. Next feature group: `watch` (its streams meeting puts, deletes, compaction
   and lease expiry should be rich), then `lock`/`election`.
4. Harness candidates (for `antithesis-coverage-setup`, needing a decision):
   `ETCD_FEATURE_GATES=LeaseCheckpoint=true` (reaches `lessor.Checkpoint`);
   adding `github.com/google/btree` to `ANTITHESIS_INSTRUMENT`.
5. Review findings not yet tried: revisions relative to the current one
   (#3), per-process value-size regimes (#5), abandoning some streams
   early (#6).

## 5. Run 4 triage and the crash investigation

Run 4 (`fb7e3f1fd12a5c417bfed2ecddf840dc-64-0`, Tier 0 + 1 + lease). All
infrastructure properties pass (instrumentation, symbols, no Antithesis
errors) and every driver ran without failing, but `container: etcd0/1/2,
exit code: 2` failed 21 times across 10 timelines. Exit code 2 is a Go panic
(run 3's single crash was exit code 1, `lg.Fatal`).

How it was investigated, in order:

1. **Per-timeline logs** (`snouty runs --json logs` for two counterexample
   moments). In both, *every* member logged the same panic within a
   millisecond: `index out of range [0] with length 0` in `server_applyAll`
   → `txn.put` (`txn/put.go:55`) ← `executeTxn`. The whole cluster crashing
   on the same committed raft entry pointed at the SUT, not at a fault.
2. **Reading the code.** `put.go:55` is `val = prevKV.KVs[0].Value` under
   `ignore_value`. Txns check `ignore_*` puts up front (`checkPut` →
   `ErrKeyNotFound`), but against the state *before* the txn runs, while ops
   execute in order. Something in the same txn must have deleted the key
   first, and `checkIntervals` is supposed to forbid exactly that. It does
   handle prefix deletes but not `range_end = "\x00"`: its interval tree uses
   `""` for +∞, so `[key, "\x00")` is an empty interval that overlaps nothing.
3. **Local repro of the hypothesis.** One txn,
   `[delete_range(key00, "\x00"), put(key05, ignore_value=true)]`, crashed all
   three local members with the identical panic. Then the checks that turn
   "crash" into "SUT bug":
   - no faults (local), so not fault injection;
   - the uninstrumented coverage build also crashes, so not instrumentation;
   - official etcd **v3.6.0 and v3.5.17** crash too (with
     `applyTxn: failed Put: key not found` → deliberate panic), so it's an
     old bug, not a `main` regression;
   - restarting the members crashes them again (WAL replay), so the cluster
     is permanently down.
4. **Run 3's fatal turned out to be the same bug.** The same hole lets a txn
   delete and re-put one key at a single revision. In `keyIndex.compact`,
   compacting at exactly that revision keeps the new generation in the index
   but leaves its revision out of the backend's keep set. Local repro (txn,
   compact at its revision, read the key): exactly run 3's
   `range failed to find revision pair`, killing only the member serving
   the read (exit 1). Reading the key on another member killed that one too,
   so the corruption is on every replica.
5. **Cross-timeline check.** The query-logs skill needs `agent-browser`, which
   isn't installed here, so it wasn't used. The multiverse debugger skill is
   browser-based too, and with local repros it wasn't needed. Instead,
   `snouty runs events` (server-side search over all timelines) for every
   panic and fatal: run 4 has 22 panics, all this signature (9 ×
   `ignore_value` at `put.go:55`, 13 × `ignore_lease` at `put.go:58`, 3 via
   a nested txn), and nothing else. Run 3 has the single fatal. Every
   container exit in both runs is explained. All three variants
   (`ignore_lease`, nested txn, delete-all-keys `("\x00","\x00")`) were also
   reproduced locally.
6. **Root cause confirmed with a fix.** In a scratch copy of etcd (not this
   checkout), mapping `"\x00"` to `""` in `checkIntervals` makes every repro
   fail with `ErrGRPCDuplicateKey` and the server stay up.

**Verdict: both crashes are real etcd bugs with one root cause. Neither is a
harness false positive.** Write-up, repro scripts and the candidate fix:
`findings/txn-from-key-delete-crash.md`, `findings/repro/`.

Why the workload found it: `kv.txn` builds inner ops from the same
`pick_range()` menu as `kv.delete_range`, which includes from-key and
all-keys deletes, and since iteration 7 its inner puts use the full
`PUT_OPTIONS` (with `ignore_value`/`ignore_lease`). Iteration 7, the one
that dropped txn ok from 51% to 28% and that iteration 8 tried to undo, is
what made run 4 hit this so often (run 3, before iteration 7, hit only the
compaction variant, once). The review's suggestion to give inner ops the
standalone menus paid off, though not in a way the coverage numbers showed.

### Fix applied, run 5

At the user's request the fix went into the checkout
(`server/etcdserver/api/v3rpc/key.go`, 5 lines: `range_end == "\x00"` maps
to `""`, the interval tree's +∞). `gofmt`/`go vet` clean; `go test
./etcdserver/api/v3rpc/` passes. With the rebuilt instrumented image, both
local repros are rejected with `duplicate key given in txn request` and all
members stay healthy. Run 5 (`a9d5dfcdfd77505dcc64d343f436d807-64-0`, 30 min)
uses exactly run 4's drivers, so the SUT fix is the only difference.
