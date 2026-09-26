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
    """Retry tenant deletions left open (#1769). Runs daily at 04:30 UTC.

    A deletion is open when its run failed (an external store, the database) or
    when the executor found something still holding the tenant. The service
    applies the backoff and holds every record while the deployment cannot erase.
    """
    return get_tenant_service().resume_tenant_erasures(datetime.now(UTC))
