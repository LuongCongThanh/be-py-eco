"""Master Admin creates a Staff account with an assigned role (guild.md
§2.2, Issue #6 commit 11) — a sensitive action (guild.md §6.2), audited.
"""

from __future__ import annotations

from django.contrib.auth.hashers import make_password

from common.auth.permissions import check_policy
from modules.accounts.errors import InsufficientPermissionError
from modules.accounts.models import Staff
from modules.accounts.services.mfa import require_confirmed_mfa
from modules.audit.services.write_audit_log import write_audit_log

CREATE_STAFF_CODENAME = "accounts.create_staff"


def create_staff(*, actor: Staff, email: str, password: str, role: str) -> Staff:
    if not check_policy(role=actor.role, codename=CREATE_STAFF_CODENAME):
        raise InsufficientPermissionError
    require_confirmed_mfa(actor)

    staff = Staff.objects.create(
        email=email.strip().lower(),
        password_hash=make_password(password),
        role=role,
    )

    write_audit_log(
        actor_type="staff",
        actor_id=str(actor.id),
        action="accounts.create_staff",
        resource_type="staff",
        resource_id=str(staff.id),
        before={},
        after={"email": staff.email, "role": staff.role},
    )
    return staff
