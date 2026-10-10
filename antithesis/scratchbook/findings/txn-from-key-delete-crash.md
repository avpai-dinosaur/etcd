# etcd bug: a txn with a from-key delete can crash the whole cluster

**Verdict: SUT bug, not a harness false positive.** One client request
crashes every member, and they crash again on restart. Reproduced locally:

- with no fault injection,
- without the Antithesis instrumentation,
- on released **etcd v3.6.0 and v3.5.17** (not a regression on `main`).

A one-line fix makes every repro fail cleanly instead.

It is client-triggerable (any client allowed to write) and leaves the cluster
permanently down, so it is a denial-of-service issue. Consider reporting it
through etcd's security process (`security/` in this repo) rather than as a
public issue.

## Root cause

`checkIntervals` (`server/etcdserver/api/v3rpc/key.go:236`) is meant to
reject a txn that both deletes and puts the same key (`ErrGRPCDuplicateKey`).
It puts each delete's `[key, range_end)` into an interval tree of
`StringAffineComparable`s, which use `""` as +∞. But a delete with
`range_end = "\x00"` means "every key ≥ key" (`mkGteRange` turns `"\x00"`
into "unbounded" when the delete *executes*). `checkIntervals` inserts the
raw `[key, "\x00")`, an empty, inverted interval that overlaps nothing. So a
txn that deletes from a key onwards (`etcdctl del --from-key`) or deletes all
keys (`key="\x00"`, `range_end="\x00"`) and then puts a key in that range
passes the check. Nested txns are affected too.

The pre-execution checks (`checkTxn` → `checkPut`) look at the state *before*
the txn runs, while ops execute in order. So the txn is accepted, committed
through raft, and then applied in a state the code assumes can't happen. That
has two consequences, and Antithesis found both.

### 1. Panic on every member (run 4)

Txn: `[delete_range(key00, "\x00"), put(key05, ignore_value=true)]` (or
`ignore_lease=true`), with key05 existing beforehand. `checkPut` passes,
because key05 exists. At execution the delete has already removed key05, so
`put()` reads `prevKV.KVs[0]` from an empty result:

- `main`: `runtime error: index out of range [0] with length 0` at
  `server/etcdserver/txn/put.go:55` (`ignore_value`) or `:58`
  (`ignore_lease`), exit code 2;
- v3.6.0 / v3.5.17: `applyTxn: failed Put: etcdserver: key not found`, then
  the deliberate `lg.Panic("unexpected error during txn with writes")`,
  exit code 2.

The entry is committed, so **every** member panics while applying it, and
panics again on restart when it replays the WAL (checked locally: all three
exit 2 again after `docker compose start`). The cluster is down for good.

### 2. Index/backend corruption after compaction (run 3)

Txn: `[delete_range(key00, "\x00"), put(key05, "v2")]`. No ignore flags, so
it succeeds, but key05 is deleted and recreated at the same main revision R
(tombstone {R,0}, new value {R,1}). mvcc assumes that never happens.
Compacting at exactly R (`keyIndex.compact` / `doCompact`,
`server/storage/mvcc/key_index.go`) walks only the older generation, drops its
tombstone, and keeps the new generation in the index. But {R,1} never goes
into the "keep" set, so the backend deletes it. The next read of key05 hits:

```
{"level":"fatal","caller":"mvcc/kvstore_txn.go:128","msg":"range failed to find revision pair",
 "revision-main":R,"revision-sub":1,"revision-current":R, ...}
```

Only the member serving the read dies (exit code 1), which is why run 3 lost
only etcd2. All members are corrupted, though: reading key05 on another member
kills that one too (checked locally). In run 3 it was revision 50, sub 8: a
txn whose from-key delete removed several keys before re-putting one.

## Evidence from Antithesis

| Run | Failing property | Signature | Timelines |
|---|---|---|---|
| `968fcfe06c5e1e8b3d0cc0f3bec78f0b-64-0` (Tier 0+1) | `container: etcd2, exit code: 1` | 1 × fatal `range failed to find revision pair` | 1 |
| `fb7e3f1fd12a5c417bfed2ecddf840dc-64-0` (Tier 0+1+lease) | `container: etcd0/1/2, exit code: 2` (8 + 6 + 7) | 22 × panic `index out of range [0] with length 0`: 9 at `put.go:55`, 13 at `put.go:58`, 3 via a nested txn (`txn.go:187`) | 10 |

Across all timelines (`snouty runs events <run> '"level":"panic"'` / `'"level":"fatal"'`)
there are no other panic or fatal signatures in either run. Every container
exit is one of these two. In run 4 the members crash together, within about
a millisecond, at 46 s, 75 s, 84 s, 111 s, 135 s, 246 s, 264 s, 317 s and 372 s
of virtual time, so the workload reaches it quickly and often. Example moments:

- run 4: input_hash `-3382880873023920581`, vtime `46.86965172877535` (etcd1 + etcd2)
- run 4: input_hash `-3024743228595039228`, vtime `76.12015166855417` (all three)
- run 3: input_hash `-1643191784216122050`, vtime `87.86915059085004` (etcd2)

The run-2 and baseline runs (Tier 0 only: no `kv.txn`) have neither signature.

## Why these aren't harness artifacts

