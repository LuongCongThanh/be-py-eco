"""LoginMethod — one way a Customer can authenticate; multiple methods can
link to the same Customer (guild.md §3.1). Google-specific fields land in
the commit that adds Google login.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel
from modules.accounts.models.customer import Customer


class LoginMethod(BaseModel):
    class Provider(models.TextChoices):
        PASSWORD = "password", "Password"
        GOOGLE = "google", "Google"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="login_methods")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    password_hash = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "accounts_login_method"
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "provider"], name="unique_customer_login_method_provider"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.customer_id}:{self.provider}"
