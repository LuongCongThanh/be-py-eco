import pytest
from django.test import RequestFactory

from modules.localization.errors import SupportedCountryNotConfiguredError
from modules.localization.services.suggest_locale import suggest_locale
from modules.localization.tests.factories import SupportedCountryFactory


@pytest.mark.django_db
def test_suggest_locale_matches_accept_language_when_supported() -> None:
    SupportedCountryFactory()
    request = RequestFactory().get("/", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9,vi;q=0.8")

    suggestion = suggest_locale(request)

    assert suggestion.country_code == "VN"
    assert suggestion.locale == "en"
    assert suggestion.currency == "VND"


@pytest.mark.django_db
def test_suggest_locale_falls_back_to_default_when_no_match() -> None:
    SupportedCountryFactory()
    request = RequestFactory().get("/", HTTP_ACCEPT_LANGUAGE="fr-FR,fr;q=0.9")

    suggestion = suggest_locale(request)

    assert suggestion.locale == "vi"


@pytest.mark.django_db
def test_suggest_locale_falls_back_to_default_when_no_accept_language_header() -> None:
    SupportedCountryFactory()
    request = RequestFactory().get("/")

    suggestion = suggest_locale(request)

    assert suggestion.locale == "vi"


@pytest.mark.django_db
def test_suggest_locale_raises_when_no_country_is_configured() -> None:
    request = RequestFactory().get("/")

    with pytest.raises(SupportedCountryNotConfiguredError):
        suggest_locale(request)
