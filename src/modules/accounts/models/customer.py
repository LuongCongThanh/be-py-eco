"""Customer — CONTEXT.md: "A registered person who can place and review
orders."

Deliberately not Django's `AUTH_USER_MODEL`/`AbstractUser`: Customer and
Staff (modules/accounts/models/staff.py, added in a later commit) are
distinct actor kinds with different auth flows (password/Google vs.
mandatory MFA). Both are authenticated through this module's own JWT
machinery rather than django.contrib.auth's session/User plumbing, so
`Staff.role` never has an `is_superuser` to be confused with (guild.md §2.1).
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel


class Customer(BaseModel):
    email = models.EmailField(unique=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounts_customer"

    def __str__(self) -> str:
        return self.email

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None
