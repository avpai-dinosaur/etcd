# Antithesis images for etcd, built from this checkout (build context: repo root).
#
#   target etcd      etcd server (+ etcdctl, etcdutl). COVERAGE=0 (default):
#                    Antithesis-instrumented. COVERAGE=1: `go build -cover`, for
#                    local coverage runs only (see config/docker-compose.coverage.yaml).
#   target workload  Python test templates + generated gRPC stubs.

ARG GO_VERSION=1.27.1

# ---------------------------------------------------------------------------
FROM golang:${GO_VERSION} AS etcd-build
ENV GOTOOLCHAIN=local CGO_ENABLED=1 NO_COLOR=1
ARG ANTITHESIS_SDK_VERSION=v0.8.0
ARG COVERAGE=0
RUN --mount=type=cache,target=/go/pkg/mod \
    go install github.com/antithesishq/antithesis-sdk-go/tools/antithesis-go-toolexec@${ANTITHESIS_SDK_VERSION}

WORKDIR /src
# Everything except the harness itself, so editing drivers doesn't rebuild etcd.
COPY --exclude=antithesis . .
# Bootstrap property (build-time only; not in the source tree).
COPY antithesis/etcd/antithesis_bootstrap.go server/etcdmain/
RUN --mount=type=cache,target=/go/pkg/mod \
    cd server && go get github.com/antithesishq/antithesis-sdk-go@${ANTITHESIS_SDK_VERSION}

# The instrumented build must not reuse the go build cache: cached packages
# skip the toolexec step and would be missing from /symbols.
# ANTITHESIS_INSTRUMENT=go.etcd.io also instruments raft (go.etcd.io/raft/v3)
# and bbolt (go.etcd.io/bbolt), which are downloaded modules and so skipped by
# default; consensus and storage are where most of etcd's risk is.
RUN --mount=type=cache,target=/go/pkg/mod \
    set -eux; mkdir -p /out /symbols; \
    LDFLAGS="-X=go.etcd.io/etcd/api/v3/version.GitSHA=antithesis"; \
    if [ "$COVERAGE" = "1" ]; then \
      (cd server && go build -cover -coverpkg=go.etcd.io/etcd/... -ldflags="$LDFLAGS" -o /out/etcd .); \
    else \
      (cd server && ANTITHESIS_SYMBOLS_DIR=/symbols ANTITHESIS_DISPLAY_NAME=etcd \
         ANTITHESIS_INSTRUMENT=go.etcd.io \
         go build -toolexec=antithesis-go-toolexec -ldflags="$LDFLAGS" -o /out/etcd .); \
    fi; \
    (cd etcdctl && go build -ldflags="$LDFLAGS" -o /out/etcdctl .); \
    (cd etcdutl && go build -ldflags="$LDFLAGS" -o /out/etcdutl .)

# ---------------------------------------------------------------------------
FROM debian:stable-slim AS etcd
ENV NO_COLOR=1
COPY --from=etcd-build /out/ /usr/local/bin/
COPY --from=etcd-build /symbols/ /symbols/
# Tees the process output to /logs/<service>.log for the log sidecar.
COPY antithesis/etcd/log-tee.sh /usr/local/bin/log-tee.sh
EXPOSE 2379 2380
CMD ["/usr/local/bin/etcd"]

# ---------------------------------------------------------------------------
FROM python:3.13-slim AS workload
ENV NO_COLOR=1 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/etcdpb
RUN pip install --no-cache-dir grpcio-tools==1.84.0 antithesis==0.4.0
COPY antithesis/workload/genproto.py /tmp/genproto.py
COPY api/etcdserverpb/rpc.proto api/etcdserverpb/
COPY api/mvccpb/kv.proto api/mvccpb/
COPY api/authpb/auth.proto api/authpb/
COPY api/versionpb/version.proto api/versionpb/
COPY server/etcdserver/api/v3lock/v3lockpb/v3lock.proto server/etcdserver/api/v3lock/v3lockpb/
COPY server/etcdserver/api/v3election/v3electionpb/v3election.proto server/etcdserver/api/v3election/v3electionpb/
RUN python3 /tmp/genproto.py / /opt/etcdpb && rm -rf /api /server /tmp/genproto.py
COPY antithesis/workload/entrypoint.py /opt/antithesis/entrypoint.py
COPY antithesis/test/ /opt/antithesis/test/
CMD ["python3", "/opt/antithesis/entrypoint.py"]
