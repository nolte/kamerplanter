"""#1946 / #1806 GDPR-003 — the three remaining destructive age selectors report what they hold.

R-04 (``revoked_at``), R-07b (``confirmed_at`` / ``revert_expires_at``) and the
glossary cache (``valid_until``) skip a record whose timestamp is missing or
unreadable, exactly like R-02 and the audit logs did before #1945. The repository
doubles are ``spec``-bound to the real classes: a counter the repository lacks
raises instead of passing vacuously. What each counter selects is measured against
a real ArangoDB in ``tests/integration/test_undated_records_held_count.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import structlog.testing

from app.data_access.arango.consent_repository import ArangoConsentRepository
from app.data_access.arango.email_change_repository import ArangoEmailChangeRepository
from app.data_access.arango.glossary_repository import ArangoGlossaryTermCacheRepository
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.retention_service import RetentionService

NOW = datetime(2026, 9, 25, 4, 35, tzinfo=UTC)


def _service(*, consent_repo: object = None, email_change_repo: object = None) -> PrivacyService:
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=consent_repo or MagicMock(),  # type: ignore[arg-type]
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=email_change_repo or MagicMock(),  # type: ignore[arg-type]
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-32-chars-min!!!", "HS256"),
        email_service=MagicMock(),
        frontend_url="http://frontend.invalid",
        retention=RetentionService(),
    )


async def test_the_consent_purge_logs_the_held_count():
    repo = MagicMock(spec=ArangoConsentRepository)
    repo.delete_revoked_before.return_value = 2
    repo.count_undated_revoked.return_value = 5

    with structlog.testing.capture_logs() as logs:
        purged = await _service(consent_repo=repo).purge_expired_consent_records(now=NOW)

    assert purged == 2
    event = next(e for e in logs if e["event"] == "retention.purge_expired_consent_records.completed")
    assert event["held_undated"] == 5
    # A record held for ever is over-retention: it is a warning, not just a field on an info line.
    warning = next(e for e in logs if e["event"] == "retention.held_undated")
    assert (warning["log_level"], warning["rule"], warning["held_undated"]) == ("warning", "R-04", 5)


async def test_a_failing_consent_count_does_not_fail_the_purge():
    repo = MagicMock(spec=ArangoConsentRepository)
    repo.delete_revoked_before.return_value = 2
    repo.count_undated_revoked.side_effect = ConnectionError("db down")

    with structlog.testing.capture_logs() as logs:
        purged = await _service(consent_repo=repo).purge_expired_consent_records(now=NOW)

    assert purged == 2
    event = next(e for e in logs if e["event"] == "retention.purge_expired_consent_records.completed")
    assert event["held_undated"] is None


async def test_the_email_change_run_logs_the_held_count_even_when_nothing_else_happened():
    repo = MagicMock(spec=ArangoEmailChangeRepository)
    repo.expire_old.return_value = 0
    repo.close_revert_windows.return_value = 0
    repo.delete_expired_unconfirmed.return_value = 0
    repo.delete_confirmed_past_revert_window.return_value = 0
    repo.count_undated_confirmed.return_value = 3

    with structlog.testing.capture_logs() as logs:
        await _service(email_change_repo=repo).expire_email_change_requests(now=NOW)

    event = next(e for e in logs if e["event"] == "retention.expire_email_change_requests.completed")
    assert event["held_undated"] == 3
    warning = next(e for e in logs if e["event"] == "retention.held_undated")
    assert (warning["log_level"], warning["rule"]) == ("warning", "R-07b")


async def test_a_failing_email_change_count_does_not_fail_the_run():
    repo = MagicMock(spec=ArangoEmailChangeRepository)
    repo.expire_old.return_value = 1
    repo.close_revert_windows.return_value = 0
    repo.delete_expired_unconfirmed.return_value = 0
    repo.delete_confirmed_past_revert_window.return_value = 0
    repo.count_undated_confirmed.side_effect = ConnectionError("db down")

    assert await _service(email_change_repo=repo).expire_email_change_requests(now=NOW) == 1


def test_the_glossary_cleanup_logs_the_held_count():
    from app.tasks import glossary_tasks

    repo = MagicMock(spec=ArangoGlossaryTermCacheRepository)
    repo.delete_expired.return_value = 4
    repo.count_undated.return_value = 2
    with (
        patch.object(glossary_tasks, "ArangoConnection"),
        patch.object(glossary_tasks, "ArangoGlossaryTermCacheRepository", return_value=repo),
        patch.object(glossary_tasks, "logger") as logger,
    ):
        removed = glossary_tasks.cleanup_expired_cache()

    assert removed == 4
    assert logger.info.call_args.kwargs["held_undated"] == 2
    assert logger.warning.call_args.kwargs["held_undated"] == 2


def test_a_failing_glossary_count_does_not_fail_the_cleanup():
    from app.tasks import glossary_tasks

    repo = MagicMock(spec=ArangoGlossaryTermCacheRepository)
    repo.delete_expired.return_value = 4
    repo.count_undated.side_effect = ConnectionError("db down")
    with (
        patch.object(glossary_tasks, "ArangoConnection"),
        patch.object(glossary_tasks, "ArangoGlossaryTermCacheRepository", return_value=repo),
        patch.object(glossary_tasks, "logger") as logger,
    ):
        assert glossary_tasks.cleanup_expired_cache() == 4
    assert logger.info.call_args.kwargs["held_undated"] is None


async def test_nothing_held_is_not_a_warning():
    repo = MagicMock(spec=ArangoConsentRepository)
    repo.delete_revoked_before.return_value = 0
    repo.count_undated_revoked.return_value = 0

    with structlog.testing.capture_logs() as logs:
        await _service(consent_repo=repo).purge_expired_consent_records(now=NOW)

    assert not [e for e in logs if e["event"] == "retention.held_undated"]
