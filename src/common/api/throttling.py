"""Rate limiting for auth endpoints — per IP and per account (guild.md
§6.3). DRF's throttling framework, not django-axes: this project's login
doesn't go through django.contrib.auth's `authenticate()`/login signals
that axes hooks into (Customer/Staff aren't `AUTH_USER_MODEL` — see
modules/accounts/models/customer.py), so DRF's request-scoped throttles fit
without fighting that mismatch — guild.md commit 12 explicitly allows this
as an alternative to django-axes.

Concrete rate numbers are NOT decided here — guild.md §16 lists "concrete
rate limits" as an explicit open decision that must not be guessed in code.
`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` reads them from the environment
with placeholder defaults suitable only for local dev/test.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle
from rest_framework.views import APIView


class AuthIPRateThrottle(AnonRateThrottle):
    """Per-IP throttle for an anonymous auth endpoint."""

    scope = "auth_ip"


class AuthAccountRateThrottle(SimpleRateThrottle):
    """Per-account throttle for an anonymous auth endpoint, keyed by the
    email in the request body (there's no `request.user` to key on yet)."""

    scope = "auth_account"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        data: Mapping[str, Any] = request.data if isinstance(request.data, Mapping) else {}
        email = str(data.get("email", "")).strip().lower()
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}


class AuthUserRateThrottle(UserRateThrottle):
    """Per-account throttle for an already-authenticated auth endpoint
    (e.g. MFA confirm), keyed by `request.user` instead of a request-body
    email."""

    scope = "auth_account"
