"""Unit tests for the validation worker's pure core — Issue #7 commit 9's
verify criterion, minus the live-MinIO round trip (see
test_validate_upload_task.py for the integration test)."""

import io

from PIL import Image

from modules.media.tasks import _validate_bytes


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color="red").save(buf, format="PNG")
    return buf.getvalue()


def test_valid_png_passes() -> None:
    data = _png_bytes()

    result = _validate_bytes(
        data=data, declared_size_bytes=len(data), declared_content_type="image/png"
    )

    assert result.is_valid is True


def test_size_mismatch_is_rejected() -> None:
    data = _png_bytes()

    result = _validate_bytes(
        data=data, declared_size_bytes=len(data) + 1, declared_content_type="image/png"
    )

    assert result.is_valid is False
    assert "size" in result.reason


def test_mislabeled_content_type_is_rejected() -> None:
    """A PNG uploaded but declared as JPEG — magic bytes don't match."""
    data = _png_bytes()

    result = _validate_bytes(
        data=data, declared_size_bytes=len(data), declared_content_type="image/jpeg"
    )

    assert result.is_valid is False
    assert "magic bytes" in result.reason


def test_unsupported_content_type_is_rejected() -> None:
    data = _png_bytes()

    result = _validate_bytes(
        data=data, declared_size_bytes=len(data), declared_content_type="application/pdf"
    )

    assert result.is_valid is False
    assert "unsupported" in result.reason


def test_corrupted_image_fails_to_decode() -> None:
    data = b"not-a-real-image" + _png_bytes()[4:]

    result = _validate_bytes(
        data=data, declared_size_bytes=len(data), declared_content_type="image/png"
    )

    assert result.is_valid is False
