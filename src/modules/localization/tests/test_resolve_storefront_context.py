"""Locale and Transaction Currency resolution for a Storefront read.

The precedence table is the whole point of this module, so it is tested
as a table. Before this existed the same rule lived, differently, in three
places and could only be exercised through an HTTP round-trip per view.
"""

from typing import cast

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from modules.accounts.models import Customer
from modules.accounts.tests.factories import CustomerFactory
from modules.localization.errors import (
    SupportedCountryNotConfiguredError,
    UnsupportedCurrencyError,
    UnsupportedLocaleError,
)
from modules.localization.services.resolve_storefront_context import resolve_storefront_context
from modules.localization.tests.factories import SupportedCountryFactory


def _request(query: str = "", *, accept_language: str = "", user=None):
    request = RequestFactory().get(f"/?{query}", HTTP_ACCEPT_LANGUAGE=accept_language)
    request.user = user if user is not None else AnonymousUser()
    return request


@pytest.fixture
def country():
    return SupportedCountryFactory()


# --- locale precedence, most explicit first ----------------------------


@pytest.mark.django_db
def test_query_param_wins_over_everything(country) -> None:
    customer = CustomerFactory(preferred_locale="vi")

    context = resolve_storefront_context(_request("locale=en", accept_language="vi", user=customer))

    assert context.locale == "en"


@pytest.mark.django_db
def test_customer_preference_wins_over_accept_language(country) -> None:
    customer = CustomerFactory(preferred_locale="en")

    context = resolve_storefront_context(_request(accept_language="vi", user=customer))

    assert context.locale == "en"


@pytest.mark.django_db
def test_accept_language_is_used_when_no_preference_is_stored(country) -> None:
    context = resolve_storefront_context(_request(accept_language="en-US,en;q=0.9"))

    assert context.locale == "en"


@pytest.mark.django_db
def test_country_default_is_the_last_resort(country) -> None:
    context = resolve_storefront_context(_request(accept_language="fr-FR,fr;q=0.9"))

    assert context.locale == country.default_locale == "vi"


@pytest.mark.django_db
def test_a_customer_with_a_blank_preference_falls_through(country) -> None:
    """`preferred_locale` is blank until the Customer has chosen one."""
    customer = CustomerFactory(preferred_locale="")

    context = resolve_storefront_context(_request(accept_language="en", user=customer))

    assert context.locale == "en"


# --- currency precedence -----------------------------------------------


@pytest.mark.django_db
def test_currency_param_wins_over_a_stored_preference(country) -> None:
    customer = CustomerFactory(preferred_currency="USD")

    context = resolve_storefront_context(_request("currency=VND", user=customer))

    assert context.currency == "VND"


@pytest.mark.django_db
def test_stored_currency_preference_is_finally_honoured(country) -> None:
    """Accounts has recorded this since Slice 1; no Storefront read used it
    until this module existed."""
    customer = CustomerFactory(preferred_currency="USD")

    context = resolve_storefront_context(_request(user=customer))

    assert context.currency == "USD"


@pytest.mark.django_db
def test_accept_language_has_no_say_over_currency(country) -> None:
    context = resolve_storefront_context(_request(accept_language="en-US,en;q=0.9"))

    assert context.currency == country.allowed_currencies[0] == "VND"


# --- refusals ----------------------------------------------------------


@pytest.mark.django_db
def test_locale_outside_the_supported_country_is_refused(country) -> None:
    with pytest.raises(UnsupportedLocaleError):
        resolve_storefront_context(_request("locale=fr"))


@pytest.mark.django_db
def test_currency_outside_the_supported_country_is_refused(country) -> None:
    with pytest.raises(UnsupportedCurrencyError):
        resolve_storefront_context(_request("currency=EUR"))


@pytest.mark.django_db
def test_no_configured_country_is_a_503_not_a_guess() -> None:
    """A Storefront with no Supported Country cannot serve correctly, so it
    says so rather than serving a guessed locale."""
    with pytest.raises(SupportedCountryNotConfiguredError):
        resolve_storefront_context(_request())


# --- invariants --------------------------------------------------------


@pytest.mark.django_db
def test_reading_a_preference_never_writes_one_back(country) -> None:
    """Changing a preference is a deliberate act through the Accounts API.
    A GET must not quietly rewrite the Customer's profile."""
    # factory_boy's return type isn't the model; cast, as accounts' own
    # factories module already does.
    customer = cast(Customer, CustomerFactory(preferred_locale="vi", preferred_currency="VND"))

    resolve_storefront_context(_request("locale=en&currency=USD", user=customer))

    customer.refresh_from_db()
    assert customer.preferred_locale == "vi"
    assert customer.preferred_currency == "VND"


@pytest.mark.django_db
def test_the_supported_country_row_is_read_once(django_assert_num_queries, country) -> None:
    """Resolving and validating share one read; composing them naively
    would cost two queries on every Storefront request."""
    with django_assert_num_queries(1):
        resolve_storefront_context(_request("locale=en&currency=USD"))
