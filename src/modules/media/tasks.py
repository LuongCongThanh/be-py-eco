"""Upload validation worker — guild.md §15 Slice 2, commit 9. Validates
declared size, declared MIME type against magic bytes, and successful
decode; rejects anything mislabeled or malformed before the malware
scan/derivative pipeline (commit 10) ever touches it.

`_validate_bytes` is the pure, storage-independent core so its rejection
logic is unit-testable without a live MinIO container; `validate_upload`
is the Celery task that wires it to the real object.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import filetype
from celery import shared_task
from django.core.files.storage import default_storage
from PIL import Image, UnidentifiedImageError

from modules.media.models.media_upload import MediaUpload, MediaUploadStatus

# declared_content_type -> the family of magic-byte MIME types considered a
# match. Images only for now — non-image assets (Issue #7 is product
# imagery) would extend this table, not branch on content_type ad hoc.
_ACCEPTED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reason: str = ""


def _validate_bytes(
    *, data: bytes, declared_size_bytes: int, declared_content_type: str
) -> ValidationResult:
    if len(data) != declared_size_bytes:
        return ValidationResult(False, "declared size does not match the uploaded object's size")

    if declared_content_type not in _ACCEPTED_MIME_TYPES:
        reason = f"unsupported declared content type: {declared_content_type}"
        return ValidationResult(False, reason)

    kind = filetype.guess(data)
    if kind is None or kind.mime != declared_content_type:
        actual = kind.mime if kind else "unknown"
        return ValidationResult(False, f"magic bytes ({actual}) do not match declared type")

    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        return ValidationResult(False, "file failed to decode as a valid image")

    return ValidationResult(True)


@shared_task(name="media.validate_upload")
def validate_upload(media_upload_id: str) -> None:
    media_upload = MediaUpload.objects.get(pk=media_upload_id)
    if media_upload.status != MediaUploadStatus.PENDING:
        return  # already processed — idempotency is hardened in commit 11

    with default_storage.open(media_upload.storage_key, "rb") as f:
        data = f.read()

    result = _validate_bytes(
        data=data,
        declared_size_bytes=media_upload.declared_size_bytes,
        declared_content_type=media_upload.declared_content_type,
    )
    if not result.is_valid:
        media_upload.status = MediaUploadStatus.REJECTED
        media_upload.rejection_reason = result.reason
        media_upload.save(update_fields=["status", "rejection_reason", "updated_at"])
