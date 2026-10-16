"""Cursor codec — guild.md §5.6. The endpoint-level walk-every-page
invariant lives in catalog/tests/test_storefront_pagination.py.
"""

import pytest

from common.api.pagination import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
    pagination_meta,
    query_fingerprint,
)

FINGERPRINT = query_fingerprint({"category_id": "c1"})


def test_a_cursor_round_trips() -> None:
    cursor = encode_cursor(["score", "p7"], fingerprint=FINGERPRINT)

    assert decode_cursor(cursor, fingerprint=FINGERPRINT) == ["score", "p7"]


def test_a_cursor_is_url_safe() -> None:
    """It travels in a query string, so it must survive one untouched."""
    cursor = encode_cursor({"id": "01a0/3759+8b48"}, fingerprint=FINGERPRINT)

    assert "/" not in cursor
    assert "+" not in cursor
    assert "=" not in cursor


@pytest.mark.parametrize("cursor", ["not-base64!!", "", "YWJj", "e30", "!!!!"])
def test_a_malformed_cursor_is_refused(cursor: str) -> None:
    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor, fingerprint=FINGERPRINT)


def test_a_cursor_from_a_different_query_is_refused() -> None:
    """Paging on with changed filters yields a page belonging to neither the
    old result set nor the new one, and nothing would signal it."""
    cursor = encode_cursor(["p7"], fingerprint=FINGERPRINT)

    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor, fingerprint=query_fingerprint({"category_id": "c2"}))


def test_the_fingerprint_ignores_filter_ordering() -> None:
    assert query_fingerprint({"a": 1, "b": 2}) == query_fingerprint({"b": 2, "a": 1})


def test_the_fingerprint_separates_a_missing_filter_from_an_empty_one() -> None:
    assert query_fingerprint({}) != query_fingerprint({"q": ""})


def test_pagination_meta_matches_the_documented_shape() -> None:
    """guild.md §5.3 fixes these three keys; frontends read them."""
    meta = pagination_meta(next_cursor="abc", has_more=True, page_size=DEFAULT_PAGE_SIZE)

    assert meta == {"next_cursor": "abc", "has_more": True, "page_size": 20}


def test_the_documented_bounds_are_what_guild_specifies() -> None:
    assert (DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE) == (20, 100)
