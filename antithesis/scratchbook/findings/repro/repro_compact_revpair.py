"""Repro attempt for 'range failed to find revision pair':
delete-from-key and re-put the same key in one txn, compact at that revision, read the key."""
import os
import grpc
from etcd.api.etcdserverpb import rpc_pb2 as pb, rpc_pb2_grpc as rpc

kv = rpc.KVStub(grpc.insecure_channel(os.environ.get("EP", "etcd0:2379")))
kv.Put(pb.PutRequest(key=b"key05", value=b"v1"), timeout=5)
r = kv.Txn(pb.TxnRequest(success=[
    pb.RequestOp(request_delete_range=pb.DeleteRangeRequest(key=b"key00", range_end=b"\x00")),
    pb.RequestOp(request_put=pb.PutRequest(key=b"key05", value=b"v2")),
]), timeout=5)
rev = r.header.revision
print("txn ok at revision", rev, "(checkIntervals let delete+put of key05 through)")
kv.Compact(pb.CompactionRequest(revision=rev, physical=True), timeout=5)
print("compacted at", rev)
try:
    print("range:", kv.Range(pb.RangeRequest(key=b"key05"), timeout=5).kvs)
except grpc.RpcError as e:
    print("range error:", e.code().name, e.details())
