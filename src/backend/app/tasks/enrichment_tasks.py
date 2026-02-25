import structlog

from app.common.dependencies import get_enrichment_engine
from app.common.enums import SyncTrigger
from app.domain.services.adapter_registry import AdapterRegistry
from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[misc]
def sync_source_task(self, source_key: str, full_sync: bool = False) -> dict:  # type: ignore[no-untyped-def]
    """Sync a single external source."""
    try:
        adapter = AdapterRegistry.get(source_key)
        engine = get_enrichment_engine()
        run = engine.sync_source(adapter, full_sync=full_sync, triggered_by=SyncTrigger.CELERY_SCHEDULE)
        return {
            "source_key": source_key,
            "status": run.status.value,
            "total_processed": run.total_processed,
            "new_mappings": run.new_mappings,
            "updated_mappings": run.updated_mappings,
        }
    except Exception as exc:
        logger.error("sync_source_task_failed", source_key=source_key, error=str(exc))
        raise self.retry(exc=exc) from exc


@celery_app.task  # type: ignore[misc]
def sync_all_sources_task(full_sync: bool = False) -> dict:  # type: ignore[no-untyped-def]
    """Dispatch sync tasks for all registered sources."""
    keys = AdapterRegistry.all_keys()
    for key in keys:
        sync_source_task.delay(key, full_sync=full_sync)
    return {"dispatched": keys}
