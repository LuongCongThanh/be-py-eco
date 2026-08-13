from binascii import unhexlify
from typing import cast

import pytest
from django_otp.oath import totp

from modules.accounts.errors import InsufficientPermissionError, MfaNotConfiguredError
from modules.accounts.models import Staff
from modules.accounts.services.disable_customer import disable_customer
from modules.accounts.services.mfa import confirm_mfa_setup, start_mfa_setup
from modules.accounts.services.register_customer import register_customer
from modules.accounts.tests.factories import StaffFactory
from modules.audit.models import AuditLogEntry


def _confirm_mfa(staff: Staff) -> None:
    device, _ = start_mfa_setup(staff=staff)
    code = str(totp(unhexlify(device.key))).zfill(6)
    confirm_mfa_setup(staff=staff, token=code)


@pytest.mark.django_db
def test_disable_customer_blocked_until_mfa_is_set_up() -> None:
    manager = cast(Staff, StaffFactory(role=Staff.Role.STORE_MANAGER))
    result = register_customer(email="blocked@example.com", password="a-strong-password-123")

    with pytest.raises(MfaNotConfiguredError):
        disable_customer(actor=manager, customer_id=result.customer.id)


@pytest.mark.django_db
def test_disable_customer_succeeds_once_mfa_is_confirmed() -> None:
    manager = cast(Staff, StaffFactory(role=Staff.Role.STORE_MANAGER))
    _confirm_mfa(manager)
    result = register_customer(email="unblocked@example.com", password="a-strong-password-123")

    customer = disable_customer(actor=manager, customer_id=result.customer.id)

    assert customer.is_active is False
    entry = AuditLogEntry.objects.get(
        action="accounts.disable_customer", resource_id=str(customer.id)
    )
    assert entry.actor_type == "staff"
    assert entry.actor_id == str(manager.id)


@pytest.mark.django_db
def test_disable_customer_denied_for_order_staff_even_with_mfa() -> None:
    order_staff = cast(Staff, StaffFactory(role=Staff.Role.ORDER_STAFF))
    _confirm_mfa(order_staff)
    result = register_customer(email="orderstaffcant@example.com", password="a-strong-password-123")

    with pytest.raises(InsufficientPermissionError):
        disable_customer(actor=order_staff, customer_id=result.customer.id)
