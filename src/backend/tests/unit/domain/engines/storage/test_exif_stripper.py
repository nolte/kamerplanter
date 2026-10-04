"""NFR-013 §5.1 step 7 — ExifStripper unit tests."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.domain.engines.storage.exif_stripper import (
    ExifStripper,
    is_strippable_format,
    is_unsupported_photo_format,
    strip_exif,
)


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


class TestFormatClassification:
    """SEC-005 — observability helpers for the erasure pipeline."""

    @pytest.mark.parametrize("mime", ["image/jpeg", "image/png", "image/webp", "IMAGE/JPEG"])
    def test_strippable_formats(self, mime: str) -> None:
        assert is_strippable_format(mime) is True
        assert is_unsupported_photo_format(mime) is False

    @pytest.mark.parametrize("mime", ["image/heic", "image/heif", "IMAGE/HEIC"])
    def test_heic_is_unsupported_not_strippable(self, mime: str) -> None:
        assert is_strippable_format(mime) is False
        assert is_unsupported_photo_format(mime) is True

    @pytest.mark.parametrize("mime", ["application/pdf", "", None])
    def test_non_photo_is_neither(self, mime) -> None:
        assert is_strippable_format(mime) is False
        assert is_unsupported_photo_format(mime) is False

    def test_heic_strip_exif_passthrough_unchanged(self) -> None:
        heic_bytes = b"\x00\x00\x00\x18ftypheic-bytes"
        assert strip_exif(heic_bytes, "image/heic") == heic_bytes


class TestDecodeCost:
    """#2108 — the strip decodes once, keeps the palette and refuses a pixel bomb."""

    def test_every_metadata_block_is_dropped_also_the_ones_pillow_re_emits(self) -> None:
        # A plain JPEG re-save re-emits ``comment`` from ``Image.info`` (measured on
        # Pillow 12.3) — the strip must not.
        exif = Image.Exif()
        exif[0x8825] = {1: "N", 2: (52.0, 31.0, 12.0)}
        source = io.BytesIO()
        Image.new("RGB", (32, 24), (40, 90, 20)).save(
            source, format="JPEG", exif=exif.tobytes(), comment=b"owner-note", xmp=b"<x:xmpmeta>gps</x:xmpmeta>"
        )

        cleaned = strip_exif(source.getvalue(), "image/jpeg")

        with Image.open(io.BytesIO(cleaned)) as img:
            leaked = sorted(k for k in img.info if k in {"exif", "xmp", "comment", "icc_profile"})
        assert leaked == []

    def test_a_palette_png_keeps_its_colours(self) -> None:
        # Rebuilding from ``getdata()`` dropped the palette: red came back black.
        palette = Image.new("P", (4, 4), 0)
        palette.putpalette([255, 0, 0] + [0, 0, 255] * 255)
        source = io.BytesIO()
        palette.save(source, format="PNG")

        cleaned = strip_exif(source.getvalue(), "image/png")

        with Image.open(io.BytesIO(cleaned)) as img:
            assert img.convert("RGB").getpixel((0, 0)) == (255, 0, 0)

    def test_an_image_above_the_ceiling_is_refused_before_decoding(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from PIL import ImageFile

        from app.common.exceptions import ImagePixelLimitError

        source = io.BytesIO()
        Image.new("L", (12_000, 12_000), 0).save(source, format="PNG", optimize=True)

        def _refuse(image: ImageFile.ImageFile) -> None:
            raise AssertionError(f"decoded a {image.size} image")

        monkeypatch.setattr(ImageFile.ImageFile, "load", _refuse)
        with pytest.raises(ImagePixelLimitError):
            strip_exif(source.getvalue(), "image/png")

    def test_the_erasure_strip_admits_stored_objects_up_to_80_megapixels(self) -> None:
        from app.domain.engines.storage.exif_stripper import strip_exif_of_stored_object

        stored = io.BytesIO()
        Image.new("L", (7_000, 6_000), 0).save(stored, format="PNG", optimize=True)  # 42 MPx
        bomb = io.BytesIO()
        Image.new("L", (9_000, 9_000), 0).save(bomb, format="PNG", optimize=True)  # 81 MPx

        assert strip_exif_of_stored_object(stored.getvalue(), "image/png") is not None
        assert strip_exif_of_stored_object(bomb.getvalue(), "image/png") is None
