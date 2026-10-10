---
sut_path: /home/exedev/etcd
commit: f061acd0902d489041448cdd19d71a345d27b9f5
updated: 2026-10-09
scope: light (written to unblock antithesis-setup)
---

# Deployment Topology: etcd (light)

## Containers

| Service | Image | Role |
|---|---|---|
| `etcd0`, `etcd1`, `etcd2` | `etcd-server` (built from this repo, instrumented) | 3-member cluster, static bootstrap (`--initial-cluster`) |
| `etcd-workload` | `etcd-workload` | Python test templates at `/opt/antithesis/test/v1/`; waits for the cluster to be healthy and emits `setup_complete` |
| `etcd-sidecar` | `etcd-sidecar` | Added by `antithesis-coverage-setup`: reads SUT logs from the shared `sut-logs` volume |

Three members is the smallest cluster that can lose one member and keep a
quorum, so Antithesis node and network faults produce leader changes without
making the cluster permanently unavailable. It matches the upstream
`tests/antithesis/config/docker-compose-3-node.yml`.

## Ports

- 2379: client gRPC + grpc-gateway (HTTP/JSON under `/v3/`), `/health`
- 2380: peer (rafthttp)

No TLS: the workload and the members talk plain HTTP/2.

## Storage

Each member keeps its data dir in the container (`/var/etcd/data`). Nothing is
shared between members. The upstream harness bind-mounts data dirs for its
history validator; this harness doesn't need that.

## Settings worth changing from defaults

Copied from the upstream harness, to make rare paths common:

- `ETCD_SNAPSHOT_COUNT=50`, `ETCD_SNAPSHOT_CATCHUP_ENTRIES=100`: snapshots and
  snapshot-based follower catch-up happen often.
- `ETCD_COMPACTION_BATCH_LIMIT=10`: compaction runs in many small batches.

## External dependencies

None. etcd needs no database, object store or network services.
