from abc import ABC, abstractmethod
from collections.abc import Callable

from app.domain.engines.slot_reservation_engine import ActivePlant, Reservation
from app.domain.models.planting_reservation import (
    ClearBedOutcome,
    ClearBedWrite,
    PlantingRow,
    QuickPlantOutcome,
    QuickPlantWrite,
    ReservationReads,
    ReservationWrite,
    RunSlotsWrite,
)


class IPlantingReservationRepository(ABC):
    """Reservations of slots by planting runs, and the multi-collection writes around them (REQ-053 WP 3.2).

    Every method that takes ``tenant_key`` filters on the **run's** tenant (a slot carries none, E-01); the
    caller has resolved the bed through ``location_ownership`` before it passes a key here.
    """

    # ── Reads ─────────────────────────────────────────────────────────

    @abstractmethod
    def reservations_for(self, slot_keys: list[str], *, tenant_key: str) -> list[Reservation]:
        """The live reservations (runs ``planned``/``active``/``harvesting``) of the tenant on ``slot_keys``."""

    @abstractmethod
    def active_plants_in(self, slot_keys: list[str], *, tenant_key: str) -> list[ActivePlant]:
        """The tenant's plants standing in ``slot_keys`` (``placed_in``, ``removed_on`` null)."""

    @abstractmethod
    def reservations_of_run(self, run_key: str, *, tenant_key: str) -> list[Reservation]:
        """The ``run_planned_at`` edges of one run, ordered by entry and ``sequence``."""

    @abstractmethod
    def list_plantings(
        self, location_key: str, *, tenant_key: str, state: str | None, year: int | None
    ) -> list[PlantingRow]:
        """Planned positions and plants of one bed (§11.3), optionally of one state and one calendar year."""

    # ── Writes (one transaction each) ─────────────────────────────────

    @abstractmethod
    def place_run_layout(self, write: RunSlotsWrite) -> list[str]:
        """Insert the layout's slots with their ``has_slot`` and ``run_planned_at`` edges; the new slot keys in order.

        Raises:
            DuplicateError: a ``slot_id`` of the bed is taken (V-20).
            WriteConflictError: another writer of the bed was faster.
        """

    @abstractmethod
    def set_reservation(self, write: ReservationWrite, verify: Callable[[ReservationReads], None]) -> None:
        """Replace the run's reservation for one entry; ``verify`` re-checks V-08 inside the transaction.

        ``verify`` raises the domain error; the transaction aborts and nothing is written.
        """

    @abstractmethod
    def release_reservation(self, run_key: str, slot_key: str) -> bool:
        """Delete the ``run_planned_at`` edge of ``run_key`` to ``slot_key``; ``False`` when there was none."""

    @abstractmethod
    def drop_run_reservations(self, run_key: str, *, remove_layout_slots: bool) -> int:
        """Delete all reservation edges of a run that ended (or was deleted); returns the edges removed.

        ``remove_layout_slots`` also deletes the slots the run's layout created (``geometry_source = layout``)
        when no plant stands in them, no other run reserves them and they are not archived.
        """

    @abstractmethod
    def clear_bed(self, write: ClearBedWrite) -> ClearBedOutcome:
        """End every live run and plant of the bed, archive or release its slots and log ``clearing``."""

    @abstractmethod
    def quick_plant(self, write: QuickPlantWrite) -> QuickPlantOutcome:
        """Run, entry, slots, plants and their edges in one transaction (GP-API-017)."""
