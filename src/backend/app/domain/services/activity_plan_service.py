from typing import TYPE_CHECKING

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.task import Task, WorkflowTemplate

if TYPE_CHECKING:
    from app.domain.engines.activity_plan_engine import ActivityPlanEngine
    from app.domain.interfaces.activity_repository import IActivityRepository
    from app.domain.interfaces.phase_repository import IPhaseRepository
    from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
    from app.domain.interfaces.task_repository import ITaskRepository


class ActivityPlanService:
    def __init__(
        self,
        engine: ActivityPlanEngine,
        activity_repo: IActivityRepository,
        phase_repo: IPhaseRepository,
        task_repo: ITaskRepository,
        planting_run_repo: IPlantingRunRepository,
        species_repo=None,
        family_repo=None,
    ) -> None:
        self._engine = engine
        self._activity_repo = activity_repo
        self._phase_repo = phase_repo
        self._task_repo = task_repo
        self._run_repo = planting_run_repo
        self._species_repo = species_repo
        self._family_repo = family_repo

    def _resolve_species_info(
        self,
        species_key: str,
    ) -> tuple:
        """Resolve species, species_name, and family_name from species_key."""
        species = None
        species_name = species_key
        family_name = ""
        if self._species_repo:
            species = self._species_repo.get_by_key(species_key)
            if species:
                species_name = (species.common_names[0] if species.common_names else "") or species.scientific_name
                if species.family_key and self._family_repo:
                    family = self._family_repo.get_by_key(species.family_key)
                    if family:
                        family_name = family.name
            else:
                raise NotFoundError("Species", species_key)
        return species, species_name, family_name

    def _resolve_lifecycle_key(
        self,
        species_key: str,
        lifecycle_key: str | None,
    ) -> str:
        """Resolve lifecycle key, falling back to species default."""
        if lifecycle_key:
            return lifecycle_key
        lc = self._phase_repo.get_lifecycle_by_species(species_key)
        if not lc:
            raise ValidationError(
                f"No lifecycle config found for species '{species_key}'.",
            )
        return lc.key or ""

    def generate_plan(
        self,
        species_key: str,
        lifecycle_key: str | None = None,
        growth_system: str | None = None,
        skill_level: str | None = None,
    ) -> WorkflowTemplate:
        """Generate an activity plan and persist as WorkflowTemplate + TaskTemplates."""
        species, species_name, family_name = self._resolve_species_info(species_key)

        lc_key = self._resolve_lifecycle_key(species_key, lifecycle_key)
        phases = self._phase_repo.get_phases_by_lifecycle(lc_key)
        if not phases:
            raise ValidationError(
                f"No growth phases found for lifecycle '{lc_key}'.",
            )

        # Load all activities
        activities, _ = self._activity_repo.get_all(offset=0, limit=500)

        wt, templates = self._engine.generate_plan(
            species_name=species_name,
            phases=phases,
            activities=activities,
            growth_system=growth_system,
            skill_level=skill_level,
            species=species,
            family_name=family_name,
        )

        # Persist WorkflowTemplate
        wt.species_key = species_key
        wt.lifecycle_key = lifecycle_key or lc_key
        wt = self._task_repo.create_workflow_template(wt)

        # Persist TaskTemplates
        for tt in templates:
            tt.workflow_template_key = wt.key
            self._task_repo.create_task_template(tt)

        return wt

    def get_or_generate_for_species(
        self,
        species_key: str,
        lifecycle_key: str | None = None,
        growth_system: str | None = None,
        skill_level: str | None = None,
    ) -> WorkflowTemplate:
        """Return existing auto-generated workflow or generate a new one."""
        existing = self._task_repo.get_auto_generated_workflow_for_species(species_key)
        if existing:
            return existing
        return self.generate_plan(
            species_key=species_key,
            lifecycle_key=lifecycle_key,
            growth_system=growth_system,
            skill_level=skill_level,
        )

    def regenerate_for_species(
        self,
        species_key: str,
        lifecycle_key: str | None = None,
        growth_system: str | None = None,
        skill_level: str | None = None,
    ) -> WorkflowTemplate:
        """Delete existing auto-generated workflow and generate a new one."""
        existing = self._task_repo.get_auto_generated_workflow_for_species(species_key)
        if existing and existing.key:
            self._task_repo.delete_task_templates_for_workflow(existing.key)
            self._task_repo.delete_workflow_template(existing.key)
        return self.generate_plan(
            species_key=species_key,
            lifecycle_key=lifecycle_key,
            growth_system=growth_system,
            skill_level=skill_level,
        )

    def apply_plan_to_plant(
        self,
        workflow_template_key: str,
        plant_key: str,
        tenant_key: str = "",
    ) -> dict:
        """Create tasks from a workflow template's task templates for a single plant."""
        wt = self._task_repo.get_workflow_template_by_key(workflow_template_key)
        if not wt:
            raise NotFoundError("WorkflowTemplate", workflow_template_key)

        templates = self._task_repo.get_task_templates_for_workflow(workflow_template_key)
        created_keys: list[str] = []

        for tt in templates:
            if not tt.enabled:
                continue

            task = Task(
                tenant_key=tenant_key,
                name=tt.name,
                name_de=tt.name_de,
                instruction=tt.instruction or tt.rationale,
                instruction_de=tt.instruction_de or tt.rationale_de,
                category=tt.category,
                plant_key=plant_key,
                status="dormant",
                priority="medium",
                skill_level=tt.skill_level,
                stress_level=tt.stress_level,
                estimated_duration_minutes=tt.estimated_duration_minutes,
                trigger_phase=tt.trigger_phase,
                activity_key=tt.activity_key,
                template_key=tt.key,
            )
            created = self._task_repo.create_task(task)
            if created.key and tt.activity_key:
                self._task_repo.create_task_activity_edge(
                    created.key,
                    tt.activity_key,
                )
            created_keys.append(created.key or "")

        return {"created_count": len(created_keys), "task_keys": created_keys}

    def apply_plan_to_run(
        self,
        workflow_template_key: str,
        run_key: str,
        tenant_key: str = "",
    ) -> dict:
        """Create tasks from a workflow template for all plants in a run."""
        run = self._run_repo.get_by_key(run_key)
        if not run:
            raise NotFoundError("PlantingRun", run_key)

        plant_dicts = self._run_repo.get_run_plants(run_key)
        if not plant_dicts:
            raise ValidationError("PlantingRun has no plants.")

        total_keys: list[str] = []
        for pd in plant_dicts:
            plant_key = pd.get("key", pd.get("_key", ""))
            result = self.apply_plan_to_plant(
                workflow_template_key,
                plant_key,
                tenant_key,
            )
            total_keys.extend(result["task_keys"])

        return {
            "run_key": run_key,
            "plant_count": len(plant_dicts),
            "tasks_per_plant": len(total_keys) // max(len(plant_dicts), 1),
            "total_tasks": len(total_keys),
            "task_keys": total_keys,
        }
