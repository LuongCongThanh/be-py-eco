"""Look up TranslationEntry rows for a given entity. Deliberately a plain
ContentType/object_id query rather than a `GenericRelation` declared on
each translatable model — that would make `catalog` (and every other
translated module) depend back on `translation`, inverting the
dependency direction the directory structure in Issue #7 establishes
(translation depends on catalog, not the other way around).
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import QuerySet

from modules.translation.models.translation_entry import TranslationEntry


def entries_for_entity(entity: models.Model) -> QuerySet[TranslationEntry]:
    content_type = ContentType.objects.get_for_model(entity)
    return TranslationEntry.objects.filter(content_type=content_type, object_id=entity.pk)
