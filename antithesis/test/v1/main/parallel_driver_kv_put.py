#!/usr/bin/env python3
"""kv.put: put menu values into pool keys, sometimes with the optional flags
(PUT_OPTIONS in helper_common)."""
from helper_client import client, pb, TIMEOUT
from helper_common import put_fields, pick_count, log_outcome, error_name

OP = "kv.put"

c = client()
for _ in range(pick_count()):
    try:
        c.kv.Put(pb.PutRequest(**put_fields()), timeout=TIMEOUT)
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
