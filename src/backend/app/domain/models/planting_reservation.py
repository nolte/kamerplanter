"""Write sets and read rows of the slot reservation (REQ-053 WP 3.2, GP-FR-055/064–066, GP-API-017…024).

Every write set is what the service has validated and the repository writes in **one transaction**
(GP-NFR-013); none of them is ever built from an HTTP body. A write set that names a ``location_key`` is
written under that bed's document lock, so two writers of one bed serialise (the loser answers 409).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.enums import LayoutStrategy, PlanRole, RowDirection
from app.domain.engines.slot_reservation_engine import ActivePlant, Reservation
from app.domain.models.care_event import CareEvent
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import (
    MAX_ROTATION_OVERRIDE_REASON,
    MAX_SPACING_CM,
    MIN_ROW_SPACING_CM,
    MIN_SPACING_CM,
    PlantingRun,
    PlantingRunEntry,
)
from app.domain.models.site import Slot

#: GP-NFR-017: one quick planting writes at most this many plants.
QUICK_PLANTING_MAX_QUANTITY = 500

#: The transaction budget of the reservation writes — the garden-plan batch's, the largest atomic write (GP-NFR-013).
RESERVATION_TIME_BUDGET_SECONDS = 10.0


class ReservationReads(Protocol):
    """The two reads V-08 needs, bound either to the database or — for the re-check — to an open transaction."""

    def reservations_for(self, slot_keys: list[str], *, tenant_key: str) -> list[Reservation]: ...

    def active_plants_in(self, slot_keys: list[str], *, tenant_key: str) -> list[ActivePlant]: ...


@dataclass(frozen=True)
class NewReservedSlot:
    """A slot the layout created, with the reservation edge it gets (GP-FR-064/065)."""

    slot: Slot
    entry_key: str
    planned_species_key: str
    #: The edge's ``sequence``: the order ``create-plants`` fills the slots in, per entry (row by row).
    sequence: int


@dataclass(frozen=True)
class RunSlotsWrite:
    """``POST /planting-runs`` on a bed with geometry: the slots and their ``run_planned_at`` edges."""

    location_key: str
    run_key: str
    planned_from: date
    planned_until: date | None
    slots: list[NewReservedSlot]
    time_budget_seconds: float = RESERVATION_TIME_BUDGET_SECONDS


@dataclass(frozen=True)
class ReservationWrite:
    """``POST /planting-runs/{key}/plan-slots``: the run's reservation for one entry is set to ``slot_keys``."""

    location_key: str
    run_key: str
    entry_key: str
    planned_species_key: str
    #: Ordered; the edge ``sequence`` is the 1-based position in this list.
    ordered_slot_keys: list[str]
    planned_from: date
    planned_until: date | None
    tenant_key: str
    time_budget_seconds: float = RESERVATION_TIME_BUDGET_SECONDS


@dataclass(frozen=True)
class PlantingRow:
    """One line of ``GET /locations/{key}/plantings`` (§11.3): a planned position or a plant."""

    state: str
    slot_key: str | None
    slot_id: str | None
    species_key: str
    cultivar_key: str | None = None
    plant_key: str | None = None
    instance_id: str | None = None
    run_key: str | None = None
    entry_key: str | None = None
    sequence: int | None = None
    planted_on: date | None = None
    removed_on: date | None = None
    termination_type: str | None = None
    planned_from: date | None = None
    planned_until: date | None = None


@dataclass(frozen=True)
class ClearBedWrite:
    """``POST /locations/{key}/clear``: end every live run and plant of the bed, archive its slots (GP-FR-055)."""

    location_key: str
    tenant_key: str
    termination_type: str
    removed_on: date
    #: The ``clearing`` event without its plants — the repository adds the ones it ended (the transaction's set).
    event: CareEvent
    time_budget_seconds: float = RESERVATION_TIME_BUDGET_SECONDS


@dataclass(frozen=True)
class ClearBedOutcome:
    plants_removed: int
    runs_completed: int
    slots_archived: int
    slots_released: int
    care_event_key: str
    removed_plant_keys: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QuickPlantedPlant:
    """One plant of the quick path: the plant, the index of its slot in :attr:`QuickPlantWrite.slots`, its history."""

    plant: PlantInstance
    slot_index: int | None
    history: PhaseHistory | None


