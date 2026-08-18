"""Full rebuild of the OpenSearch projection from PostgreSQL — guild.md
§15 Slice 3, commit 6. Wiping and rebuilding straight from the source of
truth is what makes OpenSearch disposable by construction (ADR-0001),
not just assumed-rebuildable and never actually exercised.
"""

from __future__ import annotations

from integrations.opensearch.client import get_opensearch_client
from modules.catalog.models.product import Product, ProductStatus
from modules.search.documents import build_product_document
from modules.search.mapping import index_name
from modules.search.services.ensure_index import ensure_index
from modules.search.tasks import SUPPORTED_LOCALES


def reindex_all() -> int:
    """Delete and recreate every locale's index, then index every
    published Product into all of them. Returns the number of Products
    reindexed."""
    client = get_opensearch_client()
    for locale in SUPPORTED_LOCALES:
        client.indices.delete(index=index_name(locale), ignore=[404])
        ensure_index(locale)

    count = 0
    for product in Product.objects.filter(status=ProductStatus.ACTIVE).iterator():
        for locale in SUPPORTED_LOCALES:
            document = build_product_document(product, locale)
            client.index(index=index_name(locale), id=str(product.id), body=document)
        count += 1
    return count
