"""Staff MFA setup/confirmation — mandatory before any sensitive action
(guild.md §3.1, §6.1, Issue #6 commit 11).
"""

from __future__ import annotations

import base64

from django.utils import timezone

from modules.accounts.errors import InvalidMfaTokenError
from modules.accounts.models import Staff, StaffTOTPDevice


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


def _provisioning_uri(device: StaffTOTPDevice, issuer: str = "be-py-eco") -> str:
    secret = base64.b32encode(device.bin_key).decode().rstrip("=")
    return f"otpauth://totp/{issuer}:{device.staff.email}?secret={secret}&issuer={issuer}"
