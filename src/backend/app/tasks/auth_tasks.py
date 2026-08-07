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
    cursor = db.aql.execute(
        query,
        bind_vars={
            "@collection": col.REFRESH_TOKENS,
            "cutoff": cutoff,
        },
    )
    tokens = list(cursor)
    count = 0
    for token in tokens:
        anonymized = _anonymize_ip(token["ip_address"])
        db.collection(col.REFRESH_TOKENS).update(
            {
                "_key": token["_key"],
                "ip_address": anonymized,
                "ip_anonymized_at": now,
            }
        )
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


@celery_app.task(name="app.tasks.auth_tasks.send_duplicate_registration_notice")
def send_duplicate_registration_notice(user_key: str) -> dict:
    """Tell an existing account that somebody tried to register with its address.

    REQ-023 §3.2 / SEC-H-009. Runs in the worker, never in the request: see
    :func:`dispatch_duplicate_registration_notice` for why that is not a detail.

    The payload is the account's **key**, not the address. The address is a third
    party's and would otherwise sit in the broker queue in the clear for whoever
    can read Valkey; the key is opaque and the worker resolves it against the
    same record the request already read.

    Three things can make this a no-op, each of them deliberately quiet:

    * the account is gone (erased between request and pickup),
    * the account is inactive (deactivated or soft-deleted — REQ-025 erasure
      leaves the record in place for the retention window, and mailing it would
      be processing after the fact),
    * the recipient's suppression window is still open.

    Args:
        user_key: Key of the account that already owns the probed address.

    Returns:
        ``{"status": ...}`` with ``sent``, ``suppressed``, ``skipped`` or
        ``failed`` and, for the latter two, a ``reason``.
    """
    from app.common.decoys import email_digest
    from app.common.dependencies import (
        get_email_service,
        get_registration_notice_store,
        get_user_repo,
    )
    from app.config.settings import settings
    from app.domain.engines.registration_notice_engine import RegistrationNoticeEngine

    user = get_user_repo().get_by_key(user_key)
    if user is None:
        logger.info("duplicate_registration_notice_skipped", reason="account_gone")
        return {"status": "skipped", "reason": "account_gone"}
    if not user.is_active:
        logger.info("duplicate_registration_notice_skipped", reason="inactive_account")
        return {"status": "skipped", "reason": "inactive_account"}

    recipient = str(user.email)
    digest = email_digest(recipient)

    # Claimed BEFORE the send, not after: two attempts a millisecond apart would
    # otherwise both pass the check and both send. The cost is that a failed
    # delivery burns the window — the recipient then hears nothing until it
    # expires. That is the right way round: the window exists to bound what an
    # anonymous caller can send, and an SMTP outage must not lift the bound.
    if not get_registration_notice_store().claim(recipient):
        logger.info("duplicate_registration_notice_suppressed", email_sha256=digest)
        return {"status": "suppressed"}

    subject, body = RegistrationNoticeEngine().render(user.locale, settings.frontend_url)
    try:
        get_email_service().send_notification_email(
            to_email=recipient,
            subject=subject,
            html_body=body,
        )
    except NotImplementedError:
        logger.warning("duplicate_registration_notice_unsupported", email_sha256=digest)
        return {"status": "skipped", "reason": "adapter_unsupported"}
    except Exception as exc:  # noqa: BLE001 - a delivery failure is logged, never retried
        # No retry: the window is already claimed, so a retry would return
        # "suppressed" and only cost a queue slot.
        logger.error("duplicate_registration_notice_failed", email_sha256=digest, error=str(exc))
        return {"status": "failed", "reason": "delivery_error"}

    logger.info("duplicate_registration_notice_sent", email_sha256=digest)
    return {"status": "sent"}


def dispatch_duplicate_registration_notice(user_key: str) -> None:
    """Enqueue the notice, swallowing a broker outage.

    Called from a FastAPI background task, i.e. **after** the registration
    response has been written to the socket. Both halves of that matter:

    * *Asynchronous* — the notice may not be timeable. ``/auth/register`` answers
      201 for a taken address exactly as for a free one (SEC-H-009), and
      ``require_email_verification`` defaults to ``False``, so a genuine
      registration sends no mail at all. An SMTP round trip on the duplicate
      branch alone would make it the *slower* one and hand the caller the same
      answer through the clock — the oracle #957 closed, read from the other side.
    * *Swallowed* — ``SmtpEmailAdapter._send`` re-raises. A delivery failure that
      reached the request would answer 500 where a genuine registration answers
      201: an oracle that works even better than the original, and one an
      attacker can provoke by flooding the mail queue.

    A dropped enqueue is not re-tried. The notice is informational and the next
    attempt produces another one; the alternative — a durable outbox — would put
    a third party's address into a second store for no gain the recipient can use.
    """
    try:
        send_duplicate_registration_notice.delay(user_key)
    except Exception as exc:  # noqa: BLE001 - broker outage must not reach the response
        logger.error("duplicate_registration_notice_dispatch_failed", error=str(exc))
