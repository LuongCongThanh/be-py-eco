"""Request ID middleware — assigns a correlation ID to every request.

Used by common/api's success envelope (`meta.request_id`) and error envelope
(`trace_id`), and echoed back on the response so client/server logs can be
correlated.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from common.ids.uuid7 import uuid7

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    """Sets `request.id` (a UUID) from the incoming header, or generates one."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request.id = self._parse(incoming) if incoming else uuid7()  # type: ignore[attr-defined]
        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = str(request.id)  # type: ignore[attr-defined]
        return response

    @staticmethod
    def _parse(value: str) -> uuid.UUID:
        try:
            return uuid.UUID(value)
        except ValueError:
            return uuid7()
