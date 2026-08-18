"""Per-locale OpenSearch index mapping — guild.md §15 Slice 3, commit 1.
One index per locale (`products_<locale>`) rather than a single
multilingual index, so each locale gets its own analyzer without
cross-locale interference — PostgreSQL stays the source of truth and this
projection is fully rebuildable (`services/ensure_index.py`,
`management/commands/reindex_search.py`).
"""

from __future__ import annotations

# A minimal seed list proving synonym config end-to-end (Issue #8 commit 3);
# a real catalog would source this from a managed synonym list, not code.
SYNONYMS = [
    "áo thun, t-shirt, tshirt",
    "quần, pants, trousers",
]


def index_name(locale: str) -> str:
    return f"products_{locale}"


def build_index_settings() -> dict:
    return {
        "analysis": {
            "filter": {
                "autocomplete_filter": {
                    "type": "edge_ngram",
                    "min_gram": 1,
                    "max_gram": 20,
                },
                "synonym_filter": {
                    "type": "synonym",
                    "synonyms": SYNONYMS,
                },
            },
            "analyzer": {
                # Indexes progressively longer prefixes so a partial query
                # ("Áo th") still matches — commit 3's autocomplete.
                "autocomplete_index_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "autocomplete_filter"],
                },
                # Synonym expansion belongs at search time only — expanding
                # at index time would let unrelated documents match each
                # other's synonyms.
                "search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "synonym_filter"],
                },
            },
        }
    }


def build_index_mapping() -> dict:
    return {
        "properties": {
            "product_id": {"type": "keyword"},
            "sku": {"type": "keyword"},
            "barcode": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "autocomplete_index_analyzer",
                "search_analyzer": "search_analyzer",
            },
            "category_ids": {"type": "keyword"},
            "brand_id": {"type": "keyword"},
            "attribute_value_ids": {"type": "keyword"},
            "base_price_vnd": {"type": "long"},
            "is_available": {"type": "boolean"},
            # Placeholders — populated once Order/Review data exists
            # (Slices 5, 9); wired now so sort options don't need a
            # later schema change.
            "popularity": {"type": "integer"},
            "rating": {"type": "float"},
            "published_at": {"type": "date"},
        }
    }
