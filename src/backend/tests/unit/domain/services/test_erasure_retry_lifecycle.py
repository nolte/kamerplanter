"""#1666 finding 1 — a failing Art. 17 erasure must not repeat its storage work nightly.

Before #1666 a request that failed persistently was re-selected by every daily
beat and ran the whole :meth:`PrivacyService.erase_account` again — export
cleanup, Phase 0 (hard-delete, EXIF strip, metadata anonymisation), Phase 0.5 —
and logged ``retention.erasure.failed`` at **error** every night. An error line
that appears every night by construction is the alarm everyone learns to ignore
(NFR-018 §1).

What is pinned here, measured on the **storage adapter's call count** and on
the **log**, never on a status field alone:

* the obligation stays selectable — the repository still returns it;
* a run inside the backoff window touches no storage and logs nothing at error;
* a retry after Phase 0/0.5 already finished does not repeat them;
* error level is reserved for the first failure and for reaching the
  escalation threshold;
* a missing tombstone salt is a configuration error: one error line per run,
  not one per request, and it spends no attempt.

The storage adapter is the real :class:`LocalFsStorageAdapter` on ``tmp_path``,
subclassed only to count the erasure hooks. A counting ``MagicMock`` would count
calls that could never have touched a file.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from PIL import Image
from structlog.testing import capture_logs

from app.common.enums import AttachmentCategory
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import ErasureRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakePersonalTenants, RecordingErasureExecutor

SALT = "s" * 32
TENANT = "t-1"
USER = "u-1"
T0 = datetime(2026, 9, 1, 4, 0, tzinfo=UTC)


class _AttachmentCatalog:
    """In-memory attachments index with the real repository's filter semantics.

    ``find_by_user`` filters ``tenant_key + created_by (+ category)`` exactly
    like the AQL in ``ArangoAttachmentRepository``; ``anonymize_user_metadata``
    rewrites ``created_by`` so a second pass finds nothing — the idempotence
    the production repository documents.
    """

    def __init__(self) -> None:
        self.rows: list[SimpleNamespace] = []

    def add(self, *, storage_key: str, category: AttachmentCategory, mime_type: str) -> None:
        self.rows.append(
            SimpleNamespace(
                tenant_key=TENANT,
                created_by=USER,
                category=category,
                storage_key=storage_key,
                mime_type=mime_type,
            )
        )

    def _match(self, tenant_key: str, user_key: str, categories: list[AttachmentCategory] | None):
        return [
            row
            for row in self.rows
            if row.tenant_key == tenant_key
            and row.created_by == user_key
            and (not categories or row.category in categories)
        ]

    def find_by_user(self, tenant_key: str, user_key: str, categories: list[AttachmentCategory] | None = None):
        return list(self._match(tenant_key, user_key, categories))

    def anonymize_user_metadata(
        self, tenant_key: str, user_key: str, categories: list[AttachmentCategory] | None = None
    ) -> int:
        rows = self._match(tenant_key, user_key, categories)
        for row in rows:
            row.created_by = "_anonymized"
        return len(rows)


class _CountingLocalFs(LocalFsStorageAdapter):
    """The real local-fs adapter, counting every erasure-hook call and delete."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.calls: list[str] = []

    async def delete_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        self.calls.append(f"delete_for_user:{scope}")
        return await super().delete_for_user(tenant_key, user_key, scope)

    async def strip_exif_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        self.calls.append(f"strip_exif_for_user:{scope}")
        return await super().strip_exif_for_user(tenant_key, user_key, scope)

    async def delete_object(self, key: str) -> None:
        self.calls.append("delete_object")
        await super().delete_object(key)


