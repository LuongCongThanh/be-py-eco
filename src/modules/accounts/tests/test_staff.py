from typing import cast

import pytest
from django.db import IntegrityError

from modules.accounts.errors import InsufficientPermissionError
from modules.accounts.models import Staff
from modules.accounts.services.create_staff import create_staff
from modules.accounts.tests.factories import StaffFactory


@pytest.mark.django_db
def test_create_staff_by_master_admin_succeeds() -> None:
    admin = cast(Staff, StaffFactory(role=Staff.Role.MASTER_ADMIN))

    staff = create_staff(
        actor=admin,
        email="Newstaff@Example.com",
        password="a-strong-password-123",
        role=Staff.Role.STORE_MANAGER,
    )

    assert staff.email == "newstaff@example.com"
    assert staff.role == Staff.Role.STORE_MANAGER
    assert staff.has_confirmed_mfa is False


@pytest.mark.django_db
def test_create_staff_by_non_master_admin_is_denied() -> None:
    manager = cast(Staff, StaffFactory(role=Staff.Role.STORE_MANAGER))

    with pytest.raises(InsufficientPermissionError):
        create_staff(
            actor=manager,
            email="x@example.com",
            password="a-strong-password-123",
            role=Staff.Role.ORDER_STAFF,
        )


@pytest.mark.django_db
def test_staff_email_is_unique() -> None:
    StaffFactory(email="dup@example.com")

    with pytest.raises(IntegrityError):
        StaffFactory(email="dup@example.com")
