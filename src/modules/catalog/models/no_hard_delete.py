"""No-hard-delete guard — guild.md §15 Slice 2, commit 6. Product/Variant
referenced by an Order must never resolve to nothing, so neither model can
ever be hard-deleted — even though no Order exists until Slice 5, per
Issue #7's Decision Document ("cheaper to build the constraint once, now,
than retrofit it once Order references exist"). Archive (status/flag)
instead; see `services/archive.py`.

Both the instance method and the queryset are overridden so the guard
can't be bypassed by `Model.objects.filter(...).delete()`.
"""

from __future__ import annotations

from typing import Any

from django.db import models

from modules.catalog.errors import HardDeleteNotAllowedError


class NoHardDeleteQuerySet(models.QuerySet):
    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise HardDeleteNotAllowedError()


class NoHardDeleteModel(models.Model):
    objects = NoHardDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise HardDeleteNotAllowedError()
