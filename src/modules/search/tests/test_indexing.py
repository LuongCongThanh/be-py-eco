"""Integration tests: the full outbox -> index_product -> OpenSearch
sync path — guild.md §15 Slice 3, commits 1-2. Require a live OpenSearch
cluster and a real Celery worker (per guild.md §10.1, same `celery_worker`
fixture pattern as tests/test_celery.py) and fail here for the same
reason those existing tests already do — no live infra in this
environment, not a regression.
"""

import time

import pytest

from common.db.outbox import dispatch_pending_events
from config.celery import app
from integrations.opensearch.client import get_opensearch_client
from modules.catalog.services.category_tree import create_category
from modules.catalog.services.create_product import create_product, create_variant
from modules.catalog.services.publish_product import publish_product
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus
from modules.media.services.attach_to_product import attach_media_to_product
from modules.search.mapping import index_name
from modules.translation.services.set_translation import set_translation


@pytest.fixture
def celery_config():
    return {"broker_url": app.conf.broker_url, "result_backend": app.conf.result_backend}


@pytest.fixture
def celery_app(celery_config):
    app.conf.update(**celery_config)
    return app


@pytest.fixture
def celery_worker_parameters():
    # Same workaround as tests/test_celery.py — celery's own ping
    # self-check is flaky against this environment's Redis backend.
    return {"perform_ping_check": False}


def _publish_product(sku: str):
    product = create_product(primary_category=create_category())
    set_translation(entity=product, locale="vi", field="name", value="Áo thun")
    create_variant(product=product, sku=sku, base_price_vnd=100_000, weight_grams=100)
    ready_upload = MediaUpload.objects.create(
        storage_key=f"quarantine/{sku}",
        declared_content_type="image/png",
        declared_size_bytes=10,
        status=MediaUploadStatus.READY,
    )
    attach_media_to_product(media_upload=ready_upload, product=product)
    return publish_product(product=product)


@pytest.mark.django_db
def test_publishing_a_product_indexes_it_via_the_outbox(celery_worker) -> None:
    product = _publish_product("SKU-IDX-1")

    dispatch_pending_events()  # normally runs on Celery Beat's schedule

    client = get_opensearch_client()
    deadline = time.monotonic() + 10
    document = None
    while time.monotonic() < deadline:
        try:
            document = client.get(index=index_name("vi"), id=str(product.id))
            break
        except Exception:
            time.sleep(0.5)

    assert document is not None
    assert document["_source"]["name"] == "Áo thun"
