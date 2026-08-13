"""Password reset via the shared VerificationToken mechanism (commit 5).

Works even for a Customer with no password LoginMethod yet — the confirm
step creates one if missing, which doubles as "add a password login" for a
Google-only account.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from modules.accounts.errors import InvalidVerificationTokenError
from modules.accounts.models import Customer, LoginMethod, VerificationToken
from modules.accounts.services.verification_tokens import generate_token, hash_token

PASSWORD_RESET_TOKEN_TTL = timedelta(hours=1)


def request_password_reset(*, email: str) -> None:
    """Always succeeds from the caller's perspective, regardless of whether
    the email is registered — avoids leaking account existence."""
    normalized_email = email.strip().lower()
    try:
        customer = Customer.objects.get(email=normalized_email, is_active=True)
    except Customer.DoesNotExist:
        return

    raw_token, token_hash = generate_token()
    VerificationToken.objects.create(
        customer=customer,
        purpose=VerificationToken.Purpose.PASSWORD_RESET,
        token_hash=token_hash,
        expires_at=timezone.now() + PASSWORD_RESET_TOKEN_TTL,
    )
    send_mail(
        subject="Reset your password",
        message=f"Your password reset token is: {raw_token}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[customer.email],
    )


def confirm_password_reset(*, raw_token: str, new_password: str) -> Customer:
    token_hash = hash_token(raw_token)
    try:
        token = VerificationToken.objects.select_related("customer").get(
            token_hash=token_hash,
            purpose=VerificationToken.Purpose.PASSWORD_RESET,
            consumed_at__isnull=True,
        )
    except VerificationToken.DoesNotExist:
        raise InvalidVerificationTokenError from None

    if token.expires_at < timezone.now():
        raise InvalidVerificationTokenError

    with transaction.atomic():
        token.consumed_at = timezone.now()
        token.save(update_fields=["consumed_at"])

        LoginMethod.objects.update_or_create(
            customer=token.customer,
            provider=LoginMethod.Provider.PASSWORD,
            defaults={"password_hash": make_password(new_password)},
        )

    return token.customer
