from datetime import UTC, date, datetime

from arango.database import StandardDatabase

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.common.types import TaskKey, WorkflowExecutionKey, WorkflowTemplateKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.tenant_scope import tenant_union_predicate
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.models.task import (
    Task,
    TaskAuditEntry,
    TaskComment,
    TaskTemplate,
    WorkflowExecution,
    WorkflowPhase,
    WorkflowTemplate,
)

ENTITY_TYPE_TO_COLLECTION: dict[str, str] = {
    "plant_instance": col.PLANT_INSTANCES,
    "planting_run": col.PLANTING_RUNS,
    "location": col.LOCATIONS,
    "tank": col.TANKS,
}


class ArangoTaskRepository(BaseArangoRepository[Task], ITaskRepository):
    # Base collection TASKS is tenant-scoped.  Tenant listings use get_all_tasks
    # (which filters explicitly); the inherited get_all is only reached from
    # system Celery tasks that must opt in via all_tenants=True.
    is_tenant_scoped = True
    _model_cls = Task

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.TASKS)

    # ── WorkflowTemplate ──

    def get_all_workflow_templates(
        self,
        offset: int = 0,
        limit: int = 50,
        species_key: str | None = None,
        tenant_key: str | None = None,
        target_entity_type: str | None = None,
    ) -> tuple[list[WorkflowTemplate], int]:
        filter_parts: list[str] = []
        bind_vars: dict = {}
        let_clause = ""
        if species_key:
            filter_parts.append("doc.species_key == @species_key")
            bind_vars["species_key"] = species_key
        if tenant_key:
            # Workflow templates are a hybrid catalog: globally seeded system
            # templates (is_system, empty tenant_key) PLUS per-tenant custom
            # templates. Mirror the fertilizer/nutrient-plan repositories and
            # union the caller's own rows with the global rows; a foreign
            # tenant's rows stay excluded (SEC-B4). A strict equality filter
            # here (PR #324) hid every system template from real tenants.
            predicate, predicate_vars = tenant_union_predicate(tenant_key)
            filter_parts.append(predicate)
            bind_vars.update(predicate_vars)
            # Copy-on-write dedup (#1030). Once this tenant has forked a shared
            # generated plan (#1003/#1029), the union above would surface BOTH
            # the shared original and the tenant's private copy under the same
            # name. The fork carries ``source_workflow_key`` pointing at the
            # shared row it was copied from; suppress exactly that shared row for
            # this caller so N shared plans yield N rows, not N+1, and the row
            # the caller keeps is their editable fork.
            #
            # The suppression is expressed in AQL (a ``LET`` collecting this
            # tenant's fork sources, then ``doc._key NOT IN`` it) rather than a
            # post-fetch Python filter, so it happens BEFORE ``LIMIT`` and the
            # COLLECT count. Filtering after the fetch would miscount a page (a
            # 25-row page could silently return 24) and could hide a fork whose
            # source sits on a different page. A tenant that has not forked has
            # an empty ``forked_source_keys`` and nothing is suppressed.
            let_clause = (
                f"LET forked_source_keys = ("
                f"FOR fork IN {col.WORKFLOW_TEMPLATES} "
                f"FILTER fork.tenant_key == @tenant_key AND fork.source_workflow_key != null "
                f"RETURN fork.source_workflow_key) "
            )
            filter_parts.append("doc._key NOT IN forked_source_keys")
        if target_entity_type:
            filter_parts.append("(@target_entity_type IN doc.target_entity_types)")
            bind_vars["target_entity_type"] = target_entity_type
        filt = ("FILTER " + " AND ".join(filter_parts)) if filter_parts else ""
        query = f"{let_clause}FOR doc IN {col.WORKFLOW_TEMPLATES} {filt} SORT doc.name LIMIT @offset, @limit RETURN doc"
        count_query = (
            f"{let_clause}FOR doc IN {col.WORKFLOW_TEMPLATES} {filt} COLLECT WITH COUNT INTO total RETURN total"
        )
        count_vars = dict(bind_vars)
        bind_vars["offset"] = offset
        bind_vars["limit"] = limit
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [WorkflowTemplate(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = next(count_cursor, 0)
        return items, total

    def get_workflow_template_by_key(self, key: WorkflowTemplateKey) -> WorkflowTemplate | None:
        coll = self._db.collection(col.WORKFLOW_TEMPLATES)
        doc = coll.get(key)
        return WorkflowTemplate(**self._from_doc(doc)) if doc else None

    def get_workflow_template_or_raise(self, key: WorkflowTemplateKey) -> WorkflowTemplate:
        return self.get_or_raise_by(self.get_workflow_template_by_key, "WorkflowTemplate", key)

    def create_workflow_template(self, template: WorkflowTemplate) -> WorkflowTemplate:
        coll = self._db.collection(col.WORKFLOW_TEMPLATES)
        data = self._to_doc(template)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        return WorkflowTemplate(**self._from_doc(result["new"]))

    def update_workflow_template(self, key: str, template: WorkflowTemplate) -> WorkflowTemplate:
        coll = self._db.collection(col.WORKFLOW_TEMPLATES)
        data = self._to_doc(template)
        data["updated_at"] = self._now()
        result = coll.update({"_key": key, **data}, return_new=True)
        return WorkflowTemplate(**self._from_doc(result["new"]))

    def delete_workflow_template(self, key: str) -> bool:
        wf_id = f"{col.WORKFLOW_TEMPLATES}/{key}"
        # Delete wf_contains edges
        query = f"FOR e IN {col.WF_CONTAINS} FILTER e._from == @wf_id REMOVE e IN {col.WF_CONTAINS}"
        self._db.aql.execute(query, bind_vars={"wf_id": wf_id})
        # Delete wf_has_phase edges and phases
        query = f"FOR e IN {col.WF_HAS_PHASE} FILTER e._from == @wf_id REMOVE e IN {col.WF_HAS_PHASE}"
        self._db.aql.execute(query, bind_vars={"wf_id": wf_id})
        query = (
            f"FOR doc IN {col.WORKFLOW_PHASES} "
            f"FILTER doc.workflow_template_key == @key "
            f"REMOVE doc IN {col.WORKFLOW_PHASES}"
        )
        self._db.aql.execute(query, bind_vars={"key": key})
        # Delete associated task templates
        query = (
            f"FOR doc IN {col.TASK_TEMPLATES} "
            f"FILTER doc.workflow_template_key == @key "
            f"REMOVE doc IN {col.TASK_TEMPLATES}"
        )
        self._db.aql.execute(query, bind_vars={"key": key})
        try:
            self._db.collection(col.WORKFLOW_TEMPLATES).delete(key)
            return True
        except Exception:
            return False

    # ── WorkflowPhase ──

    def get_phases_for_workflow(self, wf_key: WorkflowTemplateKey) -> list[WorkflowPhase]:
        query = (
            f"FOR doc IN {col.WORKFLOW_PHASES} "
            f"FILTER doc.workflow_template_key == @wf_key "
            f"SORT doc.phase_order "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"wf_key": wf_key})
        return [WorkflowPhase(**self._from_doc(doc)) for doc in cursor]

    def get_phase_by_key(self, key: str) -> WorkflowPhase | None:
        doc = self._db.collection(col.WORKFLOW_PHASES).get(key)
        return WorkflowPhase(**self._from_doc(doc)) if doc else None

    def get_phase_or_raise(self, key: str) -> WorkflowPhase:
        return self.get_or_raise_by(self.get_phase_by_key, "WorkflowPhase", key)

    def create_phase(self, phase: WorkflowPhase) -> WorkflowPhase:
        coll = self._db.collection(col.WORKFLOW_PHASES)
        data = self._to_doc(phase)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        created = WorkflowPhase(**self._from_doc(result["new"]))
        if phase.workflow_template_key:
            self.create_edge(
                col.WF_HAS_PHASE,
                f"{col.WORKFLOW_TEMPLATES}/{phase.workflow_template_key}",
                f"{col.WORKFLOW_PHASES}/{created.key}",
            )
        return created

    def update_phase(self, key: str, phase: WorkflowPhase) -> WorkflowPhase:
        coll = self._db.collection(col.WORKFLOW_PHASES)
        data = self._to_doc(phase)
        data["updated_at"] = self._now()
        result = coll.update({"_key": key, **data}, return_new=True)
        return WorkflowPhase(**self._from_doc(result["new"]))

    def delete_phase(self, key: str) -> bool:
        phase_id = f"{col.WORKFLOW_PHASES}/{key}"
        # Remove wf_has_phase edges
        query = f"FOR e IN {col.WF_HAS_PHASE} FILTER e._to == @phase_id REMOVE e IN {col.WF_HAS_PHASE}"
        self._db.aql.execute(query, bind_vars={"phase_id": phase_id})
        # Null out workflow_phase_key on task templates
        query = (
            f"FOR doc IN {col.TASK_TEMPLATES} "
            f"FILTER doc.workflow_phase_key == @key "
            f"UPDATE doc WITH {{ workflow_phase_key: null }} IN {col.TASK_TEMPLATES}"
        )
        self._db.aql.execute(query, bind_vars={"key": key})
        try:
            self._db.collection(col.WORKFLOW_PHASES).delete(key)
            return True
        except Exception:
            return False

    def reorder_phases(self, phase_orders: list[dict]) -> list[WorkflowPhase]:
        coll = self._db.collection(col.WORKFLOW_PHASES)
        now = self._now()
        for item in phase_orders:
            coll.update({"_key": item["key"], "phase_order": item["phase_order"], "updated_at": now})
        if phase_orders:
            first = coll.get(phase_orders[0]["key"])
            if first:
                wf_key = first.get("workflow_template_key", "")
                return self.get_phases_for_workflow(wf_key)
        return []

    def get_phase_suggestions(self) -> list[dict]:
        """Aggregate distinct phase names across all workflows with species info."""
        query = (
            f"FOR p IN {col.WORKFLOW_PHASES} "
            f"  LET wf = DOCUMENT({col.WORKFLOW_TEMPLATES}, p.workflow_template_key) "
            f"  COLLECT name = p.name, trigger = p.trigger_phase "
            f"  AGGREGATE dur = MAX(p.duration_days), stress = MAX(p.stress_tolerance), "
            f"    cnt = LENGTH(1), species = UNIQUE(wf.species_compatible) "
            f"  SORT cnt DESC "
            f"  RETURN {{ "
            f"    name: name, duration_days: dur, stress_tolerance: stress, "
            f"    trigger_phase: trigger, usage_count: cnt, "
            f"    used_by_species: FLATTEN(species) "
            f"  }}"
        )
        return list(self._db.aql.execute(query))

    # ── TaskTemplate ──

    def get_task_templates_for_workflow(self, wf_key: WorkflowTemplateKey) -> list[TaskTemplate]:
        query = (
            f"FOR doc IN {col.TASK_TEMPLATES} "
            f"FILTER doc.workflow_template_key == @wf_key "
            f"SORT doc.sequence_order "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"wf_key": wf_key})
        return [TaskTemplate(**self._from_doc(doc)) for doc in cursor]

    def get_task_template_by_key(self, key: str) -> TaskTemplate | None:
        doc = self._db.collection(col.TASK_TEMPLATES).get(key)
        return TaskTemplate(**self._from_doc(doc)) if doc else None

    def get_task_template_or_raise(self, key: str) -> TaskTemplate:
        return self.get_or_raise_by(self.get_task_template_by_key, "TaskTemplate", key)

    def create_task_template(self, template: TaskTemplate) -> TaskTemplate:
        coll = self._db.collection(col.TASK_TEMPLATES)
        data = self._to_doc(template)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        tt = TaskTemplate(**self._from_doc(result["new"]))

        if template.workflow_template_key:
            self.create_edge(
                col.WF_CONTAINS,
                f"{col.WORKFLOW_TEMPLATES}/{template.workflow_template_key}",
                f"{col.TASK_TEMPLATES}/{tt.key}",
            )
        return tt

    def update_task_template(self, key: str, template: TaskTemplate) -> TaskTemplate:
        coll = self._db.collection(col.TASK_TEMPLATES)
        data = self._to_doc(template)
        data["updated_at"] = self._now()
        result = coll.update({"_key": key, **data}, return_new=True)
        return TaskTemplate(**self._from_doc(result["new"]))

    def delete_task_template(self, key: str) -> bool:
        tt_id = f"{col.TASK_TEMPLATES}/{key}"
        # Delete wf_contains edges pointing to this template
        query = f"FOR e IN {col.WF_CONTAINS} FILTER e._to == @tt_id REMOVE e IN {col.WF_CONTAINS}"
        self._db.aql.execute(query, bind_vars={"tt_id": tt_id})
        # Delete instance_of edges from tasks
        query = f"FOR e IN {col.INSTANCE_OF} FILTER e._to == @tt_id REMOVE e IN {col.INSTANCE_OF}"
        self._db.aql.execute(query, bind_vars={"tt_id": tt_id})
        try:
            self._db.collection(col.TASK_TEMPLATES).delete(key)
            return True
        except Exception:
            return False

    # ── Task ──

    def get_all_tasks(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        tenant_key: str | None = None,
    ) -> tuple[list[Task], int]:
        query = f"FOR doc IN {col.TASKS}"
        bind_vars: dict = {}
        filter_clauses: list[str] = []

        if tenant_key:
            bind_vars["tenant_key"] = tenant_key
            filter_clauses.append("doc.tenant_key == @tenant_key")

        if filters:
            for i, (field, value) in enumerate(filters.items()):
                bind_vars[f"val{i}"] = value
                filter_clauses.append(f"doc.{field} == @val{i}")

        if filter_clauses:
            query += " FILTER " + " AND ".join(filter_clauses)

        # Defensive guard: never surface tasks whose plant_instance was removed
        # (soft-delete via ``removed_on``) or no longer exists. Task generators or
        # legacy data created before the removal-cascade can leave such orphans
        # behind; the cascade only deletes a snapshot at removal time, so the queue
        # must re-filter rather than trust that orphans never exist.
        query += (
            f" LET _plant = doc.entity_type == 'plant_instance'"
            f" ? DOCUMENT(CONCAT('{col.PLANT_INSTANCES}/', doc.entity_key))"
            f" : null"
            f" FILTER doc.entity_type != 'plant_instance'"
            f" OR (_plant != null AND _plant.removed_on == null)"
        )

        count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
        count_vars = dict(bind_vars)
        bind_vars["offset"] = offset
        bind_vars["limit"] = limit
        query += " SORT doc.due_date ASC LIMIT @offset, @limit RETURN doc"

        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [Task(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = next(count_cursor, 0)
        return items, total

    def get_task_by_key(self, key: TaskKey) -> Task | None:
        return super().get_by_key(key)

    def get_task_or_raise(self, key: TaskKey) -> Task:
        return super().get_or_raise(key)

    def create_task(self, task: Task) -> Task:
        t = super().create(task)

        # Create has_task edge from entity to task
        entity_collection = None
        entity_key = None
        target_type = None
        if task.entity_key and task.entity_type:
            entity_collection = ENTITY_TYPE_TO_COLLECTION.get(task.entity_type)
            entity_key = task.entity_key
            target_type = task.entity_type

        if entity_collection and entity_key:
            self.create_edge(
                col.HAS_TASK,
                f"{entity_collection}/{entity_key}",
                f"{col.TASKS}/{t.key}",
                data={"target_type": target_type},
            )
        if task.template_key:
            self.create_edge(col.INSTANCE_OF, f"{col.TASKS}/{t.key}", f"{col.TASK_TEMPLATES}/{task.template_key}")
        if task.workflow_execution_key:
            wfe_id = f"{col.WORKFLOW_EXECUTIONS}/{task.workflow_execution_key}"
            self.create_edge(col.WF_GENERATED, wfe_id, f"{col.TASKS}/{t.key}")

        return t

    def find_task_by_external_ref(self, *, tenant_key: str, source: str, external_ref: str) -> Task | None:
        """Tenant+source-scoped FreeStyle idempotency lookup (#1082 AC-3).

        Returns the newest task whose ``(tenant_key, source, external_ref)`` match
        the arguments, or ``None`` when none exists. This is THE single FreeStyle
        dedup predicate, mirroring :meth:`find_open_care_task`'s discipline:

        * The predicate is anchored on ``tenant_key`` **and** ``source`` in the DB,
          so a producer scoped to tenant A can never discover, read or collide with
          a task in tenant B (the negative test in ``test_freestyle_idempotency``),
          and two producers sharing an ``external_ref`` string stay in separate
          dedup namespaces by their distinct ``source`` ids — it is never a
          cross-tenant existence oracle (#1082 AC-6).
        * ``tenant_key`` is required and rejected when empty (GHSA-h5wp-r68x-97g8):
          an empty key would match only legacy tenantless rows rather than scan
          across tenants, but the guard keeps the intent explicit and fails closed.
        * A missing ``source`` or ``external_ref`` yields ``None`` — dedup is opt-in
          and only ever within a fully-qualified ``(tenant, source, external_ref)``
          triple, never on a partial key.

        Newest is ``created_at`` descending, so a re-post resolves to the most
        recent task under the reference.
        """
        self._require_tenant_key(tenant_key, "find_task_by_external_ref")
        if not source or not external_ref:
            return None
        query = (
            f"FOR doc IN {col.TASKS} "
            f"FILTER doc.tenant_key == @tenant_key "
            f"FILTER doc.source == @source "
            f"FILTER doc.external_ref == @external_ref "
            f"SORT doc.created_at DESC LIMIT 1 RETURN doc"
        )
        bind_vars = {"tenant_key": tenant_key, "source": source, "external_ref": external_ref}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        doc = next(cursor, None)
        return Task(**self._from_doc(doc)) if doc else None

    def update_task(self, key: TaskKey, task: Task) -> Task:
        return super().update(key, task)

    def delete_task(self, key: TaskKey) -> bool:
        task_id = f"{col.TASKS}/{key}"
        # Cascade-delete comments and audit entries for this task
        self.delete_comments_for_task(key)
        self._delete_audit_entries_for_task(key)
        # Delete outbound edges (instance_of, task_blocks from this task)
        for edge_col in [col.INSTANCE_OF, col.TASK_BLOCKS]:
            self.delete_edges(edge_col, task_id)
        # Delete inbound edges (has_task, wf_generated, task_blocks to this task)
        for edge_col in [col.HAS_TASK, col.WF_GENERATED, col.TASK_BLOCKS]:
            self.delete_edges(edge_col, task_id, direction="inbound")
        return super().delete(key)

    def get_tasks_for_plant(self, plant_key: str, status: str | None = None, *, tenant_key: str) -> list[Task]:
        """A plant's tasks **inside one tenant** (#927).

        This method selected on ``entity_key`` alone while its tenant-aware twin
        :meth:`get_tasks_for_entity` stood directly below it and did the same job
        correctly. ``plant_key`` comes from the URL of
        ``GET /t/{slug}/tasks/plants/{plant_key}``, so a member of tenant A read
        tenant B's task list — names, instructions, due dates, assignees.

        It is now a thin delegate to :meth:`get_tasks_for_entity` rather than a
        second copy of the same AQL: one predicate, one place to get it wrong.
        """
        self._require_tenant_key(tenant_key, "get_tasks_for_plant")
        return self.get_tasks_for_entity("plant_instance", plant_key, tenant_key, status)

    def get_tasks_for_run(self, run_key: str, status: str | None = None, *, tenant_key: str) -> list[Task]:
        """A run's tasks **inside one tenant** (#952).

        This was the last query in this repository still scanning ``tasks`` with
        no tenant predicate at all, sitting directly beside the ones #947
        hardened. Only internally reachable today (through
        ``PlantInstanceService._delete_orphaned_run_tasks``), which is precisely
        why it is worth closing now rather than when an endpoint reaches it:
        ``tenant_key`` is required and keyword-only, so a future caller cannot
        route a forgotten tenant through here.
        """
        self._require_tenant_key(tenant_key, "get_tasks_for_run")
        query = f"FOR doc IN {col.TASKS} FILTER doc.planting_run_key == @run_key AND doc.tenant_key == @tenant_key"
        bind_vars: dict = {"run_key": run_key, "tenant_key": tenant_key}
        if status:
            query += " FILTER doc.status == @status"
            bind_vars["status"] = status
        query += " SORT doc.due_date ASC RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Task(**self._from_doc(doc)) for doc in cursor]

    def get_tasks_for_entity(
        self,
        entity_type: str,
        entity_key: str,
        tenant_key: str,
        status: str | None = None,
    ) -> list[Task]:
        """The single tenant-scoped "tasks of an entity" predicate (#927).

        Both entity keys and tenant keys arrive from request URLs, so the empty
        sentinel is rejected up front: an empty ``tenant_key`` would match only
        legacy tenantless tasks in AQL, but the guard keeps the *intent* explicit
        and stops a caller from routing a forgotten tenant through here.
        """
        self._require_tenant_key(tenant_key, "get_tasks_for_entity")
        query = (
            f"FOR doc IN {col.TASKS} "
            f"FILTER doc.entity_type == @entity_type AND doc.entity_key == @entity_key "
            f"AND doc.tenant_key == @tenant_key"
        )
        bind_vars: dict = {
            "entity_type": entity_type,
            "entity_key": entity_key,
            "tenant_key": tenant_key,
        }
        if status:
            query += " FILTER doc.status == @status"
            bind_vars["status"] = status
        query += " SORT doc.due_date ASC RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Task(**self._from_doc(doc)) for doc in cursor]

    def get_pending_tasks(self, offset: int = 0, limit: int = 50, *, tenant_key: str) -> tuple[list[Task], int]:
        """Pending tasks **of one tenant** (#927, found alongside the five).

        Not one of the reported five: this one needed no foreign key at all.
        ``GET /t/{slug}/tasks/queue`` handed the *whole installation's* pending
        queue to any authenticated member, because the underlying
        :meth:`get_all_tasks` only filters by tenant when it is given one and the
        queue never gave it one.
        """
        self._require_tenant_key(tenant_key, "get_pending_tasks")
        return self.get_all_tasks(offset, limit, {"status": "pending"}, tenant_key)

    def get_overdue_tasks(self, *, tenant_key: str) -> list[Task]:
        """Overdue tasks **of one tenant** (#927, found alongside the five).

        Same shape as :meth:`get_pending_tasks`: ``GET /t/{slug}/tasks/overdue``
        selected on status and due date only, so it listed every tenant's overdue
        work.
        """
        self._require_tenant_key(tenant_key, "get_overdue_tasks")
        now = datetime.now(UTC).isoformat()
        query = (
            f"FOR doc IN {col.TASKS} "
            f"FILTER doc.tenant_key == @tenant_key "
            f"AND doc.status == 'pending' AND doc.due_date != null AND doc.due_date < @now "
            f"SORT doc.due_date ASC RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"now": now, "tenant_key": tenant_key})
        return [Task(**self._from_doc(doc)) for doc in cursor]

    #: Statuses under which a care-reminder task still blocks re-creation.
    _CARE_OPEN_STATUSES = [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]

    def find_open_care_task(
        self,
        entity_key: str,
        reminder_type: ReminderType,
        tenant_key: str,
        *,
        include_completed_today: bool = True,
    ) -> Task | None:
        """Single tenant-scoped care-reminder idempotency lookup (#509).

        Returns the newest care-reminder task that still "satisfies" the reminder
        for ``(tenant_key, entity_key, reminder_type)``, or ``None`` when none
        exists. A task satisfies the reminder while it is still open
        (``PENDING``/``IN_PROGRESS``) or — when ``include_completed_today`` — was
        completed on the current **UTC** day (the recency rule that stops a
        reminder confirmed earlier the same day from re-materializing).

        **Clock: UTC, on both sides of the comparison.** ``completed_at`` is
        always stamped with ``datetime.now(UTC)`` and persisted as an ISO string,
        so ``LEFT(doc.completed_at, 10)`` is a *UTC* calendar date. The ``@today``
        bind var is therefore derived from ``datetime.now(UTC).date()`` — never
        from ``date.today()``, which is the *local server* date. The two agree
        only on a UTC host; anywhere else they diverge for part of the day and the
        recency rule silently evaluates the wrong day, either failing to suppress
        a duplicate or suppressing a legitimate reminder depending on the offset
        direction (#772). Same UTC convention as the care notification producers
        in ``app.tasks.notification_tasks``. Pinned by
        ``test_find_open_care_task_repo.py::test_recency_rule_uses_utc_not_local_date``.

        This is THE single care-task dedup predicate: the service creation paths
        (:meth:`CareReminderService._ensure_care_task`,
        :meth:`CareReminderService.ensure_next_watering_task`), the dashboard
        auto-complete (:meth:`CareReminderService._complete_pending_care_task`)
        and the daily ``generate_due_care_reminders`` Celery producer all route
        through it, so no path can drift. Crucially the filter is scoped by
        ``tenant_key`` in the DB, so a care task in another tenant can never
        match — closing the tenant-blind gap the old
        ``find_by_field("entity_key", …)`` scans left open (#509).

        The reminder type is matched via the task-name suffix (``"— {value}"``)
        because it is not yet a first-class ``Task`` field (audit P5); newest is
        ``due_date`` then ``created_at`` descending, so ties keep the latest task.
        """
        name_suffix = f"— {reminder_type.value}"
        query = """
        FOR doc IN @@col
            FILTER doc.tenant_key == @tenant_key
            FILTER doc.entity_key == @entity_key
            FILTER doc.category == @care_category
            FILTER doc.name != null
            FILTER RIGHT(doc.name, LENGTH(@name_suffix)) == @name_suffix
            FILTER doc.status IN @open_statuses
                OR (@include_completed_today
                    AND doc.status == @completed_status
                    AND doc.completed_at != null
                    AND LEFT(doc.completed_at, 10) >= @today)
            SORT doc.due_date DESC, doc.created_at DESC
            LIMIT 1
            RETURN doc
        """
        bind_vars = {
            "@col": self._collection_name,
            "tenant_key": tenant_key,
            "entity_key": entity_key,
            "care_category": TaskCategory.CARE_REMINDER.value,
            "name_suffix": name_suffix,
            "open_statuses": self._CARE_OPEN_STATUSES,
            "completed_status": TaskStatus.COMPLETED.value,
            "include_completed_today": include_completed_today,
            # UTC, matching the UTC ``completed_at`` this is compared against.
            # ``date.today()`` (local server date) would drift by a day (#772).
            "today": datetime.now(UTC).date().isoformat(),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        doc = next(cursor, None)
        return Task(**self._from_doc(doc)) if doc is not None else None

    def get_blocking_tasks(self, task_key: TaskKey) -> list[dict]:
        task_id = f"{col.TASKS}/{task_key}"
        query = f"""
        FOR e IN {col.TASK_BLOCKS}
            FILTER e._to == @task_id
            FOR t IN {col.TASKS}
                FILTER t._key == PARSE_IDENTIFIER(e._from).key
                FILTER t.status NOT IN ['completed', 'skipped']
                RETURN {{key: t._key, name: t.name, status: t.status}}
        """
        cursor = self._db.aql.execute(query, bind_vars={"task_id": task_id})
        return list(cursor)

    # ── WorkflowExecution ──

    def create_workflow_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        coll = self._db.collection(col.WORKFLOW_EXECUTIONS)
        data = self._to_doc(execution)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        if not data.get("started_at"):
            data["started_at"] = now
        result = coll.insert(data, return_new=True)
        we = WorkflowExecution(**self._from_doc(result["new"]))

        # Create wf_executing edge from entity to execution
        entity_collection = None
        entity_key = None
        target_type = None
        if execution.entity_key and execution.entity_type:
            entity_collection = ENTITY_TYPE_TO_COLLECTION.get(execution.entity_type)
            entity_key = execution.entity_key
            target_type = execution.entity_type

        if entity_collection and entity_key:
            wfe_id = f"{col.WORKFLOW_EXECUTIONS}/{we.key}"
            self.create_edge(
                col.WF_EXECUTING,
                f"{entity_collection}/{entity_key}",
                wfe_id,
                data={"target_type": target_type},
            )
        return we

    def get_workflow_execution_by_key(self, key: WorkflowExecutionKey) -> WorkflowExecution | None:
        coll = self._db.collection(col.WORKFLOW_EXECUTIONS)
        doc = coll.get(key)
        return WorkflowExecution(**self._from_doc(doc)) if doc else None

    def get_workflow_execution_or_raise(self, key: WorkflowExecutionKey) -> WorkflowExecution:
        return self.get_or_raise_by(self.get_workflow_execution_by_key, "WorkflowExecution", key)

    def update_workflow_execution(self, key: WorkflowExecutionKey, execution: WorkflowExecution) -> WorkflowExecution:
        coll = self._db.collection(col.WORKFLOW_EXECUTIONS)
        data = self._to_doc(execution)
        data["updated_at"] = self._now()
        data["_key"] = key
        result = coll.update(data, return_new=True)
        return WorkflowExecution(**self._from_doc(result["new"]))

    # ── Comments ──

    def create_comment(self, comment: TaskComment) -> TaskComment:
        coll = self._db.collection(col.TASK_COMMENTS)
        data = self._to_doc(comment)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        tc = TaskComment(**self._from_doc(result["new"]))

        self.create_edge(
            col.TASK_HAS_COMMENT,
            f"{col.TASKS}/{comment.task_key}",
            f"{col.TASK_COMMENTS}/{tc.key}",
        )
        return tc

    def get_comments_for_task(self, task_key: str, *, tenant_key: str) -> list[TaskComment]:
        """A task's comments **inside one tenant** (#927).

        ``TaskComment`` carries no ``tenant_key`` of its own, so the predicate is
        taken from the parent task: a comment belongs to whatever tenant its task
        belongs to. That is a genuine data-access-layer filter — no schema change,
        no migration — and it means the tenant scope no longer depends on the
        caller having verified the task first. It had (``TaskService.list_comments``
        loads the task before asking), which is why this was not exploitable; it
        was one careless new caller away from being so.
        """
        self._require_tenant_key(tenant_key, "get_comments_for_task")
        # The ``LET`` sits inside the ``FOR`` because AQL has no top-level
        # ``FILTER``; it is loop-invariant, so the optimiser hoists it out
        # (``move-calculations-up``) and the parent document is read once.
        query = f"""
        FOR doc IN {col.TASK_COMMENTS}
          FILTER doc.task_key == @task_key
          LET task = DOCUMENT(CONCAT(@task_collection, "/", @task_key))
          FILTER task != null AND task.tenant_key == @tenant_key
          SORT doc.created_at ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "task_collection": col.TASKS,
                "task_key": task_key,
                "tenant_key": tenant_key,
            },
        )
        return [TaskComment(**self._from_doc(doc)) for doc in cursor]

    def get_comment_by_key(self, key: str) -> TaskComment | None:
        doc = self._db.collection(col.TASK_COMMENTS).get(key)
        return TaskComment(**self._from_doc(doc)) if doc else None

    def get_comment_or_raise(self, key: str) -> TaskComment:
        return self.get_or_raise_by(self.get_comment_by_key, "TaskComment", key)

    def update_comment(self, key: str, comment: TaskComment) -> TaskComment:
        coll = self._db.collection(col.TASK_COMMENTS)
        data = self._to_doc(comment)
        data["updated_at"] = self._now()
        result = coll.update({"_key": key, **data}, return_new=True)
        return TaskComment(**self._from_doc(result["new"]))

    def delete_comment(self, key: str) -> bool:
        comment_id = f"{col.TASK_COMMENTS}/{key}"
        # Delete task_has_comment edges pointing to this comment
        query = f"FOR e IN {col.TASK_HAS_COMMENT} FILTER e._to == @comment_id REMOVE e IN {col.TASK_HAS_COMMENT}"
        self._db.aql.execute(query, bind_vars={"comment_id": comment_id})
        try:
            self._db.collection(col.TASK_COMMENTS).delete(key)
            return True
        except Exception:
            return False

    def delete_comments_for_task(self, task_key: str) -> int:
        task_id = f"{col.TASKS}/{task_key}"
        # Delete edges from task to comments
        query = f"FOR e IN {col.TASK_HAS_COMMENT} FILTER e._from == @task_id REMOVE e IN {col.TASK_HAS_COMMENT}"
        self._db.aql.execute(query, bind_vars={"task_id": task_id})
        # Delete comment documents
        count_query = (
            f"FOR doc IN {col.TASK_COMMENTS} "
            f"FILTER doc.task_key == @task_key "
            f"COLLECT WITH COUNT INTO total "
            f"RETURN total"
        )
        count_cursor = self._db.aql.execute(count_query, bind_vars={"task_key": task_key})
        count = next(count_cursor, 0)
        delete_query = (
            f"FOR doc IN {col.TASK_COMMENTS} FILTER doc.task_key == @task_key REMOVE doc IN {col.TASK_COMMENTS}"
        )
        self._db.aql.execute(delete_query, bind_vars={"task_key": task_key})
        return count

    # ── Audit ──

    def create_audit_entry(self, entry: TaskAuditEntry) -> TaskAuditEntry:
        coll = self._db.collection(col.TASK_AUDIT_ENTRIES)
        data = self._to_doc(entry)
        if not data.get("changed_at"):
            data["changed_at"] = self._now()
        result = coll.insert(data, return_new=True)
        ae = TaskAuditEntry(**self._from_doc(result["new"]))

        self.create_edge(
            col.TASK_HAS_AUDIT,
            f"{col.TASKS}/{entry.task_key}",
            f"{col.TASK_AUDIT_ENTRIES}/{ae.key}",
        )
        return ae

    def get_audit_entries_for_task(self, task_key: str) -> list[TaskAuditEntry]:
        query = (
            f"FOR doc IN {col.TASK_AUDIT_ENTRIES} FILTER doc.task_key == @task_key SORT doc.changed_at DESC RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"task_key": task_key})
        return [TaskAuditEntry(**self._from_doc(doc)) for doc in cursor]

    def _delete_audit_entries_for_task(self, task_key: str) -> None:
        """Internal helper to cascade-delete audit entries for a task."""
        task_id = f"{col.TASKS}/{task_key}"
        query = f"FOR e IN {col.TASK_HAS_AUDIT} FILTER e._from == @task_id REMOVE e IN {col.TASK_HAS_AUDIT}"
        self._db.aql.execute(query, bind_vars={"task_id": task_id})
        delete_query = (
            f"FOR doc IN {col.TASK_AUDIT_ENTRIES} "
            f"FILTER doc.task_key == @task_key "
            f"REMOVE doc IN {col.TASK_AUDIT_ENTRIES}"
        )
        self._db.aql.execute(delete_query, bind_vars={"task_key": task_key})

    # ── Dormant ──

    def get_dormant_tasks_for_phase(self, plant_key: str, phase_name: str) -> list[Task]:
        query = (
            f"FOR t IN {col.TASKS} "
            f"FILTER t.status == 'dormant' "
            f"AND t.entity_type == 'plant_instance' AND t.entity_key == @plant_key "
            f"AND (t.trigger_phase_override == @phase "
            f"OR (t.trigger_phase_override == null AND t.trigger_phase == @phase)) "
            f"RETURN t"
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={"plant_key": plant_key, "phase": phase_name},
        )
        return [Task(**self._from_doc(doc)) for doc in cursor]

    # ── Activity edge ──

    def create_task_activity_edge(self, task_key: str, activity_key: str) -> None:
        self.create_edge(
            col.TASK_USES_ACTIVITY,
            f"{col.TASKS}/{task_key}",
            f"{col.ACTIVITIES}/{activity_key}",
        )

    # ── Auto-generated workflow lookup ──

    def get_auto_generated_workflow_for_species(
        self,
        species_key: str,
        tenant_key: str = "",
    ) -> WorkflowTemplate | None:
        """Return the caller's generated activity plan for a species (#1003).

        A generated plan is a **hybrid** row, and both halves have to be served
        or the feature breaks in one direction or the other:

        * The plan the generator persists is **global** — ``tenant_key == ""``,
          ``is_system == False`` — and is the shared template every tenant reads
          until they have edited it.
        * A tenant that *has* edited it owns a private copy carrying their own
          ``tenant_key``, and from then on that copy is their plan.

        So the predicate is a union, never an equality. ``doc.tenant_key ==
        @tenant_key`` on its own would match **nothing at all** for every tenant
        that has not forked yet — every generated plan in an existing
        installation is global — and would pass every cross-tenant negative test
        by killing the feature outright. That is PR #324's regression class, and
        PR #999 records that it was live on exactly this query.

        The ``SORT`` is what makes the union unambiguous: the caller's own row
        sorts ahead of the shared one, so a tenant with a copy gets the copy and
        everybody else gets the template. ``created_at DESC`` then breaks ties
        within a tier, as before.

        ``tenant_key == ""`` (no tenant in play — an internal caller rather than
        a route) collapses the union onto the global rows and reproduces the
        pre-#1003 answer exactly.
        """
        # Shared hybrid-catalog union (SEC-B4 / #324). The SORT tie-break below
        # is what disambiguates the union — the caller's own row sorts ahead of
        # the shared one — and MUST be preserved.
        predicate, predicate_vars = tenant_union_predicate(tenant_key)
        query = (
            f"FOR doc IN {col.WORKFLOW_TEMPLATES} "
            f"FILTER doc.auto_generated == true AND doc.species_key == @species_key "
            f"FILTER {predicate} "
            f"SORT (doc.tenant_key == @tenant_key ? 0 : 1) ASC, doc.created_at DESC "
            f"LIMIT 1 "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={"species_key": species_key, **predicate_vars},
        )
        doc = next(cursor, None)
        return WorkflowTemplate(**self._from_doc(doc)) if doc else None

    def delete_task_templates_for_workflow(self, wf_key: str) -> int:
        wf_id = f"{col.WORKFLOW_TEMPLATES}/{wf_key}"
        # Delete wf_contains edges
        query = f"FOR e IN {col.WF_CONTAINS} FILTER e._from == @wf_id REMOVE e IN {col.WF_CONTAINS}"
        self._db.aql.execute(query, bind_vars={"wf_id": wf_id})
        # Count and delete task templates
        count_query = (
            f"FOR doc IN {col.TASK_TEMPLATES} "
            f"FILTER doc.workflow_template_key == @key "
            f"COLLECT WITH COUNT INTO total "
            f"RETURN total"
        )
        count_cursor = self._db.aql.execute(count_query, bind_vars={"key": wf_key})
        count = next(count_cursor, 0)
        delete_query = (
            f"FOR doc IN {col.TASK_TEMPLATES} "
            f"FILTER doc.workflow_template_key == @key "
            f"REMOVE doc IN {col.TASK_TEMPLATES}"
        )
        self._db.aql.execute(delete_query, bind_vars={"key": wf_key})
        return count

    def get_workflow_usage_stats(self, wf_keys: list[str]) -> dict[str, dict]:
        """Return species_name and assigned plant count per workflow key."""
        if not wf_keys:
            return {}
        query = f"""
        FOR wf_key IN @wf_keys
          LET wf = DOCUMENT(CONCAT('{col.WORKFLOW_TEMPLATES}/', wf_key))
          LET sp = wf.species_key != null
            ? DOCUMENT(CONCAT('{col.SPECIES}/', wf.species_key))
            : null
          LET species_name = sp != null
            ? (LENGTH(sp.common_names) > 0 ? sp.common_names[0] : sp.scientific_name)
            : ''
          LET tt_keys = (
            FOR tt IN {col.TASK_TEMPLATES}
              FILTER tt.workflow_template_key == wf_key
              RETURN tt._key
          )
          LET entity_keys = (
            FOR t IN {col.TASKS}
              FILTER t.template_key IN tt_keys AND t.entity_key != null
              RETURN DISTINCT t.entity_key
          )
          RETURN {{ wf_key: wf_key, species_name: species_name, entity_count: LENGTH(entity_keys) }}
        """
        cursor = self._db.aql.execute(query, bind_vars={"wf_keys": wf_keys})
        result: dict[str, dict] = {}
        for row in cursor:
            result[row["wf_key"]] = {"species_name": row["species_name"], "entity_count": row["entity_count"]}
        return result

    def get_executions_for_template(self, template_key: str) -> list[dict]:
        """Return workflow executions for a template with enriched entity info."""
        query = f"""
        FOR we IN {col.WORKFLOW_EXECUTIONS}
          FILTER we.workflow_template_key == @template_key
          LET etype = we.entity_type
          LET ekey = we.entity_key
          LET plant = etype == 'plant_instance'
            ? DOCUMENT(CONCAT('{col.PLANT_INSTANCES}/', ekey))
            : null
          LET loc = etype == 'location'
            ? DOCUMENT(CONCAT('{col.LOCATIONS}/', ekey))
            : null
          LET tank = etype == 'tank'
            ? DOCUMENT(CONCAT('{col.TANKS}/', ekey))
            : null
          LET run_doc = etype == 'planting_run'
            ? DOCUMENT(CONCAT('{col.PLANTING_RUNS}/', ekey))
            : null
          LET sp = plant != null AND plant.species_key != null
            ? DOCUMENT(CONCAT('{col.SPECIES}/', plant.species_key))
            : null
          LET species_name = sp != null
            ? (LENGTH(sp.common_names) > 0 ? sp.common_names[0] : sp.scientific_name)
            : ''
          LET entity_name = plant != null
            ? (plant.plant_name || plant.instance_id || ekey)
            : (loc != null ? loc.name : (tank != null ? tank.name : (run_doc != null ? run_doc.name : ekey)))
          SORT we.created_at DESC
          RETURN {{
            key: we._key,
            entity_key: ekey,
            entity_type: etype,
            entity_name: entity_name,
            plant_removed: plant != null AND plant.removed_on != null,
            species_name: species_name,
            completion_percentage: we.completion_percentage,
            on_schedule: we.on_schedule,
            started_at: we.started_at,
            completed_at: we.completed_at
          }}
        """
        cursor = self._db.aql.execute(query, bind_vars={"template_key": template_key})
        return list(cursor)

    # ── Dashboard counts (REQ-009) ──

    #: A task is "open" for the dashboard while it is still actionable, i.e. it
    #: has neither been completed nor skipped/failed/dormant.
    _OPEN_STATUSES = [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]

    #: Care reminders are persisted as ``category == "care_reminder"`` tasks and
    #: already own the dedicated ``care_reminders_due`` tile (REQ-009 §1.4, fed by
    #: ``ArangoCareReminderRepository.count_due_on``). The generic task surfaces
    #: therefore EXCLUDE this category so a care reminder due today/overdue is
    #: counted in exactly one tile instead of being double-counted (#508).
    _CARE_CATEGORY = TaskCategory.CARE_REMINDER.value

    #: Shared orphan guard mirroring ``get_all_tasks``: a plant_instance task
    #: whose plant was soft-removed (``removed_on``) or no longer exists must not
    #: surface — otherwise the dashboard counts drift from the user-facing queue.
    _ORPHAN_GUARD = (
        " LET _plant = doc.entity_type == 'plant_instance'"
        " ? DOCUMENT(CONCAT(@plant_col, '/', doc.entity_key))"
        " : null"
        " FILTER doc.entity_type != 'plant_instance'"
        " OR (_plant != null AND _plant.removed_on == null)"
    )

    def count_open_due_on(self, tenant_key: str, today: date) -> int:
        """Count open tasks of ``tenant_key`` whose due date falls on ``today``.

        ``due_date`` is a datetime persisted as an ISO string; the first ten
        characters are its calendar date, compared against ``today`` so the count
        is timezone-offset agnostic. Orphaned plant tasks are excluded to match
        the user-facing queue (``get_all_tasks``). Care-reminder tasks are
        excluded so they are counted only in ``care_reminders_due`` (#508).
        """
        self._require_tenant_key(tenant_key, "count_open_due_on")
        query = f"""
        RETURN LENGTH(
          FOR doc IN @@col
            FILTER doc.tenant_key == @tenant_key
            FILTER doc.category != @care_category
            FILTER doc.status IN @open_statuses
            FILTER doc.due_date != null
            FILTER LEFT(doc.due_date, 10) == @today
            {self._ORPHAN_GUARD}
            RETURN 1
        )
        """
        bind_vars = {
            "@col": self._collection_name,
            "tenant_key": tenant_key,
            "care_category": self._CARE_CATEGORY,
            "open_statuses": self._OPEN_STATUSES,
            "today": today.isoformat(),
            "plant_col": col.PLANT_INSTANCES,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

    def count_overdue(self, tenant_key: str, today: date) -> int:
        """Count open tasks of ``tenant_key`` whose due date is before ``today``.

        Care-reminder tasks are excluded so an overdue care reminder is counted
        only in ``care_reminders_due`` and never double-counted here (#508).
        """
        self._require_tenant_key(tenant_key, "count_overdue")
        query = f"""
        RETURN LENGTH(
          FOR doc IN @@col
            FILTER doc.tenant_key == @tenant_key
            FILTER doc.category != @care_category
            FILTER doc.status IN @open_statuses
            FILTER doc.due_date != null
            FILTER LEFT(doc.due_date, 10) < @today
            {self._ORPHAN_GUARD}
            RETURN 1
        )
        """
        bind_vars = {
            "@col": self._collection_name,
            "tenant_key": tenant_key,
            "care_category": self._CARE_CATEGORY,
            "open_statuses": self._OPEN_STATUSES,
            "today": today.isoformat(),
            "plant_col": col.PLANT_INSTANCES,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

    def list_upcoming(
        self,
        tenant_key: str,
        today: date,
        window_end: date,
        limit: int,
    ) -> list[dict]:
        """List open tasks of ``tenant_key`` due within ``[today, window_end]``.

        Sorted by due date ascending and capped at ``limit``. Returns raw
        document dicts; the dashboard service consumes them directly.
        Care-reminder tasks are excluded — they surface in the dedicated care
        section, so the generic upcoming-tasks list stays disjoint (#508).
        """
        self._require_tenant_key(tenant_key, "list_upcoming")
        query = f"""
        FOR doc IN @@col
          FILTER doc.tenant_key == @tenant_key
          FILTER doc.category != @care_category
          FILTER doc.status IN @open_statuses
          FILTER doc.due_date != null
          FILTER LEFT(doc.due_date, 10) >= @today
            AND LEFT(doc.due_date, 10) <= @window_end
          {self._ORPHAN_GUARD}
          SORT doc.due_date ASC
          LIMIT @limit
          RETURN doc
        """
        bind_vars = {
            "@col": self._collection_name,
            "tenant_key": tenant_key,
            "care_category": self._CARE_CATEGORY,
            "open_statuses": self._OPEN_STATUSES,
            "today": today.isoformat(),
            "window_end": window_end.isoformat(),
            "limit": limit,
            "plant_col": col.PLANT_INSTANCES,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._from_doc(doc) for doc in cursor]

    # ── Batch ──

    def batch_get_tasks(self, task_keys: list[str]) -> list[Task]:
        if not task_keys:
            return []
        query = f"FOR t IN {col.TASKS} FILTER t._key IN @keys RETURN t"
        cursor = self._db.aql.execute(query, bind_vars={"keys": task_keys})
        return [Task(**self._from_doc(doc)) for doc in cursor]
