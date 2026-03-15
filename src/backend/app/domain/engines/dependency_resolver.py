from collections import deque
from datetime import UTC, datetime

# Priority scores (lower = higher priority)
PRIORITY_SCORES = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


class DependencyResolver:
    """Pure logic for task dependency resolution -- no DB access."""

    def get_ready_tasks(
        self,
        tasks: list[dict],
        dependencies: list[dict],
    ) -> list[dict]:
        """Get tasks that are unblocked and ready to execute.

        Args:
            tasks: List of dicts with keys:
                - key: str
                - status: str
                - priority: str
                - due_date: datetime | str | None
            dependencies: List of dicts with keys:
                - from_key: str (blocking task)
                - to_key: str (blocked task)

        Returns:
            List of unblocked pending tasks sorted by priority and urgency.
        """
        completed_keys = {t["key"] for t in tasks if t.get("status") in ("completed", "skipped")}

        blocked_by: dict[str, set[str]] = {}
        for dep in dependencies:
            to_key = dep["to_key"]
            from_key = dep["from_key"]
            if from_key not in completed_keys:
                blocked_by.setdefault(to_key, set()).add(from_key)

        ready = []
        now = datetime.now(UTC)
        for t in tasks:
            if t.get("status") != "pending":
                continue
            if t["key"] in blocked_by:
                continue

            due = t.get("due_date")
            if due and isinstance(due, str):
                due = datetime.fromisoformat(due)
            if due and due.tzinfo is None:
                due = due.replace(tzinfo=UTC)

            urgency = 0.0
            if due:
                delta = (due - now).total_seconds() / 86400
                urgency = -delta  # Negative = more urgent (overdue has high urgency)

            priority_score = PRIORITY_SCORES.get(t.get("priority", "medium"), 2)
            ready.append({**t, "_sort_priority": priority_score, "_sort_urgency": urgency})

        ready.sort(key=lambda x: (x["_sort_priority"], -x["_sort_urgency"]))
        return [{k: v for k, v in item.items() if not k.startswith("_")} for item in ready]

    def reschedule_dependents(
        self,
        completed_key: str,
        completed_at: datetime,
        original_due: datetime | None,
        all_tasks: list[dict],
        dependencies: list[dict],
    ) -> list[dict]:
        """Reschedule dependent tasks when a task completes late.

        Args:
            completed_key: Key of the completed task.
            completed_at: When the task was actually completed.
            original_due: When the task was originally due.
            all_tasks: All tasks in the workflow.
            dependencies: All dependency edges.

        Returns:
            List of dicts with task_key and new_due_date for tasks
            that need rescheduling.
        """
        if original_due is None or completed_at <= original_due:
            return []

        delay = completed_at - original_due

        # BFS to find all downstream dependents
        adjacency: dict[str, list[str]] = {}
        for dep in dependencies:
            adjacency.setdefault(dep["from_key"], []).append(dep["to_key"])

        task_map = {t["key"]: t for t in all_tasks}
        visited: set[str] = set()
        queue: deque[str] = deque()

        for downstream in adjacency.get(completed_key, []):
            queue.append(downstream)

        rescheduled = []
        while queue:
            task_key = queue.popleft()
            if task_key in visited:
                continue
            visited.add(task_key)

            task = task_map.get(task_key)
            if not task or task.get("status") in ("completed", "skipped"):
                continue

            due = task.get("due_date")
            if due:
                if isinstance(due, str):
                    due = datetime.fromisoformat(due)
                new_due = due + delay
                rescheduled.append(
                    {
                        "task_key": task_key,
                        "new_due_date": new_due.isoformat(),
                    }
                )

            for downstream in adjacency.get(task_key, []):
                queue.append(downstream)

        return rescheduled
