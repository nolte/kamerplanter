"""Rules of a bed's soil hazards (REQ-054 §5.2, REQ-053 §11.3a Nr. 5, #2888 F-20).

Pure logic, no data access. Five answers:

* **Where a soil hazard may stand.** Never in a vessel (a planter, tent, shelf or container group) and never where the
  roots grow in a solution (hydroponics, :func:`is_hydroponic`). ``juglone`` stands at every other location - a bed
  and an area alike (``garden``, ``zone``, a greenhouse on grown soil, a tenant's own type with ``is_bed = false``,
  operator decision O3 2026-11-27); every other hazard only at a bed (``LocationType.is_bed``).
* **What the soil under a location carries** (:func:`effective_soil_hazards`, REQ-053 §11.3a Nr. 5 v1.60): its own
  entries and those of its parent chain - a walnut's juglone recorded at the garden reaches the beds in it. A vessel
  breaks the chain; a hydroponic location carries none at all. The chain is the caller's
  (``location_ancestry.location_ancestors``): nearest parent first, within the location's site.
* **What a recorded loss proposes.** A soil-borne loss at a hydroponic location proposes cleaning the system; a
  confirmed soil-borne loss with a listed pathogen (``juglone`` excluded, see ``LOSS_SOIL_HAZARDS``) at a bed offers
  to take the pathogen over into the bed. An unconfirmed loss proposes nothing and can never be taken over
  (:func:`entry_from_loss` refuses it, so the rule holds for every caller, not only the dialog).
* **How a new entry merges.** One entry per hazard; a later confirmation replaces the earlier one, an earlier or equal
  one leaves it as it is. A grower can therefore extend a hazard but never shorten it - only the lead removes it.
* **What the knowledge table says about an entry.** Pathogens, the ``soft`` flag, hosts and non-hosts with their
  evidence status - as data. No host is judged here (open operator decisions P1-P7, F-21).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.common.enums import (
    IrrigationSystem,
    SoilHazard,
    SoilHazardFollowUpKind,
    SoilHazardRefusal,
    SoilHazardScope,
    TerminationType,
)
from app.domain.models.bed_soil_hazard import (
    CONTAINER_LOCATION_TYPES,
    HYDROPONIC_IRRIGATION_SYSTEMS,
    LOSS_SOIL_HAZARDS,
    NON_BED_VESSEL_LOCATION_TYPES,
    BedSoilHazard,
    ResolvedBedSoilHazard,
    ResolvedHost,
    SoilHazardFollowUp,
)
from app.domain.models.failure_cause import SOIL_BORNE_CLASSES
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location
from app.domain.models.soil_hazard_knowledge import HostEntry, SoilHazardKnowledgeTable


class LossNotPromotableError(ValueError):
    """The loss names no confirmed, listed soil-borne pathogen; ``reason`` says which condition failed."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def is_vessel_type(location_type_key: str) -> bool:
    """A planter, tent, shelf or container group: its substrate is replaced, it carries no soil hazard."""
    return location_type_key in CONTAINER_LOCATION_TYPES or location_type_key in NON_BED_VESSEL_LOCATION_TYPES


def soil_hazard_refusal_for_type(
    location_type_key: str, *, is_bed: bool, hazard: SoilHazard | None
) -> SoilHazardRefusal | None:
    """Why a location of this type does not carry ``hazard``: a vessel, or no bed. ``None`` when its type may.

    ``juglone`` stands at every type that is no vessel; every other hazard only at a bed (operator decision O3,
    2026-11-27). ``hazard = None`` is a hazard not known yet - the pathogen of a loss, never ``juglone`` - and is
    held to the bed rule. ``is_bed`` is ``LocationType.is_bed`` of the type (``False`` for an unknown or empty key).
    """
    if is_vessel_type(location_type_key):
        return SoilHazardRefusal.CONTAINER
    if is_bed or hazard is SoilHazard.JUGLONE:
        return None
    return SoilHazardRefusal.NOT_A_BED


def effective_irrigation_system(location: Location, ancestors: Sequence[Location]) -> IrrigationSystem:
    """The irrigation system that applies at ``location``: its own, or - when that is ``manual`` - its parents'.

    ``manual`` is the default every location is created with, so it stands for "nothing entered": a shelf or tent
    left at it under a hydroponic room counts as hydroponic (operator decision O5, 2026-11-27). The nearest parent with
    another value decides; without one it stays ``manual``. ``ancestors`` is the parent chain, nearest first.
    """
    for candidate in (location, *ancestors):
        if candidate.irrigation_system is not IrrigationSystem.MANUAL:
            return candidate.irrigation_system
    return IrrigationSystem.MANUAL


