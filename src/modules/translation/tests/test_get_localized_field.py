import pytest

from modules.catalog.models import Product
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product
from modules.translation.selectors.get_localized_field import get_localized_field
from modules.translation.services.set_translation import set_translation


def _make_product() -> Product:
    category = create_category()
    return create_product(primary_category=category)


@pytest.mark.django_db
def test_returns_requested_locale_when_present() -> None:
    product = _make_product()
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    set_translation(entity=product, locale="en", field="name", value="T-shirt")

    result = get_localized_field(product, field="name", locale="en", default_locale="vi")

    assert result.value == "T-shirt"
    assert result.locale == "en"
    assert result.is_fallback is False


@pytest.mark.django_db
def test_falls_back_to_default_locale_when_requested_locale_missing() -> None:
    product = _make_product()
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")

    result = get_localized_field(product, field="name", locale="en", default_locale="vi")

    assert result.value == "Áo thun"
    assert result.locale == "vi"
    assert result.is_fallback is True


@pytest.mark.django_db
def test_unapproved_translation_is_not_returned() -> None:
    product = _make_product()
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    set_translation(
        entity=product, locale="en", field="name", value="Draft", is_ai_generated=True
    )

    result = get_localized_field(product, field="name", locale="en", default_locale="vi")

    assert result.value == "Áo thun"
    assert result.is_fallback is True


@pytest.mark.django_db
def test_no_content_in_any_locale_returns_none_flagged_as_fallback() -> None:
    product = _make_product()

    result = get_localized_field(product, field="name", locale="en", default_locale="vi")

    assert result.value is None
    assert result.is_fallback is True
