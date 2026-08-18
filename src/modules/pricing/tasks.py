"""Celery Beat entry point for the Exchange Rate sync — guild.md §15
Slice 3, commit 8. Scheduled via `CELERY_BEAT_SCHEDULE`
(`config/settings/base.py`, task name `pricing.sync_exchange_rates`).
"""

from __future__ import annotations

from celery import shared_task

from modules.pricing.services.sync_exchange_rates import sync_exchange_rates as _sync_exchange_rates


@shared_task(name="pricing.sync_exchange_rates")
def sync_exchange_rates() -> int:
    return _sync_exchange_rates()
