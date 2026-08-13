"""Customer disable — one of guild.md §6.2's canonical sensitive actions:
permission AND a confirmed MFA device required. Audit write lands in a
later commit.
"""

from __future__ import annotations

from uuid import UUID

from common.auth.permissions import check_policy
from modules.accounts.errors import InsufficientPermissionError, MfaNotConfiguredError
from modules.accounts.models import Customer, Staff
from modules.accounts.services.sessions import revoke_all_sessions

DISABLE_CUSTOMER_CODENAME = "accounts.disable_customer"


def disable_customer(*, actor: Staff, customer_id: UUID) -> Customer:
    if not check_policy(role=actor.role, codename=DISABLE_CUSTOMER_CODENAME):
        raise InsufficientPermissionError
    if not actor.has_confirmed_mfa:
        raise MfaNotConfiguredError

    customer = Customer.objects.get(id=customer_id)
    customer.is_active = False
    customer.save(update_fields=["is_active"])
    revoke_all_sessions(customer=customer)
    return customer
