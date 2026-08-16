"""Shared raw-token/hash generation for VerificationToken rows.

Only the hash is ever persisted; the raw token is returned to the caller
once, to be embedded in the verification/reset email.
"""

from __future__ import annotations

import hashlib
import secrets


def generate_token() -> tuple[str, str]:
    """Return `(raw_token, token_hash)`."""
    raw_token = secrets.token_urlsafe(32)
    return raw_token, hash_token(raw_token)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
