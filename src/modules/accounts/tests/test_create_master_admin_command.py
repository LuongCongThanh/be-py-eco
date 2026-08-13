import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from modules.accounts.models import Staff


@pytest.mark.django_db
def test_create_master_admin_creates_a_master_admin_staff() -> None:
    call_command("create_master_admin", email="root@example.com", password="a-strong-password-123")

    staff = Staff.objects.get(email="root@example.com")
    assert staff.role == Staff.Role.MASTER_ADMIN
    assert staff.has_confirmed_mfa is False


@pytest.mark.django_db
def test_create_master_admin_rejects_a_duplicate_email() -> None:
    call_command("create_master_admin", email="dup@example.com", password="a-strong-password-123")

    with pytest.raises(CommandError):
        call_command(
            "create_master_admin", email="dup@example.com", password="a-strong-password-123"
        )


@pytest.mark.django_db
def test_create_master_admin_rejects_a_weak_password() -> None:
    with pytest.raises(CommandError):
        call_command("create_master_admin", email="weak@example.com", password="short")
