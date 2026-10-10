"""Shared by all drivers: key pool, value menus, outcome logging.

Menus come from the inputs tables in antithesis/scratchbook/api-surface.md.
Keep this file small and plain. Drivers import from it.
"""
import re
import sys

import grpc
from antithesis.random import random_choice

from helper_client import MAX_REQUEST_BYTES

# Small shared pool, so drivers act on the same keys. "key0" is a prefix of
# key00..key09 and "key1" of key10..key15, so prefix ranges cover several keys.
NAMES = [f"key{i:02d}".encode() for i in range(16)]

# Values: typical, empty, and around --max-request-bytes (1.5 MiB). The big
# ones are listed once among many small ones, so disk use stays bounded.
VALUES = [b"", b"x", b"0", b"hello", b"v" * 100, b"v" * 1024, b"v" * 4096, b"v" * 65536,
          b"a", b"b", b"c", b"d",
          b"v" * (1024 * 1024),               # 1 MiB
          b"v" * (MAX_REQUEST_BYTES - 1024),  # just inside the request limit
          b"v" * (MAX_REQUEST_BYTES + 1)]     # just outside: ErrRequestTooLarge

# Revisions: 0 / negative = current (most common); small and large positives
# (large ones are in the future until the cluster gets there); far future (ErrFutureRev).
REVISIONS = [0, 0, 0, 0, -1, 1, 2, 10, 100, 1000, 10000, 2 ** 62]
LIMITS = [0, 1, 2, 5, 100]
BOOLS = [False, True]

# Shared lease-ID pool (lease feature group). Grants use these IDs, so other
# drivers' revokes, keep-alives, lookups and puts hit the same leases. At any
# moment some exist and some don't (never granted, revoked, or expired).
LEASE_IDS = [0x1000 + i for i in range(8)]
# TTLs (s): 0/1 are raised to the minimum (2 s); short ones expire during a
# run; 9e9 is MaxLeaseTTL; one past it is rejected (too large lease TTL).
LEASE_TTLS = [0, 1, 2, 3, 5, 10, 30, 3600, 9_000_000_000, 9_000_000_001]


def prefix_end(prefix):
    """range_end that covers every key starting with prefix (etcdctl --prefix)."""
    return prefix[:-1] + bytes([prefix[-1] + 1])


def pick_name():
    return random_choice(NAMES)


def pick_key():
    """A pool key, or now and then the empty key (ErrGRPCEmptyKey)."""
    return random_choice(NAMES + [b""])


def pick_range(key):
    """(key, range_end) in every form the inputs table lists."""
    if not key:
        return key, b""  # empty key: rejected by the server (ErrGRPCEmptyKey)
    return random_choice([
        (key, b""),                     # single key
        (key, b"\x00"),                 # from key (--from-key)
        (key[:4], prefix_end(key[:4])),  # prefix "key0" / "key1" (--prefix)
        (b"key", prefix_end(b"key")),   # whole pool
        (b"\x00", b"\x00"),             # all keys
        (key, key),                     # empty interval
    ])


# kv.put flag combinations from the inputs table, shared by kv.put and kv.txn.
# Plain puts are the common case. "pool" means a lease from LEASE_IDS, which
# may or may not exist (lease not found). ignore_value with a value and
# ignore_lease with a lease are rejected.
PUT_OPTIONS = [{}, {}, {}, {}, {}, {}, {},
               {"prev_kv": True},
               {"ignore_value": True, "value": b""},
               {"ignore_lease": True},
               {"ignore_value": True, "ignore_lease": True, "value": b""},
               {"ignore_value": True},
               {"ignore_lease": True, "lease": "pool"},
               {"lease": "pool"}, {"lease": "pool"}]


def put_fields():
    """PutRequest fields: a pool key, a menu value, and one PUT_OPTIONS entry."""
    fields = {"key": pick_key(), "value": pick_value()}
    fields.update(random_choice(PUT_OPTIONS))
    if fields.get("lease") == "pool":
        fields["lease"] = pick_lease()
    return fields


def range_fields():
    """RangeRequest fields with the kv.range options that are valid inside a txn too."""
    key, range_end = pick_range(pick_key())
    return {"key": key, "range_end": range_end, "revision": random_choice(REVISIONS),
            "limit": random_choice(LIMITS), "serializable": random_choice(BOOLS),
            "keys_only": random_choice(BOOLS), "count_only": random_choice(BOOLS)}


def pick_lease():
    return random_choice(LEASE_IDS)


def pick(menu):
    return random_choice(menu)


def pick_value():
    return random_choice(VALUES)


def pick_count(low=1, high=20):
    return random_choice(list(range(low, high + 1)))


def error_name(e):
    """Short, space-free outcome for an error, e.g. error=INVALID_ARGUMENT:etcdserver:_key_is_not_provided."""
    if isinstance(e, grpc.RpcError):
        # Digits (sizes, IDs) replaced so the same error always gives the same outcome.
        detail = re.sub(r"\d+", "N", (e.details() or "").replace(" ", "_"))[:60]
        return f"error={e.code().name}:{detail}"
    return f"error={type(e).__name__}"


def log_outcome(op_id, outcome):
    """One line per call. Used to measure which operations run, not to check them.
    One write per line, so lines from parallel drivers don't interleave."""
    sys.stdout.write(f"OP {op_id} {outcome}\n")
    sys.stdout.flush()
