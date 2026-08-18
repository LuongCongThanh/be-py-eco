"""Registers `index_product` against catalog's outbox events — guild.md
§15 Slice 3, commit 2. Imported once, from `SearchConfig.ready()`, so
registration happens exactly at app startup regardless of import order
elsewhere.

`PRODUCT_UPDATED_EVENT` is registered now even though nothing emits it
yet: Slice 2 only wired an outbox event on `publish_product`, not on a
generic "update an already-published Product" action (no such action
exists yet). Registering the handler ahead of the emitter costs nothing
and means a future edit-and-republish action only has to call
`emit_event`, not touch this module.
"""

from __future__ import annotations

from typing import Any

from common.db.outbox import register_handler
from modules.catalog.services.publish_product import PRODUCT_PUBLISHED_EVENT
from modules.search.tasks import index_product

PRODUCT_UPDATED_EVENT = "catalog.ProductUpdated"


def _handle_product_published(payload: dict[str, Any]) -> None:
    index_product.delay(payload["product_id"])


register_handler(PRODUCT_PUBLISHED_EVENT, _handle_product_published)
register_handler(PRODUCT_UPDATED_EVENT, _handle_product_published)
