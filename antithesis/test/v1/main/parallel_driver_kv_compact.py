#!/usr/bin/env python3
"""kv.compact: compact history at revisions around the current one."""
from helper_client import client, pb, TIMEOUT
from helper_common import pick, log_outcome, error_name, BOOLS

OP = "kv.compact"

c = client()
try:
    # Read the current revision only to choose an argument (not a check).
    rev = c.kv.Range(pb.RangeRequest(key=b"key", count_only=True), timeout=TIMEOUT).header.revision
except Exception as e:
    log_outcome(OP, "read_rev_" + error_name(e))  # couldn't learn the revision; no compact sent
    raise SystemExit(0)
# Old history, recent history, the current revision, and the future (ErrFutureRev).
# Revisions at or below the last compaction fail with ErrCompacted.
target = pick([1, rev // 2, rev - 100, rev - 10, rev - 1, rev, rev + 1000])
try:
    c.kv.Compact(pb.CompactionRequest(revision=target, physical=pick(BOOLS)), timeout=TIMEOUT)
    log_outcome(OP, "ok")
except Exception as e:
    log_outcome(OP, error_name(e))
