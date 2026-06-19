"""NFR-013 §5.1 step 7 / §4.2 — EXIF / GPS metadata removal.

Re-encodes raster images without their metadata blocks (EXIF, GPS, device
maker-notes, XMP, ICC where applicable) so a stored photo cannot leak the
location or device of the person who took it.

Strategy: load the image with Pillow and write it back from the bare pixel
data — a fresh ``Image`` built from ``getdata()`` carries no ``info``
dictionary, so no EXIF/GPS survives the round-trip. Non-image bytes are
returned unchanged.

The implementation is shared by the upload pipeline (``AttachmentService``)
and the REQ-025 erasure hook (``IObjectStorageAdapter.strip_exif_for_user``)
via the module-level :func:`strip_exif` helper.
"""

from __future__ import annotations

import io

import structlog
from PIL import Image

logger = structlog.get_logger()

# MIME types we re-encode. HEIC is intentionally excluded: Pillow cannot encode
# HEIC without pillow-heif, and re-encoding to another container would change
# the stored extension. (HEIC uploads are rare on the supported clients; if
# needed this is a follow-up — documented in the run report.)
_STRIPPABLE_FORMATS: dict[str, str] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


def _save_kwargs(pil_format: str) -> dict[str, object]:
    if pil_format == "JPEG":
        return {"quality": 95, "optimize": True}
    if pil_format == "WEBP":
        return {"quality": 90, "method": 4}
    return {"optimize": True}


def strip_exif(data: bytes, mime_type: str) -> bytes:
    """Return ``data`` with image metadata removed; passthrough for non-images.

    Never raises on malformed image bytes — if Pillow cannot decode the input
    the original bytes are returned unchanged (the magic-byte validator runs
    earlier in the pipeline, so genuinely corrupt uploads are already blocked;
    this is defence in depth so erasure can never crash a batch).
    """
    pil_format = _STRIPPABLE_FORMATS.get((mime_type or "").lower().strip())
    if pil_format is None:
        return data

    try:
        with Image.open(io.BytesIO(data)) as src:
            src.load()
            # Rebuild the image from raw pixels so no metadata survives.
            clean = Image.new(src.mode, src.size)
            clean.putdata(list(src.getdata()))
            buffer = io.BytesIO()
            clean.save(buffer, format=pil_format, **_save_kwargs(pil_format))
            return buffer.getvalue()
    except (OSError, ValueError) as exc:
        logger.warning("exif_strip_skipped", mime_type=mime_type, reason=str(exc))
        return data


class ExifStripper:
    """Engine wrapper around :func:`strip_exif` (NFR-013 §5.1)."""

    def strip(self, data: bytes, mime_type: str) -> bytes:
        """Strip EXIF/GPS metadata from image bytes (passthrough for non-images)."""
        return strip_exif(data, mime_type)


__all__ = ["ExifStripper", "strip_exif"]
