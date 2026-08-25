"""ExchangeRate sync + staleness — guild.md §15 Slice 3, commit 8's
verify criterion: advance time via freezegun and confirm a stale rate is
distinguishable from a fresh one."""

from datetime import timedelta

import pytest
from freezegun import freeze_time

from modules.pricing.constants import RATE_TTL_SECONDS
from modules.pricing.models.exchange_rate import ExchangeRate
from modules.pricing.selectors.get_latest_rate import get_latest_rate
from modules.pricing.services.sync_exchange_rates import sync_exchange_rates


@pytest.mark.django_db
def test_sync_creates_a_rate_row_per_target_currency() -> None:
    synced = sync_exchange_rates()

    assert synced == ExchangeRate.objects.count()
    assert synced >= 1


@pytest.mark.django_db
def test_freshly_synced_rate_is_not_stale() -> None:
    with freeze_time("2026-01-01T00:00:00Z"):
        sync_exchange_rates()

        rate = get_latest_rate(base_currency="VND", target_currency="USD")

        assert rate is not None
        assert rate.is_stale is False


@pytest.mark.django_db
def test_rate_becomes_stale_after_its_expiry() -> None:
    with freeze_time("2026-01-01T00:00:00Z") as frozen:
        sync_exchange_rates()
        rate = get_latest_rate(base_currency="VND", target_currency="USD")
        assert rate is not None

        frozen.tick(delta=timedelta(seconds=RATE_TTL_SECONDS + 1))

        assert rate.is_stale is True


@pytest.mark.django_db
def test_get_latest_rate_returns_the_most_recently_synced_row() -> None:
    with freeze_time("2026-01-01T00:00:00Z"):
        sync_exchange_rates()
    with freeze_time("2026-01-02T00:00:00Z"):
        sync_exchange_rates()

    rate = get_latest_rate(base_currency="VND", target_currency="USD")

    assert rate is not None
    assert rate.fetched_at.year == 2026
    assert rate.fetched_at.month == 1
    assert rate.fetched_at.day == 2


@pytest.mark.django_db
def test_get_latest_rate_returns_none_when_nothing_synced_yet() -> None:
    rate = get_latest_rate(base_currency="VND", target_currency="EUR")

    assert rate is None
