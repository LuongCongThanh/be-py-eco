"""Consume an email-verification VerificationToken, flipping the Customer's
verified flag."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from modules.accounts.errors import InvalidVerificationTokenError
from modules.accounts.models import Customer, VerificationToken
from modules.accounts.services.verification_tokens import hash_token


def verify_email(*, raw_token: str) -> Customer:
    token_hash = hash_token(raw_token)
    try:
        token = VerificationToken.objects.select_related("customer").get(
            token_hash=token_hash,
            purpose=VerificationToken.Purpose.EMAIL_VERIFICATION,
            consumed_at__isnull=True,
        )
    except VerificationToken.DoesNotExist:
        raise InvalidVerificationTokenError from None

    if token.expires_at < timezone.now():
        raise InvalidVerificationTokenError

    with transaction.atomic():
        token.consumed_at = timezone.now()
        token.save(update_fields=["consumed_at"])

        customer = token.customer
        customer.email_verified_at = timezone.now()
        customer.save(update_fields=["email_verified_at"])

    return customer
