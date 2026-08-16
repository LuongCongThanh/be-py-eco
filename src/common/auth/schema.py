"""OpenAPI security scheme for `common.auth.authentication.JWTAuthentication`.

drf-spectacular only knows the built-in simplejwt authenticator's scheme;
our subclass needs its own registration or schema generation warns/fails.
Imported by common/auth/__init__.py so it's registered before generation.
"""

from __future__ import annotations

from typing import Any

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):  # type: ignore[misc]
    target_class = "common.auth.authentication.JWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema: Any) -> dict[str, str]:
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
