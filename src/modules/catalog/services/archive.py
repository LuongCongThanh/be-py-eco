"""Archive a Product/Variant — guild.md §15 Slice 2, commit 6. The only
sanctioned way to retire a record once hard-delete is blocked
(`models/no_hard_delete.py`); history stays resolvable for Orders that
will reference these once Slice 5 lands.
"""

from __future__ import annotations

from modules.catalog.models.product import Product, ProductStatus
from modules.catalog.models.variant import Variant


def archive_product(product: Product) -> Product:
    product.status = ProductStatus.ARCHIVED
    product.save(update_fields=["status", "updated_at"])
    return product


def archive_variant(variant: Variant) -> Variant:
    variant.is_archived = True
    variant.save(update_fields=["is_archived", "updated_at"])
    return variant
