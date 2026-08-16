"""Test settings — real PostgreSQL, never SQLite (guild.md §10.5).

Django's test runner creates a dedicated `test_<NAME>` database from the
`default` connection below, so no separate connection is configured here.
"""

from .base import *  # noqa: F403

DEBUG = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
GOOGLE_OAUTH_CLIENT_CLASS = "integrations.google_oauth.fake.FakeGoogleOAuthClient"

# Isolated per-process cache for tests — not the real Redis instance base.py
# points at. DRF throttling (common/api/throttling.py) stores counters in
# the cache; sharing dev's real Redis here would let one test's throttle
# hits bleed into another's. tests/test_redis.py proves real Redis
# connectivity directly, independent of this setting.
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}
