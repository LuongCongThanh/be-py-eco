"""Validates a manually-chosen locale/currency against the active
Supported Country's configuration (guild.md §3.2).
"""

from __future__ import annotations

from modules.localization.errors import (
    SupportedCountryNotConfiguredError,
    UnsupportedCurrencyError,
    UnsupportedLocaleError,
)
from modules.localization.models import SupportedCountry


def validate_locale_and_currency(*, locale: str, currency: str) -> SupportedCountry:
    country = SupportedCountry.objects.filter(is_active=True).first()
    if country is None:
        raise SupportedCountryNotConfiguredError
    if locale not in country.allowed_locales:
        raise UnsupportedLocaleError
    if currency not in country.allowed_currencies:
        raise UnsupportedCurrencyError
    return country
