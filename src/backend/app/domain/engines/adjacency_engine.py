"""Derives ``adjacent_to`` edges from slot geometry (REQ-053 GP-FR-130, GP-ACC-023) — pure, no I/O.

Two slots of one bed are neighbours when the distance of their **centres** does not exceed

``adjacency_factor × max(spacing_a, row_spacing_a, spacing_b, row_spacing_b)``

(default factor 1.5: the diagonal ``√2`` is in, the next triangular neighbour ``1.73`` is out). The row
spacing takes part on purpose: without it alternating rows would never touch. When **both** slots carry a
known ``mature_width_cm`` the interaction radius ``(w_a + w_b) / 2 × f`` replaces the spacing rule, with
``f = 1.2`` for herbs and ``f = 2.0`` as soon as one of the two is a tree or shrub (root reach 2–3 × crown
radius, O-17; both values unverified, hence parameters).

From :data:`POINT_SLOT_LIMIT` point slots on in one bed only the **zones and rows** are linked among
themselves: the edge count of a bed with thousands of positions is the cost the limit exists to avoid.

The engine returns the *derived* pairs; which edges are written, kept (``source = manual``) or removed is
the repository's reconcile step, so running the derivation twice yields the same edges (idempotent).
Lengths of geometries are metres, spacings and distances centimetres (the species fields are centimetres).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from app.common.enums import GrowthHabit, SlotRole
from app.domain.calculators.geometry_calculator import centroid
from app.domain.models.geometry import Geometry

#: Above this many point slots in one bed, only zones and rows are linked (GP-FR-130 "Kantenlimit").
POINT_SLOT_LIMIT = 200
#: Centre distance rounding of the stored ``distance_cm`` (one decimal is below any plotting precision).
DISTANCE_DECIMALS = 1
#: Interaction factor on the mean mature width for herbaceous species (unverified, O-17).
HERB_INTERACTION_FACTOR = 1.2
#: Interaction factor when one of the two is a tree or shrub (root reach 2–3 × crown radius, O-17).
WOODY_INTERACTION_FACTOR = 2.0
#: Spacing assumed for a slot that has none (no plan, no species): the layout default grid of 0.30 m.
DEFAULT_SPACING_CM = 30.0
#: Growth habits that take the woody interaction factor.
WOODY_HABITS: frozenset[GrowthHabit] = frozenset({GrowthHabit.TREE, GrowthHabit.SHRUB})

_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def lower_bound_cm(value: str | float | None) -> float | None:
    """The lower value of a centimetre field (``"60--80"`` → 60.0, ``"30"`` → 30.0); ``None`` when absent."""
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value) if value > 0 else None
    match = _NUMBER.search(value)
    if match is None:
        return None
    number = float(match.group())
    return number if number > 0 else None


@dataclass(frozen=True)
class AdjacencyNode:
    """A slot with what the derivation needs; ``None`` spacing falls back to :data:`DEFAULT_SPACING_CM`."""

    key: str
    role: SlotRole
    geometry: Geometry
    spacing_cm: float | None = None
    row_spacing_cm: float | None = None
    mature_width_cm: float | None = None
    growth_habit: GrowthHabit | None = None

    @property
    def woody(self) -> bool:
        return self.growth_habit in WOODY_HABITS


@dataclass(frozen=True)
class AdjacentPair:
    """One neighbourhood; ``slot_a_key < slot_b_key`` so a pair has exactly one spelling."""

    slot_a_key: str
    slot_b_key: str
    distance_cm: float


def _reach_cm(a: AdjacencyNode, b: AdjacencyNode, factor: float) -> float:
    """The largest centre distance (cm) at which *a* and *b* still count as neighbours."""
    if a.mature_width_cm is not None and b.mature_width_cm is not None:
        interaction = WOODY_INTERACTION_FACTOR if (a.woody or b.woody) else HERB_INTERACTION_FACTOR
        return (a.mature_width_cm + b.mature_width_cm) / 2.0 * interaction
    spans = [v for v in (a.spacing_cm, a.row_spacing_cm, b.spacing_cm, b.row_spacing_cm) if v is not None]
    return factor * (max(spans) if spans else DEFAULT_SPACING_CM)


def derive_adjacency(nodes: list[AdjacencyNode], factor: float) -> list[AdjacentPair]:
    """The neighbour pairs of one bed's slots, sorted by ``(slot_a_key, slot_b_key)``.

    Slots without a key are ignored. Beyond :data:`POINT_SLOT_LIMIT` point slots the positions are left out
    and only zones and rows are compared with each other.
    """
    candidates = [node for node in nodes if node.key]
    point_count = sum(1 for node in candidates if node.role is SlotRole.POSITION)
    if point_count > POINT_SLOT_LIMIT:
        candidates = [node for node in candidates if node.role is not SlotRole.POSITION]
    centres = {node.key: centroid(node.geometry) for node in candidates}
    ordered = sorted(candidates, key=lambda node: node.key)
    pairs: list[AdjacentPair] = []
    for index, first in enumerate(ordered):
        cx, cy = centres[first.key]
        for second in ordered[index + 1 :]:
            distance_cm = math.hypot(centres[second.key][0] - cx, centres[second.key][1] - cy) * 100.0
            if distance_cm <= _reach_cm(first, second, factor) + 1e-9:
                pairs.append(AdjacentPair(first.key, second.key, round(distance_cm, DISTANCE_DECIMALS)))
    return pairs
