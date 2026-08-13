import pytest

from modules.localization.models import SupportedCountry


@pytest.mark.django_db
def test_supported_country_str_is_its_code() -> None:
    country = SupportedCountry.objects.create(
        code="VN",
        name="Vietnam",
        default_locale="vi",
        allowed_locales=["vi", "en"],
        allowed_currencies=["VND", "USD"],
    )

    assert str(country) == "VN"
