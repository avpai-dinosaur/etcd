---
sut_path: /home/exedev/etcd
commit: f061acd0902d489041448cdd19d71a345d27b9f5
updated: 2026-10-09
scope: light (written to unblock antithesis-setup; no property catalog)
---

# SUT Analysis: etcd (light)

This is a deliberately short analysis, written only so `antithesis-setup` and
`antithesis-coverage-setup` have what they need. It is not a full
`antithesis-research` pass: there is no property catalog, and failure-prone
areas are only sketched. The operation-level view lives in `api-surface.md`.

## What it is

etcd is a strongly consistent, distributed key-value store. A cluster of
members replicates a log with Raft (`go.etcd.io/raft/v3`, an external module,
not in this repo). Applied entries update an MVCC store (`server/storage/mvcc`)
on top of a bbolt backend (`server/storage/backend`). Clients talk gRPC
(`api/etcdserverpb/rpc.proto`, plus lock and election services) on port 2379,
or the JSON grpc-gateway on the same port under `/v3/`. Members talk to each
other over HTTP (`rafthttp`) on port 2380.

## Language and build

- Go, multi-module workspace (`go.work`): `api`, `client/pkg`, `client/v3`,
  `pkg`, `server`, `etcdctl`, `etcdutl`, `cache`, `tests`, tools.
- Go 1.27 (`toolchain go1.27.1`, `.go-version` = 1.27.1).
- Binaries: `etcd` (built from `./server`), `etcdctl` (`./etcdctl`), `etcdutl`
  (`./etcdutl`). Upstream builds with `CGO_ENABLED=0` (`scripts/build_lib.sh`);
  the Antithesis build must use `CGO_ENABLED=1`.
- No Antithesis SDK in the main modules today. `tests/antithesis/` has an
  upstream harness that clones etcd from GitHub, turns `// gofail` comments into
  `assert.Reachable`, and swaps `verify` asserts for `assert.Always`.

## Main components (server)

| Area | Path | Notes |
|---|---|---|
| Entry point | `server/main.go` → `server/etcdmain` | Flag parsing, `startEtcd`, signal handling (`pkg/osutil/interrupt_unix.go`) |
| Embedding / listeners | `server/embed` | Client/peer listeners, gRPC + gateway serving |
| gRPC API | `server/etcdserver/api/v3rpc` | KV, Watch, Lease, Cluster, Maintenance, Auth; quota wrappers |
| Server core | `server/etcdserver` | `raftRequest`, apply loop, linearizable reads, snapshots |
| Apply | `server/etcdserver/apply`, `server/etcdserver/txn` | Put/Range/DeleteRange/Txn against MVCC |
| Storage | `server/storage/{mvcc,backend,wal,schema}` | Revisions, compaction, bbolt, WAL |
| Lease | `server/lease` | Lessor, expiry, checkpoints |
| Auth | `server/auth` | Users, roles, tokens (simple/JWT) |
| Membership | `server/etcdserver/api/membership` | Member add/remove/promote, learners |
| Lock / election | `server/etcdserver/api/v3lock`, `v3election` | Built on `client/v3/concurrency` |

## Failure-prone areas (sketch)

- Raft leader changes, slow followers catching up via snapshot
  (`--snapshot-count`, `--experimental-snapshot-catchup-entries`).
- Linearizable reads (ReadIndex) during leader changes and partitions.
- Compaction racing with reads, watches and range streams.
- Lease expiry and keepalive across leader changes.
- Member reconfiguration (learners, promote, remove the leader).
- Restart/recovery from WAL + snapshot + backend.

## Signal handling (matters for coverage builds)

`osutil.HandleInterrupts` catches SIGINT/SIGTERM, runs the registered handlers
(`e.Close`), then re-raises the signal with the default handler, so the process
dies by the signal. Only when etcd is PID 1 does it call `os.Exit(0)` instead.
