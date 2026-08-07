"""#951 — every confirm-produced watering row carries its tenant_key.

The twin of ``test_watering_log_tenant_key_stamping`` (#580), for the path that
was missed at the time. ``WateringService.confirm_watering`` built its
``WateringEvent`` and every derived ``FeedingEvent`` without a ``tenant_key``;
both models default the field to ``""`` and ``BaseArangoRepository.create`` does
not stamp it afterwards.

Nothing noticed, because no read filtered on the field. #947 added the predicate
to ``get_by_plant``, ``get_by_location`` and ``get_stats_by_location`` — at which
point every row this live UI path produces (``WateringConfirmDialog``,
``PlantingRunDetailPage``) would have dropped out of all three. So the property
under test is not "the field is set" but "a confirmation is still *visible*
afterwards", which is what would actually have broken.

``PlantingRunService.create_plants`` had the same omission on its batch
``PlantInstance``s although ``run.tenant_key`` was right there; that is pinned
here too, since it is the same defect in the same family.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.nutrient_plan import NutrientPlan
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.watering_event import WateringEvent
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.watering_service import WateringService
from tests.conftest import wire_get_or_raise

TENANT = "tenant-A"
PLANT_KEY = "plant-1"
RUN_KEY = "run-1"


class FakeWateringRepo:
    """In-memory watering-event repo that mirrors the tenant-scoping contract.

    ``get_by_plant`` filters on ``tenant_key`` exactly like the real Arango
    repository does since #947, so a tenantless event surfaces in *no* scoped
    read — which is precisely the regression #951 describes.
    """

    def __init__(self) -> None:
        self.events: list[WateringEvent] = []

    def create(self, event: WateringEvent) -> WateringEvent:
        stored = WateringEvent(**{**event.model_dump(), "_key": f"we-{len(self.events) + 1}"})
        self.events.append(stored)
        return stored

    def get_by_plant(self, plant_key: str, offset: int = 0, limit: int = 50, *, tenant_key: str) -> list[WateringEvent]:
        if not tenant_key:
            raise ValueError("get_by_plant is tenant-scoped and requires a non-empty tenant_key")
        return [e for e in self.events if e.tenant_key == tenant_key and plant_key in e.plant_keys]


class FakeFeedingRepo:
    def __init__(self) -> None:
        self.events: list[FeedingEvent] = []

    def create(self, event: FeedingEvent) -> FeedingEvent:
        self.events.append(event)
        return event


def _service() -> tuple[WateringService, FakeWateringRepo, FakeFeedingRepo]:
    watering_repo = FakeWateringRepo()
    feeding_repo = FakeFeedingRepo()

    run_repo = MagicMock()
    run_repo.get_run_nutrient_plan_key.return_value = "plan-1"
    run_repo.get_run_plants.return_value = [{"_key": PLANT_KEY, "slot_key": "slot-1"}]

    plan_repo = MagicMock()
    plan_repo.get_by_key.return_value = NutrientPlan(_key="plan-1", tenant_key=TENANT, name="Plan")

    task_repo = MagicMock()
    task_repo.get_by_key.return_value = None

    service = WateringService(
        repo=watering_repo,
        engine=MagicMock(),
        site_repo=MagicMock(),
        run_repo=run_repo,
        task_repo=task_repo,
        feeding_repo=feeding_repo,
        nutrient_plan_repo=plan_repo,
    )
    return service, watering_repo, feeding_repo


class TestConfirmWateringStampsTheTenant:
    def test_the_event_is_visible_in_the_plants_history_afterwards(self):
        """The property #947 would otherwise have broken, not just "the field is set"."""
        service, watering_repo, _ = _service()

        service.confirm_watering(run_key=RUN_KEY, task_key="task-1", tenant_key=TENANT)

        assert [e.key for e in watering_repo.get_by_plant(PLANT_KEY, tenant_key=TENANT)] == ["we-1"]

    def test_the_derived_feeding_events_are_stamped_too(self):
        service, _, feeding_repo = _service()

        service.confirm_watering(run_key=RUN_KEY, task_key="task-1", tenant_key=TENANT)

        assert feeding_repo.events
        assert all(e.tenant_key == TENANT for e in feeding_repo.events)

    def test_quick_confirm_stamps_the_same_way(self):
        service, watering_repo, feeding_repo = _service()

        service.quick_confirm_watering(RUN_KEY, "task-1", tenant_key=TENANT)

        assert watering_repo.events[0].tenant_key == TENANT
        assert all(e.tenant_key == TENANT for e in feeding_repo.events)

    def test_another_tenant_does_not_see_the_confirmation(self):
        """The positive direction's counterpart: the stamp is a real boundary."""
        service, watering_repo, _ = _service()

        service.confirm_watering(run_key=RUN_KEY, task_key="task-1", tenant_key=TENANT)

        assert watering_repo.get_by_plant(PLANT_KEY, tenant_key="tenant-B") == []

    def test_omitting_the_tenant_entirely_is_a_type_error(self):
        service, _, _ = _service()

        with pytest.raises(TypeError):
            service.confirm_watering(run_key=RUN_KEY, task_key="task-1")


class TestBatchCreatedPlantsCarryTheirRunsTenant:
    """``create_plants`` built its instances without a tenant (#951)."""

    def _run_service(self) -> tuple[PlantingRunService, MagicMock]:
        run = PlantingRun(
            _key=RUN_KEY,
            tenant_key=TENANT,
            name="Tomaten 2026",
            run_type=PlantingRunType.MONOCULTURE,
            status=PlantingRunStatus.PLANNED,
            location_key="loc-1",
        )
        run_repo = MagicMock()
        run_repo.get_by_key.return_value = run
        wire_get_or_raise(run_repo, "PlantingRun")
        run_repo.get_entries.return_value = [
            PlantingRunEntry(_key="e1", run_key=RUN_KEY, species_key="sp-tomato", quantity=1, id_prefix="TOM"),
        ]
        run_repo.get_existing_ids_at_location.return_value = set()

        plant_repo = MagicMock()
        plant_repo.create.side_effect = lambda plant: plant.model_copy(update={"key": plant.instance_id})

        engine = MagicMock()
        engine.validate_run_type_constraints.return_value = None
        engine.generate_plant_ids.return_value = [
            {"instance_id": "TOM-1", "species_key": "sp-tomato", "cultivar_key": None}
        ]

        site_repo = MagicMock()
        site_repo.get_slots_by_location.return_value = []

        service = PlantingRunService(
            run_repo=run_repo,
            plant_repo=plant_repo,
            engine=engine,
            site_repo=site_repo,
        )
        return service, plant_repo

    def test_every_created_instance_carries_the_runs_tenant(self):
        service, plant_repo = self._run_service()

        service.create_plants(RUN_KEY)

        created = [call.args[0] for call in plant_repo.create.call_args_list]
        assert created
        assert all(plant.tenant_key == TENANT for plant in created)
