"""Provider contract test — guild.md §15 Slice 3, commit 7's verify
criterion. The production adapter, whenever it lands (guild.md §16),
must satisfy this exact same suite; only `PROVIDERS` grows.
"""

from decimal import Decimal

import pytest

from integrations.exchange_rate.client import ExchangeRateProviderError
from integrations.exchange_rate.fake import FakeExchangeRateProvider

PROVIDERS = [FakeExchangeRateProvider]


@pytest.fixture(params=PROVIDERS)
def provider(request):
    return request.param()


def test_same_currency_rate_is_one(provider) -> None:
    rate = provider.get_rate("VND", "VND")

    assert rate.rate == Decimal("1")
    assert rate.base_currency == "VND"
    assert rate.target_currency == "VND"


def test_rate_is_a_positive_decimal(provider) -> None:
    rate = provider.get_rate("VND", "USD")

    assert isinstance(rate.rate, Decimal)
    assert rate.rate > 0


def test_rate_carries_source_and_fetched_at(provider) -> None:
    rate = provider.get_rate("VND", "USD")

    assert rate.source
    assert rate.fetched_at is not None


def test_unsupported_pair_raises_provider_error(provider) -> None:
    with pytest.raises(ExchangeRateProviderError):
        provider.get_rate("VND", "XYZ")
