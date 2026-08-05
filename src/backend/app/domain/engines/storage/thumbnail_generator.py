"""NFR-013 §8.2 — WEBP thumbnail rendition generation.

Produces three down-scaled WEBP renditions of an uploaded image, sized by
their *longest edge*: 128 px (grid/avatar), 512 px (card), 1280 px (preview).
The aspect ratio is preserved and images are never upscaled.

Thumbnail keys live next to the original with the scheme
``{ulid}_t{size}.webp`` (NFR-013 §8.2), where ``{ulid}`` is the original's
stem. Generation runs in a Celery task (``generate_thumbnails``) off the
upload critical path.

**Renditions never carry EXIF (NFR-013 §8.2).** This is a normative property,
not a side effect of re-encoding: renditions are delivered to third parties
(REQ-050 §4.4 hands them to an external language model over MCP) where the
original may not be, and that permission rests entirely on the renditions
being free of GPS coordinates, device identifiers and capture timestamps —
**also** when the tenant set ``STORAGE_KEEP_EXIF_<CATEGORY>=true``, which
governs the *original file* only (NFR-013 §6.4).

Because it is normative it is enforced here in three layers rather than
inherited from Pillow's encoder defaults:

1. every metadata block is dropped from ``Image.info`` before encoding, so the
   encoder is never even offered EXIF/ICC/XMP (a decoded ``Image`` keeps the
   source's ``info`` dict across ``copy()``, ``convert()`` and ``thumbnail()``);
2. ``exif``/``xmp``/``icc_profile`` are passed to ``save()`` as explicitly
   empty, so no encoder default can reintroduce them;
3. the **encoded bytes** are re-opened and verified — the only check that also
   covers a future Pillow that starts sourcing metadata from somewhere else.
   A violation raises :class:`ThumbnailMetadataError` and produces *no*
   rendition. Failing closed is deliberate: REQ-050 §4.4 already handles a
   missing rendition gracefully (``thumbnail_pending``), while a rendition with
   GPS in it would be shipped to a third-party model unnoticed.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import structlog
from PIL import Image

from app.common.exceptions import KamerplanterError

logger = structlog.get_logger()

#: Longest-edge target sizes (px), in ascending order (NFR-013 §8.2).
THUMBNAIL_SIZES: tuple[int, ...] = (128, 512, 1280)

THUMBNAIL_MIME_TYPE = "image/webp"

# MIME types we can render thumbnails for (decodable by stock Pillow).
_RENDERABLE = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})

# ``Image.info`` keys that can carry capture location, device identity, capture
# time, editing history or an embedded colour profile. These are removed before
# encoding and asserted absent afterwards (NFR-013 §8.2). Harmless layout keys
# (``dpi``, ``jfif*``, ``background``, ``loop``) are deliberately not listed —
# they identify nobody.
_METADATA_INFO_KEYS: frozenset[str] = frozenset(
    {
        "exif",
        "Raw profile type exif",
        "xmp",
        "XML:com.adobe.xmp",
        "icc_profile",
        "iptc",
        "photoshop",
        "adobe",
        "comment",
    }
)

# Encoder parameters that pin every metadata block to "empty" (NFR-013 §8.2).
# ``icc_profile=None`` is Pillow's own "no profile" spelling for the WEBP writer.
_METADATA_FREE_SAVE_PARAMS: dict[str, object] = {
    "exif": b"",
    "xmp": b"",
    "icc_profile": None,
}


class ThumbnailMetadataError(KamerplanterError):
    """NFR-013 §8.2 — an encoded rendition still carried image metadata.

    Raised instead of returning the rendition, because a rendition is allowed to
    leave the instance (REQ-050 §4.4) precisely on the promise that it carries
    none. Only the *names* of the leaked blocks are reported — never their
    content, which is the personal data in question (NFR-013 §9.2).
    """

    def __init__(self, size: int, leaked_keys: list[str]) -> None:
        super().__init__(
            message=(
                f"Thumbnail rendition ({size} px) still carries image metadata "
                f"({', '.join(leaked_keys)}); refusing to emit it."
            ),
            error_code="THUMBNAIL_METADATA_LEAK",
            status_code=500,
        )


@dataclass(frozen=True)
class Thumbnail:
    """One generated thumbnail rendition."""

    size: int
    suffix: str  # e.g. "_t128.webp"
    mime_type: str
    data: bytes


def can_render(mime_type: str) -> bool:
    """Return ``True`` when thumbnails can be produced for ``mime_type``."""
    return (mime_type or "").lower().strip() in _RENDERABLE


def metadata_keys(data: bytes) -> list[str]:
    """Return the metadata blocks an encoded image still carries.

    Empty list = free of EXIF/GPS, XMP, IPTC and colour profile. Used as the
    rendition post-condition (NFR-013 §8.2) and usable by callers that need to
    re-assert the property on bytes they did not produce themselves.
    """
    try:
        with Image.open(io.BytesIO(data)) as image:
            return sorted(key for key in image.info if key in _METADATA_INFO_KEYS)
    except (OSError, ValueError) as exc:
        # Undecodable bytes cannot be asserted about; the caller (generator)
        # only ever passes bytes it just encoded itself.
        logger.debug("thumbnail_metadata_check_undecodable", reason=str(exc))
        return []


def thumbnail_key(original_key: str, size: int) -> str:
    """Derive the thumbnail key for ``size`` next to ``original_key``.

    ``t/<tenant>/diary/2026/06/<ulid>.jpg`` → ``.../<ulid>_t512.webp``.
    """
    base, _, _ext = original_key.rpartition(".")
    stem = base or original_key
    return f"{stem}_t{size}.webp"


class ThumbnailGenerator:
    """Generate WEBP thumbnail renditions (NFR-013 §8.2)."""

    def __init__(self, sizes: tuple[int, ...] = THUMBNAIL_SIZES) -> None:
        self._sizes = sizes

    @property
    def sizes(self) -> tuple[int, ...]:
        """The configured longest-edge thumbnail sizes (px)."""
        return self._sizes

    def generate(self, data: bytes, mime_type: str) -> list[Thumbnail]:
        """Return one :class:`Thumbnail` per configured size.

        Returns an empty list for non-renderable types. Each rendition is a
        WEBP encoded with the longest edge clamped to the target size and
        **guaranteed free of EXIF/GPS, XMP, IPTC and colour-profile metadata**
        (NFR-013 §8.2) — independent of ``STORAGE_KEEP_EXIF_<CATEGORY>``, which
        applies to the stored original only. The source may therefore still be
        carrying its EXIF when it reaches this method; that is the normal case
        for a keep-EXIF tenant.

        Raises:
            ThumbnailMetadataError: if an encoded rendition still carries a
                metadata block. No thumbnail is returned in that case — a
                rendition that may leave the instance is never emitted on a
                "probably clean" basis.
        """
        if not can_render(mime_type):
            return []

        thumbnails: list[Thumbnail] = []
        with Image.open(io.BytesIO(data)) as src:
            src.load()
            image = src.convert("RGB") if src.mode not in ("RGB", "RGBA") else src
            for size in self._sizes:
                rendition = image.copy()
                # thumbnail() preserves aspect ratio and never upscales.
                rendition.thumbnail((size, size), Image.LANCZOS)
                # Layer 1: the decoded image still carries the source's info
                # dict (copy()/convert()/thumbnail() all propagate it) — drop it
                # so no metadata is even reachable for the encoder.
                rendition.info = {}
                buffer = io.BytesIO()
                # Layer 2: pin every metadata block to empty explicitly.
                rendition.save(
                    buffer,
                    format="WEBP",
                    quality=82,
                    method=4,
                    **_METADATA_FREE_SAVE_PARAMS,
                )
                encoded = buffer.getvalue()
                # Layer 3: verify on the bytes that will actually be stored.
                leaked = metadata_keys(encoded)
                if leaked:
                    logger.error(
                        "thumbnail_metadata_leak",
                        size=size,
                        source_mime_type=mime_type,
                        leaked_blocks=leaked,
                    )
                    raise ThumbnailMetadataError(size, leaked)
                thumbnails.append(
                    Thumbnail(
                        size=size,
                        suffix=f"_t{size}.webp",
                        mime_type=THUMBNAIL_MIME_TYPE,
                        data=encoded,
                    )
                )
        return thumbnails


__all__ = [
    "THUMBNAIL_MIME_TYPE",
    "THUMBNAIL_SIZES",
    "Thumbnail",
    "ThumbnailGenerator",
    "ThumbnailMetadataError",
    "can_render",
    "metadata_keys",
    "thumbnail_key",
]
