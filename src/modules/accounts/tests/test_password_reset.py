from datetime import timedelta

import pytest
from django.contrib.auth.hashers import check_password
from django.core import mail
from django.utils import timezone

from modules.accounts.errors import InvalidVerificationTokenError
from modules.accounts.models import LoginMethod, VerificationToken
from modules.accounts.services.password_reset import (
    confirm_password_reset,
    request_password_reset,
)
from modules.accounts.services.register_customer import register_customer


@pytest.mark.django_db
def test_request_password_reset_sends_email_for_known_customer() -> None:
    register_customer(email="reset1@example.com", password="a-strong-password-123")

    request_password_reset(email="reset1@example.com")

    assert len(mail.outbox) == 2  # verification email + reset email
    token = VerificationToken.objects.get(purpose=VerificationToken.Purpose.PASSWORD_RESET)
    assert token.new_email == ""


@pytest.mark.django_db
def test_request_password_reset_is_silent_for_unknown_email() -> None:
    request_password_reset(email="nobody@example.com")

    assert len(mail.outbox) == 0
    assert VerificationToken.objects.count() == 0


@pytest.mark.django_db
def test_confirm_password_reset_updates_the_password_hash() -> None:
    register_customer(email="reset2@example.com", password="a-strong-password-123")
    request_password_reset(email="reset2@example.com")
    raw_token = mail.outbox[-1].body.rsplit(": ", 1)[-1].strip()

    customer = confirm_password_reset(raw_token=raw_token, new_password="a-new-password-456")

    login_method = LoginMethod.objects.get(
        customer=customer, provider=LoginMethod.Provider.PASSWORD
    )
    assert check_password("a-new-password-456", login_method.password_hash)
    assert not check_password("a-strong-password-123", login_method.password_hash)


@pytest.mark.django_db
def test_confirm_password_reset_rejects_expired_token() -> None:
    register_customer(email="reset3@example.com", password="a-strong-password-123")
    request_password_reset(email="reset3@example.com")
    raw_token = mail.outbox[-1].body.rsplit(": ", 1)[-1].strip()
    VerificationToken.objects.filter(purpose=VerificationToken.Purpose.PASSWORD_RESET).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    with pytest.raises(InvalidVerificationTokenError):
        confirm_password_reset(raw_token=raw_token, new_password="a-new-password-456")


@pytest.mark.django_db
def test_confirm_password_reset_rejects_unknown_token() -> None:
    with pytest.raises(InvalidVerificationTokenError):
        confirm_password_reset(raw_token="bogus", new_password="a-new-password-456")
