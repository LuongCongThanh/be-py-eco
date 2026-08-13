"""First-visit locale/currency suggestion (guild.md §3.2). Country is fixed
to the single active Supported Country until multi-country support (Slice
11); language is derived from the browser's `Accept-Language` header.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.http import HttpRequest

from modules.localization.errors import SupportedCountryNotConfiguredError
from modules.localization.models import SupportedCountry


@dataclass(frozen=True)
class LocaleSuggestion:
    country_code: str
    locale: str
    currency: str


def suggest_locale(request: HttpRequest) -> LocaleSuggestion:
    country = SupportedCountry.objects.filter(is_active=True).first()
    if country is None:
        raise SupportedCountryNotConfiguredError

    locale = _best_locale_match(request, country.allowed_locales) or country.default_locale
    return LocaleSuggestion(
        country_code=str(country.code), locale=locale, currency=country.allowed_currencies[0]
    )


def _best_locale_match(request: HttpRequest, allowed_locales: list[str]) -> str | None:
    accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for part in accept_language.split(","):
        lang = part.split(";")[0].strip().split("-")[0].lower()
        if lang in allowed_locales:
            return lang
    return None
