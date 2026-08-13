"""API test: register -> verify email journey (guild.md §10.2 journey #1,
partial — login is a later commit)."""

import pytest
from django.core import mail
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
