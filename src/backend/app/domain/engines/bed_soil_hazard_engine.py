"""Rules of a bed's soil hazards (REQ-054 §5.2, REQ-053 §11.3a Nr. 5, #2888 F-20).

Pure logic, no data access. Four answers:

* **Where a soil hazard may stand.** A bed (``LocationType.is_bed``) that is no vessel and has soil - a planter, tent
  or shelf is a vessel, a location whose ``irrigation_system`` is hydroponic has no soil.
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

from app.common.enums import SoilHazardFollowUpKind, SoilHazardRefusal, TerminationType
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


def soil_hazard_refusal_for_type(location_type_key: str, *, is_bed: bool) -> SoilHazardRefusal | None:
    """Why a location of this type carries no soil hazard: a vessel, or no bed. ``None`` when its type may.

    ``is_bed`` is ``LocationType.is_bed`` of the type (``False`` for an unknown or empty type key).
    """
    if location_type_key in CONTAINER_LOCATION_TYPES or location_type_key in NON_BED_VESSEL_LOCATION_TYPES:
        return SoilHazardRefusal.CONTAINER
    if not is_bed:
        return SoilHazardRefusal.NOT_A_BED
    return None


def soil_hazard_refusal(location: Location, *, is_bed: bool) -> SoilHazardRefusal | None:
    """Why ``location`` carries no soil hazard - its type, or hydroponics (no soil) - or ``None`` when it may."""
    refusal = soil_hazard_refusal_for_type(location.location_type_key, is_bed=is_bed)
    if refusal is not None:
        return refusal
    if location.irrigation_system in HYDROPONIC_IRRIGATION_SYSTEMS:
        return SoilHazardRefusal.HYDROPONIC
    return None


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


def follow_up_for_loss(plant: PlantInstance, location: Location | None, *, is_bed: bool) -> SoilHazardFollowUp | None:
    """What the app proposes after recording ``plant``'s loss at ``location``; ``None`` = nothing.

    Hydroponics first: a soil-borne loss there - confirmed or not - is the hint to clean the system (REQ-053 §11.3a
    Nr. 5, research R-004.3 d), also in a tent. Otherwise only a promotable loss at a location that may carry a soil
    hazard is offered, and only when the bed does not hold that hazard already as late or later.
    """
    if location is None or location.key is None or not is_soil_borne_loss(plant):
        return None
    if location.irrigation_system in HYDROPONIC_IRRIGATION_SYSTEMS:
        return SoilHazardFollowUp(kind=SoilHazardFollowUpKind.CLEAN_SYSTEM, location_key=location.key)
    if soil_hazard_refusal(location, is_bed=is_bed) is not None:
        return None
    try:
        entry = entry_from_loss(plant)
    except LossNotPromotableError:
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
