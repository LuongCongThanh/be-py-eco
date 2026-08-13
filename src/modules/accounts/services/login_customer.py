"""Password login — issues an access/refresh token pair for a Customer.

Refresh rotation and hashed session storage land in a later commit (Issue
#6 commit 7); this commit only issues tokens via simplejwt's low-level
`RefreshToken.for_user()`, tagged with the `actor_type` claim
common/auth/authentication.py dispatches on.
"""

from __future__ import annotations

from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

from common.auth.authentication import ACTOR_TYPE_CLAIM, CUSTOMER_ACTOR_TYPE
from modules.accounts.errors import InvalidCredentialsError
from modules.accounts.models import Customer, LoginMethod


def login_customer(*, email: str, password: str) -> tuple[Customer, RefreshToken]:
    normalized_email = email.strip().lower()
    try:
        customer = Customer.objects.get(email=normalized_email, is_active=True)
        login_method = customer.login_methods.get(provider=LoginMethod.Provider.PASSWORD)
    except (Customer.DoesNotExist, LoginMethod.DoesNotExist):
        raise InvalidCredentialsError from None

    if not check_password(password, login_method.password_hash):
        raise InvalidCredentialsError

    # Customer isn't AbstractBaseUser by design (see models/customer.py);
    # for_user() only needs `USER_ID_FIELD` (id) to exist on the object.
    refresh = RefreshToken.for_user(customer)  # type: ignore[type-var]
    refresh[ACTOR_TYPE_CLAIM] = CUSTOMER_ACTOR_TYPE
    refresh.access_token[ACTOR_TYPE_CLAIM] = CUSTOMER_ACTOR_TYPE
    return customer, refresh
