"""build_product_document — guild.md §15 Slice 3, commit 2's pure half.
No live OpenSearch cluster needed; `test_indexing.py` covers the actual
cluster round trip."""

import pytest

from modules.catalog.models import Attribute, AttributeValue
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.set_variant_attributes import set_variant_attributes
from modules.search.documents import build_product_document
from modules.translation.services.set_translation import set_translation


@pytest.mark.django_db
def test_document_includes_localized_name_and_sku() -> None:
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="en", field="name", value="T-shirt")
    create_variant(product=product, sku="SKU-DOC-1", base_price_vnd=100_000, weight_grams=100)

    document = build_product_document(product, "en")

    assert document["name"] == "T-shirt"
    assert document["sku"] == ["SKU-DOC-1"]
    assert document["is_available"] is True


@pytest.mark.django_db
def test_document_uses_cheapest_variant_price() -> None:
    product = create_product(primary_category=create_category())
    create_variant(product=product, sku="SKU-DOC-2", base_price_vnd=200_000, weight_grams=100)
    create_variant(product=product, sku="SKU-DOC-3", base_price_vnd=100_000, weight_grams=100)

    document = build_product_document(product, "vi")

    assert document["base_price_vnd"] == 100_000


@pytest.mark.django_db
def test_document_excludes_archived_variants() -> None:
    product = create_product(primary_category=create_category())
    variant = create_variant(
        product=product, sku="SKU-DOC-4", base_price_vnd=100_000, weight_grams=100
    )
    variant.is_archived = True
    variant.save(update_fields=["is_archived"])

    document = build_product_document(product, "vi")

    assert document["sku"] == []
    assert document["is_available"] is False
    assert document["base_price_vnd"] is None


@pytest.mark.django_db
def test_document_includes_category_and_attribute_ids() -> None:
    category = create_category()
    product = create_product(primary_category=category)
    color = Attribute.objects.create(code="color")
    red = AttributeValue.objects.create(attribute=color, code="red")
    variant = create_variant(
        product=product, sku="SKU-DOC-5", base_price_vnd=100_000, weight_grams=100
    )
    set_variant_attributes(variant=variant, attribute_values=[red])

    document = build_product_document(product, "vi")

    assert document["category_ids"] == [str(category.id)]
    assert document["attribute_value_ids"] == [str(red.id)]
