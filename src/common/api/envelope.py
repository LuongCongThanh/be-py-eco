"""Success response envelope — `{"data": ..., "meta": ...}` per guild.md §5.3.

Every `/api/v1/...` view builds its success response through this helper so
pagination/request-id conventions stay identical across modules; no module
reimplements the envelope shape.
"""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest


def success_envelope(
    data: Any,
    *,
    request: HttpRequest | None = None,
    pagination: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the `{"data": ..., "meta": ...}` body for a success response."""
    meta: dict[str, Any] = {"request_id": str(getattr(request, "id", "")) if request else ""}
    if pagination is not None:
        meta["pagination"] = pagination
    return {"data": data, "meta": meta}
