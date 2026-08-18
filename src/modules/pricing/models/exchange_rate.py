"""ExchangeRate — guild.md §15 Slice 3, commit 8. Synced periodically
(Celery Beat, `services/sync_exchange_rates.py`) into PostgreSQL, never
fetched inline on a catalog read (commit 12's regression test enforces
this). `rate` is a high-precision `DecimalField` — never a JSON float,
per guild.md §10.3.
"""

from __future__ import annotations

from django.db import models
from django.utils import timezone

from common.db.models import BaseModel


class ExchangeRate(BaseModel):
    base_currency = models.CharField(max_length=3)
    target_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=20, decimal_places=10)
    source = models.CharField(max_length=100)
    fetched_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "pricing_exchange_rate"
        constraints = [
            models.UniqueConstraint(
                fields=["base_currency", "target_currency", "fetched_at"],
                name="unique_exchange_rate_snapshot",
            ),
        ]
        indexes = [
            models.Index(fields=["base_currency", "target_currency", "-fetched_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.base_currency}->{self.target_currency}@{self.fetched_at.isoformat()}"

    @property
    def is_stale(self) -> bool:
        return timezone.now() >= self.expires_at
