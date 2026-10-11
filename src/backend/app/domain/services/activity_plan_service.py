from typing import Any

from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership, verify_tenant_read_access
from app.data_access.arango.base_repository import get_all_pages
from app.domain.engines.activity_plan_engine import ActivityPlanEngine
from app.domain.interfaces.activity_repository import IActivityRepository
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun
from app.domain.models.task import Task, WorkflowTemplate


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
        phase_seq_repo: IPhaseSequenceRepository | None = None,
        plant_repo: IPlantInstanceRepository | None = None,
    ) -> None:
        self._engine = engine
        self._activity_repo = activity_repo
        self._phase_repo = phase_repo
        self._task_repo = task_repo
        self._run_repo = planting_run_repo
        self._species_repo = species_repo
        self._family_repo = family_repo
        self._phase_seq_repo = phase_seq_repo
        # #2107 review SEC-001: the apply targets are resolved under the caller's
        # tenant here, not by a router pre-check.
        self._plant_repo = plant_repo

    def _resolve_species_info(
        self,
        species_key: str,
    ) -> tuple:
        """Resolve species, species_name, and family_name from species_key."""
        species = None
        species_name = species_key
        family_name = ""
        if self._species_repo:
            species = self._species_repo.get_or_raise(species_key)
            species_name = (species.common_names[0] if species.common_names else "") or species.scientific_name
            if species.family_key and self._family_repo:
                family = self._family_repo.get_by_key(species.family_key)
                if family:
                    family_name = family.name
        return species, species_name, family_name

    def _resolve_lifecycle_key(
        self,
        species_key: str,
        lifecycle_key: str | None,
    ) -> str:
        """Resolve lifecycle key, falling back to species default.

        Tries PhaseSequence first for auto-resolution, then LifecycleConfig.
        """
        own = self._species_lifecycle_keys(species_key)
        if lifecycle_key:
            # Only one of the species' own lifecycles (security review of #1876,
            # SEC-001): a key taken as given copied another species' phases —
            # another tenant's private lifecycle included — into the plan. One
            # answer for a foreign and an unknown key.
            if lifecycle_key not in own:
                raise ValidationError(f"Lifecycle '{lifecycle_key}' does not belong to species '{species_key}'.")
            return lifecycle_key
        if not own:
            raise ValidationError(
                f"No lifecycle config found for species '{species_key}'.",
            )
        return own[0]

    def _species_lifecycle_keys(self, species_key: str) -> list[str]:
        """The species' own lifecycle keys, preferred first: its PhaseSequence, then its LifecycleConfig."""
        keys: list[str] = []
        if self._phase_seq_repo:
            seq = self._phase_seq_repo.get_sequence_by_species(species_key)
            if seq and seq.key:
                keys.append(seq.key)
        lc = self._phase_repo.get_lifecycle_by_species(species_key)
        if lc and lc.key:
            keys.append(lc.key)
        return keys

    def generate_plan(
        self,
        species_key: str,
        lifecycle_key: str | None = None,
        growth_system: str | None = None,
        skill_level: str | None = None,
        *,
        tenant_key: str,
    ) -> WorkflowTemplate:
        """Generate an activity plan and persist as WorkflowTemplate + TaskTemplates.

        ``tenant_key`` decides who owns the result and has no default (#2107): the
        owner of a persisted plan is named by every caller, never implied. Empty
        means the globally **shared template** every tenant reads — what
        :meth:`get_or_generate_for_species` passes for a global species: a
        generated plan is derived from the species and its phases, nothing
        tenant-specific goes into it, and generating one per tenant would
        multiply identical documents. A
        tenant only ever owns a plan once they have changed it, which is
        copy-on-write's whole premise (#1003).

        :meth:`regenerate_for_species` passes the caller's tenant instead,
        because rebuilding is a write.
        """
        species, species_name, family_name = self._resolve_species_info(species_key)

        lc_key = self._resolve_lifecycle_key(species_key, lifecycle_key)

        # Try PhaseSequence first for phase resolution
        phases = []
        if self._phase_seq_repo:
            seq = self._phase_seq_repo.get_sequence_by_key(lc_key)
            if seq:
                from app.domain.models.lifecycle import GrowthPhase

                entries = self._phase_seq_repo.get_entries_for_sequence(lc_key)
                for entry in entries:
                    defn = self._phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
                    if defn:
                        phases.append(
                            GrowthPhase(
                                _key=entry.key,
                                name=defn.name,
                                display_name=defn.display_name,
                                lifecycle_key=lc_key,
                                typical_duration_days=entry.override_duration_days or defn.typical_duration_days,
                                sequence_order=entry.sequence_order,
                                is_terminal=entry.is_terminal,
                                allows_harvest=entry.allows_harvest,
                                is_recurring=entry.is_recurring,
                                stress_tolerance=defn.stress_tolerance,
                                watering_interval_days=defn.watering_interval_days,
                            )
                        )

        # Fallback to LifecycleConfig phases
        if not phases:
            phases = self._phase_repo.get_phases_by_lifecycle(lc_key)

        if not phases:
            raise ValidationError(
                f"No growth phases found for lifecycle '{lc_key}'.",
            )

        # Load all activities
        # Every catalogue activity this plan's owner may read, not the first 500 (#2015):
        # a shared template (tenant_key "") is built from global activities only, so a
        # tenant's own activity can never land in a plan every tenant reads (#2119).
        activities = get_all_pages(self._activity_repo, tenant_key=tenant_key)

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
        wt.tenant_key = tenant_key
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
        *,
        tenant_key: str,
    ) -> WorkflowTemplate:
        """Return the caller's activity plan for a species, generating it if absent.

        The lookup answers ``tenant_key``'s private copy when they have one and
        the shared template otherwise (#1003) — a union, not an equality; see
        :meth:`ITaskRepository.get_auto_generated_workflow_for_species`. What is
        generated when neither exists is the **shared** template, not a private
        plan: reading a plan is not a write, and it is the write that forks.
        """
        species_owner = self._readable_species_owner(species_key, tenant_key)
        existing = self._task_repo.get_auto_generated_workflow_for_species(
            species_key,
            tenant_key=tenant_key,
        )
        if existing:
            return existing
        # A plan derived from a *global* species with its defaults is the shared
        # template. One derived from a private (own or granted) species is the
        # caller's: a shared template would carry the private species' name to
        # every tenant (#1871 B10). So is one shaped by the caller's own
        # parameters — the first caller must not decide what every tenant reads
        # (security review of #1876, SEC-001).
        caller_shaped = any(value is not None for value in (lifecycle_key, growth_system, skill_level))
        shared = species_owner == "" and not caller_shaped
        return self.generate_plan(
            species_key=species_key,
            lifecycle_key=lifecycle_key,
            growth_system=growth_system,
            skill_level=skill_level,
            tenant_key="" if shared else tenant_key,
        )

    def _readable_species_owner(self, species_key: str, tenant_key: str) -> str:
        """The species' owner if ``tenant_key`` may read it — global, own or granted (#1092) — else 404.

        The generate routes resolved ``species_key`` unscoped, so another
        tenant's private species produced a plan (#1871 B10). With no tenant in
        play (an internal caller) the species is only required to exist.
        """
        if self._species_repo is None:
            # Fail closed for a tenant request (security review of #1876, SEC-004):
            # without the repository nothing can tell a private species from a
            # global one, and "global" would generate the shared template.
            if tenant_key:
                raise NotFoundError("Species", species_key)
            return ""
        species = self._species_repo.get_or_raise(species_key)
        owner = getattr(species, "tenant_key", "") or ""
        if (
            tenant_key
            and owner not in ("", tenant_key)
            and not self._species_repo.is_granted_to(species_key, tenant_key)
        ):
            raise NotFoundError("Species", species_key)
        return owner

    def regenerate_for_species(
        self,
        species_key: str,
        lifecycle_key: str | None = None,
        growth_system: str | None = None,
        skill_level: str | None = None,
        *,
        tenant_key: str,
    ) -> WorkflowTemplate:
        """Rebuild the caller's activity plan from scratch.

        Regenerating is a **write**, and the loudest one the plan editor has: it
        drops a plan and builds a new one. Applied to the shared template it
        would therefore discard every tenant's plan at once — the same defect as
        an edit (#1003), only total. So it forks like every other write: the
        result is owned by ``tenant_key``, and the shared template is left for
        the tenants still reading it.

        Only the caller's *own* previous copy is deleted. Where the lookup
        answers the shared template — the caller has never forked — there is
        nothing of theirs to delete, and the new private plan simply supersedes
        it for them.

        With no tenant in play (``tenant_key == ""``, an internal caller rather
        than a route) this is the pre-#1003 behaviour unchanged: the shared plan
        is replaced in place.
        """
        self._readable_species_owner(species_key, tenant_key)
        existing = self._task_repo.get_auto_generated_workflow_for_species(
            species_key,
            tenant_key=tenant_key,
        )
        if existing and existing.key and existing.tenant_key == tenant_key:
            self._task_repo.delete_task_templates_for_workflow(existing.key)
            self._task_repo.delete_workflow_template(existing.key)
        return self.generate_plan(
            species_key=species_key,
            lifecycle_key=lifecycle_key,
            growth_system=growth_system,
            skill_level=skill_level,
            tenant_key=tenant_key,
        )

    def apply_plan_to_plant(
        self,
        workflow_template_key: str,
        plant_key: str,
        *,
        tenant_key: str,
    ) -> dict:
        """Create tasks from a workflow template's task templates for a single plant.

        ``tenant_key`` comes from the verified path context (#1000), never the
        request body, and is what every created ``Task`` is stamped with — so the
        stamping below is correct by construction rather than by the caller's word.

        The plan itself is resolved for that same tenant: a caller may apply the
        globally generated **shared template** (``tenant_key == ""``) or their own
        forked copy (#1003), but not another tenant's private copy.
        :func:`verify_tenant_read_access` spells that union out — a foreign
        tenant's workflow raises ``NotFoundError`` (404), the same answer an
        unknown key gets, so the route is no cross-tenant existence oracle. A
        strict ``== tenant_key`` here would instead reject the shared template
        every reader depends on, which is the #324 trap.
        """
        self._owned_plant(plant_key, tenant_key=tenant_key)
        return self._create_plan_tasks(
            self._readable_workflow(workflow_template_key, tenant_key), plant_key, tenant_key
        )

    def _readable_workflow(self, workflow_template_key: str, tenant_key: str) -> str:
        workflow = self._task_repo.get_workflow_template_or_raise(workflow_template_key)
        verify_tenant_read_access(workflow, tenant_key, "WorkflowTemplate")
        return workflow_template_key

    def _owned_plant(self, plant_key: str, *, tenant_key: str) -> PlantInstance:
        """The plant ``plant_key`` of ``tenant_key``, or 404 (#2107 review SEC-001).

        The route used to check the plant first and this method trusted it. Fails
        closed when no plant repository is wired: nothing could tell an own plant
        from a foreign one.
        """
        if self._plant_repo is None:
            raise NotFoundError("PlantInstance", plant_key)
        plant = self._plant_repo.get_or_raise(plant_key)
        verify_tenant_ownership(plant, tenant_key, "PlantInstance")
        return plant

    def _owned_run(self, run_key: str, *, tenant_key: str) -> PlantingRun:
        """The run ``run_key`` of ``tenant_key``, or 404 (#2107 review SEC-001)."""
        run = self._run_repo.get_or_raise(run_key)
        verify_tenant_ownership(run, tenant_key, "PlantingRun")
        return run

    def _create_plan_tasks(self, workflow_template_key: str, plant_key: str, tenant_key: str) -> dict[str, Any]:
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
                entity_key=plant_key,
                entity_type="plant_instance",
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
        *,
        tenant_key: str,
    ) -> dict:
        """Create tasks from a workflow template for all plants of a run of ``tenant_key``.

        The run is resolved under the tenant here (#2107 review SEC-001). Its plants
        come from ``run_contains`` edges, not from the caller: each is resolved again
        and one that is missing or belongs to another tenant (a legacy edge) is
        skipped — no task is created for it and it is not counted.
        """
        self._owned_run(run_key, tenant_key=tenant_key)
        workflow_key = self._readable_workflow(workflow_template_key, tenant_key)

        plant_keys = [self._row_key(row) for row in self._run_repo.get_run_plants(run_key)]
        owned = [key for key in plant_keys if key and self._is_owned_plant(key, tenant_key)]
        if not owned:
            raise ValidationError("PlantingRun has no plants.")

        total_keys: list[str] = []
        for plant_key in owned:
            result = self._create_plan_tasks(workflow_key, plant_key, tenant_key)
            total_keys.extend(result["task_keys"])

        return {
            "run_key": run_key,
            "plant_count": len(owned),
            "tasks_per_plant": len(total_keys) // max(len(owned), 1),
            "total_tasks": len(total_keys),
            "task_keys": total_keys,
        }

    @staticmethod
    def _row_key(row: dict[str, Any]) -> str:
        return row.get("key") or row.get("_key") or ""

    def _is_owned_plant(self, plant_key: str, tenant_key: str) -> bool:
        if self._plant_repo is None:
            return False
        plant = self._plant_repo.get_by_key(plant_key)
        return plant is not None and bool(tenant_key) and plant.tenant_key == tenant_key
