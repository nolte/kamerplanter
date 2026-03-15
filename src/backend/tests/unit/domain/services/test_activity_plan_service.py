from unittest.mock import MagicMock

import pytest

from app.common.enums import SkillLevel, StressLevel, StressTolerance
from app.domain.engines.activity_plan_engine import ActivityPlanEngine
from app.domain.models.activity import Activity
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.task import TaskTemplate, WorkflowTemplate
from app.domain.services.activity_plan_service import ActivityPlanService

from app.common.enums import ActivityCategory


def _make_species():
    m = MagicMock()
    m.key = "sp1"
    m.common_names = ["Tomato"]
    m.scientific_name = "Solanum lycopersicum"
    m.family_key = None
    return m


def _make_lifecycle():
    return LifecycleConfig(
        _key="lc1",
        species_key="sp1",
    )


def _make_phase(name="vegetative", order=0, duration=20):
    return GrowthPhase(
        _key=f"ph_{name}",
        name=name,
        display_name=name.title(),
        typical_duration_days=duration,
        sequence_order=order,
        stress_tolerance=StressTolerance.MEDIUM,
    )


def _make_activity(name="Topping", key="act1"):
    return Activity(
        _key=key,
        name=name,
        category=ActivityCategory.TRAINING_HST,
        stress_level=StressLevel.MEDIUM,
        skill_level=SkillLevel.INTERMEDIATE,
        recovery_days_default=3,
    )


def _make_task_template(
    name="Topping", key="tt1", activity_key="act1",
    enabled=True, trigger_phase="vegetative",
):
    return TaskTemplate(
        _key=key,
        name=name,
        activity_key=activity_key,
        enabled=enabled,
        trigger_phase=trigger_phase,
        workflow_template_key="wt1",
        stress_level=StressLevel.MEDIUM,
        skill_level=SkillLevel.INTERMEDIATE,
    )


def _make_workflow_template(key="wt1", name="Test WF"):
    return WorkflowTemplate(
        _key=key,
        name=name,
        auto_generated=True,
        species_key="sp1",
    )


@pytest.fixture()
def service():
    engine = ActivityPlanEngine()
    activity_repo = MagicMock()
    phase_repo = MagicMock()
    task_repo = MagicMock()
    run_repo = MagicMock()
    species_repo = MagicMock()

    return ActivityPlanService(
        engine=engine,
        activity_repo=activity_repo,
        phase_repo=phase_repo,
        task_repo=task_repo,
        planting_run_repo=run_repo,
        species_repo=species_repo,
    )


class TestGeneratePlan:
    def test_resolves_lifecycle_and_generates(self, service):
        species = _make_species()
        service._species_repo.get_by_key.return_value = species
        service._phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle()
        service._phase_repo.get_phases_by_lifecycle.return_value = [_make_phase()]
        service._activity_repo.get_all.return_value = ([_make_activity()], 1)

        wt_mock = _make_workflow_template()
        service._task_repo.create_workflow_template.return_value = wt_mock

        wt = service.generate_plan("sp1")
        assert wt.name == "Test WF"
        service._task_repo.create_workflow_template.assert_called_once()
        # Should create at least one task template
        assert service._task_repo.create_task_template.call_count >= 1

    def test_uses_explicit_lifecycle_key(self, service):
        species = _make_species()
        service._species_repo.get_by_key.return_value = species
        service._phase_repo.get_phases_by_lifecycle.return_value = [_make_phase()]
        service._activity_repo.get_all.return_value = ([_make_activity()], 1)

        wt_mock = _make_workflow_template()
        service._task_repo.create_workflow_template.return_value = wt_mock

        service.generate_plan("sp1", lifecycle_key="lc_custom")
        service._phase_repo.get_phases_by_lifecycle.assert_called_with("lc_custom")


