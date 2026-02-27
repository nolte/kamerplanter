from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.common.types import TaskKey, WorkflowExecutionKey, WorkflowTemplateKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.models.task import Task, TaskTemplate, WorkflowExecution, WorkflowTemplate


class ArangoTaskRepository(ITaskRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.TASKS)

    # ── WorkflowTemplate ──

    def get_all_workflow_templates(self, offset: int = 0, limit: int = 50) -> tuple[list[WorkflowTemplate], int]:
        query = f"FOR doc IN {col.WORKFLOW_TEMPLATES} SORT doc.name LIMIT {offset}, {limit} RETURN doc"
        count_query = f"FOR doc IN {col.WORKFLOW_TEMPLATES} COLLECT WITH COUNT INTO total RETURN total"
        cursor = self._db.aql.execute(query)
        items = [WorkflowTemplate(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query)
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

    # ── Task ──

    def get_all_tasks(self, offset: int = 0, limit: int = 50, filters: dict | None = None) -> tuple[list[Task], int]:
        query = f"FOR doc IN {col.TASKS}"
        bind_vars: dict = {}

        if filters:
            filter_clauses = []
            for i, (field, value) in enumerate(filters.items()):
                bind_vars[f"val{i}"] = value
                filter_clauses.append(f"doc.{field} == @val{i}")
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