def is_hydroponic(location: Location, ancestors: Sequence[Location]) -> bool:
    """Whether the effective irrigation system at ``location`` is hydroponic (:func:`effective_irrigation_system`).

    Own or inherited. What it decides depends on the location (:func:`lacks_soil`): it switches a location without a
    bed type off entirely, at a bed type only the hazards inherited from above (REQ-053 v1.61 §11.3a Nr. 5).
    """
    return effective_irrigation_system(location, ancestors) in HYDROPONIC_IRRIGATION_SYSTEMS


def has_own_hydroponics(location: Location) -> bool:
    """The location's own ``irrigation_system`` is hydroponic - nothing inherited."""
    return location.irrigation_system in HYDROPONIC_IRRIGATION_SYSTEMS


def lacks_soil(location: Location, ancestors: Sequence[Location], *, is_bed: bool) -> bool:
    """Whether ``location`` has no soil of its own: no entry, no offer, the clean-system hint after a loss.

    Its own hydroponic value always; an inherited one at a location without a bed type and at every vessel (a shelf,
    tent, container group - and a ``planter``, which the catalogue lists as a bed type, REQ-053 v1.62) left at
    ``manual`` under a hydroponic room. A soil bed type left at ``manual`` stays a soil bed under such a room - a
    ``greenhouse_bed`` in a greenhouse set to ``hydro`` for its NFT channel keeps its confirmed clubroot (REQ-053 v1.61
    §11.3a Nr. 5, the review's safe direction: no confirmed hazard of a bed is dropped silently).
    """
    if has_own_hydroponics(location):
        return True
    soil_bed = is_bed and not is_vessel_type(location.location_type_key)
    return not soil_bed and is_hydroponic(location, ancestors)


def soil_hazard_refusal(
    location: Location, *, is_bed: bool, hazard: SoilHazard | None, ancestors: Sequence[Location]
) -> SoilHazardRefusal | None:
    """Why ``location`` does not carry ``hazard`` - its type, or hydroponics (no soil) - or ``None`` when it may."""
    refusal = soil_hazard_refusal_for_type(location.location_type_key, is_bed=is_bed, hazard=hazard)
    if refusal is not None:
        return refusal
    if lacks_soil(location, ancestors, is_bed=is_bed):
        return SoilHazardRefusal.HYDROPONIC
    return None


def soil_hazard_scope(location: Location, *, is_bed: bool, ancestors: Sequence[Location]) -> SoilHazardScope:
    """Which soil hazards ``location`` takes, for the form that records them (the server's rule, shown before)."""
    if is_vessel_type(location.location_type_key):
        return SoilHazardScope.CONTAINER
    if lacks_soil(location, ancestors, is_bed=is_bed):
        return SoilHazardScope.HYDROPONIC
    return SoilHazardScope.ALL if is_bed else SoilHazardScope.JUGLONE_ONLY


@dataclass(frozen=True)
class LocatedSoilHazard:
    """A soil hazard the soil at a location carries, with where it is recorded (REQ-053 v1.61 §11.3a Nr. 6)."""

    entry: BedSoilHazard
    #: The parent location the entry is recorded at - one of the caller's checked parent chain; ``None`` = the
    #: location itself.
    origin: Location | None = None


def effective_soil_hazards(location: Location, ancestors: Sequence[Location]) -> list[LocatedSoilHazard]:
    """The soil hazards the soil at ``location`` carries: its own and those of its parent chain (REQ-053 §11.3a Nr. 5).

    None in a vessel or where the location's **own** irrigation system is hydroponic. A soil bed that only inherits
    hydroponics keeps its own entries and those of its parents (operator decision N-e 2026-11-28, REQ-053 v1.63: "a
    soil bed inherits the hazard"). Walking up, a vessel ends the chain - whatever stands in it has its own substrate; a
    hydroponic parent does not end it, it only adds no entries of its own (it has no soil). A hazard held at several
    levels counts once, with the latest confirmation (as :func:`merged_entries`), and names the location that holds it.
    """
    if is_vessel_type(location.location_type_key) or has_own_hydroponics(location):
        return []
    found: dict[SoilHazard, LocatedSoilHazard] = {
        entry.hazard: LocatedSoilHazard(entry) for entry in location.soil_hazards
    }
    for ancestor in ancestors:
        if is_vessel_type(ancestor.location_type_key):
            break
        if has_own_hydroponics(ancestor):
            continue
        for entry in ancestor.soil_hazards:
            held = found.get(entry.hazard)
            if held is None or entry.confirmed_at > held.entry.confirmed_at:
                found[entry.hazard] = LocatedSoilHazard(entry, ancestor)
    return list(found.values())


def is_soil_borne_loss(plant: PlantInstance) -> bool:
    """A ``died`` plant whose cause class sat in the soil (``pest_soil`` / ``disease_soil``)."""
    return plant.termination_type is TerminationType.DIED and plant.failure_cause_class in SOIL_BORNE_CLASSES


