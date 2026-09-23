"""#1645 — neither REQ-025 executor may report a success it did not deliver.

The two defects this file pins are not "the feature is unfinished". They are
*records that claim otherwise*:

* ``_finalize_erasure`` wrote ``status="completed"`` while logging that the
  ArangoDB deletion was still pending. ``completed`` is the audit record's own
  claim that the Art. 17 erasure ran; an operator reading ``erasure_requests``
  could not tell a finished erasure from one that deleted nothing.
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
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import DataExportRequest, ErasureRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakeDataExportRepo


def _make_service(**overrides) -> PrivacyService:
    deps = {
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


@pytest.mark.asyncio
class TestErasureDoesNotClaimAnUnrunDeletion:
    async def test_an_erasure_that_deleted_no_document_is_not_completed(self):
        """The record may not say ``completed`` while the user still exists.

        The two halves are asserted together on purpose: the status is only
        meaningful next to the effect it describes.
        """
        erasure = ErasureRequest(
            key="er-1",
            user_key="u-1",
            status="scheduled",
            requested_at=datetime.now(UTC),
        )
        erasure_repo = MagicMock()
        erasure_repo.list_due_for_hard_delete.return_value = [erasure]
        user_repo = MagicMock()
        svc = _make_service(erasure_repo=erasure_repo, user_repo=user_repo)

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        # Effect: nothing was removed.
        user_repo.delete.assert_not_called()
        # Claim: therefore the record must not read as a finished erasure, and
        # the run must not count it as one.
        assert erasure.status != "completed"
        assert erasure.completed_at is None
        assert finalised == 0

    async def test_the_unfinished_erasure_names_what_did_not_run(self):
        """A truthful record must be actionable, not merely non-``completed``."""
        erasure = ErasureRequest(
            key="er-1",
            user_key="u-1",
            status="scheduled",
            requested_at=datetime.now(UTC),
        )
        erasure_repo = MagicMock()
        erasure_repo.list_due_for_hard_delete.return_value = [erasure]
        svc = _make_service(erasure_repo=erasure_repo)

        await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert erasure.error_message
        # The reason is derived from the one declared inventory (#1622), not
        # written down a second time here: a step re-attributed to a real
        # executor must drop out of the message without editing this test.
        unexecuted = [step.collection for step in ErasureEngine.steps_for("retention_worker")]
        assert unexecuted, "guard against a vacuous assertion if the slice ever empties"
        for name in unexecuted:
            assert name in erasure.error_message

    async def test_the_request_stays_selectable_for_a_later_retry(self):
        """The obligation stays open: the daily beat must pick it up again.

        ``ArangoErasureRepository.list_due_for_hard_delete`` selects exactly
        ``scheduled`` / ``partially_completed`` / stale ``in_progress``. A
        terminal state outside that set would silently drop the Art. 17 duty.
        """
        erasure = ErasureRequest(key="er-1", user_key="u-1", status="scheduled")
        erasure_repo = MagicMock()
        erasure_repo.list_due_for_hard_delete.return_value = [erasure]
        svc = _make_service(erasure_repo=erasure_repo)

        await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert erasure.status in {"scheduled", "partially_completed", "in_progress"}


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
