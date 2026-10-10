---
sut_path: /home/exedev/etcd
commit: f061acd0902d489041448cdd19d71a345d27b9f5
updated: 2026-10-09
---

# API Surface: etcd

## Summary

| Field | Value |
|---|---|
| System | etcd |
| Tier 0 confirmed by user | yes |
| Operations | 60 |

etcd is a strongly consistent, distributed key-value store replicated with Raft.
Its main job is storing and retrieving keys with linearizable reads and writes
and an MVCC revision history; on top of that it offers watches, leases, and
lock/election primitives for coordination, plus cluster membership, maintenance,
downgrade, and RBAC auth administration. Sources: gRPC services in
`api/etcdserverpb/rpc.proto`, `server/etcdserver/api/v3lock/v3lockpb/v3lock.proto`,
`server/etcdserver/api/v3election/v3electionpb/v3election.proto` (registered in
`server/etcdserver/api/v3rpc/grpc.go:Server` and `server/embed/serve.go`), the
etcdctl and etcdutl command trees, `client/v3`, and https://etcd.io/docs/v3.8/.

## Index

| ID | Name | Tier | Feature group | Kind |
|---|---|---|---|---|
| `kv.put` | Put | 0 | — | data |
| `kv.range` | Range (get) | 0 | — | data |
| `kv.delete_range` | Delete range | 0 | — | data |
| `kv.txn` | Transaction | 1 | — | data |
| `kv.range_stream` | Range stream | 1 | — | data |
| `kv.compact` | Compact | 1 | — | data |
| `watch.create` | Watch create | 2 | `watch` | data |
| `watch.cancel` | Watch cancel | 2 | `watch` | data |
| `watch.progress` | Watch progress request | 2 | `watch` | data |
| `lease.grant` | Lease grant | 2 | `lease` | data |
| `lease.revoke` | Lease revoke | 2 | `lease` | data |
| `lease.keepalive` | Lease keep-alive | 2 | `lease` | data |
| `lease.timetolive` | Lease time-to-live | 2 | `lease` | data |
| `lease.list` | Lease list | 2 | `lease` | data |
| `lock.lock` | Lock | 2 | `lock` | data |
| `lock.unlock` | Unlock | 2 | `lock` | data |
| `election.campaign` | Campaign | 2 | `election` | data |
| `election.proclaim` | Proclaim | 2 | `election` | data |
| `election.leader` | Leader | 2 | `election` | data |
| `election.observe` | Observe | 2 | `election` | data |
| `election.resign` | Resign | 2 | `election` | data |
| `member.add` | Member add | 3 | `membership` | admin |
| `member.promote` | Member promote | 3 | `membership` | admin |
| `member.remove` | Member remove | 3 | `membership` | admin |
| `member.update` | Member update | 3 | `membership` | admin |
| `member.list` | Member list | 3 | `membership` | admin |
| `alarm.list` | Alarm list | 3 | `alarm` | admin |
| `alarm.disarm` | Alarm disarm | 3 | `alarm` | admin |
| `alarm.activate` | Alarm activate | 3 | `alarm` | admin |
| `maintenance.status` | Status | 3 | — | admin |
| `maintenance.defragment` | Defragment | 3 | — | admin |
| `maintenance.hash` | Hash | 3 | — | admin |
| `maintenance.hashkv` | Hash KV | 3 | — | admin |
| `maintenance.snapshot` | Snapshot save | 3 | — | admin |
| `maintenance.move_leader` | Move leader | 3 | — | admin |
| `downgrade.validate` | Downgrade validate | 3 | `downgrade` | admin |
| `downgrade.enable` | Downgrade enable | 3 | `downgrade` | admin |
| `downgrade.cancel` | Downgrade cancel | 3 | `downgrade` | admin |
| `auth.enable` | Auth enable | 3 | `auth` | admin |
| `auth.disable` | Auth disable | 3 | `auth` | admin |
| `auth.status` | Auth status | 3 | `auth` | admin |
| `auth.authenticate` | Authenticate | 3 | `auth` | admin |
| `user.add` | User add | 3 | `auth` | admin |
| `user.get` | User get | 3 | `auth` | admin |
| `user.list` | User list | 3 | `auth` | admin |
| `user.delete` | User delete | 3 | `auth` | admin |
| `user.change_password` | User change password | 3 | `auth` | admin |
| `user.grant_role` | User grant role | 3 | `auth` | admin |
| `user.revoke_role` | User revoke role | 3 | `auth` | admin |
| `role.add` | Role add | 3 | `auth` | admin |
| `role.get` | Role get | 3 | `auth` | admin |
| `role.list` | Role list | 3 | `auth` | admin |
| `role.delete` | Role delete | 3 | `auth` | admin |
| `role.grant_permission` | Role grant permission | 3 | `auth` | admin |
| `role.revoke_permission` | Role revoke permission | 3 | `auth` | admin |
| `offline.snapshot_restore` | Snapshot restore | 3 | `offline` | admin |
| `offline.snapshot_status` | Snapshot status | 3 | `offline` | admin |
| `offline.defrag` | Offline defrag | 3 | `offline` | admin |
| `offline.migrate` | Storage migrate | 3 | `offline` | admin |
| `offline.hashkv` | Offline hash KV | 3 | `offline` | admin |

## Feature Groups

| ID | Description |
|---|---|
| `watch` | Stream change events for keys or ranges from a revision onward |
| `lease` | Time-to-live leases that keys can attach to and that expire unless kept alive |
| `lock` | Server-side distributed lock service built on leases and keys |
| `election` | Server-side leader election service built on leases and keys |
| `membership` | Runtime cluster reconfiguration: add, remove, update, promote members |
| `alarm` | Cluster-wide alarms (NOSPACE, CORRUPT) that restrict writes |
| `downgrade` | Cluster version downgrade workflow |
| `auth` | Authentication and role-based access control (users, roles, permissions, tokens) |
| `offline` | etcdutl commands run against a stopped member's data directory or a snapshot file |

## Flagged

- Left out (health/metrics/debug): HTTP `/health`, `/livez`, `/readyz` (and their sub-checks), `/metrics`, `/version`, `/debug/vars`, `/debug/pprof/*` (`server/etcdserver/api/etcdhttp/*.go`), and the standard gRPC health service registered in `server/etcdserver/api/v3rpc/grpc.go:Server`. Not user operations.
- Left out (internal peer traffic): rafthttp pipeline/stream/snapshot/probing handlers (`server/etcdserver/api/rafthttp/transport.go`), peer `/members` and `/members/promote/` (forwarding for `member.promote`), peer lease renew/ttl handlers in `leasehttp` (forwarding for `lease.keepalive` / `lease.timetolive`), and the peer downgrade-enabled and hashkv handlers (`server/etcdserver/api/etcdhttp/peer.go`). Lease checkpointing (`LeaseCheckpoint` alpha gate) is likewise leader-internal.
- Left out (deployment mode, not an operation): the gRPC proxy (`server/etcdmain/grpc_proxy.go`, `server/proxy/grpcproxy/*`) re-exposes the same KV, Watch, Lease, Cluster, Maintenance, Auth, Lock and Election services. The L4 etcd gateway and v2/v3 discovery are bootstrap/deployment features.
- Left out (background, not a user call): lease expiry (`server/lease/lessor.go` revokes expired leases through raft, same effect as `lease.revoke`), auto-compaction (`--auto-compaction-mode` / `--auto-compaction-retention`, `server/etcdserver/api/v3compactor`, same path as `kv.compact`), and server-raised alarms on quota/corruption (same path as `alarm.activate`).
- Client-side composites with no RPC of their own: `etcdctl make-mirror` (Range + Watch + Txn against another cluster), `etcdctl check perf` / `check datascale` (load generators), `etcdctl endpoint health` (a Get of key `health` plus an alarm list), `clientv3.KV.Do`, `concurrency.STM`, `concurrency.Session`, `Mutex.TryLock` / `NewLocker`, and `client/v3/experimental/recipes` (RWMutex, Barrier, DoubleBarrier, Queue, PriorityQueue). `client/v3/namespace`, `client/v3/ordering`, `client/v3/leasing` and `client/v3/mirror` are also client wrappers.
- Note: `etcdctl lock` and `etcdctl elect` do NOT call the `v3lockpb.Lock` / `v3electionpb.Election` RPCs; they run `client/v3/concurrency` client-side over KV, Lease and Watch. Calling `lock.*` / `election.*` requires a gRPC (or HTTP gateway) client.
- Note: TLS client-certificate CN authentication (`--client-cert-auth`, `server/auth/store.go:authStore.AuthInfoFromTLS`) is an implicit login path with no RPC; it belongs to the `auth` group as configuration.
- Note: `etcdctl snapshot restore` / `snapshot status` moved to etcdutl; only `etcdctl snapshot save` remains in etcdctl. The `offline.*` operations cover the etcdutl versions. The bbolt CLI embedded in etcdutl (`etcdutl/ctl.go`) is low-level debug tooling and is left out, as are `version`, `completion` and `options` subcommands.
- Note: `alarm.activate` and `maintenance.hash` are accepted by the public gRPC API but not exposed by clientv3 or etcdctl (`maintenance.hash` is documented in the proto as testing-only). Both are kept as Tier 3 operations with low confidence.
- Note: the v3 HTTP/JSON gateway (`POST /v3/...`, `server/embed/serve.go`) exposes the same RPCs as gRPC (except `KV/RangeStream`, which is gRPC-only); it is recorded under each operation's How to call rather than as separate operations.

## Tier 0: Core

### `kv.put`: Put

- **What it does:** Stores a value under a key, creating or replacing it. Each put bumps the store revision by one and produces one event in the history. It can optionally attach a lease or return the previous key-value.
- **Tier reason:** First write in https://etcd.io/docs/v3.8/quickstart/ and https://etcd.io/docs/v3.8/tasks/developer/writing-to-etcd/; top-level `clientv3.KV.Put` in `client/v3/kv.go`; `etcdctl put`.
- **Notes:** Goes through raft (`EtcdServer.raftRequest`). The quota wrapper (`quotaKVServer.Put`) refuses the request and raises a NOSPACE alarm when the backend is over `--quota-backend-bytes`. `ignore_value` and `ignore_lease` reuse the key's current value or lease, so the key must already exist; setting `ignore_value` with a non-empty value (or `ignore_lease` with a non-zero lease) is rejected up front.

| Field | Value |
|---|---|
| ID | `kv.put` |
| Tier | 0 |
| Feature group | — |
| Kind | data |
| How to call | `etcdserverpb.KV/Put`, `POST /v3/kv/put`, `etcdctl put <key> <value>`, `clientv3.KV.Put` |
| Requires | — |
| Enabled by | — |
| Changes state | keys, revisions |
| Reads state | keys, leases, alarms |
| Related | `kv.range`, `kv.delete_range`, `kv.txn`, `kv.range_stream`, `kv.compact` |
| Code locations | `server/etcdserver/api/v3rpc/key.go:kvServer.Put`, `server/etcdserver/v3_server.go:EtcdServer.Put`, `server/etcdserver/txn/put.go:Put` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| key | bytes | Must be non-empty (`ErrGRPCEmptyKey`). The whole request must fit in `--max-request-bytes` (default 1.5 MiB) |
| value | bytes | Can be empty. Bounded by `--max-request-bytes` (default 1.5 MiB); total DB size bounded by `--quota-backend-bytes` (default 2 GiB; above 8 GiB triggers a startup warning) |
| lease | int64 | 0 = no lease. Must be an existing lease ID, otherwise lease-not-found. etcdctl takes it as hex (`--lease`) |
| prev_kv | bool | Default false; returns the key-value as it was before the put (`--prev-kv`) |
| ignore_value | bool | Default false; keeps the current value. value must be empty; the key must exist (`--ignore-value`) |
| ignore_lease | bool | Default false; keeps the current lease. lease must be 0; the key must exist (`--ignore-lease`) |

### `kv.range`: Range (get)

- **What it does:** Reads one key, or every key in `[key, range_end)`, at the current or a given historical revision. Supports limit, sort, keys-only and count-only, plus filters on mod and create revision.
- **Tier reason:** In https://etcd.io/docs/v3.8/quickstart/, https://etcd.io/docs/v3.8/tasks/developer/reading-from-etcd/ and https://etcd.io/docs/v3.8/tasks/developer/how-to-get-key-by-prefix/; top-level `clientv3.KV.Get`; `etcdctl get`.
- **Notes:** All variants (single key, prefix, from-key, historical `--rev`, serializable, sort, filters) go through the same handler, `EtcdServer.Range` → `txn.Range`, so they are inputs, not separate operations. By default a read is linearizable: it waits on `LinearizableReadNotify` (ReadIndex). With `serializable=true` it is served from the member's local state. Reading a revision at or below the compaction point returns `mvcc: required revision has been compacted`; reading a future revision returns `ErrFutureRev`.

| Field | Value |
|---|---|
| ID | `kv.range` |
| Tier | 0 |
| Feature group | — |
| Kind | data |
| How to call | `etcdserverpb.KV/Range`, `POST /v3/kv/range`, `etcdctl get <key> [range_end] [--prefix\|--from-key\|--rev\|--consistency=s\|...]`, `clientv3.KV.Get` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | keys, revisions, compaction |
| Related | `kv.put`, `kv.delete_range`, `kv.txn`, `kv.range_stream`, `kv.compact` |
| Code locations | `server/etcdserver/api/v3rpc/key.go:kvServer.Range`, `server/etcdserver/v3_server.go:EtcdServer.Range`, `server/etcdserver/txn/range.go:Range` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| key | bytes | Must be non-empty. `\x00` together with range_end `\x00` means all keys |
| range_end | bytes | Empty = single key; `\x00` = all keys >= key (`--from-key`); key+1 = prefix (`--prefix`) |
| limit | int64 | 0 = no limit; `more` in the response is set when results were cut off |
| revision | int64 | <= 0 = current revision. Must be above the compaction revision and at most the current revision (`--rev`) |
| sort_order | enum | NONE (default), ASCEND, DESCEND; other values return `ErrGRPCInvalidSortOption` |
| sort_target | enum | KEY (default), VERSION, CREATE, MOD, VALUE |
| serializable | bool | Default false (linearizable). etcdctl `--consistency=s` |
| keys_only | bool | Default false; leaves values out |
| count_only | bool | Default false; returns only the count |
| min_mod_revision / max_mod_revision | int64 | 0 = no filter. Applied after the read (`--min-mod-rev`, `--max-mod-rev`) |
| min_create_revision / max_create_revision | int64 | 0 = no filter (`--min-create-rev`, `--max-create-rev`) |

