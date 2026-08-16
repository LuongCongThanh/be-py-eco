"""API test: first-visit suggestion + manual override persisting across a
subsequent request (guild.md §3.2, Issue #6 commit 13's verify criterion).
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from modules.localization.tests.factories import SupportedCountryFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_suggestion_endpoint_reflects_accept_language(api_client: APIClient) -> None:
    SupportedCountryFactory()

    response = api_client.get(
        "/api/v1/storefront/localization/suggestion",
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == {"country_code": "VN", "locale": "en", "currency": "VND"}


@pytest.mark.django_db
def test_override_locale_preference_persists_across_a_subsequent_request(
    api_client: APIClient,
) -> None:
    SupportedCountryFactory()
    register_response = api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "localeapi@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    assert register_response.status_code == status.HTTP_201_CREATED

    login_response = api_client.post(
        "/api/v1/storefront/accounts/login",
        {"email": "localeapi@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access']}"}

    override_response = api_client.patch(
        "/api/v1/storefront/accounts/me/locale",
        {"locale": "en", "currency": "USD"},
        format="json",
        headers=headers,
    )
    assert override_response.status_code == status.HTTP_200_OK
    assert override_response.json()["data"]["preferred_locale"] == "en"

    me_response = api_client.get("/api/v1/storefront/accounts/me", headers=headers)
    assert me_response.json()["data"]["preferred_locale"] == "en"
    assert me_response.json()["data"]["preferred_currency"] == "USD"


@pytest.mark.django_db
def test_override_rejects_unsupported_currency(api_client: APIClient) -> None:
    SupportedCountryFactory()
    api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "badcurrency@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    login_response = api_client.post(
        "/api/v1/storefront/accounts/login",
        {"email": "badcurrency@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access']}"}

    response = api_client.patch(
        "/api/v1/storefront/accounts/me/locale",
        {"locale": "vi", "currency": "EUR"},
        format="json",
        headers=headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "localization.unsupported_currency"