| Possible harness cause | Ruled out by |
|---|---|
| Fault injection / Antithesis timing | Local repro, no faults; also no faults active at the run-3 crash |
| Antithesis instrumentation (toolexec rewrites code) | Same panic on the uninstrumented `go build -cover` image |
| This checkout / `main` only | Same crash on official `gcr.io/etcd-development/etcd:v3.6.0` and `v3.5.17` images |
| The workload sending an invalid request the server should reject | That's the bug: the server is *supposed* to reject it (`ErrGRPCDuplicateKey`), and with the fix it does |

## Reproduce

Scripts in `repro/` (Python, gRPC stubs from the workload image; set `EP`):

```bash
docker compose -f antithesis/config/docker-compose.yaml up -d
docker cp antithesis/scratchbook/findings/repro/repro_put_ignore_value.py etcd-workload:/tmp/r.py
docker exec etcd-workload python3 /tmp/r.py          # all 3 members exit 2
# repro_variants.py {ignore_lease|nested|all_keys}   # needs EP=host:port
# repro_compact_revpair.py                           # member serving the read exits 1
```

## Version history (bisected locally, 2026-10-10)

Tested on a fresh single-member cluster per version, with no Antithesis and no
faults. Released versions came from `gcr.io/etcd-development/etcd` images or
GitHub release tarballs. Old `main` commits were built from source (Go 1.8.7
for the 2017 commits, local Go for 2024). Crash = the member exits.

| Release | `repro_put_ignore_value.py` (panic) | `repro_compact_revpair.py` (fatal) |
|---|---|---|
| v3.0.17, v3.1.0, v3.1.24 | no crash* | no crash |
| v3.2.0, v3.2.4, v3.2.32, v3.3.0, v3.3.27 | **exit 2** | no crash |
| v3.4.0 … v3.4.33 | **exit 2** | no crash |
| v3.4.34, v3.4.45 | **exit 2** | **exit 1** |
| v3.5.0 … v3.5.15 | **exit 2** | no crash |
| v3.5.16, v3.5.17, v3.5.34 | **exit 2** | **exit 1** |
| v3.6.0, v3.6.15, v3.7.2 | **exit 2** | **exit 1** |

\* v3.0/v3.1 still accept the bad txn (the delete covers key05 and the put
re-creates it at the same revision), but they don't know `ignore_value`. The
server drops the field and writes an empty value, so nothing can fail at apply
time.

Commits involved (all on `main`):

1. **Validation hole, `4fc89678b` (2016-02-18), "etcdserver: add >= support
   for v3 delete range".** It made `range_end="\x00"` mean "≥ key" for
   DeleteRange at apply time. It did not update the duplicate-key check
   (`checkRequestDupKeys`, from `c5c5063ef`). That check still treats `"\x00"`
   as a literal end, so a from-key delete overlaps nothing. `6ed51dc62`
   (nested txns, 2017-06) rewrote the check as `checkIntervals` and kept the
   hole. Found by reading the code, not by a build.
2. **Panic, `8752ee52a` (2016-12-05; merged in PR #6894 on 2017-01-13),
   "etcdserver: use prev-value for ignore_value writes".** The first way to
   make a txn put fail at apply time (`ErrKeyNotFound`), which then hits the
   "unexpected error during txn" panic. Verified by building: `7f8b5774a` (its
   parent's parent) doesn't crash, and `8752ee52a` crashes. The parent,
   `e655420d3`, doesn't build on its own. `8a87769a0` (2017-01-25, the
   `ignore_lease` change) adds the second path, also verified with builds on
   each side. First affected release: **v3.2.0**.
3. **Compaction fatal, `bbdc94181` (2024-07-04; PR #18274), "*: keep tombstone
   if revision == compactAtRev".** It changed `doCompact` to stop at a
   generation whose tombstone equals `atRev` (`>` became `>=`). With a
   delete and a put at the same main revision, that is the old generation, so
   `{R,1}` in the new generation never goes into the keep set and the backend
   deletes it. Verified by building: `bbdc94181^` doesn't crash and `bbdc94181`
   does. Backported as #18474 / #18475. First affected releases: **v3.5.16,
   v3.4.34** (and every v3.6+).

## Fix (applied to this checkout on 2026-10-10)

Applied in `server/etcdserver/api/v3rpc/key.go` (same change as
`repro/candidate-fix.diff`); the existing `v3rpc` unit tests pass. Re-run on
the rebuilt instrumented image: both repros are rejected and all members stay
healthy. Antithesis run with the fix: `a9d5dfcdfd77505dcc64d343f436d807-64-0`.
Originally: in `checkIntervals`, treat `range_end == "\x00"`
as unbounded (`""`) when building the delete interval. Built in a scratch copy
and run against every repro above: each txn is rejected with `INVALID_ARGUMENT:
etcdserver: duplicate key given in txn request`, and the server stays up.
Separately, `put()` indexing `prevKV.KVs[0]` without a length check and the
compaction keep-set logic both trust this invariant. Worth hardening as
defence in depth, and worth a regression test in `tests/` for from-key and
all-keys deletes inside txns.

## Effect on the Antithesis workload

Until it's fixed, every timeline that hits this loses its whole cluster for
good (crash loop), so the rest of that timeline explores nothing. Run 4
lost 10 timelines this way. Options (a decision for the user, since
the coverage-workload rules say not to bend the workload around a bug):
apply the fix to the SUT for further runs, or keep it as is and accept the
lost timelines.
