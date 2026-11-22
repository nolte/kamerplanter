"""Window orientation and the sun window it suggests for nearby locations (REQ-053 §9.8, GP-FR-181, WP 10.7).

Pure functions, no I/O. They are the reference of ``features/gardenPlanner/model/windowOrientation.ts``; both run
against the operations ``window_facing`` and ``window_sun_window`` of
``spec/e2e-testcases/fixtures/garden-plan-vectors.json``.

**Which way a window faces** (:func:`window_facing`). A window is a line in the wall (GardenObject ``window``,
polyline). Its wall direction is the chord from the first to the last vertex; the window faces along the normal of
that chord that points **outside**, as a compass azimuth (0 = north, clockwise) derived with the plan's
``north_angle_deg`` (GP-FR-015). Which side is outside is decided by the site outline (``SitePlan.boundary``): two
probes :data:`OUTSIDE_PROBE_M` from the chord midpoint, one along each normal; when exactly one of them lies inside the
outline, the other side is outside (:attr:`FacingBasis.BOUNDARY`). Without an outline, or when both or neither probe
lies inside (a window in an inner wall, a window beyond the outline), the drawing direction decides by convention:
**outside is left of the drawing direction** - walls traced clockwise on screen keep the room on their right
(:attr:`FacingBasis.DRAWING_DIRECTION`). The azimuth is rounded to 0.1 degree like ``north_angle_deg`` and falls into
one of eight sectors through :func:`~app.domain.calculators.orientation_calculator.orientation_from_aspect` - the
one sector definition of the code base, half-open.

**What it suggests** (:func:`suggest_sun_window`, agrobiology review 2026-11-11). Northern hemisphere: a north window
gets no direct sun (it contributes nothing, hint ``diffuse_light_only``); northeast, east and southeast give
``morning``; south ``midday``; southwest, west and northwest ``afternoon``. South of the equator the azimuth is
mirrored first, ``a -> (180 - a) mod 360``. Without a latitude the northern hemisphere is assumed and said
(``hemisphere_assumed``); between the tropics (``|latitude| < 23.5``) the sun stands high on both sides over the
year and nothing is suggested (``tropics``). Several windows: the set of their contributions - empty gives nothing,
one value that value, morning + midday + afternoon ``all_day``, every other combination ``mixed``; no distance
weighting, and a single window never gives ``all_day``.

Only ``sun_profile.sun_window`` is suggested: no hours of sun, no leaf shade, no ``sun_exposure``, no PPFD/lux/DLI -
a window says when the sun can come in, not how much of it reaches the plant. The caveats every suggestion carries
(shading by buildings and trees and the storey not considered, the season, the distance to the window, the glass)
say so to the user. The suggestion is never written on its own: the user confirms it (GP-FR-181, G-W10 c).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Final

from app.common.enums import Orientation, SunWindow
from app.domain.calculators.geometry_calculator import CircleShape, point_in_polygon, to_shape
from app.domain.calculators.orientation_calculator import FULL_TURN_DEG, orientation_from_aspect
from app.domain.models.geometry import Geometry, PolylineGeometry

#: How far from the window the two sides are probed against the outline, metres: wider than a wall drawn on its
#: inner or outer face, narrower than a room.
OUTSIDE_PROBE_M: Final = 0.5
#: Between the tropics (``|latitude| < TROPIC_LATITUDE_DEG``) the sun passes north and south of the zenith over the
#: year; a window direction says nothing about the time of day.
TROPIC_LATITUDE_DEG: Final = 23.5
#: Default radius around a window within which a location takes it into account, metres (GP-FR-181).
DEFAULT_WINDOW_SUGGESTION_RADIUS_M: Final = 1.5


class FacingBasis(StrEnum):
    """How the outside of a window was found."""

    #: The site outline told the outside from the inside.
    BOUNDARY = "boundary"
    #: Convention: outside is left of the drawing direction.
    DRAWING_DIRECTION = "drawing_direction"


class WindowHint(StrEnum):
    """Why a suggestion is limited or missing; the UI shows one text per code. The order is the display order."""

    HEMISPHERE_ASSUMED = "hemisphere_assumed"
    TROPICS = "tropics"
    NO_WINDOW = "no_window"
    DIFFUSE_LIGHT_ONLY = "diffuse_light_only"
    SHADING_NOT_CONSIDERED = "shading_not_considered"
    SEASON = "season"
    WINDOW_DISTANCE = "window_distance"
    GLAZING = "glazing"


#: The caveats every suggestion carries.
SUGGESTION_CAVEATS: Final[tuple[WindowHint, ...]] = (
    WindowHint.SHADING_NOT_CONSIDERED,
    WindowHint.SEASON,
    WindowHint.WINDOW_DISTANCE,
    WindowHint.GLAZING,
)

#: Northern-hemisphere table; ``None`` = no direct sun (diffuse light only).
_SUN_WINDOW_BY_ORIENTATION: Final[dict[Orientation, SunWindow | None]] = {
    Orientation.NORTH: None,
    Orientation.NORTHEAST: SunWindow.MORNING,
    Orientation.EAST: SunWindow.MORNING,
    Orientation.SOUTHEAST: SunWindow.MORNING,
    Orientation.SOUTH: SunWindow.MIDDAY,
    Orientation.SOUTHWEST: SunWindow.AFTERNOON,
    Orientation.WEST: SunWindow.AFTERNOON,
    Orientation.NORTHWEST: SunWindow.AFTERNOON,
}
_ALL_DAY_PARTS: Final = frozenset({SunWindow.MORNING, SunWindow.MIDDAY, SunWindow.AFTERNOON})


@dataclass(frozen=True)
class WindowFacing:
    """The direction a window faces: compass azimuth (0.1 degree), its sector and how the outside was found."""

    azimuth_deg: float
    orientation: Orientation
    basis: FacingBasis


@dataclass(frozen=True)
class SunWindowSuggestion:
    """The suggested sun window (``None`` = no suggestion) and the hint codes, in display order."""

    sun_window: SunWindow | None
    hints: tuple[WindowHint, ...]


def round_azimuth(azimuth_deg: float) -> float:
    """Wrap into ``[0, 360)`` and round to 0.1 degree, ties away from zero (the TypeScript ``toFixed(1)``)."""
    wrapped = azimuth_deg % FULL_TURN_DEG
    rounded = float(Decimal(wrapped).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    return 0.0 if rounded >= FULL_TURN_DEG else rounded


def _inside(point: tuple[float, float], boundary: Geometry) -> bool:
    shape = to_shape(boundary)
    if isinstance(shape, CircleShape):
        return math.hypot(point[0] - shape.center[0], point[1] - shape.center[1]) < shape.radius_m
    if not shape.closed:
        return False
    return point_in_polygon(point, shape.vertices)


def window_facing(window: Geometry, north_angle_deg: float, boundary: Geometry | None = None) -> WindowFacing | None:
    """The direction *window* faces, or ``None`` when it is no line or its chord has no length."""
    if not isinstance(window, PolylineGeometry):
        return None
    (x1, y1), (x2, y2) = window.points[0], window.points[-1]
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return None
    # The two normals in the plan frame (y up): left of the drawing direction and right of it.
    left = (-dy / length, dx / length)
    right = (dy / length, -dx / length)
    outward, basis = left, FacingBasis.DRAWING_DIRECTION
    if boundary is not None:
        mid = ((x1 + x2) / 2, (y1 + y2) / 2)
        left_inside = _inside((mid[0] + left[0] * OUTSIDE_PROBE_M, mid[1] + left[1] * OUTSIDE_PROBE_M), boundary)
        right_inside = _inside((mid[0] + right[0] * OUTSIDE_PROBE_M, mid[1] + right[1] * OUTSIDE_PROBE_M), boundary)
        if left_inside != right_inside:
            outward = right if left_inside else left
            basis = FacingBasis.BOUNDARY
    # Mathematical angle of the normal (counter-clockwise from +x) -> compass azimuth relative to plan north.
    theta_deg = math.atan2(outward[1], outward[0]) * 180.0 / math.pi
    azimuth = round_azimuth(90.0 - theta_deg - north_angle_deg)
    return WindowFacing(azimuth_deg=azimuth, orientation=orientation_from_aspect(azimuth), basis=basis)


def contribution(azimuth_deg: float, latitude: float | None) -> SunWindow | None:
    """What one window facing *azimuth_deg* contributes outside the tropics; ``None`` = diffuse light only."""
    mapped = (180.0 - azimuth_deg) % FULL_TURN_DEG if latitude is not None and latitude < 0 else azimuth_deg
    return _SUN_WINDOW_BY_ORIENTATION[orientation_from_aspect(mapped)]


def is_tropical(latitude: float | None) -> bool:
    """Whether *latitude* lies between the tropics; an unknown latitude is not (the northern hemisphere is assumed)."""
    return latitude is not None and abs(latitude) < TROPIC_LATITUDE_DEG


def suggest_sun_window(azimuths: list[float] | tuple[float, ...], latitude: float | None) -> SunWindowSuggestion:
    """The sun window the windows facing *azimuths* suggest at *latitude* (``Site.gps_coordinates[0]``)."""
    hints: list[WindowHint] = []
    if latitude is None:
        hints.append(WindowHint.HEMISPHERE_ASSUMED)
    if is_tropical(latitude):
        return SunWindowSuggestion(None, (*hints, WindowHint.TROPICS))
    if not azimuths:
        return SunWindowSuggestion(None, (*hints, WindowHint.NO_WINDOW))
    contributions = [contribution(azimuth, latitude) for azimuth in azimuths]
    if None in contributions:
        hints.append(WindowHint.DIFFUSE_LIGHT_ONLY)
    values = {value for value in contributions if value is not None}
    if not values:
        return SunWindowSuggestion(None, tuple(hints))
    if len(values) == 1:
        suggested = next(iter(values))
    elif values >= _ALL_DAY_PARTS:
        suggested = SunWindow.ALL_DAY
    else:
        suggested = SunWindow.MIXED
    return SunWindowSuggestion(suggested, (*hints, *SUGGESTION_CAVEATS))
