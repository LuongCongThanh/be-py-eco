"""Publish preconditions — Issue #7 commit 7's verify criterion: publish
fails with a specific error per missing precondition, succeeds once all
three are met."""

import pytest

from modules.catalog.errors import (
    IncompleteDefaultLocaleContentError,
    NoReadyMediaError,
    NoSellableVariantError,
)
from modules.catalog.models.product import ProductStatus
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.translation.services.set_translation import set_translation


def _make_product():
    return create_product(primary_category=create_category())


@pytest.mark.django_db
def test_publish_fails_without_default_locale_content() -> None:
    product = _make_product()
    create_variant(product=product, sku="SKU-PUB-1", base_price_vnd=1000, weight_grams=1)

    with pytest.raises(IncompleteDefaultLocaleContentError):
        publish_product(product=product, has_ready_media=lambda p: True)


@pytest.mark.django_db
def test_publish_fails_without_sellable_variant() -> None:
    product = _make_product()
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")

    with pytest.raises(NoSellableVariantError):
        publish_product(product=product, has_ready_media=lambda p: True)


@pytest.mark.django_db
def test_publish_fails_when_only_variant_is_archived() -> None:
    product = _make_product()
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    variant = create_variant(product=product, sku="SKU-PUB-2", base_price_vnd=1000, weight_grams=1)
    variant.is_archived = True
    variant.save(update_fields=["is_archived"])

    with pytest.raises(NoSellableVariantError):
        publish_product(product=product, has_ready_media=lambda p: True)


@pytest.mark.django_db
def test_publish_fails_without_ready_media_stub() -> None:
    product = _make_product()
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku="SKU-PUB-3", base_price_vnd=1000, weight_grams=1)

    with pytest.raises(NoReadyMediaError):
        publish_product(product=product)


@pytest.mark.django_db
def test_publish_fails_without_ready_media_when_injected_false() -> None:
    product = _make_product()
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku="SKU-PUB-4", base_price_vnd=1000, weight_grams=1)

    with pytest.raises(NoReadyMediaError):
        publish_product(product=product, has_ready_media=lambda p: False)


@pytest.mark.django_db
def test_publish_succeeds_once_all_three_preconditions_are_met() -> None:
    product = _make_product()
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku="SKU-PUB-5", base_price_vnd=1000, weight_grams=1)

    published = publish_product(product=product, has_ready_media=lambda p: True)

    assert published.status == ProductStatus.ACTIVE
