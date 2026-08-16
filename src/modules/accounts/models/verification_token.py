"""VerificationToken — single-use, hashed, expiring token backing email
verification (this commit), password reset and email change (both reuse
this same mechanism in a later commit — see Issue #6 commit 9).
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel
from modules.accounts.models.customer import Customer


class VerificationToken(BaseModel):
    class Purpose(models.TextChoices):
        EMAIL_VERIFICATION = "email_verification", "Email verification"
        PASSWORD_RESET = "password_reset", "Password reset"
        EMAIL_CHANGE = "email_change", "Email change"

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="verification_tokens"
    )
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    # Only the hash is stored — the raw token is returned once, to be emailed.
    token_hash = models.CharField(max_length=64, unique=True)
    new_email = models.EmailField(blank=True)  # only used by EMAIL_CHANGE
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_verification_token"

    def __str__(self) -> str:
        return f"{self.customer_id}:{self.purpose}"
