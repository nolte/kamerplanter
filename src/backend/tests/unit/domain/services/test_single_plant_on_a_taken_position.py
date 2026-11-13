"""A single plant on a planting position that is already taken is refused (REQ-053 GP-UX-071, V-25, #2913).

Measured before this rule: ``PlantInstanceService.create_plant`` with a ``slot_key`` checked only crop rotation and
neighbours, so ``POST /plant-instances`` put a second plant on a position that already carried one (and onto a
position a planned run had reserved) and answered 201. The plan's tool "Pflanze setzen" re-read the slot first, which
narrows the window but cannot close it.

The rule is narrow on purpose:

* only a ``position`` slot - rows and zones take several plants (``capacity_plants``) through their run;
* only a **live** plant of the tenant (``removed_on`` null, its own ``slot_key`` still naming the slot) - a removed
  plant leaves the position free;
* only a reservation of a **live** run whose window has not ended - a completed or cancelled run released its slots;
* also with ``skip_validation`` - occupation is integrity, not advice.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.common.datetimes import today_utc
from app.common.enums import SlotRole
from app.common.exceptions import PlanError
from app.domain.engines.slot_reservation_engine import Reservation
from tests.support.single_plant_fakes import (
    OTHER,
    TENANT,
    build_service,
    make_plant,
    make_reservation,
    make_slot,
)


def test_a_free_position_takes_one_plant() -> None:
    service, _plants, sites, _ = build_service({"s1": make_slot("s1")})
    created = service.create_plant(make_plant(slot_key="s1"), tenant_key=TENANT)
    assert created.slot_key == "s1"
    assert sites.occupied == ["s1"]


def test_a_position_with_a_live_plant_refuses_a_second_one_409_slot_occupied() -> None:
    standing = make_plant(_key="p-old", instance_id="TOM-1", slot_key="s1")
    service, plants, sites, _ = build_service({"s1": make_slot("s1")}, standing=[standing])
    with pytest.raises(PlanError) as refused:
        service.create_plant(make_plant(slot_key="s1"), tenant_key=TENANT)
    assert refused.value.status_code == 409
    assert refused.value.error_code == "slot.occupied"
    assert refused.value.details[0]["field"] == "slot_key"
    assert refused.value.details[0]["slot_key"] == "s1"
    assert plants.created == []
    assert sites.occupied == []


def test_the_refusal_holds_with_skip_validation_too() -> None:
    standing = make_plant(_key="p-old", slot_key="s1")
    service, plants, _, _ = build_service({"s1": make_slot("s1")}, standing=[standing])
    with pytest.raises(PlanError):
        service.create_plant(make_plant(slot_key="s1"), skip_validation=True, tenant_key=TENANT)
    assert plants.created == []


def test_a_removed_plant_leaves_the_position_free() -> None:
    gone = make_plant(_key="p-old", slot_key="s1", removed_on=date(2026, 10, 1))
    service, plants, _, _ = build_service({"s1": make_slot("s1")}, standing=[gone])
    service.create_plant(make_plant(slot_key="s1"), tenant_key=TENANT)
    assert len(plants.created) == 1


def test_another_tenants_plant_is_not_read_as_standing_on_the_position() -> None:
    foreign = make_plant(_key="p-foreign", slot_key="s1", tenant_key=OTHER)
    service, plants, _, _ = build_service({"s1": make_slot("s1")}, standing=[foreign])
    service.create_plant(make_plant(slot_key="s1"), tenant_key=TENANT)
    assert len(plants.created) == 1


@pytest.mark.parametrize("role", [SlotRole.ROW, SlotRole.ZONE])
def test_rows_and_zones_keep_taking_several_plants(role: SlotRole) -> None:
    standing = make_plant(_key="p-old", slot_key="r1")
    service, plants, _, _ = build_service(
        {"r1": make_slot("r1", role, capacity=20)}, standing=[standing], reservations=[make_reservation("r1")]
    )
    service.create_plant(make_plant(slot_key="r1"), tenant_key=TENANT)
    assert len(plants.created) == 1


def test_a_position_a_live_run_reserves_refuses_409_slot_already_planned() -> None:
    service, plants, _, _ = build_service({"s1": make_slot("s1")}, reservations=[make_reservation("s1")])
    with pytest.raises(PlanError) as refused:
        service.create_plant(make_plant(slot_key="s1"), tenant_key=TENANT)
    assert refused.value.status_code == 409
    assert refused.value.error_code == "slot.already_planned"
    detail = refused.value.details[0]
    assert detail["conflicting_run_key"] == "run-7"
    assert detail["overlap_from"] == (today_utc() + timedelta(days=10)).isoformat()
    assert plants.created == []


@pytest.mark.parametrize(
    "reservation",
    [
        make_reservation("s1", status="completed"),
        make_reservation("s1", status="cancelled"),
        make_reservation("s1", until=today_utc() - timedelta(days=1)),
    ],
    ids=["completed-run", "cancelled-run", "window-ended"],
)
def test_a_released_or_ended_reservation_does_not_block(reservation: Reservation) -> None:
    service, plants, _, _ = build_service({"s1": make_slot("s1")}, reservations=[reservation])
    service.create_plant(make_plant(slot_key="s1"), tenant_key=TENANT)
    assert len(plants.created) == 1


def test_the_reservation_read_is_scoped_to_the_callers_tenant() -> None:
    service, _, _, reservations = build_service({"s1": make_slot("s1")})
    service.create_plant(make_plant(slot_key="s1"), tenant_key=TENANT)
    assert reservations.asked == [(["s1"], TENANT)]


def test_a_plant_without_a_slot_is_not_checked() -> None:
    service, plants, _, reservations = build_service({}, reservations=[make_reservation("s1")])
    service.create_plant(make_plant(), tenant_key=TENANT)
    assert len(plants.created) == 1
    assert reservations.asked == []


def test_the_dependency_wiring_hands_the_service_the_reservation_reader() -> None:
    """Built from the real factory, inspected on the object - a substring check on the source passes when unwired."""
    from app.common import dependencies

    original_get_db = dependencies.get_db
    dependencies.get_db = lambda: MagicMock()  # type: ignore[assignment]
    try:
        service = dependencies.get_plant_instance_service()
    finally:
        dependencies.get_db = original_get_db  # type: ignore[assignment]
    assert service._reservation_repo is not None
