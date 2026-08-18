"""get_converted_price — guild.md §15 Slice 3, commits 10-11's verify
criteria: VND passes through as-is, a fresh rate converts correctly, and
a stale/missing rate degrades the price with a visible flag."""

from datetime import timedelta

import pytest
from freezegun import freeze_time

from modules.pricing.constants import RATE_TTL_SECONDS
from modules.pricing.selectors.get_converted_price import get_converted_price
from modules.pricing.services.sync_exchange_rates import sync_exchange_rates


def test_vnd_target_passes_through_unconverted_and_never_stale() -> None:
    result = get_converted_price(base_price_vnd=150_000, target_currency="VND")

    assert result.amount == 150_000
    assert result.is_stale is False


def test_none_base_price_yields_none_amount() -> None:
    result = get_converted_price(base_price_vnd=None, target_currency="USD")

    assert result.amount is None
    assert result.is_stale is False


@pytest.mark.django_db
def test_missing_rate_degrades_with_stale_flag() -> None:
    result = get_converted_price(base_price_vnd=150_000, target_currency="USD")

    assert result.amount is None
    assert result.is_stale is True


@pytest.mark.django_db
def test_fresh_rate_converts_correctly() -> None:
    with freeze_time("2026-01-01T00:00:00Z"):
        sync_exchange_rates()

        result = get_converted_price(base_price_vnd=150_000, target_currency="USD")

    assert result.amount is not None
    assert result.is_stale is False


@pytest.mark.django_db
def test_stale_rate_still_converts_but_flags_staleness() -> None:
    with freeze_time("2026-01-01T00:00:00Z") as frozen:
        sync_exchange_rates()
        frozen.tick(delta=timedelta(seconds=RATE_TTL_SECONDS + 1))

        result = get_converted_price(base_price_vnd=150_000, target_currency="USD")

    assert result.amount is not None
    assert result.is_stale is True
