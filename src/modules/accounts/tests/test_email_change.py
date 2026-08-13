from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from modules.accounts.errors import EmailAlreadyTakenError, InvalidVerificationTokenError
from modules.accounts.models import VerificationToken
from modules.accounts.services.email_change import confirm_email_change, request_email_change
from modules.accounts.services.register_customer import register_customer


@pytest.mark.django_db
def test_request_email_change_sends_a_token_to_the_new_address() -> None:
    result = register_customer(email="oldmail@example.com", password="a-strong-password-123")

    request_email_change(customer=result.customer, new_email="newmail@example.com")

    token = VerificationToken.objects.get(purpose=VerificationToken.Purpose.EMAIL_CHANGE)
    assert token.new_email == "newmail@example.com"
    assert mail.outbox[-1].to == ["newmail@example.com"]


@pytest.mark.django_db
def test_request_email_change_rejects_an_email_taken_by_another_customer() -> None:
    result = register_customer(email="mine@example.com", password="a-strong-password-123")
    register_customer(email="taken@example.com", password="a-strong-password-123")

    with pytest.raises(EmailAlreadyTakenError):
        request_email_change(customer=result.customer, new_email="taken@example.com")


@pytest.mark.django_db
def test_confirm_email_change_updates_the_email_and_marks_it_verified() -> None:
    result = register_customer(email="confirmold@example.com", password="a-strong-password-123")
    request_email_change(customer=result.customer, new_email="confirmnew@example.com")
    raw_token = mail.outbox[-1].body.rsplit(": ", 1)[-1].strip()

    customer = confirm_email_change(raw_token=raw_token)

    assert customer.email == "confirmnew@example.com"
    assert customer.is_email_verified is True


@pytest.mark.django_db
def test_confirm_email_change_rejects_expired_token() -> None:
    result = register_customer(email="expiredold@example.com", password="a-strong-password-123")
    request_email_change(customer=result.customer, new_email="expirednew@example.com")
    raw_token = mail.outbox[-1].body.rsplit(": ", 1)[-1].strip()
    VerificationToken.objects.filter(purpose=VerificationToken.Purpose.EMAIL_CHANGE).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    with pytest.raises(InvalidVerificationTokenError):
        confirm_email_change(raw_token=raw_token)


@pytest.mark.django_db
def test_confirm_email_change_rejects_unknown_token() -> None:
    with pytest.raises(InvalidVerificationTokenError):
        confirm_email_change(raw_token="bogus")
