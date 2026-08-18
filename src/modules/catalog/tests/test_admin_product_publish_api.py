"""API test for the dedicated `publish` action endpoint — Issue #7
commit 7."""

from typing import cast

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from modules.accounts.models import Staff
from modules.accounts.tests.factories import StaffFactory
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
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
def test_publish_fails_with_409_when_no_ready_media_exists(api_client: APIClient) -> None:
    auth = _staff_auth_header(api_client)
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku="SKU-API-PUB-1", base_price_vnd=1000, weight_grams=1)

    response = api_client.post(f"/api/v1/admin/catalog/products/{product.id}/publish", headers=auth)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["code"] == "catalog.no_ready_media"


@pytest.mark.django_db
def test_publish_fails_with_409_for_missing_content_before_missing_media(
    api_client: APIClient,
) -> None:
    auth = _staff_auth_header(api_client)
    product = create_product(primary_category=create_category())

    response = api_client.post(f"/api/v1/admin/catalog/products/{product.id}/publish", headers=auth)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["code"] == "catalog.incomplete_default_locale_content"
