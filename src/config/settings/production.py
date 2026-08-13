"""Production settings — managed services, strict host checks, no accidental defaults."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

# Connection pooling via psycopg3's built-in pool. Exact pool sizing is an
# infrastructure-sizing decision deferred per Issue #4's Further Notes
# (guild.md §16) — this only turns pooling on, not its size.
DATABASES["default"]["OPTIONS"] = {  # noqa: F405
    **DATABASES["default"].get("OPTIONS", {}),  # noqa: F405
    "pool": True,
}
