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


@pytest.fixture(autouse=True)
def _storefront_country(supported_country):
    """Every test in this module is a Storefront read, and a Storefront read
    resolves locale and Transaction Currency against the active Supported
    Country. Declared once here rather than on each signature, but still
    explicit: this module states the dependency, it is not granted globally.
    """


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


# --- locale and Transaction Currency resolution ------------------------
# The precedence rule itself is table-tested in
# localization/tests/test_resolve_storefront_context.py; these prove the
# Storefront endpoints actually go through it.


def _as_customer(client: APIClient, customer) -> APIClient:
    from modules.accounts.services.sessions import issue_session

    access, _ = issue_session(customer)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


@pytest.mark.django_db
def test_signed_in_customers_stored_currency_is_finally_used(api_client: APIClient) -> None:
    """Accounts has recorded `preferred_currency` since Slice 1 and no
    Storefront read consulted it until now."""
    from modules.accounts.tests.factories import CustomerFactory
    from modules.pricing.services.sync_exchange_rates import sync_exchange_rates

    sync_exchange_rates()
    customer = CustomerFactory(preferred_currency="USD")
    _make_published_product("SKU-CTX-1")

    response = _as_customer(api_client, customer).get("/api/v1/storefront/catalog/products")

    assert response.json()["data"][0]["price"]["currency"] == "USD"


@pytest.mark.django_db
def test_an_explicit_currency_param_beats_the_stored_preference(api_client: APIClient) -> None:
    from modules.accounts.tests.factories import CustomerFactory

    customer = CustomerFactory(preferred_currency="USD")
    _make_published_product("SKU-CTX-2")

    response = _as_customer(api_client, customer).get(
        "/api/v1/storefront/catalog/products", {"currency": "VND"}
    )

    assert response.json()["data"][0]["price"]["currency"] == "VND"


@pytest.mark.django_db
def test_list_content_language_reports_the_requested_locale(api_client: APIClient) -> None:
    """A list can mix locales, so no per-Product answer is right. This used
    to report whichever Product happened to be serialized last."""
    _make_published_product("SKU-CTX-3")
    _make_published_product("SKU-CTX-4")

    response = api_client.get(
        "/api/v1/storefront/catalog/products", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9"
    )

    assert response["Content-Language"] == "en"
