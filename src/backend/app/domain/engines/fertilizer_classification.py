"""Structural fertilizer classification helpers (REQ-004-A §5, DOM-6).

Central place for deciding whether a fertilizer is a CalMag supplement, a
sulfate-bearing product, or a silicate. The primary signal is the structured
``FertilizerType`` enum; a *normalized* product-name fallback keeps legacy
tenant data (not yet reclassified) working — e.g. "Cal-Mag" and "CaliMagic"
are recognised where a naive substring check ("calmag"/"calcium") failed.

REQ-004-A Z. 457 already mandates type-based silicate detection; this module
extends that same structural pattern to CalMag and sulfates.
"""

import re

from app.common.enums import FertilizerType
from app.domain.models.fertilizer import Fertilizer

# Normalized name fragments (lowercase, alphanumerics only) that identify a
# CalMag supplement when no structured type is set. "camg" covers "Ca/Mg" and
# "CaMg" style names once normalization strips the separators.
_CALMAG_NAME_PATTERNS: tuple[str, ...] = ("calmag", "calimagic", "camg")

# Sulfate-bearing product name fragments (Epsom salt / "Bittersalz" = MgSO4).
_SULFATE_NAME_PATTERNS: tuple[str, ...] = ("sulfat", "sulfate", "epsom", "bittersalz")

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_name(name: str) -> str:
    """Lowercase a product name and strip every non-alphanumeric character.

    ``"Cal-Mag Plus"`` -> ``"calmagplus"``, ``"CaliMagic"`` -> ``"calimagic"``.
    """
    return _NON_ALNUM_RE.sub("", name.lower())


def matches_calmag_name(name: str) -> bool:
    """Return True if a product *name* alone identifies a CalMag supplement.

    The bare "calcium" token is intentionally *not* a standalone match to avoid
    false positives (e.g. "Calcium Nitrate" is a base fertilizer, not a CalMag),
    but "calcium ... magnesium" style names still match.
    """
    normalized = normalize_name(name)
    if any(pattern in normalized for pattern in _CALMAG_NAME_PATTERNS):
        return True
    return "calcium" in normalized and "magnesium" in normalized


def is_calmag(fert: Fertilizer) -> bool:
    """Return True if the fertilizer is a CalMag supplement.

    Primary signal: ``fertilizer_type == FertilizerType.CALMAG``. Fallback: the
    normalized product name matches a known CalMag pattern (``matches_calmag_name``).
    """
    if fert.fertilizer_type == FertilizerType.CALMAG:
        return True
    return matches_calmag_name(fert.product_name)


def is_sulfate_bearing(fert: Fertilizer) -> bool:
    """Return True if the fertilizer carries sulfate (precipitation risk with Ca)."""
    normalized = normalize_name(fert.product_name)
    return any(pattern in normalized for pattern in _SULFATE_NAME_PATTERNS)


def is_silicate(fert: Fertilizer) -> bool:
    """Return True if the fertilizer is a silicate (REQ-004-A Z. 457, type-based)."""
    return fert.fertilizer_type == FertilizerType.SILICATE
