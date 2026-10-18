from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import AttachmentCategory, TaskCategory, TaskOrigin, TaskStatus, TenantRole, WorkflowTargetType
from app.common.exceptions import ForbiddenError, KarenzViolationError, NotFoundError, PlanError, ValidationError
from app.common.log_privacy import log_tenant
from app.common.tenant_guard import verify_tenant_ownership, verify_tenant_read_access
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.engines.recurrence_engine import RecurrenceEngine
from app.domain.engines.task_completion_engine import HARVEST_BATCHES, TaskCompletionEngine
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.interfaces.task_completion_repository import ITaskCompletionRepository
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.models.care_event import UNDO_REASON, CareEvent, CareEventInput, CareEventOrigin
from app.domain.models.task import (
    ChecklistItem,
    Task,
    TaskAuditEntry,
    TaskComment,
    TaskTemplate,
    WorkflowExecution,
    WorkflowPhase,
    WorkflowTemplate,
)
from app.domain.models.task_completion import (
    MAX_BATCH_COMPLETION,
    CompletionActor,
    CompletionWrite,
    DomainDocument,
    TaskCompletionDetails,
    UndoWrite,
)
from app.domain.services.care_event_service import check_performed_instant, check_void_allowed
from app.domain.services.notification_propagation_service import NotificationPropagationService

if TYPE_CHECKING:
    from app.domain.services.care_event_service import CareEventService
    from app.domain.services.harvest_service import HarvestService

logger = structlog.get_logger(__name__)

#: Rows the unscoped task queue answers with at most.
#:
#: Named rather than inline because it is the number the whole #1484/#1503 class
#: turns on: anything past this cut is invisible to a caller that narrows the
#: answer, so every filter has to be asked of the *server* — and a reader of
#: either layer has to be able to find the cap that makes that true.
QUEUE_LIMIT = 200

#: At most this many clones per "for every plant" request (REQ-053 GP-FR-081); a bed holds a few dozen plants.
MAX_FAN_OUT = 200

# ── Update allow-lists (mass assignment, #965) ──
#
# The three ``update_*`` methods below used to loop over the caller's dict and
# ``setattr`` every entry onto the loaded model. That is mass assignment: the
# request body decided which *fields* were written, not the service — and since
# no domain model sets ``validate_assignment`` (#968), none of those writes was
# validated either. ``BaseArangoRepository.update_fields`` already states the
# obligation these sets discharge: a partial update must be built from an
# explicit allow-list, never from a raw body.
#
# Each set is the field list the corresponding request schema exposes, so no
# reachable edit is lost. What they keep out is what an editor must never move:
# identity and audit fields (``key``, ``created_at``, ``updated_at``), the
# ownership marker ``tenant_key`` and the ``is_system`` flag that guards the
# global catalog, and foreign references no route exposes (``activity_key``,
# ``phase_definition_key``) and which are therefore unverified.

#: Fields ``update_workflow_template`` may write (mirrors ``WorkflowTemplateUpdate``).
WORKFLOW_TEMPLATE_UPDATABLE_FIELDS = frozenset(
    {
        "name",
        "description",
        "version",
        "species_compatible",
        "growth_system",
        "difficulty_level",
        "category",
        "tags",
        "target_entity_types",
    }
)

#: Fields ``update_workflow_phase`` may write (mirrors ``WorkflowPhaseUpdate``).
#: ``workflow_template_key`` is deliberately absent: a phase belongs to the
#: workflow it was created under, and re-pointing it is how it would land in
#: another tenant's workflow.
WORKFLOW_PHASE_UPDATABLE_FIELDS = frozenset(
    {
        "name",
        "description",
        "phase_order",
        "duration_days",
        "stress_tolerance",
        "trigger_phase",
    }
)

#: Fields ``update_task_template`` may write (mirrors ``TaskTemplateUpdate``).
#: ``workflow_template_key`` is included because moving a task template between
#: the caller's own workflows is a legitimate edit — and it is exactly the field
#: :meth:`TaskService._verify_workflow_template_reference` checks, so the check
#: stays live on the update path instead of being dead code.
#:
#: **It is not reachable over HTTP, and that is left as it is (#964, #965).**
#: ``TaskTemplateUpdate`` does not declare the field, so Pydantic's
#: ``extra='ignore'`` drops it from a request body. Declaring it would make the
#: reference check genuinely reachable rather than accidentally unnecessary —
#: but it would also *widen* the write surface, and not only in theory: the SPA's
#: two inline editors (the enabled switch and the day-offset field) send
#: ``{...template, enabled: …}``, and ``TaskTemplateResponse`` carries
#: ``workflow_template_key``. Declaring the field turns that spread from
#: "silently ignored" into a re-point written on every toggle and every
#: keystroke, and any client posting a stale or partial template would move or
#: orphan it. The field therefore stays undeclared, and the guard stays live for
#: the non-HTTP callers that do reach this method.
TASK_TEMPLATE_UPDATABLE_FIELDS = frozenset(
    {
        "name",
        "instruction",
        "category",
        "trigger_type",
        "trigger_phase",
        "days_offset",
        "stress_level",
        "estimated_duration_minutes",
        "requires_photo",
        "timer_duration_seconds",
        "timer_label",
        "tools_required",
        "skill_level",
        "optimal_time_of_day",
        "workflow_template_key",
        "workflow_phase_key",
        "sequence_order",
        "default_checklist",
        "require_all_checklist_items",
    }
)


#: Fields the *activity-plan editor* may write on a task template (#992).
#: Mirrors ``app.api.v1.activity_plans.schemas.TaskTemplateUpdateRequest``, which
#: is a strictly smaller surface than the workflow editor's ``TaskTemplateUpdate``
#: above: the activity-plan tab only switches an activity on and off, re-times it
#: and re-points its trigger phase. Kept as its own set rather than folded into
#: :data:`TASK_TEMPLATE_UPDATABLE_FIELDS` for two reasons — an allow-list mirrors
#: exactly one request schema, and ``enabled`` (which only this editor exposes)
#: would otherwise silently widen the workflow editor's write surface too.
ACTIVITY_PLAN_TASK_TEMPLATE_UPDATABLE_FIELDS = frozenset(
    {
        "enabled",
        "days_offset",
        "trigger_phase",
    }
)


#: Refusal raised when a caller tries to write a *child* of a globally seeded
#: system workflow (#965 item 3, #992). Deliberately the same ``ValidationError``
#: — HTTP 422, ``VALIDATION_ERROR`` — that ``update_workflow_template`` and
#: ``delete_workflow_template`` already raise on the parent itself, rather than a
#: third convention for what is the same rule one level down. It is not the 404 a
#: foreign or unknown parent produces: that answer means "you may not even see
#: this", while a system workflow is visible to every tenant on purpose and only
#: refuses to be written into. The message names the supported way forward,
#: because duplicating is what the caller actually wants and it still works.
#:
#: Shared by both child surfaces: the tenant-scoped ``/tasks`` child routes
#: (#984) and the activity-plan template routes (#992), which were developed in
#: parallel and deliberately defined this contract identically so that the second
#: one to land collapsed into a single definition rather than leaving the project
#: with two refusal wordings for one rule.
SYSTEM_WORKFLOW_CHILD_REFUSAL = (
    "Cannot modify system workflow templates. "
    "Duplicate the workflow first to get an editable copy of its phases and task templates."
)


def _allowed(data: dict, allowed_fields: frozenset[str]) -> dict:
    """Return only the entries of ``data`` the caller is allowed to write.

    Everything else is dropped rather than rejected, mirroring how the request
    schemas already treat an unknown field (Pydantic ``extra='ignore'``): the
    body cannot widen the set of fields an update touches.
    """
    return {field: value for field, value in data.items() if field in allowed_fields}


#: Refusal for a write into a *shared* workflow: one with ``tenant_key == ""`` that is
#: not a seeded system template — the generated activity plans ``ActivityPlanService``
#: persists for every tenant of a species (#2101). Every tenant reads that one row, so
#: an in-place write is a write on every tenant's plan. A 403 rather than the 422 of a
#: system template because the cure differs: the caller is not asked to duplicate a
#: seed, they are told the row is not theirs. The activity-plan editor never reaches
#: this: it forks the plan on a write (#1003), and so does ``PUT`` on the workflow.
SHARED_WORKFLOW_REFUSAL = (
    "This workflow template is shared by every tenant and cannot be modified in place. "
    "Duplicate it to get an editable copy of your own."
)


def _refuse_system_workflow(workflow: WorkflowTemplate) -> None:
    """Stop a child write whose parent is a globally seeded system workflow or a shared plan.

    The one place the "system templates are read-only" rule is applied to a
    *resolved* parent, so the three child-write paths (task-template create,
    task-template re-point, phase create/update/delete) cannot drift apart. The
    two parent-level guards in :meth:`TaskService.update_workflow_template` and
    :meth:`TaskService.delete_workflow_template` keep their own wording — they
    refuse a different verb on a different object — but raise the same error.
    """
    if workflow.is_system:
        raise ValidationError(SYSTEM_WORKFLOW_CHILD_REFUSAL)
    if not workflow.tenant_key:
        raise ForbiddenError(SHARED_WORKFLOW_REFUSAL)


