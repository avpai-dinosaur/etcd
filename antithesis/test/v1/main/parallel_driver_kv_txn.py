#!/usr/bin/env python3
"""kv.txn: compares on every target, then range/put/delete/nested-txn ops."""
from helper_client import client, pb, TIMEOUT, MAX_TXN_OPS
from helper_common import (pick, pick_name, pick_key, pick_range, pick_count, put_fields,
                           range_fields, log_outcome, error_name)

OP = "kv.txn"
TARGETS = {0: "version", 1: "create_revision", 2: "mod_revision", 3: "value", 4: "lease"}


def compare():
    target = pick(list(TARGETS) * 3 + [5])  # 5 is not a valid target (rare)
    value = pick([b"", b"x", b"hello"]) if target == 3 else pick([0, 1, 2, 10, 100])
    key, range_end = pick([(pick_key(), b""), pick_range(pick_name())])  # pick_key: rarely empty
    return pb.Compare(result=pick([0, 1, 2, 3] * 3 + [4]), target=target, key=key,  # 4: invalid
                      range_end=range_end, **({TARGETS[target]: value} if target in TARGETS else {}))


def request_op(nested):
    key, range_end = pick_range(pick_key())
    # Empty ops reject the whole txn (ErrGRPCKeyNotFound), so they're rare.
    kind = pick(["range", "put", "put", "delete"] * 3 + ["empty"] + ([] if nested else ["txn"]))
    if kind == "range":  # same options as kv.range / kv.put, so inner ops can fail checks too
        return pb.RequestOp(request_range=pb.RangeRequest(**range_fields()))
    if kind == "put":
        return pb.RequestOp(request_put=pb.PutRequest(**put_fields()))
    if kind == "delete":
        return pb.RequestOp(request_delete_range=pb.DeleteRangeRequest(key=key, range_end=range_end))
    if kind == "txn":
        return pb.RequestOp(request_txn=txn(nested=True))
    return pb.RequestOp()  # empty op


def txn(nested=False):
    ops = lambda: [request_op(nested) for _ in range(pick([0, 1, 1, 2, 3]))]
    if not nested and pick([False] * 19 + [True]):  # over --max-txn-ops: ErrGRPCTooManyOps
        ops = lambda: [pb.RequestOp(request_range=pb.RangeRequest(key=pick_name()))] * (MAX_TXN_OPS + 1)
    return pb.TxnRequest(compare=[compare() for _ in range(pick([0, 1, 1, 2, 3]))],
                         success=ops(), failure=ops())


c = client()
for _ in range(pick_count()):
    try:
        c.kv.Txn(txn(), timeout=TIMEOUT)
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
