"""Approve a translation draft — guild.md §15 Slice 2, commit 4. Only an
approved entry is ever surfaced by `selectors/get_translation.py` to the
Storefront; this is the sole way an AI-generated draft becomes visible.
"""

from __future__ import annotations

import uuid

from modules.translation.errors import TranslationEntryNotFoundError
from modules.translation.models.translation_entry import TranslationEntry


def approve_translation(*, entry_id: uuid.UUID) -> TranslationEntry:
    try:
        entry = TranslationEntry.objects.get(pk=entry_id)
    except TranslationEntry.DoesNotExist as exc:
        raise TranslationEntryNotFoundError() from exc

    entry.is_approved = True
    entry.save(update_fields=["is_approved", "updated_at"])
    return entry
