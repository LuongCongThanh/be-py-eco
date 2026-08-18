"""Product/Variant can never be hard-deleted — Issue #7 commit 6's verify
criterion: a hard-delete attempt raises a domain error, not a database
DELETE."""

import pytest

from modules.catalog.errors import HardDeleteNotAllowedError
from modules.catalog.models import Product, Variant
from modules.catalog.services.archive import archive_product, archive_variant
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant


@pytest.mark.django_db
def test_product_instance_delete_is_blocked() -> None:
    product = create_product(primary_category=create_category())

    with pytest.raises(HardDeleteNotAllowedError):
        product.delete()

    assert Product.objects.filter(pk=product.pk).exists()


@pytest.mark.django_db
def test_product_queryset_bulk_delete_is_blocked() -> None:
    create_product(primary_category=create_category())

    with pytest.raises(HardDeleteNotAllowedError):
        Product.objects.all().delete()

    assert Product.objects.exists()


@pytest.mark.django_db
def test_variant_instance_delete_is_blocked() -> None:
    product = create_product(primary_category=create_category())
    variant = create_variant(product=product, sku="SKU-NHD-1", base_price_vnd=1000, weight_grams=1)

    with pytest.raises(HardDeleteNotAllowedError):
        variant.delete()

    assert Variant.objects.filter(pk=variant.pk).exists()


@pytest.mark.django_db
def test_variant_queryset_bulk_delete_is_blocked() -> None:
    product = create_product(primary_category=create_category())
    create_variant(product=product, sku="SKU-NHD-2", base_price_vnd=1000, weight_grams=1)

    with pytest.raises(HardDeleteNotAllowedError):
        Variant.objects.all().delete()

    assert Variant.objects.exists()


@pytest.mark.django_db
def test_archive_product_sets_status_instead_of_deleting() -> None:
    product = create_product(primary_category=create_category())

    archived = archive_product(product)

    assert archived.status == "archived"
    assert Product.objects.filter(pk=product.pk).exists()


@pytest.mark.django_db
def test_archive_variant_sets_flag_instead_of_deleting() -> None:
    product = create_product(primary_category=create_category())
    variant = create_variant(product=product, sku="SKU-NHD-3", base_price_vnd=1000, weight_grams=1)

    archived = archive_variant(variant)

    assert archived.is_archived is True
    assert Variant.objects.filter(pk=variant.pk).exists()
