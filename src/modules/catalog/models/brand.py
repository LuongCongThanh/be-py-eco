"""Brand — guild.md §15 Slice 2 / CONTEXT.md "Brand". A Brand is only a
commercial identity attached to a Product; the Merchant remains the sole
seller (this is not a marketplace). Presentational content (name,
description) lives in the `translation` module, not on this model.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel


class Brand(BaseModel):
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_brand"

    def __str__(self) -> str:
        return str(self.id)
