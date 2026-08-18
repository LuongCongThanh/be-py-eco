"""Build an OpenSearch query body from Storefront search parameters —
guild.md §15 Slice 3, commits 3-5: full-text + typo tolerance (query-time
`fuzziness`), synonyms (the `search_analyzer` configured in
`mapping.py`), facets (Category/price/Attribute/availability/Brand), sort
options, and an exact SKU/barcode match ranked above fuzzy text scoring.

Pure over its arguments — no OpenSearch client involved — so it's fully
unit-testable without a live cluster; `api/storefront/views.py` is the
only caller that actually executes the query.
"""

from __future__ import annotations

from typing import Any

SORT_CLAUSES: dict[str, list[dict[str, Any]] | None] = {
    "relevance": None,  # OpenSearch's default _score sort
    "popularity": [{"popularity": "desc"}],
    "rating": [{"rating": "desc"}],
    "recency": [{"published_at": "desc"}],
}

# An exact SKU/barcode match should outrank any fuzzy text score — commit
# 5. A large boost on its `should` clause means it ranks first among
# results that already match (exact or fuzzy) via minimum_should_match: 1
# below, without needing a separate query path.
_EXACT_MATCH_BOOST = 1000


def build_search_query(
    *,
    text: str | None = None,
    category_id: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    attribute_value_ids: list[str] | None = None,
    brand_id: str | None = None,
    available_only: bool = False,
    sort: str = "relevance",
) -> dict[str, Any]:
    should: list[dict[str, Any]] = []
    filters: list[dict[str, Any]] = []

    if text:
        # All three clauses live in `should` with minimum_should_match: 1
        # (at least one must match) rather than putting the fuzzy
        # multi_match in `must` — a `must` clause would silently exclude
        # a document whose SKU matches exactly but whose name doesn't
        # fuzzy-match the query text, defeating the exact-match boost
        # instead of just outranking with it.
        should.append({"term": {"sku": {"value": text, "boost": _EXACT_MATCH_BOOST}}})
        should.append({"term": {"barcode": {"value": text, "boost": _EXACT_MATCH_BOOST}}})
        should.append(
            {
                "multi_match": {
                    "query": text,
                    "fields": ["name"],
                    "fuzziness": "AUTO",  # typo tolerance — commit 3
                }
            }
        )

    if category_id:
        filters.append({"term": {"category_ids": category_id}})
    if brand_id:
        filters.append({"term": {"brand_id": brand_id}})
    for value_id in attribute_value_ids or []:
        filters.append({"term": {"attribute_value_ids": value_id}})
    if price_min is not None or price_max is not None:
        price_range: dict[str, int] = {}
        if price_min is not None:
            price_range["gte"] = price_min
        if price_max is not None:
            price_range["lte"] = price_max
        filters.append({"range": {"base_price_vnd": price_range}})
    if available_only:
        filters.append({"term": {"is_available": True}})

    bool_query: dict[str, Any] = {}
    if should:
        bool_query["should"] = should
        bool_query["minimum_should_match"] = 1
    if filters:
        bool_query["filter"] = filters

    query: dict[str, Any] = {"bool": bool_query} if bool_query else {"match_all": {}}

    body: dict[str, Any] = {"query": query}
    sort_clause = SORT_CLAUSES.get(sort)
    if sort_clause:
        body["sort"] = sort_clause
    return body


def build_autocomplete_query(prefix: str) -> dict[str, Any]:
    """Prefix match against the edge_ngram-indexed `name` field, bypassing
    the synonym `search_analyzer` at query time (an unfinished prefix
    shouldn't be synonym-expanded) — commit 3's autocomplete."""
    return {
        "query": {
            "match": {
                "name": {"query": prefix, "analyzer": "standard"},
            }
        }
    }
