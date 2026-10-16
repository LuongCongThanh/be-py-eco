"""Create a Product and its initial Variant — guild.md §15 Slice 2, commit 2.

Publication (status transition, precondition checks) is a separate action
added in commit 7 (`services/publish_product.py`); this service only
creates the Draft record.
"""

from __future__ import annotations

from modules.catalog.errors import PrimaryCategoryNotInCategoriesError
from modules.catalog.models.brand import Brand
from modules.catalog.models.category import Category
from modules.catalog.models.product import Product, ProductCategory
from modules.catalog.models.variant import Variant


def create_product(
    *,
    primary_category: Category,
    categories: list[Category] | None = None,
    brand: Brand | None = None,
) -> Product:
    categories = categories or [primary_category]
    if primary_category not in categories:
        raise PrimaryCategoryNotInCategoriesError()

    product = Product.objects.create(
        primary_category=primary_category,
        brand=brand,
    )
    ProductCategory.objects.bulk_create(
        [ProductCategory(product=product, category=category) for category in categories]
    )
    return product


def create_variant(
    *,
    product: Product,
    sku: str,
    base_price_vnd: int,
    weight_grams: int,
    barcode: str | None = None,
) -> Variant:
    return Variant.objects.create(
        product=product,
        sku=sku,
        barcode=barcode,
        base_price_vnd=base_price_vnd,
        weight_grams=weight_grams,
    )
