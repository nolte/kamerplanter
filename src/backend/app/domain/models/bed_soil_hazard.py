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

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.datetimes import today_utc
from app.common.enums import (
    EvidenceStatus,
    HostLevel,
    IrrigationSystem,
    PathogenConfirmationSource,
    SoilHazard,
    SoilHazardFollowUpKind,
)
from app.domain.models.failure_cause import LOSS_PATHOGENS

#: A bed holds at most one entry per hazard, so never more entries than there are hazards.
MAX_BED_SOIL_HAZARDS: int = len(SoilHazard)

#: Location types that are vessels (REQ-053 §11.3a Nr. 5, GP-FR-137): their substrate is replaced, not rotated, and
#: they carry no soil hazard. The same set switches the bed-level crop-rotation check off by default.
CONTAINER_LOCATION_TYPES: frozenset[str] = frozenset({"planter", "tent", "shelf"})

#: Irrigation systems without soil (operator decision 2026-11-17: ``Location.irrigation_system`` is authoritative).
HYDROPONIC_IRRIGATION_SYSTEMS: frozenset[IrrigationSystem] = frozenset(
    {IrrigationSystem.HYDRO, IrrigationSystem.NFT, IrrigationSystem.EBB_FLOW}
)

#: Location types that are no bed but a vessel all the same (``container``: pot/container group, ``is_bed`` false).
#: They are refused like ``planter``/``tent``/``shelf`` and with the same words, but they stay out of
#: :data:`CONTAINER_LOCATION_TYPES`, because that set also switches the crop-rotation check off (GP-FR-137).
NON_BED_VESSEL_LOCATION_TYPES: frozenset[str] = frozenset({"container"})

#: The earliest confirmation date accepted (#2888 F-20 review D5): older is a typo, not a finding.
EARLIEST_CONFIRMATION: date = date(1900, 1, 1)


def confirmation_date_violation(confirmed_at: date) -> str | None:
    """Why ``confirmed_at`` cannot be a confirmation date - after today (UTC) or before 1900 - or ``None``.

    One rule for every writer: the manual route, the take-over from a loss and the plan import all build a
    :class:`BedSoilHazard`, whose validator applies it.
    """
    if confirmed_at > today_utc():
        return "confirmed_in_future"
    if confirmed_at < EARLIEST_CONFIRMATION:
        return "confirmed_too_early"
    return None


#: Hazards a loss can hand over to its bed: exactly the pathogens a loss may name (``failure_cause.LOSS_PATHOGENS``,
#: the one definition - ``juglone`` is entered by hand only).
LOSS_SOIL_HAZARDS: frozenset[SoilHazard] = frozenset(LOSS_PATHOGENS)


class BedSoilHazard(BaseModel):
    """One stored entry of ``Location.soil_hazards`` (REQ-054 §5.2)."""

    model_config = ConfigDict(frozen=True)

    hazard: SoilHazard
    confirmed_at: date
    source: PathogenConfirmationSource

    @field_validator("confirmed_at")
    @classmethod
    def _a_plausible_day(cls, value: date) -> date:
        """Not after today (UTC) and not before 1900 - for a hand entry, a loss and an imported plan alike."""
        violation = confirmation_date_violation(value)
        if violation is not None:
            raise ValueError(f"confirmed_at {value.isoformat()}: {violation.replace('_', ' ')}")
        return value


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
