"""Celery app bound to Django settings.

`task_ignore_result=True` by default: the domain's asynchronous work follows
the transactional-outbox pattern (ADR-0004) — dispatchers/consumers act on
committed events and don't need callers to poll a result backend.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("be_py_eco")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(name="ping_task", ignore_result=False)
def ping_task():
    """Trivial no-op task proving worker<->broker<->result connectivity —
    not a real business task. See Issue #5, commit 11. `ignore_result=False`
    overrides the CELERY_TASK_IGNORE_RESULT default only for this smoke
    task, so the round-trip can be asserted in tests."""
    return "pong"
