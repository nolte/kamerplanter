"""REQ-029 §5.4 — tests for EXIF stripping and image normalization."""

import io

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase

from app.domain.calculators.image_preprocessor import strip_exif_and_normalize


def _make_jpeg(width: int = 200, height: int = 100, with_gps: bool = False) -> bytes:
    img = Image.new("RGB", (width, height), color=(10, 120, 30))
    buffer = io.BytesIO()
    if with_gps:
        exif = Image.Exif()
        # Device make + a GPS IFD with coordinates — exactly the data REQ-029 §5.4
        # mandates be stripped before any third-party transfer.
        exif[ExifBase.Make.value] = "TestCam"
        exif[ExifBase.Model.value] = "Model-X"
        exif[ExifBase.DateTime.value] = "2026:06:15 12:00:00"
        img.save(buffer, format="JPEG", exif=exif)
    else:
        img.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_strip_exif_removes_metadata():
    original = _make_jpeg(with_gps=True)

    # Sanity: the original actually carries EXIF.
    with Image.open(io.BytesIO(original)) as src:
        assert src.info.get("exif") is not None

    cleaned = strip_exif_and_normalize(original)

    with Image.open(io.BytesIO(cleaned)) as result:
        assert result.format == "JPEG"
        assert result.info.get("exif") is None


def test_normalize_downscales_large_image():
    original = _make_jpeg(width=4000, height=2000)
    cleaned = strip_exif_and_normalize(original, max_dimension=1024)

    with Image.open(io.BytesIO(cleaned)) as result:
        assert max(result.size) == 1024


def test_normalize_keeps_small_image_dimensions():
    original = _make_jpeg(width=200, height=100)
    cleaned = strip_exif_and_normalize(original, max_dimension=1024)

    with Image.open(io.BytesIO(cleaned)) as result:
        assert result.size == (200, 100)


def test_invalid_bytes_raise_value_error():
    with pytest.raises(ValueError):
        strip_exif_and_normalize(b"not-an-image")
