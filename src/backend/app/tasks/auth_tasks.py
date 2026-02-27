from datetime import UTC, datetime, timedelta

import structlog

from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.auth_tasks.cleanup_expired_tokens")
def cleanup_expired_tokens() -> dict:
    """Remove expired and revoked refresh tokens."""
    from app.common.dependencies import get_refresh_token_repo

    repo = get_refresh_token_repo()
    count = repo.cleanup_expired()
    logger.info("cleanup_expired_tokens", removed=count)
    return {"removed": count}


@celery_app.task(name="app.tasks.auth_tasks.cleanup_unverified_accounts")
def cleanup_unverified_accounts() -> dict:
    """Remove unverified accounts older than 72 hours."""
    from app.common.dependencies import get_user_repo

    repo = get_user_repo()
    cutoff = (datetime.now(UTC) - timedelta(hours=72)).isoformat()
    users = repo.get_unverified_before(cutoff)
    count = 0
    for user in users:
        if user.key:
            repo.delete(user.key)
            count += 1
    logger.info("cleanup_unverified_accounts", removed=count)
    return {"removed": count}
