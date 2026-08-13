"""Password login — issues an access/refresh token pair for a Customer."""

from __future__ import annotations

from django.contrib.auth.hashers import check_password

from modules.accounts.errors import InvalidCredentialsError
from modules.accounts.models import Customer, LoginMethod
from modules.accounts.services.sessions import issue_session


def login_customer(*, email: str, password: str) -> tuple[Customer, str, str]:
    """Returns `(customer, access_token, refresh_token)`."""
    normalized_email = email.strip().lower()
    try:
        customer = Customer.objects.get(email=normalized_email, is_active=True)
        login_method = customer.login_methods.get(provider=LoginMethod.Provider.PASSWORD)
    except (Customer.DoesNotExist, LoginMethod.DoesNotExist):
        raise InvalidCredentialsError from None

    if not check_password(password, login_method.password_hash):
        raise InvalidCredentialsError

    access, refresh = issue_session(customer)
    return customer, access, refresh
