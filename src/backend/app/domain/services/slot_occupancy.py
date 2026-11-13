"""Who still stands on a slot — the one predicate both occupation writers free a slot by (#2727) — and the refusals
a slot answers when it is already taken.

A slot is freed only when no plant is left on it. ``get_active_by_slot`` reads the ``placed_in`` edges, and those
are written when a plant is created and not re-pointed when a plant is moved off a slot (``PlantInstance.slot_key``
is): a plant counts as standing on the slot only while its own ``slot_key`` still names it.
"""

from __future__ import annotations

from datetime import date

from app.common.enums import SlotRole
from app.common.exceptions import PlanError
from app.common.types import SlotKey
from app.domain.engines.slot_reservation_engine import LIVE_RUN_STATUSES
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_reservation_repository import IPlantingReservationRepository
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Slot

#: 409 - plants stand in the slot already (sowing and thinning a row/zone, a single plant on a position).
ERROR_SLOT_OCCUPIED = "slot.occupied"
#: 409 - V-08: the slot is planned (reserved by a live run) or planted in the window asked for.
ERROR_SLOT_ALREADY_PLANNED = "slot.already_planned"


def plants_standing_on(
    plants: IPlantInstanceRepository, slot_key: SlotKey, *, tenant_key: str, leaving: str | None = None
) -> list[PlantInstance]:
    """The tenant's live plants on ``slot_key``, without ``leaving`` (the plant being taken off it)."""
    return [
        plant
        for plant in plants.get_active_by_slot(slot_key, tenant_key=tenant_key)
        if plant.slot_key == slot_key and (leaving is None or plant.key != leaving)
    ]


def require_free_position(
    slot: Slot,
    *,
    plants: IPlantInstanceRepository,
    reservations: IPlantingReservationRepository | None,
    tenant_key: str,
    today: date,
) -> None:
    """Refuse a single plant on a ``position`` slot that is already taken (REQ-053 GP-UX-071, V-25, #2913).

    A position holds one plant (``Slot`` caps its capacity at 1 and a planting run puts one plant on it). It is
    taken when a live plant of the tenant stands on it (409 ``slot.occupied``) or a live planting run of the tenant
    reserves it for a window that has not ended (409 ``slot.already_planned``, V-08): that run puts its own plant
    there. Rows and zones are not checked here - they take several plants (``capacity_plants``) and are sown and
    thinned through their run.

    Check-then-write, like the planting run path (``PlantingRunService.create_plants`` reads the free slots, then
    writes): two requests that arrive at the same moment can both pass. There is no unique edge to lean on -
    ``placed_in`` keeps the edges of plants that left a slot.
    """
    if slot.slot_role is not SlotRole.POSITION or not slot.key:
        return
    standing = plants_standing_on(plants, slot.key, tenant_key=tenant_key)
    if standing:
        raise PlanError(
            ERROR_SLOT_OCCUPIED,
            "A plant stands on this planting position already.",
            status_code=409,
            field="slot_key",
            slot_key=slot.key,
        )
    if reservations is None:
        return
    for reservation in reservations.reservations_for([slot.key], tenant_key=tenant_key):
        if reservation.run_status not in LIVE_RUN_STATUSES:
            continue
        if reservation.planned_until is not None and reservation.planned_until < today:
            continue
        raise PlanError(
            ERROR_SLOT_ALREADY_PLANNED,
            "A planting run reserves this planting position.",
            status_code=409,
            field="slot_key",
            slot_key=slot.key,
            conflicting_run_key=reservation.run_key,
            overlap_from=reservation.planned_from.isoformat() if reservation.planned_from else None,
            overlap_until=reservation.planned_until.isoformat() if reservation.planned_until else None,
        )
