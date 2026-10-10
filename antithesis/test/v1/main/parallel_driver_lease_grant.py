#!/usr/bin/env python3
"""lease.grant: grant leases from the shared lease-ID pool (or server-chosen IDs)."""
from helper_client import client, pb, TIMEOUT
from helper_common import pick, pick_lease, pick_count, log_outcome, error_name, LEASE_TTLS

OP = "lease.grant"

c = client()
for _ in range(pick_count(1, 5)):
    # ID 0 lets the server choose; pool IDs collide with other drivers (ErrLeaseExists).
    lease_id = pick([0, pick_lease(), pick_lease(), pick_lease()])
    try:
        c.lease.LeaseGrant(pb.LeaseGrantRequest(ID=lease_id, TTL=pick(LEASE_TTLS)), timeout=TIMEOUT)
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
