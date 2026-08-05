"""Shared image fixtures for the storage-engine tests."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase

#: Marker values embedded in the metadata fixtures. Tests assert on these
#: literally (as substrings of the encoded bytes), so a leak is detected even
#: when the leaking container is one Pillow does not parse back into ``info``.
CAMERA_MAKE = "TestCam"
CAMERA_MODEL = "SecretPhone X"
CAPTURE_TIME = "2026:08:04 12:34:56"
XMP_MARKER = b"<x:xmpmeta>secret-location</x:xmpmeta>"
#: 52°31'12" N, 13°24'36" E — Berlin, i.e. a real, resolvable position.
GPS_LATITUDE = (52.0, 31.0, 12.0)
GPS_LONGITUDE = (13.0, 24.0, 36.0)


def gps_exif() -> Image.Exif:
    """EXIF block with a resolvable GPS position, device identity and capture time."""
    exif = Image.Exif()
    exif[ExifBase.Make.value] = CAMERA_MAKE
    exif[ExifBase.Model.value] = CAMERA_MODEL
    exif[ExifBase.DateTime.value] = CAPTURE_TIME
    gps_ifd = exif.get_ifd(ExifBase.GPSInfo.value)
    gps_ifd[1] = "N"  # GPSLatitudeRef
    gps_ifd[2] = GPS_LATITUDE  # GPSLatitude
    gps_ifd[3] = "E"  # GPSLongitudeRef
    gps_ifd[4] = GPS_LONGITUDE  # GPSLongitude
    gps_ifd[5] = 0  # GPSAltitudeRef (above sea level)
    return exif


def _make_image(fmt: str, *, size: tuple[int, int] = (640, 480), exif: bytes | None = None, **params) -> bytes:
    img = Image.new("RGB", size, color=(120, 200, 80))
    buffer = io.BytesIO()
    if exif is not None:
        img.save(buffer, format=fmt, exif=exif, **params)
    else:
        img.save(buffer, format=fmt, **params)
    return buffer.getvalue()


@pytest.fixture
def jpeg_with_gps() -> bytes:
    """A JPEG carrying EXIF GPS coordinates, device tags and capture time.

    The GPS IFD holds an actual position (Berlin), not just the N/E reference
    letters — a rendition that leaked only the refs but not the coordinates
    would otherwise pass a weaker test while still being a location disclosure.
    """
    return _make_image("JPEG", exif=gps_exif().tobytes())


@pytest.fixture
def png_with_gps() -> bytes:
    """A PNG carrying the same EXIF block in an ``eXIf`` chunk."""
    return _make_image("PNG", exif=gps_exif().tobytes())


@pytest.fixture
def webp_with_gps() -> bytes:
    """A WEBP carrying EXIF *and* XMP — the source format is also a thumbnail target."""
    return _make_image("WEBP", exif=gps_exif().tobytes(), xmp=XMP_MARKER)


@pytest.fixture
def plain_jpeg() -> bytes:
    return _make_image("JPEG")


@pytest.fixture
def plain_png() -> bytes:
    return _make_image("PNG")


@pytest.fixture
def plain_webp() -> bytes:
    return _make_image("WEBP")
