"""Soil hazards of a bed (REQ-054 §5.2, AP-API-012, REQ-053 §11.3a Nr. 5, #2888 F-20).

A bed's ``soil_hazards[]`` entry records **that** a persistent soil hazard was confirmed on the bed, **when** and
**how** (a category, never a person: ``source`` says lab result, advisory service or an unmistakable symptom). It
stores the hazard key only. Pathogens, hosts and durations resolve from the knowledge table (REQ-054 §5.2a) at read
time, so a re-researched value also reaches every existing finding (operator decision 2026-11-17).

F-20 records and shows; it does not judge. Which hosts warn or block, and for how long, is the planting dialog's and
the planner's (F-21, H-10) and depends on open operator decisions (P1-P7 in ``project/features/
soil-hazard-knowledge.md``). The read model below therefore carries every host with its evidence status as data and
no verdict.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import (
    EvidenceStatus,
    HostLevel,
    IrrigationSystem,
    PathogenConfirmationSource,
    SoilHazard,
    SoilHazardFollowUpKind,
)

#: A bed holds at most one entry per hazard, so never more entries than there are hazards.
MAX_BED_SOIL_HAZARDS: int = len(SoilHazard)

#: Location types that are vessels (REQ-053 §11.3a Nr. 5, GP-FR-137): their substrate is replaced, not rotated, and
#: they carry no soil hazard. The same set switches the bed-level crop-rotation check off by default.
CONTAINER_LOCATION_TYPES: frozenset[str] = frozenset({"planter", "tent", "shelf"})

#: Irrigation systems without soil (operator decision 2026-11-17: ``Location.irrigation_system`` is authoritative).
HYDROPONIC_IRRIGATION_SYSTEMS: frozenset[IrrigationSystem] = frozenset(
    {IrrigationSystem.HYDRO, IrrigationSystem.NFT, IrrigationSystem.EBB_FLOW}
)

#: Hazards a plant loss can name as its cause and offer to the bed. ``juglone`` is no pathogen of the plant but the
#: allelopathy of a walnut tree next to or formerly on the bed (research §2: "a hazard from outside the bed, no
#: prior crop"); its ``confirmed_at`` is the felling of the tree (REQ-054 §5.2a), which no loss records. It is
#: entered by hand only.
LOSS_SOIL_HAZARDS: frozenset[SoilHazard] = frozenset(
    hazard for hazard in SoilHazard if hazard is not SoilHazard.JUGLONE
)


class BedSoilHazard(BaseModel):
    """One stored entry of ``Location.soil_hazards`` (REQ-054 §5.2)."""

    model_config = ConfigDict(frozen=True)

    hazard: SoilHazard
    confirmed_at: date
    source: PathogenConfirmationSource


class SoilHazardFollowUp(BaseModel):
    """The follow-up of one recorded loss; ``hazard``/``confirmed_at``/``source`` are set for an offer only."""

    model_config = ConfigDict(frozen=True)

    kind: SoilHazardFollowUpKind
    location_key: str
    hazard: SoilHazard | None = None
    confirmed_at: date | None = None
    source: PathogenConfirmationSource | None = None


class ResolvedHost(BaseModel):
    """A host or non-host of the knowledge table with its evidence status - data, no verdict."""

    model_config = ConfigDict(frozen=True)

    level: HostLevel
    name: str
    evidence_status: EvidenceStatus


class ResolvedBedSoilHazard(BaseModel):
    """A stored entry with what the knowledge table says about its hazard at read time."""

    model_config = ConfigDict(frozen=True)

    hazard: SoilHazard
    confirmed_at: date
    source: PathogenConfirmationSource
    pathogens: tuple[str, ...] = Field(min_length=1)
    soft: bool
    hosts: tuple[ResolvedHost, ...]
    non_hosts: tuple[ResolvedHost, ...] = ()
