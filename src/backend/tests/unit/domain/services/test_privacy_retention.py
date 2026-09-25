"""NFR-011 retention pipeline tests for PrivacyService scaffolding.

Covers the four hooks that the Celery retention tasks call:
``process_data_export``, ``execute_scheduled_erasures``,
``expire_email_change_requests``, ``expire_data_exports``.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from tests.support.privacy_doubles import FakeDataExportRepo


def _make_service(**overrides):
    from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
    from app.domain.engines.consent_engine import ConsentEngine
    from app.domain.engines.data_export_engine import DataExportEngine
    from app.domain.engines.erasure_engine import ErasureEngine
    from app.domain.services.privacy_service import PrivacyService

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
        "data_controller_name": "Acme",
        "data_controller_email": "privacy@acme.test",
    }
    deps.update(overrides)
    return PrivacyService(**deps)


@pytest.mark.asyncio
class TestRetentionPipeline:
    async def test_process_data_export_missing_returns_none(self):
        export_repo = MagicMock()
        export_repo.get_by_key.return_value = None
        svc = _make_service(export_repo=export_repo)

        result = await svc.process_data_export("missing-key")
        assert result is None

    async def test_process_data_export_skips_non_pending(self):
        from app.domain.models.privacy import DataExportRequest

        export = DataExportRequest(
            key="x",
            user_key="u-1",
            status="completed",
            requested_at=datetime.now(UTC),
        )
        export_repo = MagicMock()
        export_repo.get_by_key.return_value = export
        svc = _make_service(export_repo=export_repo)

        result = await svc.process_data_export("x")
        assert result.status == "completed"
        export_repo.update.assert_not_called()

    async def test_process_data_export_records_that_a_run_started(self):
        """The run is observable, and it does not stop at ``processing``.

        #1645 — this used to assert ``status == "processing"`` as the end state,
        which is exactly the defect: a request that never leaves ``processing``
        neither delivers data nor reports a failure.
        """
        from app.domain.models.privacy import DataExportRequest

        export = DataExportRequest(
            key="x",
            user_key="u-1",
            status="pending",
            requested_at=datetime.now(UTC),
        )
        export_repo = FakeDataExportRepo(export)
        svc = _make_service(export_repo=export_repo)

        result = await svc.process_data_export("x")
        assert result.processing_started_at is not None
        assert result.status in {"completed", "failed"}

    async def test_process_data_export_records_the_manifest_it_read(self):
        """#1622 — the Art. 15 scope on the record IS the declared manifest.

        Before #1622 ``USER_DATA_MANIFEST`` had no caller at all and the run
        recorded nothing about its scope. The assertion compares the recorded
        list against the engine rather than against a written-down expectation,
        so a manifest entry added later is covered without editing this test —
        and a run that stopped reading the manifest goes red.
        """
        from app.domain.engines.data_export_engine import DataExportEngine
        from app.domain.models.privacy import DataExportRequest

        export = DataExportRequest(
            key="x",
            user_key="u-1",
            status="pending",
            requested_at=datetime.now(UTC),
        )
        export_repo = FakeDataExportRepo(export)
        svc = _make_service(export_repo=export_repo)

        result = await svc.process_data_export("x")

        assert result.manifest_collections == [source.collection for source in DataExportEngine.USER_DATA_MANIFEST]
        assert result.manifest_collections

    async def test_execute_scheduled_erasures_returns_zero_when_empty(self):
        erasure_repo = MagicMock()
        erasure_repo.list_due_for_hard_delete.return_value = []
        svc = _make_service(erasure_repo=erasure_repo)

        result = await svc.execute_scheduled_erasures(datetime.now(UTC))
        assert result == 0

    async def test_execute_scheduled_erasures_counts_only_finalised_erasures(self):
        """#1645 — the return value is *finalised*, not *seen*.

        It used to be 3 here because every candidate was marked ``completed``
        regardless of what ran. Now each candidate runs the declared plan; the
        one whose run fails stays open and is not counted.
        """
        from app.domain.models.privacy import ErasureRequest
        from tests.support.privacy_doubles import RecordingErasureExecutor

        erasure_repo = MagicMock()
        erasure_repo.list_due_for_hard_delete.return_value = [
            ErasureRequest(key=f"er-{i}", user_key=f"u-{i}", status="scheduled") for i in range(3)
        ]
        executor = RecordingErasureExecutor(fail_with=RuntimeError("arango down"), fail_for=frozenset({"u-1"}))
        svc = _make_service(erasure_repo=erasure_repo, erasure_executor=executor, tombstone_salt="s" * 32)

        result = await svc.execute_scheduled_erasures(datetime.now(UTC))
        assert result == 2
        assert [user for user, _tombstone in executor.runs] == ["u-0", "u-1", "u-2"]

    async def test_expire_email_change_requests_delegates_to_repo(self):
        email_repo = MagicMock()
        email_repo.expire_old.return_value = 7
        svc = _make_service(email_change_repo=email_repo)

        result = await svc.expire_email_change_requests(datetime.now(UTC))
        assert result == 7
        email_repo.expire_old.assert_called_once()

    async def test_expire_data_exports_delegates_to_repo(self):
        from app.domain.models.privacy import DataExportRequest

        export_repo = MagicMock()
        # #1645 — `expire_old` now hands back the records it expired, because the
        # caller must delete each bundle from object storage (NFR-011 R-05).
        export_repo.expire_old.return_value = [
            DataExportRequest(key=f"e-{i}", user_key="u-1", status="expired") for i in range(4)
        ]
        svc = _make_service(export_repo=export_repo)

        result = await svc.expire_data_exports(datetime.now(UTC))
        assert result == 4
        export_repo.expire_old.assert_called_once()
