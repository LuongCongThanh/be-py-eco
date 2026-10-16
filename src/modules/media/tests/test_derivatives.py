"""Unit tests for derivative generation — Issue #7 commit 10's verify
criterion, minus the storage/malware-scan round trip."""

import io

from PIL import Image

from modules.media.derivatives import generate_derivatives


def _png_with_exif() -> bytes:
    buf = io.BytesIO()
    image = Image.new("RGB", (16, 16), color="purple")
    exif = image.getexif()
    exif[0x0131] = "test-camera-software"  # Software tag
    image.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def test_generates_webp_avif_and_thumbnail() -> None:
    derivatives = generate_derivatives(_png_with_exif())

    assert Image.open(io.BytesIO(derivatives.webp)).format == "WEBP"
    assert Image.open(io.BytesIO(derivatives.avif)).format == "AVIF"
    assert Image.open(io.BytesIO(derivatives.thumbnail_webp)).format == "WEBP"


def test_thumbnail_is_bounded_by_thumbnail_size() -> None:
    derivatives = generate_derivatives(_png_with_exif())

    thumbnail = Image.open(io.BytesIO(derivatives.thumbnail_webp))
    assert thumbnail.width <= 320
    assert thumbnail.height <= 320


def test_derivatives_carry_no_exif() -> None:
    derivatives = generate_derivatives(_png_with_exif())

    webp_image = Image.open(io.BytesIO(derivatives.webp))
    assert not webp_image.getexif()
