#!/usr/bin/env python3
"""kv.range: read single keys, prefixes and ranges with the options from the inputs table."""
from helper_client import client, pb, TIMEOUT
from helper_common import (pick, pick_key, pick_range, pick_count, log_outcome, error_name,
                           BOOLS, LIMITS, REVISIONS)

OP = "kv.range"
SORT_ORDERS = [0, 0, 0, 0, 1, 1, 2, 2, 3]       # NONE, ASCEND, DESCEND; 3 is invalid (rare)
SORT_TARGETS = [0, 1, 2, 3, 4] * 2 + [5]        # KEY, VERSION, CREATE, MOD, VALUE; 5 is invalid (rare)
REV_FILTERS = [0, 0, 0, 0, 1, 10, 100, 1000]

c = client()
for _ in range(pick_count()):
    key, range_end = pick_range(pick_key())
    req = pb.RangeRequest(
        key=key, range_end=range_end, limit=pick(LIMITS), revision=pick(REVISIONS),
        sort_order=pick(SORT_ORDERS), sort_target=pick(SORT_TARGETS),
        serializable=pick(BOOLS), keys_only=pick(BOOLS), count_only=pick(BOOLS),
        min_mod_revision=pick(REV_FILTERS), max_mod_revision=pick(REV_FILTERS),
        min_create_revision=pick(REV_FILTERS), max_create_revision=pick(REV_FILTERS))
    try:
        c.kv.Range(req, timeout=TIMEOUT)
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
