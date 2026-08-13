import json

import pytest

from integrations.google_oauth.client import GoogleOAuthError
from integrations.google_oauth.fake import FakeGoogleOAuthClient
from modules.accounts.errors import InvalidGoogleTokenError
from modules.accounts.models import Customer, LoginMethod
from modules.accounts.services.login_with_google import login_with_google
from modules.accounts.services.register_customer import register_customer


def _fake_token(sub: str, email: str, email_verified: bool = True) -> str:
    return json.dumps({"sub": sub, "email": email, "email_verified": email_verified})


@pytest.mark.django_db
def test_login_with_google_creates_a_new_customer() -> None:
    customer, access, refresh = login_with_google(
        id_token=_fake_token("google-1", "newgoogle@example.com")
    )

    assert access
    assert refresh
    assert customer.email == "newgoogle@example.com"
    assert customer.is_email_verified is True
    assert LoginMethod.objects.get(customer=customer).provider == LoginMethod.Provider.GOOGLE


@pytest.mark.django_db
def test_login_with_google_links_to_an_existing_password_registered_customer() -> None:
    result = register_customer(email="linked@example.com", password="a-strong-password-123")

    customer, _, _ = login_with_google(id_token=_fake_token("google-2", "linked@example.com"))

    assert customer.id == result.customer.id
    assert LoginMethod.objects.filter(customer=customer).count() == 2
    assert customer.is_email_verified is True  # Google's verification is trusted


@pytest.mark.django_db
def test_login_with_google_is_idempotent_for_the_same_google_account() -> None:
    first_customer, _, _ = login_with_google(id_token=_fake_token("google-3", "repeat@example.com"))
    second_customer, _, _ = login_with_google(
        id_token=_fake_token("google-3", "repeat@example.com")
    )

    assert first_customer.id == second_customer.id
    assert Customer.objects.filter(email="repeat@example.com").count() == 1
    assert LoginMethod.objects.filter(customer=first_customer).count() == 1


@pytest.mark.django_db
def test_login_with_google_rejects_an_unverifiable_token() -> None:
    with pytest.raises(InvalidGoogleTokenError):
        login_with_google(id_token="not-valid-json")


def test_fake_google_oauth_client_rejects_malformed_fixtures() -> None:
    with pytest.raises(GoogleOAuthError):
        FakeGoogleOAuthClient().verify_id_token("{}")
