"""Read one translated field for many entities in a single query.

`get_localized_field` answers for one entity and queries per call, which is
right for a detail read and wrong inside a loop: a paginated Product
listing called it once per row, so a page of 20 cost 20 queries for what
is one lookup by (content_type, object_id, field).

Same fallback rule as the single-entity selector, deliberately: a Customer
must never see a blank page because one locale is missing content, and the
Admin API must still be able to tell which fields are only showing
fallback content.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db import models

from modules.translation.models.translation_entry import TranslationEntry
from modules.translation.selectors.get_localized_field import LocalizedField


def localized_fields_for_entities(
    entities: Sequence[models.Model],
    *,
    field: str,
    locale: str,
    default_locale: str,
) -> dict[Any, LocalizedField]:
    """Map each entity's pk to its `LocalizedField`.

    Entities must share a model -- the ContentType is taken from the first
    one, which is what lets this be a single query.
    """
    if not entities:
        return {}

    content_type = ContentType.objects.get_for_model(entities[0])
    wanted = {locale, default_locale}
    entries = TranslationEntry.objects.filter(
        content_type=content_type,
        object_id__in=[entity.pk for entity in entities],
        field=field,
        is_approved=True,
        locale__in=wanted,
    ).values_list("object_id", "locale", "value")

    by_entity: dict[Any, dict[str, str]] = {}
    for object_id, entry_locale, value in entries:
        by_entity.setdefault(object_id, {})[entry_locale] = value

    resolved = {}
    for entity in entities:
        values = by_entity.get(entity.pk, {})
        if locale in values:
            resolved[entity.pk] = LocalizedField(
                value=values[locale], locale=locale, is_fallback=False
            )
        elif locale != default_locale and default_locale in values:
            resolved[entity.pk] = LocalizedField(
                value=values[default_locale], locale=default_locale, is_fallback=True
            )
        else:
            resolved[entity.pk] = LocalizedField(value=None, locale=None, is_fallback=True)
    return resolved
