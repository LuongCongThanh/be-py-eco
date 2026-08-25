"""Validates a manually-chosen locale/currency against the active
Supported Country's configuration (guild.md §3.2).

Split in two so a caller that has already loaded the country — as
`resolve_storefront_context` does on every Storefront read — can validate
without a second query for the same row.
"""

from __future__ import annotations

from modules.localization.errors import (
    SupportedCountryNotConfiguredError,
    UnsupportedCurrencyError,
    UnsupportedLocaleError,
)
from modules.localization.models import SupportedCountry


def active_supported_country() -> SupportedCountry:
    country = SupportedCountry.objects.filter(is_active=True).first()
    if country is None:
        raise SupportedCountryNotConfiguredError
    return country


def validate_against_country(*, country: SupportedCountry, locale: str, currency: str) -> None:
    if locale not in country.allowed_locales:
        raise UnsupportedLocaleError
    if currency not in country.allowed_currencies:
        raise UnsupportedCurrencyError


def validate_locale_and_currency(*, locale: str, currency: str) -> SupportedCountry:
    country = active_supported_country()
    validate_against_country(country=country, locale=locale, currency=currency)
    return country
