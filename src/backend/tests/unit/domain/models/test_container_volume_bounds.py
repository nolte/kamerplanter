"""One upper bound for a pot volume on every input (#2832 review): the plant instance's 500 litres.

The inputs refuse more; the read model of a stored slot does not, because ``Slot.container_volume_l`` has been
stored without an upper bound since WP 1.7 and a bounded read model would turn such a document into a 500.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.plant_instances.schemas import PlantCreate
from app.domain.models.garden_plan import SlotBatchItem
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import MAX_CONTAINER_VOLUME_L, Slot

_RECT = {"kind": "rect", "origin": [0.1, 0.1], "width_m": 0.3, "length_m": 0.3}


def _upper_bound(model: type, field: str) -> object:
    return next(m.le for m in model.model_fields[field].metadata if getattr(m, "le", None) is not None)


def test_the_bound_is_the_plant_instance_bound() -> None:
    assert MAX_CONTAINER_VOLUME_L == 500.0
    assert _upper_bound(PlantInstance, "container_volume_liters") == MAX_CONTAINER_VOLUME_L
    assert _upper_bound(PlantCreate, "container_volume_liters") == MAX_CONTAINER_VOLUME_L


class TestSlotBatchItem:
    def test_the_bound_itself_is_accepted(self) -> None:
        item = SlotBatchItem(slot_id="A01", geometry=_RECT, container_volume_l=MAX_CONTAINER_VOLUME_L)

        assert item.container_volume_l == MAX_CONTAINER_VOLUME_L

    @pytest.mark.parametrize("volume", [500.5, 10_000.0])
    def test_above_the_bound_is_refused(self, volume: float) -> None:
        with pytest.raises(ValidationError) as caught:
            SlotBatchItem(slot_id="A01", geometry=_RECT, container_volume_l=volume)

        assert [error["loc"] for error in caught.value.errors()] == [("container_volume_l",)]


def test_a_stored_slot_above_the_bound_still_reads() -> None:
    slot = Slot(slot_id="TENT01_A1", location_key="loc", container_volume_l=800.0)

    assert slot.container_volume_l == 800.0
