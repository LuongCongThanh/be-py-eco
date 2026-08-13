import celery.contrib.testing.tasks  # noqa: F401 — registers "celery.ping" for celery_worker's readiness check

pytest_plugins = ("celery.contrib.pytest",)
