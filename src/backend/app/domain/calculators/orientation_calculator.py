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

**Orientation from the geometry (GP-FR-017).** Without an aspect, a placed bed's orientation is derived from its
geometry, ``rotation_deg`` and the plan's ``north_angle_deg`` - "aus ``rotation_deg`` + ``north_angle_deg``
**abgeleitet**" (REQ-053 §9.3, GP-FR-017), the successor of REQ-002's ``bed_orientation`` (north-south, east-west,
diagonal; §20.8). That is an **axis**, not a facing: the bed's long axis in its own frame (before ``rotation_deg``),

* ``rect`` - along ``+y`` when ``length_m > width_m``, along ``+x`` when ``width_m > length_m``;
* ``polygon`` - the longer side of its bounding box in its own frame (the stored points, before ``rotation_deg``),
  i.e. the polygon is read like the rectangle that encloses it there; extents compared at storage precision;
* ``circle``, a square and a polygon with a square bounding box - no long axis, nothing derived;

turned by ``rotation_deg`` (counter-clockwise) and read as a compass azimuth against ``north_angle_deg``
(:func:`bed_axis`). An axis has two ends, so its azimuth is folded into the half turn ``[0, 180)`` (0.1 degree,
like ``north_angle_deg``) and named by its end between north and southeast: a north-south axis is ``north``, a
northeast-southwest axis ``northeast``, an east-west axis ``east``, a southeast-northwest axis ``southeast``. The
same eight half-open sectors as above; the south sector of the half turn (``[157.5, 180)``) is the north-south axis.

:func:`derived_orientation` puts the rules in order: a set ``aspect_deg`` wins (GP-FR-168), then the long axis of
the geometry, else nothing is derived and the manually maintained value stands. The axis rules are the reference of
``features/gardenPlanner/model/bedOrientation.ts``; both run against the operation ``bed_axis`` of
``spec/e2e-testcases/fixtures/garden-plan-vectors.json``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Final

from app.common.enums import Orientation
from app.domain.models.geometry import Geometry, PolygonGeometry, RectGeometry, round_length

#: A full turn in degrees.
FULL_TURN_DEG: Final = 360.0
#: An axis has two ends: its azimuth is folded into the half turn.
HALF_TURN_DEG: Final = 180.0
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


@dataclass(frozen=True)
class BedAxis:
    """The long axis of a bed: compass azimuth folded into ``[0, 180)`` (0.1 degree) and the sector naming it."""

    azimuth_deg: float
    orientation: Orientation


def _round_half_turn(azimuth_deg: float) -> float:
    """Fold into ``[0, 180)`` and round to 0.1 degree, ties away from zero (the TypeScript ``toFixed(1)``)."""
    folded = azimuth_deg % HALF_TURN_DEG
    rounded = float(Decimal(folded).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) + 0.0
    return 0.0 if rounded >= HALF_TURN_DEG else rounded


def _long_side(width: float, length: float) -> float | None:
    """The mathematical angle of the long side in the bed's own frame: 0 = ``+x``, 90 = ``+y``; ``None`` = square."""
    width, length = round_length(width), round_length(length)
    if width == length:
        return None
    return 0.0 if width > length else 90.0


def _own_frame_angle(geometry: Geometry) -> float | None:
    if isinstance(geometry, RectGeometry):
        return _long_side(geometry.width_m, geometry.length_m)
    if isinstance(geometry, PolygonGeometry):
        xs = [x for x, _ in geometry.points]
        ys = [y for _, y in geometry.points]
        return _long_side(max(xs) - min(xs), max(ys) - min(ys))
    return None


def orientation_from_axis(axis_deg: float) -> Orientation:
    """The sector naming an axis at *axis_deg*: its end between north and southeast (north-south is ``north``)."""
    sector = orientation_from_aspect(_round_half_turn(axis_deg))
    return Orientation.NORTH if sector is Orientation.SOUTH else sector


def bed_axis(geometry: Geometry, north_angle_deg: float) -> BedAxis | None:
    """The long axis of *geometry* as a compass direction on a plan whose north lies at *north_angle_deg*.

    ``None`` for a shape without a long axis (circle, square, a polygon with a square bounding box) and for any
    shape that encloses no area.
    """
    own = _own_frame_angle(geometry)
    if own is None:
        return None
    rotation = geometry.rotation_deg if isinstance(geometry, RectGeometry | PolygonGeometry) else 0.0
    # Mathematical angle (counter-clockwise from +x) -> compass azimuth relative to plan north, as window_facing.
    azimuth = _round_half_turn(90.0 - (own + rotation) - north_angle_deg)
    return BedAxis(azimuth_deg=azimuth, orientation=orientation_from_axis(azimuth))


def derived_orientation(
    aspect_deg: float | None, geometry: Geometry | None, north_angle_deg: float
) -> Orientation | None:
    """GP-FR-017/168: the aspect's sector, else the geometry's long axis, else ``None`` (the manual value stands)."""
    if aspect_deg is not None:
        return orientation_from_aspect(aspect_deg)
    if geometry is None:
        return None
    axis = bed_axis(geometry, north_angle_deg)
    return axis.orientation if axis is not None else None
