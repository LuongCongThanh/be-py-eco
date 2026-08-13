"""Google ID token verification adapter (guild.md §7.6): checkout/services
never call a vendor SDK directly — they go through this interface, and the
concrete implementation is chosen via `settings.GOOGLE_OAUTH_CLIENT_CLASS`
(the real HTTP client in production, `integrations.google_oauth.fake` in
local/test).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx
from django.conf import settings
from django.utils.module_loading import import_string

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleOAuthError(Exception):
    """Raised when a Google ID token can't be verified."""


@dataclass(frozen=True)
class GoogleProfile:
    subject_id: str  # Google's `sub`
    email: str
    email_verified: bool


class GoogleOAuthClient(Protocol):
    def verify_id_token(self, id_token: str) -> GoogleProfile: ...


class HttpGoogleOAuthClient:
    def __init__(self) -> None:
        self._client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        self._timeout = 5.0

    def verify_id_token(self, id_token: str) -> GoogleProfile:
        try:
            response = httpx.get(
                GOOGLE_TOKENINFO_URL, params={"id_token": id_token}, timeout=self._timeout
            )
        except httpx.HTTPError as exc:
            raise GoogleOAuthError("Could not reach Google to verify the ID token.") from exc

        if response.status_code != 200:
            raise GoogleOAuthError("Google rejected the ID token.")

        payload = response.json()
        if payload.get("aud") != self._client_id:
            raise GoogleOAuthError("ID token was issued for a different client.")

        return GoogleProfile(
            subject_id=payload["sub"],
            email=payload["email"].strip().lower(),
            email_verified=payload.get("email_verified") == "true",
        )


def get_google_oauth_client() -> GoogleOAuthClient:
    client_class = import_string(settings.GOOGLE_OAUTH_CLIENT_CLASS)
    return client_class()  # type: ignore[no-any-return]
