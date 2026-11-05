"""The companion-planting layer of a bed: one judged line per neighbouring pair of slots (REQ-053 WP 8.15).

:meth:`CompanionOverlayService.companion_edges` - ``GET /locations/{key}/companion-edges`` (GP-FR-134, REQ-028
§7.3). For every ``adjacent_to`` pair of the bed's slots in which **both** slots hold a species - a plant standing
there (``removed_on = null``) or one planned there by a live planting run (``run_planned_at.planned_species_key``),
the same set the planting dialog reads (:meth:`IGardenPlanRepository.load_slot_species_hints`) - the pair is judged
``compatible``, ``incompatible`` or ``unknown`` with
:func:`~app.domain.engines.companion_planting_engine.judge_neighbour`, the rule the planting dialog and the engine
apply. There is no second rule here.

A pair of slots can hold several species on each side, and a companion edge is stored per direction. Every species of
one slot is judged against every species of the other, **in both directions**, and the verdicts are folded with
:func:`~app.domain.engines.companion_planting_engine.strongest_verdict` (incompatible wins, else the best compatible
score, else unknown) - the same answer the dialog gives as its strongest hint when either species is planted next to
the other.

**Reads, not per edge.** One bed resolution, one species-hint read, one adjacency read, one companion read and one
slot read whatever the number of pairs; species names come with the companion read and only for species the tenant
may read (#927, MT-054).

**The work is bounded, not only the answer (SEC-001).**

* The adjacency read folds, sorts by ``(slot_a_key, slot_b_key)`` and cuts the pairs **in the database** at
  :data:`MAX_JUDGED_PAIRS`; ``total`` is counted there separately and is exact.
* At most :data:`MAX_SPECIES_PER_SLOT` species per slot (by key) enter the cross product, so one pair costs at most
  ``2 * 8 * 8 = 128`` rule calls; an endpoint with more says so in ``species_truncated``.
* The companion read stops at :data:`MAX_COMPANION_RELATIONS` edges per collection; the slot read names only the
  slots of the judged pairs.

**What the order guarantees.** The judgement is the shared Python rule, so the status order cannot be pushed into the
database without a second rule. Within the judged window the answer is exact: the
:data:`MAX_COMPANION_EDGES` strongest pairs, ``incompatible`` before ``compatible`` before ``unknown``, then by slot
keys. When a bed has more than :data:`MAX_JUDGED_PAIRS` occupied pairs (``total`` above it), the pairs beyond the
window - the last by slot keys - are not judged and not answered, whatever their status; ``truncated`` is ``true``.

Every public method takes ``*, tenant_key: str`` without a default; the bed is resolved through
:mod:`~app.domain.services.location_ownership` (a bed carries no ``tenant_key`` of its own, #2107), so another
tenant's bed and an unknown one are the same 404.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import structlog

from app.domain.calculators.geometry_calculator import bed_to_plan_transform
from app.domain.engines.companion_planting_engine import (
    COMPANION_STATUS_RANK,
    CompanionStatus,
    CompanionVerdict,
    judge_neighbour,
    strongest_verdict,
)
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.graph_repository import CompanionRelations, IGraphRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.geometry import (
    Geometry,
    PointGeometry,
    PolygonGeometry,
    PolylineGeometry,
    round_length,
)
from app.domain.services.location_ownership import resolve_owned_location

logger = structlog.get_logger()

#: At most this many pairs per response (GP-FR-134: the renderer culls to 500 lines per viewport).
MAX_COMPANION_EDGES = 500
#: At most this many pairs are read and judged per request (four times the answer, cut in the database).
MAX_JUDGED_PAIRS = 2000
#: At most this many species per slot enter the cross product (sorted by key). A slot holds one plant, or a few
#: species of a mixed planting; eight is above any mixed slot the plan editor creates.
MAX_SPECIES_PER_SLOT = 8
#: At most this many edges per companion edge collection are read among the judged species.
MAX_COMPANION_RELATIONS = 10_000

#: The reason codes of a judged pair; the frontend translates them (``companion.*``).
REASON_CODES: dict[CompanionStatus, str] = {
    "incompatible": "companion.incompatible",
    "compatible": "companion.compatible",
    "unknown": "companion.unknown",
}

Point2D = tuple[float, float]


@dataclass(frozen=True)
class CompanionEndpoint:
    """One slot of a pair: where it lies in the plan frame and which species stand or are planned in it."""

    slot_key: str
    #: The slot's anchor in plan coordinates (metres): a point's origin, else the mean of its vertices.
    #: ``None`` when the slot or its bed has no geometry - the line cannot be drawn.
    position: Point2D | None
    species_keys: list[str]
    #: ``True`` when the slot holds more than :data:`MAX_SPECIES_PER_SLOT` species and only the first were judged.
    species_truncated: bool = False


@dataclass(frozen=True)
class DecidingPair:
    """The two species whose relation decided the pair; the names only where the tenant may read the species."""

    species_a_key: str
    species_a_name: str | None
    species_b_key: str
    species_b_name: str | None


@dataclass(frozen=True)
class CompanionEdge:
    slot_a: CompanionEndpoint
    slot_b: CompanionEndpoint
    status: CompanionStatus
    reason_code: str
    #: The curated reason of the deciding ``incompatible_with`` edge, if it names one; ``None`` otherwise.
    reason: str | None
    #: The ``compatible_with`` score of the deciding pair; ``None`` for any other status (nothing is assumed, E-10).
    score: float | None
    #: ``None`` when no edge relates any species of the two slots (``unknown``).
    deciding: DecidingPair | None
    #: ``adjacent_to.distance_cm`` as stored; ``None`` for an edge without one (a manual or legacy edge).
    distance_cm: float | None


@dataclass(frozen=True)
class CompanionEdges:
    location_key: str
    edges: list[CompanionEdge]
    #: Every pair with species on both sides, counted in the database (exact, not bounded by the window).
    total: int
    truncated: bool


@dataclass(frozen=True)
class _Judged:
    verdict: CompanionVerdict
    anchor: str | None = None
    other: str | None = None


class CompanionOverlayService:
    def __init__(
        self, site_repo: ISiteRepository, plan_repo: IGardenPlanRepository, graph_repo: IGraphRepository
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._graph = graph_repo

    def companion_edges(self, location_key: str, *, tenant_key: str) -> CompanionEdges:
        """The judged neighbouring pairs of a bed's occupied slots, strongest first, at most 500 (GP-FR-134)."""
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        bed_key = location.key or location_key

        species_by_slot: dict[str, set[str]] = {}
        for hint in self._plan.load_slot_species_hints(bed_key, tenant_key=tenant_key):
            species_by_slot.setdefault(hint.slot_key, set()).add(hint.species_key)
        if not species_by_slot:
            return CompanionEdges(location_key=bed_key, edges=[], total=0, truncated=False)

        window = self._graph.get_slot_adjacency(
            bed_key, sorted(species_by_slot), tenant_key=tenant_key, limit=MAX_JUDGED_PAIRS
        )
        pairs = [
            pair
            for pair in window.pairs[:MAX_JUDGED_PAIRS]
            if pair.slot_a_key in species_by_slot and pair.slot_b_key in species_by_slot
        ]
        if not pairs:
            return CompanionEdges(location_key=bed_key, edges=[], total=window.total, truncated=window.total > 0)

        in_pairs = sorted({key for pair in pairs for key in (pair.slot_a_key, pair.slot_b_key)})
        judged_species = {key: sorted(species_by_slot[key])[:MAX_SPECIES_PER_SLOT] for key in in_pairs}
        relations = self._graph.load_companion_relations(
            sorted({species for keys in judged_species.values() for species in keys}),
            tenant_key=tenant_key,
            limit=MAX_COMPANION_RELATIONS,
        )
        if not relations.complete:
            logger.warning("companion_overlay.relations_truncated", location_key=bed_key, limit=MAX_COMPANION_RELATIONS)
        rules = _Rules(relations)
        positions = self._positions(location.site_key, bed_key, location.geometry, in_pairs, tenant_key=tenant_key)

        def endpoint(slot_key: str) -> CompanionEndpoint:
            return CompanionEndpoint(
                slot_key,
                positions[slot_key] if slot_key in positions else None,  # noqa: SIM401 - call-graph ceiling
                judged_species[slot_key],
                species_truncated=len(species_by_slot[slot_key]) > MAX_SPECIES_PER_SLOT,
            )

        edges = [
            self._edge(rules, relations, endpoint(pair.slot_a_key), endpoint(pair.slot_b_key), pair.distance_cm)
            for pair in pairs
        ]
        edges.sort(key=lambda edge: (COMPANION_STATUS_RANK[edge.status], edge.slot_a.slot_key, edge.slot_b.slot_key))
        answered = edges[:MAX_COMPANION_EDGES]
        total = max(window.total, len(edges))
        truncated = total > len(answered)
        logger.debug(
            "companion_overlay.read", location_key=bed_key, judged=len(edges), total=total, truncated=truncated
        )
        return CompanionEdges(location_key=bed_key, edges=answered, total=total, truncated=truncated)

    @staticmethod
    def _edge(
        rules: _Rules,
        relations: CompanionRelations,
        slot_a: CompanionEndpoint,
        slot_b: CompanionEndpoint,
        distance_cm: float | None,
    ) -> CompanionEdge:
        judged = [
            _Judged(rules.judge(anchor, other), anchor, other)
            for left, right in ((slot_a, slot_b), (slot_b, slot_a))
            for anchor in left.species_keys
            for other in right.species_keys
        ]
        verdict = strongest_verdict(item.verdict for item in judged)
        # The deciding pair is the first judged pair that carries the folded verdict (stable: sorted species keys).
        deciding = (
            next((item for item in judged if item.verdict == verdict), None) if verdict.status != "unknown" else None
        )
        pair: DecidingPair | None = None
        reason: str | None = None
        if deciding is not None and deciding.anchor is not None and deciding.other is not None:
            first, second = sorted((deciding.anchor, deciding.other))
            pair = DecidingPair(first, relations.names.get(first), second, relations.names.get(second))
            if verdict.status == "incompatible":
                reason = rules.reason(deciding.anchor, deciding.other)
        score = verdict.score if verdict.status == "compatible" and isinstance(verdict.score, int | float) else None
        return CompanionEdge(
            slot_a=slot_a,
            slot_b=slot_b,
            status=verdict.status,
            reason_code=REASON_CODES[verdict.status],
            reason=reason,
            score=float(score) if score is not None else None,
            deciding=pair,
            distance_cm=distance_cm,
        )

    def _positions(
        self,
        site_key: str,
        bed_key: str,
        bed_geometry: Geometry | None,
        slot_keys: list[str],
        *,
        tenant_key: str,
    ) -> dict[str, Point2D]:
        """The plan-frame anchor of each slot in *slot_keys* (one read of just those slots, one bed transform)."""
        if bed_geometry is None or not slot_keys:
            return {}
        to_plan = bed_to_plan_transform(bed_geometry)
        wanted = set(slot_keys)
        return {
            slot.key: point
            for slot in self._plan.load_active_slots(site_key, [bed_key], tenant_key=tenant_key, slot_keys=slot_keys)
            if slot.key in wanted and (point := _slot_anchor(slot.geometry, to_plan)) is not None
        }


