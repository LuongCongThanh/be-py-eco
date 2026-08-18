"""Registers `index_product` against catalog's `ProductPublished` outbox
event — guild.md §15 Slice 3, commit 2. Imported once, from
`SearchConfig.ready()`, so registration happens exactly at app startup
regardless of import order elsewhere.
"""

from __future__ import annotations

from typing import Any

from common.db.outbox import register_handler
from modules.catalog.services.publish_product import PRODUCT_PUBLISHED_EVENT
from modules.search.tasks import index_product


def _handle_product_published(payload: dict[str, Any]) -> None:
    index_product.delay(payload["product_id"])


register_handler(PRODUCT_PUBLISHED_EVENT, _handle_product_published)
