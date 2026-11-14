"""Write sets and read rows of the slot reservation (REQ-053 WP 3.2, GP-FR-055/064–066, GP-API-017…024).

Every write set is what the service has validated and the repository writes in **one transaction**
(GP-NFR-013); none of them is ever built from an HTTP body. A write set that names a ``location_key`` is
written under that bed's document lock, so two writers of one bed serialise (the loser answers 409).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Protocol

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
    #: The bed's ``slot_rules_revision`` read with the slots V-04/V-06 were checked against (#2773); ``None`` when
    #: the write carries no slot.
    slot_rules_revision: int | None = None
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
    #: The slot's role and sowing day, on a planned position only (§11.3 "gesät", W-015).
    slot_role: str | None = None
    sown_at: date | None = None


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
    #: The bed's ``slot_rules_revision`` read with the slots V-04/V-06 were checked against (#2773); ``None`` when
    #: the write carries no slot.
    slot_rules_revision: int | None = None
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
class ContainerVolumeWarning:
    """A run of a mixed culture whose pot is below its species' recommendation (W-016.5) - a warning, never a refusal.

    ``run_index`` is the position of the run in the request; ``recommended_l`` the lower value of the species'
    ``recommended_container_volume_l`` (``container_volume_calculator``).
    """

    run_index: int
    species_key: str
    container_volume_l: float
    recommended_l: float


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
    #: The bed's ``slot_rules_revision`` read with the slots V-04/V-06 were checked against (#2773); ``None`` when
    #: the write carries no slot.
    slot_rules_revision: int | None = None
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


# ── Thinning a sown row or zone (REQ-053 §11.3 "gesät", §12 ``thinning``, W-015) ──

#: Where the row spacing of a thinning count came from (#2862): the run entry or the species profile.
type RowSpacingSource = Literal["run", "species"]

#: The widest spacing a sown crop is thinned to (cm). Thinning is for direct-sown vegetables and herbs; anything
#: spaced wider is planted, not thinned (agrobiology review of WP 10.9). The run entry itself takes up to 1 500 cm.
MAX_THINNING_SPACING_CM = 200.0


class SlotThinningInput(BaseModel):
    """What the grower says when thinning a sown slot (``POST /slots/{key}/thinning``).

    The count follows from the slot's measure and ``thinning_to_cm``: the run's value unless the grower enters
    one here. ``count`` overrides the computed number (the seedlings actually left standing). Neither field has a
    default — without a spacing on the run or in the request and without a count the request is refused (E-10).

    ``row_spacing_cm`` counts only for a zone (#2862): a value here replaces the run's and the species profile's,
    an explicit ``null`` says "broadcast, no rows" (the square-grid estimate), and leaving the field out takes the
    run entry's ``row_spacing_cm``, else the lower value of the species' ``row_spacing_cm`` — never a constant.
    The bounds are those of the layout's row spacing (GP-FR-060).
    """

    model_config = ConfigDict(extra="forbid")

    thinning_to_cm: float | None = Field(default=None, gt=0, le=MAX_THINNING_SPACING_CM)
    row_spacing_cm: float | None = Field(default=None, ge=MIN_ROW_SPACING_CM, le=MAX_SPACING_CM)
    count: int | None = Field(default=None, ge=1, le=QUICK_PLANTING_MAX_QUANTITY)
    planted_on: date | None = None


@dataclass(frozen=True)
class SlotThinningPlan:
    """What thinning a sown slot would do, read before the grower confirms (``GET /slots/{key}/thinning``).

    ``thinning_to_cm`` is the run entry's value, ``None`` when the run has none (the grower must enter it).
    ``row_spacing_cm`` is the run entry's row spacing (``row_spacing_source = "run"``), else the lower value of the
    species profile's range (``"species"``, the range itself in ``species_row_spacing_cm``), else ``None`` — then a
    zone is counted on the square-grid estimate. ``count_formula`` names the rule behind ``suggested_count``:
    ``along_row``, ``rows`` or ``square_grid``. ``suggested_count`` is
    :func:`~app.domain.calculators.thinning_calculator.thinning_count` for those values, ``None`` without a spacing
    or without a measure.
    """

    slot_key: str
    slot_id: str
    slot_role: str
    sown_at: date
    run_key: str
    entry_key: str
    species_key: str
    cultivar_key: str | None
    measure_kind: str | None
    measure_value: float | None
    thinning_to_cm: float | None
    suggested_count: int | None
    max_count: int = QUICK_PLANTING_MAX_QUANTITY
    row_spacing_cm: float | None = None
    row_spacing_source: RowSpacingSource | None = None
    species_row_spacing_cm: str | None = None
    count_formula: str | None = None


@dataclass(frozen=True)
class SlotThinningWrite:
    """The plants a thinned slot gets, its cleared ``sown_at`` and the ``thinning`` care event — one transaction.

    ``sown_at`` is the day the service read: a slot thinned or re-sown in between no longer matches and the write
    is refused (409), and so is a slot whose reservation by ``run_key`` / ``entry_key`` was released meanwhile. A run
    still ``planned`` when the transaction reaches it turns ``active`` with ``run_phase_key`` and ``run_history``.
    """

    location_key: str
    slot_key: str
    sown_at: date
    run_key: str
    entry_key: str
    tenant_key: str
    plants: list[QuickPlantedPlant]
    #: The ``thinning`` event without its plants — the repository names the ones it created.
    event: CareEvent
    #: When the plants' (and a started run's) phase began: the thinning day.
    phase_started_at: datetime
    run_history: PhaseHistory | None = None
    run_phase_key: str | None = None
    #: Start the run if it is still ``planned`` when the transaction reaches it (decided there, not on the service's
    #: read); ``False`` leaves the run's status alone.
    activate_run: bool = True
    time_budget_seconds: float = RESERVATION_TIME_BUDGET_SECONDS


@dataclass(frozen=True)
class SlotThinningOutcome:
    plant_keys: list[str]
    instance_ids: list[str]
    care_event_key: str
    #: The run was still ``planned`` and the thinning started it.
    run_started: bool = False
