"""#1700 review — the unverified-account cleanup runs the full Art. 17 erasure.

Until the review the task called ``ArangoUserRepository.delete``, which runs only
the ``account_cascade`` slice of the plan. The personal tenant registration
created kept the display name as ``name``/``slug`` and the key as
``owner_user_key`` — a name-bearing orphan of an account that no longer
existed. The task now calls :meth:`PrivacyService.erase_account`, the same entry
both account-deletion paths use; the reach on a real server is measured in
``tests/integration/test_erasure_inventory_special_cases.py``.

The full entry has a precondition the narrow delete did not: the NFR-011 §4
tombstone salt. Without it the task must neither fall back to the narrow delete
(the orphan again) nor report success over nothing — it reports the run as
blocked, loudly, and leaves the accounts for the next run.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.common.exceptions import FeatureNotConfiguredError
from app.tasks.auth_tasks import cleanup_unverified_accounts


def _done(status: str = "completed") -> SimpleNamespace:
    return SimpleNamespace(status=status)


def _run(users: list, erase: AsyncMock) -> tuple[dict, MagicMock, MagicMock]:
    repo = MagicMock()
    repo.get_unverified_before.return_value = users
    repo.count_unverified_undated.return_value = 0
    repo.count_unverified_local_registrations_before.return_value = 0
    service = MagicMock()
    service.erase_account_now = erase
    with (
        patch("app.common.dependencies.get_user_repo", return_value=repo),
        patch("app.common.dependencies.get_privacy_service", return_value=service),
        patch("app.tasks.auth_tasks.logger") as logger,
    ):
        result = cleanup_unverified_accounts.run()
    return result, repo, logger


class TestTheCleanupErasesThroughTheFullPlan:
    def test_every_candidate_goes_through_erase_account_now(self):
        erase = AsyncMock(return_value=_done())
        result, repo, _ = _run([SimpleNamespace(key="u1"), SimpleNamespace(key="u2")], erase)

        assert [call.args[0] for call in erase.await_args_list] == ["u1", "u2"]
        assert {call.kwargs["origin"] for call in erase.await_args_list} == {"unverified_cleanup"}
        repo.delete.assert_not_called()
        assert result == {
            "removed": 2,
            "failed": 0,
            "deferred": 0,
            "skipped": 0,
            "blocked": 0,
            "held_undated": 0,
            "local_registrations_pending": 0,
        }

    def test_an_account_verified_meanwhile_is_skipped(self):
        erase = AsyncMock(return_value=None)
        result, _, _ = _run([SimpleNamespace(key="u1")], erase)

        assert result == {
            "removed": 0,
            "failed": 0,
            "deferred": 0,
            "skipped": 1,
            "blocked": 0,
            "held_undated": 0,
            "local_registrations_pending": 0,
        }

    def test_a_request_left_in_its_backoff_counts_as_deferred_not_removed(self):
        erase = AsyncMock(return_value=_done("partially_completed"))
        result, _, _ = _run([SimpleNamespace(key="u1")], erase)

        assert result == {
            "removed": 0,
            "failed": 0,
            "deferred": 1,
            "skipped": 0,
            "blocked": 0,
            "held_undated": 0,
            "local_registrations_pending": 0,
        }

    def test_no_candidates_needs_no_privacy_service(self):
        erase = AsyncMock()
        result, _, _ = _run([], erase)
        erase.assert_not_awaited()
        assert result == {
            "removed": 0,
            "failed": 0,
            "deferred": 0,
            "skipped": 0,
            "blocked": 0,
            "held_undated": 0,
            "local_registrations_pending": 0,
        }


class TestAMissingSaltBlocksTheRunLoudly:
    def test_nothing_is_deleted_and_the_run_reports_blocked(self):
        erase = AsyncMock(side_effect=FeatureNotConfiguredError("account_erasure", "Set ERASURE_TOMBSTONE_SALT."))
        result, repo, logger = _run([SimpleNamespace(key="u1"), SimpleNamespace(key="u2")], erase)

        repo.delete.assert_not_called()
        assert result == {
            "removed": 0,
            "failed": 0,
            "deferred": 0,
            "skipped": 0,
            "blocked": 2,
            "held_undated": 0,
            "local_registrations_pending": 0,
            "reason": "erasure_not_configured",
        }
        assert erase.await_count == 1, "the precondition is instance-wide; retrying per account changes nothing"
        logger.error.assert_called_once()
        assert logger.error.call_args.args[0] == "cleanup_unverified_accounts_blocked"


class TestOneFailingAccountDoesNotStopTheOthers:
    def test_the_failure_is_counted_and_logged_without_the_key(self):
        erase = AsyncMock(side_effect=[RuntimeError("write to users failed for u1"), _done()])
        result, _, logger = _run([SimpleNamespace(key="u1"), SimpleNamespace(key="u2")], erase)

        assert result == {
            "removed": 1,
            "failed": 1,
            "deferred": 0,
            "skipped": 0,
            "blocked": 0,
            "held_undated": 0,
            "local_registrations_pending": 0,
        }
        (call,) = logger.error.call_args_list
        assert call.args[0] == "cleanup_unverified_account_failed"
        # #1700: erasure logs carry no plaintext account key (the error text may).
        assert "u1" not in str(call)


class TestUndatedAccountsAreCountedNotSilentlyHeld:
    """#1806 GDPR-003 — the selector skips an account whose age is unreadable; the run says how many."""

    def test_the_held_count_is_in_the_result_and_the_audit_line_on_every_path(self):
        from app.data_access.arango.user_repository import ArangoUserRepository

        # ``spec``: a double that invents a method the real repository lacks would pass vacuously.
        repo = MagicMock(spec=ArangoUserRepository)
        repo.get_unverified_before.return_value = []
        repo.count_unverified_undated.return_value = 3
        with (
            patch("app.common.dependencies.get_user_repo", return_value=repo),
            patch("app.tasks.auth_tasks.logger") as logger,
        ):
            result = cleanup_unverified_accounts.run()

        assert result["held_undated"] == 3
        assert logger.info.call_args.kwargs["held_undated"] == 3


