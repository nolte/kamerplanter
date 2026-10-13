"""#2107 review — stored run references are re-resolved under the tenant at action time.

A run's plants come from ``run_contains`` edges and its nutrient plan from a stored
key. Neither is proof of ownership: a legacy edge can point at another tenant's
plant, a legacy plan key at another tenant's private plan. Every write that walks
them now resolves each one again and leaves out what is not the caller's:

* SEC-001 sweep — ``PlantingRunService.batch_remove`` / ``batch_update_phase_dates``
  / ``_reassign_plant_slots`` and both ``confirm_watering`` paths skip a foreign
  plant on a run edge (``ActivityPlanService.apply_plan_to_run`` is covered in
  ``tests/api/test_activity_plan_apply_tenant_scope.py``).
* SEC-002 — both ``confirm_watering`` paths follow the run's plan only when the
  tenant may read it; an unreadable plan is treated as no plan.
* SEC-003 — ``FeedingService.create_event``, ``SuccessionPlanService.create_plan``
  and ``HarvestService.create_harvest_batch`` stamp the caller's tenant and refuse
  an empty one.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.common.exceptions import NotFoundError
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.harvest import HarvestBatch
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.services.feeding_service import FeedingService
from app.domain.services.harvest_service import HarvestService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.succession_plan_service import SuccessionPlanService
from app.domain.services.watering_log_service import WateringLogService
from app.domain.services.watering_service import WateringService
from tests.api.test_run_and_tank_writes_check_the_tenant import _Sites
from tests.conftest import wire_or_raise

OWN = "tenant_anna"
FOREIGN = "tenant_bob"
RUN = "run_1"


def _plant(key: str, owner: str, slot_key: str | None = None) -> PlantInstance:
    return PlantInstance(
        _key=key,
        instance_id=key.upper(),
        species_key="sp_tomato",
        planted_on=date(2026, 1, 1),
        tenant_key=owner,
        slot_key=slot_key,
    )


#: The run's edges: its own plant and, through a legacy edge, another tenant's.
_ROWS = [{"_key": "p_own", "slot_key": "slot_own"}, {"_key": "p_b", "slot_key": "slot_b"}]


def _plants() -> MagicMock:
    known = {"p_own": _plant("p_own", OWN, "slot_own"), "p_b": _plant("p_b", FOREIGN, "slot_b")}
    repo = MagicMock()
    repo.get_by_key.side_effect = known.get
    return repo


def _run_repo(status: PlantingRunStatus = PlantingRunStatus.ACTIVE) -> MagicMock:
    run = PlantingRun(_key=RUN, tenant_key=OWN, name="Lauf", run_type=PlantingRunType.MONOCULTURE, status=status)
    repo = MagicMock()
    repo.get_by_key.side_effect = lambda key: run if key == RUN else None
    wire_or_raise(repo, "PlantingRun")
    repo.get_run_plants.side_effect = lambda key, include_detached=False: [dict(r) for r in _ROWS]
    repo.update.side_effect = lambda key, doc: doc
    return repo


def _updated_plants(plant_repo: MagicMock) -> list[str]:
    return [call.args[0] for call in plant_repo.update.call_args_list]


# ── SEC-001 sweep: PlantingRunService walks run edges ───────────────────────


def test_batch_remove_never_removes_another_tenants_plant() -> None:
    plant_repo = _plants()
    service = PlantingRunService(run_repo=_run_repo(), plant_repo=plant_repo, engine=MagicMock())
    result = service.batch_remove(RUN, tenant_key=OWN)
    assert _updated_plants(plant_repo) == ["p_own"]
    assert "p_b" not in str(result)


def test_batch_phase_dates_never_touch_another_tenants_phase_history() -> None:
    plant_repo = _plants()
    phase_repo = MagicMock()
    phase_repo.get_phase_history.side_effect = lambda key: [
        SimpleNamespace(key=f"h_{key}", phase_key="veg", entered_at=datetime(2026, 1, 1, tzinfo=UTC), exited_at=None)
    ]
    service = PlantingRunService(run_repo=_run_repo(), plant_repo=plant_repo, engine=MagicMock(), phase_repo=phase_repo)
    service.batch_update_phase_dates(RUN, "veg", entered_at=datetime(2026, 2, 1, tzinfo=UTC), tenant_key=OWN)
    assert [c.args[0] for c in phase_repo.get_phase_history.call_args_list] == ["p_own"]
    assert [c.args[0] for c in phase_repo.update_phase_history.call_args_list] == ["h_p_own"]
    assert _updated_plants(plant_repo) == ["p_own"]


def test_reslotting_a_run_moves_only_the_tenants_own_plants() -> None:
    sites = _Sites()
    plant_repo = _plants()
    service = PlantingRunService(run_repo=_run_repo(), plant_repo=plant_repo, engine=MagicMock(), site_repo=sites)
    service._reassign_plant_slots(RUN, "loc_own", tenant_key=OWN)
    assert set(_updated_plants(plant_repo)) == {"p_own"}
    assert sites.slots["slot_b"].currently_occupied is True


def test_reslotting_reads_plants_through_the_repository_interface() -> None:
    """The release loop called ``plant_repo.get``, which the real repository does not have."""
    plant_repo = MagicMock(spec=["get_by_key", "update"])
    plant_repo.get_by_key.side_effect = _plants().get_by_key.side_effect
    service = PlantingRunService(run_repo=_run_repo(), plant_repo=plant_repo, engine=MagicMock(), site_repo=_Sites())
    service._reassign_plant_slots(RUN, "loc_own", tenant_key=OWN)
    assert "p_own" in _updated_plants(plant_repo)


# ── SEC-001 sweep + SEC-002: both confirm_watering paths ────────────────────


def _confirm_world(*, plan_readable: bool) -> SimpleNamespace:
    run_repo = _run_repo()
    run_repo.get_run_nutrient_plan_key.return_value = "plan_b"
    plans = MagicMock()
    schedule = SimpleNamespace(application_method="fertigation")
    if plan_readable:
        plans.get_readable_or_raise.return_value = SimpleNamespace(key="plan_b", watering_schedule=schedule)
    else:
        plans.get_readable_or_raise.side_effect = NotFoundError("NutrientPlan", "plan_b")
    created: list = []
    store = MagicMock()
    store.create.side_effect = lambda doc: created.append(doc) or doc.model_copy(update={"key": "w1"})
    feeding = MagicMock()
    task_repo = MagicMock(get_by_key=MagicMock(return_value=None))
    common = dict(run_repo=run_repo, task_repo=task_repo, nutrient_plan_repo=plans, plant_repo=_plants())
    return SimpleNamespace(
        events=WateringService(store, MagicMock(), MagicMock(), feeding_repo=feeding, **common),
        logs=WateringLogService(store, MagicMock(), MagicMock(), **common),
        created=created,
        feeding=feeding,
        plans=plans,
    )


def test_an_unreadable_run_plan_is_no_plan_for_a_watering_event() -> None:
    world = _confirm_world(plan_readable=False)
    world.events.confirm_watering(RUN, "", tenant_key=OWN)
    (event,) = world.created
    assert event.nutrient_plan_key is None
    assert event.application_method == "drench"
    world.feeding.create.assert_not_called()
    world.plans.get_readable_or_raise.assert_called_once_with("plan_b", tenant_key=OWN)


def test_an_unreadable_run_plan_is_no_plan_for_a_watering_log() -> None:
    world = _confirm_world(plan_readable=False)
    world.logs.confirm_watering(RUN, "", tenant_key=OWN)
    (log,) = world.created
    assert log.nutrient_plan_key is None
    assert log.application_method == "drench"


def test_a_readable_run_plan_is_followed() -> None:
    world = _confirm_world(plan_readable=True)
    world.events.confirm_watering(RUN, "", tenant_key=OWN)
    (event,) = world.created
    assert event.nutrient_plan_key == "plan_b"
    assert event.application_method == "fertigation"


def test_a_watering_event_and_its_feeding_events_leave_out_a_foreign_plant_on_a_run_edge() -> None:
    world = _confirm_world(plan_readable=True)
    world.events.confirm_watering(RUN, "", tenant_key=OWN)
    (event,) = world.created
    assert event.plant_keys == ["p_own"]
    assert [c.args[0].plant_key for c in world.feeding.create.call_args_list] == ["p_own"]


def test_a_watering_log_leaves_out_a_foreign_plant_and_its_slot() -> None:
    world = _confirm_world(plan_readable=False)
    world.logs.confirm_watering(RUN, "", tenant_key=OWN)
    (log,) = world.created
    assert log.plant_keys == ["p_own"]
    assert log.slot_keys == ["slot_own"]


# ── SEC-003: creates stamp the caller's tenant and refuse an empty one ──────


def _succession() -> tuple[SuccessionPlanService, MagicMock]:
    repo = MagicMock()
    repo.create.side_effect = lambda plan: plan
    return SuccessionPlanService(repo, MagicMock(), site_repo=MagicMock(), species_resolver=MagicMock()), repo


def _succession_plan(owner: str = "") -> SuccessionPlan:
    return SuccessionPlan(
        tenant_key=owner,
        name="Salat",
        species_key="sp_lettuce",
        interval_days=14,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 5, 1),
        plants_per_batch=4,
    )


def _harvest() -> tuple[HarvestService, MagicMock]:
    repo = MagicMock()
    repo.batch_id_exists.return_value = False
    repo.create_batch.side_effect = lambda batch: batch
    ipm = MagicMock()
    ipm.check_harvest_safety.return_value = (True, [])
    return HarvestService(repo, ipm, MagicMock(), MagicMock()), repo


def test_the_creates_refuse_an_empty_tenant() -> None:
    feeding_repo = MagicMock()
    succession, succession_repo = _succession()
    harvest, harvest_repo = _harvest()
    with pytest.raises(ValueError, match="tenant_key"):
        FeedingService(feeding_repo).create_event(FeedingEvent(plant_key="p1", volume_applied_liters=1), tenant_key="")
    with pytest.raises(ValueError, match="tenant_key"):
        succession.create_plan(_succession_plan(), tenant_key="")
    with pytest.raises(ValueError, match="tenant_key"):
        harvest.create_harvest_batch("p1", HarvestBatch(), tenant_key="")
    feeding_repo.create.assert_not_called()
    succession_repo.create.assert_not_called()
    harvest_repo.create_batch.assert_not_called()


def test_the_creates_stamp_the_callers_tenant_over_the_models() -> None:
    feeding_repo = MagicMock()
    feeding_repo.create.side_effect = lambda event: event
    succession, _repo = _succession()
    harvest, _hrepo = _harvest()

    event = FeedingService(feeding_repo).create_event(
        FeedingEvent(tenant_key=FOREIGN, plant_key="p1", volume_applied_liters=1), tenant_key=OWN
    )
    plan = succession.create_plan(_succession_plan(FOREIGN), tenant_key=OWN)
    batch = harvest.create_harvest_batch("p1", HarvestBatch(tenant_key=FOREIGN), tenant_key=OWN)

    assert (event.tenant_key, plan.tenant_key, batch.tenant_key) == (OWN, OWN, OWN)
    # The Karenz gate and the batch-id lookup read the stamped tenant, not the model's.
    harvest._ipm.check_harvest_safety.assert_called_once()
    assert harvest._ipm.check_harvest_safety.call_args.kwargs["tenant_key"] == OWN


# ── SEC-001 sweep: a run-scoped diary entry on a foreign plant ──────────────


@pytest.mark.parametrize("plant_key", ["p_b", "p_unknown"], ids=["foreign-on-legacy-edge", "not-in-run"])
def test_a_run_scoped_diary_entry_refuses_a_plant_that_is_not_the_tenants_run_member(plant_key: str) -> None:
    from app.common.enums import TenantRole
    from app.domain.models.plant_diary_entry import PlantDiaryEntry
    from app.domain.services.plant_diary_service import PlantDiaryService

    run_repo = MagicMock()
    run_repo.get_run_plants.return_value = [
        {"_key": "p_own", "tenant_key": OWN},
        {"_key": "p_b", "tenant_key": FOREIGN},
    ]
    diary_repo = MagicMock()
    service = PlantDiaryService(diary_repo, run_repo=run_repo)
    entry = PlantDiaryEntry(tenant_key=OWN, created_by="u_anna", entry_type="note", title="Notiz", text="Blatt gelb")
    with pytest.raises(NotFoundError) as exc:
        service.create_entry(plant_key, entry, run_key=RUN, actor_role=TenantRole.LEAD, capture_environment=False)
    assert exc.value.message == f"PlantingRunEntry with key '{plant_key}' not found."
    diary_repo.create.assert_not_called()
