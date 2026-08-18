"""Read the most recently synced Exchange Rate for a currency pair —
guild.md §15 Slice 3, commit 8. Never triggers a provider call; if
nothing has been synced yet, returns `None`.
"""

from __future__ import annotations

from modules.pricing.models.exchange_rate import ExchangeRate


def get_latest_rate(*, base_currency: str, target_currency: str) -> ExchangeRate | None:
    return (
        ExchangeRate.objects.filter(base_currency=base_currency, target_currency=target_currency)
        .order_by("-fetched_at")
        .first()
    )
