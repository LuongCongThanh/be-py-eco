"""DRF exception handler producing RFC 9457 Problem Details per guild.md §5.4.

Wired via `REST_FRAMEWORK["EXCEPTION_HANDLER"]`. Every `/api/v1/...` error
response goes through here so the `code`/`errors`/`trace_id` shape is
identical across modules — no module reimplements error formatting.

`type` is fixed to RFC 9457's `"about:blank"`: this project's public domain
name (for a dereferenceable problem-type URI) is an explicit open decision
(guild.md §16) and must not be guessed in code; `code` is the stable,
frontend-facing identifier in the meantime.
"""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings

_TITLE_BY_CODE = {
    "invalid": "Validation Error",
    "not_found": "Not Found",
    "authentication_failed": "Authentication Failed",
    "not_authenticated": "Authentication Required",
    "permission_denied": "Permission Denied",
    "throttled": "Too Many Requests",
    "parse_error": "Malformed Request",
    "not_acceptable": "Not Acceptable",
    "unsupported_media_type": "Unsupported Media Type",
    "method_not_allowed": "Method Not Allowed",
}


def _is_leaf(node: Any) -> bool:
    return isinstance(node, dict) and "message" in node and set(node) <= {"message", "code"}


def _flatten_full_details(node: Any, prefix: str = "") -> list[dict[str, str]]:
    """Flatten `exc.get_full_details()` into a list of `{field, code, message}`."""
    if _is_leaf(node):
        return [
            {
                "field": prefix,
                "code": str(node.get("code", "invalid")),
                "message": str(node["message"]),
            }
        ]

    errors: list[dict[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            field = "" if key == api_settings.NON_FIELD_ERRORS_KEY else key
            next_prefix = f"{prefix}.{field}" if prefix and field else (field or prefix)
            errors.extend(_flatten_full_details(value, next_prefix))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            next_prefix = f"{prefix}.{index}" if prefix else str(index)
            errors.extend(_flatten_full_details(item, next_prefix))
    else:
        errors.append({"field": prefix, "code": "invalid", "message": str(node)})
    return errors


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Convert `exc` into a Problem Details `Response`, or `None` if unhandled."""
    if isinstance(exc, Http404):
        exc = drf_exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = drf_exceptions.PermissionDenied()

    if not isinstance(exc, drf_exceptions.APIException):
        return None  # Unhandled — Django's own 500 handling takes over.

    headers = {}
    if getattr(exc, "auth_header", None):
        headers["WWW-Authenticate"] = exc.auth_header
    if getattr(exc, "wait", None) is not None:
        headers["Retry-After"] = f"{exc.wait}"

    request = context.get("request")
    errors = _flatten_full_details(exc.get_full_details())
    single_unnamed_error = len(errors) == 1 and not errors[0]["field"]
    code = errors[0]["code"] if single_unnamed_error else exc.default_code
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.default_detail)

    body = {
        "type": "about:blank",
        "title": _TITLE_BY_CODE.get(code, exc.__class__.__name__),
        "status": exc.status_code,
        "code": code,
        "detail": detail,
        "instance": request.path if request is not None else "",
        "errors": [] if single_unnamed_error else errors,
        "trace_id": str(getattr(request, "id", "")) if request is not None else "",
    }
    return Response(body, status=exc.status_code, headers=headers)
