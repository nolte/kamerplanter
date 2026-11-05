"""Orientation of a bed from its aspect (REQ-053 GP-FR-017, GP-FR-168, WP 8.24).

A pure function, no I/O. ``SiteConditions.aspect_deg`` is the compass direction the bed slopes towards, clockwise
from geographic north (``0`` = north, ``90`` = east, ``180`` = south, ``270`` = west). It falls into one of eight
compass sectors of 45 degrees, each centred on its direction:

=========== ==============================
north       ``[337.5, 360)`` and ``[0, 22.5)``
northeast   ``[22.5, 67.5)``
east        ``[67.5, 112.5)``
southeast   ``[112.5, 157.5)``
south       ``[157.5, 202.5)``
southwest   ``[202.5, 247.5)``
west        ``[247.5, 292.5)``
northwest   ``[292.5, 337.5)``
=========== ==============================

A boundary belongs to the sector that **starts** there, clockwise: ``22.5`` is northeast, ``337.5`` is north.
"""

from __future__ import annotations

import math
from typing import Final

from app.common.enums import Orientation

#: A full turn in degrees.
FULL_TURN_DEG: Final = 360.0
#: Width of one compass sector: eight sectors share the full turn.
SECTOR_WIDTH_DEG: Final = 45.0

#: The sectors clockwise from north; index ``i`` is centred on ``i * 45`` degrees.
_SECTORS: Final[tuple[Orientation, ...]] = (
    Orientation.NORTH,
    Orientation.NORTHEAST,
    Orientation.EAST,
    Orientation.SOUTHEAST,
    Orientation.SOUTH,
    Orientation.SOUTHWEST,
    Orientation.WEST,
    Orientation.NORTHWEST,
)


def orientation_from_aspect(aspect_deg: float) -> Orientation:
    """The compass sector *aspect_deg* falls into; any finite angle is normalised to ``[0, 360)`` first.

    Raises:
        ValueError: *aspect_deg* is NaN or infinite - there is no direction to name.
    """
    if not math.isfinite(aspect_deg):
        raise ValueError(f"aspect_deg must be a finite angle, got {aspect_deg}.")
    normalised = aspect_deg % FULL_TURN_DEG
    index = int((normalised + SECTOR_WIDTH_DEG / 2) // SECTOR_WIDTH_DEG) % len(_SECTORS)
    return _SECTORS[index]
