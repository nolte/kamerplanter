"""The background picture of a garden plan on the printed page (REQ-053 GP-FR-033, GP-NFR-052 (f)).

Pure logic besides one Pillow re-encode. The SVG writer of the plan (``plan_svg_engine``) emits no ``image``
element and no URL on purpose (SR-015), so the underlay is **not** drawn into the SVG: the PDF template lays it
as a second ``<img>`` *under* the plan figure, as a ``data:`` URI the restrictive ``url_fetcher`` accepts
(``data:`` and the template tree only). This module answers where on the page that picture goes.

**Geometry.** The picture's top-left pixel sits at ``underlay.origin`` (plan metres); a pixel is
``calibration.metres_per_pixel`` metres; the picture turns counter-clockwise by ``rotation_deg`` about its
top-left pixel (plan sense, y up). On the page y grows down, so the same turn is a *negative* CSS rotation.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Final

from PIL import Image, UnidentifiedImageError

from app.common.exceptions import ImagePixelLimitError
from app.common.image_bounds import open_bounded_image
from app.domain.engines.plan_svg_engine import PlanFrame
from app.domain.models.site import SiteUnderlay

#: Longest edge of the picture embedded in a PDF. An A3 sheet at 200 dpi is ~3 300 px; the print never resolves
#: finer than the scale allows, and a smaller image keeps the document small and the render fast.
PDF_MAX_EDGE_PX: Final = 2400
_JPEG_QUALITY: Final = 85
#: Longest edge of the picture's box on the page, in millimetres. An A3 sheet is 420 mm; ten times that still
#: allows a picture that covers the page from far outside it, and nothing larger is ever useful.
MAX_PLACED_MM: Final = 4200.0


class UnderlayImageError(ValueError):
    """The stored picture cannot be decoded - the PDF is then drawn without it."""


@dataclass(frozen=True)
class UnderlayImage:
    """A picture ready for the page: ``data:`` URI plus its size in the *original* pixels (the calibration's unit)."""

    data_uri: str
    width_px: int
    height_px: int


@dataclass(frozen=True)
class UnderlayPlacement:
    """Where the picture goes on the page, all lengths in millimetres, the turn in degrees (CSS sense)."""

    data_uri: str
    left_mm: float
    top_mm: float
    width_mm: float
    height_mm: float
    rotation_css_deg: float
    opacity: float


def prepare_image(data: bytes) -> UnderlayImage:
    """Decode *data*, flatten transparency onto white, shrink to :data:`PDF_MAX_EDGE_PX` and re-encode as JPEG.

    Raises:
        UnderlayImageError: the bytes are not an image Pillow can read.
    """
    try:
        with open_bounded_image(data) as source:
            width, height = source.size
            # Shrink while decoding where the format allows (a JPEG decodes at 1/2..1/8 scale), and shrink *before*
            # the RGBA conversion: a 40 MPx picture is never held at full size as four channels.
            source.draft("RGB", (PDF_MAX_EDGE_PX, PDF_MAX_EDGE_PX))
            source.thumbnail((PDF_MAX_EDGE_PX, PDF_MAX_EDGE_PX))
            rgba: Image.Image = source.convert("RGBA")
    except (UnidentifiedImageError, OSError, ValueError, ImagePixelLimitError) as exc:
        raise UnderlayImageError("The underlay picture cannot be decoded.") from exc
    return UnderlayImage(data_uri=_jpeg_data_uri(rgba), width_px=width, height_px=height)


def _jpeg_data_uri(rgba: Image.Image) -> str:
    """Flatten onto white, shrink to :data:`PDF_MAX_EDGE_PX`, encode (typed receivers: Pillow is external)."""
    flat: Image.Image = Image.new("RGB", rgba.size, (255, 255, 255))
    flat.paste(rgba, mask=rgba.getchannel("A"))
    buffer: io.BytesIO = io.BytesIO()
    flat.save(buffer, format="JPEG", quality=_JPEG_QUALITY)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def place_underlay(underlay: SiteUnderlay, image: UnderlayImage, frame: PlanFrame) -> UnderlayPlacement | None:
    """The picture's box on the page, from the calibration and the plan's own frame.

    ``None`` when the box would be absurdly large (a one-pixel calibration over 2 000 m scales a picture to
    kilometres): such a picture covers any page entirely, so printing it would only make the renderer allocate it.
    """
    metres_per_px = underlay.calibration.metres_per_pixel
    left, top = frame.paper_point(underlay.origin[0], underlay.origin[1])
    mm_per_px = metres_per_px * 1000.0 / frame.scale
    if max(image.width_px, image.height_px) * mm_per_px > MAX_PLACED_MM:
        return None
    return UnderlayPlacement(
        data_uri=image.data_uri,
        left_mm=left,
        top_mm=top,
        width_mm=image.width_px * mm_per_px,
        height_mm=image.height_px * mm_per_px,
        rotation_css_deg=-underlay.rotation_deg,
        opacity=underlay.opacity,
    )


__all__ = [
    "MAX_PLACED_MM",
    "PDF_MAX_EDGE_PX",
    "UnderlayImage",
    "UnderlayImageError",
    "UnderlayPlacement",
    "place_underlay",
    "prepare_image",
]
