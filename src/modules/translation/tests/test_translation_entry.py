import uuid

import pytest

from modules.catalog.models import Product
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product
from modules.translation.errors import TranslationEntryNotFoundError
from modules.translation.selectors.entries_for_entity import entries_for_entity
from modules.translation.services.approve_translation import approve_translation
from modules.translation.services.set_translation import set_translation


def _make_product() -> Product:
    category = create_category()
    return create_product(primary_category=category)


@pytest.mark.django_db
def test_product_has_no_fixed_locale_columns() -> None:
    field_names = {field.name for field in Product._meta.get_fields()}

    assert "name_vi" not in field_names
    assert "name_en" not in field_names


@pytest.mark.django_db
def test_stores_vi_and_en_content_for_one_product() -> None:
    product = _make_product()

    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    set_translation(entity=product, locale="en", field="name", value="T-shirt")

    vi = entries_for_entity(product).get(locale="vi", field="name")
    en = entries_for_entity(product).get(locale="en", field="name")
    assert vi.value == "Áo thun"
    assert en.value == "T-shirt"


@pytest.mark.django_db
def test_human_authored_translation_is_approved_immediately() -> None:
    product = _make_product()

    entry = set_translation(entity=product, locale="en", field="name", value="T-shirt")

    assert entry.is_approved is True
    assert entry.is_ai_generated is False


@pytest.mark.django_db
def test_ai_generated_translation_starts_unapproved() -> None:
    product = _make_product()

    entry = set_translation(
        entity=product,
        locale="en",
        field="name",
        value="T-shirt (draft)",
        is_ai_generated=True,
    )

    assert entry.is_approved is False


@pytest.mark.django_db
def test_approving_a_draft_makes_it_approved() -> None:
    product = _make_product()
    entry = set_translation(
        entity=product,
        locale="en",
        field="name",
        value="T-shirt (draft)",
        is_ai_generated=True,
    )

    approved = approve_translation(entry_id=entry.id)

    assert approved.is_approved is True


@pytest.mark.django_db
def test_approving_a_missing_entry_raises() -> None:
    with pytest.raises(TranslationEntryNotFoundError):
        approve_translation(entry_id=uuid.uuid4())


@pytest.mark.django_db
def test_setting_translation_twice_updates_the_same_entry() -> None:
    product = _make_product()
    set_translation(entity=product, locale="en", field="name", value="First")

    set_translation(entity=product, locale="en", field="name", value="Second")

    assert entries_for_entity(product).filter(locale="en", field="name").count() == 1
    assert entries_for_entity(product).get(locale="en", field="name").value == "Second"
