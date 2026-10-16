import math
from typing import assert_never

from app.common.enums import LayoutStrategy

#: Row-spacing factor of a staggered (triangular / hexagonal) layout: the rows of
#: an equilateral-triangle packing sit ``spacing × sin(60°)`` apart (REQ-053
#: GP-FR-060 / GP-FR-073, W-002).
TRIANGULAR_ROW_FACTOR = 0.866


def calculate_max_capacity(
    area_m2: float,
    plant_spacing_cm: float,
) -> int:
    """Calculate max number of plants fitting in area with given spacing."""
    if plant_spacing_cm <= 0 or area_m2 <= 0:
        return 0
    spacing_m = plant_spacing_cm / 100.0
    area_per_plant = spacing_m * spacing_m
    return int(math.floor(area_m2 / area_per_plant))


def calculate_optimal_range(
    area_m2: float,
    plant_spacing_cm: float,
    density_factor_low: float = 0.7,
    density_factor_high: float = 0.9,
) -> tuple[int, int]:
    """Calculate optimal plant count range (min, max) for an area.
    Uses density factors to account for walkways, equipment, etc.
    """
    max_cap = calculate_max_capacity(area_m2, plant_spacing_cm)
    return (
        max(1, int(math.floor(max_cap * density_factor_low))),
        int(math.floor(max_cap * density_factor_high)),
    )


def _area_per_plant_m2(
    spacing_cm: float,
    row_spacing_cm: float | None,
    strategy: LayoutStrategy,
) -> float:
    """Area one plant occupies (m²) under the given layout strategy.

    ``grid`` → ``spacing²``; ``rows`` → ``spacing × row_spacing``; ``triangular``
    → ``spacing² × 0.866`` (the staggered rows pack tighter). ``zone`` and ``free``
    carry no per-plant geometry of their own, so the nominal ``spacing²``
    estimate applies. Callers guarantee ``spacing_cm > 0`` and, for ``rows``,
    ``row_spacing_cm > 0``.
    """
    spacing_m = spacing_cm / 100.0
    match strategy:
        case LayoutStrategy.ROWS:
            if row_spacing_cm is None:
                raise ValueError("The rows layout needs a row_spacing_cm; none was given")
            return spacing_m * (row_spacing_cm / 100.0)
        case LayoutStrategy.TRIANGULAR:
            return spacing_m * spacing_m * TRIANGULAR_ROW_FACTOR
        case LayoutStrategy.GRID | LayoutStrategy.ZONE | LayoutStrategy.FREE:
            return spacing_m * spacing_m
        case _:
            assert_never(strategy)


def calculate_plants_per_m2(
    spacing_cm: float,
    row_spacing_cm: float | None = None,
    strategy: LayoutStrategy | str = LayoutStrategy.GRID,
) -> float:
    """Plant density per square metre for a spacing, row spacing and layout (GP-FR-073).

    ``calculate_plants_per_m2(60, 80, "rows")`` → ``2.08`` (tomato); the old
    ``1/spacing²`` reading gave ``2.78`` because it ignored the row spacing (W-003).
    ``triangular`` yields ``1 / (spacing² × 0.866)``. With no row spacing and the
    default ``grid`` strategy the result equals the previous ``1/spacing²``, so
    the one-argument callers keep their numbers.

    A non-positive (or NaN) spacing returns ``0.0``, and so does a non-positive
    row spacing under ``rows`` — the same shape the sibling functions use for
    unusable input. ``rows`` without any row spacing raises ``ValueError``
    rather than quietly computing the grid density W-003 complains about; the
    caller owns that fallback (GP-FR-061: no silent default). A strategy outside
    ``LayoutStrategy`` raises ``ValueError`` as well.
    """
    layout = LayoutStrategy(strategy)
    if not spacing_cm > 0:
        return 0.0
    if layout is LayoutStrategy.ROWS and row_spacing_cm is not None and not row_spacing_cm > 0:
        return 0.0
    return 1.0 / _area_per_plant_m2(spacing_cm, row_spacing_cm, layout)
