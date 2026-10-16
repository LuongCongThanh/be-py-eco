"""Index a Product into every locale's OpenSearch projection — guild.md
§15 Slice 3, commit 2. Triggered asynchronously by the outbox dispatcher
(`common.db.outbox`) consuming catalog's `ProductPublished` event —
never called synchronously from the originating request.

Upserting by `product_id` (OpenSearch's document `id`) makes this
idempotent under at-least-once outbox delivery: re-indexing the same
Product just overwrites the same document.

`acks_late=True` + `autoretry_for`/`retry_backoff` close the gap the
outbox dispatcher explicitly doesn't cover (`common.db.outbox`'s
docstring): the outbox only guarantees this task gets *enqueued* at
least once, not that a worker crash mid-run doesn't lose it — Celery's
own late-ack plus retry-with-backoff is what makes the task itself
durable once queued.
"""

from __future__ import annotations

from celery import shared_task

from integrations.opensearch.client import get_opensearch_client
from modules.catalog.models.product import Product
from modules.search.documents import build_product_document
from modules.search.services.ensure_index import ensure_index

SUPPORTED_LOCALES = ("vi", "en")


@shared_task(
    name="search.index_product",
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def index_product(product_id: str) -> None:
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return  # deleted/never existed by the time this ran — nothing to index

    client = get_opensearch_client()
    for locale in SUPPORTED_LOCALES:
        index = ensure_index(locale)
        document = build_product_document(product, locale)
        client.index(index=index, id=str(product.id), body=document, refresh=True)
