"""NFR-013 §4.3 — deterministic storage-key construction.

Object keys follow the scheme::

    t/{tenant_key}/{category}/{yyyy}/{mm}/{ulid}.{ext}

The date partition (``yyyy/mm``) comes from the attachment's ``created_at``
(UTC). The extension is **always** derived from the MIME type, never from the
client-supplied filename — a ``.jpg`` upload that is really a PNG is stored
with a ``.png`` key so the key never lies about its content.

The ULID is a 26-char Crockford-Base32 string (48-bit millisecond timestamp +
80 bits of randomness). We implement it inline rather than adding a dependency.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from app.common.enums import AttachmentCategory

# MIME → file extension (no leading dot). The closed whitelist mirrors
# NFR-013 §5.2 allowed types.
MIME_TO_EXTENSION: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
    "image/heif": "heic",
    "image/gif": "gif",
    "application/pdf": "pdf",
    "text/csv": "csv",
    "application/zip": "zip",
}

# Crockford Base32 alphabet (excludes I, L, O, U to avoid ambiguity).
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_crockford(value: int, length: int) -> str:
    chars = []
    for _ in range(length):
        chars.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def generate_ulid(timestamp_ms: int | None = None) -> str:
    """Return a 26-char Crockford-Base32 ULID.

    Layout: 48-bit millisecond timestamp (10 chars) + 80-bit randomness
    (16 chars). Lexicographically sortable by creation time, which keeps a
    listing roughly chronological without a secondary index.
    """
    if timestamp_ms is None:
        timestamp_ms = int(datetime.now(UTC).timestamp() * 1000)
    timestamp_ms &= (1 << 48) - 1
    randomness = int.from_bytes(os.urandom(10), "big")  # 80 bits
    return _encode_crockford(timestamp_ms, 10) + _encode_crockford(randomness, 16)


class StorageKeyBuilder:
    """Build object-storage keys (NFR-013 §4.3)."""

    def extension_for_mime(self, mime_type: str) -> str:
        """Return the canonical extension for ``mime_type``.

        Raises:
            ValueError: when the MIME type is not in the allowed whitelist.
        """
        ext = MIME_TO_EXTENSION.get(mime_type.lower().strip())
        if ext is None:
            raise ValueError(f"No extension mapping for MIME type '{mime_type}'.")
        return ext

    def build(
        self,
        *,
        tenant_key: str,
        category: AttachmentCategory,
        mime_type: str,
        created_at: datetime | None = None,
        ulid: str | None = None,
    ) -> str:
        """Construct the canonical object key for a new attachment.

        ``created_at`` drives the ``yyyy/mm`` partition (UTC); ``ulid`` lets the
        caller reuse a pre-generated ULID (e.g. to share the stem with
        thumbnails). The extension is always derived from ``mime_type``.
        """
        if created_at is None:
            created_at = datetime.now(UTC)
        elif created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        created_at = created_at.astimezone(UTC)

        ext = self.extension_for_mime(mime_type)
        ulid = ulid or generate_ulid(int(created_at.timestamp() * 1000))
        category_value = category.value if isinstance(category, AttachmentCategory) else str(category)
        return f"t/{tenant_key}/{category_value}/{created_at.year:04d}/{created_at.month:02d}/{ulid}.{ext}"

    @staticmethod
    def ulid_from_key(storage_key: str) -> str:
        """Extract the ULID stem from a storage key (drops the extension)."""
        filename = storage_key.rsplit("/", 1)[-1]
        return filename.rsplit(".", 1)[0]


__all__ = ["MIME_TO_EXTENSION", "StorageKeyBuilder", "generate_ulid"]
