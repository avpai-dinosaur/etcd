#!/usr/bin/env python3
"""kv.range_stream: stream ranges over the pool, reading every chunk."""
from helper_client import client, pb, TIMEOUT
from helper_common import (pick, pick_key, pick_range, pick_count, log_outcome, error_name,
                           BOOLS, LIMITS, REVISIONS)

OP = "kv.range_stream"
# Only default ordering and no revision filters are allowed; the rare
# non-default values are rejected with Unimplemented.
SORT_ORDERS = [0] * 9 + [2]
MIN_MOD_REVISIONS = [0] * 9 + [1]

c = client()
for _ in range(pick_count()):
    key, range_end = pick_range(pick_key())
    req = pb.RangeRequest(key=key, range_end=range_end, limit=pick(LIMITS), revision=pick(REVISIONS),
                          serializable=pick(BOOLS), keys_only=pick(BOOLS), count_only=pick(BOOLS),
                          sort_order=pick(SORT_ORDERS), min_mod_revision=pick(MIN_MOD_REVISIONS))
    try:
        for _chunk in c.kv.RangeStream(req, timeout=TIMEOUT):
            pass
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
