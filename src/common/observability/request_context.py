"""Pulls IP/request-id off a request for audit logging (guild.md §12.3).
Duck-typed on `.META`/`.id` so it accepts either a Django `HttpRequest` or
a DRF `Request` (which proxies both through to the wrapped request).
"""

from __future__ import annotations

from typing import Any


def client_ip(request: Any) -> str | None:
    if request is None:
        return None
    return request.META.get("REMOTE_ADDR")


def request_id(request: Any) -> str:
    if request is None:
        return ""
    return str(getattr(request, "id", ""))
