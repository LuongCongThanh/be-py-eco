"""Integration test: `manage.py reindex_search` against a real OpenSearch
cluster — guild.md §15 Slice 3, commit 6's verify criterion (delete the
index, run the command, confirm all published Products are searchable
again). Fails here for the same connection-refused reason
tests/test_opensearch.py already does — no live infra in this
environment, not a regression.
"""

import pytest
from django.core.management import call_command

from integrations.opensearch.client import get_opensearch_client
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.search.mapping import index_name
from modules.translation.services.set_translation import set_translation


@pytest.mark.django_db
def test_reindex_rebuilds_index_after_deletion() -> None:
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku="SKU-CMD-1", base_price_vnd=100_000, weight_grams=100)
    ready_upload = MediaUpload.objects.create(
        storage_key="quarantine/SKU-CMD-1",
        declared_content_type="image/png",
        declared_size_bytes=10,
        status=MediaUploadStatus.READY,
    )
    attach_media_to_product(media_upload=ready_upload, product=product)
    publish_product(product=product)

    client = get_opensearch_client()
    client.indices.delete(index=index_name("vi"), ignore=[404])

    call_command("reindex_search")

    document = client.get(index=index_name("vi"), id=str(product.id))
    assert document["_source"]["name"] == "Áo thun"
