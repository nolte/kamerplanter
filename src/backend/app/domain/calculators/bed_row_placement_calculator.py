"""Where the beds of a CSV bed list land on the plan (REQ-053 GP-FR-174; WP 8.26, #2669).

GP-FR-174: the import "lays out the beds without a layout, at first in one row; the arrangement happens in the
editor". The decision bundle (#2643, question 6) fixes the row: from the **top-left corner**, left to right, a
``gap`` of 0.5 m between two beds. Two rules are added here so that a row does not refuse beds that fit:

* **Wrapping at the boundary.** With a garden boundary the row ends at the right edge of the boundary's bounding box
  and the next row starts below the tallest bed of the previous one, again with ``gap``. Without a boundary the
  frame is the whole plan frame (1 000 m), so the list is one row in practice.
* **Existing beds are stepped over.** A position that would cover the bounding box of a bed already on the plan
  (an ``obstacle``) moves right past it; the batch's overlap rule (V-05) then has nothing to refuse.

A bed that does not fit (wider than the frame, or no row left above the bottom edge) gets no position (``None``)
and takes no space: a smaller bed after it may still fit. The importing service reports it for its line. The plan
frame is mathematical (``+y`` up, §9.2), so "top" is the largest ``y``.

Computed in whole millimetres - the precision of every stored length (§9.2) - so that a position the calculator
found free is free after the geometry rounds it: the frame is rounded inwards, an obstacle outwards. Pure functions,
no I/O.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

#: ``(min_x, min_y, max_x, max_y)`` - the shape of :func:`app.domain.calculators.geometry_calculator.bounding_box`.
type Box = tuple[float, float, float, float]

_MM = 1000
#: Below this, a float is the same millimetre (``2.0005`` m is read as 2 000.5 mm, not as 2 001).
_ROUNDING_SLACK = 1e-6


def _down(metres: float) -> int:
    return math.floor(metres * _MM + _ROUNDING_SLACK)


def _up(metres: float) -> int:
    return math.ceil(metres * _MM - _ROUNDING_SLACK)


def _nearest(metres: float) -> int:
    return round(metres * _MM)


#: The most obstacle comparisons one placement may make. A realistic list (a few hundred beds, a few hundred beds
#: already on the plan) needs a few ten thousand; the bound keeps a crafted one - rows blocked across the width,
#: beds that fit nowhere - from turning a dry run into seconds of CPU (#2669 SEC-001).
MAX_PLACEMENT_STEPS = 2_000_000


class PlacementTooComplexError(ValueError):
    """The placement needed more than ``max_steps`` obstacle comparisons; nothing was placed."""


def _overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    """Interiors overlap; two boxes that only touch do not (V-05 compares interiors)."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def place_in_rows(
    sizes: Sequence[tuple[float, float]],
    *,
    frame: Box,
    obstacles: Sequence[Box] = (),
    gap: float,
    max_steps: int = MAX_PLACEMENT_STEPS,
) -> list[tuple[float, float] | None]:
    """The lower-left corner of every ``(width, length)`` in ``sizes``, in order, rows filled from the top-left.

    ``frame`` is the area to fill (the boundary's bounding box, or the plan frame); ``obstacles`` are boxes no
    position may cover. ``None`` for a bed that finds no place. Terminates for any input: every step either places a
    bed, moves right past an obstacle, or starts a strictly lower row; and it gives up with
    :class:`PlacementTooComplexError` after ``max_steps`` obstacle comparisons.
    """
    left, bottom, right, top = _up(frame[0]), _up(frame[1]), _down(frame[2]), _down(frame[3])
    blocked = [(_down(b[0]), _down(b[1]), _up(b[2]), _up(b[3])) for b in obstacles]
    spacing = _nearest(gap)
    positions: list[tuple[float, float] | None] = []
    row_top = top
    row_height = 0
    #: The lowest bottom edge of the obstacles that blocked the current row.
    row_floor: int | None = None
    x = left
    steps = 0
    for width_m, length_m in sizes:
        width, length = max(_nearest(width_m), 1), max(_nearest(length_m), 1)
        saved = (row_top, row_height, row_floor, x)
        fits = width <= right - left
        while fits:
            if x > left and x + width > right:
                # The row is full: the next one starts below its tallest bed; a row in which no bed was placed
                # (obstacles across its width) is left below the lowest obstacle that blocked it. Either way the
                # row top falls strictly, so the loop ends.
                if row_height > 0:
                    row_top -= row_height + spacing
                elif row_floor is not None:
                    row_top = row_floor - spacing
                else:
                    row_top -= length + spacing
                row_height, row_floor, x = 0, None, left
                steps += 1
                continue
            candidate = (x, row_top - length, x + width, row_top)
            if candidate[1] < bottom:
                fits = False  # no row left for it
                break
            hit: tuple[int, int, int, int] | None = None
            for box in blocked:
                steps += 1
                if _overlaps(candidate, box):
                    hit = box
                    break
            if steps > max_steps:
                raise PlacementTooComplexError(f"The placement needed more than {max_steps} steps.")
            if hit is None:
                break
            row_floor = hit[1] if row_floor is None else min(row_floor, hit[1])
            x = hit[2] + spacing
        if not fits:
            row_top, row_height, row_floor, x = saved
            positions.append(None)
            continue
        positions.append((x / _MM, (row_top - length) / _MM))
        x += width + spacing
        row_height = max(row_height, length)
    return positions
