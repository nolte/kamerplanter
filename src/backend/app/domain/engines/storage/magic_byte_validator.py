"""NFR-013 §5.1 step 3 — magic-byte content validation.

Verifies that the *actual* leading bytes of an upload match the *declared*
MIME type, defeating extension/Content-Type spoofing (a ``.jpg`` that is
really a ``.exe``, an HTML payload labelled ``image/png``, ...).

No ``libmagic`` / ``python-magic`` dependency: the signatures we accept are a
small, closed whitelist (NFR-013 §5.2 allowed types), so a hand-rolled
byte-signature table is both sufficient and dependency-free.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger()

# Number of leading bytes inspected. Binary signatures need only ~16 bytes;
# the larger window bounds the text/CSV UTF-8 decode to a cheap prefix so a
# multi-megabyte upload is never fully decoded just to sniff its type (SEC-008).
_SNIFF_LEN = 512


class MagicByteValidator:
    """Validate a byte prefix against the declared MIME type (NFR-013 §5.1)."""

    def is_valid(self, data: bytes, mime_type: str) -> bool:
        """Return ``True`` when ``data`` plausibly matches ``mime_type``.

        Only the first ``_SNIFF_LEN`` bytes are inspected; the service already
        passes a sliced prefix, but the slice here makes the bound hold for any
        caller. Unknown MIME types return ``False`` (deny by default) — the
        caller has already whitelisted the type, so a validator miss means an
        unexpected type slipped through.
        """
        checker = _SIGNATURE_CHECKS.get(mime_type)
        if checker is None:
            return False
        return checker(data[:_SNIFF_LEN])


# --- Per-type signature predicates --------------------------------------


def _check_jpeg(data: bytes) -> bool:
    # FF D8 FF
    return data[:3] == b"\xff\xd8\xff"


def _check_png(data: bytes) -> bool:
    # 89 50 4E 47 0D 0A 1A 0A
    return data[:8] == b"\x89PNG\r\n\x1a\n"


def _check_webp(data: bytes) -> bool:
    # "RIFF" .... "WEBP"
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def _check_gif(data: bytes) -> bool:
    # "GIF8" (covers GIF87a / GIF89a)
    return data[:4] == b"GIF8"


def _check_pdf(data: bytes) -> bool:
    # "%PDF"
    return data[:4] == b"%PDF"


def _check_zip(data: bytes) -> bool:
    # 50 4B 03 04 (also tolerate empty-archive 50 4B 05 06 / spanned 50 4B 07 08)
    return data[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


def _check_heic(data: bytes) -> bool:
    # ISO-BMFF: "ftyp" box at offset 4, brand at offset 8.
    if len(data) < 12 or data[4:8] != b"ftyp":
        return False
    brand = data[8:12]
    return brand in _HEIC_BRANDS


def _check_text_csv(data: bytes) -> bool:
    # No magic number for CSV/plain text. Accept when the prefix is valid
    # UTF-8 and contains no NUL byte (which would indicate a binary file).
    if b"\x00" in data:
        return False
    try:
        # Decode defensively: a truncated multibyte char at the chunk boundary
        # must not produce a false negative, so ignore a trailing partial.
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        # Tolerate a multibyte sequence cut at the very end of the sniff buffer.
        return exc.start >= len(data) - 3
    return True


_HEIC_BRANDS: frozenset[bytes] = frozenset(
    {
        b"heic",
        b"heix",
        b"heif",
        b"hevc",
        b"mif1",
        b"msf1",
    }
)

_SIGNATURE_CHECKS = {
    "image/jpeg": _check_jpeg,
    "image/png": _check_png,
    "image/webp": _check_webp,
    "image/gif": _check_gif,
    "image/heic": _check_heic,
    "image/heif": _check_heic,
    "application/pdf": _check_pdf,
    "application/zip": _check_zip,
    "text/csv": _check_text_csv,
    "text/plain": _check_text_csv,
}

__all__ = ["MagicByteValidator", "_SNIFF_LEN"]
