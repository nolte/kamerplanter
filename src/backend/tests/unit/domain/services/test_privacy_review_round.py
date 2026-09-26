"""#1662 review round — findings that a status field could not have shown.

Each case names the review finding it pins. All of them are about a record or a
response that says one thing while the system did another, which is the class
#1645 is about; several were introduced by the first version of that repair.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.personal_data_repository import IPersonalDataRepository
from app.domain.models.privacy import DataExportRequest, ErasureRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakeDataExportRepo, FakePersonalTenants, RecordingErasureExecutor

USER = "u-1"


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A deployment that can erase has a log salt (#1812): the erasure refuses to run without one."""
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


def _service(**overrides) -> PrivacyService:
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
        "tenant_service": FakePersonalTenants(),
    }
    deps.update(overrides)
    return PrivacyService(**deps)


class _ProfileOnlyRepo(IPersonalDataRepository):
    """Answers the profile source and nothing else; records what it was asked."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, tuple[str, ...]]] = []

    def collect_for_user(self, source, user_key, tenant_keys):
        self.asked.append((source.collection, tuple(tenant_keys)))
        if source.filter_field == "_key":
            return [{"email": "s@example.invalid"}]
        return []


class _Storage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []

    async def put_object(self, key, stream, mime_type, metadata=None):
        self.objects[key] = b"".join([c async for c in stream])
        return MagicMock(key=key)

    async def delete_object(self, key):
        self.deleted.append(key)
        self.objects.pop(key, None)


# ── SCR-010: the erasure status route has an owner ─────────────────


class TestErasureStatusIsOwnerScoped:
    def test_another_users_erasure_reads_as_not_found(self):
        erasure_repo = MagicMock()
        erasure_repo.get_or_raise.return_value = ErasureRequest(key="er-1", user_key="someone-else", status="scheduled")
        svc = _service(erasure_repo=erasure_repo)

        with pytest.raises(NotFoundError):
            svc.get_erasure_status(USER, "er-1")

    def test_the_owner_reads_their_own(self):
        erasure_repo = MagicMock()
        erasure_repo.get_or_raise.return_value = ErasureRequest(key="er-1", user_key=USER, status="scheduled")
        svc = _service(erasure_repo=erasure_repo)

        assert svc.get_erasure_status(USER, "er-1").key == "er-1"


# ── SCR-003: a completed erasure does not keep its old failure reason ──


@pytest.mark.asyncio
class TestCompletedErasureClearsItsReason:
    async def test_the_completed_write_clears_error_message(self):
        """Pinned on the *write*, because the repository merges (#1506).

        A full-model write cannot clear a field; only a named-field write with
        ``keep_none`` can. So the assertion is that ``update_fields`` is the
        method used and that it names ``error_message: None`` explicitly.
        """
        erasure = ErasureRequest(
            key="er-1",
            user_key=USER,
            status="partially_completed",
            error_message="ArangoDB erasure did not run: …",
        )
        erasure_repo = MagicMock()
        erasure_repo.list_due_for_hard_delete.return_value = [erasure]
        # #1645 — the retry now runs the declared plan through a real executor
        # entry instead of a patched-away inventory slice.
        svc = _service(erasure_repo=erasure_repo, erasure_executor=RecordingErasureExecutor(), tombstone_salt="s" * 32)

        await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert erasure.status == "completed"
        assert erasure.error_message is None
        written = [
            c.args[1] for c in erasure_repo.update_fields.call_args_list if c.args[1].get("status") == "completed"
        ]
        assert written, "the completed transition must be a named-field write"
        assert "error_message" in written[-1] and written[-1]["error_message"] is None


# ── SCR-005: the download counter is a narrow write ──────────────


class TestDownloadCounterWriteIsNarrow:
    def test_download_does_not_write_the_full_model_back(self):
        export = DataExportRequest(
            key="exp-1",
            user_key=USER,
            status="completed",
            file_path="privacy/exports/u-1/exp-1.json",
            file_size_bytes=10,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        repo = FakeDataExportRepo(export)
        svc = _service(export_repo=repo)

        result = svc.prepare_export_download(USER, "exp-1")

        assert result.download_count == 1
        assert repo.full_model_updates == 0, "a full-model write-back can resurrect a record expiry just cleared"


# ── SCR-006 / SCR-008: a failed run leaves no orphan and leaks no internals ──


@pytest.mark.asyncio
class TestFailedExportLeavesNothingBehind:
    async def test_a_status_write_failure_after_upload_deletes_the_bundle(self):
        export = DataExportRequest(key="exp-1", user_key=USER, status="pending")
        repo = FakeDataExportRepo(export)
        storage = _Storage()
        svc = _service(export_repo=repo, storage_adapter=storage, personal_data_repo=_ProfileOnlyRepo())
        svc._membership_repo = MagicMock()
        svc._membership_repo.list_by_user.return_value = []

        real_update_fields = repo.update_fields

        def failing_completion(key, fields):
            if fields.get("status") == "completed":
                raise RuntimeError("write-write conflict on data_export_requests")
            return real_update_fields(key, fields)

        repo.update_fields = failing_completion

        result = await svc.process_data_export("exp-1")

        assert result.status == "failed"
        assert storage.objects == {}, "the full disclosure of the account stayed in object storage"

    async def test_an_internal_error_is_not_forwarded_to_the_requester(self):
        export = DataExportRequest(key="exp-1", user_key=USER, status="pending")
        repo = FakeDataExportRepo(export)
        svc = _service(export_repo=repo)
        svc._build_export_bundle = AsyncMock(
            side_effect=RuntimeError("AQL: FOR d IN users FILTER d._key == 'u-1' @ arangodb-0.internal:8529")
        )

        result = await svc.process_data_export("exp-1")

        assert result.status == "failed"
        assert "arangodb-0.internal" not in (result.error_message or "")
        assert "AQL" not in (result.error_message or "")
        assert result.error_message, "the requester still gets a reason and a reference"


# ── SCR-001 (c): the walk never leaves the subject's tenants ────────


@pytest.mark.asyncio
class TestTheWalkIsBoundToTheSubjectsTenants:
    async def test_every_tenant_scoped_source_is_asked_with_the_subjects_tenants(self):
        export = DataExportRequest(key="exp-1", user_key=USER, status="pending")
        repo = FakeDataExportRepo(export)
        reader = _ProfileOnlyRepo()
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [MagicMock(tenant_key="t-a"), MagicMock(tenant_key="t-b")]
        svc = _service(
            export_repo=repo,
            storage_adapter=_Storage(),
            personal_data_repo=reader,
            membership_repo=membership_repo,
        )

        await svc.process_data_export("exp-1")

        scoped = [s for s in DataExportEngine.USER_DATA_MANIFEST if s.tenant_scoped and not s.disclosure_gap]
        assert scoped, "guard against a vacuous loop"
        asked = dict(reader.asked)
        for source in scoped:
            assert asked[source.collection] == ("t-a", "t-b"), source.collection


# ── SCR-001 (b): a category that cannot be disclosed says so ────────


@pytest.mark.asyncio
class TestUndisclosableCategoriesSaySo:
    async def test_the_bundle_names_the_reason_instead_of_being_empty(self, monkeypatch):
        """Since #1669 no production source carries a ``disclosure_gap`` (the three
        retained categories are keyed on their server-set account field), so the
        mechanism is exercised with a constructed source added to the manifest
        rather than skipped for lack of one."""
        import json

        from app.domain.models.privacy import DataSourceDefinition

        gapped = DataSourceDefinition(
            collection="gapped_fixture",
            tenant_scoped=True,
            filter_field="whoever",
            label="x",
            fields=["notes"],
            disclosure_gap="cannot be attributed in this fixture",
        )
        monkeypatch.setattr(DataExportEngine, "USER_DATA_MANIFEST", [*DataExportEngine.USER_DATA_MANIFEST, gapped])

        export = DataExportRequest(key="exp-1", user_key=USER, status="pending")
        repo = FakeDataExportRepo(export)
        storage = _Storage()
        reader = _ProfileOnlyRepo()
        svc = _service(export_repo=repo, storage_adapter=storage, personal_data_repo=reader)
        svc._membership_repo = MagicMock()
        svc._membership_repo.list_by_user.return_value = []

        await svc.process_data_export("exp-1")

        bundle = json.loads(next(iter(storage.objects.values())))
        gaps = {s.collection: s.disclosure_gap for s in DataExportEngine.USER_DATA_MANIFEST if s.disclosure_gap}
        assert gaps, "guard against a vacuous loop"
        sections = {s["collection"]: s for s in bundle["sections"]}
        for collection, reason in gaps.items():
            section = sections[collection]
            assert section["disclosed"] is False
            assert section["not_disclosed_reason"] == reason
            assert section["records"] == []
        # And a source that cannot be disclosed is never queried at all: an empty
        # result would read as "no data", which is the lie being removed.
        assert not {c for c, _t in reader.asked} & set(gaps)
