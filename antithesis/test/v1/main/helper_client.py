"""How drivers reach etcd: generated gRPC stubs on a plaintext channel to one
randomly chosen member.

    c = client()
    c.kv.Put(pb.PutRequest(key=b"k", value=b"v"), timeout=TIMEOUT)

Stubs: c.kv, c.watch, c.lease, c.cluster, c.maintenance, c.auth (etcdserverpb),
c.lock (v3lockpb), c.election (v3electionpb). Request types: pb (etcdserverpb),
lockpb, electionpb. The stubs are generated at image build time from the protos
in this repo (antithesis/workload/genproto.py) into /opt/etcdpb.
"""
import os

import grpc
from antithesis.random import random_choice
from etcd.api.etcdserverpb import rpc_pb2 as pb, rpc_pb2_grpc as rpc
from etcd.server.etcdserver.api.v3election.v3electionpb import (
    v3election_pb2 as electionpb, v3election_pb2_grpc as election_rpc)
from etcd.server.etcdserver.api.v3lock.v3lockpb import v3lock_pb2 as lockpb, v3lock_pb2_grpc as lock_rpc

ENDPOINTS = os.environ.get("ETCD_ENDPOINTS", "etcd0:2379,etcd1:2379,etcd2:2379").split(",")
# Short, so drivers don't hang during network faults.
TIMEOUT = 5
# Server limits from api-surface.md (defaults; the harness doesn't change them).
MAX_REQUEST_BYTES = 1572864  # --max-request-bytes, 1.5 MiB
MAX_TXN_OPS = 128            # --max-txn-ops

__all__ = ["client", "pb", "lockpb", "electionpb", "TIMEOUT", "MAX_REQUEST_BYTES", "MAX_TXN_OPS"]


class Client:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        # Allow responses up to the server's own limit plus gRPC overhead.
        self.channel = grpc.insecure_channel(endpoint, options=[
            ("grpc.max_receive_message_length", 64 * 1024 * 1024),
            ("grpc.max_send_message_length", 64 * 1024 * 1024),
        ])
        self.kv = rpc.KVStub(self.channel)
        self.watch = rpc.WatchStub(self.channel)
        self.lease = rpc.LeaseStub(self.channel)
        self.cluster = rpc.ClusterStub(self.channel)
        self.maintenance = rpc.MaintenanceStub(self.channel)
        self.auth = rpc.AuthStub(self.channel)
        self.lock = lock_rpc.LockStub(self.channel)
        self.election = election_rpc.ElectionStub(self.channel)


def client():
    """A client connected to a random member, so traffic spreads across the cluster."""
    return Client(random_choice(ENDPOINTS))
