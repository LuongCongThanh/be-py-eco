"""convert_price rounding/precision invariants — guild.md §15 Slice 3,
commit 9's verify criterion and §10.3's explicit call-out for a
property-based test on currency conversion.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from modules.pricing.services.convert_price import UnsupportedCurrencyError, convert_price

_prices = st.integers(min_value=0, max_value=10**12)
_rates = st.decimals(
    min_value=Decimal("0.0000001"), max_value=Decimal("100000"), places=10, allow_nan=False
)


@given(price=_prices, rate=_rates)
def test_converted_amount_is_always_a_non_negative_integer(price, rate) -> None:
    converted = convert_price(base_price_vnd=price, rate=rate, target_currency="USD")

    assert isinstance(converted, int)
    assert converted >= 0


@given(price=_prices)
def test_identity_rate_of_one_is_a_no_op_for_vnd(price) -> None:
    converted = convert_price(base_price_vnd=price, rate=Decimal("1"), target_currency="VND")

    assert converted == price


@given(price=_prices, rate=_rates)
def test_vnd_target_never_produces_fractional_minor_units(price, rate) -> None:
    """VND has a zero-decimal minor unit — every VND conversion must land
    on a whole VND, by construction (exponent 0)."""
    converted = convert_price(base_price_vnd=price, rate=rate, target_currency="VND")

    assert converted == int(converted)


@given(price_a=_prices, price_b=_prices, rate=_rates)
def test_conversion_is_monotonic_in_price(price_a, price_b, rate) -> None:
    if price_a > price_b:
        price_a, price_b = price_b, price_a

    converted_a = convert_price(base_price_vnd=price_a, rate=rate, target_currency="USD")
    converted_b = convert_price(base_price_vnd=price_b, rate=rate, target_currency="USD")

    assert converted_a <= converted_b


def test_zero_price_converts_to_zero() -> None:
    assert convert_price(base_price_vnd=0, rate=Decimal("0.00004"), target_currency="USD") == 0


def test_known_value_rounds_half_up() -> None:
    # 25 VND * 0.00004 USD/VND = 0.001 USD = 0.1 cents -> rounds up to 1 cent.
    result = convert_price(base_price_vnd=25, rate=Decimal("0.00004"), target_currency="USD")

    assert result == 0  # 25 * 0.00004 = 0.001 USD = 0.1 cent -> rounds to 0
    # sanity: a value that clearly rounds up
    result_up = convert_price(base_price_vnd=125, rate=Decimal("0.00004"), target_currency="USD")
    assert result_up == 1  # 125 * 0.00004 = 0.005 USD = 0.5 cent -> half-up rounds to 1


def test_unsupported_currency_raises() -> None:
    with pytest.raises(UnsupportedCurrencyError):
        convert_price(base_price_vnd=100, rate=Decimal("1"), target_currency="EUR")
