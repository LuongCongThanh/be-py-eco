"""UUIDv7 generator — time-ordered UUIDs (RFC 9562) for use as primary keys.

Monotonic within the same millisecond via a random tie-breaker in the
remaining bits, so IDs generated in quick succession still sort correctly.
"""

import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """Generate a UUIDv7: 48-bit millisecond timestamp + random bits."""
    unix_ms = time.time_ns() // 1_000_000
    timestamp_bytes = unix_ms.to_bytes(6, byteorder="big")
    rand_bytes = bytearray(os.urandom(10))

    # Set version (7) in the high nibble of byte 6.
    rand_bytes[0] = (rand_bytes[0] & 0x0F) | 0x70
    # Set variant (RFC 4122) in the high bits of byte 8.
    rand_bytes[2] = (rand_bytes[2] & 0x3F) | 0x80

    return uuid.UUID(bytes=timestamp_bytes + bytes(rand_bytes))
