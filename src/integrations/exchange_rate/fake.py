"""Deterministic exchange-rate provider double — guild.md §15 Slice 3,
commit 7. Used in test/local until a production provider is chosen
(`guild.md` §16); the production adapter, whenever it lands, must satisfy
the same `ExchangeRateProvider` contract test this fake already passes.
"""

from __future__ import annotations

from decimal import Decimal

from django.utils import timezone

from integrations.exchange_rate.client import ExchangeRateProviderError, Rate

# Fixed, made-up-but-plausible VND-per-unit rates — deterministic, not
# meant to reflect real markets.
_FIXED_RATES: dict[tuple[str, str], Decimal] = {
    ("VND", "USD"): Decimal("0.0000400"),
    ("USD", "VND"): Decimal("25000.00"),
}


class FakeExchangeRateProvider:
    def get_rate(self, base_currency: str, target_currency: str) -> Rate:
        if base_currency == target_currency:
            return Rate(
                base_currency=base_currency,
                target_currency=target_currency,
                rate=Decimal("1"),
                source="fake",
                fetched_at=timezone.now(),
            )

        rate = _FIXED_RATES.get((base_currency, target_currency))
        if rate is None:
            raise ExchangeRateProviderError(
                f"No fake rate configured for {base_currency}->{target_currency}"
            )
        return Rate(
            base_currency=base_currency,
            target_currency=target_currency,
            rate=rate,
            source="fake",
            fetched_at=timezone.now(),
        )
