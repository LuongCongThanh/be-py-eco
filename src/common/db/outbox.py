"""Write-side helper for the transactional outbox — ADR-0004. Every module
emits domain events through `emit_event`, always inside the same
`transaction.atomic()` block as the state change it announces, so a
committed state change and its outbox row can never diverge. No
dispatcher/consumer exists yet — Slice 3's search sync is the first real
one (guild.md §15 Slice 2, commit 14's Decision Document).
"""

from __future__ import annotations

from typing import Any

from common.db.models import OutboxEvent


def emit_event(*, event_type: str, payload: dict[str, Any]) -> OutboxEvent:
    return OutboxEvent.objects.create(event_type=event_type, payload=payload)
