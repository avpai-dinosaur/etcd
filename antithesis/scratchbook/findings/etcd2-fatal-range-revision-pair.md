# Possible etcd bug: member fatals with "range failed to find revision pair" after compaction

Found while building the coverage workload (no properties). Antithesis's
built-in property **"No unexpected container exits"** failed:
`container: etcd2, exit code: 1`. Not investigated to root cause.

## Where

- Run: `968fcfe06c5e1e8b3d0cc0f3bec78f0b-64-0` (30 min, Tier 0 + Tier 1
  drivers: put, range, delete_range, txn, range_stream, compact)
- Moment: input_hash `-1643191784216122050`, vtime `87.86915059085004`
- SUT: etcd `main` @ f061acd09, built with the Antithesis Go instrumentor
- Log: `snouty runs --json logs 968fcfe06c5e1e8b3d0cc0f3bec78f0b-64-0 -1643191784216122050 87.86915059085004`

## What happened (timeline in vtime)

| vtime | Who | Event |
|---|---|---|
| 83.02 | fault injector | network faults restored on all nodes (no faults active afterwards) |
| 85.67 | etcd0/1/2 | `compact tree index`, revision 50 (from a `kv.compact` driver call at the current revision) |
| 85.76 | etcd0/1/2 | `finished scheduled compaction`, compact-revision 50, 72 keys compacted, **same hash 2434236642 on all three**, db in use 25 kB |
| 85.76–87.38 | etcd2 | no log lines |
| 87.38 | etcd2 | **fatal** `mvcc/kvstore_txn.go:128` "range failed to find revision pair": revision-main 50, revision-sub 8, revision-current 50, key `key0` … end `key1` (prefix range), len-revpairs 1, len-values 0 |

Stack (abridged): `rangeKeys` ← `storeTxnWrite.Range` ← `txn.executeRange` ←
`txn.executeTxn` ← `txn.Txn` ← `applierV3backend.Txn` ← … ←
`EtcdServer.applyEntryNormal`. So it was the **apply of a committed write txn**
whose inner range op (prefix `key0`) ran before the txn's own writes. The tree
index returned revision {50, 8} for a key in that range, but the backend
had no value for it.

etcd0 and etcd1 did not crash, and all three reported the same post-compaction
hash, so the backends agreed at 85.76. Something on etcd2 between 85.76 and
87.38 (or how that read saw the backend) made the index and the backend
disagree.

## How often

One timeline in run `968fcfe0…` (`snouty runs events <run> "range failed to
find revision pair"`). Zero in the two Tier 0-only runs (`d827d5ee…`,
`5eace8bd…`), which have no `kv.compact` or `kv.txn`.

## Ingredients

- Compaction at exactly the current revision (`kv.compact` picks `rev` from a
  fresh response header), with `ETCD_COMPACTION_BATCH_LIMIT=10`
- Revision 50 had at least 9 sub-revisions. That can be a txn with many
  writes, or a single prefix/range delete (each deleted key gets its own
  sub-revision), so {50, 8} may be a **tombstone**. Unverified hypothesis:
  compaction at exactly a tombstone's revision leaves the index and the
  backend disagreeing on one member.
- Write txns with inner prefix ranges (from `kv.txn`): the failing read
- `ETCD_SNAPSHOT_COUNT=50` (frequent snapshots)
- Antithesis thread pausing and earlier network faults

## Next steps

- `antithesis-debug` on the moment above: inspect etcd2's index and backend
  around vtime 86–87, or branch earlier to see whether it reproduces.
- `antithesis-query-logs`: does "range failed to find revision pair" occur
  in other timelines, and is it always preceded by a compaction at the
  current revision?
- Compare with known etcd issues about index/backend mismatch after
  compaction.
