"""Master Admin creates a Staff account with an assigned role (guild.md
§2.2, Issue #6 commit 11).
"""

from __future__ import annotations

from django.contrib.auth.hashers import make_password

from common.auth.permissions import check_policy
from modules.accounts.errors import InsufficientPermissionError
from modules.accounts.models import Staff

CREATE_STAFF_CODENAME = "accounts.create_staff"


def create_staff(*, actor: Staff, email: str, password: str, role: str) -> Staff:
    if not check_policy(role=actor.role, codename=CREATE_STAFF_CODENAME):
        raise InsufficientPermissionError

    return Staff.objects.create(
        email=email.strip().lower(),
        password_hash=make_password(password),
        role=role,
    )
