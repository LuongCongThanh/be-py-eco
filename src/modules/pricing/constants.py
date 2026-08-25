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

# Minor-unit decimal exponent per currency — VND has no minor unit (0
# decimal places), USD is cents (2). Money is always an integer count of
# this unit, never a float; guild.md §10.3.
CURRENCY_MINOR_UNIT_EXPONENTS: dict[str, int] = {
    "VND": 0,
    "USD": 2,
}
