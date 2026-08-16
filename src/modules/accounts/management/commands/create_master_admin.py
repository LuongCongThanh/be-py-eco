"""Bootstrap the very first Master Admin (guild.md §14.1: no default
user/password in production, so this reads credentials from the caller
rather than hardcoding anything). Deliberately not idempotent — creating a
Staff account is a one-time operational action, not a re-runnable seed
like localization's seed_supported_countries.
"""

from __future__ import annotations

import getpass
from typing import Any

from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from modules.accounts.models import Staff


class Command(BaseCommand):
    help = "Bootstrap the first Master Admin. Prompts for a password if --password isn't given."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", default=None, help="Omit to be prompted (recommended).")

    def handle(self, *args: Any, **options: Any) -> None:
        email = options["email"].strip().lower()
        if Staff.objects.filter(email=email).exists():
            raise CommandError(f"A Staff account already exists for {email}.")

        password = options["password"] or getpass.getpass("Password: ")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("\n".join(exc.messages)) from exc

        staff = Staff.objects.create(
            email=email, password_hash=make_password(password), role=Staff.Role.MASTER_ADMIN
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created Master Admin {staff.email}. They must still set up MFA via "
                "POST /api/v1/admin/staff/mfa/setup and /confirm before they can call any "
                "sensitive action (guild.md §3.1)."
            )
        )
