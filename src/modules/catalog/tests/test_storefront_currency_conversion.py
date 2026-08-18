"""Storefront price conversion — guild.md §15 Slice 3, commits 10-11's
verify criteria: the same Product in two currencies returns two
correctly-converted amounts, and a stale/missing rate flags the price."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.pricing.services.sync_exchange_rates import sync_exchange_rates
from modules.translation.services.set_translation import set_translation


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _make_published_product(sku: str):
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku=sku, base_price_vnd=250_000, weight_grams=100)
    ready_upload = MediaUpload.objects.create(
        storage_key=f"quarantine/{sku}",
        declared_content_type="image/png",
        declared_size_bytes=10,
        status=MediaUploadStatus.READY,
    )
    attach_media_to_product(media_upload=ready_upload, product=product)
    return publish_product(product=product)


@pytest.mark.django_db
def test_default_currency_is_vnd_unconverted(api_client: APIClient) -> None:
    product = _make_published_product("SKU-PX-1")

    response = api_client.get(f"/api/v1/storefront/catalog/products/{product.id}")

    price = response.json()["data"]["price"]
    assert price == {"amount": 250_000, "currency": "VND", "is_stale": False}


@pytest.mark.django_db
def test_same_product_in_two_currencies_returns_two_converted_amounts(
    api_client: APIClient,
) -> None:
    sync_exchange_rates()
    product = _make_published_product("SKU-PX-2")

    vnd_response = api_client.get(
        f"/api/v1/storefront/catalog/products/{product.id}", {"currency": "VND"}
    )
    usd_response = api_client.get(
        f"/api/v1/storefront/catalog/products/{product.id}", {"currency": "USD"}
    )

    vnd_price = vnd_response.json()["data"]["price"]
    usd_price = usd_response.json()["data"]["price"]
    assert vnd_price["amount"] == 250_000
    assert usd_price["currency"] == "USD"
    assert usd_price["amount"] is not None
    assert usd_price["amount"] != vnd_price["amount"]


@pytest.mark.django_db
def test_missing_rate_flags_price_as_stale(api_client: APIClient) -> None:
    product = _make_published_product("SKU-PX-3")

    response = api_client.get(
        f"/api/v1/storefront/catalog/products/{product.id}", {"currency": "USD"}
    )

    price = response.json()["data"]["price"]
    assert price["amount"] is None
    assert price["is_stale"] is True
    assert response.status_code == status.HTTP_200_OK  # non-blocking, per Issue #8
