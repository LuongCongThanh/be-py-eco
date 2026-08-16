import factory

from modules.localization.models import SupportedCountry


class SupportedCountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupportedCountry

    code = "VN"
    name = "Vietnam"
    default_locale = "vi"
    allowed_locales = ["vi", "en"]
    allowed_currencies = ["VND", "USD"]
    is_active = True
