"""Variant — guild.md §15 Slice 2 / CONTEXT.md "Variant". SKU, optional
barcode, VND Base Price and weight live here (Product stays presentational).
`attribute_combination_key` is a deterministic, sorted digest of a
Variant's `VariantAttributeValue` set, kept in sync by
`services/set_variant_attributes.py`; it backs the database-level
uniqueness constraint that rejects two Variants of the same Product
sharing an Attribute combination. `is_archived` backs the no-hard-delete
guard added in commit 6 — Product/Variant referenced by an Order must
never be deleted, only archived.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel
from modules.catalog.models.attribute import AttributeValue
from modules.catalog.models.no_hard_delete import NoHardDeleteModel
from modules.catalog.models.product import Product


class Variant(NoHardDeleteModel, BaseModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    barcode = models.CharField(max_length=64, unique=True, null=True, blank=True)
    base_price_vnd = models.PositiveIntegerField()
    weight_grams = models.PositiveIntegerField()
    is_archived = models.BooleanField(default=False)
    attribute_combination_key = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "catalog_variant"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "attribute_combination_key"],
                condition=~models.Q(attribute_combination_key=""),
                name="unique_attribute_combination_per_product",
            ),
        ]

    def __str__(self) -> str:
        return self.sku


class VariantAttributeValue(BaseModel):
    """One (Attribute, AttributeValue) pair attached to a Variant. The
    denormalized `attribute` FK (rather than reaching through
    `attribute_value.attribute`) is what makes "one value per Attribute per
    Variant" a database-level constraint instead of an application check.
    """

    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey("catalog.Attribute", on_delete=models.PROTECT)
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.PROTECT)

    class Meta:
        db_table = "catalog_variant_attribute_value"
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "attribute"],
                name="unique_attribute_per_variant",
            ),
        ]
