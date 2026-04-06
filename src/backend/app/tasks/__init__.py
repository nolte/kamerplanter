from celery import Celery
from celery.schedules import crontab

from app.config.settings import settings

celery_app = Celery(
    "kamerplanter",
    broker=settings.redis_url,
)
celery_app.conf.update(
    include=[
        "app.tasks.auth_tasks",
        "app.tasks.care_tasks",
        "app.tasks.dormancy_checks",
        "app.tasks.enrichment_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.phase_transitions",
        "app.tasks.sensor_ingestion_tasks",
        "app.tasks.tank_maintenance_tasks",
        "app.tasks.tenant_tasks",
        "app.tasks.vernalization_updates",
        "app.tasks.watering_tasks",
    ],
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "enrichment-incremental-daily": {
            "task": "app.tasks.enrichment_tasks.sync_all_sources_task",
            "schedule": 86400,
            "kwargs": {"full_sync": False},
        },
        "enrichment-full-weekly": {
            "task": "app.tasks.enrichment_tasks.sync_all_sources_task",
            "schedule": 604800,
            "kwargs": {"full_sync": True},
        },
        # REQ-023 Auth tasks
        "auth-cleanup-tokens-hourly": {
            "task": "app.tasks.auth_tasks.cleanup_expired_tokens",
            "schedule": 3600,
        },
        "auth-cleanup-unverified-daily": {
            "task": "app.tasks.auth_tasks.cleanup_unverified_accounts",
            "schedule": 86400,
        },
        "auth-anonymize-ips-daily": {
            "task": "app.tasks.auth_tasks.anonymize_old_ips",
            "schedule": 86400,
        },
        "auth-rotate-oidc-discovery": {
            "task": "app.tasks.auth_tasks.rotate_oidc_discovery",
            "schedule": 21600,  # 6 hours
        },
        # REQ-024 Tenant tasks
        "tenant-cleanup-invitations-daily": {
            "task": "app.tasks.tenant_tasks.cleanup_expired_invitations",
            "schedule": 86400,
        },
        # REQ-022 Care Reminder tasks
        "care-generate-reminders-daily": {
            "task": "app.tasks.care_tasks.generate_due_care_reminders",
            "schedule": 86400,
        },
        # Watering schedule tasks
        "watering-generate-tasks-daily": {
            "task": "app.tasks.watering_tasks.generate_watering_tasks",
            "schedule": 86400,
        },
        # REQ-014 Tank maintenance tasks
        "tank-maintenance-tasks-daily": {
            "task": "app.tasks.tank_maintenance_tasks.generate_tank_maintenance_tasks",
            "schedule": 86400,
        },
        "tank-sync-states-from-ha-5min": {
            "task": "app.tasks.tank_maintenance_tasks.sync_tank_states_from_ha",
            "schedule": 300,
        },
        "tank-check-alerts-hourly": {
            "task": "app.tasks.tank_maintenance_tasks.check_tank_alerts",
            "schedule": 3600,
        },
        # REQ-004-A Runoff trend analysis
        "runoff-trend-check-daily": {
            "task": "app.tasks.tank_maintenance_tasks.check_runoff_trends",
            "schedule": 86400,
        },
        # REQ-030 Notification tasks
        "notifications-dispatch-care-daily": {
            "task": "notifications.dispatch_due_care",
            "schedule": crontab(hour=6, minute=5),
        },
        "notifications-escalate-overdue": {
            "task": "notifications.escalate_overdue",
            "schedule": crontab(hour=12, minute=0),
        },
        "notifications-daily-summary": {
            "task": "notifications.send_daily_summary",
            "schedule": crontab(hour=6, minute=30),
        },
        "notifications-email-digests": {
            "task": "notifications.send_email_digests",
            "schedule": crontab(hour=7, minute=0),
        },
    },
)

# TimescaleDB sensor ingestion (conditional)
if settings.timescaledb_enabled:
    celery_app.conf.beat_schedule["sensor-ingest-ha-5min"] = {
        "task": "app.tasks.sensor_ingestion_tasks.ingest_ha_readings",
        "schedule": 300,
    }
