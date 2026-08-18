"""Request a presigned upload credential — guild.md §15 Slice 2, commit 8.

The storage key is a random UUID under `quarantine/`, never derived from
the client-declared filename — nothing about the object's location is
attacker-controlled, and no client-settable public ACL is ever passed
through (`generate_presigned_upload` fixes the bucket/policy server-side).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from integrations.media_storage.client import QUARANTINE_PREFIX, generate_presigned_upload
from modules.media.models.media_upload import MediaUpload

MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MiB — generous for product imagery


@dataclass(frozen=True)
class UploadCredential:
    media_upload: MediaUpload
    upload_url: str
    upload_fields: dict


def request_upload(*, content_type: str, size_bytes: int) -> UploadCredential:
    storage_key = f"{QUARANTINE_PREFIX}{uuid.uuid4()}"
    media_upload = MediaUpload.objects.create(
        storage_key=storage_key,
        declared_content_type=content_type,
        declared_size_bytes=size_bytes,
    )
    presigned = generate_presigned_upload(
        key=storage_key,
        content_type=content_type,
        max_size_bytes=MAX_UPLOAD_SIZE_BYTES,
    )
    return UploadCredential(
        media_upload=media_upload,
        upload_url=presigned["url"],
        upload_fields=presigned["fields"],
    )
