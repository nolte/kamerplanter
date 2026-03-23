"""Celery tasks for the notification system (REQ-030).

These tasks bridge the synchronous Celery worker context with the
async NotificationService by using asyncio.run() for async operations.
"""

import asyncio

import structlog

from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="notifications.dispatch_due_care")
def dispatch_due_care_notifications() -> dict:
    """Dispatch notifications for due care tasks.

    Runs daily at 06:05 UTC (5 min after REQ-022 care reminder generation).

    Logic:
    1. Load all today-due tasks with category='care_reminder'
    2. Group by user_key
    3. Send batched notifications via NotificationService
    """
    from datetime import UTC, date, datetime

    from app.common.dependencies import get_notification_service, get_task_repo
    from app.common.enums import TaskCategory, TaskStatus

    task_repo = get_task_repo()
    service = get_notification_service()

    today = date.today()
    today_start = datetime(today.year, today.month, today.day, tzinfo=UTC)
    today_end = datetime(
        today.year, today.month, today.day, 23, 59, 59, tzinfo=UTC
    )

    # Find all pending/in-progress care reminder tasks due today
    all_tasks, _ = task_repo.get_all(offset=0, limit=500)
    due_tasks: list[dict] = []

    for task_doc in all_tasks:
        if task_doc.get("category") != TaskCategory.CARE_REMINDER.value:
            continue
        if task_doc.get("status") not in (
            TaskStatus.PENDING.value,
            TaskStatus.IN_PROGRESS.value,
        ):
            continue

        due_date_raw = task_doc.get("due_date")
        if due_date_raw is None:
            continue

        # Parse due_date (stored as ISO string)
        if isinstance(due_date_raw, str):
            try:
                due_dt = datetime.fromisoformat(due_date_raw)
            except ValueError:
                continue
        elif isinstance(due_date_raw, datetime):
            due_dt = due_date_raw
        else:
            continue

        if due_dt < today_start or due_dt > today_end:
            continue

        # Determine urgency from priority
        priority = task_doc.get("priority", "medium")
        urgency = "due_today"
        if priority == "high":
            urgency = "overdue"

        # Extract reminder type from task name (format: "PlantName -- type")
        task_name = task_doc.get("name", "")
        reminder_type = "watering"
        if " \u2014 " in task_name:
            reminder_type = task_name.split(" \u2014 ")[-1].strip()

        plant_name = task_name.split(" \u2014 ")[0].strip() if " \u2014 " in task_name else task_name

        due_tasks.append(
            {
                "user_key": task_doc.get("assigned_to", ""),
                "plant_key": task_doc.get("plant_key", ""),
                "plant_name": plant_name,
                "reminder_type": reminder_type,
                "urgency": urgency,
                "due_date": due_dt.isoformat(),
                "tenant_key": task_doc.get("tenant_key", ""),
            }
        )

    if not due_tasks:
        logger.info("notification_dispatch_no_due_tasks")
        return {"status": "empty", "tasks_found": 0, "tenants_processed": 0}

    # Group by tenant_key for batched sending
    by_tenant: dict[str, list[dict]] = {}
    for task_dict in due_tasks:
        tenant_key = task_dict.get("tenant_key", "")
        if tenant_key not in by_tenant:
            by_tenant[tenant_key] = []
        by_tenant[tenant_key].append(task_dict)

    total_users_notified = 0
    total_sent = 0

    for tenant_key, tenant_tasks in by_tenant.items():
        if not tenant_key:
            continue

        try:
            result = asyncio.run(
                service.send_care_notifications(tenant_key, tenant_tasks)
            )
            total_users_notified += result.get("users_notified", 0)
            total_sent += result.get("total_sent", 0)
        except Exception:
            logger.exception(
                "notification_dispatch_tenant_failed",
                tenant_key=tenant_key,
            )

    logger.info(
        "notification_dispatch_complete",
        tasks_found=len(due_tasks),
        tenants_processed=len(by_tenant),
        users_notified=total_users_notified,
        total_sent=total_sent,
    )

    return {
        "status": "complete",
        "tasks_found": len(due_tasks),
        "tenants_processed": len(by_tenant),
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
    tenants, _ = tenant_repo.get_all(offset=0, limit=1000)

    total_escalated = 0
    tenants_processed = 0

    for tenant_doc in tenants:
        tenant_key = tenant_doc.get("_key", tenant_doc.get("key", ""))
        if not tenant_key:
            continue

        try:
            result = asyncio.run(
                service._engine.escalate_overdue(tenant_key)
            )
            escalated = result.get("escalated", 0)
            total_escalated += escalated
            tenants_processed += 1

            if escalated > 0:
                logger.info(
                    "notification_escalation_tenant",
                    tenant_key=tenant_key,
                    escalated=escalated,
                )
        except Exception:
            logger.exception(
                "notification_escalation_tenant_failed",
                tenant_key=tenant_key,
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
    """
    from datetime import UTC, date, datetime

    from app.common.dependencies import get_notification_service, get_task_repo
    from app.common.enums import TaskCategory, TaskStatus
    from app.domain.models.notification import NotificationUrgency

    service = get_notification_service()
    task_repo = get_task_repo()

    today = date.today()
    today_start = datetime(today.year, today.month, today.day, tzinfo=UTC)

    # Find all due/overdue care tasks
    all_tasks, _ = task_repo.get_all(offset=0, limit=1000)
    care_tasks: list[dict] = []

    for task_doc in all_tasks:
        if task_doc.get("category") != TaskCategory.CARE_REMINDER.value:
            continue
        if task_doc.get("status") not in (
            TaskStatus.PENDING.value,
            TaskStatus.IN_PROGRESS.value,
        ):
            continue
        care_tasks.append(task_doc)

    # Group by user (assigned_to)
    by_user: dict[str, list[dict]] = {}
    for task_doc in care_tasks:
        user_key = task_doc.get("assigned_to", "")
        if not user_key:
            continue
        if user_key not in by_user:
            by_user[user_key] = []
        by_user[user_key].append(task_doc)

    summaries_sent = 0

    for user_key, user_tasks in by_user.items():
        # Check if user has daily_summary enabled
        prefs = service.get_preferences(user_key)
        if not prefs.daily_summary.enabled:
            continue

        tenant_key = ""
        if user_tasks:
            tenant_key = user_tasks[0].get("tenant_key", "")

        # Categorize tasks
        overdue = []
        due_today = []

        for task_doc in user_tasks:
            due_date_raw = task_doc.get("due_date")
            if due_date_raw is None:
                continue

            if isinstance(due_date_raw, str):
                try:
                    due_dt = datetime.fromisoformat(due_date_raw)
                except ValueError:
                    continue
            elif isinstance(due_date_raw, datetime):
                due_dt = due_date_raw
            else:
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
            parts.append(
                f"Due today ({len(due_today)}): {', '.join(due_today[:5])}"
            )

        if not parts:
            continue

        body = "\n".join(parts)
        title = f"Daily care summary: {len(overdue) + len(due_today)} tasks"

        urgency = (
            NotificationUrgency.HIGH if overdue else NotificationUrgency.NORMAL
        )

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
                    group_key=f"daily_summary:{user_key}:{today.isoformat()}",
                )
            )
            summaries_sent += 1
        except Exception:
            logger.exception(
                "daily_summary_send_failed",
                user_key=user_key,
            )

    logger.info(
        "daily_summary_complete",
        users_with_tasks=len(by_user),
        summaries_sent=summaries_sent,
    )

    return {
        "status": "complete",
        "users_with_tasks": len(by_user),
        "summaries_sent": summaries_sent,
    }


@celery_app.task(name="notifications.send_email_digests")
def send_email_digests() -> dict:
    """Send collected email digests.

    Runs daily at 07:00 UTC. Collects all notifications queued for
    email digest delivery and sends them as a single email per user.
    """
    # Email digest delivery requires a dedicated query method on
    # the preference repository (list_users_with_digest_enabled)
    # which will be added when the EmailNotificationChannel is
    # fully implemented. For now, this task is a no-op placeholder.
    digests_sent = 0

    logger.info(
        "email_digests_complete",
        digests_sent=digests_sent,
    )

    return {
        "status": "complete",
        "digests_sent": digests_sent,
    }
