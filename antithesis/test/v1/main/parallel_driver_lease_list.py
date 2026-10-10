#!/usr/bin/env python3
"""lease.list: list the serving member's leases."""
from helper_client import client, pb, TIMEOUT
from helper_common import pick_count, log_outcome, error_name

OP = "lease.list"

c = client()
for _ in range(pick_count(1, 5)):
    try:
        c.lease.LeaseLeases(pb.LeaseLeasesRequest(), timeout=TIMEOUT)
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
