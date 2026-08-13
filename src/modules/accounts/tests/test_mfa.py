from binascii import unhexlify
from typing import cast

import pytest
from django_otp.oath import totp

from modules.accounts.errors import InsufficientPermissionError, InvalidMfaTokenError
from modules.accounts.models import Staff, StaffTOTPDevice
from modules.accounts.services.mfa import confirm_mfa_setup, reset_staff_mfa, start_mfa_setup
from modules.accounts.tests.factories import StaffFactory
from modules.audit.models import AuditLogEntry


def _current_code(device: StaffTOTPDevice) -> str:
    return str(totp(unhexlify(device.key))).zfill(6)


@pytest.mark.django_db
def test_start_mfa_setup_is_idempotent() -> None:
    staff = cast(Staff, StaffFactory())

    device_a, uri_a = start_mfa_setup(staff=staff)
    device_b, uri_b = start_mfa_setup(staff=staff)

    assert device_a.id == device_b.id
    assert uri_a == uri_b
    assert uri_a.startswith("otpauth://totp/")
    assert StaffTOTPDevice.objects.filter(staff=staff).count() == 1


@pytest.mark.django_db
def test_confirm_mfa_setup_with_valid_code_marks_it_confirmed() -> None:
    staff = cast(Staff, StaffFactory())
    device, _ = start_mfa_setup(staff=staff)

    confirm_mfa_setup(staff=staff, token=_current_code(device))

    device.refresh_from_db()
    assert device.is_confirmed is True
    staff.refresh_from_db()
    assert staff.has_confirmed_mfa is True


@pytest.mark.django_db
def test_confirm_mfa_setup_rejects_wrong_code() -> None:
    staff = cast(Staff, StaffFactory())
    start_mfa_setup(staff=staff)

    with pytest.raises(InvalidMfaTokenError):
        confirm_mfa_setup(staff=staff, token="000000")


@pytest.mark.django_db
def test_confirm_mfa_setup_without_a_device_raises() -> None:
    staff = cast(Staff, StaffFactory())

    with pytest.raises(InvalidMfaTokenError):
        confirm_mfa_setup(staff=staff, token="123456")


@pytest.mark.django_db
def test_reset_staff_mfa_deletes_the_device_and_writes_an_audit_log_entry() -> None:
    admin = cast(Staff, StaffFactory(role=Staff.Role.MASTER_ADMIN))
    target = cast(Staff, StaffFactory(role=Staff.Role.ORDER_STAFF))
    device, _ = start_mfa_setup(staff=target)
    confirm_mfa_setup(staff=target, token=_current_code(device))

    reset_staff_mfa(actor=admin, target_staff=target)

    assert StaffTOTPDevice.objects.filter(staff=target).exists() is False
    entry = AuditLogEntry.objects.get(action="accounts.reset_staff_mfa", resource_id=str(target.id))
    assert entry.actor_id == str(admin.id)
    assert entry.before == {"mfa_confirmed": True}
    assert entry.after == {"mfa_confirmed": False}


@pytest.mark.django_db
def test_reset_staff_mfa_denied_for_non_master_admin() -> None:
    manager = cast(Staff, StaffFactory(role=Staff.Role.STORE_MANAGER))
    target = cast(Staff, StaffFactory(role=Staff.Role.ORDER_STAFF))

    with pytest.raises(InsufficientPermissionError):
        reset_staff_mfa(actor=manager, target_staff=target)
