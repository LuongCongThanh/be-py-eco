"""PriceConverter — the Exchange Rate is resolved once, at construction,
and `convert` is pure from then on. These tests pin the *design* (where
the database read happens); `catalog/tests/test_storefront_query_count.py`
pins the benefit it exists for.
"""

from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from freezegun import freeze_time

from modules.pricing.constants import RATE_TTL_SECONDS
from modules.pricing.errors import UnsupportedCurrencyError
from modules.pricing.selectors.price_converter import get_price_converter
from modules.pricing.services.sync_exchange_rates import sync_exchange_rates


def test_unsupported_currency_is_rejected_at_construction() -> None:
    """A currency with no minor unit can never be converted, however many
    rates are synced — that is a client error, not a degraded read."""
    with pytest.raises(UnsupportedCurrencyError):
        get_price_converter(target_currency="EUR")


@pytest.mark.django_db
def test_base_currency_needs_no_rate_and_no_query() -> None:
    with CaptureQueriesContext(connection) as captured:
        converter = get_price_converter(target_currency="VND")

    assert converter.rate is None
    assert converter.is_stale is False
    assert len(captured) == 0


@pytest.mark.django_db
def test_factory_reads_the_rate_exactly_once_and_convert_reads_nothing() -> None:
    sync_exchange_rates()

    with CaptureQueriesContext(connection) as building:
        converter = get_price_converter(target_currency="USD")
    with CaptureQueriesContext(connection) as converting:
        for base_price in range(100_000, 100_010):
            converter.convert(base_price)

    assert len(building) == 1
    assert len(converting) == 0


@pytest.mark.django_db
def test_missing_rate_degrades_instead_of_raising() -> None:
    """USD is supported but nothing has synced yet — an operational
    condition, told apart from an unsupported currency by degrading."""
    converter = get_price_converter(target_currency="USD")

    result = converter.convert(150_000)

    assert converter.rate is None
    assert result.amount is None
    assert result.is_stale is True


@pytest.mark.django_db
def test_expired_rate_still_converts_but_flags_staleness() -> None:
    with freeze_time("2026-01-01T00:00:00Z") as frozen:
        sync_exchange_rates()
        frozen.tick(delta=timedelta(seconds=RATE_TTL_SECONDS + 1))

        converter = get_price_converter(target_currency="USD")
        result = converter.convert(150_000)

    assert converter.is_stale is True
    assert result.amount is not None
    assert result.is_stale is True


@pytest.mark.django_db
def test_none_base_price_is_never_stale_even_on_a_stale_converter() -> None:
    """A Product with no Base Price has nothing to convert, so the
    freshness of the rate says nothing about it."""
    converter = get_price_converter(target_currency="USD")  # no rate synced

    result = converter.convert(None)

    assert converter.is_stale is True
    assert result.amount is None
    assert result.is_stale is False


@pytest.mark.django_db
def test_exposes_the_rate_it_used_so_slice_5_can_lock_it() -> None:
    sync_exchange_rates()

    converter = get_price_converter(target_currency="USD")

    assert converter.rate is not None
    assert converter.rate.target_currency == "USD"
    assert converter.rate.source
