"""A catalog read must never call the exchange-rate provider directly —
guild.md §15 Slice 3, commit 12's verify criterion."""

from unittest.mock import patch

import pytest

from modules.pricing.selectors.get_converted_price import get_converted_price
from modules.pricing.services.sync_exchange_rates import sync_exchange_rates


@pytest.mark.django_db
def test_get_converted_price_never_calls_the_provider() -> None:
    sync_exchange_rates()  # seed a rate the normal way, once, out-of-band

    target = "integrations.exchange_rate.fake.FakeExchangeRateProvider.get_rate"
    with patch(target) as mock_get_rate:
        get_converted_price(base_price_vnd=150_000, target_currency="USD")
        get_converted_price(base_price_vnd=200_000, target_currency="USD")

    mock_get_rate.assert_not_called()


@pytest.mark.django_db
def test_missing_rate_still_never_calls_the_provider() -> None:
    """Even the degrade-to-stale path (no rate synced yet) must not fall
    back to an inline provider call."""
    target = "integrations.exchange_rate.fake.FakeExchangeRateProvider.get_rate"
    with patch(target) as mock_get_rate:
        get_converted_price(base_price_vnd=150_000, target_currency="USD")

    mock_get_rate.assert_not_called()
