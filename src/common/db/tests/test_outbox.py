"""Outbox dispatcher — guild.md §15 Slice 3, commit 2's non-OpenSearch
half: at-least-once delivery to registered handlers."""

import pytest

from common.db import outbox
from common.db.models import OutboxEvent


@pytest.fixture(autouse=True)
def _clean_handler_registry():
    """`register_handler` mutates module-level state; tests must not leak
    handlers into each other."""
    saved = {k: list(v) for k, v in outbox._HANDLERS.items()}
    outbox._HANDLERS.clear()
    yield
    outbox._HANDLERS.clear()
    outbox._HANDLERS.update(saved)


@pytest.mark.django_db
def test_dispatch_calls_registered_handler_and_marks_dispatched() -> None:
    calls: list[dict] = []
    outbox.register_handler("test.event", calls.append)
    event = outbox.emit_event(event_type="test.event", payload={"x": 1})

    dispatched = outbox.dispatch_pending_events()

    assert dispatched == 1
    assert calls == [{"x": 1}]
    event.refresh_from_db()
    assert event.dispatched_at is not None


@pytest.mark.django_db
def test_event_with_no_registered_handler_is_still_marked_dispatched() -> None:
    event = outbox.emit_event(event_type="nobody.listens", payload={})

    outbox.dispatch_pending_events()

    event.refresh_from_db()
    assert event.dispatched_at is not None


@pytest.mark.django_db
def test_already_dispatched_events_are_not_redelivered() -> None:
    calls: list[dict] = []
    outbox.register_handler("test.event", calls.append)
    outbox.emit_event(event_type="test.event", payload={})
    outbox.dispatch_pending_events()

    outbox.dispatch_pending_events()

    assert len(calls) == 1


@pytest.mark.django_db
def test_a_raising_handler_leaves_the_event_undispatched() -> None:
    def _boom(payload):
        raise RuntimeError("handler failed")

    outbox.register_handler("test.event", _boom)
    event = outbox.emit_event(event_type="test.event", payload={})

    dispatched = outbox.dispatch_pending_events()

    assert dispatched == 0
    event.refresh_from_db()
    assert event.dispatched_at is None
    assert OutboxEvent.objects.filter(dispatched_at__isnull=True).count() == 1
