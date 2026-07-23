"""Synchronous source→notification feedback loop (REQ-030 §4.2/§5.2, Issue #742).

REQ-030 closes the delivery gap of REQ-006 (tasks) and REQ-022 (care reminders).
This service closes the *reverse* gap: when the **source** of a notification
changes — a task is moved, reassigned, completed or deleted, or a care reminder's
cycle is edited or confirmed — the associated in-app notification must follow
synchronously (updated, marked done or removed), without creating duplicates or
leaving orphans.

Design (why here / why sync):

* **In-app only, repository-scoped.** The in-app Notification Center (§5.2) reads
  persisted notification rows. Every propagation step is a pure repository write
  (locate by ``group_key`` → update / mark done / delete / create), so it runs
  **synchronously** inside the existing sync service layer. It deliberately does
  **not** re-dispatch through the async :class:`NotificationEngine`: channel
  delivery (Home Assistant / e-mail / Web Push) stays on the periodic/engine path,
  so a mere update or reschedule never fires a duplicate push.
* **No layering cycle.** This service depends only on
  :class:`INotificationRepository`. ``TaskService`` / ``CareReminderService``
  depend on *this* service — an acyclic Service→Service edge.
* **Idempotent via ``group_key``.** Each source owns exactly one stable
  ``group_key`` (``task.due:{task_key}`` / ``task.assigned:{task_key}`` /
  ``care.{reminder_type}:{plant_key}``); a repeated update converges on a single
  row (any stray duplicate is pruned).
* **Fail-closed tenant isolation.** Every operation requires a non-empty
  ``tenant_key`` and binds it into the lookup; an empty tenant is a no-op, never a
  cross-tenant scan (SEC-B4).
* **Resilient.** A propagation failure is logged and swallowed by the callers so a
  notification hiccup can never abort the underlying task/care mutation (NFR-007).
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from app.common.enums import ReminderType
from app.domain.interfaces.notification_repository import INotificationRepository
from app.domain.models.notification import (
    Notification,
    NotificationAction,
    NotificationStatus,
    NotificationUrgency,
)
from app.domain.models.task import Task

logger = structlog.get_logger()

#: Task statuses for which a live "due" notification should exist.
_ACTIONABLE_TASK_STATUSES: frozenset[str] = frozenset({"pending", "in_progress"})


def _task_due_group_key(task_key: str) -> str:
    return f"task.due:{task_key}"


def _task_assigned_group_key(task_key: str) -> str:
    return f"task.assigned:{task_key}"


def _care_group_key(reminder_type: ReminderType | str, plant_key: str) -> str:
    value = reminder_type.value if isinstance(reminder_type, ReminderType) else str(reminder_type)
    return f"care.{value}:{plant_key}"


def _due_label(due_date: datetime | None) -> str:
    """Render a task/care due date as an ISO date, or an empty string when unset."""
    if due_date is None:
        return ""
    return due_date.date().isoformat()


class NotificationPropagationService:
    """Keep in-app notifications in sync with their source task/care reminder."""

    def __init__(self, notification_repo: INotificationRepository) -> None:
        self._repo = notification_repo

    # ── Task hooks ────────────────────────────────────────────────────

    def sync_task_due_notification(self, task: Task) -> None:
        """Upsert the task's single ``task.due`` in-app notification (idempotent).

        A ``pending``/``in_progress`` task with a due date and an assignee gets
        exactly one live notification reflecting its current title and due date; any
        other state (completed, unassigned, date-less) marks the existing
        notification done instead. Care-reminder tasks are skipped here — they are
        driven by the care path (:meth:`sync_care_notification`) so the two never
        double-notify.
        """
        if task.category == "care_reminder":
            return
        if not task.tenant_key or not task.key:
            return

        group_key = _task_due_group_key(task.key)
        try:
            existing = self._repo.list_by_group_key(group_key, task.tenant_key)
        except Exception:
            logger.warning("notification_propagation_lookup_failed", group_key=group_key)
            return

        actionable = (
            task.status in _ACTIONABLE_TASK_STATUSES and task.due_date is not None and bool(task.assigned_to_user_key)
        )
        if not actionable:
            self._mark_group_done(existing)
            return

        title = task.name
        body = self._task_due_body(task)
        data = {
            "task_key": task.key,
            "entity_key": task.entity_key,
            "entity_type": task.entity_type,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "action_url": f"/aufgaben/tasks/{task.key}",
        }

        if existing:
            self._update_single(
                existing,
                user_key=task.assigned_to_user_key or "",
                title=title,
                body=body,
                data=data,
            )
            return

        self._create(
            Notification(
                tenant_key=task.tenant_key,
                user_key=task.assigned_to_user_key or "",
                notification_type="task.due",
                title=title,
                body=body,
                urgency=NotificationUrgency.NORMAL,
                data=data,
                group_key=group_key,
                status=NotificationStatus.DELIVERED,
            )
        )

    def on_task_reassigned(self, task: Task, *, previous_user_key: str | None) -> None:
        """Move the task's notifications to the newly assigned member.

        The previous assignee's ``task.due``/``task.assigned`` notifications are
        removed (they no longer own the task) and a fresh assignment notification is
        delivered to the new assignee, alongside a re-synced ``task.due`` entry.
        A no-op reassignment (same user) does nothing.
        """
        new_user_key = task.assigned_to_user_key or ""
        if (previous_user_key or "") == new_user_key:
            return
        if not task.tenant_key or not task.key:
            return

        # Drop the previous assignee's notifications for this task (no orphan).
        for gk in (_task_due_group_key(task.key), _task_assigned_group_key(task.key)):
            self._delete_group_for_user(gk, task.tenant_key, previous_user_key)

        if not new_user_key:
            return

        # Deliver an assignment notification to the new member.
        data = {
            "task_key": task.key,
            "entity_key": task.entity_key,
            "entity_type": task.entity_type,
            "action_url": f"/aufgaben/tasks/{task.key}",
        }
        assigned_group = _task_assigned_group_key(task.key)
        existing_assigned = self._safe_lookup(assigned_group, task.tenant_key)
        assignment = Notification(
            tenant_key=task.tenant_key,
            user_key=new_user_key,
            notification_type="task.assigned",
            title=task.name,
            body=self._task_assigned_body(task),
            urgency=NotificationUrgency.NORMAL,
            data=data,
            group_key=assigned_group,
            status=NotificationStatus.DELIVERED,
        )
        if existing_assigned:
            self._update_single(
                existing_assigned,
                user_key=new_user_key,
                title=assignment.title,
                body=assignment.body,
                data=data,
                reset_read=True,
            )
        else:
            self._create(assignment)

        # Keep the due notification in sync for the new owner.
        self.sync_task_due_notification(task)

    def on_task_completed(self, task: Task) -> None:
        """Mark the task's open due/assignment notifications done (badge drops).

        Covers both a generic task (its ``task.due``/``task.assigned`` notifications)
        and a care-reminder task completed via the task queue — the latter's
        per-plant ``care.<type>`` notification is closed too, so completing the
        watering task and confirming the reminder on the dashboard behave alike.
        """
        if not task.tenant_key or not task.key:
            return
        for gk in (_task_due_group_key(task.key), _task_assigned_group_key(task.key)):
            self._mark_group_done(self._safe_lookup(gk, task.tenant_key))

        if task.category == "care_reminder" and task.entity_key:
            reminder_type = self._reminder_type_from_task_name(task.name)
            if reminder_type is not None:
                self.on_care_confirmed(
                    tenant_key=task.tenant_key,
                    plant_key=task.entity_key,
                    reminder_type=reminder_type,
                )

    @staticmethod
    def _reminder_type_from_task_name(task_name: str) -> ReminderType | None:
        """Recover the care ``ReminderType`` from a ``"<plant> — <type>"`` task name.

        Mirrors the em-dash suffix convention of :func:`build_care_reminder_task`
        so a care task completed via the queue maps back to its per-plant care
        notification.
        """
        if not task_name:
            return None
        for reminder_type in ReminderType:
            if task_name.endswith(f"— {reminder_type.value}"):
                return reminder_type
        return None

    def on_task_deleted(self, task: Task) -> None:
        """Remove the deleted task's orphaned notifications (no dead action_url)."""
        if not task.tenant_key or not task.key:
            return
        for gk in (_task_due_group_key(task.key), _task_assigned_group_key(task.key)):
            for notif in self._safe_lookup(gk, task.tenant_key):
                self._delete(notif)

    # ── Care hooks ────────────────────────────────────────────────────

    def sync_care_notification(
        self,
        *,
        tenant_key: str,
        user_key: str,
        plant_key: str,
        plant_label: str,
        reminder_type: ReminderType,
        due_date: datetime | None,
        task_key: str | None = None,
    ) -> None:
        """Upsert the plant's single ``care.<type>`` notification with the new due.

        Guarantees exactly one entry per ``(plant, reminder type)``: a repeated
        interval edit updates the same row (any stray duplicate is pruned) rather
        than piling up a second ``care.watering`` note for the same period
        (TC-REQ-030-066). The notification carries an actionable ``confirm`` button
        driving the §4.2 one-tap callback.
        """
        if not tenant_key or not plant_key:
            return

        group_key = _care_group_key(reminder_type, plant_key)
        data = {
            "plant_key": plant_key,
            "reminder_type": reminder_type.value,
            "task_key": task_key,
            "due_date": due_date.isoformat() if due_date else None,
            "action_url": "/pflege",
        }
        title = plant_label or plant_key
        body = self._care_body(plant_label or plant_key, reminder_type, due_date)
        actions = [self._confirm_action()]

        existing = self._safe_lookup(group_key, tenant_key)
        if existing:
            self._update_single(
                existing,
                user_key=user_key,
                title=title,
                body=body,
                data=data,
                actions=actions,
            )
            return

        self._create(
            Notification(
                tenant_key=tenant_key,
                user_key=user_key,
                notification_type=f"care.{reminder_type.value}",
                title=title,
                body=body,
                urgency=NotificationUrgency.NORMAL,
                data=data,
                actions=actions,
                group_key=group_key,
                status=NotificationStatus.DELIVERED,
            )
        )

    def on_care_confirmed(
        self,
        *,
        tenant_key: str,
        plant_key: str,
        reminder_type: ReminderType,
    ) -> None:
        """Mark the plant's ``care.<type>`` notification done after confirmation."""
        if not tenant_key or not plant_key:
            return
        group_key = _care_group_key(reminder_type, plant_key)
        self._mark_group_done(self._safe_lookup(group_key, tenant_key))

    # ── Internal helpers ──────────────────────────────────────────────

    @staticmethod
    def _confirm_action() -> NotificationAction:
        """The actionable ``confirm`` button that drives the §4.2 callback."""
        return NotificationAction(action_id="confirm", title="Done", uri="/pflege")

    @staticmethod
    def _task_due_body(task: Task) -> str:
        due = _due_label(task.due_date)
        return f"Task due{f' on {due}' if due else ''}: {task.name}"

    @staticmethod
    def _task_assigned_body(task: Task) -> str:
        due = _due_label(task.due_date)
        return f"You were assigned{f' (due {due})' if due else ''}: {task.name}"

    @staticmethod
    def _care_body(plant_label: str, reminder_type: ReminderType, due_date: datetime | None) -> str:
        due = _due_label(due_date)
        return f"{reminder_type.value} due{f' on {due}' if due else ''}: {plant_label}"

    def _safe_lookup(self, group_key: str, tenant_key: str) -> list[Notification]:
        try:
            return self._repo.list_by_group_key(group_key, tenant_key)
        except Exception:
            logger.warning("notification_propagation_lookup_failed", group_key=group_key)
            return []

    def _create(self, notification: Notification) -> None:
        try:
            self._repo.create(notification)
        except Exception:
            logger.warning(
                "notification_propagation_create_failed",
                group_key=notification.group_key,
            )

    def _delete(self, notification: Notification) -> None:
        if not notification.key:
            return
        try:
            self._repo.delete(notification.key)
        except Exception:
            logger.warning("notification_propagation_delete_failed", key=notification.key)

    def _delete_group_for_user(self, group_key: str, tenant_key: str, user_key: str | None) -> None:
        for notif in self._safe_lookup(group_key, tenant_key):
            if user_key is None or notif.user_key == user_key:
                self._delete(notif)

    def _update_single(
        self,
        existing: list[Notification],
        *,
        user_key: str,
        title: str,
        body: str,
        data: dict,
        actions: list[NotificationAction] | None = None,
        reset_read: bool = False,
    ) -> None:
        """Update the newest matching notification and prune any duplicates.

        Keeping only the newest row (the list is sorted newest-first) enforces the
        "exactly one" idempotency guarantee even if a stray duplicate slipped in.
        """
        if not existing:
            return
        keep, *duplicates = existing
        for dup in duplicates:
            self._delete(dup)
        if not keep.key:
            return

        keep.user_key = user_key or keep.user_key
        keep.title = title
        keep.body = body
        keep.data = data
        if actions is not None:
            keep.actions = actions
        if reset_read:
            keep.read_at = None
            keep.acted_at = None
        try:
            self._repo.update(keep.key, keep)
        except Exception:
            logger.warning("notification_propagation_update_failed", key=keep.key)

    def _mark_group_done(self, notifications: list[Notification]) -> None:
        """Stamp ``read_at`` + ``acted_at`` so the group drops out of the badge."""
        now = datetime.now(UTC)
        for notif in notifications:
            if not notif.key:
                continue
            if notif.read_at is not None and notif.acted_at is not None:
                continue
            try:
                self._repo.mark_read(notif.key, now)
                self._repo.mark_acted(notif.key, now)
            except Exception:
                logger.warning("notification_propagation_mark_done_failed", key=notif.key)
