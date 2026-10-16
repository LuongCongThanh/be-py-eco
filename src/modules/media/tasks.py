"""Upload processing pipeline — guild.md §15 Slice 2, commits 9-11.
`validate_upload` is the object-created event handler: it validates
declared size/MIME/magic-bytes/decode (commit 9), then malware-scans,
strips metadata, and generates WebP/AVIF + thumbnail derivatives (commit
10), ending the `MediaUpload` in `ready` or `rejected`.

Idempotency (commit 11) is `select_for_update()` plus a status guard: a
duplicate object-created event for an upload that has already left
`pending` is a no-op, and the row lock means two concurrent deliveries
can't both pass the guard and double-process the same upload.

`_validate_bytes` is the pure, storage-independent validation core so its
rejection logic is unit-testable without a live MinIO container;
`generate_derivatives` (in `derivatives.py`) is likewise pure over bytes.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import filetype
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from integrations.clamav.client import InfectedFileError, scan_bytes
from modules.media.derivatives import generate_derivatives
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus

# declared_content_type -> the family of magic-byte MIME types considered a
# match. Images only for now — non-image assets (Issue #7 is product
# imagery) would extend this table, not branch on content_type ad hoc.
_ACCEPTED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

READY_PREFIX = "products/"


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


def _reject(media_upload: MediaUpload, reason: str) -> None:
    media_upload.status = MediaUploadStatus.REJECTED
    media_upload.rejection_reason = reason
    media_upload.save(update_fields=["status", "rejection_reason", "updated_at"])


@shared_task(name="media.validate_upload")
def validate_upload(media_upload_id: str) -> None:
    with transaction.atomic():
        media_upload = MediaUpload.objects.select_for_update().get(pk=media_upload_id)
        if media_upload.status != MediaUploadStatus.PENDING:
            return  # already processed — duplicate object-created delivery

        with default_storage.open(media_upload.storage_key, "rb") as f:
            data = f.read()

        result = _validate_bytes(
            data=data,
            declared_size_bytes=media_upload.declared_size_bytes,
            declared_content_type=media_upload.declared_content_type,
        )
        if not result.is_valid:
            _reject(media_upload, result.reason)
            return

        try:
            scan_bytes(data)
        except InfectedFileError as exc:
            _reject(media_upload, str(exc))
            return

        derivatives = generate_derivatives(data)
        base = f"{READY_PREFIX}{media_upload.id}"
        webp_key = default_storage.save(f"{base}.webp", ContentFile(derivatives.webp))
        avif_key = default_storage.save(f"{base}.avif", ContentFile(derivatives.avif))
        thumbnail_key = default_storage.save(
            f"{base}-thumb.webp", ContentFile(derivatives.thumbnail_webp)
        )

        media_upload.status = MediaUploadStatus.READY
        media_upload.webp_key = webp_key
        media_upload.avif_key = avif_key
        media_upload.thumbnail_key = thumbnail_key
        media_upload.save(
            update_fields=["status", "webp_key", "avif_key", "thumbnail_key", "updated_at"]
        )
