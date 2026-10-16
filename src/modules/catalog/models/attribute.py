"""Attribute / Attribute Value — guild.md §15 Slice 2, commit 3. Flexible,
translatable Variant differentiators (e.g. color, size) so Variant
differentiation isn't hard-coded per Product type. `code` is the stable,
non-translatable identifier used for lookups and constraints; the
human-facing label lives in the `translation` module.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel


class Attribute(BaseModel):
    code = models.SlugField(max_length=50, unique=True)

    class Meta:
        db_table = "catalog_attribute"

    def __str__(self) -> str:
        return self.code


class AttributeValue(BaseModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT, related_name="values")
    code = models.SlugField(max_length=50)

    class Meta:
        db_table = "catalog_attribute_value"
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "code"],
                name="unique_attribute_value_code_per_attribute",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.attribute.code}:{self.code}"
