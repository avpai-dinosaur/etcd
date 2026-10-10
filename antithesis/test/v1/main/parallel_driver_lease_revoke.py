#!/usr/bin/env python3
"""lease.revoke: revoke leases from the shared pool, deleting their keys."""
from helper_client import client, pb, TIMEOUT
from helper_common import pick_lease, pick_count, log_outcome, error_name

OP = "lease.revoke"

c = client()
for _ in range(pick_count(1, 3)):
    try:
        c.lease.LeaseRevoke(pb.LeaseRevokeRequest(ID=pick_lease()), timeout=TIMEOUT)
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
