"""Idempotently create a locale's OpenSearch index — guild.md §15 Slice 3,
commit 1. Safe to call from both `index_product` (lazily, before the
first write) and `reindex_search` (explicitly, after a delete).
"""

from __future__ import annotations

from integrations.opensearch.client import get_opensearch_client
from modules.search.mapping import build_index_mapping, build_index_settings, index_name


def ensure_index(locale: str) -> str:
    client = get_opensearch_client()
    name = index_name(locale)
    if not client.indices.exists(index=name):
        client.indices.create(
            index=name,
            body={"settings": build_index_settings(), "mappings": build_index_mapping()},
        )
    return name
