"""Cursor pagination on the Storefront Product listing — guild.md §5.6.

The invariant that matters is the walk: page through the whole catalog and
end up with exactly the set that was published, no repeats and no gaps. A
wrong comparison operator or a missing tiebreaker shows up there and
almost nowhere else, which is why checking only the first page would prove
very little.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from common.api.pagination import DEFAULT_PAGE_SIZE
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.translation.services.set_translation import set_translation

URL = "/api/v1/storefront/catalog/products"


@pytest.fixture(autouse=True)
def _storefront_country(supported_country):
    """Every test here is a Storefront read, which resolves locale and
    Transaction Currency against the active Supported Country."""


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _publish_products(count: int) -> set[str]:
    category = create_category()
    published = set()
    for index in range(count):
        product = create_product(primary_category=category)
        set_translation(entity=product, locale="vi", field="name", value=f"Áo thun {index}")
        create_variant(
            product=product, sku=f"SKU-PG-{index}", base_price_vnd=250_000, weight_grams=100
        )
        upload = MediaUpload.objects.create(
            storage_key=f"quarantine/pg-{index}",
            declared_content_type="image/png",
            declared_size_bytes=10,
            status=MediaUploadStatus.READY,
        )
        attach_media_to_product(media_upload=upload, product=product)
        published.add(str(publish_product(product=product).id))
    return published


def _walk_every_page(api_client: APIClient, **params: str | int) -> tuple[list[str], int]:
    """Follow next_cursor to exhaustion, returning every id seen in order."""
    seen: list[str] = []
    cursor = None
    requests = 0
    while True:
        query: dict[str, str | int] = dict(params)
        if cursor:
            query["cursor"] = cursor
        response = api_client.get(URL, query)
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        seen.extend(item["id"] for item in body["data"])
        requests += 1
        pagination = body["meta"]["pagination"]
        if not pagination["has_more"]:
            assert pagination["next_cursor"] is None
            return seen, requests
        cursor = pagination["next_cursor"]
        assert requests < 50, "pagination is not terminating"


@pytest.mark.django_db
def test_walking_every_page_sees_each_product_exactly_once(api_client: APIClient) -> None:
    published = _publish_products(25)

    seen, requests = _walk_every_page(api_client, page_size=10)

    assert len(seen) == len(set(seen)) == 25  # no repeats, no gaps
    assert set(seen) == published
    assert requests == 3


@pytest.mark.django_db
def test_pages_are_stable_across_the_boundary(api_client: APIClient) -> None:
    """The keyset is on a UUIDv7 primary key, so the order is total even for
    Products created in the same millisecond -- as these are."""
    _publish_products(6)

    first = api_client.get(URL, {"page_size": 3}).json()
    cursor = first["meta"]["pagination"]["next_cursor"]
    second = api_client.get(URL, {"page_size": 3, "cursor": cursor}).json()

    first_ids = [item["id"] for item in first["data"]]
    second_ids = [item["id"] for item in second["data"]]
    assert set(first_ids).isdisjoint(second_ids)
    assert first_ids == sorted(first_ids)
    assert max(first_ids) < min(second_ids)


@pytest.mark.django_db
def test_the_last_page_reports_no_further_cursor(api_client: APIClient) -> None:
    _publish_products(3)

    body = api_client.get(URL, {"page_size": 10}).json()

    assert body["meta"]["pagination"] == {
        "next_cursor": None,
        "has_more": False,
        "page_size": 10,
    }


@pytest.mark.django_db
def test_an_empty_catalog_paginates_without_incident(api_client: APIClient) -> None:
    body = api_client.get(URL).json()

    assert body["data"] == []
    assert body["meta"]["pagination"]["has_more"] is False


@pytest.mark.django_db
def test_page_size_defaults_to_the_documented_value(api_client: APIClient) -> None:
    _publish_products(DEFAULT_PAGE_SIZE + 5)

    body = api_client.get(URL).json()

    assert len(body["data"]) == DEFAULT_PAGE_SIZE
    assert body["meta"]["pagination"]["page_size"] == DEFAULT_PAGE_SIZE


@pytest.mark.django_db
@pytest.mark.parametrize("page_size", [0, 101, -1])
def test_page_size_outside_the_documented_bounds_is_refused(
    api_client: APIClient, page_size: int
) -> None:
    response = api_client.get(URL, {"page_size": page_size})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_a_malformed_cursor_is_a_400_not_a_500(api_client: APIClient) -> None:
    response = api_client.get(URL, {"cursor": "obviously-not-a-cursor"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "api.invalid_cursor"


@pytest.mark.django_db
def test_the_rate_is_still_read_once_across_a_paginated_page(api_client: APIClient) -> None:
    """The guard from the price-converter work must survive pagination."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from modules.pricing.services.sync_exchange_rates import sync_exchange_rates

    sync_exchange_rates()
    _publish_products(20)

    with CaptureQueriesContext(connection) as captured:
        api_client.get(URL, {"currency": "USD", "page_size": "20"})

    rate_queries = [q for q in captured.captured_queries if "pricing_exchange_rate" in q["sql"]]
    assert len(rate_queries) == 1
