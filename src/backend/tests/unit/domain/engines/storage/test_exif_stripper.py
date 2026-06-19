"""NFR-013 §5.1 step 7 — ExifStripper unit tests."""

from __future__ import annotations

import io

from PIL import Image

from app.domain.engines.storage.exif_stripper import ExifStripper


def _exif_of(data: bytes) -> Image.Exif:
    with Image.open(io.BytesIO(data)) as img:
        return img.getexif()


class TestExifStripper:
    def setup_method(self) -> None:
        self.stripper = ExifStripper()

    def test_strips_gps_and_device_metadata(self, jpeg_with_gps: bytes) -> None:
        # Sanity: the source actually carries EXIF.
        assert len(_exif_of(jpeg_with_gps)) > 0

        cleaned = self.stripper.strip(jpeg_with_gps, "image/jpeg")
        assert len(_exif_of(cleaned)) == 0

    def test_cleaned_image_is_still_decodable(self, jpeg_with_gps: bytes) -> None:
        cleaned = self.stripper.strip(jpeg_with_gps, "image/jpeg")
        with Image.open(io.BytesIO(cleaned)) as img:
            img.load()
            assert img.size == (640, 480)

    def test_png_passthrough_decodable(self, plain_png: bytes) -> None:
        cleaned = self.stripper.strip(plain_png, "image/png")
        with Image.open(io.BytesIO(cleaned)) as img:
            assert img.format == "PNG"

    def test_non_image_is_returned_unchanged(self) -> None:
        pdf = b"%PDF-1.7\nhello"
        assert self.stripper.strip(pdf, "application/pdf") == pdf

    def test_malformed_image_returns_original(self) -> None:
        garbage = b"\xff\xd8\xff\xe0not-really-a-jpeg"
        assert self.stripper.strip(garbage, "image/jpeg") == garbage
