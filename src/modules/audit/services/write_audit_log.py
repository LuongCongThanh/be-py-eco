"""Bare audit write primitive (Issue #6 commit 14) — actor, action,
resource, redacted before/after, reason, IP, request ID, UTC timestamp
(guild.md §12.3). Never pass a secret in as `before`/`after`; known secret-
shaped keys are redacted defensively regardless.
"""

from __future__ import annotations

from typing import Any

from modules.audit.models import AuditLogEntry

REDACTED_KEYS = frozenset({"password", "password_hash", "token", "token_hash", "secret", "key"})
REDACTED_PLACEHOLDER = "<redacted>"


def _redact(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    return {
        key: (REDACTED_PLACEHOLDER if key.lower() in REDACTED_KEYS else value)
        for key, value in data.items()
    }


def write_audit_log(
    *,
    actor_type: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str = "",
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str = "",
    ip_address: str | None = None,
    request_id: str = "",
) -> AuditLogEntry:
    return AuditLogEntry.objects.create(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before=_redact(before),
        after=_redact(after),
        reason=reason,
        ip_address=ip_address,
        request_id=request_id,
    )
