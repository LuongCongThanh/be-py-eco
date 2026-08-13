"""API tests: /health/live never touches PostgreSQL; /health/ready does."""

from unittest.mock import patch

import pytest
from django.db.utils import OperationalError
from django.test import Client


def test_live_returns_ok_even_when_database_is_unreachable(client: Client) -> None:
    with patch("django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection") as ensure:
        ensure.side_effect = OperationalError("db down")
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    ensure.assert_not_called()


@pytest.mark.django_db
def test_ready_returns_ok_when_database_is_reachable(client: Client) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_503_when_database_is_unreachable(client: Client) -> None:
    with patch("django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection") as ensure:
        ensure.side_effect = OperationalError("db down")
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
