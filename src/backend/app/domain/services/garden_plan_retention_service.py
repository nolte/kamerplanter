"""NFR-011 retention of the garden plan's two logs (REQ-053 GP-NFR-055; WP 4.1, #2400).

Two rules, two methods, two Celery beat tasks (``retention.anonymize_expired_care_events`` and
``retention.purge_expired_garden_plan_audit``): NFR-011 §3.1 knows no master task, and a failure of one rule
must not hold the other back.

* **R-25 — the care log.** A care event keeps its person fields, free texts and photos for
  ``RETENTION_CARE_EVENT_RETENTION_YEARS`` (five) from ``performed_at``, the look-back of the crop rotation
  (GP-FR-103). After that the five account references become the erasure marker, the five free-text fields
  ``[redacted]`` and the photos are deleted; ``category``, ``performed_at``, ``quantity``, ``location_key`` and
  ``plant_keys`` stay (Art. 17 para. 3: the cultivation history). ``pest_control`` / ``ipm`` entries follow
  the longer of the care-event and the treatment period (PflSchG §11, as R-17).
* **R-26 — the plan change log.** A ``garden_plan_audit`` row is hard-deleted one year after ``at``.

Both are installation-wide sweeps and read the periods from :class:`RetentionService` only. They run in batches,
so one run never holds the collection in memory, and log counts only.
"""

from __future__ import annotations

from datetime import datetime

import structlog

from app.domain.interfaces.care_event_repository import ICareEventRepository
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.retention_service import RetentionService

logger = structlog.get_logger()

#: Rows per batch, and batches per run: a run is bounded (a backlog is worked off over several nights).
BATCH_SIZE = 500
MAX_BATCHES = 200


class GardenPlanRetentionService:
    def __init__(
        self,
        care_event_repo: ICareEventRepository,
        plan_repo: IGardenPlanRepository,
        attachment_service: AttachmentService,
        retention: RetentionService,
    ) -> None:
        self._care_events = care_event_repo
        self._plan = plan_repo
        self._attachments = attachment_service
        self._retention = retention

    async def anonymize_expired_care_events(self, now: datetime) -> dict[str, int]:
        """Anonymise the care events past R-25 and delete the photos they held (unless another carrier holds them)."""
        cutoff = self._retention.care_event_anonymisation_cutoff(now)
        pflschg_cutoff = self._retention.care_event_pflschg_cutoff(now)
        anonymized = 0
        photos_deleted = 0
        for _ in range(MAX_BATCHES):
            batch = self._care_events.anonymize_expired(
                cutoff=cutoff, pflschg_cutoff=pflschg_cutoff, now=now, batch=BATCH_SIZE
            )
            anonymized += batch.anonymized
            for tenant_key, attachment_id in batch.detached_photos:
                if await self._attachments.delete_if_unreferenced(attachment_id, tenant_key):
                    photos_deleted += 1
            if batch.anonymized < BATCH_SIZE:
                break
        logger.info(
            "retention.anonymize_expired_care_events.completed",
            anonymized=anonymized,
            photos_deleted=photos_deleted,
            retention_years=self._retention.care_event_retention_years,
        )
        return {"anonymized": anonymized, "photos_deleted": photos_deleted}

    def purge_expired_garden_plan_audit(self, now: datetime) -> int:
        """Hard-delete the plan audit rows past R-26."""
        cutoff = self._retention.garden_plan_audit_purge_cutoff(now)
        purged = 0
        for _ in range(MAX_BATCHES):
            removed = self._plan.purge_audit_before(cutoff, batch=BATCH_SIZE)
            purged += removed
            if removed < BATCH_SIZE:
                break
        logger.info(
            "retention.purge_expired_garden_plan_audit.completed",
            purged=purged,
            retention_days=self._retention.garden_plan_audit_retention_days,
        )
        return purged