class _Rules:
    """The companion edges of the bed's species as the inputs :func:`judge_neighbour` takes, per anchor species."""

    def __init__(self, relations: CompanionRelations) -> None:
        self._incompatible: dict[str, dict[str, str | None]] = {}
        self._compatible: dict[str, dict[str, float | None]] = {}
        for relation in relations.relations:
            if relation.incompatible:
                self._incompatible.setdefault(relation.from_key, {})[relation.to_key] = relation.reason
            else:
                self._compatible.setdefault(relation.from_key, {})[relation.to_key] = relation.score

    def judge(self, anchor: str, other: str) -> CompanionVerdict:
        return judge_neighbour(other, self._incompatible.get(anchor, {}).keys(), self._compatible.get(anchor, {}))

    def reason(self, anchor: str, other: str) -> str | None:
        return self._incompatible.get(anchor, {}).get(other)


def _slot_anchor(geometry: Geometry | None, to_plan: Callable[[Point2D], Point2D]) -> Point2D | None:
    """A slot's anchor in the plan frame: a point's origin, a row's or zone's vertex mean, rounded to millimetres."""
    if geometry is None:
        return None
    if isinstance(geometry, PointGeometry):
        x, y = to_plan(geometry.origin)
    elif isinstance(geometry, PolylineGeometry | PolygonGeometry):
        mapped = [to_plan(point) for point in geometry.points]
        x, y = sum(p[0] for p in mapped) / len(mapped), sum(p[1] for p in mapped) / len(mapped)
    else:  # a slot is a point, a row or a zone (``Slot`` refuses every other shape, §20.5)
        return None
    return (round_length(x), round_length(y))
