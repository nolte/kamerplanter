import structlog

from app.common.dependencies import get_invitation_repo
from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.tenant_tasks.cleanup_expired_invitations")
def cleanup_expired_invitations() -> dict:
    """Mark expired invitations. Runs daily at 02:00."""
    repo = get_invitation_repo()
    count = repo.cleanup_expired()
    logger.info("expired_invitations_cleaned", count=count)
    return {"expired_count": count}
