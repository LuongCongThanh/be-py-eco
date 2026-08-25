"""The one seam through which the Storefront API touches OpenSearch for
querying — guild.md §7.6's adapter convention applied to search: views
build a query body (`selectors/search_query.py`) and call `execute_search`
rather than reaching for `get_opensearch_client()` themselves, and a
cluster failure becomes a Problem Details response instead of a raw 500.

Returns each hit's sort values alongside its document. Cursor pagination
resumes with `search_after`, which needs exactly those values, and this is
the only layer that ever sees them — a caller cannot recover them from
`_source`. Per-hit rather than last-hit-only because a caller over-fetches
by one to detect `has_more`, and the cursor must point at the last hit it
actually kept, not at the extra one it discarded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from opensearchpy.exceptions import OpenSearchException

from integrations.opensearch.client import get_opensearch_client
from modules.search.errors import SearchUnavailableError
from modules.search.mapping import index_name


@dataclass(frozen=True)
class SearchHits:
    documents: list[dict[str, Any]]
    sorts: list[list[Any]]


def execute_search(*, locale: str, body: dict[str, Any]) -> SearchHits:
    client = get_opensearch_client()
    try:
        result = client.search(index=index_name(locale), body=body)
    except OpenSearchException as exc:
        raise SearchUnavailableError() from exc

    hits = result["hits"]["hits"]
    return SearchHits(
        documents=[hit["_source"] for hit in hits],
        sorts=[hit.get("sort", []) for hit in hits],
    )
