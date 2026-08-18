"""Product — guild.md §15 Slice 2. Presentational/lifecycle only; SKU,
Base Price, weight and inventory reference live on Variant
(`modules.catalog.models.variant`). Translatable content (name,
description, SEO) lives in the `translation` module, not here.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel
from modules.catalog.models.brand import Brand
from modules.catalog.models.category import Category


class ProductStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Product(BaseModel):
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
    )
    brand = models.ForeignKey(
        Brand,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="products",
    )
    primary_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="primary_products",
    )
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        through="ProductCategory",
    )

    class Meta:
        db_table = "catalog_product"

    def __str__(self) -> str:
        return str(self.id)


class ProductCategory(BaseModel):
    """Through table for `Product.categories` — a plain M2M would work too,
    but an explicit through model gives every Product-Category association
    its own row/id for auditing and future per-association fields (e.g.
    display order) without a migration.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    class Meta:
        db_table = "catalog_product_category"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "category"],
                name="unique_product_category",
            ),
        ]
