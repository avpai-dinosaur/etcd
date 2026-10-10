# Coverage Setup: etcd

## How drivers reach the system

**Network client (gRPC).** There is no official Python etcd client, so the
workload image generates Python gRPC stubs at build time from this repo's
protos (`antithesis/workload/genproto.py` strips the grpc-gateway/OpenAPI
annotations grpcio-tools can't resolve, then runs `grpc_tools.protoc` into
`/opt/etcdpb`, which is on `PYTHONPATH`). gRPC rather than the HTTP gateway
because `kv.range_stream`, watches and lease keep-alives are gRPC-only or
streaming.

`antithesis/test/v1/main/helper_client.py`:

- `client()` returns a `Client` connected to a random member
  (`antithesis.random.random_choice` over `ETCD_ENDPOINTS`).
- Stubs: `c.kv`, `c.watch`, `c.lease`, `c.cluster`, `c.maintenance`, `c.auth`,
  `c.lock`, `c.election`. Message modules: `pb` (etcdserverpb), `lockpb`,
  `electionpb`.
- `TIMEOUT = 5` seconds: pass `timeout=TIMEOUT` on every call.
- `MAX_REQUEST_BYTES`, `MAX_TXN_OPS`: the server defaults (the harness
  doesn't change them).
- Client-side message limits are raised to 64 MiB so oversized requests reach
  the server's own checks instead of being refused by the client.

Each Python driver process spends about 0.65 s importing grpc + stubs + SDK
before its first call.

## Shared state

Obvious: the etcd cluster. All drivers talk to the same three members.

## Logs

| Service | File in `/logs` (volume `sut-logs`) |
|---|---|
| `etcd0` | `etcd0.log` |
| `etcd1` | `etcd1.log` |
| `etcd2` | `etcd2.log` |

etcd logs JSON (zap) to stderr, unbuffered. `log-tee.sh` is the entrypoint of
each etcd service. The workload container's output is not on the volume
(except `sdk-workload.jsonl` in coverage runs). The sidecar is `etcd-sidecar`,
reducers folder empty.

## Local runs

```bash
antithesis/local/run-local.sh <label> <seed>          # DURATION defaults to 300 s
DURATION=120 antithesis/local/run-local.sh <label> <seed>
```

- About 30 s of overhead (start, setup, stop, extract) plus `DURATION`.
  Building `etcd-server:coverage` from scratch takes ~1.5 min on this VM
  (2 vCPU); cached afterwards unless SUT source changes.
- Produces `antithesis/local/out/<label>/coverage.gocov` (plus
  `coverage.modpaths.gocov`, the raw profile with Go import paths, and
  `coverage-percent.txt`, per-package statement percentages).
- Needs a Go toolchain on the host (`go tool covdata`).

How coverage gets written: the coverage override sets `init: false`, so
`log-tee.sh` is PID 1 and execs etcd, which then *is* PID 1. etcd's SIGTERM
handler (`pkg/osutil/interrupt_unix.go`) calls `os.Exit(0)` only when it is
PID 1; otherwise it re-raises the signal and dies without flushing Go coverage.
Checked: `docker compose stop etcd0` → exit 0, `covcounters.*` + `covmeta.*`
written.

## Coverage format and paths

Use the LCOV file (it has function names):

```bash
python3 <antithesis-coverage-workload>/scripts/coverage_report.py normalize \
  --format lcov antithesis/local/out/<label>/coverage.lcov --repo /home/exedev/etcd -o <snapshot>.json
```

- `extract_coverage()` merges the three `GOCOVERDIR`s with `go tool covdata
  textfmt`, rewrites Go import paths to repo paths
  (`go.etcd.io/etcd/server/v3/...` → `server/...`, same for `api`,
  `client/pkg`, `client/v3`, `pkg`, `etcdctl`, `etcdutl`, `cache`) into
  `coverage.gocov`, then `antithesis/local/gocov2lcov.py` turns that into
  `coverage.lcov` with one `FN`/`FNDA` per Go function, named `Type.Method` or
  `Func` (matches the code locations in `api-surface.md`).
- `coverage.gocov` still works with `--format gocover`, but then `by-op`
  shows 0 functions (Go profiles carry no names).
- No `--strip-prefix` or `--keep-function` needed.
- Instrumented packages: `-coverpkg=go.etcd.io/etcd/...` (everything from this
  repo that the etcd binary links). Baseline: 350 files, ~1,100 functions.
- The profile is in `set` mode (reached or not, no counts).

## Antithesis build instrumentation

`ANTITHESIS_INSTRUMENT=go.etcd.io`: etcd's own packages **plus** raft
(`go.etcd.io/raft/v3`, incl. `confchange`, `quorum`) and bbolt
(`go.etcd.io/bbolt`), which are downloaded modules and would be skipped by
default. 93 symbol tables. Their coverage helps Antithesis steer, but
`normalize --repo` drops them from snapshots (not in this repo).

## Known gaps

- Raft and bbolt are instrumented for Antithesis, but not in local coverage,
  and `--repo` drops them from Antithesis snapshots.
- etcdctl/etcdutl in the etcd image are not instrumented (only the `etcd`
  binary is). Offline `etcdutl` operations would need a different driver path.
- Locally there's no fault injection: leader changes, snapshot catch-up and
  recovery paths only show up in Antithesis.
- The last log lines of an etcd member can be lost when it exits in a
  coverage run (tee dies with PID 1). Doesn't affect Antithesis runs.
- **No Antithesis coverage export.** `snouty --json runs show` has no
  `results.coverage` with snouty 0.7.2 / tenant release 64.0, so
  `coverage_report.py normalize --format antithesis` has nothing to read.
  Compare Antithesis runs by triage properties and by outcome lines
  (`snouty runs events <run> "OP kv.put" -n 1000`; one search term only,
  unless `SNOUTY_UNSTABLE_FEATURES=runs-search` is set).
