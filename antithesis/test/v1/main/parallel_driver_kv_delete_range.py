#!/usr/bin/env python3
"""kv.delete_range: delete single keys, prefixes and ranges from the pool."""
from helper_client import client, pb, TIMEOUT
from helper_common import pick, pick_key, pick_range, pick_count, log_outcome, error_name, BOOLS

OP = "kv.delete_range"

c = client()
for _ in range(pick_count(1, 5)):  # fewer than put/range, so the pool stays populated
    key, range_end = pick_range(pick_key())
    try:
        c.kv.DeleteRange(pb.DeleteRangeRequest(key=key, range_end=range_end, prev_kv=pick(BOOLS)),
                         timeout=TIMEOUT)
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
