"""#1645 — neither REQ-025 executor may report a success it did not deliver.

The two defects this file pins are not "the feature is unfinished". They are
*records that claim otherwise*:

* ``_finalize_erasure`` wrote ``status="completed"`` while logging that the
  ArangoDB deletion was still pending. ``completed`` is the audit record's own
  claim that the Art. 17 erasure ran; an operator reading ``erasure_requests``
  could not tell a finished erasure from one that deleted nothing. #1662 made
  it say ``partially_completed`` while no executor existed; since #1645 it runs
  ``erase_account`` and the inverse is pinned: ``completed`` exactly when the
  declared plan ran and accounted for every step, never otherwise.
* ``process_data_export`` flipped the request to ``processing`` and returned.
  The request never left that state, so an Art. 15 request neither delivered a
  bundle nor failed — it simply sat there.

Every assertion below is about the *effect*: what was deleted, what reaches the
requester. A test that asserted a status field alone would be the same defect.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import DataExportRequest, ErasureRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakeDataExportRepo, RecordingErasureExecutor

SALT = "s" * 32


def _make_service(**overrides) -> PrivacyService:
    deps = {
        # #1753 — every erasure path needs a wired reference-index store.
        "reference_index_store": NoopReferenceIndexStore(),
        "export_repo": MagicMock(),
        "consent_repo": MagicMock(),
        "restriction_repo": MagicMock(),
        "erasure_repo": MagicMock(),
        "email_change_repo": MagicMock(),
        "user_repo": MagicMock(),
        "refresh_token_repo": MagicMock(),
        "data_export_engine": DataExportEngine(),
        "erasure_engine": ErasureEngine(),
        "consent_engine": ConsentEngine(),
        "password_engine": MagicMock(),
        "token_engine": MagicMock(),
        "email_service": MagicMock(),
        "frontend_url": "https://app.test",
    }
    deps.update(overrides)
    return PrivacyService(**deps)


def _pending_export(key: str = "exp-1", user_key: str = "u-1") -> DataExportRequest:
    return DataExportRequest(
        key=key,
        user_key=user_key,
        status="pending",
        requested_at=datetime.now(UTC),
    )


def _recording_export_repo(export: DataExportRequest) -> FakeDataExportRepo:
    """A double that honours the repository's real merge semantics (#1506)."""
    return FakeDataExportRepo(export)


def _due(user_key: str = "u-1", status: str = "scheduled") -> ErasureRequest:
    return ErasureRequest(key="er-1", user_key=user_key, status=status, requested_at=datetime.now(UTC))


def _erasure_service(erasure: ErasureRequest, executor: RecordingErasureExecutor, **overrides) -> PrivacyService:
    erasure_repo = MagicMock()
    erasure_repo.list_due_for_hard_delete.return_value = [erasure]
    deps = {"erasure_repo": erasure_repo, "erasure_executor": executor, "tombstone_salt": SALT}
    deps.update(overrides)
    return _make_service(**deps)