class TestGetOrGenerateForSpecies:
    def test_returns_existing_workflow(self, service):
        existing_wt = _make_workflow_template()
        service._task_repo.get_auto_generated_workflow_for_species.return_value = existing_wt

        result = service.get_or_generate_for_species("sp1")
        assert result.key == "wt1"
        # Should not call generate
        service._task_repo.create_workflow_template.assert_not_called()

    def test_generates_when_no_existing(self, service):
        service._task_repo.get_auto_generated_workflow_for_species.return_value = None
        species = _make_species()
        service._species_repo.get_by_key.return_value = species
        service._phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle()
        service._phase_repo.get_phases_by_lifecycle.return_value = [_make_phase()]
        service._activity_repo.get_all.return_value = ([_make_activity()], 1)

        wt_mock = _make_workflow_template()
        service._task_repo.create_workflow_template.return_value = wt_mock

        result = service.get_or_generate_for_species("sp1")
        service._task_repo.create_workflow_template.assert_called_once()


class TestRegenerateForSpecies:
    def test_deletes_old_and_creates_new(self, service):
        existing_wt = _make_workflow_template()
        service._task_repo.get_auto_generated_workflow_for_species.return_value = existing_wt
        species = _make_species()
        service._species_repo.get_by_key.return_value = species
        service._phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle()
        service._phase_repo.get_phases_by_lifecycle.return_value = [_make_phase()]
        service._activity_repo.get_all.return_value = ([_make_activity()], 1)

        wt_mock = _make_workflow_template(key="wt2")
        service._task_repo.create_workflow_template.return_value = wt_mock

        result = service.regenerate_for_species("sp1")
        service._task_repo.delete_task_templates_for_workflow.assert_called_once_with("wt1")
        service._task_repo.delete_workflow_template.assert_called_once_with("wt1")
        service._task_repo.create_workflow_template.assert_called_once()


class TestApplyPlanToPlant:
    def test_creates_tasks_for_enabled_templates(self, service):
        wt = _make_workflow_template()
        service._task_repo.get_workflow_template_by_key.return_value = wt
        service._task_repo.get_task_templates_for_workflow.return_value = [
            _make_task_template(key="tt1", enabled=True),
            _make_task_template(key="tt2", name="Skipped", enabled=False),
        ]
        created_task = MagicMock()
        created_task.key = "t1"
        service._task_repo.create_task.return_value = created_task

        result = service.apply_plan_to_plant("wt1", "plant1")

        # Only 1 enabled template
        assert result["created_count"] == 1
        assert service._task_repo.create_task.call_count == 1

    def test_creates_activity_edge(self, service):
        wt = _make_workflow_template()
        service._task_repo.get_workflow_template_by_key.return_value = wt
        service._task_repo.get_task_templates_for_workflow.return_value = [
            _make_task_template(key="tt1", activity_key="act1", enabled=True),
        ]
        created_task = MagicMock()
        created_task.key = "t1"
        service._task_repo.create_task.return_value = created_task

        service.apply_plan_to_plant("wt1", "plant1")

        service._task_repo.create_task_activity_edge.assert_called_once_with("t1", "act1")

    def test_skips_disabled_templates(self, service):
        wt = _make_workflow_template()
        service._task_repo.get_workflow_template_by_key.return_value = wt
        service._task_repo.get_task_templates_for_workflow.return_value = [
            _make_task_template(key="tt1", enabled=False),
            _make_task_template(key="tt2", enabled=False),
        ]

        result = service.apply_plan_to_plant("wt1", "plant1")
        assert result["created_count"] == 0
        assert service._task_repo.create_task.call_count == 0


class TestApplyPlanToRun:
    def test_applies_to_all_plants(self, service):
        wt = _make_workflow_template()
        service._task_repo.get_workflow_template_by_key.return_value = wt
        service._task_repo.get_task_templates_for_workflow.return_value = [
            _make_task_template(key="tt1", enabled=True),
        ]

        run = MagicMock()
        run.key = "run1"
        service._run_repo.get_by_key.return_value = run
        service._run_repo.get_run_plants.return_value = [
            {"key": "p1"}, {"key": "p2"},
        ]
        created_task = MagicMock()
        created_task.key = "t1"
        service._task_repo.create_task.return_value = created_task

        result = service.apply_plan_to_run("wt1", "run1")
        assert result["plant_count"] == 2
        assert result["total_tasks"] == 2  # 1 enabled x 2 plants
