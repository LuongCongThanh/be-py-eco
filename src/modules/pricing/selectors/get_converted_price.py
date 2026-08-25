"""Convert a single VND Base Price into a Customer's selected Transaction
Currency for display — guild.md §15 Slice 3, commits 10-12.

A one-call convenience over `price_converter`, for the genuine
single-Product read. Anything rendering more than one price should build
a `PriceConverter` once and loop over `convert` instead — calling this in
a loop re-reads the Exchange Rate on every iteration.

Like the converter it delegates to, this never calls the provider
adapter: a catalog or search read can run as often as it likes without
ever blocking on the exchange-rate provider (guild.md §3.7, enforced by
`tests/test_no_inline_provider_call.py`).
"""

from __future__ import annotations

from modules.pricing.selectors.price_converter import ConvertedPrice, get_price_converter

__all__ = ["ConvertedPrice", "get_converted_price"]


def get_converted_price(*, base_price_vnd: int | None, target_currency: str) -> ConvertedPrice:
    return get_price_converter(target_currency=target_currency).convert(base_price_vnd)
