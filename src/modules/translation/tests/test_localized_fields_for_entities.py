"""localized_fields_for_entities — the batched form of
`get_localized_field`, which must agree with it case for case while
costing one query instead of N.
"""

import pytest

from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product
from modules.translation.selectors.get_localized_field import get_localized_field
from modules.translation.selectors.localized_fields_for_entities import (
    localized_fields_for_entities,
)
from modules.translation.services.set_translation import set_translation


def _resolve(entities, locale="en"):
    return localized_fields_for_entities(entities, field="name", locale=locale, default_locale="vi")


@pytest.mark.django_db
def test_one_query_regardless_of_how_many_entities(django_assert_num_queries) -> None:
    """The whole reason this exists. ContentType is cached by
    get_for_model, so the entry lookup is the only query."""
    category = create_category()
    products = [create_product(primary_category=category) for _ in range(10)]
    for product in products:
        set_translation(entity=product, locale="en", field="name", value="T-shirt")

    with django_assert_num_queries(1):
        _resolve(products)


@pytest.mark.django_db
def test_it_agrees_with_the_single_entity_selector() -> None:
    """Two implementations of one rule must not drift; this is the check
    that they have not."""
    category = create_category()
    translated = create_product(primary_category=category)
    fallback_only = create_product(primary_category=category)
    untranslated = create_product(primary_category=category)
    set_translation(entity=translated, locale="en", field="name", value="T-shirt")
    set_translation(entity=translated, locale="vi", field="name", value="Áo thun")
    set_translation(entity=fallback_only, locale="vi", field="name", value="Áo thun")

    products = [translated, fallback_only, untranslated]
    batched = _resolve(products)

    for product in products:
        assert batched[product.pk] == get_localized_field(
            product, field="name", locale="en", default_locale="vi"
        )


@pytest.mark.django_db
def test_missing_locale_falls_back_and_is_flagged() -> None:
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")

    resolved = _resolve([product])[product.pk]

    assert (resolved.value, resolved.locale, resolved.is_fallback) == ("Áo thun", "vi", True)


@pytest.mark.django_db
def test_unapproved_translations_stay_invisible() -> None:
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="en", field="name", value="Draft", is_ai_generated=True)

    resolved = _resolve([product])[product.pk]

    assert resolved.value is None


@pytest.mark.django_db
def test_no_entities_needs_no_query(django_assert_num_queries) -> None:
    with django_assert_num_queries(0):
        assert _resolve([]) == {}