def _as_aware_utc(value: datetime | None) -> datetime | None:
    """Anchor a naive datetime to UTC so it can be compared safely.

    Persisted task datetimes carry mixed timezone-awareness: values parsed from
    a full ISO timestamp are aware, while a date-only ``due_date`` (the common
    case for a task created via the date picker) is stored naive. Comparing the
    two raises ``TypeError`` and would abort the surrounding flow (e.g. skip the
    recurrence follow-up on completion), so naive values are anchored to UTC.
    ``None`` passes through unchanged.
    """
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class TaskService:
    def __init__(
        self,
        repo: ITaskRepository,
        hst_validator: HSTValidator,
        dependency_resolver: DependencyResolver,
        recurrence: RecurrenceEngine | None = None,
        notification_propagation: NotificationPropagationService | None = None,
        attachment_repo: IAttachmentRepository | None = None,
        membership_lookup: Callable[[str, str], Any] | None = None,
        completion: ITaskCompletionRepository | None = None,
        care_events: CareEventService | None = None,
        harvests: HarvestService | None = None,
        fertilizers: IFertilizerRepository | None = None,
    ) -> None:
        self._repo = repo
        # The atomic completion transition (REQ-053 WP 4.3, ADR-008 phase 3 for tasks). All three are supplied by
        # the DI factory; a service built without them (unit tests, the Celery beat) keeps the plain
        # single-document completion and writes no care-log line.
        self._completion = completion
        self._care_events = care_events
        self._harvests = harvests
        self._completion_engine = TaskCompletionEngine(fertilizers)
        # ``(user_key, tenant_key) -> membership | None`` — decides who a task may
        # be assigned to (#1871 B9). Without it an assignment is refused.
        self._membership_lookup = membership_lookup
        # Resolves the `photo_refs` a completion carries (#1339 review). Optional
        # only so the many existing constructions of this service keep working;
        # the DI factory always supplies it, and `_verify_photo_refs` fails
        # closed rather than waving a reference through when it is absent.
        self._attachment_repo = attachment_repo
        self._hst = hst_validator
        self._deps = dependency_resolver
        self._recurrence = recurrence or RecurrenceEngine()
        #: Optional REQ-030 §4.2 coupling: when wired, task mutations synchronously
        #: propagate into the in-app notification centre (Issue #742). Left ``None``
        #: in unit tests that don't exercise the feedback loop — every call site is
        #: guarded so the core task flow is unaffected when it is absent.
        self._notifications = notification_propagation

    # ── Workflow Templates ──

    def list_workflow_templates(
        self,
        offset: int = 0,
        limit: int = 50,
        species_key: str | None = None,
        tenant_key: str = "",
        target_entity_type: str | None = None,
    ) -> tuple[list[WorkflowTemplate], int]:
        return self._repo.get_all_workflow_templates(
            offset,
            limit,
            species_key=species_key,
            tenant_key=tenant_key,
            target_entity_type=target_entity_type,
        )

    def list_workflow_templates_window(
        self,
        offset: int = 0,
        limit: int = 50,
        species_key: str | None = None,
        target_entity_type: str | None = None,
        *,
        tenant_key: str,
    ) -> list[WorkflowTemplate]:
        """One page of :meth:`list_workflow_templates` without the count query (MT-035, #2131)."""
        return self._repo.list_workflow_templates_window(
            offset,
            limit,
            species_key=species_key,
            target_entity_type=target_entity_type,
            tenant_key=tenant_key,
        )

    def get_workflow_usage_stats(self, wf_keys: list[str], *, tenant_key: str) -> dict[str, dict]:
        """Return species_name and ``tenant_key``'s assigned entity count per workflow key (#1708)."""
        return self._repo.get_workflow_usage_stats(wf_keys, tenant_key=tenant_key)

    def get_workflow_template(self, key: str, tenant_key: str = "") -> WorkflowTemplate:
        wt = self._repo.get_workflow_template_or_raise(key)
        if tenant_key:
            # Read access spans the hybrid catalog: the caller's own templates
            # PLUS globally seeded system templates (empty tenant_key), so the
            # detail/instantiate/duplicate routes work for the system templates
            # the list restores. Write ownership is guarded separately below.
            verify_tenant_read_access(wt, tenant_key, "WorkflowTemplate")
        return wt

    def create_workflow_template(self, template: WorkflowTemplate) -> WorkflowTemplate:
        return self._repo.create_workflow_template(template)

    def update_workflow_template(self, key: str, data: dict, *, tenant_key: str) -> WorkflowTemplate:
        """Apply an allow-listed partial edit to a workflow template (#965).

        ``data`` is filtered through :data:`WORKFLOW_TEMPLATE_UPDATABLE_FIELDS`
        before anything is assigned, so the body can no longer reach
        ``tenant_key`` (handing the template to another tenant, or emptying it
        into the global catalog) or ``is_system`` (clearing the very flag the
        guard below reads).
        """
        wt = self.get_workflow_template(key, tenant_key=tenant_key)
        if wt.is_system:
            # Read access is hybrid-catalog-wide, so the router guard now admits
            # system templates; writes must stay blocked (mirrors delete below).
            raise ValidationError("Cannot modify system workflow templates.")
        if not wt.tenant_key:
            # A shared (generated) plan: every tenant reads this one row, so the
            # edit lands on the caller's own copy, as the activity-plan editor's
            # does (#1003, #2101). The shared row is never written.
            # A generated plan already forked by this tenant is reused (the same lookup the
            # read path and the activity-plan editor use), so a client that still holds the
            # shared key does not mint a new copy per save.
            existing_fork = (
                self._repo.get_auto_generated_workflow_for_species(wt.species_key, tenant_key=tenant_key)
                if wt.auto_generated and wt.species_key
                else None
            )
            if existing_fork is not None and existing_fork.tenant_key == tenant_key:
                wt = existing_fork
            else:
                wt, _ = self._copy_workflow_template(
                    wt, name=wt.name, tenant_key=tenant_key, auto_generated=wt.auto_generated
                )
            key = wt.key or key
        for field, value in _allowed(data, WORKFLOW_TEMPLATE_UPDATABLE_FIELDS).items():
            setattr(wt, field, value)
        return self._repo.update_workflow_template(key, wt)

    def delete_workflow_template(self, key: str, *, tenant_key: str) -> bool:
        wt = self.get_workflow_template(key, tenant_key=tenant_key)
        if wt.is_system:
            raise ValidationError("Cannot delete system workflow templates.")
        if not wt.tenant_key:
            raise ForbiddenError(SHARED_WORKFLOW_REFUSAL)
        return self._repo.delete_workflow_template(key)

    def duplicate_workflow_template(self, key: str, new_name: str, *, tenant_key: str) -> WorkflowTemplate:
        """Duplicate a workflow template including all its task templates.

        The clone is owned by ``tenant_key`` (the duplicating tenant), never by
        the source's tenant. A tenant may duplicate a global system template,
        but the copy must be a private, tenant-scoped template — leaving it with
        the source's empty tenant_key would make it globally visible to every
        tenant now that the catalog list unions global rows.

        The copy itself is :meth:`_copy_workflow_template`'s, shared with the
        copy-on-write fork of #1003. This method's own contribution is the two
        decisions that differ there: the user-chosen name, and ``auto_generated``
        cleared — an explicit duplicate is an authored workflow from that point
        on, and must not answer the generated-plan lookup.

        ``tenant_key`` is keyword-only without a default (#2107): with the old
        ``""`` default the read admission below was skipped and the copy was
        stamped with no owner — a globally visible template.
        """
        source = self.get_workflow_template(key, tenant_key=tenant_key)
        clone, _ = self._copy_workflow_template(
            source,
            name=new_name,
            tenant_key=tenant_key,
            auto_generated=False,
        )
        return clone

    def _copy_workflow_template(
        self,
        source: WorkflowTemplate,
        *,
        name: str,
        tenant_key: str,
        auto_generated: bool,
    ) -> tuple[WorkflowTemplate, dict[str, str]]:
        """Copy a workflow with its phases and task templates, for ``tenant_key``.

        The one copier in the service, used by both flows that produce a copy of
        a shared workflow: the explicit "duplicate first" the system-workflow
        refusal points at (#984), and the automatic copy-on-write fork a tenant's
        first edit of a generated activity plan produces (#1003). They differ
        only in the two arguments above, which is why this is one function rather
        than two that drift.

        Returns the created workflow **and the source-to-copy key map of its task
        templates**. The map is what the copy-on-write caller needs and the
        duplicate caller ignores: a client that still holds the shared plan's
        keys keeps addressing the originals after the fork, and the map is how
        such a key is redirected onto the row in the copy that it stands for. It
        is also persisted per row as ``TaskTemplate.source_template_key``, so the
        redirect survives beyond this call.

        ``is_system`` is deliberately not carried over: a copy of system data is
        the caller's own editable workflow, which is the entire point of
        offering the copy.
        """
        clone = WorkflowTemplate(
            name=name,
            tenant_key=tenant_key,
            description=source.description,
            species_compatible=list(source.species_compatible),
            species_key=source.species_key,
            lifecycle_key=source.lifecycle_key,
            growth_system=source.growth_system,
            difficulty_level=source.difficulty_level,
            category=source.category,
            tags=list(source.tags),
            auto_generated=auto_generated,
            total_duration_days=source.total_duration_days,
            skill_level_filter=source.skill_level_filter,
            target_entity_types=list(source.target_entity_types),
            source_workflow_key=source.key,
        )
        created_wf = self._repo.create_workflow_template(clone)

        # Clone phases and build key mapping
        source_phases = self._repo.get_phases_for_workflow(source.key or "")
        phase_key_map: dict[str, str] = {}
        for sp in source_phases:
            old_key = sp.key
            sp.key = None
            sp.workflow_template_key = created_wf.key or ""
            sp.created_at = None
            sp.updated_at = None
            new_phase = self._repo.create_phase(sp)
            phase_key_map[old_key or ""] = new_phase.key or ""

        template_key_map: dict[str, str] = {}
        templates = self._repo.get_task_templates_for_workflow(source.key or "")
        for tt in templates:
            source_key = tt.key
            tt.key = None
            tt.source_template_key = source_key
            tt.workflow_template_key = created_wf.key or ""
            if tt.workflow_phase_key and tt.workflow_phase_key in phase_key_map:
                tt.workflow_phase_key = phase_key_map[tt.workflow_phase_key]
            tt.created_at = None
            tt.updated_at = None
            created_tt = self._repo.create_task_template(tt)
            if source_key:
                template_key_map[source_key] = created_tt.key or ""

        return created_wf, template_key_map

    # ── Workflow Phases ──

    def get_workflow_phases(self, wf_key: str) -> list[WorkflowPhase]:
        self.get_workflow_template(wf_key)
        return self._repo.get_phases_for_workflow(wf_key)

    def get_workflow_phase(self, key: str) -> WorkflowPhase:
        return self._repo.get_phase_or_raise(key)

    def _require_writable_parent_workflow(self, workflow_template_key: str, tenant_key: str) -> WorkflowTemplate:
        """Resolve a phase's parent workflow for a write by ``tenant_key`` (#2107).

        A phase carries no tenant of its own; its parent ``WorkflowTemplate`` is the
        only anchor. The parent is resolved through :meth:`get_workflow_template`
        under the caller's tenant — a foreign or unknown parent, and a phase with no
        parent at all, answer ``NotFoundError`` (404, no cross-tenant oracle) — and a
        system or shared parent then refuses the write (:func:`_refuse_system_workflow`).

        Until #2107 the tenant half of this lived in the router: ``get_workflow_phase``
        and ``get_workflow_template(..., tenant_key=...)`` ran there, and the service
        method that wrote resolved the parent again without a tenant.
        """
        if not workflow_template_key:
            raise NotFoundError("WorkflowTemplate", workflow_template_key)
        workflow = self.get_workflow_template(workflow_template_key, tenant_key=tenant_key)
        _refuse_system_workflow(workflow)
        return workflow

    def create_workflow_phase(self, phase: WorkflowPhase, *, tenant_key: str) -> WorkflowPhase:
        """Add ``phase`` to its workflow, which ``tenant_key`` must own (#2107)."""
        self._require_writable_parent_workflow(phase.workflow_template_key, tenant_key)
        return self._repo.create_phase(phase)

    def update_workflow_phase(self, key: str, data: dict, *, tenant_key: str) -> WorkflowPhase:
        """Apply an allow-listed partial edit to a workflow phase (#965).

        Same shape as :meth:`update_task_template`: the phase carries no tenant
        of its own and is anchored on ``workflow_template_key``, which the
        allow-list keeps out of reach — re-pointing it is how a phase would move
        into another tenant's workflow. The parent is verified against
        ``tenant_key`` here, not in the calling route (#2107).
        """
        phase = self.get_workflow_phase(key)
        self._require_writable_parent_workflow(phase.workflow_template_key, tenant_key)
        for field, value in _allowed(data, WORKFLOW_PHASE_UPDATABLE_FIELDS).items():
            setattr(phase, field, value)
        return self._repo.update_phase(key, phase)

    def delete_workflow_phase(self, key: str, *, tenant_key: str) -> bool:
        """Delete a phase of a workflow ``tenant_key`` owns (#2107)."""
        phase = self.get_workflow_phase(key)
        self._require_writable_parent_workflow(phase.workflow_template_key, tenant_key)
        return self._repo.delete_phase(key)

    def _refuse_writing_into_a_system_workflow(self, workflow_template_key: str | None) -> None:
        """Refuse an edit whose *parent* workflow is a system template (#965 item 3).

        Used wherever a child is edited or removed **in place** — the phase
        routes and the two task-template routes — which reach their parent
        through the child's own ``workflow_template_key``.

        Resolution is deliberately **tenant-blind**: only ``is_system`` is
        consulted, never the caller's tenant. That keeps this a pure system-data
        guard and leaves #965 item 1 (a *foreign tenant's* child, reachable
        because ``get_task_template`` is unanchored) exactly where it was.
        Anchoring on the parent's tenant is the larger change that needs the
        orphan-ownership field and its backfill; doing it here by accident would
        settle that question in the wrong place.

        A child with no parent key is left alone: there is nothing to anchor on,
        and refusing it here would be an orphan decision bolted onto the delete
        path — orphans do have an owner now (global, decided on #965), but that
        belongs to items 1/2/4 with their own field, not to this guard.
        """
        if not workflow_template_key:
            return
        _refuse_system_workflow(self.get_workflow_template(workflow_template_key))

    def reorder_workflow_phases(self, phase_orders: list[dict], *, tenant_key: str) -> list[WorkflowPhase]:
        """Reorder a workflow's phases, verifying each against ``tenant_key`` (#965 item 1).

        ``reorder_phases`` wrote ``phase_order`` by ``_key`` with no scoping at
        all, so a caller could re-sequence another tenant's workflow — the one
        write path in the phase group the #964 sweep left open. Every phase key
        is now resolved to its parent ``WorkflowTemplate`` (the only tenant anchor
        a phase has) and verified through :meth:`get_workflow_template`, which
        answers ``NotFoundError`` for a foreign or unknown parent — the same
        tenant check the per-key phase routes already perform, and never a
        cross-tenant oracle. A system workflow's phases are refused too, matching
        the sibling edit/delete routes: re-sequencing seeded phases would move
        them for every tenant.

        ``tenant_key`` is keyword-only (#948): a route that forgets to thread it
        fails loudly rather than compiling away the isolation.
        """
        for item in phase_orders:
            phase = self.get_workflow_phase(item["key"])
            self.get_workflow_template(phase.workflow_template_key, tenant_key=tenant_key)
            self._refuse_writing_into_a_system_workflow(phase.workflow_template_key)
        return self._repo.reorder_phases(phase_orders)

    def get_phase_suggestions(self, *, tenant_key: str) -> list[dict]:
        return self._repo.get_phase_suggestions(tenant_key=tenant_key)

    # ── Task Templates ──

    def get_task_templates(self, wf_key: str) -> list[TaskTemplate]:
        return self._repo.get_task_templates_for_workflow(wf_key)

    def get_task_template(self, key: str) -> TaskTemplate:
        return self._repo.get_task_template_or_raise(key)

    def get_task_template_for_read(self, key: str, *, tenant_key: str) -> TaskTemplate:
        """Load a task template the caller is allowed to read (SEC-001, #965).

        The write paths (:meth:`update_task_template`/:meth:`delete_task_template`)
        grew an entity-level tenant check when ``TaskTemplate`` gained its own
        ``tenant_key``, but the single-template ``GET`` was left on the unanchored
        :meth:`get_task_template` primitive — a member of *any* tenant could fetch
        another tenant's private template by key, and the keys are ArangoDB
        auto-generated and enumerable. This mirrors the write guard exactly: the
        entity's own ``tenant_key`` is verified against the caller through
        :func:`verify_tenant_read_access`, so a foreign template answers
        ``NotFoundError`` (404, never a cross-tenant oracle) while the global
        catalogue (``tenant_key == ""``) stays readable so #324 is not re-broken.

        The bare :meth:`get_task_template` stays as the internal primitive the
        three write/enrichment methods compose with their own parent-based checks;
        this is the anchored read for the HTTP ``GET``. ``tenant_key`` is
        keyword-only (#948) so a route that forgets to thread it fails loudly.
        """
        tt = self.get_task_template(key)
        verify_tenant_read_access(tt, tenant_key, "TaskTemplate")
        return tt

    @staticmethod
    def _refuse_a_shared_task_template(template: TaskTemplate) -> None:
        """A task template with no owner (``tenant_key == ""``) is shared, not editable (#2101).

        ``verify_tenant_read_access`` admits it on purpose — the read side of the
        hybrid catalogue — and until now the write side followed it, which is what
        let any tenant rewrite the standalone templates migration ``v0035`` could
        not attribute. Newly created templates are stamped with their owner.
        """
        if not template.tenant_key:
            raise ForbiddenError(SHARED_WORKFLOW_REFUSAL)

    def _verify_workflow_template_reference(self, workflow_template_key: str | None, tenant_key: str) -> None:
        """Resolve a caller-supplied ``workflow_template_key`` before it is written (#965).

        ``TaskTemplate`` carries no ``tenant_key``; its parent ``WorkflowTemplate``
        does, and is therefore the anchor. The key went unchecked on both write
        paths: the repository builds a ``wf_contains`` edge from it on create,
        and ``get_task_templates_for_workflow`` filters on the *field*, so a
        foreign key attaches the caller's template to another tenant's workflow —
        an edge written across the isolation boundary, and a task that tenant's
        next instantiation will generate.

        Resolution goes through :meth:`get_workflow_template`, so an unknown key
        and a foreign tenant's key produce the identical ``NotFoundError`` (404,
        never 403 — no cross-tenant oracle). A template with **no** parent at all
        is a supported standalone state and is left alone.

        A globally seeded **system** workflow resolves — read access spans the
        hybrid catalog on purpose — but then refuses the write (#965 item 3).
        Until that was added, the "cannot modify system workflow templates" rule
        the two sibling guards enforce on the parent stopped at the parent: a
        tenant could hang a task template off "Tomato Standard", and because
        ``get_task_templates_for_workflow`` filters on the denormalised parent
        field, it surfaced for *every* tenant. The refusal is that same
        ``ValidationError`` (422), never the 404 — the caller may read this
        workflow, they may only not write into it.
        """
        if not workflow_template_key:
            return
        _refuse_system_workflow(self.get_workflow_template(workflow_template_key, tenant_key=tenant_key))

    def _verify_workflow_phase_reference(self, workflow_phase_key: str | None, tenant_key: str) -> None:
        """Resolve a caller-supplied ``workflow_phase_key`` before it is written (SEC-003).

        A task template may name the phase it belongs to. ``workflow_phase_key`` is
        in :data:`TASK_TEMPLATE_UPDATABLE_FIELDS` and settable on create, but was
        never checked — only ``workflow_template_key`` was — so a caller could store
        a reference to a **foreign** tenant's phase on their own template. It is not
        a cross-tenant write (the template stays the caller's) and leaks nothing on
        the paths traced today, but it stores an unvalidated cross-boundary
        reference a future join could dereference, exactly the class the update
        allow-list excludes ``phase_definition_key``/``activity_key`` to avoid.

        The phase's only tenant anchor is its parent ``WorkflowTemplate``, so the
        check hangs there through :meth:`get_workflow_template` — a foreign or
        unknown phase/parent answers ``NotFoundError`` (404, no cross-tenant
        oracle); a phase with no parent, or none supplied, is left alone.
        """
        if not workflow_phase_key:
            return
        phase = self.get_workflow_phase(workflow_phase_key)
        if not phase.workflow_template_key:
            return
        self.get_workflow_template(phase.workflow_template_key, tenant_key=tenant_key)

    def create_task_template(self, template: TaskTemplate, *, tenant_key: str) -> TaskTemplate:
        """Create a task template for ``tenant_key``, verifying its parent workflow (#965).

        ``tenant_key`` is required and keyword-only, following #948: a route that
        forgets to thread it does not compile away silently, it fails loudly.

        The caller's tenant is **stamped onto the entity** (#965 item 1). Since
        ``TaskTemplate`` grew its own ``tenant_key`` field, a template created here
        records its owner rather than being un-owned — a standalone template (no
        parent workflow) is now the caller's, not a globally editable orphan. The
        value comes from the auth/path context, never the request body, mirroring
        how ``Task`` and ``WorkflowTemplate`` are stamped at their construction
        sites. ``update``/``delete`` verify this field back against the caller.
        """
        self._verify_workflow_template_reference(template.workflow_template_key, tenant_key)
        self._verify_workflow_phase_reference(template.workflow_phase_key, tenant_key)
        template.tenant_key = tenant_key
        return self._repo.create_task_template(template)

    def update_task_template(self, key: str, data: dict, *, tenant_key: str) -> TaskTemplate:
        """Apply an allow-listed partial edit to a task template (#965).

        Two defects met here. ``data`` was assigned field by field with no
        allow-list, so the request body chose what got written; and
        ``workflow_template_key`` is among the fields an edit may legitimately
        move, so the update path could re-point a template into another tenant's
        workflow just as create could. The allow-list bounds *which* fields are
        written, the reference check bounds *which values* the parent field may
        take.

        Three answers, layered so the earlier one wins (#965 items 1 and 3):

        * **Foreign → 404.** The entity's own ``tenant_key`` (added for item 1) is
          verified against the caller through :func:`verify_tenant_read_access`,
          which raises ``NotFoundError`` for a template owned by another tenant —
          no cross-tenant oracle. It admits the global catalogue (``tenant_key ==
          ""``) so #324 is not re-broken. This runs *first*, so a foreign template
          is refused before it is ever classified by system-ness.
        * **System → 422.** The template's **current** parent decides whether the
          edit may happen at all: a seeded template of "Tomato Standard" is system
          data, so renaming or re-timing it is the same refusal as attaching a new
          one, only arriving by a different verb.
        * **Own → proceed.** The **target** parent is then checked as before, so a
          move can neither leave a system workflow's contents editable nor land in
          one.
        """
        tt = self.get_task_template(key)
        verify_tenant_read_access(tt, tenant_key, "TaskTemplate")
        self._refuse_writing_into_a_system_workflow(tt.workflow_template_key)
        self._refuse_a_shared_task_template(tt)
        fields = _allowed(data, TASK_TEMPLATE_UPDATABLE_FIELDS)
        if "workflow_template_key" in fields:
            self._verify_workflow_template_reference(fields["workflow_template_key"], tenant_key)
        if "workflow_phase_key" in fields:
            self._verify_workflow_phase_reference(fields["workflow_phase_key"], tenant_key)
        for field, value in fields.items():
            setattr(tt, field, value)
        return self._repo.update_task_template(key, tt)

    def delete_task_template(self, key: str, *, tenant_key: str) -> bool:
        """Remove a task template the caller owns, unless it is system data (#965 items 1, 3).

        The same three layered answers as :meth:`update_task_template`, and in the
        same order — foreign → 404, system → 422, own → proceed:

        * **Foreign → 404.** The entity's own ``tenant_key`` is verified against
          the caller (:func:`verify_tenant_read_access`); another tenant's template
          answers ``NotFoundError``, never a cross-tenant oracle. The global
          catalogue (``tenant_key == ""``) is admitted so #324 stands.
        * **System → 422.** Deleting a seeded template of a system workflow removes
          it for every tenant, the same modification the two parent-level guards
          already refuse.

        ``tenant_key`` is required and keyword-only (#948): the anchor item 1 was
        missing, so a route that forgets to thread it fails loudly rather than
        deleting across the isolation boundary.
        """
        tt = self.get_task_template(key)
        verify_tenant_read_access(tt, tenant_key, "TaskTemplate")
        self._refuse_writing_into_a_system_workflow(tt.workflow_template_key)
        self._refuse_a_shared_task_template(tt)
        return self._repo.delete_task_template(key)

    # ── Task Templates of an activity plan (tenant-anchored, #992) ──

    def _resolve_task_template_for_tenant_write(self, key: str, tenant_key: str) -> TaskTemplate:
        """Load a task template only if ``tenant_key`` may write it (#992).

        ``TaskTemplate`` carries no ``tenant_key`` of its own — ownership is not
        stored on the entity, exactly like ``Location``/``Slot``, which are
        verified through their parent site. The only anchor is the parent
        ``WorkflowTemplate`` behind ``workflow_template_key``, so the predicate
        hangs there. Hanging it on the template itself would match nothing and
        refuse every caller while looking like a working guard.

        Three answers, and the difference between them is deliberate:

        * **Foreign or unknown parent → 404.** Resolution goes through
          :meth:`get_workflow_template`, whose ``verify_tenant_read_access``
          answers ``NotFoundError`` for both, so this route cannot be used as a
          cross-tenant existence oracle.
        * **System workflow → 422.** A globally seeded workflow is visible to
          every tenant on purpose (#324: the strict direction must not hide the
          global catalogue), so it resolves — and then refuses the *write*, with
          the shared :data:`SYSTEM_WORKFLOW_CHILD_REFUSAL`. Deleting one of its
          task templates would remove it for every tenant.
        * **No parent at all → 404.** An activity plan's task templates always
          have one: ``ActivityPlanService.generate_plan`` assigns
          ``tt.workflow_template_key = wt.key`` to every template before it is
          persisted, and the seeder skips any template whose workflow it cannot
          resolve. A parentless template is therefore an unreachable state here,
          and it has no owner — so it is refused rather than left writable by
          anyone, which is what "no anchor, so no refusal" would mean on a route
          that has no tenant scoping of its own. The answer is the 404 rather
          than a 422 because "who owns this" has no answer: telling the caller
          the key exists but is unowned is the oracle the 404 avoids. The state
          is logged so it fails loudly where loudness helps — in the operator's
          log, not in an attacker's response body.

        * **A shared generated plan → the caller's private copy of it (#1003).**
          What ``ActivityPlanService`` persists is global (``tenant_key == ""``,
          ``is_system == False``), so #992 let every tenant write it — and every
          tenant write the *same* one. The write is not refused, because a
          generated plan is the user's working surface and they have no reason
          to expect it to be shared; it is redirected. See
          :meth:`_private_copy_for_a_shared_plan`.

        The caller's *own* templates pass through untouched.
        """
        template = self.get_task_template(key)
        parent_key = template.workflow_template_key
        if not parent_key:
            logger.warning(
                "task_template_without_parent_workflow",
                task_template_key=key,
                tenant=log_tenant(tenant_key),
            )
            raise NotFoundError("TaskTemplate", key)
        parent = self.get_workflow_template(parent_key, tenant_key=tenant_key)
        if parent.is_system:
            raise ValidationError(SYSTEM_WORKFLOW_CHILD_REFUSAL)
        if tenant_key and not parent.tenant_key:
            return self._private_copy_for_a_shared_plan(parent, template, tenant_key)
        return template

    def _private_copy_for_a_shared_plan(
        self,
        shared_plan: WorkflowTemplate,
        template: TaskTemplate,
        tenant_key: str,
    ) -> TaskTemplate:
        """Redirect a write on a shared generated plan onto the caller's own copy (#1003).

        The plan ``ActivityPlanService`` generates is one global object that
        every tenant growing that species reads. #992 anchored the *route* on the
        parent workflow but left that object writable by all of them, so tenant
        A switching an activity off switched it off for tenant B, silently. The
        answer taken is **copy-on-write**: the generated plan stays a shared
        template, and a tenant's first write materialises a private copy which
        that tenant works on from then on.

        Three properties this has to hold, in order of how easily they break:

        1. **Idempotence.** The copy is materialised once. Every later write
           resolves the existing copy through the same lookup the *read* path
           uses (:meth:`ITaskRepository.get_auto_generated_workflow_for_species`),
           so the plan the caller edits and the plan the caller is shown can
           never be two different objects.
        2. **Stale keys keep working.** After the fork a client still holds the
           shared plan's task-template keys, and the SPA sends them on the next
           toggle. Such a key is mapped onto the copy through
           ``source_template_key`` rather than refused, so an open tab does not
           start writing the shared object again — which would be the original
           defect, reintroduced through the back door.
        3. **The source is never written.** Nothing here touches
           ``shared_plan``; the copy is built from it and only the copy is
           returned.

        A shared workflow that is *not* a generated plan cannot be forked — the
        copy would be unreachable, because the lookup that finds it keys on
        ``auto_generated`` and ``species_key``. That state is unreachable in
        practice (``auto_generated`` is set only by ``ActivityPlanEngine``, and
        ``generate_plan`` always stamps the species), so it is refused loudly
        with the same 404 an unowned template gets rather than written through,
        which would leave the shared object mutable exactly as before.
        """
        if not (shared_plan.auto_generated and shared_plan.species_key):
            logger.warning(
                "shared_workflow_is_not_a_generated_plan",
                workflow_template_key=shared_plan.key,
                task_template_key=template.key,
                tenant=log_tenant(tenant_key),
            )
            raise NotFoundError("TaskTemplate", template.key or "")

        copy = self._repo.get_auto_generated_workflow_for_species(
            shared_plan.species_key,
            tenant_key=tenant_key,
        )
        if copy is None or copy.tenant_key != tenant_key:
            copy, template_key_map = self._copy_workflow_template(
                shared_plan,
                name=shared_plan.name,
                tenant_key=tenant_key,
                auto_generated=True,
            )
            logger.info(
                "activity_plan_forked_on_write",
                source_workflow_key=shared_plan.key,
                workflow_template_key=copy.key,
                tenant=log_tenant(tenant_key),
            )
            copied_key = template_key_map.get(template.key or "")
            if copied_key:
                return self._repo.get_task_template_or_raise(copied_key)
            raise NotFoundError("TaskTemplate", template.key or "")

        for candidate in self._repo.get_task_templates_for_workflow(copy.key or ""):
            if candidate.source_template_key == template.key:
                return candidate

        # The caller's copy exists but no longer carries this activity — they
        # deleted it from their own plan while a client still showed it. The key
        # is genuinely gone *for this tenant*, so it answers like any other key
        # they may not reach, and the shared template stays untouched.
        logger.info(
            "activity_plan_template_absent_from_private_copy",
            source_template_key=template.key,
            workflow_template_key=copy.key,
            tenant=log_tenant(tenant_key),
        )
        raise NotFoundError("TaskTemplate", template.key or "")

    def update_activity_plan_task_template(self, key: str, data: dict, *, tenant_key: str) -> TaskTemplate:
        """Apply the activity-plan editor's partial edit, anchored on the parent workflow (#992).

        ``tenant_key`` is required and keyword-only, following #948: a route that
        forgets to thread it fails loudly instead of silently authorising
        everyone — which is precisely how the previous version of this edit, made
        in the API layer straight against the repository, let any authenticated
        user retime any tenant's task template.

        The write lands on the template the resolution **returned**, not on the
        key the caller sent (#1003). The two differ whenever the caller addressed
        a shared generated plan: the resolution then hands back the equivalent
        row in that tenant's private copy, and writing ``key`` here would put the
        edit straight back onto the shared object the copy exists to protect.
        """
        template = self._resolve_task_template_for_tenant_write(key, tenant_key)
        for field, value in _allowed(data, ACTIVITY_PLAN_TASK_TEMPLATE_UPDATABLE_FIELDS).items():
            setattr(template, field, value)
        return self._repo.update_task_template(template.key or key, template)

    def delete_activity_plan_task_template(self, key: str, *, tenant_key: str) -> bool:
        """Remove a task template of an activity plan, anchored on the parent workflow (#992).

        A delete on a shared generated plan is a write like any other and forks
        the same way (#1003): the caller's private copy is materialised and the
        activity is removed **from the copy**, leaving the shared template whole
        for every other tenant. Refusing instead was the alternative considered —
        it would have been the only editor action a tenant could not perform on
        their own plan, and "remove this activity" is what an activity plan is
        for.
        """
        template = self._resolve_task_template_for_tenant_write(key, tenant_key)
        return self._repo.delete_task_template(template.key or key)

    # ── Workflow Instantiation ──

    def instantiate_workflow(
        self,
        template_key: str,
        entity_key: str,
        entity_type: str,
        *,
        tenant_key: str,
    ) -> WorkflowExecution:
        """Generate tasks from a workflow template for a specific entity.

        Tasks whose trigger_phase does not match the current phase are created
        with status 'dormant' for plant_instance entities and 'pending' for
        all other entity types (which have no phase concept).

        ``tenant_key`` is required and keyword-only (#1708): every generated task
        is stamped with it. Before, the tasks kept the model default ``""`` — and
        since every task list filters strictly on the caller's tenant, a workflow
        instantiated through the route produced tasks that appeared in *no*
        tenant's list and counted for no tenant's usage statistics. An empty value
        is refused rather than stamped, because it is that same silence spelled
        differently. The template read is anchored on the same tenant, so a
        foreign private template is a 404 here as it is at the route.

        ``entity_type`` must be a :class:`WorkflowTargetType`: an execution on any
        other type has no owner the execution list could resolve, so it would
        exist and appear nowhere. Whether ``entity_key`` belongs to the tenant is
        the caller's check (:class:`TaskEntityGuard`, as on ``POST /tasks``).

        The :class:`WorkflowExecution` record itself carries no tenant; it belongs
        to the entity it runs on, and every read resolves the owner there.
        """
        if not tenant_key:
            raise ValueError("instantiate_workflow requires a tenant_key")
        try:
            target_type = WorkflowTargetType(entity_type)
        except ValueError as exc:
            raise ValidationError(f"Unsupported workflow entity type '{entity_type}'.") from exc
        entity_type = target_type.value
        wt = self.get_workflow_template(template_key, tenant_key=tenant_key)
        templates = self._repo.get_task_templates_for_workflow(template_key)

        if not templates:
            raise ValidationError(f"Workflow '{wt.name}' has no task templates.")

        execution = WorkflowExecution(
            workflow_template_key=template_key,
            entity_key=entity_key,
            entity_type=entity_type,
        )
        execution = self._repo.create_workflow_execution(execution)

        now = datetime.now(UTC)
        for tt in templates:
            checklist = [ChecklistItem(text=item.text, done=False, order=item.order) for item in tt.default_checklist]

            status = "pending"
            # recurrence-owner-ok: a workflow-template offset — it says when the FIRST task
            # of this run falls due relative to instantiation, not when the next one does.
            # Template offsets are named outside boundary 1 by the phase-0 counting
            # definition; task recurrence runs through RecurrenceEngine in
            # _create_next_recurring_task.
            due_date = now + timedelta(days=tt.days_offset) if tt.days_offset else None
            # Only plant_instance entities support phase-based dormant tasks
            if (
                entity_type == "plant_instance"
                and tt.trigger_phase
                and tt.trigger_type in ("phase_entry", "days_after_phase")
            ):
                status = "dormant"
                due_date = None

            task = Task(
                name=tt.name,
                name_de=tt.name_de,
                instruction=tt.instruction,
                instruction_de=tt.instruction_de,
                category=tt.category,
                entity_key=entity_key,
                entity_type=entity_type,
                due_date=due_date,
                status=status,
                priority="medium",
                skill_level=tt.skill_level,
                stress_level=tt.stress_level,
                estimated_duration_minutes=tt.estimated_duration_minutes,
                requires_photo=tt.requires_photo,
                timer_duration_seconds=tt.timer_duration_seconds,
                timer_label=tt.timer_label,
                checklist=checklist,
                trigger_phase=tt.trigger_phase,
                template_key=tt.key,
                workflow_execution_key=execution.key,
                activity_key=tt.activity_key,
                tenant_key=tenant_key,
            )
            created_task = self._repo.create_task(task)

            if tt.activity_key and created_task.key:
                self._repo.create_task_activity_edge(
                    created_task.key,
                    tt.activity_key,
                )

        return execution

    # ── Notification propagation (REQ-030 §4.2, #742) ──

    def _propagate(self, action) -> None:  # noqa: ANN001 — Callable[[NotificationPropagationService], None]
        """Run a notification-propagation ``action`` when the coupling is wired.

        Swallows and logs any propagation error so a notification-centre hiccup can
        never abort the underlying task mutation (NFR-007 graceful degradation).
        """
        if self._notifications is None:
            return
        try:
            action(self._notifications)
        except Exception:  # pragma: no cover - defensive; propagation is best-effort
            import structlog

            structlog.get_logger().warning("task_notification_propagation_failed")

    # ── Task CRUD ──

    def list_tasks(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        *,
        tenant_key: str,
        origins: Sequence[str] | None = None,
    ) -> tuple[list[Task], int]:
        """The tenant's tasks, paged and narrowed.

        ``tenant_key`` is keyword-only and required, mirroring the repository
        signature it delegates to (#1533). It carried ``= ""`` — the sentinel the
        repository reads as "no tenant predicate" — so the listing could be widened
        to the whole installation by leaving one argument out.

        ``origins`` is separate from ``filters`` for the reason spelled out on
        :meth:`ITaskRepository.get_all_tasks`: the provenance filter is a
        partition over several values, not one equality (#1503).
        """
        self._require_tenant_key(tenant_key, "list_tasks")
        return self._repo.get_all_tasks(offset, limit, filters, tenant_key=tenant_key, origins=origins)

    def list_tasks_window(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict[str, Any] | None = None,
        *,
        tenant_key: str,
        origins: Sequence[str] | None = None,
    ) -> list[Task]:
        """One page of the tenant's tasks without the count query (MT-035, #2131).

        The list route answers a bare array; the ``total`` :meth:`list_tasks` pays a
        second scan of every matching task for was never read there.
        """
        self._require_tenant_key(tenant_key, "list_tasks_window")
        return self._repo.get_tasks_window(offset, limit, filters, tenant_key=tenant_key, origins=origins)

    @staticmethod
    def _require_tenant_key(tenant_key: str, method: str) -> None:
        """Reject the empty-``tenant_key`` sentinel before a tenant-scoped load.

        Mirrors ``BaseRepository._require_tenant_key`` at the service layer so a
        caller that forgets the argument fails **closed** (GHSA-h5wp-r68x-97g8).
        The ownership check used to be conditional on a truthy ``tenant_key`` with
        a ``""`` default, so an omitted argument silently skipped it and read
        across every tenant. Raising here removes that fragile invariant.
        """
        if not tenant_key:
            raise ValueError(
                f"{method} is tenant-scoped and requires a non-empty tenant_key (GHSA-h5wp-r68x-97g8 tenant isolation)."
            )

    def get_task(self, key: str, *, tenant_key: str) -> Task:
        self._require_tenant_key(tenant_key, "get_task")
        task = self._repo.get_task_or_raise(key)
        verify_tenant_ownership(task, tenant_key, "Task")
        return task

    def _require_member_assignee(self, user_key: str | None, tenant_key: str) -> None:
        """Refuse an assignee who is not an active member of the task's tenant (#1871 B9).

        ``assigned_to_user_key`` came from request bodies and was stored as given,
        and the assignment notified that user — any user of the installation. An
        unknown user, a non-member and an inactive member answer the same 404.
        Clearing an assignee (``None``) needs no check.
        """
        if not user_key:
            return
        membership = self._membership_lookup(user_key, tenant_key) if self._membership_lookup and tenant_key else None
        if membership is None or not getattr(membership, "is_active", False):
            raise NotFoundError("User", user_key)

    def _still_a_member(self, user_key: str | None, tenant_key: str) -> str | None:
        """*user_key* when it is an active member of *tenant_key*, else ``None`` — no error.

        A task without a tenant (system context) keeps its assignee: there is no
        membership to consult.
        """
        if not tenant_key:
            return user_key
        try:
            self._require_member_assignee(user_key, tenant_key)
        except NotFoundError:
            return None
        return user_key

    def create_task(self, task: Task, *, actor_user_key: str = "") -> Task:
        self._recurrence.require_rrule(task.recurrence_rule)  # 422 recurrence.rrule_required (GP-ACC-038)
        self._require_member_assignee(task.assigned_to_user_key, task.tenant_key)
        created = self._repo.create_task(task)
        self._propagate(lambda p: p.sync_task_due_notification(created, recipient_user_key=actor_user_key))
        if created.assigned_to_user_key:
            self._propagate(lambda p: p.on_task_reassigned(created, previous_user_key=None))
        return created

    def create_task_idempotent(self, task: Task, *, actor_user_key: str = "") -> tuple[Task, bool]:
        """Create a task, or upsert the existing one for an idempotent producer re-post.

        The FreeStyle producer contract (#1082 AC-3). A machine producer
        (``origin != user``) that supplies an ``external_ref`` gets *upsert*
        semantics scoped to ``(tenant_key, source, external_ref)``: re-posting the
        same reference refreshes and returns the existing task instead of
        duplicating it. Because the lookup is anchored on the caller's own
        ``tenant_key`` and ``source`` (see
        :meth:`ITaskRepository.find_task_by_external_ref`), it is never a
        cross-tenant existence oracle and two producers cannot collide.

        Interactive tasks (``origin == user``) and producer tasks without an
        ``external_ref`` fall straight through to :meth:`create_task`, so this is a
        safe superset of the plain create path and the single POST endpoint can
        route both through it.

        Returns ``(task, created)`` where ``created`` is ``False`` for an
        idempotent hit — the endpoint maps that onto HTTP 200 (vs 201 on create).
        """
        if task.origin != TaskOrigin.USER and task.source and task.external_ref:
            existing = self._repo.find_task_by_external_ref(
                tenant_key=task.tenant_key,
                source=task.source,
                external_ref=task.external_ref,
            )
            if existing is not None and existing.key:
                refreshed = self._apply_freestyle_refresh(existing, task)
                updated = self._repo.update_task(existing.key, refreshed)
                self._propagate(lambda p: p.sync_task_due_notification(updated, recipient_user_key=actor_user_key))
                return updated, False
        return self.create_task(task, actor_user_key=actor_user_key), True

    @staticmethod
    def _apply_freestyle_refresh(existing: Task, incoming: Task) -> Task:
        """Refresh a re-posted FreeStyle task's presentation fields in place.

        A producer re-post updates what the producer authored — the free text, the
        due date, the category, the run reference — while preserving everything the
        *system* owns on the existing task: its key, its lifecycle ``status`` and
        the user's own progress (started/completed timestamps, notes, ratings), its
        ``created_at`` and its ``(source, external_ref)`` identity. That way a
        re-post never resurrects a task the user already completed or silently
        re-homes it onto another entity.

        **A re-post can set the three nullable fields, never clear them** (#1525
        SCR-004). ``due_date``, ``scheduled_time`` and ``source_run_ref`` were copied
        unconditionally, and a producer that omits them gets ``None`` from the model
        default — so a re-post without a due date meant "clear the due date". That
        never *did* anything, because ``tasks`` merged every ``None`` away and the
        stored value survived; making the repository honest (#1516) would have turned
        a dormant line into data loss on the documented idempotent-upsert path
        (#1082 AC-3). Preserving the observed contract is the conservative reading,
        and a producer that genuinely wants to unset a due date has ``PUT``.

        ``model_fields_set`` is **not** the discriminator here, measured rather than
        assumed: the POST handler builds the model from
        ``body.model_dump(exclude=...)``, a *full* dump, so every field counts as set
        whether the client sent it or not. Reading it would have been a rule that
        looks precise and answers the same for every request.
        """
        existing.name = incoming.name
        existing.name_de = incoming.name_de
        existing.instruction = incoming.instruction
        existing.instruction_de = incoming.instruction_de
        existing.category = incoming.category
        existing.priority = incoming.priority
        existing.tags = incoming.tags
        for field in ("due_date", "scheduled_time", "source_run_ref"):
            value = getattr(incoming, field)
            if value is not None:
                setattr(existing, field, value)
        return existing

    def update_task(self, key: str, task: Task, *, previous: Task | None = None, actor_user_key: str = "") -> Task:
        """Persist a task edit and propagate it into the notification centre (#742).

        A due-date/title edit refreshes the task's ``task.due`` notification in
        place (owned by ``actor_user_key`` — the editing user threaded from the API
        context); a change of assignee additionally delivers a fresh assignment
        notification to the new member. The ``previous`` snapshot (pre-edit task)
        lets the coupling detect a reassignment.
        """
        # 422 recurrence.rrule_required (GP-ACC-038) — only for a rule the edit changes, so a task
        # that still carries a not-yet-migrated rule can be renamed or reassigned.
        if previous is None or task.recurrence_rule != previous.recurrence_rule:
            self._recurrence.require_rrule(task.recurrence_rule)
        prev_assignee = previous.assigned_to_user_key if previous is not None else None
        if task.assigned_to_user_key != prev_assignee:
            self._require_member_assignee(task.assigned_to_user_key, task.tenant_key)
        rule_changed = previous is None or task.recurrence_rule != previous.recurrence_rule
        updated = self._repo.update_task(key, task)
        if rule_changed and task.recurrence_rule:
            # #2411 item 4: a new RRULE answers the question the migration parked (v0097 kept the unconvertible
            # original in ``recurrence_rule_unconvertible``); no API field, no notification.
            self._repo.clear_parked_recurrence(key)
        self._propagate(lambda p: p.sync_task_due_notification(updated, recipient_user_key=actor_user_key))
        if prev_assignee != updated.assigned_to_user_key:
            self._propagate(lambda p: p.on_task_reassigned(updated, previous_user_key=prev_assignee))
        return updated

    def delete_task(self, key: str, *, tenant_key: str) -> bool:
        # ``get_task`` verifies tenant ownership before anything is read or
        # deleted, so ``self._repo.delete_task`` below is only ever reached after
        # a tenant-checked load (GHSA-h5wp-r68x-97g8).
        task = self.get_task(key, tenant_key=tenant_key)
        # No "cancelled": `TaskStatus` has no such member (pending, in_progress,
        # completed, skipped, failed, dormant), so that entry could never match a
        # status Pydantic would accept — an allowlist row that cannot fire. Dropping
        # it changes no behaviour and stops the set from describing a state machine
        # this one does not have. `failed` stays out deliberately: its photos may be
        # the record of what went wrong.
        allowed = {"pending", "skipped", "dormant"}
        if task.status not in allowed:
            raise ValidationError(
                f"Cannot delete task in status '{task.status}'. "
                f"Only {', '.join(sorted(allowed))} tasks can be deleted.",
            )
        # The status alone does not say whether this task was ever completed.
        # ``reopen_task`` puts a **completed** task back to ``pending`` and leaves
        # ``photo_refs`` in place, so without this line a reopened task is deletable
        # while carrying the photographic record of its completion — and #1393 makes
        # deletion take those photos with it (dispatched below, and the orphan sweep
        # would collect them anyway once nothing referenced them).
        #
        # The gate's own promise is that a completed task's documentation cannot be
        # lost this way. ``reopen_task`` was a back door through it; this closes it,
        # so the promise holds rather than merely reading well.
        #
        # The marker is durable because ``reopen_task`` refuses to downgrade it, not
        # because nothing writes it — an earlier version of this comment claimed the
        # latter ("never cleared — not by completing again, not by skipping"), which
        # was true of ``skip_task`` and false of the *reopen after* the skip. That
        # sequence overwrote the marker and made this refusal escapable; the claim had
        # been written from reading one method instead of running the sequence, and it
        # is why nobody looked again for four review rounds.
        #
        # The message names only what is actually possible: ``skip_task`` takes the
        # task out of the queue. It used to advise cancelling, an operation
        # ``TaskStatus`` has no member for. Whether a re-completed task should become
        # deletable again is a product question, not one this gate can answer.
        if task.reopened_from_status == "completed":
            raise ValidationError(
                "Cannot delete a task that was completed and reopened: it still carries the "
                "photos and record of that completion. Skip it to take it out of the queue.",
            )
        # No photo cleanup here, and that is a measured decision rather than an
        # omission: ``complete_task`` is the only writer of ``photo_refs``, nothing
        # ever removes an entry, and the gate above refuses every task that was once
        # completed — so a task that reaches this line carries no photos to clean up.
        # ``tests/unit/domain/services/test_deletable_task_carries_no_photos.py`` pins
        # that invariant and fails if the gate is ever relaxed.
        #
        # An eager ``delete_attachments`` call stood here through five review rounds.
        # It could not run, because of the invariant above — except through the reopen
        # hole round 6 found, where it would have destroyed exactly the completion
        # photos this gate exists to protect. A background call that deletes
        # attachments is not worth carrying for a path that cannot execute.
        deleted = self._repo.delete_task(key)
        if deleted:
            self._propagate(lambda p: p.on_task_deleted(task))
        return deleted

    def start_task(self, key: str, *, tenant_key: str) -> Task:
        task = self.get_task(key, tenant_key=tenant_key)
        if task.status != "pending":
            raise ValidationError(f"Cannot start task in status '{task.status}'.")
        task.status = "in_progress"
        task.started_at = datetime.now(UTC)
        return self._repo.update_task(key, task)

    def _verify_photo_refs(
        self,
        refs: list[str],
        already_attached: list[str],
        *,
        tenant_key: str,
    ) -> None:
        """Refuse a photo reference that is not this tenant's task attachment.

        ``TaskCompleteRequest.photo_refs`` is a bare ``list[str]`` and was
        forwarded verbatim, so ``['x']`` satisfied a ``requires_photo`` task and
        a foreign attachment id could be pinned onto one's own task. The diary
        sibling has resolved every reference through the attachment catalogue
        since REQ-050; this is the same rule for REQ-006.

        A reference already stored on the task is not re-checked: it passed once,
        and re-validating it would make an unrelated completion fail after a
        legitimate attachment was later erased under NFR-011 retention.

        Unknown, foreign and wrong-category all raise the **same**
        ``ValidationError`` (422): distinguishing them would confirm that an id
        exists somewhere else in the installation.

        Args:
            refs: The references the caller sent.
            already_attached: References the task already carries.
            tenant_key: Owning tenant of the task.

        Raises:
            ValidationError: If a new reference does not resolve to a
                ``TASK``-category attachment of this tenant, or if no attachment
                catalogue is configured to judge it.
        """
        known = set(already_attached)
        added = [ref for ref in dict.fromkeys(refs) if ref not in known]
        if not added:
            return

        if self._attachment_repo is None:
            # Fail closed. A service assembled without the resolver cannot judge
            # a reference, and accepting it "for now" is how a guard ends up
            # inert in production while every test still passes.
            raise ValidationError(
                "Task photo references cannot be validated: no attachment catalogue is configured.",
                details=[{"field": "photo_refs", "message": "attachment lookup unavailable"}],
            )

        for ref in added:
            attachment = self._attachment_repo.get(ref, tenant_key)
            if attachment is None or attachment.category != AttachmentCategory.TASK:
                raise ValidationError(
                    f"'{ref}' is not a task photo of this tenant.",
                    details=[{"field": "photo_refs", "message": f"unknown task attachment '{ref}'"}],
                )

    # ── Completion: the one transition (ADR-008 phase 3 for tasks, REQ-053 GP-FR-083) ──

    @staticmethod
    def _require_completable(task: Task) -> None:
        if task.status not in ("pending", "in_progress"):
            raise ValidationError(f"Cannot complete task in status '{task.status}'.")

    def _bed_of(self, task: Task, *, tenant_key: str) -> str | None:
        """The bed this task's completion is logged in, or ``None`` for a task outside the care log (GP-FR-083)."""
        entity = TaskCompletionEngine.bed_entity(task)
        if entity is None or self._completion is None or self._care_events is None:
            return None
        kind, entity_key = entity
        if kind == "location":
            return entity_key
        return self._completion.plant_location(entity_key, tenant_key=tenant_key)

    @staticmethod
    def _care_input(
        task: Task,
        location_key: str,
        details: TaskCompletionDetails,
        *,
        performed_at: datetime,
        completion_notes: str | None,
        photo_refs: list[str],
    ) -> CareEventInput:
        """The care event a completion logs, in the vocabulary of GP-FR-100; all fields but the instant optional."""
        try:
            return CareEventInput(
                location_key=location_key,
                category=task.category.value,
                summary=task.name,
                performed_at=performed_at,
                plant_keys=list(details.plant_keys),
                reason=details.reason,
                product_ref=details.product_ref,
                product_label=details.product_label,
                quantity=details.quantity,
                unit=details.unit,
                material=details.material,
                measurements=details.measurements,
                # The completion note is the log's note: it fills the outcome text when the client gave none.
                observed_outcome=details.observed_outcome or (completion_notes[:2000] if completion_notes else None),
                outcome_rating=details.outcome_rating,
                photo_refs=photo_refs,
            )
        except PydanticValidationError as exc:
            raise ValidationError(
                "The care fields of the completion are not valid.",
                details=[
                    {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
                    for err in exc.errors(include_url=False, include_input=False, include_context=False)
                ],
            ) from exc

    def _event_plants(self, event: CareEvent, *, tenant_key: str) -> list[str]:
        """The plants the specialist document is attributed to: the event's own, else the plants standing in the bed."""
        if event.plant_keys:
            return list(event.plant_keys)
        if self._completion is None or self._care_events is None:
            return []
        subtree = self._care_events.location_subtree(event.location_key, tenant_key=tenant_key)
        return self._completion.plants_in_locations(subtree, tenant_key=tenant_key)

    def _prepare_completion(
        self,
        task: Task,
        *,
        completion_notes: str | None,
        actual_minutes: int | None,
        photo_refs: list[str] | None,
        difficulty_rating: int | None,
        quality_rating: int | None,
        details: TaskCompletionDetails | None,
        actor: CompletionActor | None,
        tenant_key: str,
        taken_batch_ids: set[str],
    ) -> CompletionWrite:
        """Validate one completion and compute everything its transaction writes; nothing is stored here."""
        self._require_completable(task)
        if task.requires_photo and not task.photo_refs and not photo_refs:
            raise ValidationError("This task requires at least one photo before completion.")
        details = details or TaskCompletionDetails()
        new_photos: list[str] = []
        if photo_refs:
            self._verify_photo_refs(photo_refs, task.photo_refs, tenant_key=tenant_key)
            # Order-preserving dedup across what is already stored and what arrives. The completion form seeds its
            # list from the task's own `photo_refs`, so reopening a completed task and completing it again used to
            # append every existing ref a second time — `[a, a, b]` in the document and duplicate React keys in the
            # gallery (#1339 review).
            known = set(task.photo_refs)
            new_photos = [ref for ref in dict.fromkeys(photo_refs) if ref not in known]
            task.photo_refs.extend(new_photos)

        performed_at = details.performed_at or datetime.now(UTC)
        location_key = self._bed_of(task, tenant_key=tenant_key) if actor is not None else None
        event: CareEvent | None = None
        domain: DomainDocument | None = None
        replaces_event_key: str | None = None
        if location_key is not None and actor is not None and self._care_events is not None:
            event = self._build_event(
                task,
                location_key,
                details,
                actor=actor,
                performed_at=performed_at,
                completion_notes=completion_notes,
                photo_refs=new_photos,
                tenant_key=tenant_key,
            )
            if event is not None:
                domain = self._domain_document(task, event, tenant_key=tenant_key, taken_batch_ids=taken_batch_ids)
                replaces_event_key = self._line_to_replace(task, actor, tenant_key=tenant_key)
        elif details.carries_care_fields:
            raise PlanError(
                "task.no_bed_context",
                "This task is not bound to a bed, so there is no care log to write the care fields into.",
                status_code=422,
                field="plant_keys",
            )
        if event is None and details.performed_at is not None:
            check_performed_instant(performed_at)  # V-11 holds the instant of a completion outside the care log too

        task.status = TaskStatus.COMPLETED
        task.completed_at = performed_at
        if completion_notes:
            task.completion_notes = completion_notes
        if actual_minutes is not None:
            task.actual_duration_minutes = actual_minutes
        if difficulty_rating is not None:
            task.difficulty_rating = difficulty_rating
        if quality_rating is not None:
            task.quality_rating = quality_rating
        patch = task.model_dump(
            mode="json",
            include={
                "status",
                "completed_at",
                "completion_notes",
                "actual_duration_minutes",
                "difficulty_rating",
                "quality_rating",
                "photo_refs",
            },
            exclude_none=True,
        )
        return CompletionWrite(
            task_key=task.key or "",
            task_patch=patch,
            event=event,
            domain=domain,
            replaces_event_key=replaces_event_key,
        )

    def _line_to_replace(self, task: Task, actor: CompletionActor, *, tenant_key: str) -> str | None:
        """The open care line of an earlier, reopened completion that this completion may replace, else ``None``.

        Only the author of that line or a lead may take it out (no time window: the task was reopened by someone
        entitled to, and the line says "done" for a task that is not); anyone else completing the task adds a line
        and leaves the author's alone — the lead can void it (GP-API-037).
        """
        if self._completion is None:
            return None
        earlier = self._completion.task_event(task.key or "", tenant_key=tenant_key)
        if earlier is None:
            return None
        if earlier.created_by == actor.user_key or actor.role == TenantRole.LEAD:
            return earlier.key
        return None

    def _build_event(
        self,
        task: Task,
        location_key: str,
        details: TaskCompletionDetails,
        *,
        actor: CompletionActor,
        performed_at: datetime,
        completion_notes: str | None,
        photo_refs: list[str],
        tenant_key: str,
    ) -> CareEvent | None:
        """The validated care event of the completion; ``None`` when the task's bed is gone (the task still closes)."""
        assert self._care_events is not None  # noqa: S101 — guarded by the caller; narrows the optional for mypy
        data = self._care_input(
            task,
            location_key,
            details,
            performed_at=performed_at,
            completion_notes=completion_notes,
            photo_refs=photo_refs,
        )
        try:
            return self._care_events.build_event(
                data,
                tenant_key=tenant_key,
                user_key=actor.user_key,
                role=actor.role,
                origin=CareEventOrigin(trigger="task", task_key=task.key),
            )
        except NotFoundError:
            # The task points at a bed that no longer exists (or is not the tenant's): the task is still done, there
            # is just no bed to log it in. A body that named plants for that bed cannot be honoured.
            if details.carries_care_fields:
                raise
            check_performed_instant(performed_at)
            return None

    def _domain_document(
        self, task: Task, event: CareEvent, *, tenant_key: str, taken_batch_ids: set[str]
    ) -> DomainDocument | None:
        """The specialist document of the event (§12.1), with the checks its own service would have made."""
        wants_plants = event.category in (
            TaskCategory.WATERING.value,
            TaskCategory.FEEDING.value,
            TaskCategory.SOIL_AMENDMENT.value,
            TaskCategory.HARVEST.value,
        )
        plants = self._event_plants(event, tenant_key=tenant_key) if wants_plants else []
        domain = self._completion_engine.domain_document(task, event, plant_keys=plants)
        if domain is None or domain.collection != HARVEST_BATCHES:
            return domain
        if self._harvests is None:
            return None  # no harvest service wired: no batch is written rather than one that skipped the Karenz gate
        self._harvests.require_karenz_clear(plants, event.performed_at, tenant_key=tenant_key)
        plant_key = str(domain.document.get("plant_key", ""))
        batch_id = self._harvests.next_batch_id(
            plant_key, event.performed_at, tenant_key=tenant_key, taken=taken_batch_ids
        )
        return replace(domain, document={**domain.document, "batch_id": batch_id})

    def _commit_completions(self, writes: list[CompletionWrite], tasks: list[Task], *, tenant_key: str) -> list[Task]:
        """Store the prepared completions; one transaction when the transition is wired, else task by task."""
        if self._completion is not None:
            self._completion.complete(writes, tenant_key=tenant_key)
            return [self._repo.get_task_or_raise(write.task_key) for write in writes]
        return [self._repo.update_task(task.key or "", task) for task in tasks]

    def _after_completion(self, completed: Task, as_stored: Task) -> None:
        """What follows the committed completion: dependents, the next occurrence, the notification (not atomic)."""
        # Reschedule dependents if late. Coerce both operands to timezone-aware UTC first: a date-only due_date is
        # stored naive and would otherwise crash the comparison (and abort the recurrence spawn below).
        due_aware = _as_aware_utc(as_stored.due_date)
        completed_aware = _as_aware_utc(as_stored.completed_at)
        if due_aware and completed_aware and completed_aware > due_aware:
            self._reschedule_dependents(as_stored.key or "", as_stored)

        # Create next recurring task if applicable
        if as_stored.recurrence_rule:
            self._create_next_recurring_task(completed)

        # Mark the task's open due notification done (badge drops, #742).
        self._propagate(lambda p: p.on_task_completed(completed))

    def complete_task(
        self,
        key: str,
        completion_notes: str | None = None,
        actual_minutes: int | None = None,
        photo_refs: list[str] | None = None,
        difficulty_rating: int | None = None,
        quality_rating: int | None = None,
        *,
        tenant_key: str,
        details: TaskCompletionDetails | None = None,
        actor: CompletionActor | None = None,
    ) -> Task:
        """Complete a task: ONE transition over the task, the care-log line and the specialist document.

        With an ``actor`` and a task bound to a bed the care event (``trigger = task``) and — per §12.1 — the
        ``watering_events`` / ``feeding_events`` / ``harvest_batches`` document are written in the same stream
        transaction as the status change (GP-FR-083, GP-ACC-024): an error in any of them leaves the task as it was.
        A task without a bed, or a caller without an actor, closes the task alone. The recurrence spawn, the
        dependents and the notification follow the commit (their own ADR-008 strand, E-02).
        """
        task = self.get_task(key, tenant_key=tenant_key)
        prepared = self._prepare_completion(
            task,
            completion_notes=completion_notes,
            actual_minutes=actual_minutes,
            photo_refs=photo_refs,
            difficulty_rating=difficulty_rating,
            quality_rating=quality_rating,
            details=details,
            actor=actor,
            tenant_key=tenant_key,
            taken_batch_ids=set(),
        )
        updated = self._commit_completions([prepared], [task], tenant_key=tenant_key)[0]
        self._after_completion(updated, task)
        return updated

    def _reschedule_dependents(self, key: str, task: Task) -> None:
        # ``tenant_key`` is part of the guard, not an optional extra: the
        # repository rejects the empty sentinel since #927, and a task without a
        # tenant has no tenant-scoped sibling set to reschedule against. Such a
        # task simply has no dependents here rather than triggering a scan across
        # every tenant's tasks.
        if task.entity_key and task.entity_type and task.tenant_key:
            all_tasks = self._repo.get_tasks_for_entity(
                task.entity_type,
                task.entity_key,
                task.tenant_key,
            )
        else:
            all_tasks = []
        deps = self._repo.get_blocking_tasks(key)
        task_dicts = [
            {"key": t.key, "status": t.status, "priority": t.priority, "due_date": t.due_date} for t in all_tasks
        ]
        dep_dicts = [{"from_key": key, "to_key": d["key"]} for d in deps]
        # Anchor naive datetimes (a date-only due_date is stored without tzinfo)
        # so the resolver's completed_at/original_due comparison cannot crash.
        rescheduled = self._deps.reschedule_dependents(
            key,
            _as_aware_utc(task.completed_at),
            _as_aware_utc(task.due_date),
            task_dicts,
            dep_dicts,
        )
        for r in rescheduled:
            dep_task = self._repo.get_task_by_key(r["task_key"])
            if dep_task:
                dep_task.due_date = datetime.fromisoformat(r["new_due_date"])
                self._repo.update_task(r["task_key"], dep_task)

    def _create_next_recurring_task(self, completed_task: Task) -> Task | None:
        """Create the next instance of a recurring task after completion."""
        if not completed_task.recurrence_rule:
            return None

        # Check end date
        if completed_task.recurrence_end_date and datetime.now(UTC) >= completed_task.recurrence_end_date:
            return None

        # Compute the next due date from the recurrence rule via the shared engine.
        next_dt = self._recurrence.next_occurrence(completed_task.recurrence_rule, datetime.now(UTC))
        if next_dt is None:
            return None

        new_task = Task(
            tenant_key=completed_task.tenant_key,
            name=completed_task.name,
            name_de=completed_task.name_de,
            instruction=completed_task.instruction,
            instruction_de=completed_task.instruction_de,
            category=completed_task.category,
            entity_key=completed_task.entity_key,
            entity_type=completed_task.entity_type,
            due_date=next_dt,
            scheduled_time=completed_task.scheduled_time,
            status="pending",
            priority=completed_task.priority,
            skill_level=completed_task.skill_level,
            stress_level=completed_task.stress_level,
            estimated_duration_minutes=completed_task.estimated_duration_minutes,
            requires_photo=completed_task.requires_photo,
            timer_duration_seconds=completed_task.timer_duration_seconds,
            timer_label=completed_task.timer_label,
            tags=list(completed_task.tags),
            checklist=[
                ChecklistItem(text=item.text, done=False, order=item.order) for item in completed_task.checklist
            ],
            # Only while the assignee is still an active member (#1876 review, Info):
            # a member who left stayed the assignee of every later occurrence.
            assigned_to_user_key=self._still_a_member(completed_task.assigned_to_user_key, completed_task.tenant_key),
            recurrence_rule=completed_task.recurrence_rule,
            recurrence_end_date=completed_task.recurrence_end_date,
            parent_recurring_task_key=completed_task.key,
        )
        return self._repo.create_task(new_task)

    def _compute_next_recurrence(self, rule: str, after: datetime) -> datetime | None:
        """Delegate to the shared :class:`RecurrenceEngine` (kept for callers/tests).

        The recurrence algorithm now lives in one place so the generic task path
        and the fixed-interval care path share a single implementation (#510).
        """
        return self._recurrence.next_occurrence(rule, after)

    def skip_task(self, key: str, *, tenant_key: str) -> Task:
        task = self.get_task(key, tenant_key=tenant_key)
        if task.status not in ("pending", "in_progress"):
            raise ValidationError(f"Cannot skip task in status '{task.status}'.")
        task.status = "skipped"
        task.completed_at = datetime.now(UTC)
        updated = self._repo.update_task(key, task)
        self._propagate(lambda p: p.on_task_completed(updated))
        return updated

    # ── Clone ──

    def clone_task(
        self,
        key: str,
        due_date_offset_days: int | None = None,
        target_entity_key: str | None = None,
        target_entity_type: str | None = None,
        *,
        tenant_key: str,
    ) -> Task:
        source = self.get_task(key, tenant_key=tenant_key)
        due_date = None
        if due_date_offset_days is not None:
            # recurrence-owner-ok: a clone offset the caller chooses for one new task. It
            # produces a single due date and establishes no cadence — the cloned task's own
            # recurrence_rule, if it has one, is advanced by RecurrenceEngine.
            due_date = datetime.now(UTC) + timedelta(days=due_date_offset_days)

        entity_key = target_entity_key or source.entity_key
        entity_type = target_entity_type or source.entity_type
        return self._clone_of(source, entity_type=entity_type, entity_key=entity_key, due_date=due_date)

    def _clone_of(
        self, source: Task, *, entity_type: str | None, entity_key: str | None, due_date: datetime | None
    ) -> Task:
        """One new pending task copied from ``source`` onto an entity, linked by ``task_cloned_from`` (GP-FR-081)."""
        new_task = Task(
            tenant_key=source.tenant_key,
            name=source.name,
            name_de=source.name_de,
            instruction=source.instruction,
            instruction_de=source.instruction_de,
            category=source.category,
            entity_key=entity_key,
            entity_type=entity_type,
            due_date=due_date,
            status="pending",
            priority=source.priority,
            skill_level=source.skill_level,
            stress_level=source.stress_level,
            estimated_duration_minutes=source.estimated_duration_minutes,
            requires_photo=source.requires_photo,
            timer_duration_seconds=source.timer_duration_seconds,
            timer_label=source.timer_label,
            tags=list(source.tags),
            checklist=[ChecklistItem(text=item.text, done=False, order=item.order) for item in source.checklist],
        )
        created = self._repo.create_task(new_task)
        if source.key and created.key:
            self._repo.create_task_cloned_from_edge(created.key, source.key)
        return created

    def fan_out_to_plants(
        self,
        key: str,
        *,
        tenant_key: str,
        include_children: bool = True,
        keep_source: bool = False,
    ) -> list[Task]:
        """ "For every plant in the bed": one clone of a bed task per plant standing in it (GP-FR-081).

        ``key`` must be an open task bound to a bed (``entity_type = location``). Every active plant of the bed
        (and of its sub-locations when ``include_children``) gets a pending clone bound to it, linked back by a
        ``task_cloned_from`` edge. The bed task itself is then ``skipped`` — the user chose "for every plant"
        *instead of* "for the bed" — unless ``keep_source``. A bed without plants clones nothing and leaves the
        source open. The clones are written one by one, not in one transaction: a failure part-way leaves the
        source open, so the request is not lost; a retry clones only the plants that hold no clone yet.
        """
        self._require_tenant_key(tenant_key, "fan_out_to_plants")
        source = self.get_task(key, tenant_key=tenant_key)
        self._require_completable(source)
        if source.entity_type != "location" or not source.entity_key:
            raise ValidationError(
                "Only a task bound to a bed (entity_type 'location') can be fanned out to its plants."
            )
        if source.category == "care_reminder":
            # Care reminders have their own strand (GP-FR-106), and the queue collapses same-named care tasks.
            raise ValidationError("A care reminder cannot be fanned out; the reminder engine writes one per plant.")
        if self._care_events is None or self._completion is None:
            raise RuntimeError("fan_out_to_plants needs the care-event service and the completion repository.")
        scope = self._care_events.location_scope(
            source.entity_key, include_children=include_children, tenant_key=tenant_key
        )
        plants = self._completion.plants_in_locations(scope, tenant_key=tenant_key)
        if len(plants) > MAX_FAN_OUT:
            raise ValidationError(
                f"The bed holds {len(plants)} plants; at most {MAX_FAN_OUT} tasks are created at once."
            )
        # A retry after a failure part-way clones only the plants that have no clone yet.
        already = self._repo.get_clone_entity_keys(key, tenant_key=tenant_key)
        clones = [
            self._clone_of(source, entity_type="plant_instance", entity_key=plant_key, due_date=source.due_date)
            for plant_key in plants
            if plant_key not in already
        ]
        if plants and not keep_source:
            self.skip_task(key, tenant_key=tenant_key)
        return clones

    # ── Reopen ──

    def reopen_task(
        self,
        key: str,
        *,
        tenant_key: str,
        undo: bool = False,
        actor: CompletionActor | None = None,
    ) -> Task:
        """Reopen a completed or skipped task.

        ``undo`` is the field-mode snackbar (GP-FR-149): the task's care-log line is voided with
        ``void_reason = undo`` in the same transaction as the reopen — the lead any time, the author within ten
        minutes (the predicate of ``POST /care-events/{key}/void``, GP-API-037). It needs the ``actor``.
        """
        if undo and actor is None:
            raise ValueError("reopen_task(undo=True) needs the actor: the void is held to the caller's role.")
        task = self.get_task(key, tenant_key=tenant_key)
        if task.status not in ("completed", "skipped"):
            raise ValidationError(
                f"Cannot reopen task in status '{task.status}'. Only completed or skipped tasks can be reopened.",
            )
        # Never downgraded once it says ``"completed"``. ``delete_task`` reads this
        # field to refuse destroying a task that still carries the ``photo_refs``
        # completion wrote, and the plain assignment made that refusal escapable with
        # four ordinary clicks: complete → reopen (marker "completed") → skip
        # (``skip_task`` accepts ``pending``) → reopen (marker overwritten with
        # "skipped"). ``photo_refs`` is untouched throughout, so the photos were still
        # there and the gate was not.
        #
        # The two obvious alternative anchors do not work. ``completed_at`` is set to
        # ``None`` three lines below, by this very method. Gating on non-empty
        # ``photo_refs`` would be unbypassable — nothing ever removes an entry — but it
        # narrows the rule to "carries photos" where the decision taken was "was ever
        # completed", and a completion without photos is still a completion.
        #
        # The field's meaning becomes "the status this task was reopened from, with a
        # completion remembered in preference to a later skip". ``delete_task`` is its
        # only production reader; the API exposes it and no client reads it.
        if task.reopened_from_status != "completed":
            task.reopened_from_status = task.status
        task.reopened_at = datetime.now(UTC)
        task.status = TaskStatus.PENDING
        task.completed_at = None
        task.actual_duration_minutes = None
        task.completion_notes = None
        task.difficulty_rating = None
        task.quality_rating = None
        if undo and actor is not None and self._completion is not None and self._care_events is not None:
            event = self._completion.task_event(key, tenant_key=tenant_key)
            if event is not None:
                check_void_allowed(event, reason=UNDO_REASON, user_key=actor.user_key, role=actor.role)
            self._completion.reopen(
                UndoWrite(
                    task_key=key,
                    task_patch=task.model_dump(
                        mode="json",
                        include={
                            "status",
                            "reopened_at",
                            "reopened_from_status",
                            "completed_at",
                            "actual_duration_minutes",
                            "completion_notes",
                            "difficulty_rating",
                            "quality_rating",
                        },
                    ),
                    event_key=event.key if event else None,
                    voided_by=actor.user_key,
                    voided_at=datetime.now(UTC),
                ),
                tenant_key=tenant_key,
            )
            return self._repo.get_task_or_raise(key)
        return self._repo.update_task(key, task)

    # ── Batch Operations ──
    #
    # Found by the #948 write-surface sweep. Every *single*-task route resolves
    # its key with ``service.get_task(key, tenant_key=ctx.tenant_key)`` first —
    # the line each router has to remember — and all three batch routes forgot
    # it, while taking their ``task_keys`` from the request body. A member of
    # tenant A could therefore complete, skip, delete or reassign another
    # tenant's tasks in bulk. ``tenant_key`` is now required and keyword-only on
    # all three, and each key is resolved through the tenant guard before
    # anything is written. A foreign key lands in ``failed`` with the same
    # "not found" text an unknown key produces, so the batch envelope is not a
    # cross-tenant oracle either.

    def batch_status_change(
        self,
        task_keys: list[str],
        action: str,
        completion_notes: str | None = None,
        *,
        tenant_key: str,
        details: TaskCompletionDetails | None = None,
        actor: CompletionActor | None = None,
    ) -> tuple[list[str], list[dict]]:
        """Apply ``start`` / ``complete`` / ``skip`` to many tasks.

        ``complete`` is the atomic transition (GP-FR-088, GP-API-032): every key is resolved first — an unknown or
        foreign one answers 404 for the **whole** batch and nothing is written — then the completable tasks are
        completed in ONE transaction, one care event each. A task that cannot be completed (wrong status, missing
        photo) is reported in ``failed`` and left out. The other actions keep their per-key result.
        """
        if action != "complete" and details is not None and (details.carries_care_fields or details.performed_at):
            raise ValidationError(
                "Care fields belong to action 'complete'.",
                details=[{"field": "action", "message": "performed_at and care fields apply to 'complete' only"}],
            )
        if action == "complete":
            return self._batch_complete(
                task_keys, completion_notes, tenant_key=tenant_key, details=details, actor=actor
            )
        succeeded: list[str] = []
        failed: list[dict] = []
        for tk in task_keys:
            try:
                # Each mutating call now enforces the tenant guard itself; the
                # explicit resolve is kept so the unknown-action branch below is
                # also tenant-checked and never becomes an existence oracle.
                self.get_task(tk, tenant_key=tenant_key)
                if action == "start":
                    self.start_task(tk, tenant_key=tenant_key)
                elif action == "skip":
                    self.skip_task(tk, tenant_key=tenant_key)
                else:
                    failed.append({"key": tk, "error": f"Unknown action: {action}"})
                    continue
                succeeded.append(tk)
            except (NotFoundError, ValidationError) as e:
                failed.append({"key": tk, "error": str(e)})
        return succeeded, failed

    def _batch_complete(
        self,
        task_keys: list[str],
        completion_notes: str | None,
        *,
        tenant_key: str,
        details: TaskCompletionDetails | None,
        actor: CompletionActor | None,
    ) -> tuple[list[str], list[dict[str, str]]]:
        keys = list(dict.fromkeys(task_keys))
        if len(keys) > MAX_BATCH_COMPLETION:
            raise ValidationError(
                f"A batch completes at most {MAX_BATCH_COMPLETION} tasks.",
                details=[{"field": "task_keys", "message": f"at most {MAX_BATCH_COMPLETION}"}],
            )
        # All keys first: a foreign or unknown one is a 404 for the whole batch (GP-API-032) — before any write and
        # before any status is judged, so the answer cannot tell a foreign task from an absent one.
        tasks = [self.get_task(key, tenant_key=tenant_key) for key in keys]
        failed: list[dict[str, str]] = []
        prepared: list[CompletionWrite] = []
        ready: list[Task] = []
        taken_batch_ids: set[str] = set()
        for task in tasks:
            try:
                prepared.append(
                    self._prepare_completion(
                        task,
                        completion_notes=completion_notes,
                        actual_minutes=None,
                        photo_refs=None,
                        difficulty_rating=None,
                        quality_rating=None,
                        details=details,
                        actor=actor,
                        tenant_key=tenant_key,
                        taken_batch_ids=taken_batch_ids,
                    )
                )
                ready.append(task)
            except (ValidationError, KarenzViolationError) as e:
                # Not completable (status, missing photo) or a harvest inside its safety interval: this task is
                # reported and left out. A refused reference of the care fields (a plant outside the bed) is the
                # request's error and fails the whole batch with its own code.
                failed.append({"key": task.key or "", "error": str(e)})
        if not ready:
            return [], failed
        stored = self._commit_completions(prepared, ready, tenant_key=tenant_key)
        for completed, as_stored in zip(stored, ready, strict=True):
            # The batch is committed: one task's follow-up (next occurrence, notification) failing must not turn the
            # answer into a 500 for tasks that are completed, nor starve the follow-up of the rest.
            try:
                self._after_completion(completed, as_stored)
            except Exception as exc:  # noqa: BLE001 — see above; the failure is logged by type, never by text
                logger.error("task_completion.follow_up_failed", task_key=completed.key, error_type=type(exc).__name__)
        return [task.key or "" for task in stored], failed

    def batch_delete(self, task_keys: list[str], *, tenant_key: str) -> tuple[list[str], list[dict]]:
        succeeded: list[str] = []
        failed: list[dict] = []
        for tk in task_keys:
            try:
                self.delete_task(tk, tenant_key=tenant_key)
                succeeded.append(tk)
            except (NotFoundError, ValidationError) as e:
                failed.append({"key": tk, "error": str(e)})
        return succeeded, failed

    def batch_assign(
        self,
        task_keys: list[str],
        assigned_to_user_key: str,
        *,
        tenant_key: str,
    ) -> tuple[list[str], list[dict]]:
        succeeded: list[str] = []
        failed: list[dict] = []
        for tk in task_keys:
            try:
                task = self.get_task(tk, tenant_key=tenant_key)
                self._require_member_assignee(assigned_to_user_key, tenant_key)
                previous_assignee = task.assigned_to_user_key
                task.assigned_to_user_key = assigned_to_user_key
                updated = self._repo.update_task(tk, task)
                if previous_assignee != assigned_to_user_key:
                    self._propagate(
                        lambda p, u=updated, prev=previous_assignee: p.on_task_reassigned(u, previous_user_key=prev)
                    )
                succeeded.append(tk)
            except (NotFoundError, ValidationError) as e:
                failed.append({"key": tk, "error": str(e)})
        return succeeded, failed

    # ── Comments ──

    def list_comments(self, task_key: str, *, tenant_key: str) -> list[TaskComment]:
        """A task's comments, scoped to ``tenant_key`` (#927).

        The task lookup verifies ownership and answers 404 for a foreign key; the
        repository applies the same tenant predicate to the comment query, so the
        isolation survives a caller that forgets the first step.
        """
        self.get_task(task_key, tenant_key=tenant_key)
        return self._repo.get_comments_for_task(task_key, tenant_key=tenant_key)

    def create_comment(self, task_key: str, text: str, created_by: str, *, tenant_key: str) -> TaskComment:
        self.get_task(task_key, tenant_key=tenant_key)  # ensure task exists and belongs to the tenant
        comment = TaskComment(
            task_key=task_key,
            comment_text=text,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        return self._repo.create_comment(comment)

    def update_comment(self, task_key: str, comment_key: str, text: str, *, tenant_key: str) -> TaskComment:
        self.get_task(task_key, tenant_key=tenant_key)  # ensure task exists and belongs to the tenant
        comment = self._task_comment(task_key, comment_key)
        comment.comment_text = text
        comment.updated_at = datetime.now(UTC)
        return self._repo.update_comment(comment_key, comment)

    def delete_comment(self, task_key: str, comment_key: str, *, tenant_key: str) -> bool:
        self.get_task(task_key, tenant_key=tenant_key)  # ensure task exists and belongs to the tenant
        self._task_comment(task_key, comment_key)
        return self._repo.delete_comment(comment_key)

    def _task_comment(self, task_key: str, comment_key: str) -> TaskComment:
        """The comment ``comment_key`` of ``task_key`` — 404 for an absent one *and* another task's (MT-045.7).

        The task is already scoped to the caller's tenant; the comment is loaded by key
        alone. Answering another task's comment with a 422 ("does not belong") told it
        apart from a missing key — an existence oracle over every tenant's comments.
        """
        comment = self._repo.get_comment_or_raise(comment_key)
        if comment.task_key != task_key:
            raise NotFoundError("TaskComment", comment_key)
        return comment

    # ── Audit / History ──

    def get_task_history(self, task_key: str, *, tenant_key: str) -> list[TaskAuditEntry]:
        self.get_task(task_key, tenant_key=tenant_key)  # ensure task exists and belongs to the tenant
        return self._repo.get_audit_entries_for_task(task_key)

    def _record_audit(
        self,
        task_key: str,
        action: str,
        changed_by: str = "system",
        field: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> TaskAuditEntry:
        entry = TaskAuditEntry(
            task_key=task_key,
            changed_at=datetime.now(UTC),
            changed_by=changed_by,
            action=action,
            field=field,
            old_value=old_value,
            new_value=new_value,
        )
        return self._repo.create_audit_entry(entry)

    # ── Dormant Task Activation ──

    def activate_dormant_tasks_for_phase(
        self, plant_key: str, phase_name: str, *, trigger: object = None
    ) -> list[Task]:
        """Activate dormant tasks whose trigger_phase matches the new phase.

        ``trigger`` is part of the shared post-transition callback contract
        (:meth:`PhaseService.register_on_transition`) but is irrelevant here — a
        dormant task is activated by reaching its phase regardless of whether the
        transition was automatic or manual — so it is accepted and ignored.
        """
        dormant_tasks = self._repo.get_dormant_tasks_for_phase(plant_key, phase_name)
        activated: list[Task] = []
        now = datetime.now(UTC)
        for task in dormant_tasks:
            task.status = "pending"
            if task.trigger_phase and task.trigger_phase == phase_name:
                # For phase_entry triggers: due now
                # For days_after_phase: offset from now
                tt = self._repo.get_task_template_by_key(task.template_key or "")
                if tt and tt.trigger_type == "days_after_phase" and tt.days_offset:
                    # recurrence-owner-ok: a `days_after_phase` template offset measured from the
                    # phase entry. It fires once per transition for a dormant task and advances no
                    # cadence.
                    task.due_date = now + timedelta(days=tt.days_offset)
                else:
                    task.due_date = now
            else:
                task.due_date = now
            updated = self._repo.update_task(task.key or "", task)
            activated.append(updated)
        return activated

    # ── Add Task to Workflow Execution ──

    def add_task_to_workflow_execution(self, execution_key: str, task: Task, *, tenant_key: str) -> Task:
        """Attach an ad-hoc task to ``tenant_key``'s execution ``execution_key``.

        The execution is resolved under the caller's tenant first (#1714): a
        foreign or orphaned execution is a 404, exactly like an unknown key, and
        nothing is written. Without it a member of one tenant could append tasks
        to — and so move the progress of — another tenant's execution.
        """
        execution = self.get_workflow_execution(execution_key, tenant_key=tenant_key)
        task.workflow_execution_key = execution_key
        task.entity_key = task.entity_key or execution.entity_key
        task.entity_type = task.entity_type or execution.entity_type
        return self._repo.create_task(task)

    # ── Task Queue ──

    def get_task_queue(
        self,
        plant_key: str | None = None,
        *,
        tenant_key: str,
        category: str | None = None,
        origins: Sequence[str] | None = None,
        location_key: str | None = None,
        include_children: bool = True,
    ) -> list[Task]:
        """The prioritised task queue of one tenant (#927, #1503).

        ``location_key`` (REQ-053 GP-FR-080, GP-API-030) narrows the queue to a bed: the tasks bound to it and to
        the plants standing in it, with the sub-locations below it when ``include_children``. The bed is resolved
        against the caller's tenant here, so a foreign or unknown key is a 404 — never an empty queue. It excludes
        ``plant_key``: asking for both is a 422 rather than a silent intersection.

        Both branches are tenant-scoped: the per-plant one because ``plant_key``
        comes from a query parameter and used to select across tenants, the
        unfiltered one because it used to return the whole installation's pending
        tasks.

        ``category`` and ``origins`` are narrowings of the **query**, not of its
        answer. The unscoped branch is capped at :data:`QUEUE_LIMIT` rows, so a
        caller that fetched the page and filtered it afterwards could only ever
        see what the cap had already let through — a task matching the filter but
        sorting past the cut simply was not in the payload (#1503, the shape
        #1484 closed for ``plant_key``). Both are threaded into the query the
        same way ``plant_key`` is, and both apply to either branch.
        """
        if plant_key and location_key:
            raise ValidationError("plant_key and location_key cannot be combined.")
        if location_key:
            if self._care_events is None:
                raise RuntimeError("get_task_queue by location needs the care-event service.")
            scope = self._care_events.location_scope(
                location_key, include_children=include_children, tenant_key=tenant_key
            )
            tasks = self._repo.get_pending_tasks_in_locations(
                scope, QUEUE_LIMIT, tenant_key=tenant_key, category=category, origins=origins
            )
        elif plant_key:
            tasks = self._repo.get_tasks_for_plant(
                plant_key, "pending", tenant_key=tenant_key, category=category, origins=origins
            )
        else:
            tasks, _ = self._repo.get_pending_tasks(
                0, QUEUE_LIMIT, tenant_key=tenant_key, category=category, origins=origins
            )

        # Deduplicate care_reminder tasks: keep only the newest per entity_key + name suffix
        tasks = self._deduplicate_care_tasks(tasks)

        task_dicts = [
            {
                "key": t.key,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in tasks
        ]
        deps: list[dict] = []
        for t in tasks:
            blocking = self._repo.get_blocking_tasks(t.key or "")
            for b in blocking:
                deps.append({"from_key": b["key"], "to_key": t.key})

        ready_dicts = self._deps.get_ready_tasks(task_dicts, deps)
        ready_keys = {d["key"] for d in ready_dicts}
        return [t for t in tasks if t.key in ready_keys]

    @staticmethod
    def _deduplicate_care_tasks(tasks: list[Task]) -> list[Task]:
        """Remove duplicate care_reminder tasks for the same plant + reminder type.

        Groups by ``(tenant_key, full task name)`` — the name (e.g.
        "CANNA-0320-X90 — watering") is unique per plant+type, and pinning the
        tenant_key ensures two tenants whose plants happen to share a display
        name + reminder type are never collapsed into one (cross-tenant dedup
        gap, #509). Within each group, prefers tasks with entity_key set (newer
        format) over those without (legacy data), then by newest due_date/created_at.
        """
        result: list[Task] = []
        care_groups: dict[tuple[str, str], list[Task]] = {}

        for task in tasks:
            if task.category == "care_reminder":
                # Group by (tenant, full name) — tenant-scoped so the read-time
                # safety net can never merge two tenants' care tasks (#509).
                care_groups.setdefault((task.tenant_key, task.name), []).append(task)
            else:
                result.append(task)

        def _as_aware(value: datetime | None) -> datetime:
            """Coerce a datetime to timezone-aware UTC for safe comparison.

            Persisted tasks can carry a mix of timezone-aware (parsed from ISO
            strings with an offset) and timezone-naive ``due_date``/``created_at``
            values. Comparing the two directly raises ``TypeError`` and would
            crash the whole task queue, so naive values are anchored to UTC and
            missing values fall back to the minimum instant.
            """
            if value is None:
                return datetime.min.replace(tzinfo=UTC)
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value

        for group in care_groups.values():
            if len(group) == 1:
                result.append(group[0])
            else:
                # Prefer tasks with entity_key, then newest by due_date/created_at
                def _sort_key(t):  # noqa: E501
                    return (
                        1 if t.entity_key else 0,
                        _as_aware(t.due_date),
                        _as_aware(t.created_at),
                    )

                best = max(group, key=_sort_key)
                result.append(best)

        return result

    def get_overdue_tasks(self, *, tenant_key: str) -> list[Task]:
        """Overdue tasks of one tenant (#927)."""
        tasks = self._repo.get_overdue_tasks(tenant_key=tenant_key)
        return self._deduplicate_care_tasks(tasks)

    def get_tasks_for_plant(
        self,
        plant_key: str,
        status: str | None = None,
        *,
        tenant_key: str,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Task]:
        """A plant's tasks, scoped to ``tenant_key`` (#927).

        ``plant_key`` is not resolved against the caller's tenant here — the
        repository's tenant predicate is what turns a foreign key into an empty
        list instead of the other tenant's task list. ``offset``/``limit`` read
        one window (MT-035, #2131).
        """
        return self._repo.get_tasks_for_plant(plant_key, status, tenant_key=tenant_key, offset=offset, limit=limit)

    def get_tasks_for_entity(
        self,
        entity_type: str,
        entity_key: str,
        tenant_key: str,
        status: str | None = None,
    ) -> list[Task]:
        return self._repo.get_tasks_for_entity(entity_type, entity_key, tenant_key, status)

    # ── HST Validation ──

    def validate_hst(
        self,
        task_name: str,
        current_phase: str,
        recent_hst_tasks: list[dict],
        species_name: str = "",
    ) -> dict:
        return self._hst.validate(
            task_name,
            current_phase,
            recent_hst_tasks,
            species_name,
        )

    # ── Workflow Execution ──

    def get_workflow_execution(self, key: str, *, tenant_key: str) -> WorkflowExecution:
        """``tenant_key``'s execution ``key``; foreign, orphaned and unknown are one 404 (#1714)."""
        return self._repo.get_workflow_execution_or_raise(key, tenant_key=tenant_key)

    def get_executions_for_template(
        self, template_key: str, *, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> list[dict]:
        """A template's executions in ``tenant_key``, newest first; ``offset``/``limit`` read one window (MT-035)."""
        return self._repo.get_executions_for_template(template_key, tenant_key=tenant_key, offset=offset, limit=limit)
