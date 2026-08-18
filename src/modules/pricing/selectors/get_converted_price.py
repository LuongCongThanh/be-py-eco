"""Convert a VND Base Price into a Customer's selected Transaction
Currency for display — guild.md §15 Slice 3, commits 10-12. Reads the
latest synced `ExchangeRate` row (`get_latest_rate`) and never calls the
provider adapter itself — a catalog/search read can call this as often
as it likes without ever blocking on or invoking the exchange-rate
provider (commit 12's regression test asserts exactly this).

`is_stale` surfaces commit 11's non-blocking signal: a stale/missing
required rate degrades the price display (amount `None`, `is_stale`
`True`) rather than silently serving an outdated conversion. Hard-
blocking checkout on staleness is Slice 5's concern, not this one's.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.pricing.constants import BASE_CURRENCY
from modules.pricing.selectors.get_latest_rate import get_latest_rate
from modules.pricing.services.convert_price import convert_price


@dataclass(frozen=True)
class ConvertedPrice:
    amount: int | None
    currency: str
    is_stale: bool


def get_converted_price(*, base_price_vnd: int | None, target_currency: str) -> ConvertedPrice:
    if base_price_vnd is None:
        return ConvertedPrice(amount=None, currency=target_currency, is_stale=False)

    if target_currency == BASE_CURRENCY:
        return ConvertedPrice(amount=base_price_vnd, currency=target_currency, is_stale=False)

    rate_row = get_latest_rate(base_currency=BASE_CURRENCY, target_currency=target_currency)
    if rate_row is None:
        # No rate has ever been synced for this pair — degrade exactly
        # like a stale one, since there's nothing trustworthy to show.
        return ConvertedPrice(amount=None, currency=target_currency, is_stale=True)

    amount = convert_price(
        base_price_vnd=base_price_vnd, rate=rate_row.rate, target_currency=target_currency
    )
    return ConvertedPrice(amount=amount, currency=target_currency, is_stale=rate_row.is_stale)
