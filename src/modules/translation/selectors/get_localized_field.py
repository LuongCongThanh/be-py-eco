"""Read a single translated field with default-locale fallback —
guild.md §15 Slice 2, commit 5. A Customer must never see a blank page
because one locale is missing content (Issue #7 story); a Store Manager
must be able to see, in the Admin API, which fields are only showing
fallback content and still need localizing.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import models

from modules.translation.selectors.entries_for_entity import entries_for_entity


@dataclass(frozen=True)
class LocalizedField:
    value: str | None
    locale: str | None
    is_fallback: bool


def get_localized_field(
    entity: models.Model,
    *,
    field: str,
    locale: str,
    default_locale: str,
) -> LocalizedField:
    entries = entries_for_entity(entity).filter(field=field, is_approved=True)

    requested = next((entry for entry in entries if entry.locale == locale), None)
    if requested is not None:
        return LocalizedField(value=requested.value, locale=locale, is_fallback=False)

    if locale != default_locale:
        fallback = next((entry for entry in entries if entry.locale == default_locale), None)
        if fallback is not None:
            return LocalizedField(value=fallback.value, locale=default_locale, is_fallback=True)

    return LocalizedField(value=None, locale=None, is_fallback=True)
