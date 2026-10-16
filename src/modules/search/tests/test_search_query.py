"""build_search_query / build_autocomplete_query — guild.md §15 Slice 3,
commits 3-5's query-shape contract. Pure functions, no live cluster
needed; test_search_behavior.py covers actual OpenSearch execution."""

from modules.search.selectors.search_query import (
    AUTOCOMPLETE_SIZE,
    SORT_CLAUSES,
    build_autocomplete_query,
    build_search_query,
)


def test_text_query_uses_fuzziness_for_typo_tolerance() -> None:
    body = build_search_query(text="ao thun")

    should = body["query"]["bool"]["should"]
    multi_match = next(c["multi_match"] for c in should if "multi_match" in c)
    assert multi_match["fuzziness"] == "AUTO"
    assert multi_match["fields"] == ["name"]


def test_exact_sku_and_barcode_are_boosted_should_clauses() -> None:
    body = build_search_query(text="SKU-123")

    should = body["query"]["bool"]["should"]
    boosts = {
        clause["term"]["sku"]["boost"] for clause in should if "sku" in clause.get("term", {})
    }
    assert boosts == {1000}
    assert body["query"]["bool"]["minimum_should_match"] == 1


def test_exact_sku_match_alone_is_not_excluded_by_the_fuzzy_clause() -> None:
    """The fuzzy text clause must not be a `must` — a document whose SKU
    matches exactly but whose name doesn't fuzzy-match the query text
    must still be a candidate match, not filtered out entirely."""
    body = build_search_query(text="ABC-999")

    assert "must" not in body["query"]["bool"]


def test_no_text_produces_match_all_without_filters() -> None:
    body = build_search_query()

    assert body["query"] == {"match_all": {}}


def test_category_and_brand_facets_become_filter_clauses() -> None:
    body = build_search_query(category_id="cat-1", brand_id="brand-1")

    filters = body["query"]["bool"]["filter"]
    assert {"term": {"category_ids": "cat-1"}} in filters
    assert {"term": {"brand_id": "brand-1"}} in filters


def test_values_of_one_attribute_are_or_ed_into_a_single_clause() -> None:
    """This used to emit one `term` clause per value, which AND-ed them:
    ticking Red and Blue in one colour facet asked for a Product carrying
    both values of the same Attribute, and the answer to that is always no
    results."""
    body = build_search_query(attribute_filters=[("color", "red"), ("color", "blue")])

    filters = body["query"]["bool"]["filter"]
    assert filters == [{"terms": {"attributes": ["color:red", "color:blue"]}}]


def test_different_attributes_are_and_ed_across_clauses() -> None:
    body = build_search_query(attribute_filters=[("color", "red"), ("size", "m")])

    filters = body["query"]["bool"]["filter"]
    assert {"terms": {"attributes": ["color:red"]}} in filters
    assert {"terms": {"attributes": ["size:m"]}} in filters
    assert len(filters) == 2


def test_or_within_and_and_across_combine() -> None:
    """The conventional storefront rule, in one assertion: red OR blue,
    and size M."""
    body = build_search_query(
        attribute_filters=[("color", "red"), ("size", "m"), ("color", "blue")]
    )

    filters = body["query"]["bool"]["filter"]
    assert {"terms": {"attributes": ["color:red", "color:blue"]}} in filters
    assert {"terms": {"attributes": ["size:m"]}} in filters
    assert len(filters) == 2


def test_price_range_facet() -> None:
    body = build_search_query(price_min=1000, price_max=5000)

    filters = body["query"]["bool"]["filter"]
    assert {"range": {"base_price_vnd": {"gte": 1000, "lte": 5000}}} in filters


def test_availability_facet() -> None:
    body = build_search_query(available_only=True)

    filters = body["query"]["bool"]["filter"]
    assert {"term": {"is_available": True}} in filters


def test_relevance_sort_is_score_then_a_tiebreaker() -> None:
    """Relevance used to leave `sort` off and let OpenSearch default to
    _score. It is spelled out now because search_after has nothing to
    resume from without an explicit sort, and _score alone is not a total
    order — equal scores would break per-shard, skipping or repeating
    Products exactly at a page boundary."""
    body = build_search_query(text="x", sort="relevance")

    assert body["sort"] == [{"_score": "desc"}, {"product_id": "asc"}]


def test_recency_sort_adds_explicit_sort_clause() -> None:
    body = build_search_query(sort="recency")

    assert body["sort"] == [{"published_at": "desc"}, {"product_id": "asc"}]


def test_every_sort_ends_in_the_same_tiebreaker() -> None:
    """The invariant cursors depend on: whichever sort a Customer picks,
    the ordering is total, so a page boundary lands in exactly one place."""
    for sort in SORT_CLAUSES:
        assert build_search_query(sort=sort)["sort"][-1] == {"product_id": "asc"}


def test_window_arguments_reach_the_body() -> None:
    body = build_search_query(size=21, search_after=[1.0, "p20"])

    assert body["size"] == 21
    assert body["search_after"] == [1.0, "p20"]


def test_autocomplete_is_capped_without_asking_the_caller() -> None:
    assert build_autocomplete_query("Áo th")["size"] == AUTOCOMPLETE_SIZE


def test_autocomplete_query_bypasses_synonym_analyzer() -> None:
    body = build_autocomplete_query("Áo th")

    assert body["query"]["match"]["name"]["query"] == "Áo th"
    assert body["query"]["match"]["name"]["analyzer"] == "standard"
