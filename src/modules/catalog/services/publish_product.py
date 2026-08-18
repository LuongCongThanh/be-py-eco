"""Publish a Product — guild.md §15 Slice 2, commit 7 (commit 12 wires in
the real media check). A dedicated action (not a generic `PATCH status`)
so publication can enforce its own preconditions: complete default-locale
content, ≥1 sellable (non-archived) Variant, and ≥1 `ready` media asset.

`_default_has_ready_media` reads `Product.media_uploads` — a reverse
accessor from `media.MediaUpload.product` — without this module importing
anything from `media`, keeping the dependency one-directional (media
depends on catalog, not vice versa). `has_ready_media` stays an
injectable seam (it was the only way to test this precondition in commit
7, before `media` existed) but now defaults to the real check instead of
commit 7's always-`False` stub.
"""

from __future__ import annotations

from collections.abc import Callable

from django.db import transaction

from common.db.outbox import emit_event
from modules.catalog.constants import DEFAULT_LOCALE, REQUIRED_TRANSLATION_FIELDS
from modules.catalog.errors import (
    IncompleteDefaultLocaleContentError,
    NoReadyMediaError,
    NoSellableVariantError,
)
from modules.catalog.models.product import Product, ProductStatus
from modules.translation.selectors.entries_for_entity import entries_for_entity

PRODUCT_PUBLISHED_EVENT = "catalog.ProductPublished"

HasReadyMedia = Callable[[Product], bool]

# Mirrors media.MediaUploadStatus.READY's value as a literal, rather than
# importing that enum, to keep this module's dependency on `media` limited
# to the reverse ORM accessor Django wires up from MediaUpload.product.
_READY_MEDIA_STATUS = "ready"


def _default_has_ready_media(product: Product) -> bool:
    # media_uploads is Django's reverse accessor for media.MediaUpload.product
    # (related_name="media_uploads"); mypy/django-stubs can't see it from
    # here without catalog importing media, which is exactly the coupling
    # this accessor is meant to avoid.
    media_uploads = product.media_uploads  # type: ignore[attr-defined]
    return media_uploads.filter(status=_READY_MEDIA_STATUS).exists()


def _has_complete_default_locale_content(product: Product) -> bool:
    approved_fields = set(
        entries_for_entity(product)
        .filter(locale=DEFAULT_LOCALE, is_approved=True)
        .values_list("field", flat=True)
    )
    return set(REQUIRED_TRANSLATION_FIELDS).issubset(approved_fields)


def _has_sellable_variant(product: Product) -> bool:
    return product.variants.filter(is_archived=False).exists()


def publish_product(
    *,
    product: Product,
    has_ready_media: HasReadyMedia = _default_has_ready_media,
) -> Product:
    if not _has_complete_default_locale_content(product):
        raise IncompleteDefaultLocaleContentError()
    if not _has_sellable_variant(product):
        raise NoSellableVariantError()
    if not has_ready_media(product):
        raise NoReadyMediaError()

    with transaction.atomic():
        product.status = ProductStatus.ACTIVE
        product.save(update_fields=["status", "updated_at"])
        # guild.md §15 Slice 2, commit 14 — no consumer exists until
        # Slice 3's search sync; this only proves the producer side
        # commits atomically with the Product change.
        emit_event(
            event_type=PRODUCT_PUBLISHED_EVENT,
            payload={"product_id": str(product.id)},
        )
    return product
