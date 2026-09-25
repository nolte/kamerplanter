from datetime import UTC, datetime

import structlog

from app.common.dependencies import get_invitation_repo, get_tenant_service
from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.tenant_tasks.cleanup_expired_invitations")
def cleanup_expired_invitations() -> dict:
    """Mark expired invitations. Runs daily at 02:00."""
    repo = get_invitation_repo()
    count = repo.cleanup_expired()
    logger.info("expired_invitations_cleaned", count=count)
    return {"expired_count": count}


@celery_app.task(name="app.tasks.tenant_tasks.resume_tenant_erasures")
def resume_tenant_erasures() -> dict:
    """Retry tenant deletions left open (#1769). Runs daily at 04:30 UTC.

    A deletion is open when its run failed (an external store, the database) or
    when the executor found something still holding the tenant. The service
    applies the backoff and holds every record while the deployment cannot erase.
    """
    return get_tenant_service().resume_tenant_erasures(datetime.now(UTC))
