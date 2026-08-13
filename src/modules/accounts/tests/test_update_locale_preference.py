import pytest

from modules.accounts.services.register_customer import register_customer
from modules.accounts.services.update_locale_preference import update_locale_preference
from modules.localization.errors import UnsupportedLocaleError
from modules.localization.tests.factories import SupportedCountryFactory


@pytest.mark.django_db
def test_update_locale_preference_persists_the_choice() -> None:
    SupportedCountryFactory()
    result = register_customer(email="localepref@example.com", password="a-strong-password-123")

    customer = update_locale_preference(customer=result.customer, locale="en", currency="USD")

    assert customer.preferred_locale == "en"
    assert customer.preferred_currency == "USD"
    result.customer.refresh_from_db()
    assert result.customer.preferred_locale == "en"


@pytest.mark.django_db
def test_update_locale_preference_rejects_unsupported_locale() -> None:
    SupportedCountryFactory()
    result = register_customer(email="badlocale@example.com", password="a-strong-password-123")

    with pytest.raises(UnsupportedLocaleError):
        update_locale_preference(customer=result.customer, locale="fr", currency="VND")
