"""#2108 — the one place under ``app/`` that hands image bytes to a Pillow decoder.

Every image the backend decodes — attachment EXIF strip and thumbnails,
identification, CV diagnosis, pest detection, reference-image acquisition — is
opened through :func:`open_bounded_image`. It reads ``width x height`` from the
header (``Image.open`` is lazy: no pixel is decoded there) and refuses an image
above :data:`MAX_IMAGE_PIXELS` with :class:`~app.common.exceptions.ImagePixelLimitError`
(HTTP 413) **before** the caller can ``load()`` it.

Why a ceiling of our own: Pillow's default ``Image.MAX_IMAGE_PIXELS`` (~89 MPx)
only *warns*; it raises ``DecompressionBombError`` at twice that (~178 MPx). A
445 KB PNG of 12 000 x 12 000 px (144 MPx) passed and was fully decoded
(measured for #2108). 40 MPx is far above any phone or plant camera
(~6300 x 6300 px) and was already the limit of the identification and CV routes.

Importing this module also lowers Pillow's process-global
``Image.MAX_IMAGE_PIXELS`` to the same value, so a decode this module never sees
(a library decoding internally) meets Pillow's own check at 40 MPx (warning) and
80 MPx (error) instead of 89 / 178 MPx. The guard
``tests/unit/guards/test_image_decodes_go_through_the_pixel_ceiling.py`` keeps
every ``Image.open`` under ``app/`` in this module.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from contextlib import contextmanager

from PIL import Image

from app.common.exceptions import ImagePixelLimitError

#: The decode ceiling in pixels (``width x height``), ~6300 x 6300 px.
MAX_IMAGE_PIXELS = 40_000_000

#: The highest ceiling a caller may ask for. Pillow raises its own
#: ``DecompressionBombError`` above twice ``Image.MAX_IMAGE_PIXELS``; with the
#: global lowered below that is 80 MPx. Only the erasure EXIF strip of objects
#: stored before #2108 uses it — those were accepted under Pillow's defaults.
STORED_IMAGE_MAX_PIXELS = 2 * MAX_IMAGE_PIXELS

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


@contextmanager
def open_bounded_image(data: bytes, *, max_pixels: int = MAX_IMAGE_PIXELS) -> Iterator[Image.Image]:
    """Open *data* lazily and refuse it before decoding when it has more than *max_pixels* pixels.

    The yielded image has only its header parsed; decoding happens when the
    caller loads, converts or saves it.

    Raises:
        ImagePixelLimitError: the header declares more than *max_pixels*
            pixels — also when Pillow's own decompression-bomb check refuses it
            first. ``max_pixels`` above :data:`STORED_IMAGE_MAX_PIXELS` is a
            programming error (``ValueError``): Pillow would refuse those itself.
        PIL.UnidentifiedImageError / OSError / ValueError: as ``Image.open``.
    """
    if max_pixels > STORED_IMAGE_MAX_PIXELS:
        raise ValueError(f"max_pixels {max_pixels} is above the ceiling Pillow enforces ({STORED_IMAGE_MAX_PIXELS})")
    try:
        # Between the ceiling and twice it Pillow emits a DecompressionBombWarning
        # and goes on; the size check below refuses those images before decoding.
        image = Image.open(io.BytesIO(data))
    except Image.DecompressionBombError as exc:
        raise ImagePixelLimitError(max_pixels) from exc
    with image:
        width, height = image.size
        if width * height > max_pixels:
            raise ImagePixelLimitError(max_pixels)
        yield image


def image_dimensions(data: bytes, *, max_pixels: int = MAX_IMAGE_PIXELS) -> tuple[int, int]:
    """``(width, height)`` from the header of *data*, refused above *max_pixels* like :func:`open_bounded_image`."""
    with open_bounded_image(data, max_pixels=max_pixels) as image:
        return image.size


__all__ = [
    "MAX_IMAGE_PIXELS",
    "STORED_IMAGE_MAX_PIXELS",
    "image_dimensions",
    "open_bounded_image",
]
