"""REQ-048 Stufe 1 — canonical scientific-name normalization.

The single source of truth for turning a botanical ``scientific_name`` into a
canonical deduplication key. Two spellings that a human treats as the same
taxon — ``Fragaria × ananassa`` (U+00D7 multiplication sign) and
``Fragaria x ananassa`` (ASCII ``x``), or differences in casing / whitespace —
must collapse onto one key so the identify→create path never accumulates
duplicate species ("Datenleichen", Issue #436).

This is a pure, side-effect-free helper (no I/O, no persistence). It is consumed
by the Species model (deriving the persisted ``scientific_name_normalized`` key),
the identification engine, the species service, the ArangoDB repository lookup
and the backfill migration — nobody re-implements the rules locally
(``photo_quality_assessor`` also delegates here).

The normalized value is an *internal* key only; it is never displayed. The
human-facing ``scientific_name`` keeps its original spelling (REQ-048 R3).
"""

from __future__ import annotations

import re

#: U+00D7 MULTIPLICATION SIGN — the botanical hybrid marker (× ananassa,
#: ×ananassa, or the genus-hybrid prefix × Chitalpa).
_HYBRID_SIGN = "×"

#: Collapses any run of whitespace to a single space.
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_scientific_name(name: str) -> str:
    """Return the canonical dedup key for a botanical scientific name.

    Rules (REQ-048 Stufe 1 §2 / R1):

    * **Hybrid marker** — every U+00D7 ``×`` (whether the infix hybrid marker
      ``× ananassa`` / ``×ananassa`` or the leading genus-hybrid prefix
      ``× Chitalpa``) collapses onto a space-padded ASCII ``x``. Padding with
      spaces means the attached (``×ananassa``) and the spaced (``× ananassa``)
      forms yield the same token once the whitespace below is collapsed, and both
      match the plain ASCII ``x`` spelling. A regular letter ``x`` inside a name
      (``Maxillaria``) is never touched — only the U+00D7 sign is rewritten.
    * **Casing** — ``casefold()`` for robust, locale-independent lowercasing.
    * **Whitespace** — internal runs collapse to one space; leading/trailing
      whitespace is stripped.

    The genus-hybrid prefix is preserved (unified to a leading ``x``), not
    dropped: a nothogenus (``× Chitalpa``) is a distinct taxon from its parent
    genus and must not collapse onto it.

    Args:
        name: The raw scientific name (any spelling of the hybrid marker/casing).

    Returns:
        The canonical, lower-case, whitespace-normalized dedup key. An empty or
        whitespace-only input returns ``""``.
    """
    # Unify the hybrid marker first (space-padded so attached/spaced forms merge),
    # then lower-case and collapse the resulting whitespace.
    unified = name.replace(_HYBRID_SIGN, " x ")
    return _WHITESPACE_RE.sub(" ", unified.casefold()).strip()


__all__ = ["normalize_scientific_name"]
