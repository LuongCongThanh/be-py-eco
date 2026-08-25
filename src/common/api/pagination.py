"""Cursor pagination — guild.md §5.3 (the `meta.pagination` shape) and
§5.6 ("Cursor pagination cho Product search... Mặc định 20, tối đa 100;
cursor opaque").

Cursor, not limit/offset: an offset silently skips or repeats rows when
the underlying set changes between pages, which for a live catalog is the
normal case rather than the edge case.

The cursor is opaque in the sense that a client must not construct or
reason about one — not in the sense of being secret. It is base64url of
compact JSON and is deliberately unsigned: a cursor is a *position*, not a
capability, and unlocks nothing a plain request could not already reach.

It does carry a short fingerprint of the query that issued it. Paging with
filters that have since changed produces a page that is neither the old
result set nor the new one, with nothing to signal it — the fingerprint
turns that silent wrong answer into a 400.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class InvalidCursorError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "This cursor is not valid for this query."
    default_code = "api.invalid_cursor"


class CursorPageSerializer(serializers.Serializer):
    """Mixed into an endpoint's query serializer so `cursor`/`page_size` are
    declared, validated and documented in the same place as its filters."""

    cursor = serializers.CharField(
        required=False, help_text="Opaque cursor from a previous response's meta.pagination."
    )
    page_size = serializers.IntegerField(
        required=False,
        default=DEFAULT_PAGE_SIZE,
        min_value=1,
        max_value=MAX_PAGE_SIZE,
        help_text=f"Results per page, {1}-{MAX_PAGE_SIZE}. Defaults to {DEFAULT_PAGE_SIZE}.",
    )


def query_fingerprint(filters: dict[str, Any]) -> str:
    """Digest of everything that shapes *which* rows come back.

    Pass only the filters. `page_size`, `cursor` and display-only params
    such as `currency` change how results are presented, not which ones
    exist, so including them would reject a page for a change that cannot
    affect it.
    """
    normalized = json.dumps(filters, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode()).hexdigest()[:8]


def encode_cursor(position: Any, *, fingerprint: str) -> str:
    payload = json.dumps({"p": position, "f": fingerprint}, separators=(",", ":"), default=str)
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: str, *, fingerprint: str) -> Any:
    padding = "=" * (-len(cursor) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor + padding))
        position = payload["p"]
        issued_for = payload["f"]
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise InvalidCursorError() from exc

    if issued_for != fingerprint:
        raise InvalidCursorError(
            "The filters changed since this cursor was issued. Start from the first page."
        )
    return position


def pagination_meta(*, next_cursor: str | None, has_more: bool, page_size: int) -> dict[str, Any]:
    """The `meta.pagination` object specified in guild.md §5.3."""
    return {"next_cursor": next_cursor, "has_more": has_more, "page_size": page_size}
