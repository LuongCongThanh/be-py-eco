"""Build a per-locale search document from a catalog Product — guild.md
§15 Slice 3, commit 2. Pure over already-loaded model data so it's
unit-testable without a live OpenSearch cluster; `tasks.index_product` is
the only caller that actually writes it.
"""

from __future__ import annotations

from modules.catalog.constants import DEFAULT_LOCALE
from modules.catalog.models.product import Product
from modules.translation.selectors.get_localized_field import get_localized_field


def build_product_document(product: Product, locale: str) -> dict:
    name = get_localized_field(product, field="name", locale=locale, default_locale=DEFAULT_LOCALE)
    variants = list(product.variants.filter(is_archived=False))
    attribute_value_ids = {
        str(value_id)
        for variant in variants
        for value_id in variant.attribute_values.values_list("attribute_value_id", flat=True)
    }
    cheapest_price = min((v.base_price_vnd for v in variants), default=None)

    return {
        "product_id": str(product.id),
        "sku": [v.sku for v in variants],
        "barcode": [v.barcode for v in variants if v.barcode],
        "name": name.value or "",
        "category_ids": [str(cid) for cid in product.categories.values_list("id", flat=True)],
        "brand_id": str(product.brand_id) if product.brand_id else None,
        "attribute_value_ids": sorted(attribute_value_ids),
        "base_price_vnd": cheapest_price,
        "is_available": bool(variants),
        "popularity": 0,
        "rating": 0.0,
        "published_at": product.updated_at.isoformat(),
    }
