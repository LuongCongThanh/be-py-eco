"""build_search_query / build_autocomplete_query — guild.md §15 Slice 3,
commits 3-5's query-shape contract. Pure functions, no live cluster
needed; test_search_behavior.py covers actual OpenSearch execution."""

from modules.search.selectors.search_query import build_autocomplete_query, build_search_query


def test_text_query_uses_fuzziness_for_typo_tolerance() -> None:
    body = build_search_query(text="ao thun")

    multi_match = body["query"]["bool"]["must"][0]["multi_match"]
    assert multi_match["fuzziness"] == "AUTO"
    assert multi_match["fields"] == ["name"]


def test_exact_sku_and_barcode_are_boosted_should_clauses() -> None:
    body = build_search_query(text="SKU-123")

    should = body["query"]["bool"]["should"]
    boosts = {clause["term"]["sku"]["boost"] for clause in should if "sku" in clause["term"]}
    assert boosts == {1000}
    assert body["query"]["bool"]["minimum_should_match"] == 0


def test_no_text_produces_match_all_without_filters() -> None:
    body = build_search_query()

    assert body["query"] == {"match_all": {}}
    assert "sort" not in body


def test_category_and_brand_facets_become_filter_clauses() -> None:
    body = build_search_query(category_id="cat-1", brand_id="brand-1")

    filters = body["query"]["bool"]["filter"]
    assert {"term": {"category_ids": "cat-1"}} in filters
    assert {"term": {"brand_id": "brand-1"}} in filters


def test_attribute_value_facets_become_multiple_filter_clauses() -> None:
    body = build_search_query(attribute_value_ids=["v1", "v2"])

    filters = body["query"]["bool"]["filter"]
    assert {"term": {"attribute_value_ids": "v1"}} in filters
    assert {"term": {"attribute_value_ids": "v2"}} in filters


def test_price_range_facet() -> None:
    body = build_search_query(price_min=1000, price_max=5000)

    filters = body["query"]["bool"]["filter"]
    assert {"range": {"base_price_vnd": {"gte": 1000, "lte": 5000}}} in filters


def test_availability_facet() -> None:
    body = build_search_query(available_only=True)

    filters = body["query"]["bool"]["filter"]
    assert {"term": {"is_available": True}} in filters


def test_relevance_sort_omits_explicit_sort_clause() -> None:
    body = build_search_query(text="x", sort="relevance")

    assert "sort" not in body


def test_recency_sort_adds_explicit_sort_clause() -> None:
    body = build_search_query(sort="recency")

    assert body["sort"] == [{"published_at": "desc"}]


def test_autocomplete_query_bypasses_synonym_analyzer() -> None:
    body = build_autocomplete_query("Áo th")

    assert body["query"]["match"]["name"]["query"] == "Áo th"
    assert body["query"]["match"]["name"]["analyzer"] == "standard"
