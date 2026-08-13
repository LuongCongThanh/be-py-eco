"""Generic Idempotency-Key primitive (guild.md §3.10, §6.2, §12.4) — shared
by every sensitive/side-effecting action so no module reimplements it.

Same actor + key + request body -> same stored response, replayed, no new
side effect. Same key, different body -> `IdempotencyKeyConflict`. Records
default to a 7-day TTL (guild.md §12.4); nothing actively purges expired
rows yet — that's a retention-job concern, not this primitive's.
"""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

from django.utils import timezone

from common.db.models import IdempotencyRecord

IDEMPOTENCY_RECORD_TTL = timedelta(days=7)


class IdempotencyKeyConflict(Exception):
    """Same key, different request body."""


def _hash_request(data: dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def get_cached_response(
    *,
    actor_type: str,
    actor_id: str,
    action: str,
    idempotency_key: str,
    request_data: dict[str, Any],
) -> tuple[int, Any] | None:
    """Returns the cached `(status, body)` for a replayed request, `None`
    for a fresh key, or raises `IdempotencyKeyConflict` for key reuse with
    a different body."""
    try:
        record = IdempotencyRecord.objects.get(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            idempotency_key=idempotency_key,
        )
    except IdempotencyRecord.DoesNotExist:
        return None

    if record.expires_at < timezone.now():
        record.delete()
        return None

    if record.request_hash != _hash_request(request_data):
        raise IdempotencyKeyConflict

    return record.response_status, record.response_body


def store_response(
    *,
    actor_type: str,
    actor_id: str,
    action: str,
    idempotency_key: str,
    request_data: dict[str, Any],
    response_status: int,
    response_body: Any,
) -> None:
    IdempotencyRecord.objects.create(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        idempotency_key=idempotency_key,
        request_hash=_hash_request(request_data),
        response_status=response_status,
        response_body=response_body,
        expires_at=timezone.now() + IDEMPOTENCY_RECORD_TTL,
    )
