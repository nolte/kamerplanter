import ipaddress
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


def _anonymize_ip(ip_str: str) -> str:
    """Anonymize IP address: IPv4 → last octet=0, IPv6 → /48 prefix."""
    try:
        addr = ipaddress.ip_address(ip_str)
        if isinstance(addr, ipaddress.IPv4Address):
            parts = ip_str.split(".")
            parts[-1] = "0"
            return ".".join(parts)
        else:
            # IPv6: zero out everything after /48 (first 3 groups)
            net = ipaddress.IPv6Network(f"{ip_str}/48", strict=False)
            return str(net.network_address)
    except ValueError:
        return "0.0.0.0"


@celery_app.task(name="app.tasks.auth_tasks.anonymize_old_ips")
def anonymize_old_ips() -> dict:
    """Anonymize IP addresses in refresh tokens older than 7 days (SEC-K-002)."""
    from app.common.dependencies import get_db
    from app.data_access.arango import collections as col

    db = get_db()
    cutoff = (datetime.now(UTC) - timedelta(days=7)).isoformat()
    now = datetime.now(UTC).isoformat()

    # Find tokens with non-anonymized IPs older than 7 days
    query = """
    FOR doc IN @@collection
      FILTER doc.ip_address != null
        AND doc.ip_anonymized_at == null
        AND doc.created_at < @cutoff
      RETURN { _key: doc._key, ip_address: doc.ip_address }
    """
    cursor = db.aql.execute(query, bind_vars={
        "@collection": col.REFRESH_TOKENS,
        "cutoff": cutoff,
    })
    tokens = list(cursor)
    count = 0
    for token in tokens:
        anonymized = _anonymize_ip(token["ip_address"])
        db.collection(col.REFRESH_TOKENS).update({
            "_key": token["_key"],
            "ip_address": anonymized,
            "ip_anonymized_at": now,
        })
        count += 1

    logger.info("anonymize_old_ips", anonymized=count)
    return {"anonymized": count}


@celery_app.task(name="app.tasks.auth_tasks.rotate_oidc_discovery")
def rotate_oidc_discovery() -> dict:
    """Refresh OIDC discovery documents for all auto-discover providers (every 6h)."""
    from app.common.dependencies import get_oauth_engine, get_oidc_config_repo

    repo = get_oidc_config_repo()
    engine = get_oauth_engine()
    configs = repo.list_all()
    updated = 0
    errors = 0

    for config in configs:
        if not config.auto_discover or not config.enabled:
            continue
        try:
            discovery = engine.fetch_discovery_document(config.issuer_url)
            config.discovery_document = discovery
            config.discovery_refreshed_at = datetime.now(UTC)
            if config.key:
                repo.update(config.key, config)
            updated += 1
        except Exception:
            logger.warning("oidc_discovery_failed", slug=config.slug)
            errors += 1

    logger.info("rotate_oidc_discovery", updated=updated, errors=errors)
    return {"updated": updated, "errors": errors}
