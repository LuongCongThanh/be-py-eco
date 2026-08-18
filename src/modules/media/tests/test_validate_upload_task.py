"""Integration test: validate_upload against a real MinIO object — Issue
#7 commit 9. Requires the local infra stack (see tests/test_storage.py
for the same bucket-provisioning pattern); it is not mocked because the
interesting behavior here is the storage round trip, not the request.
"""

import io

import boto3
import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image

from modules.media.models.media_upload import MediaUploadStatus
from modules.media.services.request_upload import request_upload
from modules.media.tasks import validate_upload


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


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color="blue").save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.django_db
def test_mislabeled_upload_is_rejected() -> None:
    data = b"this is not an image, mislabeled as one"
    credential = request_upload(content_type="image/png", size_bytes=len(data))
    default_storage.save(credential.media_upload.storage_key, ContentFile(data))

    try:
        validate_upload(str(credential.media_upload.id))

        credential.media_upload.refresh_from_db()
        assert credential.media_upload.status == MediaUploadStatus.REJECTED
        assert credential.media_upload.rejection_reason
    finally:
        default_storage.delete(credential.media_upload.storage_key)
