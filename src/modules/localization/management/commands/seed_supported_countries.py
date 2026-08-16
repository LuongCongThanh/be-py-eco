"""Idempotent seed for the baseline Supported Country (guild.md §14.1).

Vietnam is the only launch entry — vi/en locales, VND + USD allowed.
Safe to re-run: `get_or_create` never duplicates the row.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from modules.localization.models import SupportedCountry


class Command(BaseCommand):
    help = "Seed the baseline Supported Country (Vietnam). Idempotent."

    def handle(self, *args: Any, **options: Any) -> None:
        _, created = SupportedCountry.objects.get_or_create(
            code="VN",
            defaults={
                "name": "Vietnam",
                "default_locale": "vi",
                "allowed_locales": ["vi", "en"],
                "allowed_currencies": ["VND", "USD"],
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created Supported Country: Vietnam"))
        else:
            self.stdout.write("Supported Country already exists: Vietnam")
