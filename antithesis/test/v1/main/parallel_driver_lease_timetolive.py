#!/usr/bin/env python3
"""lease.timetolive: look up pool leases, sometimes with their attached keys."""
from helper_client import client, pb, TIMEOUT
from helper_common import pick, pick_lease, pick_count, log_outcome, error_name, BOOLS

OP = "lease.timetolive"

c = client()
for _ in range(pick_count()):
    try:
        c.lease.LeaseTimeToLive(pb.LeaseTimeToLiveRequest(ID=pick_lease(), keys=pick(BOOLS)),
                                timeout=TIMEOUT)
        log_outcome(OP, "ok")
    except Exception as e:
        log_outcome(OP, error_name(e))
