"""Convert VND Base Prices into one Transaction Currency for display,
with the Exchange Rate resolved exactly once — guild.md §15 Slice 3,
commits 10-12, reshaped so a list read costs one rate lookup instead of
one per row.

The split is deliberate: `get_price_converter` is the only part that
touches the database, and `PriceConverter.convert` is pure. A caller
rendering N prices builds the converter once, outside its loop, and the
cost of the read no longer scales with the number of Products.

`is_stale` lives on the converter, not on each price: a single response
cannot have one price computed from a fresh rate and the next from a
stale one. `rate` is exposed read-only so Slice 5 can lock the exact
Exchange Rate a Customer was shown, rather than re-reading and risking a
different row.

Staleness here only degrades the display (amount `None` for a rate that
was never synced, a visible flag for one that expired). Hard-blocking
checkout on a stale rate is Slice 5's concern, per guild.md §3.7.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.pricing.constants import BASE_CURRENCY, CURRENCY_MINOR_UNIT_EXPONENTS
from modules.pricing.errors import UnsupportedCurrencyError
from modules.pricing.models.exchange_rate import ExchangeRate
from modules.pricing.selectors.get_latest_rate import get_latest_rate
from modules.pricing.services.convert_price import convert_price


@dataclass(frozen=True)
class ConvertedPrice:
    amount: int | None
    currency: str
    is_stale: bool


@dataclass(frozen=True)
class PriceConverter:
    """Bound to one Transaction Currency and one Exchange Rate snapshot.

    `rate` is `None` in two distinct cases, told apart by `target_currency`:
    the Base Currency needs no conversion at all, and a currency whose rate
    has never been synced has nothing trustworthy to convert with.
    """

    target_currency: str
    rate: ExchangeRate | None
    is_stale: bool

    def convert(self, base_price_vnd: int | None) -> ConvertedPrice:
        if base_price_vnd is None:
            # No price at all — the freshness of a rate says nothing about
            # a Product that has no Base Price to convert.
            return ConvertedPrice(amount=None, currency=self.target_currency, is_stale=False)

        if self.target_currency == BASE_CURRENCY:
            return ConvertedPrice(
                amount=base_price_vnd, currency=self.target_currency, is_stale=False
            )

        if self.rate is None:
            return ConvertedPrice(amount=None, currency=self.target_currency, is_stale=True)

        amount = convert_price(
            base_price_vnd=base_price_vnd,
            rate=self.rate.rate,
            target_currency=self.target_currency,
        )
        return ConvertedPrice(amount=amount, currency=self.target_currency, is_stale=self.is_stale)


def get_price_converter(*, target_currency: str) -> PriceConverter:
    """Resolve the Exchange Rate for `target_currency` once.

    A currency with no configured minor unit is a client error, not a
    degraded read: it can never be converted, however many rates are
    synced. That is a different thing from a supported currency whose rate
    is missing or expired, which degrades with `is_stale` instead.

    Membership of `SUPPORTED_TARGET_CURRENCIES` is deliberately *not* the
    test — that constant lists what the periodic sync fetches, not what a
    Customer may ask for. See ADR-0008.
    """
    if target_currency not in CURRENCY_MINOR_UNIT_EXPONENTS:
        raise UnsupportedCurrencyError(target_currency)

    if target_currency == BASE_CURRENCY:
        # No Exchange Rate participates, so none is recorded — inventing a
        # rate of 1 here would hand Slice 5 a fact that never happened.
        return PriceConverter(target_currency=target_currency, rate=None, is_stale=False)

    rate_row = get_latest_rate(base_currency=BASE_CURRENCY, target_currency=target_currency)
    if rate_row is None:
        return PriceConverter(target_currency=target_currency, rate=None, is_stale=True)

    return PriceConverter(
        target_currency=target_currency, rate=rate_row, is_stale=rate_row.is_stale
    )
