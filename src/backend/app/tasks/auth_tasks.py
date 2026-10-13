from datetime import UTC, datetime

import structlog

from app.common.log_privacy import loggable_error, loggable_ip
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
    """Erase unverified accounts past the NFR-011 R-02 period through the full Art. 17 plan.

    The period is ``settings.retention_unverified_account_days`` (default 7,
    NFR-011 R-02 / REQ-023 AK-17), read through :class:`RetentionService`, the
    one place the R-02 cutoff is computed. Until #1772 the task carried a
    literal 72 hours — a period neither the spec nor a setting named.

    Each candidate goes through :meth:`PrivacyService.erase_account_now` (#1767):
    the same persisted erasure request, ``unreached`` gate and retry the
    self-service path has. Until #1767 the task called ``erase_account`` and
    kept only a counter — a run that skipped a declared step counted as
    ``removed``, and a failed one left nothing that would retry it (GDPR-004).
    A failed account now stays an open ``partially_completed`` request the
    daily erasure beat retries with backoff; one inside its backoff is left to
    the beat and counted ``deferred``. An account that confirmed its address
    after the candidate list was read is left alone and counted ``skipped``.

    A deployment that cannot erase (tombstone salt, a derived index) is
    instance-wide, so the run stops at the first
    :class:`FeatureNotConfiguredError`, changes nothing, logs an error and
    reports every remaining candidate as ``blocked``; the next run retries them
    once the configuration is fixed. Any other failure is per account:
    counted, logged without the key (#1700), and the loop moves on.

    **Locally registered accounts (#2010).** Registration writes a ``LOCAL`` provider
    row, so the default selector never reaches an abandoned local registration. The
    run counts how many it would erase (``local_registrations_pending``, also logged)
    and erases them only once ``RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED`` is set
    (the operator's release after reading the count). If that count fails, the run
    keeps the narrow selector.

    Returns:
        ``{"removed", "failed", "deferred", "skipped", "blocked", "held_undated",
        "local_registrations_pending"}`` counts, plus ``reason`` when blocked.
    """
    from app.common.async_bridge import run_async
    from app.common.dependencies import get_privacy_service, get_retention_service, get_user_repo
    from app.common.exceptions import FeatureNotConfiguredError
    from app.common.held_count import held_undated_count

    retention = get_retention_service()
    cutoff = retention.unverified_account_cutoff(datetime.now(UTC)).isoformat()
    user_repo = get_user_repo()
    # #2010 dry run: how many abandoned *local* registrations (a LOCAL provider row
    # counts as linked for the default selector) the released run would erase. Counted
    # on every run, erased only when the operator has released it. A failing count
    # keeps the narrow selector: widening is never done on an error path.
    pending = held_undated_count(
        lambda: user_repo.count_unverified_local_registrations_before(cutoff), task="cleanup_unverified_accounts"
    )
    widen = retention.unverified_local_reap_enabled is True and pending is not None
    if pending:
        logger.warning("unverified_local_registrations_pending", pending=pending, released=widen)
    candidates = [
        user.key for user in user_repo.get_unverified_before(cutoff, include_local_registrations=widen) if user.key
    ]
    # #1806 GDPR-003: accounts the selector skips because their age is unreadable
    # are held for ever; say how many instead of staying silent (the R-06
    # ``held_without_tombstone`` convention).
    result: dict = {
        "removed": 0,
        "failed": 0,
        "deferred": 0,
        "skipped": 0,
        "blocked": 0,
        "held_undated": held_undated_count(
            lambda: user_repo.count_unverified_undated(include_local_registrations=widen),
            task="cleanup_unverified_accounts",
        ),
        "local_registrations_pending": pending,
    }
    if not candidates:
        logger.info("cleanup_unverified_accounts", **result)
        return result

    privacy_service = get_privacy_service()
    for position, user_key in enumerate(candidates):
        try:
            erasure = run_async(privacy_service.erase_account_now(user_key, origin="unverified_cleanup"))
        except FeatureNotConfiguredError as exc:
            result["blocked"] = len(candidates) - position
            result["reason"] = "erasure_not_configured"
            logger.error(
                "cleanup_unverified_accounts_blocked",
                # The salt, a derived index (#1753 / #1759) — the error says which.
                reason=loggable_error(exc),
                **{k: v for k, v in result.items() if k != "reason"},
            )
            return result
        except Exception as exc:  # noqa: BLE001 - one account must not stop the others
            result["failed"] += 1
            logger.error("cleanup_unverified_account_failed", error_type=type(exc).__name__)
            continue
        if erasure is None:
            # Verified (or gone) since the candidate list was read.
            result["skipped"] += 1
        elif erasure.status == "completed":
            result["removed"] += 1
        else:
            result["deferred"] += 1
    logger.info("cleanup_unverified_accounts", **result)
    return result


