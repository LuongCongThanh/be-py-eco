"""Shared catalog-module constants — kept in one place so the Admin API and
the `publish_product` precondition check can't drift apart.
"""

from __future__ import annotations

# guild.md §2 — launch is Vietnam-only; `vi` is the default locale content
# falls back to and the locale "complete default-locale content" is
# measured against. Slice 11 makes this configurable per Supported
# Country instead of a module constant.
DEFAULT_LOCALE = "vi"

# Fields that must have an approved translation in DEFAULT_LOCALE before a
# Product can publish (Issue #7 commit 7's precondition #1).
REQUIRED_TRANSLATION_FIELDS = ["name"]