### `kv.delete_range`: Delete range

- **What it does:** Deletes one key, or every key in `[key, range_end)`. Returns the number deleted and optionally the deleted key-values. One revision bump; one delete event per deleted key.
- **Tier reason:** https://etcd.io/docs/v3.8/tasks/developer/how-to-delete-keys/ and the "Delete keys" section of https://etcd.io/docs/v3.8/dev-guide/interacting_v3/; top-level `clientv3.KV.Delete`; `etcdctl del`.
- **Notes:** Goes through raft. Not wrapped by the quota check (it frees space), so it is still allowed while a NOSPACE alarm is active. Deleting a key that does not exist succeeds with `deleted=0`.

| Field | Value |
|---|---|
| ID | `kv.delete_range` |
| Tier | 0 |
| Feature group | — |
| Kind | data |
| How to call | `etcdserverpb.KV/DeleteRange`, `POST /v3/kv/deleterange`, `etcdctl del <key> [range_end] [--prefix\|--from-key\|--prev-kv]`, `clientv3.KV.Delete` |
| Requires | — |
| Enabled by | — |
| Changes state | keys, revisions |
| Reads state | keys |
| Related | `kv.put`, `kv.range`, `kv.txn` |
| Code locations | `server/etcdserver/api/v3rpc/key.go:kvServer.DeleteRange`, `server/etcdserver/v3_server.go:EtcdServer.DeleteRange`, `server/etcdserver/txn/delete.go:DeleteRange` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| key | bytes | Must be non-empty (`ErrGRPCEmptyKey`) |
| range_end | bytes | Empty = single key; `\x00` = all keys >= key; key+1 = prefix |
| prev_kv | bool | Default false; returns the deleted key-values |

## Tier 1: Core variants

### `kv.txn`: Transaction

- **What it does:** Evaluates a list of comparisons against keys and runs either the `success` or the `failure` list of operations (range, put, delete range, nested txn), atomically, at a single revision.
- **Tier reason:** https://etcd.io/docs/v3.8/tasks/developer/how-to-transactional-write/; top-level `clientv3.KV.Txn` (If/Then/Else); `etcdctl txn`. It combines existing KV ops with compare-and-swap rather than adding a new concept, so it is a core variant.
- **Notes:** A read-only txn (no puts or deletes) does not go through raft. It is served like a range, linearizable unless every range is serializable. Write txns go through raft and are quota-checked (`quotaKVServer.Txn`). The same key cannot be put twice, or both put and deleted, in one txn (`ErrGRPCDuplicateKey`, checked by `checkIntervals`). Etcd's own `concurrency` (locks/elections) and the lease-keyed patterns in https://etcd.io/docs/v3.8/dev-guide/api_concurrency_reference_v3/ are built on Txn. The `TxnModeWriteWithSharedBuffer` feature gate (Beta, default on) changes how read checks run inside a write txn, not what the txn does.

| Field | Value |
|---|---|
| ID | `kv.txn` |
| Tier | 1 |
| Feature group | — |
| Kind | data |
| How to call | `etcdserverpb.KV/Txn`, `POST /v3/kv/txn`, `etcdctl txn [-i]`, `clientv3.KV.Txn(ctx).If(...).Then(...).Else(...).Commit()` |
| Requires | — |
| Enabled by | — |
| Changes state | keys, revisions |
| Reads state | keys, revisions, leases, alarms |
| Related | `kv.put`, `kv.range`, `kv.delete_range` |
| Code locations | `server/etcdserver/api/v3rpc/key.go:kvServer.Txn`, `server/etcdserver/v3_server.go:EtcdServer.Txn`, `server/etcdserver/txn/txn.go:Txn` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| compare | list of Compare | Each has a non-empty key, an optional range_end (3.3+), a result (EQUAL, GREATER, LESS, NOT_EQUAL) and a target (VERSION, CREATE, MOD, VALUE, LEASE) with a matching value. An empty list means the comparison is true |
| success | list of RequestOp | Run if all compares hold. Each op is range, put, delete_range or nested txn; an empty or nil op returns `ErrGRPCKeyNotFound` |
| failure | list of RequestOp | Run otherwise |
| (count limit) | — | max(len(compare), len(success), len(failure)) must be <= `--max-txn-ops` (default 128), and nested txns share the remaining budget. Otherwise `ErrGRPCTooManyOps`. Whole request must fit in `--max-request-bytes` (default 1.5 MiB) |

### `kv.range_stream`: Range stream

- **What it does:** Same request as Range, but the server sends the results as a stream of chunks instead of one response. Each chunk's size adapts toward `--max-request-bytes`. The whole stream reads at one pinned revision, and the last chunk carries the header, `more` and the total `count`.
- **Tier reason:** A gRPC-only streaming variant of Range: same `RangeRequest`, same auth check and linearizable/serializable path. Exposed as top-level `clientv3.KV.GetStream` (`client/v3/kv.go`) and `etcdctl get --stream`; the "Read keys" section of https://etcd.io/docs/v3.8/dev-guide/interacting_v3/ shows `etcdctl get --stream --prefix foo` and says the result matches a unary Range.
- **Notes:** No HTTP gateway mapping, on purpose (see the comment on `rpc RangeStream` in `api/etcdserverpb/rpc.proto`). Requests with a custom sort order or any min/max revision filter are rejected with `Unimplemented` (`checkRangeStreamRequest`). `count_only` sends a single chunk. If revision is 0, the server pins it to the store revision when the stream starts, so later writes do not show up in later chunks. The first chunk asks for 10 keys (`initialStreamChunkLimit`); after that the per-chunk limit doubles or halves. `clientv3.GetStreamToGetResponse` merges the chunks back into one GetResponse.
- **Uncertain:** Could count as its own feature (new streaming transport, separate RPC) instead of a Tier 1 variant. Kept at Tier 1 because it uses the same request type, the same read path and the same result, and is documented as a flag on `etcdctl get`.

| Field | Value |
|---|---|
| ID | `kv.range_stream` |
| Tier | 1 |
| Feature group | — |
| Kind | data |
| How to call | `etcdserverpb.KV/RangeStream` (server-streaming, gRPC only, no HTTP gateway), `etcdctl get --stream <key> [--prefix\|--from-key\|--rev\|--limit\|--keys-only\|--count-only]`, `clientv3.KV.GetStream` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | keys, revisions, compaction |
| Related | `kv.range`, `kv.put`, `kv.delete_range`, `kv.compact` |
| Code locations | `server/etcdserver/api/v3rpc/key.go:kvServer.RangeStream`, `server/etcdserver/v3_server.go:EtcdServer.RangeStream`, `server/etcdserver/v3_server.go:EtcdServer.rangeStream` |
| Confidence | low |

| Input | Type | Limits and notes |
|---|---|---|
| key | bytes | Must be non-empty |
| range_end | bytes | Same meaning as Range (empty, `\x00`, prefix) |
| limit | int64 | 0 = no limit (total across all chunks). First chunk is 10 keys, then adjusts toward `--max-request-bytes` (default 1.5 MiB) |
| revision | int64 | 0 = pinned to the current revision when the stream starts; must not be compacted or in the future |
| serializable | bool | Default false (linearizable) |
| keys_only | bool | Default false |
| count_only | bool | Default false; one chunk with the count only |
| sort_order / sort_target | enum | Only the default ordering is allowed; anything else returns `Unimplemented` |
| min/max mod/create revision | int64 | Must be 0; any filter returns `Unimplemented` |

### `kv.compact`: Compact

- **What it does:** Throws away key history older than the given revision. Afterwards, reads and watches at earlier revisions fail with `required revision has been compacted`. The latest version of each live key is kept. With `physical=true`, the call waits until the old entries are actually removed from the backend.
- **Tier reason:** Top-level method on the main KV interface (`clientv3.KV.Compact` in `client/v3/kv.go`), in the `KV` gRPC service, and covered in the "Compacted revisions" section of https://etcd.io/docs/v3.8/dev-guide/interacting_v3/. Also `etcdctl compaction` (the docs examples write `etcdctl compact`).
- **Notes:** Kind is `data` because it changes which revisions of user keys can be read (`revisions`, `compaction`), not cluster configuration. However, when auth is on it needs admin (root) permission (`AuthAdmin.isPermitted` in `kvServer.Compact`). Goes through raft; the actual deletion runs in the background in batches (`--compaction-batch-limit`, `--compaction-sleep-interval`). Operators mostly rely on auto-compaction (`--auto-compaction-mode` periodic|revision, `--auto-compaction-retention`, default "0" = off), which calls the same apply path. https://etcd.io/docs/v3.8/op-guide/maintenance/ ("History compaction") pairs compaction with defrag to reclaim disk space.
- **Uncertain:** Tier 1 (top-level KV method, shown in the dev guide) vs. Tier 3 (presented mainly as a maintenance task in the op-guide, and admin-only under auth). Also `data` vs. `admin`: it acts on user-key history, but needs admin permission when auth is on (`AuthAdmin.isPermitted`).

| Field | Value |
|---|---|
| ID | `kv.compact` |
| Tier | 1 |
| Feature group | — |
| Kind | data |
| How to call | `etcdserverpb.KV/Compact`, `POST /v3/kv/compaction`, `etcdctl compaction <rev> [--physical]`, `clientv3.KV.Compact(ctx, rev, clientv3.WithCompactPhysical())` |
| Requires | — |
| Enabled by | — |
| Changes state | compaction, revisions |
| Reads state | revisions, compaction, auth_status, users, roles |
| Related | `kv.range`, `kv.range_stream`, `kv.put`, `kv.txn`, `kv.delete_range` |
| Code locations | `server/etcdserver/api/v3rpc/key.go:kvServer.Compact`, `server/etcdserver/v3_server.go:EtcdServer.Compact`, `server/storage/mvcc/kvstore.go:store.Compact` |
| Confidence | low |

| Input | Type | Limits and notes |
|---|---|---|
| revision | int64 | Must be above the current compaction revision (otherwise `ErrCompacted`) and at most the current revision (otherwise `ErrFutureRev`) |
| physical | bool | Default false; true waits for the backend to finish removing old revisions (`--physical`) |

## Tier 2: Features

### `watch.create`: Watch create

