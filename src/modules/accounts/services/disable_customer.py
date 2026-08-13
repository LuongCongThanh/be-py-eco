"""Customer disable — one of guild.md §6.2's canonical sensitive actions:
permission AND a confirmed MFA device required, audited.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from common.auth.permissions import check_policy
from common.observability.request_context import client_ip, request_id
from modules.accounts.errors import (
    InsufficientPermissionError,
    MfaNotConfiguredError,
    ReasonRequiredError,
)
from modules.accounts.models import Customer, Staff
from modules.accounts.services.sessions import revoke_all_sessions
from modules.audit.services.write_audit_log import write_audit_log

DISABLE_CUSTOMER_CODENAME = "accounts.disable_customer"


def disable_customer(
    *, actor: Staff, customer_id: UUID, reason: str, request: Any = None
) -> Customer:
    if not check_policy(role=actor.role, codename=DISABLE_CUSTOMER_CODENAME):
        raise InsufficientPermissionError
    if not actor.has_confirmed_mfa:
        raise MfaNotConfiguredError
    if not reason.strip():
        raise ReasonRequiredError

    customer = Customer.objects.get(id=customer_id)
    customer.is_active = False
    customer.save(update_fields=["is_active"])
    revoke_all_sessions(customer=customer)

    write_audit_log(
        actor_type="staff",
        actor_id=str(actor.id),
        action="accounts.disable_customer",
        resource_type="customer",
        resource_id=str(customer.id),
        before={"is_active": True},
        after={"is_active": False},
        reason=reason.strip(),
        ip_address=client_ip(request),
        request_id=request_id(request),
    )
    return customer
