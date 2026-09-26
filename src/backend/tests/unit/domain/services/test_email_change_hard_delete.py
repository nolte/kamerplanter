"""#1800 — NFR-011 R-07 / R-07b: email-change requests get real deletion, not just a status flip.

Until #1800, ``retention.expire_email_change_requests`` (via
``PrivacyService.expire_email_change_requests``) only flipped an unconfirmed
request's status to ``expired`` (R-07) and nulled the R-07a revert fields of a
confirmed one — the rest of both documents (``new_email``, ``requested_at``,
``confirmed_at``, …) stayed forever. This exercises the two hard-deletes the
same beat now also runs: R-07 against ``expires_at``, R-07b against the
*stored* R-07a revert window rather than a value the service recomputes. The
actual AQL is measured against real ArangoDB in
``tests/integration/test_retention_instant_comparisons.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.retention_service import RetentionService

NOW = datetime(2026, 9, 25, 4, 15, tzinfo=UTC)


def _service(email_change_repo: object, *, retention: RetentionService | None = None) -> PrivacyService:
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=email_change_repo,  # type: ignore[arg-type]
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-32-chars-min!!!", "HS256"),
        email_service=MagicMock(),
        frontend_url="http://frontend.invalid",
        retention=retention or RetentionService(),
    )


def _repo() -> MagicMock:
    repo = MagicMock()
    repo.expire_old.return_value = 0
    repo.close_revert_windows.return_value = 0
    repo.delete_expired_unconfirmed.return_value = 0
    repo.delete_confirmed_past_revert_window.return_value = 0
    return repo


class TestR07HardDeletesUnconfirmedRequests:
    async def test_delegates_to_the_repository_with_now(self):
        repo = _repo()
        repo.delete_expired_unconfirmed.return_value = 3
        service = _service(repo)

        await service.expire_email_change_requests(now=NOW)

        repo.delete_expired_unconfirmed.assert_called_once_with(NOW.isoformat())

    async def test_the_count_is_part_of_the_run(self):
        repo = _repo()
        repo.delete_expired_unconfirmed.return_value = 3
        service = _service(repo)

        affected = await service.expire_email_change_requests(now=NOW)

        # The method's return value stays R-07's own "flipped to expired" count
        # (``affected``) — the beat task's own docstring covers the rest.
        assert affected == repo.expire_old.return_value


class TestR07bHardDeletesConfirmedRequestsPastTheRevertWindow:
    """#1800 security review (SEC-002): R-07b reads the *stored* window, never recomputes one.

    An earlier version passed ``now - RETENTION_EMAIL_CHANGE_REVERT_DAYS``
    compared against ``confirmed_at`` — lowering that setting later would have
    retroactively shrunk a window already granted at confirmation time,
    hard-deleting a confirmed change while its mailed revert link still
    worked. The repository now decides from the row's own
    ``revert_token_hash`` / ``revert_expires_at`` (:meth:`ArangoEmailChangeRepository.
    delete_confirmed_past_revert_window`); the service's job is only to hand
    over ``now``, unmodified by the currently configured period.
    """

    async def test_delegates_to_the_repository_with_the_current_instant(self):
        repo = _repo()
        service = _service(repo, retention=RetentionService(email_change_revert_days=7))

        await service.expire_email_change_requests(now=NOW)

        repo.delete_confirmed_past_revert_window.assert_called_once_with(NOW.isoformat())

    async def test_the_argument_does_not_depend_on_the_revert_days_setting(self):
        """A different RETENTION_EMAIL_CHANGE_REVERT_DAYS must not change what is handed to the repository.

        Only the repository's own stored-window selector may decide what is
        due; the service passing anything setting-derived would reopen SEC-002.
        """
        repo = _repo()
        service = _service(repo, retention=RetentionService(email_change_revert_days=3))

        await service.expire_email_change_requests(now=NOW)

        repo.delete_confirmed_past_revert_window.assert_called_once_with(NOW.isoformat())


class TestTheBeatLogsWhenAnyOfTheFourStepsDidSomething:
    async def test_logs_when_only_a_hard_delete_happened(self):
        import structlog.testing

        repo = _repo()
        repo.delete_expired_unconfirmed.return_value = 1
        service = _service(repo)

        with structlog.testing.capture_logs() as logs:
            await service.expire_email_change_requests(now=NOW)

        (event,) = [e for e in logs if e["event"] == "retention.expire_email_change_requests.completed"]
        assert event["deleted_unconfirmed"] == 1
        assert event["deleted_confirmed"] == 0

    async def test_no_log_when_nothing_happened(self):
        import structlog.testing

        repo = _repo()
        service = _service(repo)

        with structlog.testing.capture_logs() as logs:
            await service.expire_email_change_requests(now=NOW)

        assert not [e for e in logs if e["event"] == "retention.expire_email_change_requests.completed"]
