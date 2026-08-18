"""The one seam through which the Storefront API touches OpenSearch for
querying — guild.md §7.6's adapter convention applied to search: views
build a query body (`selectors/search_query.py`) and call `execute_search`
rather than reaching for `get_opensearch_client()` themselves, and a
cluster failure becomes a Problem Details response instead of a raw 500.
"""

from __future__ import annotations

from typing import Any

from opensearchpy.exceptions import OpenSearchException

from integrations.opensearch.client import get_opensearch_client
from modules.search.errors import SearchUnavailableError
from modules.search.mapping import index_name


def execute_search(*, locale: str, body: dict[str, Any]) -> list[dict[str, Any]]:
    client = get_opensearch_client()
    try:
        result = client.search(index=index_name(locale), body=body)
    except OpenSearchException as exc:
        raise SearchUnavailableError() from exc
    return [hit["_source"] for hit in result["hits"]["hits"]]
