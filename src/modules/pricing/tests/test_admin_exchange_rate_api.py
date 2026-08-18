"""Admin Exchange Rate visibility — guild.md §15 Slice 3's acceptance
criterion: a Store Manager can view current Exchange Rates including
source, timestamp, and expiry."""

from typing import cast

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from modules.accounts.models import Staff
from modules.accounts.tests.factories import StaffFactory
from modules.pricing.services.sync_exchange_rates import sync_exchange_rates


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _staff_auth_header(api_client: APIClient) -> dict:
    staff = cast(Staff, StaffFactory(mfa_confirmed=True))
    response = api_client.post(
        "/api/v1/admin/staff/login",
        {"email": staff.email, "password": "a-strong-password-123"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    access = response.json()["data"]["access"]
    return {"Authorization": f"Bearer {access}"}


@pytest.mark.django_db
def test_lists_current_rates_with_source_timestamp_and_expiry(api_client: APIClient) -> None:
    auth = _staff_auth_header(api_client)
    sync_exchange_rates()

    response = api_client.get("/api/v1/admin/pricing/exchange-rates", headers=auth)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert len(data) >= 1
    row = data[0]
    assert row["base_currency"] == "VND"
    assert row["source"]
    assert row["fetched_at"]
    assert row["expires_at"]
    assert "is_stale" in row


@pytest.mark.django_db
def test_no_synced_rates_returns_empty_list(api_client: APIClient) -> None:
    auth = _staff_auth_header(api_client)

    response = api_client.get("/api/v1/admin/pricing/exchange-rates", headers=auth)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []


@pytest.mark.django_db
def test_unauthenticated_request_is_rejected(api_client: APIClient) -> None:
    response = api_client.get("/api/v1/admin/pricing/exchange-rates")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