- **What it does:** Opens a watcher on a key, key range, or prefix in a bidirectional watch stream. The server then streams put and delete events from `start_revision`, or from the next revision if none is given, until the watcher is canceled.
- **Tier reason:** Has its own task page (https://etcd.io/docs/v3.8/tasks/developer/how-to-watch-keys/) and sections in dev-guide/interacting_v3/ ("Watch key changes", "Watch historical changes of keys"). It is a top-level client interface, `clientv3.Watcher.Watch` (client/v3/watch.go), embedded in `clientv3.Client`. It also has its own `etcdctl watch` command (etcdctl/ctlv3/command/watch_command.go). Subscriptions are a new concept beyond plain KV.
- **Notes:** `watch.create`, `watch.cancel`, and `watch.progress` are separate request types (`WatchCreateRequest`, `WatchCancelRequest`, `WatchProgressRequest`) in the `oneof` of `WatchRequest`, all sent on the one `Watch` stream RPC. They are split here because each has its own branch in `serverWatchStream.recvLoop` (server/etcdserver/api/v3rpc/watch.go). One gRPC stream can hold many watchers. The clientv3 client multiplexes watches that share the same ctx metadata onto one stream.

  Creation is asynchronous. The server answers with `created=true` and the assigned `watch_id`. A start_revision older than the compacted revision returns `canceled=true` with `compact_revision` set. A negative start_revision is answered as canceled with `ErrCompacted`. If auth is enabled, the watcher is checked for read permission on the range, and a failure comes back as a canceled response with a reason.

  Events from a txn come out in one response, which is split only when `fragment` is set. A watch on a range that has no writes is valid but emits nothing, so this operation is useful only together with writes. Common usage: watch a prefix from `header.revision+1` after a range read (the informer/list-watch pattern used by Kubernetes).
- **Notes (dependency):** No operation is strictly required first: a watch on an empty range is created successfully and only emits events once `kv.put`, `kv.delete_range`, `kv.txn`, or `lease.revoke` change keys.

| Field | Value |
|---|---|
| ID | `watch.create` |
| Tier | 2 |
| Feature group | `watch` |
| Kind | data |
| How to call | `etcdserverpb.Watch/Watch` bidi stream with `WatchRequest.create_request` (HTTP gateway `POST /v3/watch`), `etcdctl watch [--prefix] [--rev] [--prev-kv] [--progress-notify] key [range_end]`, `clientv3.Watcher.Watch(ctx, key, opts...)` |
| Requires | — |
| Enabled by | — |
| Changes state | watchers |
| Reads state | keys, revisions, compaction |
| Related | `watch.cancel`, `watch.progress`, `kv.put`, `kv.delete_range`, `kv.txn`, `kv.compact`, `lease.revoke` |
| Code locations | `server/etcdserver/api/v3rpc/watch.go:serverWatchStream.recvLoop`, `server/storage/mvcc/watcher.go:watchStream.Watch`, `server/storage/mvcc/watchable_store.go:watchableStore.watch` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| key | bytes | Empty becomes `\x00`, the smallest key. clientv3 `WithPrefix` / `WithFromKey` set range_end. |
| range_end | bytes | Empty means single key. `\x00` means all keys >= key. key+1 (prefix end) means prefix. `key >= range_end` is rejected with `mvcc: watcher range is empty`, returned as a canceled create response. |
| start_revision | int64 | 0 means "now" (watches from current rev+1). Inclusive. Below the compacted revision gives a canceled watcher with `compact_revision`. Negative is rejected as compacted. A future revision is allowed: the watcher waits. clientv3 `WithRev`. |
| progress_notify | bool | Server sends empty progress responses on idle watchers every `--watch-progress-notify-interval` (default 10m, minimum 100ms). clientv3 `WithProgressNotify`. etcdctl `--progress-notify`. |
| filters | enum list | `NOPUT`, `NODELETE`. Drop those event types server-side. clientv3 `WithFilterPut` / `WithFilterDelete`. |
| prev_kv | bool | Include the previous KV in each event. Nothing is returned if the previous KV is compacted. clientv3 `WithPrevKV`. etcdctl `--prev-kv`. |
| watch_id | int64 | 0 = auto-assign (the clientv3 `AutoWatchID`). A non-zero value already in use on the stream fails with `mvcc: duplicate watch ID provided on the WatchStream`. Not exposed by clientv3 `Watch`. |
| fragment | bool | Split a revision's events across several responses when the response exceeds `--max-request-bytes` (default 1.5 MiB) + 512 KiB gRPC overhead. Only splits when there are 2+ events. clientv3 `WithFragment`. |

### `watch.cancel`: Watch cancel

- **What it does:** Cancels one watcher on a watch stream by `watch_id`. The server replies with `canceled=true` and sends no more events for that ID.
- **Tier reason:** Part of the watch feature. `WatchCancelRequest` is in rpc.proto. In clientv3 it is not a separate method: canceling the ctx passed to `clientv3.Watcher.Watch`, or calling `Watcher.Close`, makes the client send `WatchCancelRequest` (client/v3/watch.go `watchGRPCStream.run`, `closingc` branch). Not covered on the docs task pages.
- **Notes:** Own handler branch in `serverWatchStream.recvLoop`. Canceling an unknown ID is silently ignored, with no response. clientv3 also sends a cancel by itself when it gets events for a watch ID it does not know. Closing the whole gRPC stream cancels all its watchers through `watchStream.Close`. Watchers can also be canceled by the server, for example on compaction, without this request.

| Field | Value |
|---|---|
| ID | `watch.cancel` |
| Tier | 2 |
| Feature group | `watch` |
| Kind | data |
| How to call | `etcdserverpb.Watch/Watch` stream with `WatchRequest.cancel_request` (HTTP gateway `POST /v3/watch`), clientv3: cancel the `Watch` ctx or `clientv3.Watcher.Close()`, etcdctl: interrupt `etcdctl watch` |
| Requires | `watch.create` |
| Enabled by | — |
| Changes state | watchers |
| Reads state | watchers |
| Related | `watch.create`, `watch.progress` |
| Code locations | `server/etcdserver/api/v3rpc/watch.go:serverWatchStream.recvLoop`, `server/storage/mvcc/watcher.go:watchStream.Cancel`, `server/storage/mvcc/watchable_store.go:watchableStore.cancelWatcher` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| watch_id | int64 | ID from the create response. An unknown or already canceled ID gets no response. |

### `watch.progress`: Watch progress request

- **What it does:** Asks the server to send, as soon as it can, a progress notification on the stream: an event-less `WatchResponse` whose header revision tells the client that all events up to that revision have been delivered.
- **Tier reason:** Section "Watch progress" in https://etcd.io/docs/v3.8/dev-guide/interacting_v3/. Method on the top-level interface, `clientv3.Watcher.RequestProgress` (client/v3/watch.go). Typed as `progress` in `etcdctl watch -i` interactive mode (etcdctl/ctlv3/command/watch_command.go). Only meaningful with an open watch stream.
- **Notes:** A separate request type in the same `Watch` stream RPC, with its own branch in `recvLoop` that calls `watchStream.RequestProgressAll`. A notification is sent only if every watcher on the stream is synced (`watchableStore.progressIfSync`). Otherwise it is deferred and resent later by the send loop. The response has `watch_id = -1` (InvalidWatchID), and clientv3 broadcasts it to all watch channels on that stream. Added in v3.4. Used by Kubernetes for consistent reads from its watch cache.

| Field | Value |
|---|---|
| ID | `watch.progress` |
| Tier | 2 |
| Feature group | `watch` |
| Kind | data |
| How to call | `etcdserverpb.Watch/Watch` stream with `WatchRequest.progress_request` (HTTP gateway `POST /v3/watch`), `clientv3.Watcher.RequestProgress(ctx)`, `etcdctl watch -i` then `progress` |
| Requires | `watch.create` |
| Enabled by | — |
| Changes state | — |
| Reads state | watchers, revisions |
| Related | `watch.create`, `watch.cancel` |
| Code locations | `server/etcdserver/api/v3rpc/watch.go:serverWatchStream.recvLoop`, `server/storage/mvcc/watcher.go:watchStream.RequestProgressAll`, `server/storage/mvcc/watchable_store.go:watchableStore.progressIfSync` |
| Confidence | high |

No inputs.

### `lease.grant`: Lease grant

- **What it does:** Creates a lease with a TTL in seconds and returns its ID. Keys attached to the lease (through `kv.put` with `lease`) are deleted when the lease expires or is revoked.
- **Tier reason:** Own task page (https://etcd.io/docs/v3.8/tasks/developer/how-to-create-lease/) and section "Grant leases" in dev-guide/interacting_v3/. Top-level interface method `clientv3.Lease.Grant` (client/v3/lease.go). `etcdctl lease grant` (etcdctl/ctlv3/command/lease_command.go). Introduces leases as a new concept.
- **Notes:** Goes through raft (`InternalRaftRequest.LeaseGrant`). An ID of 0 makes the server pick a positive random ID. The granted TTL in the response may be larger than requested because of the minimum TTL. On followers the lease is held "forever" until promotion; only the leader (the primary lessor) expires leases. Lease expiry runs on its own in the background (the leader's `lessor.revokeExpiredLeases` proposes revokes). There is no separate API call for it. Attaching keys is done with `kv.put` `lease=`.

| Field | Value |
|---|---|
| ID | `lease.grant` |
| Tier | 2 |
| Feature group | `lease` |
| Kind | data |
| How to call | `etcdserverpb.Lease/LeaseGrant` (HTTP gateway `POST /v3/lease/grant`), `etcdctl lease grant <ttl>`, `clientv3.Lease.Grant(ctx, ttl)` |
| Requires | — |
| Enabled by | — |
| Changes state | leases |
| Reads state | leases |
| Related | `lease.revoke`, `lease.keepalive`, `lease.timetolive`, `lease.list`, `kv.put` |
| Code locations | `server/etcdserver/api/v3rpc/lease.go:LeaseServer.LeaseGrant`, `server/etcdserver/v3_server.go:EtcdServer.LeaseGrant`, `server/lease/lessor.go:lessor.Grant` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| TTL | int64 (seconds) | Raised to the minimum TTL = ceil(1.5 × election timeout). Default election timeout is 1000 ms (10 ticks × 100 ms heartbeat), so the minimum is 2 s. Max `MaxLeaseTTL` = 9,000,000,000 s. Above that returns `etcdserver: too large lease TTL` (OutOfRange). Can be rejected under `NOSPACE` alarm (quota applier). |
| ID | int64 | 0 = server-chosen positive ID. If the ID is already in use, returns `etcdserver: lease already exists`. clientv3 `Grant` does not expose it, so set it via raw gRPC or `etcdctl` (not exposed either). |

### `lease.revoke`: Lease revoke

- **What it does:** Revokes a lease right away and deletes every key attached to it in the same backend transaction. Each deleted key produces a delete event.
- **Tier reason:** On https://etcd.io/docs/v3.8/tasks/developer/how-to-create-lease/ and in "Revoke leases" in dev-guide/interacting_v3/. `clientv3.Lease.Revoke`. `etcdctl lease revoke`.
- **Notes:** Goes through raft (`InternalRaftRequest.LeaseRevoke`). Keys are deleted in sorted order, so the deletes are the same on every member. A lease that does not exist gives `etcdserver: requested lease not found`. If auth is enabled, the caller needs write permission on all attached keys (`authApplierV3.LeaseRevoke` via `checkLeasePuts`). The same effect happens on its own when the TTL expires without keep-alive.

| Field | Value |
|---|---|
| ID | `lease.revoke` |
| Tier | 2 |
| Feature group | `lease` |
| Kind | data |
| How to call | `etcdserverpb.Lease/LeaseRevoke` (HTTP gateway `POST /v3/lease/revoke`, also `POST /v3/kv/lease/revoke`), `etcdctl lease revoke <leaseID>`, `clientv3.Lease.Revoke(ctx, id)` |
| Requires | `lease.grant` |
| Enabled by | — |
| Changes state | leases, keys, revisions |
| Reads state | leases |
| Related | `lease.grant`, `lease.keepalive`, `lease.timetolive`, `lease.list`, `kv.put`, `kv.delete_range`, `watch.create` |
| Code locations | `server/etcdserver/api/v3rpc/lease.go:LeaseServer.LeaseRevoke`, `server/etcdserver/v3_server.go:EtcdServer.LeaseRevoke`, `server/lease/lessor.go:lessor.Revoke` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| ID | int64 | Must be an existing lease. Otherwise returns NotFound. |

### `lease.keepalive`: Lease keep-alive

- **What it does:** Renews a lease's TTL back to its granted value. Runs over a bidi stream: each `LeaseKeepAliveRequest{ID}` gets a response with the new TTL, or TTL 0 if the lease is not found.
- **Tier reason:** On https://etcd.io/docs/v3.8/tasks/developer/how-to-create-lease/ and in "Keep leases alive" in dev-guide/interacting_v3/. `clientv3.Lease.KeepAlive` / `KeepAliveOnce`. `etcdctl lease keep-alive [--once]`.
- **Notes:** Renewals do not go through raft. A follower forwards them to the leader over the peer HTTP lease endpoint (`leasehttp.RenewHTTP`). On the leader, `EtcdServer.LeaseRenew` first confirms leadership. When the `FastLeaseKeepAlive` feature gate (Beta, default true, server/features/etcd_features.go) is on, it waits for the applied index only if the lease is not found locally. With the gate off, it always waits. The `LeaseCheckpoint` gate (Alpha, default off) makes a renew propose a checkpoint that clears remaining TTL. clientv3 `KeepAlive` sends a request every TTL/3 and buffers 16 responses (`LeaseResponseChSize`). Renewing an expired lease that is pending revoke waits for the revoke and then reports not found.

| Field | Value |
|---|---|
| ID | `lease.keepalive` |
| Tier | 2 |
| Feature group | `lease` |
| Kind | data |
| How to call | `etcdserverpb.Lease/LeaseKeepAlive` bidi stream (HTTP gateway `POST /v3/lease/keepalive`), `etcdctl lease keep-alive [--once] <leaseID>`, `clientv3.Lease.KeepAlive(ctx, id)` / `clientv3.Lease.KeepAliveOnce(ctx, id)` |
| Requires | `lease.grant` |
| Enabled by | — |
| Changes state | leases |
| Reads state | leases, leader |
| Related | `lease.grant`, `lease.revoke`, `lease.timetolive` |
| Code locations | `server/etcdserver/api/v3rpc/lease.go:LeaseServer.leaseKeepAlive`, `server/etcdserver/v3_server.go:EtcdServer.LeaseRenew`, `server/lease/lessor.go:lessor.Renew` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| ID | int64 | A missing or expired lease returns a response with TTL 0, not an error. clientv3 then closes the KeepAlive channel. If auth is enabled, the caller needs permission on the lease's keys (`checkLeaseRenew`). |

### `lease.timetolive`: Lease time-to-live

- **What it does:** Returns a lease's remaining TTL and granted TTL, and optionally the keys attached to it.
- **Tier reason:** Section "Get lease information" in https://etcd.io/docs/v3.8/dev-guide/interacting_v3/. `clientv3.Lease.TimeToLive` with `clientv3.WithAttachedKeys()`. `etcdctl lease timetolive [--keys]`.
- **Notes:** Answered by the leader after waiting for the applied index. Followers forward the call to the leader. A lease that does not exist returns TTL -1 rather than an error (`LeaseServer.LeaseTimeToLive`). If the leader changes during the lookup, returns `ErrLeaderChanged`. The RBAC check (read on the attached keys) runs only when `keys=true`.

| Field | Value |
|---|---|
| ID | `lease.timetolive` |
| Tier | 2 |
| Feature group | `lease` |
| Kind | data |
| How to call | `etcdserverpb.Lease/LeaseTimeToLive` (HTTP gateway `POST /v3/lease/timetolive`, also `POST /v3/kv/lease/timetolive`), `etcdctl lease timetolive [--keys] <leaseID>`, `clientv3.Lease.TimeToLive(ctx, id, clientv3.WithAttachedKeys())` |
| Requires | `lease.grant` |
| Enabled by | — |
| Changes state | — |
| Reads state | leases, keys |
| Related | `lease.grant`, `lease.keepalive`, `lease.revoke`, `lease.list`, `kv.put` |
| Code locations | `server/etcdserver/api/v3rpc/lease.go:LeaseServer.LeaseTimeToLive`, `server/etcdserver/v3_server.go:EtcdServer.LeaseTimeToLive`, `server/etcdserver/v3_server.go:EtcdServer.leaseTimeToLive` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| ID | int64 | A missing lease returns TTL -1. |
| keys | bool | Default false. When true, returns the attached keys and checks RBAC read permission on them. |

### `lease.list`: Lease list

- **What it does:** Lists the IDs of all current leases.
- **Tier reason:** Part of the lease feature: `clientv3.Lease.Leases` (client/v3/lease.go) and `etcdctl lease list`. Not on the docs task pages or in interacting_v3.
- **Notes:** Served from the local lessor's in-memory map without raft or a linearizable wait (`EtcdServer.LeaseLeases`); it reflects the serving member's lessor. If auth is enabled, the caller needs either admin permission or read permission on every key attached to every lease (`checkLeaseLeases`). The response holds only IDs. TTL is a TODO in the proto. Added in v3.3. The code comment calls it "really ListLeases".

| Field | Value |
|---|---|
| ID | `lease.list` |
| Tier | 2 |
| Feature group | `lease` |
| Kind | data |
| How to call | `etcdserverpb.Lease/LeaseLeases` (HTTP gateway `POST /v3/lease/leases`, also `POST /v3/kv/lease/leases`), `etcdctl lease list`, `clientv3.Lease.Leases(ctx)` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | leases |
| Related | `lease.grant`, `lease.revoke`, `lease.timetolive` |
| Code locations | `server/etcdserver/api/v3rpc/lease.go:LeaseServer.LeaseLeases`, `server/etcdserver/v3_server.go:EtcdServer.LeaseLeases`, `server/lease/lessor.go:lessor.Leases` |
| Confidence | high |

No inputs.

### `lock.lock`: Lock

- **What it does:** Acquires a named distributed lock. It blocks until the caller holds the lock, then returns an ownership key (`{name}/{leaseID-hex}`). The key exists, attached to the lease, for as long as the caller holds the lock.
- **Tier reason:** Separate gRPC service `v3lockpb.Lock` (registered in `server/embed/serve.go`), not part of the core KV/Lease/Watch API. Documented on its own pages: https://etcd.io/docs/v3.8/dev-guide/api_concurrency_reference_v3/ and tasks/developer/how-to-create-locks/. Adds a new concept (lock ownership by queue of lease-bound keys).
- **Notes:** The handler is a thin wrapper over `concurrency.NewMutex(...).Lock` running inside the server through an in-process client (`v3client`). It does not use a separate store. It writes and watches ordinary keys under the `{name}/` prefix with a Txn plus Get/Watch on that prefix. The server does not keep the session lease alive; the caller's lease governs how long the lock is held. With `lease=0` the server grants a 60 s lease (`defaultSessionTTL`) and the lock is held until it expires. Calling Lock twice with the same lease is a no-op and returns the same key. The call stays blocked while others hold the lock, until the client's context is canceled or its deadline passes. If waiting fails, the server deletes the waiter key. `etcdctl lock` does NOT call this RPC: it uses `client/v3/concurrency.Mutex` directly on the client side (with `--ttl`, default 10). The gRPC proxy (`server/proxy/grpcproxy/lock.go`) passes the call through.
- **Notes (dependency):** A lease is not mandatory: with `lease=0` the server creates a 60 s session lease itself (`client/v3/concurrency/session.go:NewSession`) and does not keep it alive, so typical use passes a lease from `lease.grant` kept alive with `lease.keepalive`.

| Field | Value |
|---|---|
| ID | `lock.lock` |
| Tier | 2 |
| Feature group | `lock` |
| Kind | data |
| How to call | `v3lockpb.Lock/Lock`, `POST /v3/lock/lock`, `v3lockpb.NewLockClient(conn).Lock()`; client-side equivalent `etcdctl lock <name>` / `concurrency.Mutex.Lock` |
| Requires | — |
| Enabled by | — |
| Changes state | locks, keys, leases |
| Reads state | locks, keys, leases |
| Related | `lock.unlock`, `lease.grant` |
| Code locations | `server/etcdserver/api/v3lock/lock.go:lockServer.Lock`, `client/v3/concurrency/mutex.go:Mutex.Lock`, `client/v3/concurrency/session.go:NewSession` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | bytes | Lock prefix. The server appends `/`, so the ownership key is `{name}/{lease-hex}`. Empty is allowed (key prefix `/`). The whole request is bounded by `--max-request-bytes` (default 1.5 MiB) |
| lease | int64 | ID of an existing lease. 0 = the server grants a 60 s lease and never refreshes it. A nonexistent or expired lease ID fails the put (lease not found). Reusing a lease that already holds or waits on the lock is a no-op |

### `lock.unlock`: Unlock

- **What it does:** Releases a lock by deleting the ownership key that Lock returned. This wakes the next waiter, which is the key with the next-lowest create revision under the prefix.
- **Tier reason:** Pairs with `lock.lock` in `v3lockpb.Lock`. Documented on https://etcd.io/docs/v3.8/dev-guide/api_concurrency_reference_v3/.
- **Notes:** The server deletes the given ownership key with `client.Delete(key)`. Unlocking a key that is already gone succeeds. The lock is also released, without Unlock, when the lease is revoked or expires (see `lease.grant`).

| Field | Value |
|---|---|
| ID | `lock.unlock` |
| Tier | 2 |
| Feature group | `lock` |
| Kind | data |
| How to call | `v3lockpb.Lock/Unlock`, `POST /v3/lock/unlock`, `v3lockpb.NewLockClient(conn).Unlock()`; client-side equivalent `concurrency.Mutex.Unlock` (etcdctl lock releases on exit) |
| Requires | `lock.lock` |
| Enabled by | — |
| Changes state | locks, keys |
| Reads state | — |
| Related | `lock.lock` |
| Code locations | `server/etcdserver/api/v3lock/lock.go:lockServer.Unlock` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| key | bytes | Ownership key returned by `lock.lock`. Empty key gives the KV "key is not provided" error |

### `election.campaign`: Campaign

- **What it does:** Joins the election `name` with the initial value `value`. It blocks until the caller becomes leader, then returns a `LeaderKey` (name, key `{name}/{lease-hex}`, creation rev, lease).
- **Tier reason:** Separate gRPC service `v3electionpb.Election` (registered in `server/embed/serve.go`). Documented on https://etcd.io/docs/v3.8/dev-guide/api_concurrency_reference_v3/ and tasks/operator/how-to-conduct-elections/. Adds the leader-election concept.
- **Notes:** Thin wrapper over `concurrency.NewElection(...).Campaign`; the server does not keep the session lease alive, so the caller's lease governs leadership. With `lease=0` the server grants a 60 s lease. Campaign is a Txn that puts the key only if absent. If the key already exists (same lease), Campaign reuses it and proclaims the new value if it differs. Then it waits for all keys with a lower create revision under the prefix to be deleted. If the context is canceled, Campaign resigns. `etcdctl elect <name> <proposal>` runs the same logic client-side through `concurrency.Election`, not this RPC.
- **Notes (dependency):** A lease is not mandatory: with `lease=0` the server creates a 60 s session lease itself (`client/v3/concurrency/session.go:NewSession`) and does not keep it alive, so typical use passes a lease from `lease.grant` kept alive with `lease.keepalive`.

| Field | Value |
|---|---|
| ID | `election.campaign` |
| Tier | 2 |
| Feature group | `election` |
| Kind | data |
| How to call | `v3electionpb.Election/Campaign`, `POST /v3/election/campaign`, `v3electionpb.NewElectionClient(conn).Campaign()`; client-side equivalent `etcdctl elect <name> <proposal>` / `concurrency.Election.Campaign` |
| Requires | — |
| Enabled by | — |
| Changes state | elections, keys, leases |
| Reads state | elections, keys, leases |
| Related | `election.proclaim`, `election.resign`, `election.leader`, `election.observe`, `lease.grant` |
| Code locations | `server/etcdserver/api/v3election/election.go:electionServer.Campaign`, `client/v3/concurrency/election.go:Election.Campaign` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | bytes | Election prefix. The server appends `/`. Bounded by `--max-request-bytes` (default 1.5 MiB) |
| lease | int64 | Lease bound to leadership. 0 = the server grants a 60 s lease, never refreshed. Leadership passes to the next campaigner when the lease expires or is revoked |
| value | bytes | Initial proclaimed value. Bounded by `--max-request-bytes` (default 1.5 MiB) |

### `election.proclaim`: Proclaim

- **What it does:** Updates the current leader's value without a new election. The leader key is overwritten only if its create revision still equals `leader.rev`.
- **Tier reason:** Part of `v3electionpb.Election`, documented on https://etcd.io/docs/v3.8/dev-guide/api_concurrency_reference_v3/.
- **Notes:** Needs the full `LeaderKey` from Campaign. Without one it returns `"leader" field must be provided`. If the key was deleted or recreated (for example, the lease expired), it returns `election: not leader`. The put reattaches `leader.lease`.

| Field | Value |
|---|---|
| ID | `election.proclaim` |
| Tier | 2 |
| Feature group | `election` |
| Kind | data |
| How to call | `v3electionpb.Election/Proclaim`, `POST /v3/election/proclaim`, `v3electionpb.NewElectionClient(conn).Proclaim()`; client-side equivalent `concurrency.Election.Proclaim` |
| Requires | `election.campaign` |
| Enabled by | — |
| Changes state | elections, keys |
| Reads state | elections, keys, leases |
| Related | `election.campaign`, `election.leader`, `election.observe` |
| Code locations | `server/etcdserver/api/v3election/election.go:electionServer.Proclaim`, `client/v3/concurrency/election.go:Election.Proclaim` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| leader | LeaderKey {name, key, rev, lease} | Required. From the CampaignResponse. `rev` must match the key's create revision. `lease` must be a live lease (nonzero, or the server grants a new one and the put uses it) |
| value | bytes | New value. Bounded by `--max-request-bytes` (default 1.5 MiB) |

### `election.leader`: Leader

- **What it does:** Returns the current leader's key-value: the key under `{name}/` with the lowest create revision.
- **Tier reason:** Part of `v3electionpb.Election`, documented on https://etcd.io/docs/v3.8/dev-guide/api_concurrency_reference_v3/.
- **Notes:** Read-only: a single ranged Get with `WithFirstCreate`. Returns `election: no leader` if no key exists under the prefix. Because the server creates the session with lease -1, it never grants a lease for this call.

| Field | Value |
|---|---|
| ID | `election.leader` |
| Tier | 2 |
| Feature group | `election` |
| Kind | data |
| How to call | `v3electionpb.Election/Leader`, `POST /v3/election/leader`, `v3electionpb.NewElectionClient(conn).Leader()`; client-side equivalent `concurrency.Election.Leader` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | elections, keys |
| Related | `election.campaign`, `election.proclaim`, `election.observe`, `election.resign` |
| Code locations | `server/etcdserver/api/v3election/election.go:electionServer.Leader`, `client/v3/concurrency/election.go:Election.Leader` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | bytes | Election prefix (the server appends `/`) |

### `election.observe`: Observe

- **What it does:** Server stream that sends the current leader's value, then each later proclamation, and then each new leader in turn as leadership changes.
- **Tier reason:** Part of `v3electionpb.Election`, documented on https://etcd.io/docs/v3.8/dev-guide/api_concurrency_reference_v3/.
- **Notes:** Built from a Get plus Watch on the election prefix, then a Watch on the leader key. If there is no leader, it waits for the first put. It does not promise to send every historical update, only the latest value. The stream ends when the client context ends or the inner watch closes. `etcdctl elect -l <name>` gives the same behavior client-side. Session uses lease -1, so no lease is granted.

| Field | Value |
|---|---|
| ID | `election.observe` |
| Tier | 2 |
| Feature group | `election` |
| Kind | data |
| How to call | `v3electionpb.Election/Observe` (server stream), `POST /v3/election/observe` (gateway streaming), `v3electionpb.NewElectionClient(conn).Observe()`; client-side equivalent `etcdctl elect -l <name>` / `concurrency.Election.Observe` |
| Requires | — |
| Enabled by | — |
| Changes state | watchers |
| Reads state | elections, keys |
| Related | `election.campaign`, `election.proclaim`, `election.resign`, `election.leader` |
| Code locations | `server/etcdserver/api/v3election/election.go:electionServer.Observe`, `client/v3/concurrency/election.go:Election.observe` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | bytes | Election prefix (the server appends `/`) |

### `election.resign`: Resign

- **What it does:** Gives up leadership (or a pending campaign) by deleting the leader key, but only if its create revision still equals `leader.rev`. The next campaigner then becomes leader.
- **Tier reason:** Part of `v3electionpb.Election`, documented on https://etcd.io/docs/v3.8/dev-guide/api_concurrency_reference_v3/.
- **Notes:** Needs the `LeaderKey`, or it returns `"leader" field must be provided`. Deletes the leader key only if its create revision matches the given `LeaderKey`. Does not revoke the lease.

| Field | Value |
|---|---|
| ID | `election.resign` |
| Tier | 2 |
| Feature group | `election` |
| Kind | data |
| How to call | `v3electionpb.Election/Resign`, `POST /v3/election/resign`, `v3electionpb.NewElectionClient(conn).Resign()`; client-side equivalent `concurrency.Election.Resign` (etcdctl elect resigns on interrupt) |
| Requires | `election.campaign` |
| Enabled by | — |
| Changes state | elections, keys |
| Reads state | elections, keys |
| Related | `election.campaign`, `election.leader`, `election.observe` |
| Code locations | `server/etcdserver/api/v3election/election.go:electionServer.Resign`, `client/v3/concurrency/election.go:Election.Resign` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| leader | LeaderKey {name, key, rev, lease} | Required. From the CampaignResponse. `rev` must match the key's create revision for the delete to happen |

## Tier 3: Specialized

### `member.add`: Member add

- **What it does:** Proposes a raft configuration change that adds a new member (voting, or a non-voting learner when `isLearner` is set) with the given peer URLs, and returns the new member ID plus the full member list. The new etcd process must then be started with `--initial-cluster-state=existing`.
- **Tier reason:** Only in the operator docs (https://etcd.io/docs/v3.8/op-guide/runtime-configuration/, https://etcd.io/docs/v3.8/learning/design-learner/); lives on the `clientv3.Cluster` sub-interface (`MemberAdd`, `MemberAddAsLearner`) and `etcdctl member add`, not on the top-level KV client.
- **Notes:** With `--strict-reconfig-check` (default true) a voting add is rejected with `ErrNotEnoughStartedMembers` if started members would fall below quorum, or `ErrUnhealthy` if the local member is not connected to a quorum (`EtcdServer.mayAddMember`). Learner adds skip the started-members check. Apply-time validation (`RaftCluster.ValidateConfigurationChange`) rejects reused IDs, duplicate peer URLs (`ErrPeerURLexists`), removed IDs, and learner adds beyond `--max-learners`. Requires root/admin when auth is enabled (`checkMembershipOperationPermission`). The operator docs recommend adding new members as learners first and promoting after they catch up.

| Field | Value |
|---|---|
| ID | `member.add` |
| Tier | 3 |
| Feature group | `membership` |
| Kind | admin |
| How to call | `etcdserverpb.Cluster/MemberAdd`, `POST /v3/cluster/member/add`, `etcdctl member add <name> --peer-urls=... [--learner]`, `clientv3.Cluster.MemberAdd` / `MemberAddAsLearner` |
| Requires | — |
| Enabled by | — |
| Changes state | members |
| Reads state | members |
| Related | `member.promote`, `member.remove`, `member.update`, `member.list` |
| Code locations | `server/etcdserver/api/v3rpc/member.go:ClusterServer.MemberAdd`, `server/etcdserver/server.go:EtcdServer.AddMember`, `server/etcdserver/api/membership/cluster.go:RaftCluster.AddMember` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| peerURLs | repeated string | Must parse as URLs (`types.NewURLs`, else `ErrGRPCMemberBadURLs`); must not be used by any existing member |
| isLearner | bool | Default false. Learner count capped by `--max-learners` (default 1); exceeding it returns `ErrTooManyLearners` |

### `member.promote`: Member promote

- **What it does:** Promotes a learner member to a voting member through a raft configuration change. Only the leader can judge whether the learner has caught up; a follower forwards the request to the leader over the peer HTTP API.
- **Tier reason:** Documented only in https://etcd.io/docs/v3.8/learning/design-learner/ and https://etcd.io/docs/v3.8/op-guide/runtime-configuration/; `clientv3.Cluster.MemberPromote` and `etcdctl member promote`.
- **Notes:** Rejected with `ErrLearnerNotReady` unless the learner's raft match index is at least 90% of the leader's (`readyPercentThreshold = 0.9`, `EtcdServer.isLearnerReady`). With `--strict-reconfig-check`, also rejected if promotion would leave started voters below quorum. Rejected with `ErrMemberNotLearner` if the target is already a voter. Requires admin when auth is enabled.

| Field | Value |
|---|---|
| ID | `member.promote` |
| Tier | 3 |
| Feature group | `membership` |
| Kind | admin |
| How to call | `etcdserverpb.Cluster/MemberPromote`, `POST /v3/cluster/member/promote`, `etcdctl member promote <memberID>`, `clientv3.Cluster.MemberPromote` |
| Requires | `member.add` |
| Enabled by | — |
| Changes state | members |
| Reads state | members, leader |
| Related | `member.add`, `member.remove`, `member.list` |
| Code locations | `server/etcdserver/api/v3rpc/member.go:ClusterServer.MemberPromote`, `server/etcdserver/server.go:EtcdServer.PromoteMember`, `server/etcdserver/api/membership/cluster.go:RaftCluster.PromoteMember` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| ID | uint64 | Must be an existing learner (`ErrIDNotFound`, `ErrMemberNotLearner`); learner must be at least 90% caught up to the leader |

### `member.remove`: Member remove

- **What it does:** Proposes a raft configuration change that removes a member by ID. The removed ID can never be reused, and a removed member shuts itself down.
- **Tier reason:** Operator docs only (https://etcd.io/docs/v3.8/op-guide/runtime-configuration/); `clientv3.Cluster.MemberRemove` and `etcdctl member remove`.
- **Notes:** With `--strict-reconfig-check` (default true), removing a voter is rejected if the remaining started voters would be below quorum, or if the active connected peers after removal would break quorum (`EtcdServer.mayRemoveMember`). Removing a learner or a member that has never connected skips the active-quorum check. A member can remove itself, including the leader. Requires admin when auth is enabled.

| Field | Value |
|---|---|
| ID | `member.remove` |
| Tier | 3 |
| Feature group | `membership` |
| Kind | admin |
| How to call | `etcdserverpb.Cluster/MemberRemove`, `POST /v3/cluster/member/remove`, `etcdctl member remove <memberID>`, `clientv3.Cluster.MemberRemove` |
| Requires | — |
| Enabled by | — |
| Changes state | members |
| Reads state | members |
| Related | `member.add`, `member.promote`, `member.update`, `member.list` |
| Code locations | `server/etcdserver/api/v3rpc/member.go:ClusterServer.MemberRemove`, `server/etcdserver/server.go:EtcdServer.RemoveMember`, `server/etcdserver/api/membership/cluster.go:RaftCluster.RemoveMember` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| ID | uint64 | Must be a current member (`ErrIDNotFound`); previously removed IDs return `ErrIDRemoved` |

### `member.update`: Member update

- **What it does:** Replaces a member's advertised peer URLs through a raft `ConfChangeUpdateNode`. It does not change client URLs or the member name; those are published by the member itself on startup.
- **Tier reason:** Operator docs only (https://etcd.io/docs/v3.8/op-guide/runtime-configuration/, "Update advertise peer URLs"); `clientv3.Cluster.MemberUpdate` and `etcdctl member update`.
- **Notes:** No strict-reconfig-check gate. Rejected at apply time if any new URL is already used by another member (`ErrPeerURLexists`). Requires admin when auth is enabled. Operators typically update the URL, then restart the member with the new `--listen-peer-urls`.

| Field | Value |
|---|---|
| ID | `member.update` |
| Tier | 3 |
| Feature group | `membership` |
| Kind | admin |
| How to call | `etcdserverpb.Cluster/MemberUpdate`, `POST /v3/cluster/member/update`, `etcdctl member update <memberID> --peer-urls=...`, `clientv3.Cluster.MemberUpdate` |
| Requires | — |
| Enabled by | — |
| Changes state | members |
| Reads state | members |
| Related | `member.add`, `member.remove`, `member.list` |
| Code locations | `server/etcdserver/api/v3rpc/member.go:ClusterServer.MemberUpdate`, `server/etcdserver/server.go:EtcdServer.UpdateMember`, `server/etcdserver/api/membership/cluster.go:RaftCluster.UpdateRaftAttributes` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| ID | uint64 | Must be a current member (`ErrIDNotFound`) |
| peerURLs | repeated string | New full list; must not overlap another member's peer URLs |

### `member.list`: Member list

- **What it does:** Returns every member with its ID, name, peer and client URLs, and learner flag. With `linearizable` it first waits for a linearizable read index so the list reflects all committed membership changes.
- **Tier reason:** Operator docs (https://etcd.io/docs/v3.8/op-guide/runtime-configuration/); `clientv3.Cluster.MemberList` and `etcdctl member list`, not the top-level KV client.
- **Notes:** `clientv3.Cluster.MemberList` is linearizable by default; `clientv3.WithSerializable()` makes it serializable. `etcdctl member list --consistency` defaults to `l`. Requires an authenticated user (any user) when auth is enabled. Members that were added but not yet started show an empty name and client URLs. The client library also calls it for endpoint auto-sync (`--auto-sync-interval`).

| Field | Value |
|---|---|
| ID | `member.list` |
| Tier | 3 |
| Feature group | `membership` |
| Kind | admin |
| How to call | `etcdserverpb.Cluster/MemberList`, `POST /v3/cluster/member/list`, `etcdctl member list [--consistency=l\|s]`, `clientv3.Cluster.MemberList` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | members |
| Related | `member.add`, `member.promote`, `member.remove`, `member.update` |
| Code locations | `server/etcdserver/api/v3rpc/member.go:ClusterServer.MemberList`, `server/etcdserver/server.go:EtcdServer.MemberList`, `server/etcdserver/api/membership/cluster.go:RaftCluster.Members` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| linearizable | bool | Proto default false; clientv3 and etcdctl send true unless serializable is asked for |

### `alarm.list`: Alarm list

- **What it does:** Returns the active alarms (member ID plus alarm type `NOSPACE` or `CORRUPT`). The request goes through raft as an `AlarmRequest` with action `GET`.
- **Tier reason:** Documented under space quota in https://etcd.io/docs/v3.8/op-guide/maintenance/; `clientv3.Maintenance.AlarmList` and `etcdctl alarm list`.
- **Notes:** `clientv3.AlarmList` sends `GET` with alarm `NONE`, which returns all alarms. Requires an authenticated user when auth is enabled. `etcdctl endpoint health` also calls it and reports an endpoint unhealthy if alarms are active.

| Field | Value |
|---|---|
| ID | `alarm.list` |
| Tier | 3 |
| Feature group | `alarm` |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Alarm` (action `GET`), `POST /v3/maintenance/alarm`, `etcdctl alarm list`, `clientv3.Maintenance.AlarmList` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | alarms |
| Related | `alarm.disarm`, `alarm.activate`, `maintenance.status` |
| Code locations | `server/etcdserver/api/v3rpc/maintenance.go:maintenanceServer.Alarm`, `server/etcdserver/v3_server.go:EtcdServer.Alarm`, `server/etcdserver/apply/backend.go:applierV3backend.Alarm` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| alarm | AlarmType | `NONE` (default) returns all; `NOSPACE` or `CORRUPT` filters |
| memberID | uint64 | Ignored for `GET` |

### `alarm.disarm`: Alarm disarm

- **What it does:** Deactivates an alarm through raft (action `DEACTIVATE`). Clearing `NOSPACE` takes the cluster out of its read-only, deletes-only mode.
- **Tier reason:** Part of the space-quota recovery procedure in https://etcd.io/docs/v3.8/op-guide/maintenance/ (compact, defrag, then disarm); `clientv3.Maintenance.AlarmDisarm` and `etcdctl alarm disarm`.
- **Notes:** `clientv3.AlarmDisarm` with a zero `AlarmMember` lists all alarms and disarms each one; `etcdctl alarm disarm` takes no arguments and does exactly that. If the database is still over quota, the next write that hits the quota raises `NOSPACE` again. After a disarm, the applier re-evaluates which alarm appliers are active (`uberApplier.Alarm` → `restoreAlarms`). Requires admin when auth is enabled.

| Field | Value |
|---|---|
| ID | `alarm.disarm` |
| Tier | 3 |
| Feature group | `alarm` |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Alarm` (action `DEACTIVATE`), `POST /v3/maintenance/alarm`, `etcdctl alarm disarm`, `clientv3.Maintenance.AlarmDisarm` |
| Requires | — |
| Enabled by | — |
| Changes state | alarms |
| Reads state | alarms |
| Related | `alarm.list`, `alarm.activate`, `maintenance.defragment` |
| Code locations | `server/etcdserver/api/v3rpc/maintenance.go:maintenanceServer.Alarm`, `server/etcdserver/apply/backend.go:applierV3backend.Alarm`, `server/etcdserver/apply/uber_applier.go:uberApplier.Alarm` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| memberID | uint64 | Member the alarm belongs to; 0 with alarm `NONE` in clientv3 means "disarm all" (done client side) |
| alarm | AlarmType | `NOSPACE` or `CORRUPT`; deactivating a non-active alarm is a no-op with an empty response |

### `alarm.activate`: Alarm activate

- **What it does:** Raises an alarm (`NOSPACE` or `CORRUPT`) for a member through raft (action `ACTIVATE`). Once applied, the cluster switches to the restricted applier: `NOSPACE` allows only reads and deletes, `CORRUPT` rejects all writes.
- **Tier reason:** The public `Maintenance/Alarm` RPC accepts `ACTIVATE`, but no docs page describes it and neither `clientv3.Maintenance` nor etcdctl exposes it. The server raises it itself when the backend quota is exceeded (`server/etcdserver/server.go`, `ErrNoSpace` path) and on corruption detection (`EtcdServer.triggerCorruptAlarm`).
- **Notes:** `ACTIVATE` with alarm `NONE` is a no-op. Requires admin when auth is enabled. Reachable from a raw gRPC client or the HTTP gateway.
- **Uncertain:** May not be meant for users. The proto comment says the RPC "activates, deactivates, and queries alarms" and the gateway exposes it, but the only callers in the repo are the server itself and tests (`server/etcdserver/apply/uber_applier_test.go`).

| Field | Value |
|---|---|
| ID | `alarm.activate` |
| Tier | 3 |
| Feature group | `alarm` |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Alarm` (action `ACTIVATE`), `POST /v3/maintenance/alarm`; no etcdctl or clientv3 method |
| Requires | — |
| Enabled by | — |
| Changes state | alarms |
| Reads state | alarms |
| Related | `alarm.list`, `alarm.disarm` |
| Code locations | `server/etcdserver/v3_server.go:EtcdServer.Alarm`, `server/etcdserver/apply/backend.go:applierV3backend.Alarm`, `server/etcdserver/apply/uber_applier.go:uberApplier.Alarm` |
| Confidence | low |

| Input | Type | Limits and notes |
|---|---|---|
| memberID | uint64 | Member to raise the alarm for; not checked against the member list |
| alarm | AlarmType | `NOSPACE` or `CORRUPT`; `NONE` is ignored |

### `maintenance.status`: Status

- **What it does:** Returns one member's view of itself: server version, leader ID, raft term, committed and applied index, DB size and in-use size, quota, learner flag, storage version, downgrade info, and errors (no leader, active alarms). Served locally, not through raft.
- **Tier reason:** Used throughout https://etcd.io/docs/v3.8/op-guide/maintenance/ (`etcdctl endpoint status` to read DB size before and after defrag); `clientv3.Maintenance.Status(endpoint)` is per endpoint.
- **Notes:** The only RPC besides serializable Range and Snapshot that a learner serves (`isRPCSupportedForLearner`). Requires an authenticated user when auth is enabled. `DbSizeQuota` reports `--quota-backend-bytes`, or the 2 GiB default when it is 0. `etcdctl move-leader` uses it to find the leader endpoint.

| Field | Value |
|---|---|
| ID | `maintenance.status` |
| Tier | 3 |
| Feature group | — |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Status`, `POST /v3/maintenance/status`, `etcdctl endpoint status [--cluster]`, `clientv3.Maintenance.Status` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | leader, backend_db, alarms, cluster_version, downgrade, storage_version |
| Related | `maintenance.defragment`, `maintenance.move_leader`, `alarm.list`, `downgrade.enable` |
| Code locations | `server/etcdserver/api/v3rpc/maintenance.go:maintenanceServer.Status` |
| Confidence | high |

No inputs.

### `maintenance.defragment`: Defragment

- **What it does:** Rewrites one member's bbolt backend file to release free pages to the filesystem, shrinking `DbSize` toward `DbSizeInUse`. Runs locally on the target member only; not replicated.
- **Tier reason:** Own section in https://etcd.io/docs/v3.8/op-guide/maintenance/ ("Defragmentation"); `clientv3.Maintenance.Defragment(endpoint)` and `etcdctl defrag`.
- **Notes:** With the `NonBlockingDefrag` feature gate (Beta, default on) most of the copy runs without blocking the member, then catches up; with it off the member blocks reads and writes for the whole defrag. `StopGRPCServiceOnDefrag` (Alpha, default off) marks the gRPC health service NOT_SERVING during defrag so clients fail over. Docs advise defragmenting one member at a time. Requires admin when auth is enabled. `etcdctl defrag --cluster` loops over all members.

| Field | Value |
|---|---|
| ID | `maintenance.defragment` |
| Tier | 3 |
| Feature group | — |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Defragment`, `POST /v3/maintenance/defragment`, `etcdctl defrag [--cluster]`, `clientv3.Maintenance.Defragment` |
| Requires | — |
| Enabled by | — |
| Changes state | backend_db |
| Reads state | backend_db |
| Related | `maintenance.status`, `alarm.disarm`, `maintenance.snapshot` |
| Code locations | `server/etcdserver/api/v3rpc/maintenance.go:maintenanceServer.Defragment`, `server/etcdserver/server.go:EtcdServer.Defragment`, `server/storage/backend/backend.go:backend.Defrag` |
| Confidence | high |

No inputs.

### `maintenance.hash`: Hash

- **What it does:** Returns a hash of the member's whole backend (all buckets, including keys, leases, auth, and members) plus the current revision. Runs locally on the member.
- **Tier reason:** The proto comment in `api/etcdserverpb/rpc.proto` says "This is designed for testing ONLY! ... Use HashKV API instead"; it is not on the `clientv3.Maintenance` interface (only the raw `retryMaintenanceClient.Hash` in `client/v3/retry.go`) and has no etcdctl command.
- **Notes:** Hashes the backend as it is at call time. Requires admin when auth is enabled.
- **Uncertain:** Registered and served on the public Maintenance service and HTTP gateway, but the proto calls it testing-only and no client or CLI exposes it. Kept as a Tier 3 operation rather than moved to Flagged because the server accepts it from any client.

| Field | Value |
|---|---|
| ID | `maintenance.hash` |
| Tier | 3 |
| Feature group | — |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Hash`, `POST /v3/maintenance/hash`; no etcdctl command or `clientv3.Maintenance` method (raw `pb.MaintenanceClient.Hash` only) |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | backend_db |
| Related | `maintenance.hashkv` |
| Code locations | `server/etcdserver/api/v3rpc/maintenance.go:maintenanceServer.Hash`, `server/storage/mvcc/hash.go:hashStorage.Hash`, `server/storage/backend/backend.go:backend.Hash` |
| Confidence | low |

No inputs.

### `maintenance.hashkv`: Hash KV

- **What it does:** Returns a hash of the MVCC `key` bucket up to a given revision, plus the compact revision and hash revision used. Operators compare it across members to check that their key-value data matches.
- **Tier reason:** `etcdctl endpoint hashkv` (documented in `etcdctl/README.md`, "ENDPOINT HASHKV") and `clientv3.Maintenance.HashKV(endpoint, rev)`; not in the developer guides.
- **Notes:** Revision 0 hashes up to the latest revision. Returns `ErrCompacted` if the revision is below the compact revision and `ErrFutureRev` if above the current revision. Hashes cached at compaction time are returned directly when the revision matches. Requires admin when auth is enabled. The server's own corruption checker uses the same hash between peers.

| Field | Value |
|---|---|
| ID | `maintenance.hashkv` |
| Tier | 3 |
| Feature group | — |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/HashKV`, `POST /v3/maintenance/hashkv`, `etcdctl endpoint hashkv [--rev=N] [--cluster]`, `clientv3.Maintenance.HashKV` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | keys, revisions, compaction |
| Related | `maintenance.hash` |
| Code locations | `server/etcdserver/api/v3rpc/maintenance.go:maintenanceServer.HashKV`, `server/storage/mvcc/hash.go:hashStorage.HashByRev` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| revision | int64 | 0 = latest (etcdctl `--rev` default 0); must be at or above the compact revision and at or below the current revision |

### `maintenance.snapshot`: Snapshot save

- **What it does:** Streams a point-in-time copy of the member's entire bbolt backend in 32 KiB chunks, followed by a SHA-256 of the data, and reports the storage version. The client writes it to a file that `etcdutl snapshot restore` can later use.
- **Tier reason:** Documented in https://etcd.io/docs/v3.8/op-guide/recovery/ ("Snapshotting the keyspace") and https://etcd.io/docs/v3.8/op-guide/maintenance/; `clientv3.Maintenance.SnapshotWithVersion` and `etcdctl snapshot save`.
- **Notes:** `snapshot.SaveWithVersion` (used by etcdctl) refuses more than one endpoint. Learners can serve it (the stream interceptor allows Snapshot on learners). Response headers carry no revision because the live store may have moved on. Requires admin when auth is enabled. Commonly run on a cron for backups.

| Field | Value |
|---|---|
| ID | `maintenance.snapshot` |
| Tier | 3 |
| Feature group | — |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Snapshot` (server stream), `POST /v3/maintenance/snapshot`, `etcdctl snapshot save <file>`, `clientv3.Maintenance.SnapshotWithVersion` (deprecated `Snapshot`) |
| Requires | — |
| Enabled by | — |
| Changes state | snapshots |
| Reads state | backend_db, storage_version |
| Related | `maintenance.defragment`, `maintenance.hashkv` |
| Code locations | `server/etcdserver/api/v3rpc/maintenance.go:maintenanceServer.Snapshot`, `server/storage/backend/backend.go:backend.Snapshot`, `client/v3/snapshot/v3_snapshot.go:SaveWithVersion` |
| Confidence | high |

No inputs.

### `maintenance.move_leader`: Move leader

- **What it does:** Asks the current leader to transfer leadership to a given voting member and waits until the transferee becomes leader or the context times out.
- **Tier reason:** `etcdctl move-leader` (documented in `etcdctl/README.md`, "MOVE-LEADER") and `clientv3.Maintenance.MoveLeader`; operator-only, not in the developer guides.
- **Notes:** Must be sent to the leader's endpoint, otherwise `ErrGRPCNotLeader`; etcdctl calls `Status` on each endpoint to find the leader first. A learner or unknown target returns `ErrBadLeaderTransferee`, and a timeout returns `ErrTimeoutLeaderTransfer`. Requires admin when auth is enabled. Operators use it before restarting or defragmenting the leader.

| Field | Value |
|---|---|
| ID | `maintenance.move_leader` |
| Tier | 3 |
| Feature group | — |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/MoveLeader`, `POST /v3/maintenance/transfer-leadership`, `etcdctl move-leader <hex-member-id>`, `clientv3.Maintenance.MoveLeader` |
| Requires | — |
| Enabled by | — |
| Changes state | leader |
| Reads state | leader, members |
| Related | `maintenance.status`, `member.list`, `member.promote` |
| Code locations | `server/etcdserver/api/v3rpc/maintenance.go:maintenanceServer.MoveLeader`, `server/etcdserver/server.go:EtcdServer.MoveLeader` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| targetID | uint64 | Must be an existing voting member (not a learner); sending to self when already leader returns immediately |

### `downgrade.validate`: Downgrade validate

- **What it does:** Checks, without changing anything, whether the cluster can be downgraded to the given version, and returns the current cluster version.
- **Tier reason:** Documented in https://etcd.io/docs/v3.8/downgrades/downgrading-etcd/; `clientv3.Maintenance.Downgrade(ctx, clientv3.DowngradeValidate, v)` and `etcdctl downgrade validate`.
- **Notes:** Does a linearizable read first. Only one minor version below the current cluster version is accepted (`allowedDowngradeVersion`); otherwise `ErrInvalidDowngradeTargetVersion`. Fails with `ErrDowngradeInProcess` if a downgrade is already enabled. Requires admin when auth is enabled.

| Field | Value |
|---|---|
| ID | `downgrade.validate` |
| Tier | 3 |
| Feature group | `downgrade` |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Downgrade` (action `VALIDATE`), `POST /v3/maintenance/downgrade`, `etcdctl downgrade validate <TARGET_VERSION>`, `clientv3.Maintenance.Downgrade(DowngradeValidate)` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | cluster_version, downgrade |
| Related | `downgrade.enable`, `downgrade.cancel`, `maintenance.status` |
| Code locations | `server/etcdserver/v3_server.go:EtcdServer.Downgrade`, `server/etcdserver/version/version.go:Manager.DowngradeValidate` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| version | string | `X.Y` or `X.Y.Z` semver; patch is dropped. Must equal current cluster major.minor minus one minor; bad format returns `ErrWrongDowngradeVersionFormat` |

### `downgrade.enable`: Downgrade enable

- **What it does:** Validates the target, then commits `DowngradeInfoSet{Enabled: true, Ver}` through raft. The cluster version is then lowered to the target, so members can be replaced one at a time with the older binary.
- **Tier reason:** Documented in https://etcd.io/docs/v3.8/downgrades/downgrading-etcd/; `clientv3.Maintenance.Downgrade(DowngradeEnable)` and `etcdctl downgrade enable`.
- **Notes:** Requires admin when auth is enabled. The version monitor cancels the downgrade on its own once all members run the target version (`Monitor.CancelDowngradeIfNeeded`). `Status.DowngradeInfo` reports progress. While a downgrade is enabled, a member started with a newer binary than allowed refuses to start (`MustDetectDowngrade`).

| Field | Value |
|---|---|
| ID | `downgrade.enable` |
| Tier | 3 |
| Feature group | `downgrade` |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Downgrade` (action `ENABLE`), `POST /v3/maintenance/downgrade`, `etcdctl downgrade enable <TARGET_VERSION>`, `clientv3.Maintenance.Downgrade(DowngradeEnable)` |
| Requires | — |
| Enabled by | — |
| Changes state | downgrade, cluster_version |
| Reads state | cluster_version, downgrade |
| Related | `downgrade.validate`, `downgrade.cancel`, `maintenance.status` |
| Code locations | `server/etcdserver/v3_server.go:EtcdServer.Downgrade`, `server/etcdserver/version/version.go:Manager.DowngradeEnable`, `server/etcdserver/apply/backend.go:applierV3backend.DowngradeInfoSet` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| version | string | Same rules as `downgrade.validate`: `X.Y`/`X.Y.Z`, exactly one minor below the current cluster version |

### `downgrade.cancel`: Downgrade cancel

- **What it does:** Commits `DowngradeInfoSet{Enabled: false}` through raft to stop an in-progress downgrade, then returns the current cluster version.
- **Tier reason:** Documented in https://etcd.io/docs/v3.8/downgrades/downgrading-etcd/; `clientv3.Maintenance.Downgrade(DowngradeCancel)` and `etcdctl downgrade cancel`.
- **Notes:** Does a linearizable read first. Clears the downgrade target through raft (`EtcdServer.downgradeCancel`). Requires admin when auth is enabled. The version input is ignored.

| Field | Value |
|---|---|
| ID | `downgrade.cancel` |
| Tier | 3 |
| Feature group | `downgrade` |
| Kind | admin |
| How to call | `etcdserverpb.Maintenance/Downgrade` (action `CANCEL`), `POST /v3/maintenance/downgrade`, `etcdctl downgrade cancel`, `clientv3.Maintenance.Downgrade(DowngradeCancel)` |
| Requires | `downgrade.enable` |
| Enabled by | — |
| Changes state | downgrade |
| Reads state | downgrade |
| Related | `downgrade.validate`, `downgrade.enable`, `maintenance.status` |
| Code locations | `server/etcdserver/v3_server.go:EtcdServer.Downgrade`, `server/etcdserver/version/version.go:Manager.DowngradeCancel`, `server/etcdserver/apply/backend.go:applierV3backend.DowngradeInfoSet` |
| Confidence | high |

No inputs.

### `auth.enable`: Auth enable

- **What it does:** Turns on authentication and RBAC for the whole cluster. Once it is on, every request must carry a valid token or a TLS client cert CN, and is checked against role permissions. Fails with `ErrRootUserNotExist` or `ErrRootRoleNotExist` unless a `root` user exists and holds the `root` role. Enabling auth when it is already on does nothing.
- **Tier reason:** Specialized admin feature. It has its own docs page (op-guide/authentication/rbac/: "Create the root user first ... then run `etcdctl auth enable`"), it sits on the `clientv3.Auth` sub-interface (`AuthEnable`), not the top-level KV client, and it uses the `etcdctl auth enable` command.
- **Notes:** Goes through raft as `InternalRaftRequest.AuthEnable`, then `authStore.AuthEnable` saves the enabled flag, enables the token provider, and rebuilds the range permission cache. It does not bump the auth revision. `etcdctl auth enable` retries automatically: on `ErrRootRoleNotExist` it runs `role add root` and `user grant-role root root` first. Once auth is on, the server rejects deleting the `root` user, deleting the `root` role, and revoking `root` from `root` with `ErrInvalidAuthMgmt`. Needs admin (root role) permission if auth is already on.

| Field | Value |
|---|---|
| ID | `auth.enable` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/AuthEnable`, `POST /v3/auth/enable`, `etcdctl auth enable`, `clientv3.Auth.AuthEnable` |
| Requires | `user.add`, `user.grant_role` |
| Enabled by | — |
| Changes state | auth_status, auth_tokens |
| Reads state | users, roles |
| Related | `auth.disable`, `auth.status`, `auth.authenticate`, `user.add`, `user.grant_role` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.AuthEnable`, `server/etcdserver/v3_server.go:EtcdServer.AuthEnable`, `server/auth/store.go:authStore.AuthEnable` |
| Confidence | high |

No inputs.

### `auth.disable`: Auth disable

- **What it does:** Turns authentication off. Requests are no longer permission-checked, and the token provider is disabled, so existing tokens stop being used. Disabling auth when it is already off does nothing.
- **Tier reason:** Specialized admin feature on op-guide/authentication/rbac/ ("Disable with `etcdctl --user root:rootpw auth disable`"). It is on the `clientv3.Auth` sub-interface (`AuthDisable`) and uses `etcdctl auth disable`.
- **Notes:** Goes through raft. Saves enabled=false, bumps the auth revision (`commitRevision`), and force-commits the backend. While auth is on, it needs the caller to hold the root role.

| Field | Value |
|---|---|
| ID | `auth.disable` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/AuthDisable`, `POST /v3/auth/disable`, `etcdctl auth disable`, `clientv3.Auth.AuthDisable` |
| Requires | `auth.enable` |
| Enabled by | — |
| Changes state | auth_status, auth_tokens |
| Reads state | auth_status |
| Related | `auth.enable`, `auth.status` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.AuthDisable`, `server/etcdserver/v3_server.go:EtcdServer.AuthDisable`, `server/auth/store.go:authStore.AuthDisable` |
| Confidence | high |

No inputs.

### `auth.status`: Auth status

- **What it does:** Returns whether auth is enabled and the current auth store revision (`authRevision`).
- **Tier reason:** Part of the specialized auth admin feature. It is on the `clientv3.Auth` sub-interface (`AuthStatus`) and uses `etcdctl auth status`. It is not part of the basic data path.
- **Notes:** Goes through raft as an `InternalRaftRequest` but is classed as side-effect free (`noSideEffect` in `server/etcdserver/apply/apply.go`). It does not need admin permission. The `authRevision` field was added in 3.5. It goes up on every user or role write and on auth disable, which makes it useful for seeing whether the auth config changed.

| Field | Value |
|---|---|
| ID | `auth.status` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/AuthStatus`, `POST /v3/auth/status`, `etcdctl auth status`, `clientv3.Auth.AuthStatus` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | auth_status |
| Related | `auth.enable`, `auth.disable` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.AuthStatus`, `server/etcdserver/v3_server.go:EtcdServer.AuthStatus`, `server/etcdserver/apply/backend.go:applierV3backend.AuthStatus` |
| Confidence | high |

No inputs.

### `auth.authenticate`: Authenticate

- **What it does:** Checks a username and password and returns a token (simple or JWT, depending on `--auth-token`). Later requests send the token in gRPC metadata. Fails with `ErrAuthNotEnabled` when auth is off, and with `ErrAuthFailed` for a wrong password, an unknown user, or a `--no-password` user.
- **Tier reason:** Part of the specialized auth feature (op-guide/authentication/rbac/, the `--user` flag). It is on the `clientv3.Auth` sub-interface (`Authenticate`). Most clients call it implicitly by setting `clientv3.Config.Username/Password`, and etcdctl calls it through the global `--user` / `--password` flags, not a subcommand.
- **Notes:** `EtcdServer.Authenticate` first does a linearizable read barrier. It then checks the bcrypt hash outside raft (`CheckPassword`), makes a simple-token prefix, and proposes `InternalAuthenticateRequest` (with no password) through raft. If the auth revision changed while the password was being checked, it retries. Simple tokens are kept in memory per member and expire after `--auth-token-ttl` (default 300 s), with the TTL reset each time the token is used. JWT tokens are stateless and signed with `--auth-token jwt,pub-key=...,priv-key=...,sign-method=...,ttl=...` (JWT ttl default 5m). Tokens carry the auth revision, and a token whose revision is older than the store's is rejected, so clients re-authenticate.

| Field | Value |
|---|---|
| ID | `auth.authenticate` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/Authenticate`, `POST /v3/auth/authenticate`, `etcdctl --user name:password <cmd>`, `clientv3.Auth.Authenticate` (or `clientv3.Config{Username, Password}`) |
| Requires | `user.add`, `auth.enable` |
| Enabled by | `--auth-token` (`simple` default, or `jwt,...`); `--auth-token-ttl` |
| Changes state | auth_tokens |
| Reads state | users, auth_status |
| Related | `auth.enable`, `user.add`, `user.change_password`, `user.delete` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.Authenticate`, `server/etcdserver/v3_server.go:EtcdServer.Authenticate`, `server/auth/store.go:authStore.Authenticate` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | string | Must be an existing user that has a password |
| password | string | Checked with bcrypt against the stored hash. Only the first 72 bytes matter to bcrypt, and etcd sets no length rule (rbac doc: "etcd does not enforce password length") |

### `user.add`: User add

- **What it does:** Creates a user with a password, or with `NoPassword` set for users that only log in by TLS CN. Fails with `ErrUserAlreadyExist` if the name is taken and `ErrUserEmpty` if the name is empty.
- **Tier reason:** RBAC management on op-guide/authentication/rbac/ (`etcdctl user add`). It is on the `clientv3.Auth` sub-interface (`UserAdd`, `UserAddWithOptions`).
- **Notes:** The API layer (`EtcdServer.UserAdd`) hashes the password with bcrypt at `--bcrypt-cost` before proposing. The raft entry carries `hashedPassword` (base64) and never the plain password. Bumps the auth revision. Needs the root role while auth is on. etcdctl accepts `name:password`, a prompt, `--interactive=false` to read stdin, `--new-user-password`, or `--no-password`. Adding the user `root` is the usual first step before `auth enable`.

| Field | Value |
|---|---|
| ID | `user.add` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/UserAdd`, `POST /v3/auth/user/add`, `etcdctl user add`, `clientv3.Auth.UserAdd` / `UserAddWithOptions` |
| Requires | — |
| Enabled by | `--bcrypt-cost` (hash cost) |
| Changes state | users, auth_status |
| Reads state | users |
| Related | `user.get`, `user.list`, `user.delete`, `user.change_password`, `user.grant_role`, `auth.authenticate` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.UserAdd`, `server/etcdserver/v3_server.go:EtcdServer.UserAdd`, `server/auth/store.go:authStore.UserAdd` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | string | Non-empty (`ErrUserEmpty`), unique (`ErrUserAlreadyExist`). `root` is the special admin user |
| password | string | Ignored if `NoPassword`. No length rule; bcrypt uses only the first 72 bytes. Hashed at `--bcrypt-cost` (default 10 = `bcrypt.DefaultCost`; values outside 4..31 fall back to 10) |
| options.no_password | bool | Default false. True means the user can only log in by TLS CN (`--client-cert-auth`), and `Authenticate` fails |

### `user.get`: User get

- **What it does:** Returns the list of roles granted to a user. Fails with `ErrUserNotFound` if the user does not exist.
- **Tier reason:** RBAC management (`etcdctl user get`, rbac doc). It is on the `clientv3.Auth` sub-interface (`UserGet`).
- **Notes:** Goes through raft but is side-effect free. While auth is on, a non-root user may get only their own record (`authApplierV3.UserGet`). `etcdctl user get --detail` also calls `RoleGet` for each role, on the client side.

| Field | Value |
|---|---|
| ID | `user.get` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/UserGet`, `POST /v3/auth/user/get`, `etcdctl user get [--detail]`, `clientv3.Auth.UserGet` |
| Requires | `user.add` |
| Enabled by | — |
| Changes state | — |
| Reads state | users |
| Related | `user.add`, `user.list`, `user.grant_role`, `user.revoke_role` |
| Code locations | `server/etcdserver/v3_server.go:EtcdServer.UserGet`, `server/etcdserver/apply/auth.go:authApplierV3.UserGet`, `server/auth/store.go:authStore.UserGet` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | string | Existing user name |

### `user.list`: User list

- **What it does:** Returns the names of all users.
- **Tier reason:** RBAC management (`etcdctl user list`, rbac doc). It is on the `clientv3.Auth` sub-interface (`UserList`).
- **Notes:** Goes through raft. Needs the root role while auth is on (`needAdminPermission`).

| Field | Value |
|---|---|
| ID | `user.list` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/UserList`, `POST /v3/auth/user/list`, `etcdctl user list`, `clientv3.Auth.UserList` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | users |
| Related | `user.add`, `user.delete`, `user.get` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.UserList`, `server/etcdserver/v3_server.go:EtcdServer.UserList`, `server/auth/store.go:authStore.UserList` |
| Confidence | high |

No inputs.

### `user.delete`: User delete

- **What it does:** Removes a user and invalidates that user's simple tokens. Fails with `ErrUserNotFound` if the user does not exist. While auth is on, deleting `root` fails with `ErrInvalidAuthMgmt`.
- **Tier reason:** RBAC management (`etcdctl user delete`, rbac doc). It is on the `clientv3.Auth` sub-interface (`UserDelete`).
- **Notes:** Bumps the auth revision and rebuilds the permission cache. Needs the root role while auth is on.

| Field | Value |
|---|---|
| ID | `user.delete` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/UserDelete`, `POST /v3/auth/user/delete`, `etcdctl user delete`, `clientv3.Auth.UserDelete` |
| Requires | `user.add` |
| Enabled by | — |
| Changes state | users, auth_status, auth_tokens |
| Reads state | users, auth_status |
| Related | `user.add`, `user.list`, `auth.authenticate` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.UserDelete`, `server/etcdserver/v3_server.go:EtcdServer.UserDelete`, `server/auth/store.go:authStore.UserDelete` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | string | Existing user. `root` is rejected while auth is on |

### `user.change_password`: User change password

- **What it does:** Replaces a user's password hash and invalidates the user's existing simple tokens. Keeps the user's roles and options. Fails with `ErrUserNotFound` if the user does not exist.
- **Tier reason:** RBAC management (`etcdctl user passwd`, rbac doc). It is on the `clientv3.Auth` sub-interface (`UserChangePassword`).
- **Notes:** `EtcdServer.UserChangePassword` hashes the password with bcrypt before proposing. For a `NoPassword` user the stored password stays empty. Bumps the auth revision, so tokens issued before the change are stale. Needs the root role while auth is on, even for a user changing their own password.

| Field | Value |
|---|---|
| ID | `user.change_password` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/UserChangePassword`, `POST /v3/auth/user/changepw`, `etcdctl user passwd`, `clientv3.Auth.UserChangePassword` |
| Requires | `user.add` |
| Enabled by | `--bcrypt-cost` (hash cost) |
| Changes state | users, auth_status, auth_tokens |
| Reads state | users |
| Related | `user.add`, `auth.authenticate` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.UserChangePassword`, `server/etcdserver/v3_server.go:EtcdServer.UserChangePassword`, `server/auth/store.go:authStore.UserChangePassword` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | string | Existing user |
| password | string | No length rule; bcrypt uses only the first 72 bytes. Hashed at `--bcrypt-cost` (default 10) |

### `user.grant_role`: User grant role

- **What it does:** Adds a role to a user's sorted role list. Granting a role the user already has succeeds and changes nothing. Fails with `ErrUserNotFound` or `ErrRoleNotFound`.
- **Tier reason:** RBAC management (`etcdctl user grant-role`, rbac doc). It is on the `clientv3.Auth` sub-interface (`UserGrantRole`).
- **Notes:** The role name `root` is special-cased: it can be granted even if no `root` role record exists. This is how the root user gets admin rights before `auth enable`. Bumps the auth revision. Needs the root role while auth is on.

| Field | Value |
|---|---|
| ID | `user.grant_role` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/UserGrantRole`, `POST /v3/auth/user/grant`, `etcdctl user grant-role`, `clientv3.Auth.UserGrantRole` |
| Requires | `user.add`, `role.add` |
| Enabled by | — |
| Changes state | users, auth_status |
| Reads state | users, roles |
| Related | `user.revoke_role`, `user.get`, `role.add`, `role.delete`, `auth.enable` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.UserGrantRole`, `server/etcdserver/v3_server.go:EtcdServer.UserGrantRole`, `server/auth/store.go:authStore.UserGrantRole` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| user | string | Existing user |
| role | string | Existing role, or `root` (always allowed) |

### `user.revoke_role`: User revoke role

- **What it does:** Removes a role from a user. Fails with `ErrRoleNotGranted` if the user does not have the role, and with `ErrUserNotFound` if the user does not exist. While auth is on, revoking `root` from user `root` fails with `ErrInvalidAuthMgmt`.
- **Tier reason:** RBAC management (`etcdctl user revoke-role`, rbac doc). It is on the `clientv3.Auth` sub-interface (`UserRevokeRole`).
- **Notes:** Bumps the auth revision and rebuilds the permission cache. Needs the root role while auth is on.

| Field | Value |
|---|---|
| ID | `user.revoke_role` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/UserRevokeRole`, `POST /v3/auth/user/revoke`, `etcdctl user revoke-role`, `clientv3.Auth.UserRevokeRole` |
| Requires | `user.grant_role` |
| Enabled by | — |
| Changes state | users, auth_status |
| Reads state | users |
| Related | `user.grant_role`, `user.get`, `role.delete` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.UserRevokeRole`, `server/etcdserver/v3_server.go:EtcdServer.UserRevokeRole`, `server/auth/store.go:authStore.UserRevokeRole` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | string | Existing user |
| role | string | A role currently granted to the user |

### `role.add`: Role add

- **What it does:** Creates an empty role with no permissions. Fails with `ErrRoleEmpty` for an empty name and `ErrRoleAlreadyExist` for a duplicate.
- **Tier reason:** RBAC management (`etcdctl role add`, rbac doc). It is on the `clientv3.Auth` sub-interface (`RoleAdd`).
- **Notes:** Bumps the auth revision. Needs the root role while auth is on. Adding a role named `root` creates the special admin role. `role get root` always reports full read-write access over all keys (`rootPerm`).

| Field | Value |
|---|---|
| ID | `role.add` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/RoleAdd`, `POST /v3/auth/role/add`, `etcdctl role add`, `clientv3.Auth.RoleAdd` |
| Requires | — |
| Enabled by | — |
| Changes state | roles, auth_status |
| Reads state | roles |
| Related | `role.get`, `role.list`, `role.delete`, `role.grant_permission`, `user.grant_role` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.RoleAdd`, `server/etcdserver/v3_server.go:EtcdServer.RoleAdd`, `server/auth/store.go:authStore.RoleAdd` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | string | Non-empty, unique. `root` is the special admin role |

### `role.get`: Role get

- **What it does:** Returns a role's key permissions (key, range_end, READ/WRITE/READWRITE). Fails with `ErrRoleNotFound` if the role does not exist.
- **Tier reason:** RBAC management (`etcdctl role get`, rbac doc). It is on the `clientv3.Auth` sub-interface (`RoleGet`).
- **Notes:** Goes through raft but is side-effect free. While auth is on, a non-root user may get only roles they hold (`authApplierV3.RoleGet`). For `root` it returns a synthetic all-keys READWRITE permission.

| Field | Value |
|---|---|
| ID | `role.get` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/RoleGet`, `POST /v3/auth/role/get`, `etcdctl role get`, `clientv3.Auth.RoleGet` |
| Requires | `role.add` |
| Enabled by | — |
| Changes state | — |
| Reads state | roles |
| Related | `role.add`, `role.grant_permission`, `role.revoke_permission`, `user.get` |
| Code locations | `server/etcdserver/v3_server.go:EtcdServer.RoleGet`, `server/etcdserver/apply/auth.go:authApplierV3.RoleGet`, `server/auth/store.go:authStore.RoleGet` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| role | string | Existing role name |

### `role.list`: Role list

- **What it does:** Returns the names of all roles.
- **Tier reason:** RBAC management (`etcdctl role list`, rbac doc). It is on the `clientv3.Auth` sub-interface (`RoleList`).
- **Notes:** Goes through raft. Needs the root role while auth is on.

| Field | Value |
|---|---|
| ID | `role.list` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/RoleList`, `POST /v3/auth/role/list`, `etcdctl role list`, `clientv3.Auth.RoleList` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | roles |
| Related | `role.add`, `role.delete`, `role.get` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.RoleList`, `server/etcdserver/v3_server.go:EtcdServer.RoleList`, `server/auth/store.go:authStore.RoleList` |
| Confidence | high |

No inputs.

### `role.delete`: Role delete

- **What it does:** Deletes a role and removes it from every user that holds it, in the same backend transaction. Fails with `ErrRoleNotFound` if the role does not exist. While auth is on, deleting `root` fails with `ErrInvalidAuthMgmt`.
- **Tier reason:** RBAC management (`etcdctl role delete`, rbac doc). It is on the `clientv3.Auth` sub-interface (`RoleDelete`).
- **Notes:** Bumps the auth revision and rebuilds the permission cache. Needs the root role while auth is on.

| Field | Value |
|---|---|
| ID | `role.delete` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/RoleDelete`, `POST /v3/auth/role/delete`, `etcdctl role delete`, `clientv3.Auth.RoleDelete` |
| Requires | `role.add` |
| Enabled by | — |
| Changes state | roles, users, auth_status |
| Reads state | roles, users |
| Related | `role.add`, `user.grant_role`, `user.revoke_role` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.RoleDelete`, `server/etcdserver/v3_server.go:EtcdServer.RoleDelete`, `server/auth/store.go:authStore.RoleDelete` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| role | string | Existing role. `root` is rejected while auth is on |

### `role.grant_permission`: Role grant permission

- **What it does:** Grants a role READ, WRITE, or READWRITE permission on one key or on a key range `[key, range_end)`. If the role already has a permission with the same key and range_end, only its type is changed. Fails with `ErrRoleNotFound`, `ErrPermissionNotGiven` (no perm given), or `ErrInvalidAuthMgmt` (invalid range).
- **Tier reason:** RBAC management (`etcdctl role grant-permission`, rbac doc). It is on the `clientv3.Auth` sub-interface (`RoleGrantPermission`, with `clientv3.PermissionType` and `clientv3.GetPrefixRangeEnd`).
- **Notes:** Permissions are kept sorted by key. Bumps the auth revision and rebuilds the permission cache. Needs the root role while auth is on. etcdctl `--prefix` sets range_end to the prefix end (`/foo/` becomes `[/foo/, /foo0)`), and `--from-key` sets range_end to `\x00` (this key and every greater key).

| Field | Value |
|---|---|
| ID | `role.grant_permission` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/RoleGrantPermission`, `POST /v3/auth/role/grant`, `etcdctl role grant-permission [--prefix\|--from-key] <role> <read\|write\|readwrite> <key> [endkey]`, `clientv3.Auth.RoleGrantPermission` |
| Requires | `role.add` |
| Enabled by | — |
| Changes state | roles, auth_status |
| Reads state | roles |
| Related | `role.revoke_permission`, `role.get`, `role.add` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.RoleGrantPermission`, `server/etcdserver/v3_server.go:EtcdServer.RoleGrantPermission`, `server/auth/store.go:authStore.RoleGrantPermission` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| name | string | Existing role |
| perm.permType | enum | READ (0), WRITE (1), READWRITE (2) |
| perm.key | bytes | Must be non-empty (`isValidPermissionRange`) |
| perm.range_end | bytes | Empty means a single key. `\x00` means from key onward. Otherwise it must be greater than key, or the request is rejected as an invalid range |

### `role.revoke_permission`: Role revoke permission

- **What it does:** Removes the permission whose key and range_end exactly match the request. Fails with `ErrPermissionNotGranted` if no permission matches, and with `ErrRoleNotFound` if the role does not exist.
- **Tier reason:** RBAC management (`etcdctl role revoke-permission`, rbac doc). It is on the `clientv3.Auth` sub-interface (`RoleRevokePermission`).
- **Notes:** The match is on the exact `(key, range_end)` pair, not on overlap. Bumps the auth revision and rebuilds the permission cache. Needs the root role while auth is on. etcdctl supports `--prefix` and `--from-key`, as for grant.

| Field | Value |
|---|---|
| ID | `role.revoke_permission` |
| Tier | 3 |
| Feature group | `auth` |
| Kind | admin |
| How to call | `etcdserverpb.Auth/RoleRevokePermission`, `POST /v3/auth/role/revoke`, `etcdctl role revoke-permission [--prefix\|--from-key] <role> <key> [endkey]`, `clientv3.Auth.RoleRevokePermission` |
| Requires | `role.grant_permission` |
| Enabled by | — |
| Changes state | roles, auth_status |
| Reads state | roles |
| Related | `role.grant_permission`, `role.get` |
| Code locations | `server/etcdserver/api/v3rpc/auth.go:AuthServer.RoleRevokePermission`, `server/etcdserver/v3_server.go:EtcdServer.RoleRevokePermission`, `server/auth/store.go:authStore.RoleRevokePermission` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| role | string | Existing role |
| key | bytes | Must exactly equal the key of a granted permission |
| range_end | bytes | Must exactly equal the range_end of that permission (empty for a single key) |

### `offline.snapshot_restore`: Snapshot restore

- **What it does:** Builds a new data directory (bbolt `member/snap/db`, a WAL, and a raft snapshot) from a snapshot file, with fresh cluster membership taken from the `--initial-cluster` flags. It can raise the latest revision (`--bump-revision`) and mark it compacted (`--mark-compacted`), so watchers and clients see a clear break in history.
- **Tier reason:** Only covered in the disaster-recovery guide (https://etcd.io/docs/v3.8/op-guide/recovery/). It is an `etcdutl snapshot restore` subcommand (`etcdutl/etcdutl/snapshot_command.go`) with no clientv3 method, and it is not offered in `etcdctl`.
- **Notes:** Runs against files on disk for a stopped or new member, not through the gRPC API. The output `--data-dir` must be empty or missing, and `--wal-dir` must not exist yet. To recover a cluster, each member is restored from the same snapshot with the same `--initial-cluster`/`--initial-cluster-token`, and then all members are started. A `db` file copied straight from a data directory has no integrity hash, so it needs `--skip-hash-check`. `--bump-revision` and `--mark-compacted` must be used together: either flag on its own fails with ExitBadArgs. When verification is enabled (`ETCD_VERIFY`), the restored data dir is checked at the end.

| Field | Value |
|---|---|
| ID | `offline.snapshot_restore` |
| Tier | 3 |
| Feature group | `offline` |
| Kind | admin |
| How to call | `etcdutl snapshot restore <file> --data-dir <dir> [flags]`; Go: `snapshot.NewV3(lg).Restore(snapshot.RestoreConfig{...})` (etcdutl/snapshot) |
| Requires | `maintenance.snapshot` |
| Enabled by | — |
| Changes state | data_dir, backend_db, members, revisions, compaction |
| Reads state | snapshots |
| Related | `maintenance.snapshot`, `offline.snapshot_status`, `offline.hashkv`, `offline.migrate` |
| Code locations | `etcdutl/etcdutl/snapshot_command.go:SnapshotRestoreCommandFunc`, `etcdutl/snapshot/v3_snapshot.go:v3Manager.Restore`, `etcdutl/snapshot/v3_snapshot.go:v3Manager.modifyLatestRevision` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| filename | path (positional) | Exactly one argument. A snapshot from `etcdctl snapshot save`, or a raw `db` file (raw files need `--skip-hash-check`) |
| --data-dir | path | Default `<name>.etcd`. Must be empty or missing |
| --wal-dir | path | Default `<data-dir>/member/wal`. If given, it must not exist yet |
| --name | string | Default `default`. Must appear in `--initial-cluster` |
| --initial-cluster | string | Default `default=http://localhost:2380`. Comma-separated `name=peerURL` list; checked by `ServerConfig.VerifyBootstrap` |
| --initial-cluster-token | string | Default `etcd-cluster`. Feeds into the cluster and member IDs |
| --initial-advertise-peer-urls | string | Default `http://localhost:2380`. Comma-separated; must match this member's entry in `--initial-cluster` |
| --skip-hash-check | bool | Default false. Skips the sha256 integrity check on the snapshot |
| --initial-memory-map-size | uint64 | Default 10 GiB (`backend.InitialMmapSize`); 0 means use the default |
| --bump-revision | uint64 | Default 0. How much to add to the latest revision. Needs `--mark-compacted` |
| --mark-compacted | bool | Default false. Required when `--bump-revision` > 0, and not allowed when it is 0 |
| --timeout (global) | duration | Default 10s. How long to wait for the db file lock; 0 waits forever |

### `offline.snapshot_status`: Snapshot status

- **What it does:** Opens a snapshot file read-only, runs bbolt's integrity check, and prints its hash, latest revision, number of live keys, total size, and storage version.
- **Tier reason:** Only covered in the recovery and maintenance docs (https://etcd.io/docs/v3.8/op-guide/recovery/). It is an `etcdutl snapshot status` subcommand with no clientv3 method.
- **Notes:** Runs against a file on disk, not through the API. Usually run on a file from `etcdctl snapshot save` before restoring it. `Version` is empty for snapshots taken from servers older than v3.6.

| Field | Value |
|---|---|
| ID | `offline.snapshot_status` |
| Tier | 3 |
| Feature group | `offline` |
| Kind | admin |
| How to call | `etcdutl snapshot status <file> [-w simple\|table\|json\|fields\|protobuf]`; Go: `snapshot.NewV3(lg).Status(path)` |
| Requires | `maintenance.snapshot` |
| Enabled by | — |
| Changes state | — |
| Reads state | snapshots, keys, revisions, storage_version |
| Related | `maintenance.snapshot`, `offline.snapshot_restore`, `offline.hashkv` |
| Code locations | `etcdutl/etcdutl/snapshot_command.go:SnapshotStatusCommandFunc`, `etcdutl/snapshot/v3_snapshot.go:v3Manager.Status` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| filename | path (positional) | Exactly one argument; must be an existing file |
| --write-out / -w (global) | enum | `simple` (default), `table`, `json`, `fields`, `protobuf` |

### `offline.defrag`: Offline defrag

- **What it does:** Opens the bbolt backend of a data directory and rewrites it into a compact file, giving free pages back to the filesystem.
- **Tier reason:** The maintenance guide (https://etcd.io/docs/v3.8/op-guide/maintenance/) describes `etcdutl defrag --data-dir` as the offline version of online defrag. It is a separate `etcdutl` command with no client method.
- **Notes:** Runs against the files of a stopped member, not through the API. It takes the db file lock and fails after `--timeout` if a running etcd holds it. The same `backend.Defrag` code runs for online defrag.

| Field | Value |
|---|---|
| ID | `offline.defrag` |
| Tier | 3 |
| Feature group | `offline` |
| Kind | admin |
| How to call | `etcdutl defrag --data-dir <dir>`; Go: `etcdutl.DefragData(dataDir)` |
| Requires | — |
| Enabled by | — |
| Changes state | backend_db |
| Reads state | data_dir, backend_db |
| Related | `maintenance.defragment`, `offline.migrate` |
| Code locations | `etcdutl/etcdutl/defrag_command.go:DefragData`, `server/storage/backend/backend.go:backend.Defrag` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| --data-dir | path | Required. Must exist; the backend is at `<data-dir>/member/snap/db` |
| --timeout (global) | duration | Default 10s. How long to wait for the db file lock; 0 waits forever |

### `offline.migrate`: Storage migrate

- **What it does:** Changes the storage schema of a data directory to match a target etcd minor version. It reads the WAL version to decide which schema changes are safe, and can force the storage version if migration fails.
- **Tier reason:** Only in the upgrade and downgrade guides (https://etcd.io/docs/v3.8/upgrades/, https://etcd.io/docs/v3.8/downgrades/). It is an `etcdutl migrate` command with no client method.
- **Notes:** Runs against the files of a stopped member, not through the API. If the detected storage version already equals the target, it does nothing. The target must have the form "X.Y" and be at least 3.5. `--force` sets the storage version anyway when migration fails; for targets below 3.6 it clears the storage version instead. The docs use it to prepare a data dir before starting an older binary during a manual downgrade.

| Field | Value |
|---|---|
| ID | `offline.migrate` |
| Tier | 3 |
| Feature group | `offline` |
| Kind | admin |
| How to call | `etcdutl migrate --data-dir <dir> --target-version X.Y [--force]` |
| Requires | — |
| Enabled by | — |
| Changes state | storage_version, backend_db |
| Reads state | data_dir, storage_version |
| Related | `offline.snapshot_restore`, `offline.defrag` |
| Code locations | `etcdutl/etcdutl/migrate_command.go:migrateCommandFunc`, `server/storage/schema/schema.go:Migrate`, `server/storage/schema/schema.go:DetectSchemaVersion` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| --data-dir | path | Required. Must contain the backend db and a WAL that can be read |
| --target-version | string | Required. Format "X.Y" (exactly one dot); at least `3.5` |
| --force | bool | Default false. When migration fails, forces the storage version: sets it for targets of 3.6 and above, clears it for 3.5. Not recommended |
| --timeout (global) | duration | Default 10s. How long to wait for the db file lock |

### `offline.hashkv`: Offline hash KV

- **What it does:** Opens a bbolt db file, loads it as an MVCC store, and prints the hash of the KV history up to a revision, along with that revision and the compact revision.
- **Tier reason:** An `etcdutl hashkv` command (`etcdutl/etcdutl/hashkv_command.go`) with no client method. It is the offline counterpart of the `Maintenance/HashKV` RPC, used to compare members' data.
- **Notes:** Runs against the db file of a stopped member, or a snapshot file, not through the API. Leases are ignored (it uses a `SimpleLessor`). The result can be compared with the online `etcdctl endpoint hashkv` value at the same revision.

| Field | Value |
|---|---|
| ID | `offline.hashkv` |
| Tier | 3 |
| Feature group | `offline` |
| Kind | admin |
| How to call | `etcdutl hashkv <db-file> [--rev N] [-w json\|table\|...]` |
| Requires | — |
| Enabled by | — |
| Changes state | — |
| Reads state | backend_db, keys, revisions, compaction |
| Related | `maintenance.hashkv`, `offline.snapshot_status` |
| Code locations | `etcdutl/etcdutl/hashkv_command.go:calculateHashKV`, `server/storage/mvcc/hash.go:hashStorage.HashByRev` |
| Confidence | high |

| Input | Type | Limits and notes |
|---|---|---|
| filename | path (positional) | Exactly one argument; the bbolt db file (e.g. `<data-dir>/member/snap/db`) |
| --rev | int64 | Default 0, meaning the latest revision. Must be no older than the compact revision and no newer than the current revision |
| --timeout (global) | duration | Default 10s. How long to wait for the db file lock |
