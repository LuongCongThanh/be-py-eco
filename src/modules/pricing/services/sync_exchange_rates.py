"""Periodic Exchange Rate sync — guild.md §15 Slice 3, commit 8. Called
by Celery Beat (`pricing.tasks.sync_exchange_rates`), never inline from a
catalog read (commit 12's regression test enforces this). Each sync
inserts a new snapshot row rather than updating one in place, so history
(source/timestamp/expiry) is preserved — a Store Manager can see when a
rate last changed, not just its current value.
"""

from __future__ import annotations

from datetime import timedelta

from integrations.exchange_rate.client import get_exchange_rate_provider
from modules.pricing.constants import BASE_CURRENCY, RATE_TTL_SECONDS, SUPPORTED_TARGET_CURRENCIES
from modules.pricing.models.exchange_rate import ExchangeRate


def sync_exchange_rates() -> int:
    provider = get_exchange_rate_provider()
    synced = 0
    for target_currency in SUPPORTED_TARGET_CURRENCIES:
        rate = provider.get_rate(BASE_CURRENCY, target_currency)
        ExchangeRate.objects.create(
            base_currency=rate.base_currency,
            target_currency=rate.target_currency,
            rate=rate.rate,
            source=rate.source,
            fetched_at=rate.fetched_at,
            expires_at=rate.fetched_at + timedelta(seconds=RATE_TTL_SECONDS),
        )
        synced += 1
    return synced
