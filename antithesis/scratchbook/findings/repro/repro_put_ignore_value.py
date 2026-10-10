"""Minimal repro: from-key delete then ignore_value put of a covered key, in one txn."""
import grpc
from etcd.api.etcdserverpb import rpc_pb2 as pb, rpc_pb2_grpc as rpc

kv = rpc.KVStub(grpc.insecure_channel(__import__("os").environ.get("EP", "etcd0:2379")))
kv.Put(pb.PutRequest(key=b"key05", value=b"v"), timeout=5)
txn = pb.TxnRequest(success=[
    pb.RequestOp(request_delete_range=pb.DeleteRangeRequest(key=b"key00", range_end=b"\x00")),
    pb.RequestOp(request_put=pb.PutRequest(key=b"key05", ignore_value=True)),
])
try:
    print("txn response:", kv.Txn(txn, timeout=5))
except grpc.RpcError as e:
    print("txn error:", e.code().name, e.details())
