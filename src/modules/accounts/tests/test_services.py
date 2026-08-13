from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from modules.accounts.errors import InvalidCredentialsError, InvalidVerificationTokenError
from modules.accounts.models import LoginMethod, VerificationToken
from modules.accounts.services.login_customer import login_customer
from modules.accounts.services.register_customer import register_customer
from modules.accounts.services.verify_email import verify_email


@pytest.mark.django_db
def test_register_customer_creates_customer_login_method_and_sends_email() -> None:
    result = register_customer(email="Test@Example.com ", password="a-strong-password-123")

    assert result.customer.email == "test@example.com"
    assert result.customer.is_email_verified is False

    login_method = LoginMethod.objects.get(customer=result.customer)
    assert login_method.provider == LoginMethod.Provider.PASSWORD
    assert login_method.password_hash != "a-strong-password-123"

    token = VerificationToken.objects.get(customer=result.customer)
    assert token.purpose == VerificationToken.Purpose.EMAIL_VERIFICATION
    assert token.consumed_at is None

    assert len(mail.outbox) == 1
    assert result.verification_token in mail.outbox[0].body


@pytest.mark.django_db
def test_verify_email_flips_the_flag_and_consumes_the_token() -> None:
    result = register_customer(email="verify@example.com", password="a-strong-password-123")

    customer = verify_email(raw_token=result.verification_token)

    assert customer.is_email_verified is True
    token = VerificationToken.objects.get(customer=customer)
    assert token.consumed_at is not None


@pytest.mark.django_db
def test_verify_email_rejects_unknown_token() -> None:
    with pytest.raises(InvalidVerificationTokenError):
        verify_email(raw_token="not-a-real-token")


@pytest.mark.django_db
def test_verify_email_rejects_already_consumed_token() -> None:
    result = register_customer(email="reused@example.com", password="a-strong-password-123")
    verify_email(raw_token=result.verification_token)

    with pytest.raises(InvalidVerificationTokenError):
        verify_email(raw_token=result.verification_token)


@pytest.mark.django_db
def test_verify_email_rejects_expired_token() -> None:
    result = register_customer(email="expired@example.com", password="a-strong-password-123")
    VerificationToken.objects.filter(customer=result.customer).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    with pytest.raises(InvalidVerificationTokenError):
        verify_email(raw_token=result.verification_token)


@pytest.mark.django_db
def test_login_customer_returns_tokens_for_valid_credentials() -> None:
    result = register_customer(email="login@example.com", password="a-strong-password-123")

    customer, refresh = login_customer(email="login@example.com", password="a-strong-password-123")

    assert customer.id == result.customer.id
    assert str(refresh.access_token)
    assert str(refresh)


@pytest.mark.django_db
def test_login_customer_rejects_wrong_password() -> None:
    register_customer(email="login2@example.com", password="a-strong-password-123")

    with pytest.raises(InvalidCredentialsError):
        login_customer(email="login2@example.com", password="wrong-password")


@pytest.mark.django_db
def test_login_customer_rejects_unknown_email() -> None:
    with pytest.raises(InvalidCredentialsError):
        login_customer(email="nobody@example.com", password="whatever-123")
