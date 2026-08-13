"""API test: register -> verify email journey (guild.md §10.2 journey #1,
partial — login is a later commit)."""

import json

import pytest
from django.core import mail
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from modules.accounts.models import Customer


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_register_then_verify_email_journey(api_client: APIClient) -> None:
    response = api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "journey@example.com", "password": "a-strong-password-123"},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["data"]["email"] == "journey@example.com"
    assert body["data"]["email_verified"] is False
    assert body["meta"]["request_id"]

    raw_token = mail.outbox[0].body.rsplit(": ", 1)[-1].strip()

    verify_response = api_client.post(
        "/api/v1/storefront/accounts/verify-email", {"token": raw_token}, format="json"
    )

    assert verify_response.status_code == status.HTTP_200_OK
    assert verify_response.json()["data"]["email_verified"] is True

    customer = Customer.objects.get(email="journey@example.com")
    assert customer.is_email_verified is True


@pytest.mark.django_db
def test_register_rejects_duplicate_email(api_client: APIClient) -> None:
    api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "dupe@example.com", "password": "a-strong-password-123"},
        format="json",
    )

    response = api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "dupe@example.com", "password": "another-strong-password-456"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["errors"][0]["code"] == "email_taken"


@pytest.mark.django_db
def test_verify_email_with_invalid_token_returns_problem_details(api_client: APIClient) -> None:
    response = api_client.post(
        "/api/v1/storefront/accounts/verify-email", {"token": "bogus"}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["code"] == "accounts.invalid_verification_token"


def _register(api_client: APIClient, email: str, password: str) -> None:
    response = api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": email, "password": password},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


def _login(api_client: APIClient, email: str, password: str) -> dict:
    response = api_client.post(
        "/api/v1/storefront/accounts/login",
        {"email": email, "password": password},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["data"]


@pytest.mark.django_db
def test_login_then_me_returns_the_authenticated_customer(api_client: APIClient) -> None:
    _register(api_client, "loginjourney@example.com", "a-strong-password-123")

    login_response = api_client.post(
        "/api/v1/storefront/accounts/login",
        {"email": "loginjourney@example.com", "password": "a-strong-password-123"},
        format="json",
    )

    assert login_response.status_code == status.HTTP_200_OK
    access = login_response.json()["data"]["access"]
    assert login_response.json()["data"]["refresh"]

    me_response = api_client.get(
        "/api/v1/storefront/accounts/me", HTTP_AUTHORIZATION=f"Bearer {access}"
    )

    assert me_response.status_code == status.HTTP_200_OK
    assert me_response.json()["data"]["email"] == "loginjourney@example.com"


@pytest.mark.django_db
def test_login_rejects_wrong_password(api_client: APIClient) -> None:
    _register(api_client, "wrongpass@example.com", "a-strong-password-123")

    response = api_client.post(
        "/api/v1/storefront/accounts/login",
        {"email": "wrongpass@example.com", "password": "not-the-password"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["code"] == "accounts.invalid_credentials"


@pytest.mark.django_db
def test_me_requires_authentication(api_client: APIClient) -> None:
    response = api_client.get("/api/v1/storefront/accounts/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_access_token_expires_after_its_configured_lifetime(api_client: APIClient) -> None:
    with freeze_time("2026-01-01 00:00:00"):
        _register(api_client, "expiry@example.com", "a-strong-password-123")
        login_response = api_client.post(
            "/api/v1/storefront/accounts/login",
            {"email": "expiry@example.com", "password": "a-strong-password-123"},
            format="json",
        )
        access = login_response.json()["data"]["access"]

        still_valid = api_client.get(
            "/api/v1/storefront/accounts/me", HTTP_AUTHORIZATION=f"Bearer {access}"
        )
        assert still_valid.status_code == status.HTTP_200_OK

    with freeze_time("2026-01-01 00:16:00"):  # ACCESS_TOKEN_LIFETIME is 15 minutes
        expired = api_client.get(
            "/api/v1/storefront/accounts/me", HTTP_AUTHORIZATION=f"Bearer {access}"
        )

    assert expired.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_token_refresh_rotates_and_rejects_reuse(api_client: APIClient) -> None:
    _register(api_client, "refreshapi@example.com", "a-strong-password-123")
    tokens = _login(api_client, "refreshapi@example.com", "a-strong-password-123")
    old_refresh = tokens["refresh"]

    refresh_response = api_client.post(
        "/api/v1/storefront/accounts/token/refresh", {"refresh": old_refresh}, format="json"
    )

    assert refresh_response.status_code == status.HTTP_200_OK
    new_refresh = refresh_response.json()["data"]["refresh"]
    assert new_refresh != old_refresh

    reuse_response = api_client.post(
        "/api/v1/storefront/accounts/token/refresh", {"refresh": old_refresh}, format="json"
    )

    assert reuse_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert reuse_response.json()["code"] == "accounts.invalid_refresh_token"


@pytest.mark.django_db
def test_session_list_then_revoke_one(api_client: APIClient) -> None:
    _register(api_client, "sessapi1@example.com", "a-strong-password-123")
    tokens = _login(api_client, "sessapi1@example.com", "a-strong-password-123")
    auth = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}

    list_response = api_client.get("/api/v1/storefront/accounts/sessions", **auth)
    assert list_response.status_code == status.HTTP_200_OK
    sessions = list_response.json()["data"]
    assert len(sessions) == 1
    session_id = sessions[0]["id"]

    revoke_response = api_client.post(
        f"/api/v1/storefront/accounts/sessions/{session_id}/revoke", **auth
    )
    assert revoke_response.status_code == status.HTTP_204_NO_CONTENT

    list_after = api_client.get("/api/v1/storefront/accounts/sessions", **auth)
    assert list_after.json()["data"] == []


@pytest.mark.django_db
def test_revoke_all_sessions(api_client: APIClient) -> None:
    _register(api_client, "sessapi2@example.com", "a-strong-password-123")
    _login(api_client, "sessapi2@example.com", "a-strong-password-123")
    tokens = _login(api_client, "sessapi2@example.com", "a-strong-password-123")
    auth = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}

    revoke_all_response = api_client.post("/api/v1/storefront/accounts/sessions/revoke-all", **auth)
    assert revoke_all_response.status_code == status.HTTP_204_NO_CONTENT

    list_after = api_client.get("/api/v1/storefront/accounts/sessions", **auth)
    assert list_after.json()["data"] == []


@pytest.mark.django_db
def test_google_login_journey(api_client: APIClient) -> None:
    id_token = json.dumps({"sub": "google-api-1", "email": "googleapi@example.com"})

    response = api_client.post(
        "/api/v1/storefront/accounts/login/google", {"id_token": id_token}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    access = response.json()["data"]["access"]

    me_response = api_client.get(
        "/api/v1/storefront/accounts/me", HTTP_AUTHORIZATION=f"Bearer {access}"
    )
    assert me_response.json()["data"]["email"] == "googleapi@example.com"


@pytest.mark.django_db
def test_google_login_rejects_invalid_id_token(api_client: APIClient) -> None:
    response = api_client.post(
        "/api/v1/storefront/accounts/login/google", {"id_token": "garbage"}, format="json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["code"] == "accounts.invalid_google_token"


@pytest.mark.django_db
def test_password_reset_journey(api_client: APIClient) -> None:
    _register(api_client, "resetapi@example.com", "a-strong-password-123")

    request_response = api_client.post(
        "/api/v1/storefront/accounts/password-reset/request",
        {"email": "resetapi@example.com"},
        format="json",
    )
    assert request_response.status_code == status.HTTP_202_ACCEPTED

    raw_token = mail.outbox[-1].body.rsplit(": ", 1)[-1].strip()
    confirm_response = api_client.post(
        "/api/v1/storefront/accounts/password-reset/confirm",
        {"token": raw_token, "new_password": "brand-new-password-789"},
        format="json",
    )
    assert confirm_response.status_code == status.HTTP_200_OK

    login_response = api_client.post(
        "/api/v1/storefront/accounts/login",
        {"email": "resetapi@example.com", "password": "brand-new-password-789"},
        format="json",
    )
    assert login_response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_email_change_journey(api_client: APIClient) -> None:
    _register(api_client, "changeold@example.com", "a-strong-password-123")
    tokens = _login(api_client, "changeold@example.com", "a-strong-password-123")
    auth = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}

    request_response = api_client.post(
        "/api/v1/storefront/accounts/email-change/request",
        {"new_email": "changenew@example.com"},
        format="json",
        **auth,
    )
    assert request_response.status_code == status.HTTP_202_ACCEPTED

    raw_token = mail.outbox[-1].body.rsplit(": ", 1)[-1].strip()
    confirm_response = api_client.post(
        "/api/v1/storefront/accounts/email-change/confirm", {"token": raw_token}, format="json"
    )

    assert confirm_response.status_code == status.HTTP_200_OK
    assert confirm_response.json()["data"]["email"] == "changenew@example.com"


@pytest.mark.django_db
def test_email_change_request_requires_authentication(api_client: APIClient) -> None:
    response = api_client.post(
        "/api/v1/storefront/accounts/email-change/request",
        {"new_email": "whatever@example.com"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
