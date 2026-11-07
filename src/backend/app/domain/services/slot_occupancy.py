"""Who still stands on a slot — the one predicate both occupation writers free a slot by (#2727).

A slot is freed only when no plant is left on it. ``get_active_by_slot`` reads the ``placed_in`` edges, and those
are written when a plant is created and not re-pointed when a plant is moved off a slot (``PlantInstance.slot_key``
is): a plant counts as standing on the slot only while its own ``slot_key`` still names it.
"""

from __future__ import annotations

from app.common.types import SlotKey
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.models.plant_instance import PlantInstance


def plants_standing_on(
    plants: IPlantInstanceRepository, slot_key: SlotKey, *, tenant_key: str, leaving: str | None = None
) -> list[PlantInstance]:
    """The tenant's live plants on ``slot_key``, without ``leaving`` (the plant being taken off it)."""
    return [
        plant
        for plant in plants.get_active_by_slot(slot_key, tenant_key=tenant_key)
        if plant.slot_key == slot_key and (leaving is None or plant.key != leaving)
    ]