class _ErasureRepo:
    """Erasure-request store honouring the real selection and write semantics.

    ``list_due_for_hard_delete`` mirrors the AQL filter of
    ``ArangoErasureRepository`` (``scheduled`` / ``partially_completed`` / stale
    ``in_progress``, due by ``hard_delete_scheduled_at``). ``update_fields``
    refuses a field the model does not declare — the real method would persist
    it and never read it back — and re-parses the merged document, as the
    driver round-trip does.
    """

    def __init__(self, erasure: ErasureRequest) -> None:
        self.erasure = erasure

    def list_due_for_hard_delete(self, now_iso: str, stale_before_iso: str) -> list[ErasureRequest]:
        e = self.erasure
        now = datetime.fromisoformat(now_iso)
        stale_before = datetime.fromisoformat(stale_before_iso)
        if e.hard_delete_scheduled_at is None or e.hard_delete_scheduled_at > now:
            return []
        if e.status in ("scheduled", "partially_completed"):
            return [e]
        if e.status == "in_progress" and (e.updated_at is None or e.updated_at <= stale_before):
            return [e]
        return []

    def claim_for_run(self, key: str, *, now_iso: str, stale_before_iso: str) -> ErasureRequest | None:
        """The atomic claim (#1767): refused for ``completed`` and a fresh ``in_progress``."""
        e = self.erasure
        if e.status == "completed":
            return None
        if (
            e.status == "in_progress"
            and e.updated_at is not None
            and e.updated_at > datetime.fromisoformat(stale_before_iso)
        ):
            return None
        return self.update_fields(key, {"status": "in_progress", "last_attempt_at": now_iso, "updated_at": now_iso})

    def update_fields(self, key: str, fields: dict[str, Any]) -> ErasureRequest:
        for field in fields:
            if field not in ErasureRequest.model_fields:
                msg = f"'{field}' is not a field of ErasureRequest; the real write would be a silent no-op."
                raise AttributeError(msg)
        merged = ErasureRequest.model_validate({**self.erasure.model_dump(by_alias=True), **fields})
        for field in ErasureRequest.model_fields:
            setattr(self.erasure, field, getattr(merged, field))
        return self.erasure


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (10, 200, 30)).save(buf, format="JPEG")
    return buf.getvalue()


async def _world(tmp_path, *, executor: RecordingErasureExecutor, salt: str = SALT):
    catalog = _AttachmentCatalog()
    storage = _CountingLocalFs(
        root=str(tmp_path),
        public_base_url="http://localhost/api/v1/storage/token",
        signing_secret="test-secret-please-change",
        max_object_size_bytes=10 * 1024 * 1024,
        attachment_repo=catalog,
    )

    async def _one(data: bytes):
        yield data

    await storage.put_object(f"t/{TENANT}/diary/photo.jpg", _one(_jpeg()), "image/jpeg")
    catalog.add(storage_key=f"t/{TENANT}/diary/photo.jpg", category=AttachmentCategory.DIARY, mime_type="image/jpeg")
    await storage.put_object(f"t/{TENANT}/pest/ref.jpg", _one(_jpeg()), "image/jpeg")
    catalog.add(
        storage_key=f"t/{TENANT}/pest/ref.jpg", category=AttachmentCategory.PEST_REFERENCE, mime_type="image/jpeg"
    )
    storage.calls.clear()

    erasure = ErasureRequest(
        key="er-1",
        user_key=USER,
        status="scheduled",
        requested_at=T0 - timedelta(days=90),
        hard_delete_scheduled_at=T0,
    )
    repo = _ErasureRepo(erasure)
    membership_repo = MagicMock()
    membership_repo.list_by_user.return_value = [SimpleNamespace(tenant_key=TENANT)]
    export_repo = MagicMock()
    export_repo.list_by_user.return_value = []

    service = PrivacyService(
        export_repo=export_repo,
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=repo,
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
        attachment_repo=catalog,
        membership_repo=membership_repo,
        reference_index_store=NoopReferenceIndexStore(),
        erasure_executor=executor,
        tenant_service=FakePersonalTenants(),
        tombstone_salt=salt,
    )
    return service, storage, repo, erasure


def _errors(logs: list[dict[str, Any]]) -> list[str]:
    return [entry["event"] for entry in logs if entry["log_level"] in ("error", "critical")]


