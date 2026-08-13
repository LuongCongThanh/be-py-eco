"""Global test fixtures — applies to every test under tests/ and src/*/tests/."""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Isolate every test from cache state left by an earlier test — matters
    most for DRF throttling (common/api/throttling.py), which stores
    request counters in the cache.
    """
    cache.clear()
    yield
