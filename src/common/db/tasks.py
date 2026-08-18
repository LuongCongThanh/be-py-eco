"""Celery Beat entry point for the outbox dispatcher — guild.md §15
Slice 3, commit 2. Scheduled via `CELERY_BEAT_SCHEDULE`
(`config/settings/base.py`); the interesting logic lives in
`common.db.outbox.dispatch_pending_events` so it stays unit-testable
without a Celery worker.
"""

from __future__ import annotations

from celery import shared_task

from common.db.outbox import dispatch_pending_events


@shared_task(name="common_db.dispatch_outbox_events")
def dispatch_outbox_events() -> int:
    return dispatch_pending_events()
