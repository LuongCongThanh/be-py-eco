"""Test settings — real PostgreSQL, never SQLite (guild.md §10.5).

Django's test runner creates a dedicated `test_<NAME>` database from the
`default` connection below, so no separate connection is configured here.
"""

from .base import *  # noqa: F403

DEBUG = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
GOOGLE_OAUTH_CLIENT_CLASS = "integrations.google_oauth.fake.FakeGoogleOAuthClient"
