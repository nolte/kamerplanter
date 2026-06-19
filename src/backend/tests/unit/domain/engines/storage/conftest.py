"""Shared image fixtures for the storage-engine tests."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase


def _make_image(fmt: str, *, size: tuple[int, int] = (640, 480), exif: bytes | None = None) -> bytes:
    img = Image.new("RGB", size, color=(120, 200, 80))
    buffer = io.BytesIO()
    if exif is not None:
        img.save(buffer, format=fmt, exif=exif)
    else:
        img.save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
def jpeg_with_gps() -> bytes:
    """A JPEG carrying EXIF GPS + device tags (to be stripped).

    Uses a GPS IFD with scalar/ref values that Pillow can encode portably, plus
    device Make/Model. The point of the fixture is that *some* EXIF/GPS metadata
    is present; the stripper must remove all of it.
    """
    exif = Image.Exif()
    exif[ExifBase.Make.value] = "TestCam"
    exif[ExifBase.Model.value] = "SecretPhone X"
    gps_ifd = exif.get_ifd(ExifBase.GPSInfo.value)
    gps_ifd[1] = "N"  # GPSLatitudeRef
    gps_ifd[3] = "E"  # GPSLongitudeRef
    gps_ifd[5] = 0  # GPSAltitudeRef (above sea level)
    return _make_image("JPEG", exif=exif.tobytes())


@pytest.fixture
def plain_jpeg() -> bytes:
    return _make_image("JPEG")


@pytest.fixture
def plain_png() -> bytes:
    return _make_image("PNG")


@pytest.fixture
def plain_webp() -> bytes:
    return _make_image("WEBP")