#: NFR-011 R-03 truncation (IPv4 last octet 0, IPv6 /48). One implementation,
#: shared with the log lines (#1781): a log never holds more than the DB keeps.
_anonymize_ip = loggable_ip


@celery_app.task(name="app.tasks.auth_tasks.anonymize_old_ips")
def anonymize_old_ips() -> dict:
    """Anonymize the IP address of every login session past NFR-011 R-03 (SEC-K-002).

    The period is ``settings.retention_ip_anonymization_days``
    (``RETENTION_IP_ANONYMIZATION_DAYS``, default 7), read through
    :meth:`RetentionService.ip_anonymisation_cutoff` — until #1782 it was a
    literal no setting reached. Selection and write go through the
    refresh-token repository; the task holds no AQL of its own (NFR-001).
    """
    from app.common.dependencies import get_refresh_token_repo, get_retention_service

    repo = get_refresh_token_repo()
    now = datetime.now(UTC)
    cutoff = get_retention_service().ip_anonymisation_cutoff(now).isoformat()
    anonymized_at = now.isoformat()

    count = 0
    for key, ip_address in repo.list_unanonymized_ips_before(cutoff):
        repo.mark_ip_anonymized(key, _anonymize_ip(ip_address), anonymized_at)
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
            if not config.key:
                continue
            # Only the two fields this task owns, and only while the issuer is still
            # the one fetched from (#1909). ``config`` is a snapshot from before the
            # fetches of every provider ahead of it, each paced by its issuer up to
            # its timeout; a write of the whole snapshot would revert a provider
            # switched off, a rotated secret or a repointed issuer — changes that pass
            # an admin step-up (#1883) which this task does not.
            stored = repo.update_discovery(
                config.key,
                issuer_url=config.issuer_url,
                discovery_document=discovery,
                refreshed_at=datetime.now(UTC),
            )
            if stored:
                updated += 1
            else:
                logger.info("oidc_discovery_issuer_changed", slug=config.slug)
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
        # The type only: ``SMTPRecipientsRefused`` embeds the refused address —
        # a third party's — in its text (#1773 review GDPR-004).
        logger.error("duplicate_registration_notice_failed", email_sha256=digest, error_type=type(exc).__name__)
        return {"status": "failed", "reason": "delivery_error"}

    logger.info("duplicate_registration_notice_sent", email_sha256=digest)
    return {"status": "sent"}


def dispatch_duplicate_registration_notice(user_key: str) -> None:
    """Enqueue the notice, swallowing a broker outage.

    Called from a FastAPI background task, i.e. **after** the registration
    response has been written to the socket. Both halves of that matter:

    * *Asynchronous* — the notice may not be timeable. ``/auth/register`` answers
      201 for a taken address exactly as for a free one (SEC-H-009), and a genuine
      registration sends no mail inside the request: none at all with
      ``require_email_verification`` off, and with it on (the default since
      #1948) the verification mail goes out after the response (#1890). An SMTP
      round trip on the duplicate branch alone would make it the *slower* one and
      hand the caller the same answer through the clock — the oracle #957 closed,
      read from the other side.
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
