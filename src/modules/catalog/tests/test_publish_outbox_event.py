"""Outbox event on publish — Issue #7 commit 14's verify criterion: the
outbox row is committed atomically with the Product change."""

from unittest.mock import patch

import pytest

from common.db.models import OutboxEvent
from modules.catalog.models.product import ProductStatus
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import PRODUCT_PUBLISHED_EVENT, publish_product
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.translation.services.set_translation import set_translation


def _make_publishable_product(sku: str):
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku=sku, base_price_vnd=1000, weight_grams=1)
    ready_upload = MediaUpload.objects.create(
        storage_key=f"quarantine/{sku}",
        declared_content_type="image/png",
        declared_size_bytes=10,
        status=MediaUploadStatus.READY,
    )
    attach_media_to_product(media_upload=ready_upload, product=product)
    return product


@pytest.mark.django_db
def test_publish_emits_product_published_event() -> None:
    product = _make_publishable_product("SKU-OB-1")

    publish_product(product=product)

    event = OutboxEvent.objects.get(event_type=PRODUCT_PUBLISHED_EVENT)
    assert event.payload["product_id"] == str(product.id)


@pytest.mark.django_db
def test_outbox_row_and_product_status_commit_together() -> None:
    """If emitting the event fails, the Product status change must roll
    back with it — same transaction, or not at all."""
    product = _make_publishable_product("SKU-OB-2")

    with patch(
        "modules.catalog.services.publish_product.emit_event", side_effect=RuntimeError("boom")
    ):
        with pytest.raises(RuntimeError):
            publish_product(product=product)

    product.refresh_from_db()
    assert product.status == ProductStatus.DRAFT
    assert not OutboxEvent.objects.filter(event_type=PRODUCT_PUBLISHED_EVENT).exists()
