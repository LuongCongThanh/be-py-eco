"""Shared pricing-module constants."""

from __future__ import annotations

# guild.md §2 — VND is the sole Base Price currency; USD is the first
# additional Transaction Currency configured for this slice's "at least
# one other configured Transaction Currency" acceptance criterion.
BASE_CURRENCY = "VND"
SUPPORTED_TARGET_CURRENCIES = ["USD"]

# How long a synced rate is considered fresh before a display-layer
# consumer must flag it as stale (commit 11) — not a checkout block,
# that's Slice 5.
RATE_TTL_SECONDS = 3600
