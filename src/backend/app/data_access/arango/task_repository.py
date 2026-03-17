from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.common.types import TaskKey, WorkflowExecutionKey, WorkflowTemplateKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.models.task import Task, TaskAuditEntry, TaskComment, TaskTemplate, WorkflowExecution, WorkflowTemplate


class ArangoTaskRepository(ITaskRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.TASKS)

    # ── WorkflowTemplate ──

    def get_all_workflow_templates(
        self,
        offset: int = 0,
        limit: int = 50,
        species_key: str | None = None,
        tenant_key: str | None = None,
    ) -> tuple[list[WorkflowTemplate], int]:
        filter_parts: list[str] = []
        bind_vars: dict = {}
        if species_key:
            filter_parts.append("doc.species_key == @species_key")
            bind_vars["species_key"] = species_key
        if tenant_key:
            filter_parts.append("doc.tenant_key == @tenant_key")
            bind_vars["tenant_key"] = tenant_key
        filt = ("FILTER " + " AND ".join(filter_parts)) if filter_parts else ""
        query = f"FOR doc IN {col.WORKFLOW_TEMPLATES} {filt} SORT doc.name LIMIT {offset}, {limit} RETURN doc"
        count_query = f"FOR doc IN {col.WORKFLOW_TEMPLATES} {filt} COLLECT WITH COUNT INTO total RETURN total"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [WorkflowTemplate(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars=bind_vars)
        total = next(count_cursor, 0)
        return items, total

    def get_workflow_template_by_key(self, key: WorkflowTemplateKey) -> WorkflowTemplate | None:
        coll = self._db.collection(col.WORKFLOW_TEMPLATES)
        doc = coll.get(key)
        return WorkflowTemplate(**self._from_doc(doc)) if doc else None

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

        count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
        query += f" SORT doc.due_date ASC LIMIT {offset}, {limit} RETURN doc"

        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [Task(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars=bind_vars)
        total = next(count_cursor, 0)
        return items, total

    def get_task_by_key(self, key: TaskKey) -> Task | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Task(**doc) if doc else None

    def create_task(self, task: Task) -> Task:
        doc = BaseArangoRepository.create(self, task)
        t = Task(**doc)

        if task.plant_key:
            self.create_edge(col.HAS_TASK, f"{col.PLANT_INSTANCES}/{task.plant_key}", f"{col.TASKS}/{t.key}")
        if task.template_key:
            self.create_edge(col.INSTANCE_OF, f"{col.TASKS}/{t.key}", f"{col.TASK_TEMPLATES}/{task.template_key}")
        if task.workflow_execution_key:
            wfe_id = f"{col.WORKFLOW_EXECUTIONS}/{task.workflow_execution_key}"
            self.create_edge(col.WF_GENERATED, wfe_id, f"{col.TASKS}/{t.key}")

        return t

    def update_task(self, key: TaskKey, task: Task) -> Task:
        doc = BaseArangoRepository.update(self, key, task)
        return Task(**doc)

    def delete_task(self, key: TaskKey) -> bool:
        task_id = f"{col.TASKS}/{key}"
        # Cascade-delete comments and audit entries for this task
        self.delete_comments_for_task(key)
        self._delete_audit_entries_for_task(key)
        # Delete outbound edges (instance_of, task_blocks from this task)
        for edge_col in [col.INSTANCE_OF, col.TASK_BLOCKS]:
            query = f"FOR e IN {edge_col} FILTER e._from == @task_id REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"task_id": task_id})
        # Delete inbound edges (has_task, wf_generated, task_blocks to this task)
        for edge_col in [col.HAS_TASK, col.WF_GENERATED, col.TASK_BLOCKS]:
            query = f"FOR e IN {edge_col} FILTER e._to == @task_id REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"task_id": task_id})
        return BaseArangoRepository.delete(self, key)

    def get_tasks_for_plant(self, plant_key: str, status: str | None = None) -> list[Task]:
        query = f"FOR doc IN {col.TASKS} FILTER doc.plant_key == @plant_key"
        bind_vars: dict = {"plant_key": plant_key}
        if status:
            query += " FILTER doc.status == @status"
            bind_vars["status"] = status
        query += " SORT doc.due_date ASC RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Task(**self._from_doc(doc)) for doc in cursor]

    def get_pending_tasks(self, offset: int = 0, limit: int = 50) -> tuple[list[Task], int]:
        return self.get_all_tasks(offset, limit, {"status": "pending"})

    def get_overdue_tasks(self) -> list[Task]:
        now = datetime.now(UTC).isoformat()
        query = (
            f"FOR doc IN {col.TASKS} "
            f"FILTER doc.status == 'pending' AND doc.due_date != null AND doc.due_date < @now "
            f"SORT doc.due_date ASC RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"now": now})
        return [Task(**self._from_doc(doc)) for doc in cursor]

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

        plant_id = f"{col.PLANT_INSTANCES}/{execution.plant_key}"
        wfe_id = f"{col.WORKFLOW_EXECUTIONS}/{we.key}"
        self.create_edge(col.WF_EXECUTING, plant_id, wfe_id)
        return we

    def get_workflow_execution_by_key(self, key: WorkflowExecutionKey) -> WorkflowExecution | None:
        coll = self._db.collection(col.WORKFLOW_EXECUTIONS)
        doc = coll.get(key)
        return WorkflowExecution(**self._from_doc(doc)) if doc else None

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

    def get_comments_for_task(self, task_key: str) -> list[TaskComment]:
        query = f"FOR doc IN {col.TASK_COMMENTS} FILTER doc.task_key == @task_key SORT doc.created_at ASC RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"task_key": task_key})
        return [TaskComment(**self._from_doc(doc)) for doc in cursor]

    def get_comment_by_key(self, key: str) -> TaskComment | None:
        doc = self._db.collection(col.TASK_COMMENTS).get(key)
        return TaskComment(**self._from_doc(doc)) if doc else None

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
            f"AND t.plant_key == @plant_key "
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

    def get_auto_generated_workflow_for_species(self, species_key: str) -> WorkflowTemplate | None:
        query = (
            f"FOR doc IN {col.WORKFLOW_TEMPLATES} "
            f"FILTER doc.auto_generated == true AND doc.species_key == @species_key "
            f"SORT doc.created_at DESC "
            f"LIMIT 1 "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"species_key": species_key})
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
          LET plant_keys = (
            FOR t IN {col.TASKS}
              FILTER t.template_key IN tt_keys AND t.plant_key != null
              RETURN DISTINCT t.plant_key
          )
          RETURN {{ wf_key: wf_key, species_name: species_name, plant_count: LENGTH(plant_keys) }}
        """
        cursor = self._db.aql.execute(query, bind_vars={"wf_keys": wf_keys})
        result: dict[str, dict] = {}
        for row in cursor:
            result[row["wf_key"]] = {"species_name": row["species_name"], "plant_count": row["plant_count"]}
        return result

    # ── Batch ──

    def batch_get_tasks(self, task_keys: list[str]) -> list[Task]:
        if not task_keys:
            return []
        query = f"FOR t IN {col.TASKS} FILTER t._key IN @keys RETURN t"
        cursor = self._db.aql.execute(query, bind_vars={"keys": task_keys})
        return [Task(**self._from_doc(doc)) for doc in cursor]
