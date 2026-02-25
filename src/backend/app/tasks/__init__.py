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
    },
)
