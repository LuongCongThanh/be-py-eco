"""Derivative generation — guild.md §15 Slice 2, commit 10. Strips
EXIF/GPS metadata (Pillow drops all metadata by default when re-encoding
without passing `exif=`/`icc_profile=` through) and produces WebP/AVIF
full-size derivatives plus a thumbnail. The `pillow-avif-plugin`
distribution's `pillow_avif` module registers AVIF support with Pillow
as a side effect of being imported.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pillow_avif  # noqa: F401 — registers the AVIF codec with Pillow
from PIL import Image

THUMBNAIL_SIZE = (320, 320)


@dataclass(frozen=True)
class Derivatives:
    webp: bytes
    avif: bytes
    thumbnail_webp: bytes


def generate_derivatives(data: bytes) -> Derivatives:
    with Image.open(io.BytesIO(data)) as image:
        # Re-encoding through a fresh RGB copy (rather than image.save(...)
        # directly) drops EXIF/GPS and any other embedded metadata — Pillow
        # only carries metadata forward when explicitly told to.
        clean = image.convert("RGB")

        webp_buf = io.BytesIO()
        clean.save(webp_buf, format="WEBP")

        avif_buf = io.BytesIO()
        clean.save(avif_buf, format="AVIF")

        thumbnail = clean.copy()
        thumbnail.thumbnail(THUMBNAIL_SIZE)
        thumbnail_buf = io.BytesIO()
        thumbnail.save(thumbnail_buf, format="WEBP")

    return Derivatives(
        webp=webp_buf.getvalue(),
        avif=avif_buf.getvalue(),
        thumbnail_webp=thumbnail_buf.getvalue(),
    )
