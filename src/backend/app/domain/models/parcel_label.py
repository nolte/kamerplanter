"""The parcel label of a location (REQ-053 GP-FR-176, §32.6 Pkt. 8; operator decision of 2026-11-14 on #2759).

An optional, user-editable short text on a location - typically the number of an allotment parcel ("A-17",
"Parzelle 12") - that stays the same across prints, unlike the running number the parcel list counts per print.
Where it is set, it **is** the bed's identifier on the parcel list (PDF) and fills the bed list's ``parcel_label``
column (CSV); where it is not, the per-print running number plus the bed name stays the fallback.

The value is one line of at most :data:`PARCEL_LABEL_MAX_CHARS` characters without control or bidi format
characters (like a plan caption, :func:`~app.domain.models.garden_object.text_label_error`): it is printed into a
table cell and a CSV cell, where a line break or a reversed text would show something other than what is stored.
Surrounding whitespace is stripped; an empty or blank value is no label (``None``).
"""

from __future__ import annotations

import unicodedata
from typing import Annotated, Final

from pydantic import BeforeValidator

from app.domain.models.garden_object import BIDI_FORMAT_CHARS

#: Longest parcel label: a parcel number or short code, never a note (``name`` holds 200, ``label`` of a caption 80).
PARCEL_LABEL_MAX_CHARS: Final = 40


def parcel_label_error(text: str) -> str | None:
    """Why ``text`` (already stripped, not empty) is no parcel label, or ``None``: too long, a control character."""
    if len(text) > PARCEL_LABEL_MAX_CHARS:
        return f"A parcel label holds at most {PARCEL_LABEL_MAX_CHARS} characters, got {len(text)}."
    for char in text:
        if unicodedata.category(char) in {"Cc", "Zl", "Zp"} or char in BIDI_FORMAT_CHARS:
            return f"A parcel label is one line of text without control characters (U+{ord(char):04X})."
    return None


def normalize_parcel_label(value: object) -> object:
    """The stored form of a parcel label: stripped, blank → ``None``; a refused text raises ``ValueError``.

    Anything that is not a string is passed on unchanged, so the field's type check refuses it as usual.
    """
    if not isinstance(value, str):
        return value
    return _stored_label(value)


def _stored_label(value: str) -> str | None:
    """``value`` stripped, ``None`` when blank; ``ValueError`` when it breaks a rule of :func:`parcel_label_error`."""
    text = value.strip()
    if not text:
        return None
    error = parcel_label_error(text)
    if error is not None:
        raise ValueError(error)
    return text


#: The field type of ``parcel_label`` on the location, its PATCH bodies and the plan file.
ParcelLabel = Annotated[str | None, BeforeValidator(normalize_parcel_label)]

__all__ = ["PARCEL_LABEL_MAX_CHARS", "ParcelLabel", "normalize_parcel_label", "parcel_label_error"]
