"""Global test fixtures — applies to every test under tests/ and src/*/tests/."""

import pytest
from django.core.cache import cache

# Registered at the root (rather than only tests/conftest.py) so
# `celery_worker`/`celery_app` are available to module-local integration
# tests too (e.g. src/modules/search/tests/test_indexing.py) — guild.md
# §15 Slice 3, commit 2.
pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Isolate every test from cache state left by an earlier test — matters
    most for DRF throttling (common/api/throttling.py), which stores
    request counters in the cache.
    """
    cache.clear()
    yield
