"""Integration tests for the upload processing pipeline — Issue #7
commits 9-11. Require the local infra stack (real MinIO + ClamAV, per
guild.md §10.1); they are not mocked because the interesting behavior
happens inside the worker's storage/scan round trip, not the request.
Same bucket-provisioning pattern as tests/test_storage.py.
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


@pytest.mark.django_db
def test_clean_image_ends_ready_with_derivatives() -> None:
    data = _png_bytes()
    credential = request_upload(content_type="image/png", size_bytes=len(data))
    default_storage.save(credential.media_upload.storage_key, ContentFile(data))

    try:
        validate_upload(str(credential.media_upload.id))

        credential.media_upload.refresh_from_db()
        assert credential.media_upload.status == MediaUploadStatus.READY
        assert default_storage.exists(credential.media_upload.webp_key)
        assert default_storage.exists(credential.media_upload.avif_key)
        assert default_storage.exists(credential.media_upload.thumbnail_key)
    finally:
        default_storage.delete(credential.media_upload.storage_key)
        if credential.media_upload.webp_key:
            default_storage.delete(credential.media_upload.webp_key)
        if credential.media_upload.avif_key:
            default_storage.delete(credential.media_upload.avif_key)
        if credential.media_upload.thumbnail_key:
            default_storage.delete(credential.media_upload.thumbnail_key)


@pytest.mark.django_db
def test_duplicate_object_created_event_does_not_reprocess() -> None:
    data = _png_bytes()
    credential = request_upload(content_type="image/png", size_bytes=len(data))
    default_storage.save(credential.media_upload.storage_key, ContentFile(data))

    try:
        validate_upload(str(credential.media_upload.id))
        credential.media_upload.refresh_from_db()
        first_webp_key = credential.media_upload.webp_key

        # A duplicate delivery of the same object-created event.
        validate_upload(str(credential.media_upload.id))
        credential.media_upload.refresh_from_db()

        assert credential.media_upload.webp_key == first_webp_key
    finally:
        default_storage.delete(credential.media_upload.storage_key)
        if credential.media_upload.webp_key:
            default_storage.delete(credential.media_upload.webp_key)
        if credential.media_upload.avif_key:
            default_storage.delete(credential.media_upload.avif_key)
        if credential.media_upload.thumbnail_key:
            default_storage.delete(credential.media_upload.thumbnail_key)
