"""Storefront read endpoints — Issue #7 commit 13's verify criterion: a
draft Product is invisible on the Storefront endpoint while visible on
the Admin endpoint."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from modules.catalog.models.product import ProductStatus
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.translation.services.set_translation import set_translation


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _make_published_product(sku: str):
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    set_translation(entity=product, locale="en", field="name", value="T-shirt")
    create_variant(product=product, sku=sku, base_price_vnd=150_000, weight_grams=200)
    ready_upload = MediaUpload.objects.create(
        storage_key=f"quarantine/{sku}",
        declared_content_type="image/png",
        declared_size_bytes=10,
        status=MediaUploadStatus.READY,
    )
    attach_media_to_product(media_upload=ready_upload, product=product)
    return publish_product(product=product)


@pytest.mark.django_db
def test_draft_product_is_invisible_on_storefront_list(api_client: APIClient) -> None:
    draft = create_product(primary_category=create_category())
    set_translation(entity=draft, locale="vi", field="name", value="Bản nháp")

    response = api_client.get("/api/v1/storefront/catalog/products")

    ids = [item["id"] for item in response.json()["data"]]
    assert str(draft.id) not in ids


@pytest.mark.django_db
def test_draft_product_404s_on_storefront_detail(api_client: APIClient) -> None:
    draft = create_product(primary_category=create_category())

    response = api_client.get(f"/api/v1/storefront/catalog/products/{draft.id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_published_product_visible_with_default_locale_by_default(api_client: APIClient) -> None:
    product = _make_published_product("SKU-SF-1")

    response = api_client.get(f"/api/v1/storefront/catalog/products/{product.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["name"] == "Áo thun"
    assert response["Content-Language"] == "vi"


@pytest.mark.django_db
def test_published_product_localized_via_accept_language(api_client: APIClient) -> None:
    product = _make_published_product("SKU-SF-2")

    response = api_client.get(
        f"/api/v1/storefront/catalog/products/{product.id}",
        headers={"accept-language": "en-US,en;q=0.9"},
    )

    data = response.json()["data"]
    assert data["name"] == "T-shirt"
    assert response["Content-Language"] == "en"


@pytest.mark.django_db
def test_published_product_appears_in_storefront_list(api_client: APIClient) -> None:
    product = _make_published_product("SKU-SF-3")

    response = api_client.get("/api/v1/storefront/catalog/products")

    ids = [item["id"] for item in response.json()["data"]]
    assert str(product.id) in ids
    assert product.status == ProductStatus.ACTIVE
