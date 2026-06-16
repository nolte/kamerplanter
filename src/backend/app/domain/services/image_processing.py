"""REQ-029 §5.4 — Shared image-processing helpers for plant identification.

Single source of truth for stripping EXIF metadata before any image leaves
the system. Used by ``IdentificationService`` (WS-1) and, later, by the
reference-image acquisition pipeline (WS-4) before sending to the
inference service.

Privacy guarantee (REQ-025 §5.4): GPS coordinates, device information and
capture timestamps are removed; the image orientation is baked into the
pixel data so dropping the EXIF orientation tag does not rotate the image.
"""

import io

import structlog
from PIL import Image, ImageOps

logger = structlog.get_logger()

# JPEG/PNG magic bytes (REQ-029 §3.5 image validation).
_JPEG_MAGIC = b"\xff\xd8"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

_SUPPORTED_OUTPUT_FORMATS = {"JPEG", "PNG"}


def is_supported_image(image_data: bytes) -> bool:
    """Return True if the bytes start with a supported (JPEG/PNG) magic header."""
    return image_data[:2] == _JPEG_MAGIC or image_data[:8] == _PNG_MAGIC


def strip_exif(image_data: bytes) -> bytes:
    """Remove all EXIF metadata from an image and normalise orientation.

    Steps:
    1. Apply the EXIF orientation tag to the pixel data (``exif_transpose``),
       so the visible orientation is preserved once EXIF is dropped.
    2. Convert to ``RGB`` (drops alpha/CMYK quirks; consistent downstream).
    3. Re-encode without any EXIF/metadata block.

    Args:
        image_data: Raw JPEG/PNG bytes.

    Returns:
        Re-encoded image bytes with no EXIF metadata.

    Raises:
        ValueError: If the image cannot be decoded.
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            source_format = (img.format or "").upper()
            oriented = ImageOps.exif_transpose(img)
            rgb = oriented.convert("RGB")

            out_format = source_format if source_format in _SUPPORTED_OUTPUT_FORMATS else "JPEG"
            buffer = io.BytesIO()
            if out_format == "JPEG":
                rgb.save(buffer, format="JPEG", quality=95)
            else:
                rgb.save(buffer, format="PNG")
            return buffer.getvalue()
    except (OSError, ValueError) as exc:
        logger.warning("exif_strip_failed", error=str(exc))
        raise ValueError("Image could not be decoded for EXIF stripping.") from exc
