"""MediaUpload — guild.md §15 Slice 2, commit 8. Created `pending` with a
presigned credential into a randomly-keyed `quarantine/` prefix; a worker
(commits 9-11) validates/scans/derives it into `ready` or `rejected`.
Only a `ready` asset is ever attachable to a Product or served via CDN —
the object key never derives from client input (declared filename,
content type) so nothing about the storage path is attacker-controlled.
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel


class MediaUploadStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    READY = "ready", "Ready"
    REJECTED = "rejected", "Rejected"


class MediaUpload(BaseModel):
    status = models.CharField(
        max_length=20,
        choices=MediaUploadStatus.choices,
        default=MediaUploadStatus.PENDING,
    )
    storage_key = models.CharField(max_length=255, unique=True)
    declared_content_type = models.CharField(max_length=100)
    declared_size_bytes = models.PositiveBigIntegerField()
    rejection_reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "media_upload"

    def __str__(self) -> str:
        return self.storage_key
