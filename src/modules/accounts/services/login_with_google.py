"""Google login: creates a Customer on first sign-in, or links the Google
LoginMethod to an existing (email-matched) Customer otherwise — guild.md
§3.1 "can link multiple login methods to the same Customer."

Only the password-first-then-Google direction is covered here (this
commit's verify criterion). Adding a password method to an existing
Google-only account needs a separate authenticated endpoint, not yet built.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from integrations.google_oauth.client import GoogleOAuthError, get_google_oauth_client
from modules.accounts.errors import GoogleEmailNotVerifiedError, InvalidGoogleTokenError
from modules.accounts.models import Customer, LoginMethod
from modules.accounts.services.sessions import issue_session


def login_with_google(*, id_token: str) -> tuple[Customer, str, str]:
    try:
        profile = get_google_oauth_client().verify_id_token(id_token)
    except GoogleOAuthError:
        raise InvalidGoogleTokenError from None

    with transaction.atomic():
        try:
            login_method = LoginMethod.objects.select_related("customer").get(
                provider=LoginMethod.Provider.GOOGLE, provider_subject_id=profile.subject_id
            )
            customer = login_method.customer
        except LoginMethod.DoesNotExist:
            customer, created = Customer.objects.get_or_create(
                email=profile.email,
                defaults={"email_verified_at": timezone.now() if profile.email_verified else None},
            )
            if not created and not profile.email_verified:
                # Refuse to link an unverified Google identity to an existing,
                # email-matched Customer — Google's email_verified=false means
                # anyone could claim that address, so linking here would let an
                # attacker take over the existing account.
                raise GoogleEmailNotVerifiedError from None
            if not created and profile.email_verified and not customer.is_email_verified:
                customer.email_verified_at = timezone.now()
                customer.save(update_fields=["email_verified_at"])

            LoginMethod.objects.create(
                customer=customer,
                provider=LoginMethod.Provider.GOOGLE,
                provider_subject_id=profile.subject_id,
            )

    access, refresh = issue_session(customer)
    return customer, access, refresh
