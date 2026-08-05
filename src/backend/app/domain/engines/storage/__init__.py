"""NFR-013 — storage-pipeline engines.

Pure, dependency-light engines used by the ``AttachmentService`` upload
pipeline (NFR-013 §5.1):

- :class:`MagicByteValidator` — content-vs-declared-MIME sniffing.
- :class:`ExifStripper` — Pillow-based EXIF/GPS metadata removal.
- :class:`ThumbnailGenerator` — WEBP thumbnail rendition generation; renditions
  are enforced metadata-free (NFR-013 §8.2), which is what allows them to be
  delivered to third parties (REQ-050 §4.4) where the original may not be.
- :class:`StorageKeyBuilder` — deterministic object-key construction.
"""

from app.domain.engines.storage.exif_stripper import ExifStripper
from app.domain.engines.storage.magic_byte_validator import MagicByteValidator
from app.domain.engines.storage.storage_key_builder import (
    MIME_TO_EXTENSION,
    StorageKeyBuilder,
    generate_ulid,
)
from app.domain.engines.storage.thumbnail_generator import (
    THUMBNAIL_SIZES,
    ThumbnailGenerator,
    ThumbnailMetadataError,
    metadata_keys,
)

__all__ = [
    "MIME_TO_EXTENSION",
    "THUMBNAIL_SIZES",
    "ExifStripper",
    "MagicByteValidator",
    "StorageKeyBuilder",
    "ThumbnailGenerator",
    "ThumbnailMetadataError",
    "generate_ulid",
    "metadata_keys",
]
