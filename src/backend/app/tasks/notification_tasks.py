"""Celery tasks for the notification system (REQ-030).

These tasks bridge the synchronous Celery worker context with the
async NotificationService by using asyncio.run() for async operations.
"""

import asyncio
from datetime import UTC, date, datetime

import structlog

from app.common.datetimes import today_utc
from app.common.enums import TenantStatus
from app.common.log_privacy import log_subject, log_tenant
from app.data_access.arango.base_repository import get_all_pages
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.tasks import celery_app
from app.tasks.tenant_gate import ActiveTenants

logger = structlog.get_logger()


def _as_doc(row) -> dict:
    """One repository row as the plain dict the loops below read with ``.get``.

    ``BaseArangoRepository.get_all`` returns the bound domain model (``Task``,
    ``Tenant``), not a dict, so ``row.get(...)`` raised ``AttributeError`` on the
    first row of a real collection (the unit doubles returned dicts and never saw
    it). The care-reminder fields the loops use are mapped from the model's own
    names: the assignee is ``assigned_to_user_key`` and the plant is the task's
    ``entity_key`` when it targets a ``plant_instance``.
    """
    if isinstance(row, dict):
        return row
    doc = row.model_dump(mode="json", by_alias=True)
    doc.setdefault("assigned_to", doc.get("assigned_to_user_key") or "")
    if doc.get("entity_type") == "plant_instance":
        doc.setdefault("plant_key", doc.get("entity_key") or "")
    return doc


class _ActiveMembers:
    """Whether ``(user, tenant)`` is an active membership, asked once per pair for one beat run (#2114).

    The care-reminder beat reads the recipient off the task (``assigned_to``). An assignment can outlive the
    membership - data from before the assignee was cleared on leaving, a failed clear, a deactivated member -
    and the beat then notified an ex-member of a tenant's plants and due dates. The stored membership of
    ``(user, tenant)`` decides, the question ``frost_forecast_tasks`` already asks. A task with no assignee
    asks for the pair ``("", tenant)`` and is refused like any non-member.

    #2166: the tenant must be active as well. A ``suspended``, ``pending_deletion`` or ``orphaned`` tenant keeps
    its memberships active on purpose (a cancelled deletion restores them unchanged) but resolves for nobody, and
    the beat notified its members of plants and due dates in a tenant they cannot open.
    """

    def __init__(self, membership_repo: IMembershipRepository, tenant_repo: ITenantRepository) -> None:
        self._repo = membership_repo
        self._tenant_is_active = ActiveTenants(tenant_repo)
        self._answers: dict[tuple[str, str], bool] = {}

    def __call__(self, user_key: str, tenant_key: str) -> bool:
        pair = (user_key, tenant_key)
        if pair not in self._answers:
            if not (user_key and tenant_key) or not self._tenant_is_active(tenant_key):
                self._answers[pair] = False
            else:
                membership = self._repo.get_by_user_and_tenant(user_key, tenant_key)
                self._answers[pair] = membership is not None and bool(getattr(membership, "is_active", False))
        return self._answers[pair]


def _active_tenant_keys(tenant_repo: ITenantRepository) -> list[str]:
    """Keys of every ``active`` tenant, read page by page (#2012, #2166).

    The care beats work tenant by tenant (MT-032, #2128): a suspended,
    pending-deletion or orphaned tenant resolves for nobody, so there is nothing
    to notify about, and a task row without a tenant was never notified either.
    """
    keys: list[str] = []
    for tenant_doc in (_as_doc(t) for t in get_all_pages(tenant_repo)):
        tenant_key = tenant_doc.get("_key", tenant_doc.get("key", ""))
        if tenant_key and tenant_doc.get("status", TenantStatus.ACTIVE.value) == TenantStatus.ACTIVE.value:
            keys.append(tenant_key)
    return keys


