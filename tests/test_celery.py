"""Celery worker<->broker<->result round-trip smoke test.

Uses Celery's pytest plugin `celery_worker` fixture (registered in
tests/conftest.py) to spin up a real worker thread against the actual
RabbitMQ broker + Redis result backend for the duration of this test —
proving the connectivity path end to end without a separately-started
worker process.
"""

import time

import pytest

from config.celery import app, ping_task


@pytest.fixture
def celery_config():
    return {
        "broker_url": app.conf.broker_url,
        "result_backend": app.conf.result_backend,
    }


@pytest.fixture
def celery_app(celery_config):
    app.conf.update(**celery_config)
    return app


@pytest.fixture
def celery_worker_parameters():
    # Skip celery's own built-in "celery.ping" self-check — its result
    # fetch is flaky against this environment's Redis backend even when
    # the task itself completes; we prove the round-trip with our own
    # task + polling loop below instead.
    return {"perform_ping_check": False}


@pytest.mark.django_db
def test_ping_task_round_trips_through_broker(celery_worker):
    result = ping_task.delay()

    deadline = time.monotonic() + 10
    while not result.ready() and time.monotonic() < deadline:
        time.sleep(0.2)

    assert result.successful(), f"task did not complete in time (state={result.state})"
    assert result.result == "pong"
