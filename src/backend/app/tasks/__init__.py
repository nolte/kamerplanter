from celery import Celery

from app.config.settings import settings

celery_app = Celery("kamerplanter", broker=settings.redis_url)
celery_app.conf.update(
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
        # REQ-024 Tenant tasks
        "tenant-cleanup-invitations-daily": {
            "task": "app.tasks.tenant_tasks.cleanup_expired_invitations",
            "schedule": 86400,
        },
    },
)
