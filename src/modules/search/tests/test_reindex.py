"""reindex_all — guild.md §15 Slice 3, commit 6. Exercised against a fake
OpenSearch client double (recording calls) rather than a live cluster,
so the delete-then-rebuild sequencing is unit-tested here; the real
end-to-end round trip against a live cluster is what
test_search_behavior.py's suite is for.
"""

from unittest.mock import patch

import pytest

from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.search.mapping import index_name
from modules.search.services.reindex import reindex_all
from modules.search.tasks import SUPPORTED_LOCALES
from modules.translation.services.set_translation import set_translation


def _make_published_product(sku: str):
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku=sku, base_price_vnd=100_000, weight_grams=100)
    ready_upload = MediaUpload.objects.create(
        storage_key=f"quarantine/{sku}",
        declared_content_type="image/png",
        declared_size_bytes=10,
        status=MediaUploadStatus.READY,
    )
    attach_media_to_product(media_upload=ready_upload, product=product)
    return publish_product(product=product)


class _FakeIndices:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.created: list[str] = []

    def delete(self, *, index: str, ignore=None) -> None:
        self.deleted.append(index)

    def exists(self, *, index: str) -> bool:
        return index in self.created

    def create(self, *, index: str, body: dict) -> None:
        self.created.append(index)


class _FakeClient:
    def __init__(self) -> None:
        self.indices = _FakeIndices()
        self.indexed: list[tuple[str, str]] = []

    def index(self, *, index: str, id: str, body: dict) -> None:
        self.indexed.append((index, id))


@pytest.fixture
def fake_client():
    client = _FakeClient()
    with (
        patch("modules.search.services.reindex.get_opensearch_client", return_value=client),
        patch("modules.search.services.ensure_index.get_opensearch_client", return_value=client),
    ):
        yield client


@pytest.mark.django_db
def test_reindex_deletes_and_recreates_every_locale_index(fake_client) -> None:
    reindex_all()

    for locale in SUPPORTED_LOCALES:
        assert index_name(locale) in fake_client.indices.deleted
        assert index_name(locale) in fake_client.indices.created


@pytest.mark.django_db
def test_reindex_indexes_every_published_product_in_every_locale(fake_client) -> None:
    product_a = _make_published_product("SKU-REIDX-1")
    product_b = _make_published_product("SKU-REIDX-2")

    count = reindex_all()

    assert count == 2
    indexed_ids = {doc_id for _, doc_id in fake_client.indexed}
    assert str(product_a.id) in indexed_ids
    assert str(product_b.id) in indexed_ids
    assert len(fake_client.indexed) == 2 * len(SUPPORTED_LOCALES)


@pytest.mark.django_db
def test_reindex_skips_unpublished_products(fake_client) -> None:
    draft = create_product(primary_category=create_category())

    reindex_all()

    indexed_ids = {doc_id for _, doc_id in fake_client.indexed}
    assert str(draft.id) not in indexed_ids
