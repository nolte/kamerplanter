"""#1666 finding 2 — the export task's declared retry policy must actually apply.

``retention.process_data_export`` declares ``autoretry_for=(Exception,)``,
``max_retries=5`` and a backoff. Since #1662 the service caught **every**
exception and wrote ``failed``, so a transient storage outage ended the Art. 15
request on the first attempt and the declared retries never ran. The task then
logged ``retention.process_data_export.completed`` for that failed result.

These tests run the real task through Celery (``apply`` — eager, so the retry
chain executes in-process without countdowns) against the real
``PrivacyService`` and the real local-fs adapter, which is made to refuse
uploads for a number of attempts the way an unreachable backend does. What is
measured is the number of upload attempts, the moment ``failed`` is written,
and the log line — not a status alone.
"""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest
from structlog.testing import capture_logs

from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.personal_data_repository import IPersonalDataRepository
from app.domain.models.privacy import DataExportRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakeDataExportRepo

USER = "u-42"


class _ProfileOnlyRepo(IPersonalDataRepository):
    def collect_for_user(self, source, user_key, tenant_keys) -> list[dict[str, Any]]:
        return [{"email": "subject@example.invalid"}] if source.filter_field == "_key" else []


class _FlakyLocalFs(LocalFsStorageAdapter):
    """The real adapter; its first ``failures`` uploads fail like an unreachable backend."""

    def __init__(self, *args: Any, failures: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.failures = failures
        self.put_attempts = 0

    async def put_object(self, key: str, stream: AsyncIterator[bytes], mime_type: str, metadata=None):
        self.put_attempts += 1
        if self.put_attempts <= self.failures:
            raise ConnectionError("object storage unreachable")
        return await super().put_object(key, stream, mime_type, metadata)


class _StatusRecordingRepo(FakeDataExportRepo):
    """Records every status write together with the upload count at that moment."""

    def __init__(self, export: DataExportRequest, storage: _FlakyLocalFs) -> None:
        super().__init__(export)
        self._storage = storage
        self.status_writes: list[tuple[str, int]] = []

    def update_fields(self, key: str, fields: dict[str, Any]) -> DataExportRequest:
        if "status" in fields:
            self.status_writes.append((fields["status"], self._storage.put_attempts))
        return super().update_fields(key, fields)


@pytest.fixture
def world(tmp_path, monkeypatch):
    def _build(failures: int):
        storage = _FlakyLocalFs(
            root=str(tmp_path),
            public_base_url="http://localhost/api/v1/storage/token",
            signing_secret="test-secret-please-change",
            max_object_size_bytes=10 * 1024 * 1024,
            failures=failures,
        )
        export = DataExportRequest(key="exp-1", user_key=USER, status="pending", requested_at=datetime.now(UTC))
        repo = _StatusRecordingRepo(export, storage)
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = []
        service = PrivacyService(
            export_repo=repo,
            consent_repo=MagicMock(),
            restriction_repo=MagicMock(),
            erasure_repo=MagicMock(),
            email_change_repo=MagicMock(),
            user_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            data_export_engine=DataExportEngine(),
            erasure_engine=ErasureEngine(),
            consent_engine=ConsentEngine(),
            password_engine=MagicMock(),
            token_engine=MagicMock(),
            email_service=MagicMock(),
            frontend_url="https://app.test",
            storage_adapter=storage,
            personal_data_repo=_ProfileOnlyRepo(),
            membership_repo=membership_repo,
        )
        deps = ModuleType("app.common.dependencies")
        deps.get_privacy_service = lambda: service  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "app.common.dependencies", deps)
        return storage, repo, export, service

    return _build


def _run() -> tuple[Any, list[dict[str, Any]]]:
    from app.tasks.retention_tasks import process_data_export

    with capture_logs() as logs:
        result = process_data_export.apply(args=["exp-1"])
    return result, logs


class TestTransientFailureIsRetriedPerTheDeclaredPolicy:
    def test_a_transient_outage_is_retried_and_then_delivers(self, world):
        storage, repo, export, _service = world(failures=2)

        result, logs = _run()

        assert storage.put_attempts == 3, "two failed uploads, then the third attempt succeeds"
        assert export.status == "completed"
        assert export.file_size_bytes
        assert "failed" not in [status for status, _ in repo.status_writes]
        assert result.get() == {"export_key": "exp-1", "status": "completed"}
        assert "retention.process_data_export.failed" not in [entry["event"] for entry in logs]

    def test_only_the_exhausted_case_writes_failed(self, world):
        from app.tasks.retention_tasks import process_data_export

        storage, repo, export, _service = world(failures=1000)

        _result, _logs = _run()

        attempts = process_data_export.max_retries + 1
        assert storage.put_attempts == attempts
        assert export.status == "failed"
        failed_writes = [uploads for status, uploads in repo.status_writes if status == "failed"]
        assert failed_writes == [attempts], "failed is written once, after the last attempt"
        assert export.error_message and "reference" in export.error_message

    def test_a_permanent_failure_is_not_retried(self, world):
        """A request that cannot be served is not an outage: one attempt, then ``failed``."""
        storage, _repo, export, service = world(failures=0)
        # No personal-data reader: ExportBundleUnavailableError, a permanent failure.
        service._personal_data_repo = None

        result, _logs = _run()

        assert storage.put_attempts == 0
        assert export.status == "failed"
        assert result.get() == {"export_key": "exp-1", "status": "failed"}


class TestTheCompletionLogReflectsTheResult:
    def test_a_failed_result_is_not_logged_as_completed(self, world):
        _storage, _repo, export, service = world(failures=0)
        service._personal_data_repo = None

        _result, logs = _run()

        events = {entry["event"]: entry for entry in logs}
        assert export.status == "failed"
        assert "retention.process_data_export.completed" not in events
        assert events["retention.process_data_export.not_completed"]["status"] == "failed"

    def test_a_completed_result_logs_completed_with_its_status(self, world):
        world(failures=0)

        _result, logs = _run()

        completed = [entry for entry in logs if entry["event"] == "retention.process_data_export.completed"]
        assert len(completed) == 1
        assert completed[0]["status"] == "completed"
