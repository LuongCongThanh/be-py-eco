"""Staff password login — shorter-lived JWTs than Customer's (guild.md
§6.1). No revocable Session row yet (unlike Customer's — commit 7); that
infrastructure isn't required by this commit's verify criterion.
"""

from __future__ import annotations

from django.contrib.auth.hashers import check_password

from common.auth.authentication import (
    ACTOR_TYPE_CLAIM,
    STAFF_ACTOR_TYPE,
    StaffRefreshToken,
)
from modules.accounts.errors import InvalidCredentialsError
from modules.accounts.models import Staff


def login_staff(*, email: str, password: str) -> tuple[Staff, str, str]:
    """Returns `(staff, access_token, refresh_token)`."""
    try:
        staff = Staff.objects.get(email=email.strip().lower(), is_active=True)
    except Staff.DoesNotExist:
        raise InvalidCredentialsError from None

    if not check_password(password, staff.password_hash):
        raise InvalidCredentialsError

    # Staff isn't AbstractBaseUser by design (see models/staff.py); for_user()
    # only needs `USER_ID_FIELD` (id) to exist on the object.
    refresh = StaffRefreshToken.for_user(staff)  # type: ignore[type-var]
    refresh[ACTOR_TYPE_CLAIM] = STAFF_ACTOR_TYPE
    refresh.access_token[ACTOR_TYPE_CLAIM] = STAFF_ACTOR_TYPE
    return staff, str(refresh.access_token), str(refresh)
