"""Publish with the real (commit 12) media check, wired through
media.attach_media_to_product — Issue #7 commit 12's verify criterion."""

import pytest

from modules.catalog.errors import NoReadyMediaError
from modules.catalog.models.product import ProductStatus
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.media.errors import MediaUploadNotReadyError
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.translation.services.set_translation import set_translation


def _make_publishable_product(sku: str):
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku=sku, base_price_vnd=1000, weight_grams=1)
    return product


@pytest.mark.django_db
def test_pending_media_cannot_be_attached() -> None:
    product = _make_publishable_product("SKU-RM-1")
    pending_upload = MediaUpload.objects.create(
        storage_key="quarantine/abc",
        declared_content_type="image/png",
        declared_size_bytes=10,
    )

    with pytest.raises(MediaUploadNotReadyError):
        attach_media_to_product(media_upload=pending_upload, product=product)


@pytest.mark.django_db
def test_rejected_media_cannot_be_attached() -> None:
    product = _make_publishable_product("SKU-RM-2")
    rejected_upload = MediaUpload.objects.create(
        storage_key="quarantine/def",
        declared_content_type="image/png",
        declared_size_bytes=10,
        status=MediaUploadStatus.REJECTED,
    )

    with pytest.raises(MediaUploadNotReadyError):
        attach_media_to_product(media_upload=rejected_upload, product=product)


@pytest.mark.django_db
def test_publish_fails_when_only_pending_media_exists() -> None:
    product = _make_publishable_product("SKU-RM-3")
    MediaUpload.objects.create(
        storage_key="quarantine/ghi",
        declared_content_type="image/png",
        declared_size_bytes=10,
        product=product,
    )

    with pytest.raises(NoReadyMediaError):
        publish_product(product=product)


@pytest.mark.django_db
def test_publish_succeeds_once_a_ready_media_is_attached() -> None:
    product = _make_publishable_product("SKU-RM-4")
    ready_upload = MediaUpload.objects.create(
        storage_key="quarantine/jkl",
        declared_content_type="image/png",
        declared_size_bytes=10,
        status=MediaUploadStatus.READY,
    )
    attach_media_to_product(media_upload=ready_upload, product=product)

    published = publish_product(product=product)

    assert published.status == ProductStatus.ACTIVE
