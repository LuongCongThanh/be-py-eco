"""Resolve the locale and Transaction Currency for one Storefront read.

Every Storefront endpoint has to answer the same two questions before it
can do its own job, and before this module each one answered them again:
`catalog` and `search` both carried a byte-identical `_resolve_locale`
over a hardcoded `("vi", "en")`, and both read `?currency=` with no
validation at all. Neither consulted the Customer's stored preference,
even though Accounts has been recording one since Slice 1.

Precedence, most explicit first:

    locale     query param -> Customer.preferred_locale
                           -> Accept-Language -> country.default_locale
    currency   query param -> Customer.preferred_currency
                           -> country.allowed_currencies[0]

An explicit query param is what the Customer is asking for *right now* and
outranks the profile default. Reading a preference never writes one back:
changing it is a deliberate act through the Accounts API, not a side
effect of browsing.

`Accept-Language` says nothing about money, so it takes no part in
resolving the currency.

The Supported Country row is read exactly once and reused for validation,
rather than resolving from it and then re-querying it to validate.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.http import HttpRequest

from modules.localization.services.locale_matching import best_locale_match
from modules.localization.services.validate_preference import (
    active_supported_country,
    validate_against_country,
)


@dataclass(frozen=True)
class StorefrontContext:
    country_code: str
    locale: str
    currency: str


def _preference(request: HttpRequest, field: str) -> str:
    """Read a Customer preference without importing Customer.

    `request.user` is a Customer whenever a valid Customer token was sent
    (common.auth.authentication dispatches on the `actor_type` claim), and
    AnonymousUser otherwise. Duck-typing keeps `localization` free of a
    dependency on `accounts` (ADR-0003); the cost is no static check on
    these two attribute names, which is acceptable while Customer is the
    only actor the Storefront authenticates.
    """
    return str(getattr(getattr(request, "user", None), field, "") or "")


def resolve_storefront_context(request: HttpRequest) -> StorefrontContext:
    country = active_supported_country()
    params = request.GET

    locale = (
        params.get("locale")
        or _preference(request, "preferred_locale")
        or best_locale_match(
            request.META.get("HTTP_ACCEPT_LANGUAGE", ""), list(country.allowed_locales)
        )
        or country.default_locale
    )
    currency = (
        params.get("currency")
        or _preference(request, "preferred_currency")
        or country.allowed_currencies[0]
    )

    validate_against_country(country=country, locale=locale, currency=currency)
    return StorefrontContext(country_code=str(country.code), locale=locale, currency=currency)
