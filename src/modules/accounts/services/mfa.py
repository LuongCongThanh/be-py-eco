"""Staff MFA setup/confirmation — mandatory before any sensitive action
(guild.md §3.1, §6.1, Issue #6 commit 11).
"""

from __future__ import annotations

import base64
from typing import Any

from django.utils import timezone

from common.auth.permissions import check_policy
from common.observability.request_context import client_ip, request_id
from modules.accounts.errors import (
    InsufficientPermissionError,
    InvalidMfaTokenError,
    MfaNotConfiguredError,
)
from modules.accounts.models import Staff, StaffTOTPDevice
from modules.audit.services.write_audit_log import write_audit_log

RESET_STAFF_MFA_CODENAME = "accounts.reset_staff_mfa"


def require_confirmed_mfa(staff: Staff) -> None:
    """Guards every sensitive action (guild.md §3.1 "MFA bắt buộc cho mọi
    staff"; §6.2: a staff account without MFA configured cannot
    successfully call a sensitive action endpoint)."""
    if not staff.has_confirmed_mfa:
        raise MfaNotConfiguredError


def start_mfa_setup(*, staff: Staff) -> tuple[StaffTOTPDevice, str]:
    """Returns `(device, provisioning_uri)`. Idempotent: re-running before
    confirmation returns the same unconfirmed device rather than a new key.
    """
    device, _ = StaffTOTPDevice.objects.get_or_create(staff=staff)
    return device, _provisioning_uri(device)


def confirm_mfa_setup(*, staff: Staff, token: str) -> StaffTOTPDevice:
    try:
        device = staff.totp_device
    except StaffTOTPDevice.DoesNotExist:
        raise InvalidMfaTokenError from None

    if not device.verify_token(token):
        raise InvalidMfaTokenError

    device.confirmed_at = timezone.now()
    device.save(update_fields=["confirmed_at"])
    return device


def reset_staff_mfa(*, actor: Staff, target_staff: Staff, request: Any = None) -> None:
    """Master Admin resets a Staff's MFA device (e.g. a lost device),
    forcing re-enrollment. A sensitive action (guild.md §6.2) — audited.
    """
    if not check_policy(role=actor.role, codename=RESET_STAFF_MFA_CODENAME):
        raise InsufficientPermissionError
    require_confirmed_mfa(actor)

    had_confirmed_mfa = target_staff.has_confirmed_mfa
    StaffTOTPDevice.objects.filter(staff=target_staff).delete()

    write_audit_log(
        actor_type="staff",
        actor_id=str(actor.id),
        action="accounts.reset_staff_mfa",
        resource_type="staff",
        resource_id=str(target_staff.id),
        before={"mfa_confirmed": had_confirmed_mfa},
        after={"mfa_confirmed": False},
        ip_address=client_ip(request),
        request_id=request_id(request),
    )


def _provisioning_uri(device: StaffTOTPDevice, issuer: str = "be-py-eco") -> str:
    secret = base64.b32encode(device.bin_key).decode().rstrip("=")
    return f"otpauth://totp/{issuer}:{device.staff.email}?secret={secret}&issuer={issuer}"
