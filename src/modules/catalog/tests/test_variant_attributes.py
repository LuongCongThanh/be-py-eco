import pytest

from modules.catalog.errors import DuplicateAttributeCombinationError, DuplicateAttributeError
from modules.catalog.models import Attribute, AttributeValue
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.set_variant_attributes import set_variant_attributes


def _make_product():
    category = create_category()
    return create_product(primary_category=category)


def _make_variant(product, sku):
    return create_variant(product=product, sku=sku, base_price_vnd=100_000, weight_grams=100)


@pytest.mark.django_db
def test_two_variants_of_one_product_with_different_combinations() -> None:
    product = _make_product()
    color = Attribute.objects.create(code="color")
    red = AttributeValue.objects.create(attribute=color, code="red")
    blue = AttributeValue.objects.create(attribute=color, code="blue")
    variant_a = _make_variant(product, "SKU-A")
    variant_b = _make_variant(product, "SKU-B")

    set_variant_attributes(variant=variant_a, attribute_values=[red])
    set_variant_attributes(variant=variant_b, attribute_values=[blue])

    variant_a.refresh_from_db()
    variant_b.refresh_from_db()
    assert variant_a.attribute_combination_key != variant_b.attribute_combination_key


@pytest.mark.django_db
def test_third_variant_with_duplicate_combination_is_rejected() -> None:
    product = _make_product()
    color = Attribute.objects.create(code="color")
    red = AttributeValue.objects.create(attribute=color, code="red")
    variant_a = _make_variant(product, "SKU-A")
    variant_b = _make_variant(product, "SKU-B")
    set_variant_attributes(variant=variant_a, attribute_values=[red])

    with pytest.raises(DuplicateAttributeCombinationError):
        set_variant_attributes(variant=variant_b, attribute_values=[red])


@pytest.mark.django_db
def test_same_combination_allowed_across_different_products() -> None:
    product_a = _make_product()
    product_b = _make_product()
    color = Attribute.objects.create(code="color")
    red = AttributeValue.objects.create(attribute=color, code="red")
    variant_a = _make_variant(product_a, "SKU-C")
    variant_b = _make_variant(product_b, "SKU-D")

    set_variant_attributes(variant=variant_a, attribute_values=[red])
    set_variant_attributes(variant=variant_b, attribute_values=[red])

    variant_a.refresh_from_db()
    variant_b.refresh_from_db()
    assert variant_a.attribute_combination_key == variant_b.attribute_combination_key


@pytest.mark.django_db
def test_two_values_of_the_same_attribute_are_rejected() -> None:
    product = _make_product()
    color = Attribute.objects.create(code="color")
    red = AttributeValue.objects.create(attribute=color, code="red")
    blue = AttributeValue.objects.create(attribute=color, code="blue")
    variant = _make_variant(product, "SKU-E")

    with pytest.raises(DuplicateAttributeError):
        set_variant_attributes(variant=variant, attribute_values=[red, blue])
