"""Idempotently create a locale's OpenSearch index — guild.md §15 Slice 3,
commit 1. Safe to call from both `index_product` (lazily, before the
first write) and `reindex_search` (explicitly, after a delete).

Creating is not enough on its own: an index that already exists keeps
whatever mapping it was created with, however far the code has since
moved. So this also refuses to write into a stale one.

Note what that does and does not cover. Both callers are write paths, so a
deploy that changes the mapping and skips the reindex fails loudly at the
next index write and says how to fix it. Reads are not gated -- checking
the mapping on every search would add a round trip to the hot path -- so
until the reindex runs, filters on a newly mapped field return nothing.
The failing writes are the signal; they arrive with the next publish.
"""

from __future__ import annotations

from typing import Any

from integrations.opensearch.client import get_opensearch_client
from modules.search.errors import SearchIndexMappingDriftError
from modules.search.mapping import build_index_mapping, build_index_settings, index_name


def _assert_mapping_current(live: dict[str, Any], expected: dict[str, Any], index: str) -> None:
    live_fields = set(live.get("properties", {}))
    expected_fields = set(expected["properties"])
    if live_fields == expected_fields:
        return
    raise SearchIndexMappingDriftError(
        f"Index {index!r} was built with a different mapping "
        f"(missing {sorted(expected_fields - live_fields)}, "
        f"unexpected {sorted(live_fields - expected_fields)}). "
        f"Run `manage.py reindex_search` to rebuild it from PostgreSQL."
    )


def ensure_index(locale: str) -> str:
    client = get_opensearch_client()
    name = index_name(locale)
    expected = build_index_mapping()

    if not client.indices.exists(index=name):
        client.indices.create(
            index=name,
            body={"settings": build_index_settings(), "mappings": expected},
        )
        return name

    live = client.indices.get_mapping(index=name)[name]["mappings"]
    _assert_mapping_current(live, expected, name)
    return name
