from celery import Celery
from celery.schedules import crontab

from app.config.settings import settings
from app.data_access.external.registration import register_external_adapters

# The Celery worker/beat boot via ``celery -A app.tasks`` and never import
# ``app.main``, so without this call the adapter registries would be empty in the
# worker process — the REQ-046 weather fetch (and any other registry-resolving
# task) would fail with ``*_source_unknown`` and write nothing. Register at
# module import time so every task has the adapters available.
register_external_adapters()

celery_app = Celery(
    "kamerplanter",
    broker=settings.redis_url,
)
celery_app.conf.update(
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.auth_tasks",
        "app.tasks.care_tasks",
        "app.tasks.dormancy_checks",
        "app.tasks.enrichment_tasks",
        "app.tasks.frost_forecast_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.pest_dataset_tasks",
        "app.tasks.pest_image_tasks",
        "app.tasks.phase_transitions",
        "app.tasks.reference_contribution_tasks",
        "app.tasks.reference_image_tasks",
        "app.tasks.retention_tasks",
        "app.tasks.season_tasks",
        "app.tasks.sensor_ingestion_tasks",
        "app.tasks.storage_tasks",
        "app.tasks.tank_maintenance_tasks",
        "app.tasks.tenant_tasks",
        "app.tasks.vernalization_updates",
        "app.tasks.watering_tasks",
        "app.tasks.weather_tasks",
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
        # REQ-031 KI-Assistent retention (§4.6)
        "ai-cleanup-conversations-daily": {
            "task": "ai.cleanup_expired_conversations",
            "schedule": crontab(hour=2, minute=30),
        },
        "ai-cleanup-audit-log-daily": {
            "task": "ai.cleanup_expired_audit_log",
            "schedule": crontab(hour=2, minute=35),
        },
        "ai-knowledge-service-ingest-weekly": {
            "task": "ai.knowledge_service_ingest",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),
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
        # NFR-011 Retention pipeline
        "retention-execute-erasures-daily": {
            "task": "retention.execute_scheduled_erasures",
            "schedule": crontab(hour=4, minute=0),  # 04:00 UTC daily
        },
        "retention-expire-email-changes-hourly": {
            "task": "retention.expire_email_change_requests",
            "schedule": crontab(minute=15),  # every hour at :15
        },
        "retention-expire-data-exports-hourly": {
            "task": "retention.expire_data_exports",
            "schedule": crontab(minute=20),  # every hour at :20
        },
        "retention-redispatch-stale-exports-hourly": {
            "task": "retention.redispatch_stale_pending_exports",
            "schedule": crontab(minute=25),  # every hour at :25
        },
    },
)

# TimescaleDB sensor ingestion (conditional)
if settings.timescaledb_enabled:
    celery_app.conf.beat_schedule["sensor-ingest-ha-5min"] = {
        "task": "app.tasks.sensor_ingestion_tasks.ingest_ha_readings",
        "schedule": 300,
    }

# REQ-046 daily weather fetch (conditional kill-switch)
if settings.weather_enabled:
    celery_app.conf.beat_schedule["weather-fetch-daily"] = {
        "task": "app.tasks.weather_tasks.fetch_weather_forecasts",
        "schedule": crontab(hour=6, minute=0),
    }
    # Issue #392 — proactive frost early-warning, evaluated shortly after the
    # daily fetch has persisted fresh forecasts.
    celery_app.conf.beat_schedule["frost-forecast-evaluate-daily"] = {
        "task": "app.tasks.frost_forecast_tasks.evaluate_forecast_frost_warnings",
        "schedule": crontab(hour=6, minute=10),
    }

# REQ-047 daily season-state evaluation (after the weather fetch; kill-switch)
if settings.season_state_eval_enabled:
    celery_app.conf.beat_schedule["season-evaluate-states-daily"] = {
        "task": "app.tasks.season_tasks.evaluate_season_states",
        "schedule": crontab(hour=6, minute=30),
    }
