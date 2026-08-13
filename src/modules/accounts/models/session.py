"""Session — one issued refresh token. Only a hash of it is stored
(guild.md §6.1); the raw refresh token is returned to the client once and
never persisted in recoverable form.
"""

from __future__ import annotations

from django.db import models
from django.utils import timezone

from common.db.models import BaseModel
from modules.accounts.models.customer import Customer


class Session(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="sessions")
    refresh_token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_session"

    def __str__(self) -> str:
        return f"{self.customer_id}:{self.id}"

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > timezone.now()
