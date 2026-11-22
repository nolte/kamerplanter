"""Containment, overlap and boundary rules of the garden plan (REQ-053 §22.2, pure — no I/O).

The service builds a working copy of the plan, applies the batch's operations to
it and hands the result here as :class:`PlanEntity` values; this engine answers
which of them violate a rule. It never reads a document and never writes one
(GP-NFR-014: the rules live in the domain, not in the router).

Rules covered:

* **V-02** ``geometry.self_intersecting`` — a polygon whose edges cross.
* **V-03** ``geometry.outside_parent`` — an object lies completely inside its
  parent location, or inside the garden boundary when it has none. Objects flagged
  ``off_site`` are exempt (§9.5: the neighbour's house).
* **V-05** ``bed.overlap`` — two beds of one parent location may not overlap. A
  bed overlapping a garden object is allowed (a path under a raised bed).
* **V-19** ``boundary.shrinks_below_objects`` — a new boundary may not leave an
  existing top-level object outside.
* **V-06** ``slot.overlap`` — zone slots of one bed may not overlap (:func:`overlapping_zones`).
* **V-10** ``bed_status.invalid_transition`` — only the transitions of §7.4
  (:func:`bed_status_transition_allowed`).

Which entities are *checked* is the service's decision (the touched set): checking
the whole plan on every batch would make a one-bed edit cost O(plan²) and would
refuse an edit to bed A because bed B, untouched, already violates a rule an older
version of the editor allowed.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.common.enums import BedStatus, GeometryKind
from app.domain.calculators.geometry_calculator import (
    VertexShape,
    contains,
    overlaps,
    to_local_shape,
    to_shape,
    validate_geometry,
)
from app.domain.models.geometry import Geometry

ERROR_OUTSIDE_PARENT = "geometry.outside_parent"
ERROR_BED_OVERLAP = "bed.overlap"
ERROR_BOUNDARY_SHRINKS = "boundary.shrinks_below_objects"
ERROR_REFERENCE_NOT_FOUND = "reference.not_found"
ERROR_OBJECT_LOCKED = "object.locked"
ERROR_SLOT_OUTSIDE_BED = "slot.outside_bed"
ERROR_SLOT_OVERLAP = "slot.overlap"
ERROR_INVALID_BED_TRANSITION = "bed_status.invalid_transition"

#: REQ-053 §7.4: ``planned → active → retired → active`` and ``planned → retired`` (never created).
BED_STATUS_TRANSITIONS: dict[BedStatus, frozenset[BedStatus]] = {
    BedStatus.PLANNED: frozenset({BedStatus.ACTIVE, BedStatus.RETIRED}),
    BedStatus.ACTIVE: frozenset({BedStatus.RETIRED}),
    BedStatus.RETIRED: frozenset({BedStatus.ACTIVE}),
}

#: ``(field, code, key)`` — what is wrong with which entity.
type Finding = tuple[str, str, str]


@dataclass(frozen=True)
class PlanEntity:
    """The slice of a location or garden object the rules need."""

    entity: str
    key: str
    geometry: Geometry | None
    parent_location_key: str | None = None
    is_bed: bool = False
    off_site: bool = False


def _label(entity: PlanEntity) -> str:
    return f"{entity.entity}:{entity.key}"


class _Missing:
    """Marker: a link of the parent chain does not exist (a deleted or never-created location)."""


_MISSING = _Missing()


def _containing_geometry(entity: PlanEntity, locations: dict[str, PlanEntity]) -> Geometry | None | _Missing:
    """The geometry an entity must lie in: its nearest ancestor that has one; ``None`` = the garden boundary.

    A location without a geometry (an unplaced "Nutzgarten") encloses nothing, so the walk goes on to its
    own parent — otherwise everything below it could lie anywhere, boundary included (V-03, V-19).
    """
    key = entity.parent_location_key
    seen: set[str] = set()
    while key:
        if key in seen:
            break  # a parent cycle is the service's to refuse; stop here instead of looping
        seen.add(key)
        parent = locations.get(key)
        if parent is None:
            return _MISSING
        if parent.geometry is not None:
            return parent.geometry
        key = parent.parent_location_key
    return None


def check_entity(
    entity: PlanEntity,
    *,
    locations: dict[str, PlanEntity],
    siblings: list[PlanEntity],
    boundary: Geometry | None,
) -> list[Finding]:
    """V-02, V-03 and V-05 for one entity against the working copy.

    ``locations`` maps a location key to its entity (the parent lookup);
    ``siblings`` are the other geometry-bearing locations with the same parent.
    A parent that is not in ``locations`` was deleted (or never existed) in this
    batch: that is ``reference.not_found``, one text for both (GP-NFR-058).
    """
    findings: list[Finding] = []
    geometry = entity.geometry
    if geometry is None:
        return findings
    for code in validate_geometry(geometry):
        findings.append(("geometry", code, entity.key))
    if findings:
        # An unsimple polygon has no defined interior: containment and overlap would answer noise.
        return findings

    container = _containing_geometry(entity, locations)
    if isinstance(container, _Missing):
        return [("parent_location_key", ERROR_REFERENCE_NOT_FOUND, entity.key)]
    enclosing = container if container is not None else boundary
    if enclosing is not None and not entity.off_site and not _contained(enclosing, geometry):
        findings.append(("geometry", ERROR_OUTSIDE_PARENT, entity.key))

    if entity.entity == "location" and entity.is_bed:
        shape = to_shape(geometry)
        for other in siblings:
            if other.key == entity.key or other.geometry is None:
                continue
            if overlaps(shape, to_shape(other.geometry)):
                findings.append(("geometry", ERROR_BED_OVERLAP, entity.key))
                break
    return findings


def _contained(parent: Geometry, child: Geometry) -> bool:
    """V-03 with the 1 cm tolerance; a parent that encloses no area contains nothing."""
    parent_shape = to_shape(parent)
    if isinstance(parent_shape, VertexShape) and not parent_shape.closed:
        return True  # a parent without an interior is not a containment rule (the model forbids it anyway)
    return contains(parent_shape, to_shape(child))


def boundary_violations(
    entities: list[PlanEntity], boundary: Geometry, *, locations: dict[str, PlanEntity]
) -> list[str]:
    """V-19: ``entity:key`` of every entity the new *boundary* leaves outside, among *entities*.

    Only entities the boundary directly bounds count: those with no ancestor that has a geometry (a child
    inside a placed parent is bounded by the parent, which is itself in *entities* or untouched and inside).
    *locations* is the whole plan, for the ancestor walk.
    """
    if validate_geometry(boundary):
        return []
    outside: list[str] = []
    for entity in entities:
        if entity.geometry is None or entity.off_site:
            continue
        if _containing_geometry(entity, locations) is not None:
            continue  # bounded by an ancestor (or by a missing one, which check_entity reports)
        if not _contained(boundary, entity.geometry):
            outside.append(_label(entity))
    return sorted(outside)


def slots_outside_bed(bed: Geometry, slots: list[tuple[str, Geometry]]) -> list[str]:
    """V-04: keys of the slots whose geometry (bed frame) no longer lies inside the bed's local shape.

    Only meaningful after the bed's *shape* changed; moving or turning a bed leaves its frame, and so every
    slot, untouched (§9.2). 1 cm tolerance, no edge inset: the inset belongs to the layout that placed the slot.
    """
    shape = to_local_shape(bed)
    return sorted(key for key, geometry in slots if not contains(shape, to_shape(geometry)))


def bed_status_transition_allowed(current: BedStatus, target: BedStatus) -> bool:
    """V-10: whether §7.4 allows ``current → target``. Staying where you are is not a transition."""
    return target in BED_STATUS_TRANSITIONS[current]


def overlapping_zones(slots: list[tuple[str, Geometry]]) -> list[tuple[str, str]]:
    """V-06: pairs of zone slots (bed frame) that overlap. Positions and rows have no overlap notion.

    Only ``polygon`` geometries take part; the caller passes the *active and planned* slots of the bed
    (``archived_at`` null, F-02). Quadratic in the number of zones, which is small by nature (a bed is
    sown in a handful of zones).
    """
    zones = [(key, to_shape(geometry)) for key, geometry in slots if geometry.kind is GeometryKind.POLYGON]
    pairs: list[tuple[str, str]] = []
    for index, (first_key, first) in enumerate(zones):
        for second_key, second in zones[index + 1 :]:
            if overlaps(first, second):
                pairs.append((first_key, second_key))
    return pairs
