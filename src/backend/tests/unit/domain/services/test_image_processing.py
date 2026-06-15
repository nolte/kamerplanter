"""Unit tests for REQ-029 §5.4 EXIF-stripping helper."""

import io

import pytest
from PIL import Image

from app.domain.services.image_processing import is_supported_image, strip_exif


def _make_jpeg_with_exif() -> bytes:
    """Create a small JPEG carrying an EXIF orientation tag."""
    img = Image.new("RGB", (12, 8), color=(10, 120, 30))
    exif = img.getexif()
    exif[274] = 6  # Orientation tag = rotate 90° CW
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def _make_png() -> bytes:
    img = Image.new("RGBA", (10, 10), color=(0, 0, 0, 255))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def test_is_supported_image_detects_jpeg_and_png():
    assert is_supported_image(_make_jpeg_with_exif()) is True
    assert is_supported_image(_make_png()) is True


def test_is_supported_image_rejects_unknown():
    assert is_supported_image(b"not-an-image") is False
    assert is_supported_image(b"GIF89a....") is False


def test_strip_exif_removes_all_metadata():
    data = _make_jpeg_with_exif()
    original = Image.open(io.BytesIO(data))
    assert dict(original.getexif()), "fixture should carry EXIF"

    cleaned = strip_exif(data)

    result = Image.open(io.BytesIO(cleaned))
    assert dict(result.getexif()) == {}
    assert result.mode == "RGB"


def test_strip_exif_applies_orientation_to_pixels():
    # Orientation 6 rotates 90°, swapping width/height once baked in.
    data = _make_jpeg_with_exif()
    cleaned = strip_exif(data)
    result = Image.open(io.BytesIO(cleaned))
    # Original 12x8 → after exif_transpose with orientation 6 → 8x12.
    assert result.size == (8, 12)


def test_strip_exif_keeps_png_as_png():
    cleaned = strip_exif(_make_png())
    result = Image.open(io.BytesIO(cleaned))
    assert result.format == "PNG"
    assert result.mode == "RGB"


def test_strip_exif_raises_on_garbage():
    with pytest.raises(ValueError, match="could not be decoded"):
        strip_exif(b"\xff\xd8totally-not-a-jpeg")