@pytest.mark.asyncio
class TestPersistentFailureDoesNotRepeatStorageWork:
    async def test_first_run_does_the_storage_work_and_logs_at_error(self, tmp_path):
        executor = RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted"))
        service, storage, _repo, erasure = await _world(tmp_path, executor=executor)

        with capture_logs() as logs:
            await service.execute_scheduled_erasures(T0)

        assert "strip_exif_for_user:user_diary_attachments" in storage.calls
        assert "delete_for_user:user_pest_reference_images" in storage.calls
        assert _errors(logs) == ["retention.erasure.failed"]
        assert erasure.status == "partially_completed"
        assert erasure.attempt_count == 1
        assert erasure.last_attempt_at == T0

    async def test_a_second_run_in_the_same_state_does_no_storage_work_and_stays_below_error(self, tmp_path):
        """The acceptance box of #1666 finding 1, measured on calls and log."""
        executor = RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted"))
        service, storage, repo, erasure = await _world(tmp_path, executor=executor)
        await service.execute_scheduled_erasures(T0)
        storage.calls.clear()

        later = T0 + timedelta(hours=1)
        with capture_logs() as logs:
            finalised = await service.execute_scheduled_erasures(later)

        assert storage.calls == []
        assert len(executor.runs) == 1
        assert _errors(logs) == []
        assert finalised == 0
        # The Art. 17 duty is still open and still selected.
        assert repo.list_due_for_hard_delete(later.isoformat(), later.isoformat()) == [erasure]
        assert erasure.status == "partially_completed"

    async def test_the_next_retry_skips_phase_0_once_it_finished(self, tmp_path):
        """The executor failed after Phase 0/0.5 completed: the retry runs only the executor."""
        executor = RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted"))
        service, storage, _repo, erasure = await _world(tmp_path, executor=executor)
        await service.execute_scheduled_erasures(T0)
        storage.calls.clear()

        with capture_logs() as logs:
            await service.execute_scheduled_erasures(T0 + timedelta(days=1))

        assert len(executor.runs) == 2, "the retry must reach the executor"
        assert storage.calls == []
        assert _errors(logs) == []
        assert erasure.attempt_count == 2

    async def test_a_retry_that_then_succeeds_completes_with_the_recorded_scopes(self, tmp_path):
        executor = RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted"))
        service, storage, _repo, erasure = await _world(tmp_path, executor=executor)
        await service.execute_scheduled_erasures(T0)
        scopes_after_phase0 = list(erasure.storage_cleanup_scopes)
        executor._fail_with = None  # the outage is over
        storage.calls.clear()

        finalised = await service.execute_scheduled_erasures(T0 + timedelta(days=1))

        assert finalised == 1
        assert erasure.status == "completed"
        assert erasure.error_message is None
        assert erasure.storage_cleanup_scopes == scopes_after_phase0
        assert "user_diary_attachments" in scopes_after_phase0
        assert storage.calls == []

    async def test_a_failure_inside_phase_0_is_repeated_on_the_next_retry(self, tmp_path):
        """No marker when Phase 0 did not finish: the retry must redo it."""
        executor = RecordingErasureExecutor()
        service, storage, _repo, erasure = await _world(tmp_path, executor=executor)
        original = storage.strip_exif_for_user

        async def _down(*_args: Any, **_kwargs: Any) -> int:
            storage.calls.append("strip_exif_for_user:down")
            raise OSError("storage unavailable")

        storage.strip_exif_for_user = _down  # type: ignore[method-assign]
        await service.execute_scheduled_erasures(T0)
        assert executor.runs == []
        assert erasure.pre_arango_completed_at is None
        storage.strip_exif_for_user = original  # type: ignore[method-assign]
        storage.calls.clear()

        finalised = await service.execute_scheduled_erasures(T0 + timedelta(days=1))

        assert "strip_exif_for_user:user_diary_attachments" in storage.calls
        assert finalised == 1

    async def test_backoff_and_escalation_over_three_weeks(self, tmp_path):
        """Daily beats for three weeks against a failure that never clears.

        Attempts land on day 0, 1, 3, 7 and 14 (1, 2, 4, 7-day cap); error level
        appears on the first failure and on reaching the escalation threshold,
        and nowhere else.
        """
        executor = RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted"))
        service, _storage, _repo, erasure = await _world(tmp_path, executor=executor)

        attempt_days: list[int] = []
        error_days: list[int] = []
        for day in range(21):
            runs_before = len(executor.runs)
            with capture_logs() as logs:
                await service.execute_scheduled_erasures(T0 + timedelta(days=day))
            if len(executor.runs) > runs_before:
                attempt_days.append(day)
            if _errors(logs):
                error_days.append(day)

        assert attempt_days == [0, 1, 3, 7, 14]
        assert error_days == [0, 14]
        assert erasure.attempt_count == PrivacyService.ERASURE_ESCALATE_AFTER_ATTEMPTS
        assert erasure.status == "partially_completed"


@pytest.mark.asyncio
class TestMissingSaltIsAConfigurationError:
    async def test_one_error_line_per_run_no_storage_work_no_attempt_spent(self, tmp_path):
        executor = RecordingErasureExecutor()
        service, storage, _repo, erasure = await _world(tmp_path, executor=executor, salt="")

        for day in (0, 1):
            with capture_logs() as logs:
                finalised = await service.execute_scheduled_erasures(T0 + timedelta(days=day))
            assert _errors(logs) == ["retention.execute_scheduled_erasures.not_configured"]
            assert finalised == 0

        assert storage.calls == []
        assert executor.runs == []
        assert erasure.attempt_count == 0
        assert erasure.next_attempt_at is None
        assert "ERASURE_TOMBSTONE_SALT" in (erasure.error_message or "")
