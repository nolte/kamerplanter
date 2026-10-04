"""NFR-013 §5.1 step 7 / §4.2 — EXIF / GPS metadata removal.

Re-encodes raster images without their metadata blocks (EXIF, GPS, device
maker-notes, XMP, ICC where applicable) so a stored photo cannot leak the
location or device of the person who took it.

Strategy: open the image through the shared pixel ceiling
(``app.common.image_bounds``, #2108), decode it once, replace its ``info``
dictionary by the layout keys that identify nobody, and re-encode it with every
metadata block pinned to empty. Non-image bytes are returned unchanged.

Until #2108 the image was rebuilt from ``list(getdata())``: every pixel became a
Python tuple (measured: 80 bytes per pixel — about 1 GB for a 12 MPx phone
photo, 11.5 GB for a 144 MPx PNG of 445 KB), and a palette (``P``-mode) image
lost its palette and came back black. Re-encoding the decoded image itself
costs the decoded raster once and keeps the palette.

The implementation is shared by the upload pipeline (``AttachmentService``)
and the REQ-025 erasure hook (``IObjectStorageAdapter.strip_exif_for_user``)
via the module-level :func:`strip_exif` helper.
"""

from __future__ import annotations

import io

import structlog

from app.common.exceptions import ImagePixelLimitError
from app.common.image_bounds import MAX_IMAGE_PIXELS, STORED_IMAGE_MAX_PIXELS, open_bounded_image

logger = structlog.get_logger()

# MIME types we re-encode. HEIC is intentionally excluded: Pillow cannot encode
# HEIC without pillow-heif, and re-encoding to another container would change
# the stored extension. Since #2139 the upload pipeline therefore refuses every
# image type missing here while EXIF stripping is on (415), and HEIC/HEIF are
# no longer in the default whitelist; the app's clients convert to JPEG first.
_STRIPPABLE_FORMATS: dict[str, str] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

# SEC-005: HEIC/HEIF cannot be EXIF-stripped without a system-level decoder
# (``pillow-heif``). They are no longer accepted for upload (#2139), but objects
# stored before that still exist. Listing them here lets the erasure pipeline
# surface those as ``skipped`` (observable) instead of silently returning the
# original bytes — so a GDPR erasure never *appears* to strip GPS from a HEIC
# photo that it actually left untouched.
#
# Re-admitting HEIC needs ``pillow-heif`` and its opener registered; then move
# these formats into ``_STRIPPABLE_FORMATS`` and drop this set.
_UNSUPPORTED_PHOTO_FORMATS: frozenset[str] = frozenset({"image/heic", "image/heif"})


def is_strippable_format(mime_type: str) -> bool:
    """Return ``True`` when :func:`strip_exif` can actually remove metadata.

    ``False`` for non-image bytes and for allowed-but-unstrippable photo types
    (HEIC/HEIF). Used by the erasure hooks to classify and audit ``skipped``
    images (SEC-005) without re-deriving the strippable-format table.
    """
    return (mime_type or "").lower().strip() in _STRIPPABLE_FORMATS


def is_unsupported_photo_format(mime_type: str) -> bool:
    """Return ``True`` for allowed photo types that cannot be EXIF-stripped.

    Currently HEIC/HEIF — images the erasure pipeline must record as ``skipped``
    (and log) rather than treating the unchanged passthrough as a success.
    """
    return (mime_type or "").lower().strip() in _UNSUPPORTED_PHOTO_FORMATS


def _save_kwargs(pil_format: str) -> dict[str, object]:
    if pil_format == "JPEG":
        return {"quality": 95, "optimize": True}
    if pil_format == "WEBP":
        return {"quality": 90, "method": 4}
    return {"optimize": True}


# ``Image.info`` keys that are re-encoded as they are: palette transparency and
# animation layout. Everything else — EXIF, GPS, XMP, ICC, IPTC, comments,
# Photoshop blocks, PNG text chunks — is dropped. An allow-list, because the
# JPEG writer re-emits ``comment`` (and newer Pillow ``xmp``) from ``info`` on a
# plain re-save (measured on Pillow 12.3).
_KEPT_INFO_KEYS: frozenset[str] = frozenset({"transparency", "duration", "loop", "background"})

# Encoder parameters that pin every metadata block to empty, so no writer can
# fall back to a value it finds elsewhere (same contract as the thumbnails).
_METADATA_FREE_SAVE_PARAMS: dict[str, object] = {"exif": b"", "xmp": b"", "icc_profile": None}


def strip_exif(data: bytes, mime_type: str, *, max_pixels: int = MAX_IMAGE_PIXELS) -> bytes:
    """Return ``data`` with image metadata removed; passthrough for non-images.

    Never raises on malformed image bytes — if Pillow cannot decode the input
    the original bytes are returned unchanged (the magic-byte validator runs
    earlier in the pipeline, so genuinely corrupt uploads are already blocked;
    this is defence in depth so erasure can never crash a batch).

    Raises:
        ImagePixelLimitError: the image declares more than *max_pixels* pixels
            (#2108) — refused from its header, before anything is decoded. The
            upload pipeline answers 413; the erasure hooks pass the higher
            ``STORED_IMAGE_MAX_PIXELS`` and count what is still above it.
    """
    pil_format = _STRIPPABLE_FORMATS.get((mime_type or "").lower().strip())
    if pil_format is None:
        return data

    try:
        with open_bounded_image(data, max_pixels=max_pixels) as src:
            src.load()
            src.info = {key: value for key, value in src.info.items() if key in _KEPT_INFO_KEYS}
            buffer = io.BytesIO()
            src.save(buffer, format=pil_format, **_save_kwargs(pil_format), **_METADATA_FREE_SAVE_PARAMS)
            return buffer.getvalue()
    except (OSError, ValueError) as exc:
        logger.warning("exif_strip_skipped", mime_type=mime_type, reason=str(exc))
        return data


def strip_exif_of_stored_object(data: bytes, mime_type: str) -> bytes | None:
    """The REQ-025 erasure strip of an already stored object, or ``None`` above the stored-object ceiling.

    Objects stored before #2108 were admitted under Pillow's defaults, so the
    erasure strip accepts up to :data:`STORED_IMAGE_MAX_PIXELS` (80 MPx) rather
    than the 40 MPx upload ceiling — without the per-pixel tuples a stored
    80 MPx image costs its decoded raster once. ``None`` means the object is
    still above that and was left untouched; the erasure hooks count and log it
    (``exif_strip_over_pixel_limit``) instead of reporting it stripped.
    """
    try:
        return strip_exif(data, mime_type, max_pixels=STORED_IMAGE_MAX_PIXELS)
    except ImagePixelLimitError:
        return None


class ExifStripper:
    """Engine wrapper around :func:`strip_exif` (NFR-013 §5.1)."""

    def strip(self, data: bytes, mime_type: str) -> bytes:
        """Strip EXIF/GPS metadata from image bytes (passthrough for non-images).

        Raises ``ImagePixelLimitError`` above the 40 MPx ceiling (#2108).
        """
        return strip_exif(data, mime_type)


__all__ = [
    "ExifStripper",
    "is_strippable_format",
    "is_unsupported_photo_format",
    "strip_exif",
    "strip_exif_of_stored_object",
]
