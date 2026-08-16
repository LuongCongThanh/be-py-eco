"""API test: exceeding the configured threshold returns 429 (guild.md
Issue #6 commit 12's verify criterion), per IP and per account.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from common.api.throttling import AuthAccountRateThrottle, AuthIPRateThrottle


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_login_is_throttled_per_ip_once_the_limit_is_exceeded(
    monkeypatch: pytest.MonkeyPatch, api_client: APIClient
) -> None:
    monkeypatch.setitem(AuthIPRateThrottle.THROTTLE_RATES, "auth_ip", "1/min")
    monkeypatch.setitem(AuthAccountRateThrottle.THROTTLE_RATES, "auth_account", "100/min")
    payload = {"email": "throttleip@example.com", "password": "wrong-password"}

    first = api_client.post("/api/v1/storefront/accounts/login", payload, format="json")
    assert first.status_code == status.HTTP_401_UNAUTHORIZED  # wrong password, not throttled yet

    second = api_client.post("/api/v1/storefront/accounts/login", payload, format="json")
    assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_login_is_throttled_per_account_even_from_different_ips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(AuthIPRateThrottle.THROTTLE_RATES, "auth_ip", "100/min")
    monkeypatch.setitem(AuthAccountRateThrottle.THROTTLE_RATES, "auth_account", "1/min")
    payload = {"email": "throttleaccount@example.com", "password": "wrong-password"}
    client_a = APIClient(REMOTE_ADDR="10.0.0.1")
    client_b = APIClient(REMOTE_ADDR="10.0.0.2")

    first = client_a.post("/api/v1/storefront/accounts/login", payload, format="json")
    assert first.status_code == status.HTTP_401_UNAUTHORIZED

    second = client_b.post("/api/v1/storefront/accounts/login", payload, format="json")
    assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_registration_is_throttled_per_ip(
    monkeypatch: pytest.MonkeyPatch, api_client: APIClient
) -> None:
    monkeypatch.setitem(AuthIPRateThrottle.THROTTLE_RATES, "auth_ip", "1/min")
    monkeypatch.setitem(AuthAccountRateThrottle.THROTTLE_RATES, "auth_account", "100/min")

    first = api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "throttlereg1@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    assert first.status_code == status.HTTP_201_CREATED

    second = api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "throttlereg2@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS
