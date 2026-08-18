"""Convert a VND Base Price into a target currency's integer minor unit —
guild.md §15 Slice 3, commit 9. One of the few places in the whole system
with a property-based (`hypothesis`) test rather than example-based only
(Issue #8's Decision Document): rounding bugs here compound silently
across every Order.

Rounding rule: round-half-up on the target currency's minor unit
(`ROUND_HALF_UP`) — a deliberate, documented choice, not Python/Decimal's
default `ROUND_HALF_EVEN` ("banker's rounding"), because a customer-facing
price should round consistently in one direction rather than alternating
based on whichever digit happens to be even.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from modules.pricing.constants import CURRENCY_MINOR_UNIT_EXPONENTS


class UnsupportedCurrencyError(Exception):
    """Raised for a target currency with no configured minor-unit exponent."""


def convert_price(*, base_price_vnd: int, rate: Decimal, target_currency: str) -> int:
    """`rate` is VND-per-1-unit-of `target_currency`'s major denomination
    (matching `integrations.exchange_rate`'s `Rate.rate` — e.g.
    VND->USD's rate is USD per VND). Returns an integer count of
    `target_currency`'s minor unit, rounded half-up.
    """
    if target_currency not in CURRENCY_MINOR_UNIT_EXPONENTS:
        raise UnsupportedCurrencyError(target_currency)

    exponent = CURRENCY_MINOR_UNIT_EXPONENTS[target_currency]
    major_amount = Decimal(base_price_vnd) * rate
    minor_amount = major_amount * (Decimal(10) ** exponent)
    return int(minor_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