class TestLocalRegistrationsAreCountedFirstAndErasedOnlyWhenReleased:
    """#2010 — dry run first. A LOCAL provider row counts as linked, so the default selector misses them."""

    def _repo(self, *, pending: int | Exception = 2):
        from app.data_access.arango.user_repository import ArangoUserRepository

        repo = MagicMock(spec=ArangoUserRepository)
        repo.get_unverified_before.return_value = [SimpleNamespace(key="u1")]
        repo.count_unverified_undated.return_value = 0
        if isinstance(pending, Exception):
            repo.count_unverified_local_registrations_before.side_effect = pending
        else:
            repo.count_unverified_local_registrations_before.return_value = pending
        return repo

    def _run(self, repo, *, released):
        erase = AsyncMock(return_value=_done())
        privacy = MagicMock()
        privacy.erase_account_now = erase
        retention = MagicMock()
        retention.unverified_local_reap_enabled = released
        with (
            patch("app.common.dependencies.get_user_repo", return_value=repo),
            patch("app.common.dependencies.get_privacy_service", return_value=privacy),
            patch("app.common.dependencies.get_retention_service", return_value=retention),
            patch("app.tasks.auth_tasks.logger") as logger,
        ):
            result = cleanup_unverified_accounts.run()
        return result, erase, logger

    def test_unreleased_the_run_counts_and_reports_but_selects_the_narrow_set(self):
        repo = self._repo()
        result, erase, logger = self._run(repo, released=False)

        assert result["local_registrations_pending"] == 2
        assert repo.get_unverified_before.call_args.kwargs == {"include_local_registrations": False}
        repo.count_unverified_undated.assert_called_once_with(include_local_registrations=False)
        warned = [c for c in logger.warning.call_args_list if c.args[0] == "unverified_local_registrations_pending"]
        assert len(warned) == 1
        assert warned[0].kwargs == {"pending": 2, "released": False}
        assert [c.args[0] for c in erase.await_args_list] == ["u1"]

    def test_released_the_run_widens_selector_and_held_counter_together(self):
        repo = self._repo()
        result, _, logger = self._run(repo, released=True)

        assert repo.get_unverified_before.call_args.kwargs == {"include_local_registrations": True}
        repo.count_unverified_undated.assert_called_once_with(include_local_registrations=True)
        assert result["local_registrations_pending"] == 2

    def test_a_failing_dry_run_count_never_widens_even_when_released(self):
        repo = self._repo(pending=ConnectionError("db down"))
        result, erase, _ = self._run(repo, released=True)

        assert repo.get_unverified_before.call_args.kwargs == {"include_local_registrations": False}
        assert result["local_registrations_pending"] is None, "unknown, not zero"
        assert erase.await_count == 1, "the narrow run still completes"

    def test_nothing_pending_logs_no_warning(self):
        _, _, logger = self._run(self._repo(pending=0), released=False)

        assert not [c for c in logger.warning.call_args_list if c.args[0] == "unverified_local_registrations_pending"]

    def test_a_truthy_non_boolean_does_not_release_the_run(self):
        """A double (or a misread setting) that is merely truthy is not the operator's release."""
        repo = self._repo()
        self._run(repo, released=MagicMock())

        assert repo.get_unverified_before.call_args.kwargs == {"include_local_registrations": False}

    def test_the_release_is_off_by_default_and_reads_the_setting(self):
        from app.config.settings import Settings
        from app.domain.services.retention_service import RetentionService

        assert Settings.model_fields["retention_unverified_local_reap_enabled"].default is False
        assert RetentionService().unverified_local_reap_enabled is False
        assert RetentionService(unverified_local_reap_enabled=True).unverified_local_reap_enabled is True
