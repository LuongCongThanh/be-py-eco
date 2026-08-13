"""Health check endpoints — guild.md §9.3.

`/health/live` only confirms the process is alive: no dependency calls, so a
struggling PostgreSQL/Redis/etc. never takes the whole pod out of rotation.
`/health/ready` additionally confirms PostgreSQL is reachable, since nothing
useful can happen without it.
"""

from __future__ import annotations

from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpRequest, JsonResponse


def live(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def ready(request: HttpRequest) -> JsonResponse:
    try:
        connections["default"].ensure_connection()
    except OperationalError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
