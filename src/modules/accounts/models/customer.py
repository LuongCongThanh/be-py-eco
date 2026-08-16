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
    # First-visit suggestion the Customer can override (guild.md §3.2);
    # blank until they've either been suggested one or chosen manually.
    preferred_locale = models.CharField(max_length=10, blank=True)
    preferred_currency = models.CharField(max_length=3, blank=True)

    class Meta:
        db_table = "accounts_customer"

    def __str__(self) -> str:
        return self.email

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    # Minimal shim for DRF's IsAuthenticated permission, which expects
    # `request.user.is_authenticated` — Customer isn't AbstractBaseUser.
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False
