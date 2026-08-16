"""DRF integration for common/db/idempotency.py — enforces `Idempotency-Key`
on sensitive/side-effecting actions (guild.md §6.2/§3.10): replays the
same response for a repeated key+body, 409s on key reuse with a different
body, 400s if the header is missing entirely.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT

from common.db.idempotency import IdempotencyKeyConflict, get_cached_response, store_response

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"


class IdempotencyKeyRequiredError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = f"This action requires an {IDEMPOTENCY_KEY_HEADER} header."
    default_code = "common.idempotency_key_required"


class IdempotencyKeyConflictError(APIException):
    status_code = HTTP_409_CONFLICT
    default_detail = "This Idempotency-Key was already used with a different request body."
    default_code = "common.idempotency_key_conflict"


def require_idempotency_key(request: Request) -> str:
    key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
    if not key:
        raise IdempotencyKeyRequiredError
    return key


def replay_if_cached(
    *, request: Request, actor_type: str, actor_id: str, action: str, idempotency_key: str
) -> Response | None:
    """Returns the replayed `Response` for a repeated request, or `None`
    for a fresh key. Raises `IdempotencyKeyConflictError` on key reuse with
    a different body."""
    try:
        cached = get_cached_response(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            idempotency_key=idempotency_key,
            request_data=request.data,
        )
    except IdempotencyKeyConflict:
        raise IdempotencyKeyConflictError from None

    if cached is None:
        return None
    response_status, body = cached
    return Response(body, status=response_status)


def remember_response(
    *,
    request: Request,
    actor_type: str,
    actor_id: str,
    action: str,
    idempotency_key: str,
    response: Response,
) -> None:
    store_response(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        idempotency_key=idempotency_key,
        request_data=request.data,
        response_status=response.status_code,
        response_body=response.data,  # None for a 204 — JSONField(null=True) accepts that.
    )
