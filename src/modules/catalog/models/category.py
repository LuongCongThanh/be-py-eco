"""Category — guild.md §15 Slice 2. Multi-level tree via a self-referential
`parent` FK. PostgreSQL has no native constraint for "no cycles in a
self-referential FK", so acyclicity is enforced in application code
(`Category.assert_acyclic`), called from the service layer before save —
see Issue #7's Decision Document.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel
from modules.catalog.errors import CategoryCycleError


class Category(BaseModel):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )

    class Meta:
        db_table = "catalog_category"

    def __str__(self) -> str:
        return str(self.id)

    def assert_acyclic(self, new_parent: Category | None) -> None:
        """Raise `CategoryCycleError` if setting `new_parent` as this
        Category's parent would create a cycle (including self-parenting).

        Walks up from `new_parent` toward the root; if `self` is encountered,
        the assignment would close a loop.
        """
        if new_parent is None:
            return
        if new_parent.pk == self.pk:
            raise CategoryCycleError()
        seen: set = {self.pk}
        node: Category | None = new_parent
        while node is not None:
            if node.pk in seen:
                raise CategoryCycleError()
            seen.add(node.pk)
            node = node.parent
