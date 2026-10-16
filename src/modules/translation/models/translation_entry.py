"""TranslationEntry — guild.md §15 Slice 2, commit 4. One row per
(entity, locale, field): Product/Category/Brand/Attribute/SEO content is
stored here, never as fixed `name_vi`/`name_en` columns on the entity
itself, so adding a locale is a data change, not a schema migration
(guild.md §15 / Issue #7 story "no `name_vi`/`name_en` columns").

`is_ai_generated` drafts start unapproved (`is_approved=False`) and stay
invisible on the Storefront until a Store Manager calls
`services/approve_translation.py` — regardless of source, storing and
approving a translation is this slice's job; generating one via AI is
out of scope (Issue #7).
"""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from common.db.models import BaseModel


class TranslationEntry(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    entity = GenericForeignKey("content_type", "object_id")

    locale = models.CharField(max_length=10)
    field = models.CharField(max_length=50)
    value = models.TextField()

    is_ai_generated = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)

    class Meta:
        db_table = "translation_entry"
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "locale", "field"],
                name="unique_translation_entry_per_field_locale",
            ),
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id", "locale"]),
        ]

    def __str__(self) -> str:
        return f"{self.content_type}:{self.object_id}:{self.locale}:{self.field}"
