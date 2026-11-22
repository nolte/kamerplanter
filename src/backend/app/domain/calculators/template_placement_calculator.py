"""Place a bed template's default geometry on the plan (REQ-053 §21.7, GP-FR-044; WP 7.9, #2475).

A template's ``default_geometry`` is expressed in the **bed frame** (§9.2): its anchor - the lower-left corner of a
rectangle, the centre of a circle, the first vertex of a polygon - is the origin of its own frame and it carries its
own ``rotation_deg``. Placing it means putting that anchor at ``origin`` on the plan and turning the shape by
``rotation_deg`` on top of its own rotation. A circle has no rotation: the requested angle is without effect on it.

The result is the *raw* mapping of a plan-frame geometry, not a model: the service validates it with the rest of
the new bed (V-01 ranges), so a placement that leaves the plan frame is refused by the same rule as any batch.
Pure functions; Python is the reference and the TypeScript port follows it (the editor's ghost preview).
"""

from __future__ import annotations

from typing import Any

from app.domain.models.geometry import (
    FULL_TURN_DEG,
    CircleGeometry,
    Geometry,
    PolygonGeometry,
    RectGeometry,
    round_length,
)


def _turned(own: float, extra: float) -> float:
    """The template's own rotation plus the requested one, folded into ``[0, 360)``."""
    turned = round_length((own + extra) % FULL_TURN_DEG)
    return 0.0 if turned >= FULL_TURN_DEG else turned


def place_geometry(geometry: Geometry, *, origin: tuple[float, float], rotation_deg: float) -> dict[str, Any]:
    """``geometry`` with its anchor at ``origin``, turned by ``rotation_deg`` about that anchor.

    Raises:
        ValueError: for a geometry that is no bed shape (rect, circle, polygon) - a stored template never holds one.
    """
    if isinstance(geometry, RectGeometry):
        return {
            "kind": "rect",
            "origin": [origin[0], origin[1]],
            "width_m": geometry.width_m,
            "length_m": geometry.length_m,
            "rotation_deg": _turned(geometry.rotation_deg, rotation_deg),
        }
    if isinstance(geometry, CircleGeometry):
        return {"kind": "circle", "origin": [origin[0], origin[1]], "radius_m": geometry.radius_m}
    if isinstance(geometry, PolygonGeometry):
        anchor_x, anchor_y = geometry.points[0]
        return {
            "kind": "polygon",
            "points": [[origin[0] + x - anchor_x, origin[1] + y - anchor_y] for x, y in geometry.points],
            "rotation_deg": _turned(geometry.rotation_deg, rotation_deg),
        }
    raise ValueError(f"A bed template holds a rect, circle or polygon, not {geometry.kind}.")
