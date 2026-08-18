"""Store a per-locale field value for any translatable entity —
guild.md §15 Slice 2, commit 4. Human-authored content is approved
immediately (a Store Manager typing a name has already reviewed it);
AI-generated content is always stored as an unapproved draft, per Issue
#7's "AI-drafted translations require review and approval" story.
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db import models

from modules.translation.models.translation_entry import TranslationEntry


def set_translation(
    *,
    entity: models.Model,
    locale: str,
    field: str,
    value: str,
    is_ai_generated: bool = False,
) -> TranslationEntry:
    content_type = ContentType.objects.get_for_model(entity)
    entry, _created = TranslationEntry.objects.update_or_create(
        content_type=content_type,
        object_id=entity.pk,
        locale=locale,
        field=field,
        defaults={
            "value": value,
            "is_ai_generated": is_ai_generated,
            "is_approved": not is_ai_generated,
        },
    )
    return entry
