#!/usr/bin/env python3
"""lease.keepalive: renew pool leases over one keep-alive stream."""
from helper_client import client, pb, TIMEOUT
from helper_common import pick_lease, pick_count, log_outcome, error_name

OP = "lease.keepalive"

c = client()
requests = [pb.LeaseKeepAliveRequest(ID=pick_lease()) for _ in range(pick_count(1, 10))]
try:
    # One response per request; TTL 0 means the lease wasn't found.
    for _resp in c.lease.LeaseKeepAlive(iter(requests), timeout=TIMEOUT):
        log_outcome(OP, "ok")
except Exception as e:
    log_outcome(OP, error_name(e))
