import os, sys, grpc
from etcd.api.etcdserverpb import rpc_pb2 as pb, rpc_pb2_grpc as rpc
kv = rpc.KVStub(grpc.insecure_channel(os.environ["EP"]))
lease = rpc.LeaseStub(grpc.insecure_channel(os.environ["EP"]))
DEL = pb.RequestOp(request_delete_range=pb.DeleteRangeRequest(key=b"key00", range_end=b"\x00"))
variant = sys.argv[1]
lid = lease.LeaseGrant(pb.LeaseGrantRequest(ID=0x1000, TTL=60), timeout=5).ID
kv.Put(pb.PutRequest(key=b"key05", value=b"v", lease=lid), timeout=5)
if variant == "ignore_lease":
    ops = [DEL, pb.RequestOp(request_put=pb.PutRequest(key=b"key05", value=b"w", ignore_lease=True))]
elif variant == "nested":
    inner = pb.TxnRequest(success=[pb.RequestOp(request_put=pb.PutRequest(key=b"key05", ignore_value=True))])
    ops = [DEL, pb.RequestOp(request_txn=inner)]
elif variant == "all_keys":  # key="\x00", range_end="\x00" (every key)
    ops = [pb.RequestOp(request_delete_range=pb.DeleteRangeRequest(key=b"\x00", range_end=b"\x00")),
           pb.RequestOp(request_put=pb.PutRequest(key=b"key05", ignore_value=True))]
try:
    kv.Txn(pb.TxnRequest(success=ops), timeout=5); print(variant, "txn returned ok")
except grpc.RpcError as e:
    print(variant, "txn error:", e.code().name, (e.details() or "")[:60])