def entry_from_loss(plant: PlantInstance) -> BedSoilHazard:
    """The bed entry a loss stands for: its pathogen, the day of the loss and who confirmed it.

    Raises:
        LossNotPromotableError: The plant is no soil-borne loss, names no pathogen, names ``juglone``, or the pathogen
            is not confirmed with a source. An unconfirmed suspicion never becomes an entry (REQ-053 §11.3a Nr. 5).
    """
    if not is_soil_borne_loss(plant) or plant.removed_on is None:
        raise LossNotPromotableError("the plant is no soil-borne loss (died with pest_soil or disease_soil)")
    if plant.failure_pathogen is None:
        raise LossNotPromotableError("the loss names no pathogen")
    if plant.failure_pathogen not in LOSS_SOIL_HAZARDS:
        raise LossNotPromotableError(f"'{plant.failure_pathogen}' is entered at the bed by hand, not from a loss")
    if plant.failure_pathogen_confirmed is not True or plant.failure_pathogen_source is None:
        raise LossNotPromotableError("the pathogen of the loss is not confirmed")
    return BedSoilHazard(
        hazard=plant.failure_pathogen,
        confirmed_at=plant.removed_on,
        source=plant.failure_pathogen_source,
    )


def merged_entries(existing: Sequence[BedSoilHazard], entry: BedSoilHazard) -> list[BedSoilHazard]:
    """``existing`` with ``entry`` recorded: added, or replacing an earlier confirmation of the same hazard."""
    current = next((item for item in existing if item.hazard is entry.hazard), None)
    if current is not None and current.confirmed_at >= entry.confirmed_at:
        return list(existing)
    return [*(item for item in existing if item.hazard is not entry.hazard), entry]


def is_recorded(existing: Sequence[BedSoilHazard], entry: BedSoilHazard) -> bool:
    """Whether recording ``entry`` would change nothing (the bed holds the hazard, confirmed as late or later)."""
    return merged_entries(existing, entry) == list(existing)


def follow_up_for_loss(
    plant: PlantInstance, location: Location | None, *, is_bed: bool, ancestors: Sequence[Location]
) -> SoilHazardFollowUp | None:
    """What the app proposes after recording ``plant``'s loss at ``location``; ``None`` = nothing.

    No soil first (:func:`lacks_soil`): a soil-borne loss there - confirmed or not - is the hint to clean the system
    (REQ-053 §11.3a Nr. 5, research R-004.3 d), also in a tent and at a location without a bed type that inherits
    hydroponics from its parents (``ancestors``, nearest first); a bed type left at ``manual`` is soil.
    Otherwise only a promotable loss at a location that may carry a soil hazard is offered, and only when the bed does
    not hold that hazard already as late or later.
    """
    if location is None or location.key is None or not is_soil_borne_loss(plant):
        return None
    if lacks_soil(location, ancestors, is_bed=is_bed):
        return SoilHazardFollowUp(kind=SoilHazardFollowUpKind.CLEAN_SYSTEM, location_key=location.key)
    try:
        entry = entry_from_loss(plant)
    except LossNotPromotableError:
        return None
    if soil_hazard_refusal(location, is_bed=is_bed, hazard=entry.hazard, ancestors=ancestors) is not None:
        return None
    if is_recorded(location.soil_hazards, entry):
        return None
    return SoilHazardFollowUp(
        kind=SoilHazardFollowUpKind.OFFER,
        location_key=location.key,
        hazard=entry.hazard,
        confirmed_at=entry.confirmed_at,
        source=entry.source,
    )


def _resolved_hosts(entries: Sequence[HostEntry]) -> tuple[ResolvedHost, ...]:
    return tuple(
        ResolvedHost(level=entry.level, name=entry.name, evidence_status=entry.evidence.status) for entry in entries
    )


def resolve_entries(entries: Sequence[BedSoilHazard], table: SoilHazardKnowledgeTable) -> list[ResolvedBedSoilHazard]:
    """Each entry with its knowledge-table row, newest confirmation first (hazard key breaks a tie)."""
    rows = {row.hazard: row for row in table.hazards}
    ordered = sorted(entries, key=lambda item: (-item.confirmed_at.toordinal(), item.hazard.value))
    return [
        ResolvedBedSoilHazard(
            hazard=entry.hazard,
            confirmed_at=entry.confirmed_at,
            source=entry.source,
            pathogens=rows[entry.hazard].pathogens,
            soft=rows[entry.hazard].soft,
            hosts=_resolved_hosts(rows[entry.hazard].hosts),
            non_hosts=_resolved_hosts(rows[entry.hazard].non_hosts),
        )
        for entry in ordered
    ]