@dataclass(frozen=True)
class QuickPlantWrite:
    """``POST /locations/{key}/quick-planting``: run, entry, slots and plants in one transaction (GP-API-017)."""

    location_key: str
    run: PlantingRun
    entry: PlantingRunEntry
    slots: list[Slot]
    plants: list[QuickPlantedPlant]
    run_history: PhaseHistory | None
    time_budget_seconds: float = RESERVATION_TIME_BUDGET_SECONDS


@dataclass(frozen=True)
class QuickPlantOutcome:
    run_key: str
    entry_key: str
    created_slot_keys: list[str]
    plant_keys: list[str]
    created_at: datetime


@dataclass(frozen=True)
class MixedRunDraft:
    """What the request says about one run of a mixed culture, before anything is validated or stored.

    ``free_points`` are the positions a grower set by hand for a ``free`` entry (bed-frame points); a computed
    layout needs none. Built by the router from the body, never trusted: the service stamps the tenant.
    """

    run: PlantingRun
    entry: PlantingRunEntry
    free_points: tuple[tuple[float, float], ...] = ()
    container_volume_l: float | None = None


@dataclass(frozen=True)
class MixedRunSlot:
    """A slot a run of a mixed culture reserves, with the ``sequence`` of its reservation edge."""

    slot: Slot
    sequence: int


@dataclass(frozen=True)
class MixedRunWrite:
    """One run of a mixed culture: the run, its single entry, and the slots it reserves."""

    run: PlantingRun
    entry: PlantingRunEntry
    planned_from: date
    planned_until: date | None
    slots: list[MixedRunSlot]


@dataclass(frozen=True)
class MixedRunsWrite:
    """``POST /planting-runs/mixed-culture``: every run of a mixed culture on one bed in **one** transaction."""

    location_key: str
    runs: list[MixedRunWrite]
    time_budget_seconds: float = RESERVATION_TIME_BUDGET_SECONDS


@dataclass(frozen=True)
class MixedRunsOutcome:
    """The keys the transaction created, one run after the other, in the order of the request."""

    run_keys: list[str]
    created_slot_keys: list[str]


class QuickPlantingInput(BaseModel):
    """What a grower reports in the field: *I planted n of this species here* (GP-API-017, GP-UX-027).

    The layout fields are optional: without a ``spacing_cm`` (or on a bed without geometry) the plants are
    recorded in the bed without positions. ``zone`` and ``free`` are not offered — a zone holds sown seed, not
    counted plants, and ``free`` places points by hand.
    """

    model_config = ConfigDict(extra="forbid")

    species_key: str = Field(min_length=1, max_length=200)
    cultivar_key: str | None = Field(default=None, max_length=200)
    quantity: int = Field(ge=1, le=QUICK_PLANTING_MAX_QUANTITY)
    planted_on: date | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    id_prefix: str | None = Field(default=None, pattern=r"^[A-Z]{2,5}$")
    spacing_cm: float | None = Field(default=None, ge=MIN_SPACING_CM, le=MAX_SPACING_CM)
    row_spacing_cm: float | None = Field(default=None, ge=MIN_ROW_SPACING_CM, le=MAX_SPACING_CM)
    row_direction: RowDirection | None = None
    layout_strategy: LayoutStrategy | None = None
    plan_role: PlanRole = PlanRole.MAIN_CROP
    rotation_override_reason: str | None = Field(default=None, max_length=MAX_ROTATION_OVERRIDE_REASON)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("layout_strategy")
    @classmethod
    def _counted_plants_only(cls, value: LayoutStrategy | None) -> LayoutStrategy | None:
        if value in (LayoutStrategy.ZONE, LayoutStrategy.FREE):
            raise ValueError("quick planting lays out counted plants: grid, rows or triangular.")
        return value

    @field_validator("plan_role")
    @classmethod
    def _no_fallow_run(cls, value: PlanRole) -> PlanRole:
        if value is PlanRole.FALLOW:
            raise ValueError("A fallow period has no planting run.")
        return value


@dataclass(frozen=True)
class QuickPlantingResult:
    run_key: str
    entry_key: str
    created_slot_keys: list[str]
    plant_keys: list[str]
    instance_ids: list[str]
    #: Hints that never block: ``layout.bed_without_geometry``, ``layout.capacity_exceeded`` …
    warnings: list[str] = field(default_factory=list)