def _parse_due(task_doc: dict) -> datetime | None:
    """The task's due date as an aware UTC-comparable instant, or ``None`` when absent or unreadable."""
    due_date_raw = task_doc.get("due_date")
    if isinstance(due_date_raw, str):
        try:
            due_dt = datetime.fromisoformat(due_date_raw)
        except ValueError:
            return None
    elif isinstance(due_date_raw, datetime):
        due_dt = due_date_raw
    else:
        return None
    if due_dt.tzinfo is None:  # stored without an offset: the beat windows are UTC
        due_dt = due_dt.replace(tzinfo=UTC)
    return due_dt


def _today_window() -> tuple[date, datetime, datetime]:
    """Today's UTC calendar day and its first and last second.

    Work in UTC consistently: the beats are scheduled in UTC and the window
    boundaries carry UTC tzinfo. ``date.today()`` (local timezone) made the
    due-date window drift by a day whenever local time had rolled past midnight
    while UTC had not (e.g. CEST 00:00-02:00).
    """
    today = today_utc()
    start = datetime(today.year, today.month, today.day, tzinfo=UTC)
    end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=UTC)
    return today, start, end


@celery_app.task(name="notifications.dispatch_due_care")
def dispatch_due_care_notifications() -> dict:
    """Dispatch notifications for due care tasks.

    Runs daily at 06:05 UTC (5 min after REQ-022 care reminder generation).

    Logic, tenant by tenant (MT-032, #2128):
    1. Read the tenant's open care reminders due today — selected in AQL
       (:meth:`ITaskRepository.list_open_care_reminders_due`), never the whole
       ``tasks`` collection
    2. Keep the ones whose assignee is an active member (#2114)
    3. Send them as one batch via NotificationService

    The worker holds one tenant's due reminders at a time, so its memory no
    longer grows with the installation's total task count.
    """
    from app.common.dependencies import get_membership_repo, get_notification_service, get_task_repo, get_tenant_repo

    task_repo = get_task_repo()
    tenant_repo = get_tenant_repo()
    service = get_notification_service()
    is_active_member = _ActiveMembers(get_membership_repo(), tenant_repo)
    _today, today_start, today_end = _today_window()

    tasks_found = 0
    tenants_processed = 0
    total_users_notified = 0
    total_sent = 0

    for tenant_key in _active_tenant_keys(tenant_repo):
        rows = task_repo.list_open_care_reminders_due(tenant_key=tenant_key, due_from=today_start, due_until=today_end)
        tenant_tasks: list[dict] = []
        for task_doc in (_as_doc(row) for row in rows):
            due_dt = _parse_due(task_doc)
            # The store selected the window; the instant is re-read here only to report it.
            if due_dt is None or due_dt < today_start or due_dt > today_end:
                continue

            # #2114 — only an active member of the task's tenant is notified of its plants and due dates.
            if not is_active_member(task_doc.get("assigned_to", ""), tenant_key):
                continue

            # Determine urgency from priority
            urgency = "overdue" if task_doc.get("priority", "medium") == "high" else "due_today"

            # Extract reminder type from task name (format: "PlantName -- type")
            task_name = task_doc.get("name", "")
            reminder_type = "watering"
            if " — " in task_name:
                reminder_type = task_name.split(" — ")[-1].strip()
            plant_name = task_name.split(" — ")[0].strip() if " — " in task_name else task_name

            tenant_tasks.append(
                {
                    "user_key": task_doc.get("assigned_to", ""),
                    "plant_key": task_doc.get("plant_key", ""),
                    "plant_name": plant_name,
                    "reminder_type": reminder_type,
                    "urgency": urgency,
                    "due_date": due_dt.isoformat(),
                    "tenant_key": tenant_key,
                }
            )

        if not tenant_tasks:
            continue
        tasks_found += len(tenant_tasks)
        tenants_processed += 1
        try:
            result = asyncio.run(service.send_care_notifications(tenant_key, tenant_tasks))
            total_users_notified += result.get("users_notified", 0)
            total_sent += result.get("total_sent", 0)
        except Exception:
            logger.exception(
                "notification_dispatch_tenant_failed",
                tenant=log_tenant(tenant_key),
            )

    if not tasks_found:
        logger.info("notification_dispatch_no_due_tasks")
        return {"status": "empty", "tasks_found": 0, "tenants_processed": 0}

    logger.info(
        "notification_dispatch_complete",
        tasks_found=tasks_found,
        tenants_processed=tenants_processed,
        users_notified=total_users_notified,
        total_sent=total_sent,
    )

    return {
        "status": "complete",
        "tasks_found": tasks_found,
        "tenants_processed": tenants_processed,
        "users_notified": total_users_notified,
        "total_sent": total_sent,
    }


