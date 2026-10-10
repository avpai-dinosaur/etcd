#!/usr/bin/env python3
"""Generate Python gRPC stubs for etcd's client-facing protos.

Usage: genproto.py <etcd-repo> <out-dir>

The protos import grpc-gateway / OpenAPI annotations that grpcio-tools doesn't
ship. Those only affect the HTTP gateway and docs, so this script copies the
protos into a temporary include tree laid out the way their imports expect
(etcd/api/..., etcd/server/...), drops those imports and option blocks, and
runs grpc_tools.protoc.
"""
import os
import re
import shutil
import sys
import tempfile

from grpc_tools import protoc
import grpc_tools

PROTOS = {
    "etcd/api/mvccpb/kv.proto": "api/mvccpb/kv.proto",
    "etcd/api/authpb/auth.proto": "api/authpb/auth.proto",
    "etcd/api/versionpb/version.proto": "api/versionpb/version.proto",
    "etcd/api/etcdserverpb/rpc.proto": "api/etcdserverpb/rpc.proto",
    "etcd/server/etcdserver/api/v3lock/v3lockpb/v3lock.proto":
        "server/etcdserver/api/v3lock/v3lockpb/v3lock.proto",
    "etcd/server/etcdserver/api/v3election/v3electionpb/v3election.proto":
        "server/etcdserver/api/v3election/v3electionpb/v3election.proto",
}
DROP_IMPORTS = re.compile(r'^import "(google/api/annotations|protoc-gen-openapiv2/[^"]*)\.proto";\n', re.M)
DROP_OPTION = re.compile(r'option \((google\.api\.http|grpc\.gateway\.[\w.]+)\)\s*=\s*\{')


def strip_options(text):
    """Remove `option (google.api.http) = {...};` style blocks (braces may nest)."""
    out, pos = [], 0
    for m in DROP_OPTION.finditer(text):
        if m.start() < pos:
            continue
        depth, i = 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        while text[i] in " \t\n":
            i += 1
        if text[i] == ";":
            i += 1
        out.append(text[pos:m.start()])
        pos = i
    out.append(text[pos:])
    return "".join(out)


def main(repo, out_dir):
    tmp = tempfile.mkdtemp()
    for dst, src in PROTOS.items():
        with open(os.path.join(repo, src)) as f:
            text = strip_options(DROP_IMPORTS.sub("", f.read()))
        os.makedirs(os.path.dirname(os.path.join(tmp, dst)), exist_ok=True)
        with open(os.path.join(tmp, dst), "w") as f:
            f.write(text)
    os.makedirs(out_dir, exist_ok=True)
    std = os.path.join(os.path.dirname(grpc_tools.__file__), "_proto")
    args = ["protoc", f"-I{tmp}", f"-I{std}", f"--python_out={out_dir}",
            f"--grpc_python_out={out_dir}", *PROTOS]
    if protoc.main(args) != 0:
        sys.exit("protoc failed")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
