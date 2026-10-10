#!/usr/bin/env python3
"""Workload container entrypoint: wait until every etcd member serves a
linearizable read, emit setup_complete, then idle so Test Composer can run the
test templates in /opt/antithesis/test/v1/."""
import os
import time

import grpc
from antithesis.lifecycle import setup_complete
from etcd.api.etcdserverpb import rpc_pb2, rpc_pb2_grpc

ENDPOINTS = os.environ.get("ETCD_ENDPOINTS", "etcd0:2379,etcd1:2379,etcd2:2379").split(",")


def healthy(endpoint):
    try:
        with grpc.insecure_channel(endpoint) as ch:
            rpc_pb2_grpc.KVStub(ch).Range(rpc_pb2.RangeRequest(key=b"health"), timeout=2)
        return True
    except grpc.RpcError as e:
        print(f"[entrypoint] {endpoint} not ready: {e.code().name}", flush=True)
        return False


while not all(healthy(ep) for ep in ENDPOINTS):
    time.sleep(1)

print(f"[entrypoint] all members ready: {ENDPOINTS}", flush=True)
setup_complete({"message": "etcd cluster serves linearizable reads", "endpoints": ENDPOINTS})

while True:
    time.sleep(3600)