@celery_app.task(name="notifications.escalate_overdue")
def escalate_overdue_notifications() -> dict:
    """Escalate overdue watering reminders.

    Runs daily at 12:00 UTC. Checks for unacted watering notifications
    and sends escalation notifications with increasing urgency.

    Escalation levels:
    - Day +2: urgency -> HIGH
    - Day +4: urgency -> CRITICAL
    - Day +7: final warning
    """
    from app.common.dependencies import get_notification_service, get_tenant_repo

    service = get_notification_service()
    tenant_repo = get_tenant_repo()

    # Get all tenants
    tenants = [_as_doc(t) for t in get_all_pages(tenant_repo)]

    total_escalated = 0
    tenants_processed = 0

    for tenant_doc in tenants:
        tenant_key = tenant_doc.get("_key", tenant_doc.get("key", ""))
        if not tenant_key:
            continue
        # #2166 — a suspended, pending-deletion or orphaned tenant resolves for nobody: nothing to escalate to.
        if tenant_doc.get("status", TenantStatus.ACTIVE.value) != TenantStatus.ACTIVE.value:
            continue

        try:
            result = asyncio.run(service._engine.escalate_overdue(tenant_key))
            escalated = result.get("escalated", 0)
            total_escalated += escalated
            tenants_processed += 1

            if escalated > 0:
                logger.info(
                    "notification_escalation_tenant",
                    tenant=log_tenant(tenant_key),
                    escalated=escalated,
                )
        except Exception:
            logger.exception(
                "notification_escalation_tenant_failed",
                tenant=log_tenant(tenant_key),
            )

    logger.info(
        "notification_escalation_complete",
        tenants_processed=tenants_processed,
        total_escalated=total_escalated,
    )

    return {
        "status": "complete",
        "tenants_processed": tenants_processed,
        "total_escalated": total_escalated,
    }


