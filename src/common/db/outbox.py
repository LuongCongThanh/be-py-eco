"""Write-side helper and dispatcher for the transactional outbox —
ADR-0004. Every module emits domain events through `emit_event`, always
inside the same `transaction.atomic()` block as the state change it
announces, so a committed state change and its outbox row can never
diverge.

`register_handler`/`dispatch_pending_events` are the read/consume side,
added in guild.md §15 Slice 3, commit 2 for `search`'s index sync — the
first real consumer (Slice 2's Decision Document flagged this as a
producer-only slice).

Delivery is at-least-once **up to the handler call returning** — a
handler that raises leaves its event undispatched for the next run, so
every handler must be idempotent (e.g. `index_product`'s upsert-by-id).
For a handler that just enqueues further async work (as `search`'s does,
via `.delay()`), this only guarantees the enqueue happened at least once;
it says nothing about whether the enqueued Celery task itself eventually
succeeds — that reliability boundary belongs to Celery's own retry/ack
configuration on the task, not to this dispatcher.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from django.utils import timezone

from common.db.models import OutboxEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], None]

_HANDLERS: dict[str, list[EventHandler]] = {}


def emit_event(*, event_type: str, payload: dict[str, Any]) -> OutboxEvent:
    return OutboxEvent.objects.create(event_type=event_type, payload=payload)


def register_handler(event_type: str, handler: EventHandler) -> None:
    """Called from a consuming module's `AppConfig.ready()` (see
    `modules.search.handlers`) — never from `emit_event`'s caller, which
    shouldn't need to know who, if anyone, consumes its event."""
    _HANDLERS.setdefault(event_type, []).append(handler)


def dispatch_pending_events(*, batch_size: int = 100) -> int:
    """Deliver undispatched events to their registered handlers, marking
    each dispatched only once every handler for it has run without
    raising. Returns the number of events dispatched."""
    events = OutboxEvent.objects.filter(dispatched_at__isnull=True).order_by("created_at")[
        :batch_size
    ]
    dispatched = 0
    for event in events:
        try:
            for handler in _HANDLERS.get(event.event_type, []):
                handler(event.payload)
        except Exception:
            logger.exception(
                "outbox handler failed for event %s (%s) — left undispatched for retry",
                event.id,
                event.event_type,
            )
            continue
        event.dispatched_at = timezone.now()
        event.save(update_fields=["dispatched_at", "updated_at"])
        dispatched += 1
    return dispatched
