"""Email change via the shared VerificationToken mechanism (commit 5).

Requesting the change requires authentication (a self-service action on
your own account); confirming it doesn't — the link is emailed to the new
address, and holding a valid token there is the proof of ownership.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.accounts.errors import EmailAlreadyTakenError, InvalidVerificationTokenError
from modules.accounts.models import Customer, VerificationToken
from modules.accounts.services.verification_tokens import generate_token, hash_token

EMAIL_CHANGE_TOKEN_TTL = timedelta(hours=24)


def request_email_change(*, customer: Customer, new_email: str) -> None:
    normalized_email = new_email.strip().lower()
    if Customer.objects.filter(email=normalized_email).exclude(id=customer.id).exists():
        raise EmailAlreadyTakenError

    raw_token, token_hash = generate_token()
    VerificationToken.objects.create(
        customer=customer,
        purpose=VerificationToken.Purpose.EMAIL_CHANGE,
        token_hash=token_hash,
        new_email=normalized_email,
        expires_at=timezone.now() + EMAIL_CHANGE_TOKEN_TTL,
    )
    send_mail(
        subject="Confirm your new email",
        message=f"Your email change token is: {raw_token}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[normalized_email],
    )


def confirm_email_change(*, raw_token: str) -> Customer:
    token_hash = hash_token(raw_token)
    try:
        token = VerificationToken.objects.select_related("customer").get(
            token_hash=token_hash,
            purpose=VerificationToken.Purpose.EMAIL_CHANGE,
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
        customer.email = token.new_email
        customer.email_verified_at = timezone.now()
        try:
            customer.save(update_fields=["email", "email_verified_at"])
        except IntegrityError:
            raise EmailAlreadyTakenError from None

    return customer
