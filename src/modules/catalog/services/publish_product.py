"""Publish a Product — guild.md §15 Slice 2, commit 7. A dedicated action
(not a generic `PATCH status`) so publication can enforce its own
preconditions: complete default-locale content, ≥1 sellable (non-archived)
Variant, and ≥1 `ready` media asset.

The media-readiness check is a stub (`_STUB_HAS_READY_MEDIA` — always
`False`) until the `media` module lands in commit 8+; commit 12 replaces
the default with a real check against `MediaUpload`. `has_ready_media` is
an injectable seam so this commit's precondition contract — and its
tests — are locked in before the dependency it checks even exists (Issue
#7's Decision Document).
"""

from __future__ import annotations

from collections.abc import Callable

from modules.catalog.constants import DEFAULT_LOCALE, REQUIRED_TRANSLATION_FIELDS
from modules.catalog.errors import (
    IncompleteDefaultLocaleContentError,
    NoReadyMediaError,
    NoSellableVariantError,
)
from modules.catalog.models.product import Product, ProductStatus
from modules.translation.selectors.entries_for_entity import entries_for_entity

HasReadyMedia = Callable[[Product], bool]


def _stub_has_ready_media(product: Product) -> bool:
    return False


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
    has_ready_media: HasReadyMedia = _stub_has_ready_media,
) -> Product:
    if not _has_complete_default_locale_content(product):
        raise IncompleteDefaultLocaleContentError()
    if not _has_sellable_variant(product):
        raise NoSellableVariantError()
    if not has_ready_media(product):
        raise NoReadyMediaError()

    product.status = ProductStatus.ACTIVE
    product.save(update_fields=["status", "updated_at"])
    return product
