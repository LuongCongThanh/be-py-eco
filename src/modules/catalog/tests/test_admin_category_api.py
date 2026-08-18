"""API test: locale fallback + CMS-visible flag — Issue #7 commit 5's
verify criterion."""

from typing import cast

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from modules.accounts.models import Staff
from modules.accounts.tests.factories import StaffFactory
from modules.catalog.services.category_tree import create_category
from modules.translation.services.set_translation import set_translation


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
def test_missing_locale_falls_back_to_default_and_is_flagged(api_client: APIClient) -> None:
    auth = _staff_auth_header(api_client)
    category = create_category()
    set_translation(entity=category, locale="vi", field="name", value="Áo")

    response = api_client.get(
        f"/api/v1/admin/catalog/categories/{category.id}",
        {"locale": "en"},
        headers=auth,
    )

    assert response.status_code == status.HTTP_200_OK
    name = response.json()["data"]["name"]
    assert name["value"] == "Áo"
    assert name["locale"] == "vi"
    assert name["is_fallback"] is True


@pytest.mark.django_db
def test_present_locale_is_not_flagged_as_fallback(api_client: APIClient) -> None:
    auth = _staff_auth_header(api_client)
    category = create_category()
    set_translation(entity=category, locale="vi", field="name", value="Áo")
    set_translation(entity=category, locale="en", field="name", value="Shirt")

    response = api_client.get(
        f"/api/v1/admin/catalog/categories/{category.id}",
        {"locale": "en"},
        headers=auth,
    )

    name = response.json()["data"]["name"]
    assert name["value"] == "Shirt"
    assert name["is_fallback"] is False


@pytest.mark.django_db
def test_unauthenticated_request_is_rejected(api_client: APIClient) -> None:
    category = create_category()

    response = api_client.get(f"/api/v1/admin/catalog/categories/{category.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
