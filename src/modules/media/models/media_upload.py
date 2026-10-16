"""MediaUpload — guild.md §15 Slice 2, commit 8. Created `pending` with a
presigned credential into a randomly-keyed `quarantine/` prefix; a worker
(commits 9-11) validates/scans/derives it into `ready` or `rejected`.
Only a `ready` asset is ever attachable to a Product or served via CDN —
the object key never derives from client input (declared filename,
content type) so nothing about the storage path is attacker-controlled.

The three `*_key` fields (commit 10) point at the public, non-quarantine
derivatives generated once an upload passes validation and the malware
scan; they stay blank until `status` is `ready`.

`product` (commit 12) is set once a Store Manager attaches a `ready`
asset to a Product — `catalog.services.publish_product` reads it back via
the reverse `product.media_uploads` accessor without `catalog` importing
anything from `media`, keeping the dependency one-directional
(media depends on catalog, not vice versa — same choice made for
`translation` in commit 4).
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
    webp_key = models.CharField(max_length=255, blank=True, default="")
    avif_key = models.CharField(max_length=255, blank=True, default="")
    thumbnail_key = models.CharField(max_length=255, blank=True, default="")
    product = models.ForeignKey(
        "catalog.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="media_uploads",
    )

    class Meta:
        db_table = "media_upload"

    def __str__(self) -> str:
        return self.storage_key
