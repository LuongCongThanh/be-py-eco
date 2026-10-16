import pytest
from django.db import IntegrityError, transaction

from modules.catalog.errors import PrimaryCategoryNotInCategoriesError
from modules.catalog.models import ProductStatus
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant


@pytest.mark.django_db
def test_create_product_defaults_to_draft_with_primary_category() -> None:
    category = create_category()

    product = create_product(primary_category=category)

    assert product.status == ProductStatus.DRAFT
    assert product.primary_category_id == category.id
    assert list(product.categories.all()) == [category]


@pytest.mark.django_db
def test_create_product_with_multiple_categories() -> None:
    primary = create_category()
    secondary = create_category()

    product = create_product(primary_category=primary, categories=[primary, secondary])

    assert set(product.categories.all()) == {primary, secondary}


@pytest.mark.django_db
def test_primary_category_must_be_in_categories() -> None:
    primary = create_category()
    other = create_category()

    with pytest.raises(PrimaryCategoryNotInCategoriesError):
        create_product(primary_category=primary, categories=[other])


@pytest.mark.django_db
def test_variant_sku_is_globally_unique() -> None:
    category = create_category()
    product = create_product(primary_category=category)
    create_variant(product=product, sku="SKU-1", base_price_vnd=100_000, weight_grams=500)

    other_product = create_product(primary_category=category)
    with pytest.raises(IntegrityError), transaction.atomic():
        create_variant(product=other_product, sku="SKU-1", base_price_vnd=200_000, weight_grams=200)


@pytest.mark.django_db
def test_variant_sku_cannot_be_reused_by_an_archived_variant() -> None:
    category = create_category()
    product = create_product(primary_category=category)
    variant = create_variant(product=product, sku="SKU-2", base_price_vnd=100_000, weight_grams=500)
    variant.is_archived = True
    variant.save(update_fields=["is_archived"])

    with pytest.raises(IntegrityError), transaction.atomic():
        create_variant(product=product, sku="SKU-2", base_price_vnd=150_000, weight_grams=400)
