"""Colour of a plant marker by growth phase — the Python reference (REQ-053 GP-FR-067, GP-UX-005, GP-UX-060).

The phase's *name* decides (``growth_phases.name``), so the same phase has the same colour in every bed, on the
screen and on paper. ``features/gardenPlanner/planting/phaseColors.ts`` is the TypeScript port; both run against the
``phase_color`` vectors in ``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (§19.6).

**The algorithm, specified so both sides compute the same value:**

1. *Named phases.* The name is lower-cased and every character outside ``a``…``z`` is dropped
   (``" Flowering "`` and ``"FLOWERING"`` → ``flowering``). A hit in :data:`PHASE_COLORS` is the colour.
2. *Any other name* takes a colour from :data:`FALLBACK_PALETTE` by a 32-bit string hash of the **unnormalised**
   name: ``h = 0``; for every UTF-16 code unit ``c`` of the name ``h = int32(h * 31 + c)`` (two's-complement
   wrap-around, JavaScript's ``| 0``); the colour is ``FALLBACK_PALETTE[abs(h) % len(FALLBACK_PALETTE)]``.

Every intermediate of step 2 stays below 2^53, so a JavaScript ``number`` computes it exactly and the two sides
agree bit for bit. The result is always ``#RRGGBB`` — a paint the SVG writer's allowlist accepts.
"""

from __future__ import annotations

import re
from typing import Final

#: Colour per normalised phase name.
PHASE_COLORS: Final[dict[str, str]] = {
    "germination": "#81C784",
    "seedling": "#66BB6A",
    "vegetative": "#43A047",
    "flowering": "#AB47BC",
    "harvest": "#EF5350",
    "drying": "#FF7043",
    "curing": "#FFA726",
    "flushing": "#42A5F5",
    "ripening": "#FF8A65",
    "cloning": "#26A69A",
}

#: Colours for every other phase name, picked by the name's hash.
FALLBACK_PALETTE: Final[tuple[str, ...]] = (
    "#7E57C2",
    "#5C6BC0",
    "#29B6F6",
    "#26C6DA",
    "#66BB6A",
    "#D4E157",
    "#FFCA28",
    "#FFA726",
    "#EC407A",
    "#78909C",
)

_NOT_A_TO_Z: Final = re.compile(r"[^a-z]")
_INT32_SPAN: Final = 1 << 32
_INT32_MAX: Final = (1 << 31) - 1


def normalised_phase_name(name: str) -> str:
    """The lookup key of ``name``: lower case, letters ``a``…``z`` only."""
    return _NOT_A_TO_Z.sub("", name.lower())


def _int32(value: int) -> int:
    """``value`` wrapped to a signed 32-bit integer, as JavaScript's ``value | 0``."""
    wrapped = value % _INT32_SPAN
    return wrapped - _INT32_SPAN if wrapped > _INT32_MAX else wrapped


def name_hash(name: str) -> int:
    """The signed 32-bit hash of ``name`` over its UTF-16 code units (``h = int32(h * 31 + c)``)."""
    units = name.encode("utf-16-le", "surrogatepass")
    hashed = 0
    for index in range(0, len(units), 2):
        hashed = _int32(hashed * 31 + int.from_bytes(units[index : index + 2], "little"))
    return hashed


def phase_color(name: str) -> str:
    """The marker colour of the phase called ``name`` (``#RRGGBB``)."""
    known = PHASE_COLORS.get(normalised_phase_name(name))
    if known is not None:
        return known
    return FALLBACK_PALETTE[abs(name_hash(name)) % len(FALLBACK_PALETTE)]


__all__ = ["FALLBACK_PALETTE", "PHASE_COLORS", "name_hash", "normalised_phase_name", "phase_color"]
