"""The Storefront read must not re-read the Exchange Rate per Product.

Scoped deliberately to queries against `pricing_exchange_rate`: two other
per-Product queries (the TranslationEntry lookup and the Variant lookup)
still remain in this loop and are tracked separately. Asserting a flat
total here would fail for reasons this change never claimed to fix.
"""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.pricing.services.sync_exchange_rates import sync_exchange_rates
from modules.translation.services.set_translation import set_translation

RATE_TABLE = "pricing_exchange_rate"


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


def _publish_products(count: int, *, start: int = 0) -> None:
    category = create_category()
    for index in range(start, start + count):
        product = create_product(primary_category=category)
        set_translation(entity=product, locale="vi", field="name", value=f"Áo thun {index}")
        create_variant(
            product=product, sku=f"SKU-QC-{index}", base_price_vnd=250_000, weight_grams=100
        )
        ready_upload = MediaUpload.objects.create(
            storage_key=f"quarantine/qc-{index}",
            declared_content_type="image/png",
            declared_size_bytes=10,
            status=MediaUploadStatus.READY,
        )
        attach_media_to_product(media_upload=ready_upload, product=product)
        publish_product(product=product)


def _rate_queries(captured: CaptureQueriesContext) -> list[str]:
    return [query["sql"] for query in captured.captured_queries if RATE_TABLE in query["sql"]]


@pytest.mark.django_db
def test_rate_is_read_once_regardless_of_product_count(api_client: APIClient) -> None:
    sync_exchange_rates()
    _publish_products(20)

    with CaptureQueriesContext(connection) as captured:
        response = api_client.get("/api/v1/storefront/catalog/products", {"currency": "USD"})

    assert len(response.json()["data"]) == 20
    assert len(_rate_queries(captured)) == 1


@pytest.mark.django_db
def test_rate_read_count_does_not_grow_with_the_catalog(api_client: APIClient) -> None:
    """The invariant is that the count is flat, not merely small — one
    Product and twenty Products must cost the same."""
    sync_exchange_rates()

    _publish_products(1)
    with CaptureQueriesContext(connection) as one_product:
        api_client.get("/api/v1/storefront/catalog/products", {"currency": "USD"})

    _publish_products(19, start=1)
    with CaptureQueriesContext(connection) as twenty_products:
        api_client.get("/api/v1/storefront/catalog/products", {"currency": "USD"})

    assert len(_rate_queries(one_product)) == len(_rate_queries(twenty_products)) == 1


@pytest.mark.django_db
def test_vnd_listing_reads_no_rate_at_all(api_client: APIClient) -> None:
    sync_exchange_rates()
    _publish_products(5)

    with CaptureQueriesContext(connection) as captured:
        api_client.get("/api/v1/storefront/catalog/products")

    assert _rate_queries(captured) == []


@pytest.mark.django_db
def test_unsupported_currency_is_a_400_not_a_null_price(api_client: APIClient) -> None:
    """Previously this returned 200 with `amount: null`, indistinguishable
    from a supported currency whose rate had not synced yet.

    The refusal now comes from `localization`, not `pricing`: the Supported
    Country does not allow EUR, which is a more specific truth than "EUR has
    no configured minor unit". `pricing`'s check survives as the guard for a
    currency a country allows but pricing cannot convert -- a misconfiguration
    rather than a client error."""
    _publish_products(1)

    response = api_client.get("/api/v1/storefront/catalog/products", {"currency": "EUR"})

    assert response.status_code == 400
    assert response.json()["code"] == "localization.unsupported_currency"
