"""Register a Customer via email/password and start email verification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from modules.accounts.models import Customer, LoginMethod, VerificationToken
from modules.accounts.services.verification_tokens import generate_token

EMAIL_VERIFICATION_TOKEN_TTL = timedelta(hours=24)


@dataclass(frozen=True)
class RegistrationResult:
    customer: Customer
    verification_token: str


def register_customer(*, email: str, password: str) -> RegistrationResult:
    """Create the Customer + password LoginMethod, issue a verification
    token, and send a (placeholder) verification email.

    Templated/localized transactional email is Slice 7 (Issue #6 "Out of
    Scope") — this sends a plain, functional message.
    """
    with transaction.atomic():
        customer = Customer.objects.create(email=email.strip().lower())
        LoginMethod.objects.create(
            customer=customer,
            provider=LoginMethod.Provider.PASSWORD,
            password_hash=make_password(password),
        )
        raw_token, token_hash = generate_token()
        VerificationToken.objects.create(
            customer=customer,
            purpose=VerificationToken.Purpose.EMAIL_VERIFICATION,
            token_hash=token_hash,
            expires_at=timezone.now() + EMAIL_VERIFICATION_TOKEN_TTL,
        )

    send_mail(
        subject="Verify your email",
        message=f"Your verification token is: {raw_token}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[customer.email],
    )
    return RegistrationResult(customer=customer, verification_token=raw_token)
