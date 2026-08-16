import pytest

from modules.localization.errors import UnsupportedCurrencyError, UnsupportedLocaleError
from modules.localization.services.validate_preference import validate_locale_and_currency
from modules.localization.tests.factories import SupportedCountryFactory


@pytest.mark.django_db
def test_validate_locale_and_currency_accepts_allowed_values() -> None:
    SupportedCountryFactory()

    country = validate_locale_and_currency(locale="en", currency="USD")

    assert str(country.code) == "VN"


@pytest.mark.django_db
def test_validate_locale_and_currency_rejects_unsupported_locale() -> None:
    SupportedCountryFactory()

    with pytest.raises(UnsupportedLocaleError):
        validate_locale_and_currency(locale="fr", currency="VND")


@pytest.mark.django_db
def test_validate_locale_and_currency_rejects_unsupported_currency() -> None:
    SupportedCountryFactory()

    with pytest.raises(UnsupportedCurrencyError):
        validate_locale_and_currency(locale="vi", currency="EUR")
