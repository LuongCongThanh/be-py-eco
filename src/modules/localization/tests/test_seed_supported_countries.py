import pytest
from django.core.management import call_command

from modules.localization.models import SupportedCountry


@pytest.mark.django_db
def test_seed_is_idempotent_and_creates_exactly_one_vietnam_row() -> None:
    call_command("seed_supported_countries")
    call_command("seed_supported_countries")

    assert SupportedCountry.objects.count() == 1
    vietnam = SupportedCountry.objects.get()
    assert str(vietnam.code) == "VN"
    assert vietnam.default_locale == "vi"
    assert vietnam.allowed_locales == ["vi", "en"]
    assert vietnam.allowed_currencies == ["VND", "USD"]
