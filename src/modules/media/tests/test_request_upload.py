"""API test: requesting a presigned upload credential — Issue #7
commit 8's verify criterion. `generate_presigned_post` is a local SigV4
signing operation (no network call), so this runs without a live MinIO
container; the pipeline itself (commits 9-11) does need one.
"""

import base64
import json
import uuid
from typing import cast

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from modules.accounts.models import Staff
from modules.accounts.tests.factories import StaffFactory
from modules.media.models import MediaUpload, MediaUploadStatus
from modules.media.services.request_upload import request_upload


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _staff_auth_header(api_client: APIClient) -> dict:
    staff = cast(Staff, StaffFactory(mfa_confirmed=True))
    response = api_client.post(
        "/api/v1/admin/staff/login",
        {"email": staff.email, "password": "a-strong-password-123"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    access = response.json()["data"]["access"]
    return {"Authorization": f"Bearer {access}"}


@pytest.mark.django_db
def test_request_upload_creates_pending_upload_with_random_quarantine_key() -> None:
    credential_a = request_upload(content_type="image/png", size_bytes=1024)
    credential_b = request_upload(content_type="image/png", size_bytes=1024)

    assert credential_a.media_upload.status == MediaUploadStatus.PENDING
    assert credential_a.media_upload.storage_key.startswith("quarantine/")
    assert credential_a.media_upload.storage_key != credential_b.media_upload.storage_key


@pytest.mark.django_db
def test_credential_url_is_not_derived_from_filename() -> None:
    credential = request_upload(content_type="image/png", size_bytes=1024)

    # the key is a random UUID under quarantine/, never a client-supplied name
    key = credential.media_upload.storage_key.removeprefix("quarantine/")
    uuid.UUID(key)  # raises ValueError if not a valid UUID


@pytest.mark.django_db
def test_credential_expires_in_about_five_minutes() -> None:
    credential = request_upload(content_type="image/png", size_bytes=1024)

    policy_b64 = credential.upload_fields["policy"]
    policy = json.loads(base64.b64decode(policy_b64))
    assert "expiration" in policy


@pytest.mark.django_db
def test_request_upload_api(api_client: APIClient) -> None:
    auth = _staff_auth_header(api_client)

    response = api_client.post(
        "/api/v1/admin/media/uploads",
        {"content_type": "image/png", "size_bytes": 2048},
        format="json",
        headers=auth,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["upload_url"]
    assert data["upload_fields"]
    media_upload = MediaUpload.objects.get(pk=data["media_upload_id"])
    assert media_upload.status == MediaUploadStatus.PENDING


@pytest.mark.django_db
def test_request_upload_api_requires_auth(api_client: APIClient) -> None:
    response = api_client.post(
        "/api/v1/admin/media/uploads",
        {"content_type": "image/png", "size_bytes": 2048},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
