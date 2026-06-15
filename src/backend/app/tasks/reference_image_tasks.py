"""REQ-029-A §4.2 — Celery tasks for reference-image acquisition.

These tasks populate the DINOv2 pgvector index from GBIF. They are NOT on a
default beat schedule — acquisition is an explicit, operator-triggered batch
(initial index build or targeted re-index per species).
"""

import structlog

from app.common.dependencies import get_reference_image_service, get_species_repo
from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)  # type: ignore[misc]
def acquire_reference_images_task(self, species_key: str, scientific_name: str) -> dict:  # type: ignore[no-untyped-def]
    """Acquire and index license-clean reference images for one species."""
    try:
        service = get_reference_image_service()
        result = service.acquire_for_species(species_key, scientific_name)
        return {
            "species_key": species_key,
            "candidates_found": result.candidates_found,
            "accepted": result.accepted,
            "rejected_license": result.rejected_license,
            "rejected_quality": result.rejected_quality + result.rejected_error,
            "usable_for_recognition": result.usable_for_recognition,
        }
    except Exception as exc:
        logger.error("acquire_reference_images_failed", species_key=species_key, error=str(exc))
        raise self.retry(exc=exc) from exc


@celery_app.task  # type: ignore[misc]
def acquire_all_reference_images_task(batch_size: int = 100) -> dict:
    """Fan out per-species acquisition across all species (initial index build)."""
    species_repo = get_species_repo()
    dispatched = 0
    offset = 0
    while True:
        species, total = species_repo.get_all(offset=offset, limit=batch_size)
        if not species:
            break
        for sp in species:
            if not sp.scientific_name:
                continue
            acquire_reference_images_task.delay(sp.key, sp.scientific_name)
            dispatched += 1
        offset += batch_size
        if offset >= total:
            break

    logger.info("acquire_all_reference_images_dispatched", dispatched=dispatched)
    return {"dispatched": dispatched}
