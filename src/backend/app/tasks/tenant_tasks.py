from datetime import UTC, datetime

import structlog

from app.common.dependencies import get_invitation_repo, get_retention_service, get_tenant_service
from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.tenant_tasks.cleanup_expired_invitations")
def cleanup_expired_invitations() -> dict:
    """Mark expired invitations, then hard-delete ones expired long enough ago. Runs daily at 02:00.

    NFR-011 R-12 (#1800): an invitation flipped to ``expired`` is hard-deleted
    ``settings.retention_invitation_retention_days`` (default 30) after its
    ``expires_at``. Until #1800 nothing did the second half and the invitee
    address stayed forever.
    """
    repo = get_invitation_repo()
    now = datetime.now(UTC)
    count = repo.cleanup_expired(now=now)
    cutoff = get_retention_service().invitation_purge_cutoff(now).isoformat()
    purged = repo.delete_expired_before(cutoff)
    if count or purged:
        logger.info("expired_invitations_cleaned", count=count, purged=purged)
    return {"expired_count": count, "purged_count": purged}


@celery_app.task(name="app.tasks.tenant_tasks.resume_tenant_erasures")
def resume_tenant_erasures() -> dict:
    """Start tenant deletions whose grace has ended, and retry those left open (#1769, #2123). Daily 04:30 UTC.

    A deletion is *scheduled* while its grace (``RETENTION_TENANT_ERASURE_GRACE_DAYS``,
    REQ-024 AK-52) runs; this beat claims it once ``scheduled_for`` has passed. A
    deletion is open when its run failed (an external store, the database) or when
    the executor found something still holding the tenant. The service applies the
    backoff and holds every record while the deployment cannot erase.
    """
    return get_tenant_service().resume_tenant_erasures(datetime.now(UTC))


@celery_app.task(name="app.tasks.tenant_tasks.run_tenant_erasure")
def run_tenant_erasure(record_key: str) -> dict:
    """Run one accepted tenant deletion (#1792), dispatched by ``DELETE /tenants/{slug}``.

    The request recorded the deletion and froze the tenant, then answered
    ``202 Accepted``; this task claims the record atomically and erases in
    bounded batches, refreshing the claim between them. A second dispatch, the
    daily :func:`resume_tenant_erasures` beat and a still-live run all find the
    claim held and do nothing; a run that crashed is claimed again once its
    heartbeat is stale. A failed run is recorded on the record (backoff,
    escalation), never raised — the broker must not redeliver a deletion that the
    record already retries.
    """
    return get_tenant_service().run_tenant_erasure_task(record_key)
