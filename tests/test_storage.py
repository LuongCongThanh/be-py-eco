import uuid

import boto3
import environ
import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import default_storage

env = environ.Env()


@pytest.fixture(autouse=True)
def _ensure_bucket_exists():
    client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    try:
        client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
    except ClientError:
        client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)


def test_storage_put_read_delete_round_trip():
    key = f"smoke/{uuid.uuid4()}.txt"
    content = b"slice-0 storage smoke test"

    from django.core.files.base import ContentFile

    saved_name = default_storage.save(key, ContentFile(content))
    try:
        with default_storage.open(saved_name) as f:
            assert f.read() == content
    finally:
        default_storage.delete(saved_name)

    assert not default_storage.exists(saved_name)
