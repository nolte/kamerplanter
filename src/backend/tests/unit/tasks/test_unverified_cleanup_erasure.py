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


def _run(users: list, erase: AsyncMock) -> tuple[dict, MagicMock, MagicMock]:
    repo = MagicMock()
    repo.get_unverified_before.return_value = users
    service = MagicMock()
    service.erase_account = erase
    with (
        patch("app.common.dependencies.get_user_repo", return_value=repo),
        patch("app.common.dependencies.get_privacy_service", return_value=service),
        patch("app.tasks.auth_tasks.logger") as logger,
    ):
        result = cleanup_unverified_accounts.run()
    return result, repo, logger


class TestTheCleanupErasesThroughTheFullPlan:
    def test_every_candidate_goes_through_erase_account(self):
        erase = AsyncMock()
        result, repo, _ = _run([SimpleNamespace(key="u1"), SimpleNamespace(key="u2")], erase)

        assert [call.args[0] for call in erase.await_args_list] == ["u1", "u2"]
        repo.delete.assert_not_called()
        assert result == {"removed": 2, "failed": 0, "blocked": 0}

    def test_no_candidates_needs_no_privacy_service(self):
        erase = AsyncMock()
        result, _, _ = _run([], erase)
        erase.assert_not_awaited()
        assert result == {"removed": 0, "failed": 0, "blocked": 0}


class TestAMissingSaltBlocksTheRunLoudly:
    def test_nothing_is_deleted_and_the_run_reports_blocked(self):
        erase = AsyncMock(side_effect=FeatureNotConfiguredError("account_erasure", "Set ERASURE_TOMBSTONE_SALT."))
        result, repo, logger = _run([SimpleNamespace(key="u1"), SimpleNamespace(key="u2")], erase)

        repo.delete.assert_not_called()
        assert result == {"removed": 0, "failed": 0, "blocked": 2, "reason": "erasure_not_configured"}
        assert erase.await_count == 1, "the precondition is instance-wide; retrying per account changes nothing"
        logger.error.assert_called_once()
        assert logger.error.call_args.args[0] == "cleanup_unverified_accounts_blocked"


class TestOneFailingAccountDoesNotStopTheOthers:
    def test_the_failure_is_counted_and_logged_without_the_key(self):
        erase = AsyncMock(side_effect=[RuntimeError("write to users failed for u1"), None])
        result, _, logger = _run([SimpleNamespace(key="u1"), SimpleNamespace(key="u2")], erase)

        assert result == {"removed": 1, "failed": 1, "blocked": 0}
        (call,) = logger.error.call_args_list
        assert call.args[0] == "cleanup_unverified_account_failed"
        # #1700: erasure logs carry no plaintext account key (the error text may).
        assert "u1" not in str(call)
