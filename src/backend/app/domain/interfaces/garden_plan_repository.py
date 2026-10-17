from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.common.types import SiteKey
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    BedCounters,
    PlanAuditEntry,
    PlanBatchOutcome,
    PlanBatchWrite,
    PlantShortInfo,
    SlotBatchOutcome,
    SlotBatchWrite,
    TaskCounter,
)
from app.domain.models.site import Location, Slot


@dataclass
class PlanReadData:
    """The documents behind ``GET /sites/{key}/plan``, read in one pass (GP-NFR-002)."""

    locations: list[Location] = field(default_factory=list)
    garden_objects: list[GardenObject] = field(default_factory=list)
    slots: list[Slot] = field(default_factory=list)
    plants: list[PlantShortInfo] = field(default_factory=list)
    task_counters: dict[str, TaskCounter] = field(default_factory=dict)
    #: Display name of the account that last changed the plan structure; ``None`` when unknown or erased.
    plan_updated_by_name: str | None = None


class IGardenPlanRepository(ABC):
    """Persistence of the garden plan beyond the single documents (REQ-053 §21.1, §21.3).

    Locations and garden objects carry no ``tenant_key`` (E-01, #2107): every read here
    takes the tenant keyword-only without a default and joins the site inside the query,
    so a foreign site answers with nothing instead of with its rows (§22.3 T-04).
    """

    @abstractmethod
    def load_structure(self, site_key: SiteKey, *, tenant_key: str) -> tuple[list[Location], list[GardenObject]]:
        """Every location and garden object of a site of ``tenant_key`` (the batch's working-copy basis)."""

    @abstractmethod
    def load_read_model(
        self, site_key: SiteKey, *, tenant_key: str, include_plants: bool, include_tasks: bool
    ) -> PlanReadData:
        """The documents of the plan read model; slots of archived runs are left out."""

    @abstractmethod
    def load_active_slots(
        self, site_key: SiteKey, location_keys: list[str], *, tenant_key: str, include_archived: bool = False
    ) -> list[Slot]:
        """Slots (``archived_at`` null, or all with ``include_archived``) of the named locations (V-04, V-06, V-20).

        The locations must belong to the tenant's site; a key of another site or tenant yields nothing.
        """

    @abstractmethod
    def bed_type_flags(self, location_type_keys: list[str]) -> dict[str, bool]:
        """``location_type_key`` → ``is_bed`` for the keys that resolve; an unknown key is absent."""

    @abstractmethod
    def count_active_plants(self, location_keys: list[str], *, tenant_key: str) -> int:
        """Plants of ``tenant_key`` with ``removed_on = null`` standing in any of the locations (V-09)."""

    @abstractmethod
    def apply_plan_batch(self, write: PlanBatchWrite) -> PlanBatchOutcome:
        """Write the set in one transaction, after re-checking the revision inside it (GP-NFR-013).

        Raises:
            PlanRevisionConflictError: the stored ``plan_revision`` is not the one expected.
            NotFoundError: the site is gone or not the tenant's.
        """

    @abstractmethod
    def list_audit(self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int) -> list[PlanAuditEntry]:
        """The site's plan change log, newest first."""

    # ── Single resources (WP 1.9, GP-API-010…015, GP-API-018) ─────────────────

    @abstractmethod
    def load_bed_counters(self, location_keys: list[str], *, tenant_key: str) -> dict[str, BedCounters]:
        """Plant, task and care counters for the named locations (which the caller took from an owned site).

        A location without any of them is absent from the result.
        """

    @abstractmethod
    def count_active_slots(self, site_key: SiteKey, *, tenant_key: str) -> int:
        """Slots (``archived_at`` null) in all locations of the tenant's site — the GP-NFR-017 quota counts these."""

    @abstractmethod
    def update_location_fields(self, location_key: str, fields: dict[str, Any]) -> None:
        """Write *only* ``fields`` (``None`` removes a stored value) — outside the plan revision (GP-API-010).

        The caller has resolved the location under the tenant through ``location_ownership``; the repository
        does not know the tenant (a location carries none, E-01).
        """

    @abstractmethod
    def update_slot_fields(self, slot_key: str, fields: dict[str, Any]) -> None:
        """Write *only* ``fields`` of a slot, nested objects replaced whole (a geometry may change its kind).

        The caller has resolved the slot under the tenant through ``location_ownership``.
        """

    @abstractmethod
    def irrigation_zone_site_key(self, zone_key: str, *, tenant_key: str) -> str | None:
        """``site_key`` of the tenant's irrigation zone ``zone_key``; ``None`` when absent or another tenant's."""

    @abstractmethod
    def substrate_visible(self, substrate_key: str, *, tenant_key: str) -> bool:
        """Whether the substrate is a catalogue one (no tenant) or the tenant's own (GP-NFR-058)."""

    @abstractmethod
    def reserved_among(self, candidates: list[str], *, tenant_key: str) -> set[str]:
        """The slots among ``candidates`` that a planting run of the tenant has reserved (``run_planned_at``, V-08)."""

    @abstractmethod
    def replace_slots(self, write: SlotBatchWrite) -> SlotBatchOutcome:
        """Delete the unoccupied slots named, insert the new ones and their ``has_slot`` edges — one transaction.

        Raises:
            DuplicateError: a ``slot_id`` of the location is taken (V-20, the unique index).
            WriteConflictError: a slot to delete became occupied or reserved after the service read it.
        """
