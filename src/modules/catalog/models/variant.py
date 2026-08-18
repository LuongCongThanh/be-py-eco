"""Variant — guild.md §15 Slice 2 / CONTEXT.md "Variant". SKU, optional
barcode, VND Base Price and weight live here (Product stays presentational).
Attribute-combination uniqueness is added in commit 3 once Attribute/
AttributeValue exist. `is_archived` backs the no-hard-delete guard added in
commit 6 — Product/Variant referenced by an Order must never be deleted,
only archived.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel
from modules.catalog.models.product import Product


class Variant(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    barcode = models.CharField(max_length=64, unique=True, null=True, blank=True)
    base_price_vnd = models.PositiveIntegerField()
    weight_grams = models.PositiveIntegerField()
    is_archived = models.BooleanField(default=False)

    class Meta:
        db_table = "catalog_variant"

    def __str__(self) -> str:
        return self.sku
