"""Persist a Customer's manually-chosen locale/currency, overriding the
first-visit suggestion (guild.md §3.2).
"""

from __future__ import annotations

from modules.accounts.models import Customer
from modules.localization.services.validate_preference import validate_locale_and_currency


def update_locale_preference(*, customer: Customer, locale: str, currency: str) -> Customer:
    validate_locale_and_currency(locale=locale, currency=currency)
    customer.preferred_locale = locale
    customer.preferred_currency = currency
    customer.save(update_fields=["preferred_locale", "preferred_currency"])
    return customer
