"""Smoke test proving Django can reach the real PostgreSQL test database.

Per guild.md §10.5: real PostgreSQL only, never SQLite.
"""

import pytest
from django.db import connection


@pytest.mark.django_db
def test_database_connection_is_reachable():
    connection.ensure_connection()
    assert connection.is_usable()
