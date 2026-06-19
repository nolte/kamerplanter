"""NFR-013 §8.2 — WEBP thumbnail rendition generation.

Produces three down-scaled WEBP renditions of an uploaded image, sized by
their *longest edge*: 128 px (grid/avatar), 512 px (card), 1280 px (preview).
The aspect ratio is preserved and images are never upscaled.

Thumbnail keys live next to the original with the scheme
``{ulid}_t{size}.webp`` (NFR-013 §8.2), where ``{ulid}`` is the original's
stem. Generation runs in a Celery task (``generate_thumbnails``) off the
upload critical path.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import structlog
from PIL import Image

logger = structlog.get_logger()

#: Longest-edge target sizes (px), in ascending order (NFR-013 §8.2).
THUMBNAIL_SIZES: tuple[int, ...] = (128, 512, 1280)

THUMBNAIL_MIME_TYPE = "image/webp"

# MIME types we can render thumbnails for (decodable by stock Pillow).
_RENDERABLE = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})


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
        WEBP encoded with the longest edge clamped to the target size.
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
                buffer = io.BytesIO()
                rendition.save(buffer, format="WEBP", quality=82, method=4)
                thumbnails.append(
                    Thumbnail(
                        size=size,
                        suffix=f"_t{size}.webp",
                        mime_type=THUMBNAIL_MIME_TYPE,
                        data=buffer.getvalue(),
                    )
                )
        return thumbnails


__all__ = [
    "THUMBNAIL_MIME_TYPE",
    "THUMBNAIL_SIZES",
    "Thumbnail",
    "ThumbnailGenerator",
    "can_render",
    "thumbnail_key",
]
