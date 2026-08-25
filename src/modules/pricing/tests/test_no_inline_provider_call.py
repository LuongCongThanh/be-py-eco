"""A catalog read must never call the exchange-rate provider directly —
guild.md §15 Slice 3, commit 12's verify criterion, and guild.md §3.7
("Không gọi rate provider trong từng request đọc catalog").

Covers both read paths: the single-price convenience and the bound
converter every list read now goes through.
"""

from unittest.mock import patch

import pytest

from modules.pricing.selectors.get_converted_price import get_converted_price
from modules.pricing.selectors.price_converter import get_price_converter
from modules.pricing.services.sync_exchange_rates import sync_exchange_rates

PROVIDER = "integrations.exchange_rate.fake.FakeExchangeRateProvider.get_rate"


@pytest.mark.django_db
def test_get_converted_price_never_calls_the_provider() -> None:
    sync_exchange_rates()  # seed a rate the normal way, once, out-of-band

    with patch(PROVIDER) as mock_get_rate:
        get_converted_price(base_price_vnd=150_000, target_currency="USD")
        get_converted_price(base_price_vnd=200_000, target_currency="USD")

    mock_get_rate.assert_not_called()


@pytest.mark.django_db
def test_missing_rate_still_never_calls_the_provider() -> None:
    """Even the degrade-to-stale path (no rate synced yet) must not fall
    back to an inline provider call."""
    with patch(PROVIDER) as mock_get_rate:
        get_converted_price(base_price_vnd=150_000, target_currency="USD")

    mock_get_rate.assert_not_called()


@pytest.mark.django_db
def test_price_converter_never_calls_the_provider() -> None:
    sync_exchange_rates()

    with patch(PROVIDER) as mock_get_rate:
        converter = get_price_converter(target_currency="USD")
        converter.convert(150_000)
        converter.convert(200_000)

    mock_get_rate.assert_not_called()


@pytest.mark.django_db
def test_price_converter_never_calls_the_provider_when_no_rate_is_synced() -> None:
    with patch(PROVIDER) as mock_get_rate:
        get_price_converter(target_currency="USD").convert(150_000)

    mock_get_rate.assert_not_called()
