# Workload Ledger

Local measurement: 3 seeds × 120 s (`DURATION=120`, concurrency 4), merged.
Snapshots: `antithesis/local/out/iterNN.json` (LCOV via `gocov2lcov.py`, so
function counts are real).

Row → local snapshot: row 0 = `iter00`, 1 = `iter01`, 2 = `iter02`,
3 = `iter03`, 5 = `iter04`, 6 = `iter06`, 7 = `iter07`, 8 = `iter08`,
9 = `iter09`, 11 = `iter10` (rows 4, 10, 12, 13 are Antithesis runs).

Note on ok rates: once `kv.compact` is active, reads at fixed historical
revisions often hit `required revision has been compacted`, so `kv.range` /
`kv.range_stream` ok fell to ~34% (from 56% in row 3). That is the compaction
paths being exercised, not broken drivers. `lease.keepalive` and
`lease.timetolive` count "not found" answers (TTL 0 / −1) as ok, since those
aren't errors, so their 100% ok says nothing about how often a pool lease
exists.

**Antithesis coverage is not available here.** `snouty --json runs show`
(snouty 0.7.2, API v1, tenant release 64.0) returns only
`results.environment`, with no `results.coverage`, and the docs describe no
other export. So the "Antithesis: edges" column can't be filled in. Antithesis
runs are judged on health (triage properties) and on outcome lines found with
`snouty runs events <run> "<text>"` (max 1,000 matches per search, so these
show presence and a rough mix, not totals).

