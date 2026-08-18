"""Attach a MediaUpload to a Product — guild.md §15 Slice 2, commit 12.
Only a `ready` asset may ever be attached; this is what makes "≥1 ready
media" a real, checkable precondition for `catalog.publish_product`.
"""

from __future__ import annotations

from modules.catalog.models.product import Product
from modules.media.errors import MediaUploadNotReadyError
from modules.media.models.media_upload import MediaUpload, MediaUploadStatus


def attach_media_to_product(*, media_upload: MediaUpload, product: Product) -> MediaUpload:
    if media_upload.status != MediaUploadStatus.READY:
        raise MediaUploadNotReadyError()

    media_upload.product = product
    media_upload.save(update_fields=["product", "updated_at"])
    return media_upload
