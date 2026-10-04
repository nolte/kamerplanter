"""#2108 — the shared decode ceiling refuses from the header, before any pixel is decoded."""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageFile

from app.common.exceptions import ImagePixelLimitError
from app.common.image_bounds import (
    MAX_IMAGE_PIXELS,
    STORED_IMAGE_MAX_PIXELS,
    image_dimensions,
    open_bounded_image,
)


def _png(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("L", (width, height), 0).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


@pytest.fixture
def no_decode(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, int]]:
    """Fail the test on any decode; records the size of what was about to be decoded."""
    decoded: list[tuple[int, int]] = []

    def _refuse(image: ImageFile.ImageFile) -> None:
        decoded.append(image.size)
        raise AssertionError(f"decoded a {image.size} image")

    monkeypatch.setattr(ImageFile.ImageFile, "load", _refuse)
    return decoded


def test_the_ceiling_is_40_megapixels_and_pillow_is_lowered_to_it() -> None:
    assert MAX_IMAGE_PIXELS == 40_000_000
    assert STORED_IMAGE_MAX_PIXELS == 80_000_000
    assert Image.MAX_IMAGE_PIXELS == MAX_IMAGE_PIXELS


def test_an_image_at_the_ceiling_opens_and_one_pixel_more_is_refused() -> None:
    data = _png(10, 7)

    with open_bounded_image(data, max_pixels=70) as image:
        assert image.size == (10, 7)
    with pytest.raises(ImagePixelLimitError) as raised:
        image_dimensions(data, max_pixels=69)

    assert raised.value.status_code == 413
    assert raised.value.error_code == "IMAGE_PIXEL_LIMIT_EXCEEDED"


def test_a_144_megapixel_png_is_refused_without_decoding(no_decode: list[tuple[int, int]]) -> None:
    # Below Pillow's own default error bound (178 MPx): only the ceiling refuses it.
    bomb = _png(12_000, 12_000)

    with pytest.raises(ImagePixelLimitError):
        image_dimensions(bomb)

    assert no_decode == []


def test_an_image_pillow_itself_refuses_surfaces_as_the_same_413(no_decode: list[tuple[int, int]]) -> None:
    # 9 000 x 9 000 = 81 MPx: above twice the lowered global, so Image.open
    # raises DecompressionBombError before our own check runs.
    bomb = _png(9_000, 9_000)

    with pytest.raises(ImagePixelLimitError):
        image_dimensions(bomb, max_pixels=STORED_IMAGE_MAX_PIXELS)

    assert no_decode == []


def test_a_ceiling_above_what_pillow_enforces_is_a_programming_error() -> None:
    with pytest.raises(ValueError, match="above the ceiling"):
        image_dimensions(_png(2, 2), max_pixels=STORED_IMAGE_MAX_PIXELS + 1)


def test_undecodable_bytes_raise_what_pillow_raises() -> None:
    with pytest.raises(OSError):
        image_dimensions(b"not an image")
