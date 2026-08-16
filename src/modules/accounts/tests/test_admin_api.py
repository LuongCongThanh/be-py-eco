"""API test: Master Admin creates Staff; MFA gates sensitive actions —
Issue #6 commit 11's verify criterion.
"""

import base64
from binascii import unhexlify
from typing import cast

import pytest
from django_otp.oath import totp
from rest_framework import status
from rest_framework.test import APIClient

from modules.accounts.models import Staff
from modules.accounts.services.mfa import confirm_mfa_setup, start_mfa_setup
from modules.accounts.tests.factories import StaffFactory
from modules.audit.models import AuditLogEntry


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _staff_login(api_client: APIClient, email: str, password: str) -> dict:
    response = api_client.post(
        "/api/v1/admin/staff/login", {"email": email, "password": password}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["data"]


def _code_from_provisioning_uri(provisioning_uri: str) -> str:
    secret_b32 = provisioning_uri.split("secret=")[1].split("&")[0]
    key = base64.b32decode(secret_b32 + "=" * (-len(secret_b32) % 8))
    return str(totp(key)).zfill(6)


@pytest.mark.django_db
def test_master_admin_creates_store_manager_blocked_until_mfa_setup(
    api_client: APIClient,
) -> None:
    master_admin = cast(Staff, StaffFactory(role=Staff.Role.MASTER_ADMIN, mfa_confirmed=True))
    admin_tokens = _staff_login(api_client, master_admin.email, "a-strong-password-123")
    admin_auth = {
        "Authorization": f"Bearer {admin_tokens['access']}",
        "Idempotency-Key": "create-staff-1",
    }

    create_response = api_client.post(
        "/api/v1/admin/staff",
        {
            "email": "newmanager@example.com",
            "password": "a-strong-password-123",
            "role": "store_manager",
        },
        format="json",
        headers=admin_auth,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    audit_entry = AuditLogEntry.objects.get(action="accounts.create_staff")
    assert audit_entry.ip_address  # populated from the real HTTP request, not None
    assert audit_entry.request_id

    manager_tokens = _staff_login(api_client, "newmanager@example.com", "a-strong-password-123")
    manager_auth = {"Authorization": f"Bearer {manager_tokens['access']}"}

    register_response = api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "victim@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    customer_id = register_response.json()["data"]["id"]

    blocked_response = api_client.post(
        f"/api/v1/admin/customers/{customer_id}/disable",
        {"reason": "Confirmed fraud report"},
        format="json",
        headers=manager_auth,
    )
    assert blocked_response.status_code == status.HTTP_403_FORBIDDEN
    assert blocked_response.json()["code"] == "accounts.mfa_not_configured"

    setup_response = api_client.post("/api/v1/admin/staff/mfa/setup", headers=manager_auth)
    assert setup_response.status_code == status.HTTP_200_OK
    provisioning_uri = setup_response.json()["data"]["provisioning_uri"]
    code = _code_from_provisioning_uri(provisioning_uri)

    confirm_response = api_client.post(
        "/api/v1/admin/staff/mfa/confirm", {"token": code}, format="json", headers=manager_auth
    )
    assert confirm_response.status_code == status.HTTP_204_NO_CONTENT

    allowed_response = api_client.post(
        f"/api/v1/admin/customers/{customer_id}/disable",
        {"reason": "Confirmed fraud report"},
        format="json",
        headers={**manager_auth, "Idempotency-Key": "disable-1"},
    )
    assert allowed_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_non_master_admin_cannot_create_staff(api_client: APIClient) -> None:
    manager = cast(Staff, StaffFactory(role=Staff.Role.STORE_MANAGER))
    tokens = _staff_login(api_client, manager.email, "a-strong-password-123")
    auth = {"Authorization": f"Bearer {tokens['access']}"}

    response = api_client.post(
        "/api/v1/admin/staff",
        {"email": "x@example.com", "password": "a-strong-password-123", "role": "order_staff"},
        format="json",
        headers=auth,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["code"] == "accounts.insufficient_permission"


@pytest.mark.django_db
def test_customer_jwt_cannot_call_admin_endpoints(api_client: APIClient) -> None:
    register_response = api_client.post(
        "/api/v1/storefront/accounts/register",
        {"email": "notstaff@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    assert register_response.status_code == status.HTTP_201_CREATED
    login_response = api_client.post(
        "/api/v1/storefront/accounts/login",
        {"email": "notstaff@example.com", "password": "a-strong-password-123"},
        format="json",
    )
    access = login_response.json()["data"]["access"]

    response = api_client.post(
        "/api/v1/admin/staff",
        {"email": "x@example.com", "password": "a-strong-password-123", "role": "order_staff"},
        format="json",
        headers={"Authorization": f"Bearer {access}"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_master_admin_resets_a_staff_members_mfa(api_client: APIClient) -> None:
    master_admin = cast(Staff, StaffFactory(role=Staff.Role.MASTER_ADMIN, mfa_confirmed=True))
    target = cast(Staff, StaffFactory(role=Staff.Role.ORDER_STAFF))
    device, _ = start_mfa_setup(staff=target)
    confirm_mfa_setup(staff=target, token=str(totp(unhexlify(device.key))).zfill(6))

    admin_tokens = _staff_login(api_client, master_admin.email, "a-strong-password-123")
    admin_auth = {
        "Authorization": f"Bearer {admin_tokens['access']}",
        "Idempotency-Key": "reset-mfa-1",
    }

    response = api_client.post(f"/api/v1/admin/staff/{target.id}/mfa/reset", headers=admin_auth)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    target.refresh_from_db()
    assert target.has_confirmed_mfa is False
