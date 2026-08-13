"""Deterministic local/test double for GoogleOAuthClient — no network call.

The "id_token" is treated as a JSON-encoded GoogleProfile fixture instead of
a real signed JWT, so tests can construct one directly:
`json.dumps({"sub": "google-123", "email": "a@example.com"})`.
"""

from __future__ import annotations

import json

from integrations.google_oauth.client import GoogleOAuthError, GoogleProfile


class FakeGoogleOAuthClient:
    def verify_id_token(self, id_token: str) -> GoogleProfile:
        try:
            payload = json.loads(id_token)
            return GoogleProfile(
                subject_id=payload["sub"],
                email=payload["email"].strip().lower(),
                email_verified=payload.get("email_verified", True),
            )
        except (json.JSONDecodeError, KeyError, AttributeError) as exc:
            raise GoogleOAuthError("Invalid fake id_token fixture.") from exc