@pytest.mark.asyncio
class TestErasureClaimsExactlyWhatRan:
    async def test_an_erasure_whose_plan_ran_is_completed(self):
        """The inverse of the #1662 pin: with the plan executed, ``completed`` is the truth.

        The status is asserted beside the effect it describes: the executor
        received the subject's plan and the NFR-011 tombstone.
        """
        erasure = _due()
        executor = RecordingErasureExecutor()
        svc = _erasure_service(erasure, executor)

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert executor.runs == [("u-1", ErasureEngine.compute_tombstone_hash("u-1", SALT))]
        assert erasure.status == "completed"
        assert erasure.completed_at is not None
        assert erasure.error_message is None
        assert finalised == 1

    async def test_a_run_that_raised_is_not_completed_and_says_why(self):
        erasure = _due()
        svc = _erasure_service(erasure, RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted")))

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert erasure.status == "partially_completed"
        assert erasure.completed_at is None
        assert "transaction aborted" in (erasure.error_message or "")
        assert finalised == 0

    async def test_a_report_missing_a_declared_step_is_not_completed(self):
        """A run that returns without accounting for a step did not erase it."""
        erasure = _due()
        svc = _erasure_service(erasure, RecordingErasureExecutor(drop=("pest_detections",)))

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert erasure.status == "partially_completed"
        assert "pest_detections" in (erasure.error_message or "")
        assert finalised == 0

    async def test_without_the_salt_nothing_runs_and_nothing_is_claimed(self):
        """503 on the admin path; on the scheduled path an open request, untouched data."""
        erasure = _due()
        executor = RecordingErasureExecutor()
        svc = _erasure_service(erasure, executor, tombstone_salt="")

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert executor.runs == []
        assert erasure.status == "partially_completed"
        assert "ERASURE_TOMBSTONE_SALT" in (erasure.error_message or "")
        assert finalised == 0

    async def test_the_request_stays_selectable_for_a_later_retry(self):
        """The obligation stays open: the daily beat must pick it up again.

        ``ArangoErasureRepository.list_due_for_hard_delete`` selects exactly
        ``scheduled`` / ``partially_completed`` / stale ``in_progress``. A
        terminal state outside that set would silently drop the Art. 17 duty.
        """
        erasure = _due()
        svc = _erasure_service(erasure, RecordingErasureExecutor(fail_with=RuntimeError("down")))

        await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert erasure.status in {"scheduled", "partially_completed", "in_progress"}

    async def test_the_status_writes_never_carry_the_subject_key(self):
        """The audit hash is written inside the run; no status write may undo it.

        ``_pseudonymize_audit_collections`` rewrites ``erasure_requests.user_key``
        to the tombstone. Every write afterwards addresses the request by its
        document key and names only status fields.
        """
        erasure = _due()
        svc = _erasure_service(erasure, RecordingErasureExecutor())

        await svc.execute_scheduled_erasures(datetime.now(UTC))

        writes = svc._erasure_repo.update_fields.call_args_list  # type: ignore[attr-defined]
        assert writes, "the run must record its status"
        assert all(call.args[0] == "er-1" for call in writes)
        assert all("user_key" not in call.args[1] for call in writes)
        svc._erasure_repo.update.assert_not_called()  # type: ignore[attr-defined]

    async def test_a_request_already_under_the_hash_is_closed_without_a_rerun(self):
        """A lost final status write must not lead to a hash of the hash.

        The tombstone reaches the request only inside the committed ArangoDB
        transaction. Re-running the plan with it as the "user key" would match
        the audit rows alone and rewrite them to ``hash(hash)``.
        """
        tombstone = ErasureEngine.compute_tombstone_hash("u-1", SALT)
        erasure = _due(user_key=tombstone, status="in_progress")
        executor = RecordingErasureExecutor()
        svc = _erasure_service(erasure, executor)

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert executor.runs == []
        assert erasure.status == "completed"
        assert finalised == 1


@pytest.mark.asyncio
class TestExportFailsVisiblyRatherThanHanging:
    async def test_an_export_that_produced_no_bundle_does_not_stay_processing(self):
        export = _pending_export()
        repo = _recording_export_repo(export)
        svc = _make_service(export_repo=repo)

        result = await svc.process_data_export("exp-1")

        assert result is not None
        assert result.status != "processing", "an Art. 15 request must not sit in processing forever"

    async def test_the_failure_carries_a_reason_the_requester_can_read(self):
        export = _pending_export()
        repo = _recording_export_repo(export)
        svc = _make_service(export_repo=repo)

        await svc.process_data_export("exp-1")
        visible = svc.get_export_status("u-1", "exp-1")

        assert visible.status == "failed"
        assert visible.error_message

    async def test_a_failed_export_is_not_offered_as_a_download(self):
        export = _pending_export()
        repo = _recording_export_repo(export)
        svc = _make_service(export_repo=repo)

        await svc.process_data_export("exp-1")

        with pytest.raises(ValidationError) as excinfo:
            svc.prepare_export_download("u-1", "exp-1")
        # Not merely refused: the refusal repeats the recorded reason, so the
        # requester learns *why* instead of seeing a bare status name.
        # ``in`` against a possibly-empty string is vacuously true, so the
        # reason is pinned as non-empty first.
        assert export.error_message
        assert export.error_message in str(excinfo.value)

    async def test_a_bundle_builder_that_raises_is_reported_not_swallowed(self):
        """The failure path must survive a real builder, not only its absence."""
        export = _pending_export()
        repo = _recording_export_repo(export)
        svc = _make_service(export_repo=repo)
        svc._build_export_bundle = AsyncMock(side_effect=RuntimeError("arango down"))

        result = await svc.process_data_export("exp-1")

        assert result is not None
        assert result.status == "failed"
        # The failure is recorded and reasoned — but the *raw* text is not what
        # the requester sees (#1662 SCR-008): an internal message may carry an
        # AQL query, a path or a hostname. The record gets a reference instead;
        # the original goes to the log.
        assert result.error_message
        assert "arango down" not in result.error_message
        assert "reference" in result.error_message