@celery_app.task(name="notifications.send_daily_summary")
def send_daily_summary() -> dict:
    """Send daily care summary notification.

    Runs daily at 06:30 UTC. Aggregates today's due tasks, overdue items,
    and weather hints into a single summary notification per user.

    Tenant by tenant (MT-032, #2128): the open care reminders due up to the end
    of today are selected in AQL (:meth:`ITaskRepository.list_open_care_reminders_due`
    without a lower bound, so the overdue ones are included); the worker never
    reads the tenant's other tasks, nor another tenant's while it summarises one.
    """
    from app.common.dependencies import get_membership_repo, get_notification_service, get_task_repo, get_tenant_repo
    from app.domain.models.notification import NotificationUrgency

    service = get_notification_service()
    task_repo = get_task_repo()
    tenant_repo = get_tenant_repo()
    is_active_member = _ActiveMembers(get_membership_repo(), tenant_repo)
    today, today_start, today_end = _today_window()

    users_with_tasks: set[str] = set()
    summaries_sent = 0

    for tenant_key in _active_tenant_keys(tenant_repo):
        rows = task_repo.list_open_care_reminders_due(tenant_key=tenant_key, due_until=today_end)

        # Group by user within this tenant (#2114): one summary per tenant the user is an active member of. It
        # used to group by user alone and file the whole lot under the tenant of the FIRST task document, so a
        # user in two tenants got one notification with both tenants' tasks, under the wrong tenant.
        by_user: dict[str, list[dict]] = {}
        for task_doc in (_as_doc(row) for row in rows):
            user_key = task_doc.get("assigned_to", "")
            if not user_key or not is_active_member(user_key, tenant_key):
                continue
            by_user.setdefault(user_key, []).append(task_doc)

        for user_key, user_tasks in by_user.items():
            users_with_tasks.add(user_key)
            # Check if user has daily_summary enabled
            prefs = service.get_preferences(user_key)
            if not prefs.daily_summary.enabled:
                continue

            # Categorize tasks
            overdue = []
            due_today = []
            for task_doc in user_tasks:
                due_dt = _parse_due(task_doc)
                if due_dt is None:
                    continue
                task_name = task_doc.get("name", "Unknown")
                if due_dt < today_start:
                    overdue.append(task_name)
                else:
                    due_today.append(task_name)

            # Build summary
            parts = []
            if overdue:
                parts.append(f"Overdue ({len(overdue)}): {', '.join(overdue[:5])}")
            if due_today:
                parts.append(f"Due today ({len(due_today)}): {', '.join(due_today[:5])}")

            if not parts:
                continue

            body = "\n".join(parts)
            title = f"Daily care summary: {len(overdue) + len(due_today)} tasks"

            urgency = NotificationUrgency.HIGH if overdue else NotificationUrgency.NORMAL

            try:
                asyncio.run(
                    service.send_notification(
                        user_key=user_key,
                        tenant_key=tenant_key,
                        notification_type="system.daily_summary",
                        title=title,
                        body=body,
                        urgency=urgency,
                        data={
                            "overdue_count": len(overdue),
                            "due_today_count": len(due_today),
                            "action_url": "/pflege",
                        },
                        group_key=f"daily_summary:{user_key}:{tenant_key}:{today.isoformat()}",
                    )
                )
                summaries_sent += 1
            except Exception:
                logger.exception(
                    "daily_summary_send_failed",
                    subject=log_subject(user_key),
                )

    logger.info(
        "daily_summary_complete",
        users_with_tasks=len(users_with_tasks),
        summaries_sent=summaries_sent,
    )

    return {
        "status": "complete",
        "users_with_tasks": len(users_with_tasks),
        "summaries_sent": summaries_sent,
    }


@celery_app.task(  # type: ignore[misc]
    name="notifications.send_email_digests",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
def send_email_digests(self) -> dict:
    """Send the daily email digest (REQ-030).

    Runs daily at 07:00 UTC. For every user who opted in
    (``channels.email.enabled`` + ``channels.email.config.digest``) it
    collects the notifications of the last 24 hours and delivers them as a
    single batch email via the registered ``email`` channel. Failures are
    isolated per user so one bad recipient does not abort the run.
    """
    from datetime import timedelta

    from app.common.dependencies import (
        get_notification_preference_repo,
        get_notification_service,
    )

    preference_repo = get_notification_preference_repo()
    service = get_notification_service()

    since = datetime.now(UTC) - timedelta(hours=24)
    candidates = preference_repo.list_users_with_digest_enabled()

    digests_sent = 0
    digests_empty = 0
    digests_failed = 0
    digests_unconfirmed = 0

    for prefs in candidates:
        user_key = prefs.user_key
        if not user_key:
            continue

        try:
            result = asyncio.run(service.send_email_digest(user_key, since))
        except Exception:
            logger.exception("email_digest_user_failed", subject=log_subject(user_key))
            digests_failed += 1
            continue

        if result["status"] == "sent":
            digests_sent += 1
        elif result["status"] == "empty":
            digests_empty += 1
        elif result["status"] == "no_confirmed_address":
            # Not a delivery failure: the account has no confirmed address (#1885).
            digests_unconfirmed += 1
        else:
            digests_failed += 1

    logger.info(
        "email_digests_complete",
        digests_unconfirmed=digests_unconfirmed,
        candidates=len(candidates),
        digests_sent=digests_sent,
        digests_empty=digests_empty,
        digests_failed=digests_failed,
    )

    return {
        "status": "complete",
        "candidates": len(candidates),
        "digests_sent": digests_sent,
        "digests_empty": digests_empty,
        "digests_failed": digests_failed,
        "digests_unconfirmed": digests_unconfirmed,
    }
