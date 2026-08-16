"""Staff — Master Admin, Store Manager, Order Staff (guild.md §2). `role` is
an explicit business field, never Django's `is_superuser`/`is_staff`
(guild.md §2.1) — permission checks go through common/auth/permissions.py.

Deliberately not Django's `AUTH_USER_MODEL` either, for the same reason as
Customer (see customer.py): authenticated via this module's own JWT
machinery.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel


class Staff(BaseModel):
    class Role(models.TextChoices):
        MASTER_ADMIN = "master_admin", "Master Admin"
        STORE_MANAGER = "store_manager", "Store Manager"
        ORDER_STAFF = "order_staff", "Order Staff"

    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounts_staff"

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    # Minimal shim for DRF's IsAuthenticated permission (see Customer).
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def has_confirmed_mfa(self) -> bool:
        return hasattr(self, "totp_device") and self.totp_device.is_confirmed
