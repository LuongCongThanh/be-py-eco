"""Category tree mutation services — guild.md §15 Slice 2, commit 1.

Cycle-checking lives on the model (`Category.assert_acyclic`); these
services are the only call sites that create/re-parent a Category, so the
check can't be bypassed by writing directly through the ORM elsewhere in
this module.
"""

from __future__ import annotations

from modules.catalog.models.category import Category


def create_category(*, parent: Category | None = None) -> Category:
    category = Category(parent=parent)
    category.assert_acyclic(parent)
    category.save()
    return category


def reparent_category(*, category: Category, new_parent: Category | None) -> Category:
    category.assert_acyclic(new_parent)
    category.parent = new_parent
    category.save(update_fields=["parent", "updated_at"])
    return category