| # | Date | Change | Active tiers / groups | Local: new lines / functions | Antithesis run | Antithesis: edges (Δ) | Notes |
|---|---|---|---|---|---|---|---|
| 0 | 2026-10-09 | Initial Tier 0 drivers (`kv.put`, `kv.range`, `kv.delete_range`) | 0 | baseline: 8,634 / 1,115 | — | — | ok rates: delete 94%, put 52%, range 49%. All Tier 0 code-location functions reached (3/3 each) |
| 1 | 2026-10-09 | `kv.delete_range`: 1–5 calls per run (was 1–20), so range-deletes stop emptying the pool | 0 | +42 / +1 (−2 / −1) | — | — | target hit: `sliceCapWithLimit` `return limit` (a range with more results than its limit). Rest is rafthttp timing noise + a proposal timeout. Pool still mostly empty: put `key not found` 17% |
| 2 | 2026-10-09 | Menus: invalid sort target (5); put with `ignore_lease` + non-zero lease | 0 | +14 / 0 (−52 / −1) | — | — | both targets hit (`key.go:163-164` `ErrGRPCInvalidSortOption` for target, `key.go:190-191` `ErrGRPCLeaseProvided`). Losses are iter01's timing noise not recurring. Cost: range ok fell to 44% (30% stop at validation) |
| 3 | 2026-10-09 | Menus: invalid values rare (sort order 1/9, target 1/11), revision 0 weighted ×4, plain puts 7/14 | 0 | +5 / +1 (−0 / −0) | — | — | ok rates up: put 49→59%, range 44→56%. `kvSortByKey.Less` back. Tier 0 local growth levelled: +42 (mostly noise), +14, +5 |
| 4 | 2026-10-09 | — (Antithesis baseline, drivers as of row 0) | 0 | — | `d827d5ee6e2901533b10185125d27a84-64-0` (30 min) | n/a: no coverage export (see notes) | healthy: all 34 properties pass, 93 instrumented modules, thread pausing on etcd0/1/2, bootstrap `etcd server process started` hit. Drivers ran ~13k times each, 0 failures. Fault-only outcomes seen: `UNAVAILABLE: leader changed`, `failed to connect`, `DEADLINE_EXCEEDED`, `CANCELLED (RST_STREAM)`; server logs `apply request took too long` (`txn/util.go:93`, unreached locally). No NOSPACE |
| 5 | 2026-10-10 | Add Tier 1: `kv.txn`, `kv.range_stream`, `kv.compact` | 0, 1 | +1,448 / +130 (−13 / −1) | — | — | all Tier 0+1 code-location functions 3/3. New: txn compare/apply, `checkIntervals` (interval tree), RangeStream chunking (`adjustChunkLimit`), compaction scheduling + KV hasher, expensive-request logging. ok: txn 51%, range_stream 36% (future/compacted revisions, Unimplemented), compact 39%. Reads now also hit `compacted` |
| 6 | 2026-10-10 | `kv.txn` compare menu: rare empty key, invalid result (4), invalid target (5) | 0, 1 | +17 / +1 (−92 / −4) | — | — | targets hit: `txn.go:335` (fallthrough `return true` on unknown result), `key.go:216` (empty compare key), `key.go:286` (then/else put overlap). Losses = slow-request logging stringers + interval-tree variety: within the seed-to-seed noise floor (16–151 lines, 1–11 functions between single seeds) |
| 7 | 2026-10-10 | `kv.txn` inner ops use the standalone menus (`put_fields()` / `range_fields()` moved into helper_common; review finding #2) | 0, 1 | +85 / +5 (−84 / −4) | — | — | targets hit: `checkTxn` error exit (`txn.go:56-58`), `checkRange` future/compacted (`txn/range.go:179-183`), `checkPut` lease-not-found (`txn/put.go:74-75`), nested interval errors (`key.go:271,291`). Cost: txn ok 51%→28% (one bad inner op fails the whole txn). Losses = timing noise |
| 8 | 2026-10-10 | `kv.txn`: inner ops use the full menus only 1 in 3 (plain otherwise) — **undone** | 0, 1 | +38 / +2 (−60 / −3) | — | — | txn ok only 28%→35%; nothing new reached; lost targeted `txn/range.go:183` (valid historical revision in a txn). Reverted to row 7 |
| 9 | 2026-10-10 | Key pool width drawn once per process (1 / 4 / 16 / 16+1,024 keys, nested; review finding #4) — **undone** | 0, 1 | +9 / +1 (−67 / −3) vs row 7 | — | — | targets not reached: btree splits are in `github.com/google/btree` (external, not in coverage), RangeStream halving needs >3 MiB chunks, not more keys. Only gain was the flaky `kvSortByKey.Less`. Reverted |
| 10 | 2026-10-10 | — (Antithesis run 2, drivers as of row 3, same 30 min) | 0 | — | `5eace8bd2d445e0eec6b01e44e6a4a44-64-0` (30 min) | n/a | healthy, all properties pass, 93 modules, drivers 12–13k runs each. Every searched outcome present in both runs at the 1,000-match cap (leader changed, UNAVAILABLE, DEADLINE_EXCEEDED, slow apply), so the two Tier 0 runs can't be ranked without coverage |
| 11 | 2026-10-10 | Add Tier 2 group `lease` (grant/revoke/keepalive/timetolive/list) over a shared 8-ID lease pool; `kv.put`/`kv.txn` lease options use the pool | 0, 1, lease | +954 / +102 (−62 / −3) vs row 7 | — | — | all lease ops 3/3. KV↔lease: `storeTxnWrite.put` attach/detach (`kvstore_txn.go:269-290`) and delete detach now reached; leader expiry (`revokeExpiredLeases`) runs; follower→leader forwarding (`leasehttp`). Lost `WAL.cut` (fewer big puts now that lease drivers take ~45% of slots). Unreached: `lessor.Checkpoint` (needs `LeaseCheckpoint` gate, off), `Recover` (restarts) |
| 12 | 2026-10-10 | — (Antithesis run 3, drivers as of row 5: Tier 0 + Tier 1) | 0, 1 | — | `968fcfe06c5e1e8b3d0cc0f3bec78f0b-64-0` (30 min) | n/a | **1 failing built-in property: `container: etcd2, exit code: 1`**: etcd2 fataled with `mvcc/kvstore_txn.go:128` "range failed to find revision pair" while applying a txn, 1.6 s after a compaction at the current revision. **etcd bug, same root cause as row 13** (confirmed by local repro), see `findings/txn-from-key-delete-crash.md`. Otherwise healthy: 93 modules, drivers 5–8.6k runs each; Tier 1 outcomes present (txn ok, range_stream ok, compact ok/compacted/future) |
| 13 | 2026-10-10 | — (Antithesis run 4, drivers as of row 11: Tier 0 + 1 + lease) | 0, 1, lease | — | `fb7e3f1fd12a5c417bfed2ecddf840dc-64-0` (30 min) | n/a | **etcd bug**: `container: etcd0/1/2, exit code: 2` (21 exits, 10 timelines). All members panic together applying a txn (`txn/put.go:55/58`, index out of range). Root cause shared with row 12: `checkIntervals` treats a from-key delete (`range_end="\x00"`) as an empty interval, so delete+put of the same key in one txn gets through. Reproduced locally (no faults, uninstrumented, also etcd v3.6.0/v3.5.17); one-line fix verified. See `findings/txn-from-key-delete-crash.md`. Infra properties all pass; drivers 3.4–5.4k runs each |
| 14 | 2026-10-10 | `kv.compact`: failures of its revision-reading Range now logged as `OP kv.compact read_rev_error=…` (were `OP kv.range error=…`, skewing kv.range counts) | 0, 1, lease | — (no behavior change) | — | — | from the final self-review |
| 15 | 2026-10-10 | **SUT fix applied** (`server/etcdserver/api/v3rpc/key.go` `checkIntervals`: delete `range_end="\x00"` treated as unbounded). Drivers unchanged from row 11/14 | 0, 1, lease | — | `a9d5dfcdfd77505dcc64d343f436d807-64-0` (30 min) | n/a | launched; compare with row 13 (same drivers, same length). Expect: no container exits; txns that delete from-key and put a covered key now fail with `duplicate key` |

## Tried and didn't help

- **Row 8**: making txn inner ops plain 2 in 3 to win back ok rate. Gained
  7 points of ok rate, reached nothing new, lost one of row 7's targeted lines,
  and added a flag to the helpers. Undone: the lower txn ok rate is the price
  of reaching the inner-op checks.
- **Row 9**: per-process key-pool width. Its two targets were either outside
  the measured code (the index btree is the external `google/btree`) or need
  big *bytes* per chunk rather than more keys (RangeStream halving). Undone.
  It might still shape state in ways coverage can't show (one hot key with
  long history), but without an Antithesis coverage export there's no way to
  check, so the simpler pool stays.
