"""Refresh-session issuance, rotation and revocation.

Only a hash of each refresh token's `jti` is stored (guild.md §6.1); refresh
tokens rotate on every use — the presented token is revoked and a new
access/refresh pair is issued.
"""

from __future__ import annotations

import hashlib
from uuid import UUID

from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from common.auth.authentication import ACTOR_TYPE_CLAIM, CUSTOMER_ACTOR_TYPE
from modules.accounts.errors import InvalidRefreshTokenError, SessionNotFoundError
from modules.accounts.models import Customer, Session


def _hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()


def issue_session(customer: Customer) -> tuple[str, str]:
    """Issue a fresh access/refresh pair and record the refresh session's
    hash. Returns `(access, refresh)` as strings."""
    refresh = RefreshToken.for_user(customer)  # type: ignore[type-var]
    refresh[ACTOR_TYPE_CLAIM] = CUSTOMER_ACTOR_TYPE
    refresh.access_token[ACTOR_TYPE_CLAIM] = CUSTOMER_ACTOR_TYPE

    Session.objects.create(
        customer=customer,
        refresh_token_hash=_hash_jti(refresh["jti"]),
        expires_at=timezone.now() + refresh.lifetime,
    )
    return str(refresh.access_token), str(refresh)


def rotate_refresh_token(*, raw_refresh_token: str) -> tuple[str, str]:
    """Validate the presented refresh token, revoke its Session, and issue
    a brand-new access/refresh pair."""
    try:
        old_refresh = RefreshToken(raw_refresh_token)  # type: ignore[arg-type]
    except TokenError:
        raise InvalidRefreshTokenError from None

    if old_refresh.get(ACTOR_TYPE_CLAIM) != CUSTOMER_ACTOR_TYPE:
        raise InvalidRefreshTokenError

    try:
        session = Session.objects.select_related("customer").get(
            refresh_token_hash=_hash_jti(old_refresh["jti"])
        )
    except Session.DoesNotExist:
        raise InvalidRefreshTokenError from None

    if not session.is_active:
        raise InvalidRefreshTokenError

    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])

    return issue_session(session.customer)


def revoke_session(*, customer: Customer, session_id: UUID) -> None:
    updated = Session.objects.filter(
        id=session_id, customer=customer, revoked_at__isnull=True
    ).update(revoked_at=timezone.now())
    if not updated:
        raise SessionNotFoundError


def revoke_all_sessions(*, customer: Customer) -> None:
    Session.objects.filter(customer=customer, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
