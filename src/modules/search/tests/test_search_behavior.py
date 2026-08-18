"""Integration tests against a real OpenSearch cluster — guild.md §15
Slice 3, commits 3-5's verify criteria (typo tolerance, autocomplete,
synonyms, combined facets, exact-match boost). Fail here for the same
reason tests/test_opensearch.py already does — no live infra in this
environment, not a regression.
"""

import pytest

from integrations.opensearch.client import get_opensearch_client
from modules.search.mapping import index_name
from modules.search.selectors.search_query import build_autocomplete_query, build_search_query
from modules.search.services.ensure_index import ensure_index

TEST_LOCALE = "vi"


@pytest.fixture
def opensearch_index():
    ensure_index(TEST_LOCALE)
    client = get_opensearch_client()
    name = index_name(TEST_LOCALE)
    yield client, name
    client.indices.delete(index=name, ignore=[404])


def _index_doc(client, index, doc_id, **fields):
    base = {
        "product_id": doc_id,
        "sku": [],
        "barcode": [],
        "name": "",
        "category_ids": [],
        "brand_id": None,
        "attribute_value_ids": [],
        "base_price_vnd": None,
        "is_available": True,
        "popularity": 0,
        "rating": 0.0,
        "published_at": "2026-01-01T00:00:00Z",
    }
    base.update(fields)
    client.index(index=index, id=doc_id, body=base, refresh=True)


def test_typo_tolerant_query_still_matches(opensearch_index) -> None:
    client, name = opensearch_index
    _index_doc(client, name, "p1", name="Áo thun")

    body = build_search_query(text="Áo thnu")  # transposed letters
    result = client.search(index=name, body=body)

    assert result["hits"]["total"]["value"] >= 1


def test_synonym_pair_matches_each_other(opensearch_index) -> None:
    client, name = opensearch_index
    _index_doc(client, name, "p1", name="t-shirt")

    body = build_search_query(text="áo thun")  # configured synonym of t-shirt
    result = client.search(index=name, body=body)

    assert result["hits"]["total"]["value"] >= 1


def test_autocomplete_prefix_matches(opensearch_index) -> None:
    client, name = opensearch_index
    _index_doc(client, name, "p1", name="Áo thun")

    body = build_autocomplete_query("Áo th")
    result = client.search(index=name, body=body)

    assert result["hits"]["total"]["value"] >= 1


def test_combined_facets_narrow_results(opensearch_index) -> None:
    client, name = opensearch_index
    _index_doc(client, name, "match", category_ids=["cat-1"], base_price_vnd=50_000)
    _index_doc(client, name, "wrong-category", category_ids=["cat-2"], base_price_vnd=50_000)
    _index_doc(client, name, "wrong-price", category_ids=["cat-1"], base_price_vnd=500_000)

    body = build_search_query(category_id="cat-1", price_max=100_000)
    result = client.search(index=name, body=body)

    ids = {hit["_id"] for hit in result["hits"]["hits"]}
    assert ids == {"match"}


def test_exact_sku_ranks_above_fuzzy_text_match(opensearch_index) -> None:
    client, name = opensearch_index
    _index_doc(client, name, "fuzzy-decoy", name="ABC-999 lookalike product")
    _index_doc(client, name, "exact-sku", name="unrelated name", sku=["ABC-999"])

    body = build_search_query(text="ABC-999")
    result = client.search(index=name, body=body)

    assert result["hits"]["hits"][0]["_id"] == "exact-sku"
