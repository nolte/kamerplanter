"""REQ-044 WP-3 — Celery task for cold-start pest dataset acquisition.

Operator-triggered (not on a beat schedule). Populates the few-shot prototype
index in the inference service from CC0/CC-BY GBIF images. Requires the
inference service to be reachable; uses GBIF's public occurrence search (no
credentials).
"""

import structlog

from app.common.dependencies import get_pest_dataset_acquisition_service
from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task  # type: ignore[misc]
def acquire_pest_dataset_task() -> dict:
    """Acquire and index few-shot prototypes for all pest taxonomy classes."""
    service = get_pest_dataset_acquisition_service()
    result = service.acquire_all()
    summary = {k: v for k, v in result.items() if k != "manifest"}
    logger.info("acquire_pest_dataset_done", classes=summary["classes"], accepted=summary["total_accepted"])
    return summary
