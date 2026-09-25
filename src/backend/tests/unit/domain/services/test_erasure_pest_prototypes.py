"""Issue #1759 — erasure deletes contributed pest prototypes and cannot fail silently.

A promoted pest-image contribution is indexed into the inference-service's
``pest_embeddings`` (``app/tasks/pest_image_tasks.py``). Before #1759 the user
erasure and the tenant deletion only *deactivated* promoted rows, skipped
demoted (already deactivated) ones, swallowed every inference error and put
nothing in the report — the erasure recorded ``completed`` with the vectors
still stored.

These tests drive the scheduled Art. 17 erasure, the tenant deletion and the
single-contribution delete through the **DI provider** with a mock
inference-service behind the real client, and read the outcome off the
service's rows:

* active and deactivated prototypes of the subject are gone; other users',
  other tenants' and curated rows stay;
* a failing delete leaves the duty open (``partially_completed``, backoff,
  ArangoDB untouched) and the contribution documents in place;
* the report and the retained erasure record name the binding and the count;
* a process that reaches no inference-service refuses once a prototype may have
  been indexed (the #1753 marker pattern), and reports ``0`` otherwise.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog.testing

from app.common import dependencies
from app.common.enums import PestImageStatus
from app.common.exceptions import ExternalSourceError, FeatureNotConfiguredError
from app.config.settings import settings
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import (
    InferenceServicePestPrototypeStore,
    NoopPestPrototypeStore,
)
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.pest_image import PestImageContribution
from app.domain.models.privacy import ErasureRequest
from app.domain.services.pest_image_service import PestImageService
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.tenant_service import TenantService
from tests.support.fake_pest_inference_service import FakePestInferenceService, route_pest_requests_to
from tests.support.privacy_doubles import RecordingErasureExecutor
from tests.support.tenant_erasure_doubles import RecordingTenantErasureExecutor, authorized, tenant_service_for_deletion
from tests.support.tenant_erasure_doubles import tenant as tenant_fixture

TOKEN = "svc-token-1759"
SUBJECT = "subject-1759"
OTHER = "other-1759"
TENANT = "t1759"
SALT = "s" * 32


class _PestImageRepo:
    """In-memory ``pest_image_contributions``: the reads and deletes the erasure uses."""

    def __init__(self, contributions: list[PestImageContribution]) -> None:
        self.docs = {c.key: c for c in contributions}

    def list_for_user(self, user_key: str) -> list[PestImageContribution]:
        return [c for c in self.docs.values() if c.contributed_by == user_key]

    def list_for_tenant(self, tenant_key: str) -> list[PestImageContribution]:
        return [c for c in self.docs.values() if c.tenant_key == tenant_key]

    def get(self, key: str, tenant_key: str) -> PestImageContribution | None:
        c = self.docs.get(key)
        return c if c is not None and c.tenant_key == tenant_key else None

    def delete(self, key: str, tenant_key: str) -> bool:
        return self.get(key, tenant_key) is not None and self.docs.pop(key) is not None


def _contribution(key: str, user: str, tenant: str, status: PestImageStatus) -> PestImageContribution:
    return PestImageContribution(
        _key=key,
        tenant_key=tenant,
        pest_key="p-mite",
        attachment_id=f"att-{key}",
        contributed_by=user,
        status=status,
    )


@pytest.fixture
def pest_index(monkeypatch) -> FakePestInferenceService:
    """Pest detection enabled; the subject has a promoted and a demoted contribution."""
    monkeypatch.setattr(settings, "pest_detection_enabled", True)
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    monkeypatch.setattr(settings, "inference_service_url", "http://recognition.test:8000")
    monkeypatch.setattr(settings, "internal_service_token", TOKEN)
    fake = FakePestInferenceService(token=TOKEN)
    # The subject's promoted contribution (active row) and a demoted one (the
    # demote path deactivated its row; the row stays).
    fake.add_contribution(label="spider_mite", tenant_key=TENANT, contribution_key="c-promoted")
    fake.add_contribution(label="spider_mite", tenant_key=TENANT, contribution_key="c-demoted", active=False)
    # Another user in the same tenant, the subject in a second tenant whose key
    # starts like the first, and a curated row sharing a record id.
    fake.add_contribution(label="spider_mite", tenant_key=TENANT, contribution_key="c-other")
    fake.add_contribution(label="aphid", tenant_key=f"{TENANT}0", contribution_key="c-second-tenant")
    fake.add_curated(label="spider_mite", record="c-promoted")
    route_pest_requests_to(monkeypatch, fake)
    return fake


def _repo() -> _PestImageRepo:
    return _PestImageRepo(
        [
            _contribution("c-promoted", SUBJECT, TENANT, PestImageStatus.PROMOTED),
            _contribution("c-demoted", SUBJECT, TENANT, PestImageStatus.PRIVATE),
            _contribution("c-private", SUBJECT, TENANT, PestImageStatus.PRIVATE),
            _contribution("c-other", OTHER, TENANT, PestImageStatus.PROMOTED),
            _contribution("c-second-tenant", SUBJECT, f"{TENANT}0", PestImageStatus.PROMOTED),
        ]
    )


def _privacy_service(erasure: ErasureRequest, pest_repo, store, executor) -> PrivacyService:  # type: ignore[no-untyped-def]
    erasure_repo = MagicMock()
    erasure_repo.list_due_for_hard_delete.return_value = [erasure]
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=erasure_repo,
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
        reference_index_store=NoopReferenceIndexStore(),
        pest_image_repo=pest_repo,
        pest_prototype_store=store,
        erasure_executor=executor,
        tombstone_salt=SALT,
    )


def _erasure() -> ErasureRequest:
    return ErasureRequest(key="er-1759", user_key=SUBJECT, status="scheduled")


# -- Art. 17 user erasure -----------------------------------------------------


async def test_the_scheduled_erasure_deletes_active_and_deactivated_prototypes(pest_index):
    erasure = _erasure()
    repo = _repo()
    executor = RecordingErasureExecutor()
    service = _privacy_service(erasure, repo, dependencies.get_pest_prototype_store(), executor)

    assert await service.execute_scheduled_erasures(datetime.now(UTC)) == 1

    assert erasure.status == "completed"
    # Promoted and demoted rows, in both tenants, are gone; the other user's
    # row and the curated row with the same record id stay.
    assert sorted((r["source"], r["source_record_id"]) for r in pest_index.rows) == [
        ("gbif", "c-promoted"),
        ("user_contributed", "c-other"),
    ]
    assert set(repo.docs) == {"c-other"}
    assert len(executor.runs) == 1


async def test_the_report_and_the_record_name_the_binding_and_the_count(pest_index):
    erasure = _erasure()
    service = _privacy_service(erasure, _repo(), dependencies.get_pest_prototype_store(), RecordingErasureExecutor())

    with structlog.testing.capture_logs() as logs:
        await service.execute_scheduled_erasures(datetime.now(UTC))

    assert erasure.pest_prototype_binding == "inference_service"
    assert erasure.pest_prototypes_removed == 3
    (event,) = [e for e in logs if e["event"] == "erasure.account_erased"]
    assert event["pest_prototype_binding"] == "inference_service"
    assert event["pest_prototypes_removed"] == 3
    # No key in the request line (#1700): the keys travel in the body.
    assert all(SUBJECT not in str(r.url) and "c-promoted" not in str(r.url) for r in pest_index.requests)


@pytest.mark.parametrize("status", [401, 500, 503])
async def test_a_failing_prototype_delete_leaves_the_duty_open(pest_index, status):
    pest_index.failure_status = status
    erasure = _erasure()
    repo = _repo()
    executor = RecordingErasureExecutor()
    service = _privacy_service(erasure, repo, dependencies.get_pest_prototype_store(), executor)

    assert await service.execute_scheduled_erasures(datetime.now(UTC)) == 0

    assert erasure.status == "partially_completed"
    assert erasure.attempt_count == 1
    assert erasure.next_attempt_at is not None
    assert f"HTTP {status}" in (erasure.error_message or "")
    assert SUBJECT not in (erasure.error_message or "")
    assert erasure.pre_arango_completed_at is None
    assert executor.runs == []
    # The documents that carry the contribution keys stay for the retry.
    assert {"c-promoted", "c-demoted"} <= set(repo.docs)


async def test_a_process_without_the_service_reports_zero_until_a_prototype_was_indexed(monkeypatch):
    monkeypatch.setattr(settings, "pest_detection_enabled", False)
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    erasure = _erasure()
    store = NoopPestPrototypeStore(marker=_Marker(since=None))
    service = _privacy_service(erasure, _repo(), store, RecordingErasureExecutor())

    assert await service.execute_scheduled_erasures(datetime.now(UTC)) == 1

    assert erasure.status == "completed"
    assert erasure.pest_prototype_binding == "noop"
    assert erasure.pest_prototypes_removed == 0


async def test_a_process_without_the_service_holds_the_erasure_once_a_prototype_was_indexed():
    erasure = _erasure()
    executor = RecordingErasureExecutor()
    store = NoopPestPrototypeStore(marker=_Marker(since=datetime(2026, 9, 1, tzinfo=UTC)))
    service = _privacy_service(erasure, _repo(), store, executor)

    assert await service.execute_scheduled_erasures(datetime.now(UTC)) == 0

    assert erasure.status == "partially_completed"
    assert "PEST_DETECTION_ENABLED" in (erasure.error_message or "")
    # A configuration hold spends no attempt (#1666).
    assert erasure.attempt_count == 0
    assert executor.runs == []


async def test_erase_account_refuses_a_pest_image_repo_without_a_store():
    executor = RecordingErasureExecutor()
    service = _privacy_service(_erasure(), _repo(), None, executor)

    with pytest.raises(FeatureNotConfiguredError):
        await service.erase_account(SUBJECT)
    assert executor.runs == []


# -- REQ-024 tenant deletion -------------------------------------------------


def _tenant_service(store, pest_repo, storage=None) -> TenantService:  # type: ignore[no-untyped-def]
    """The deletion wiring of ``get_tenant_service`` (#1769: executor + record store + salt)."""
    return tenant_service_for_deletion(
        existing=tenant_fixture(TENANT),
        executor=RecordingTenantErasureExecutor(),
        storage_adapter=storage,
        reference_index_store=NoopReferenceIndexStore(),
        pest_image_repo=pest_repo,
        pest_prototype_store=store,
    )


def test_tenant_deletion_deletes_the_tenants_prototypes_including_orphans(pest_index):
    # A prototype whose contribution document is already gone.
    pest_index.add_contribution(label="aphid", tenant_key=TENANT, contribution_key="c-orphan")
    repo = _repo()
    service = _tenant_service(dependencies.get_pest_prototype_store(), repo)

    with structlog.testing.capture_logs() as logs:
        assert service.delete_tenant(TENANT, **authorized(TENANT)).status == "completed"

    assert sorted((r["source"], r["source_record_id"]) for r in pest_index.rows) == [
        ("gbif", "c-promoted"),
        ("user_contributed", "c-second-tenant"),
    ]
    (event,) = [e for e in logs if e["event"] == "tenant_pest_prototype_cleanup"]
    assert (event["binding"], event["removed"]) == ("inference_service", 4)
    # The link documents themselves are an inventory entry of the ArangoDB run
    # (#1769), measured in tests/integration/test_tenant_erasure_reach.py.
    (plan,) = service._tenant_erasure_executor.plans
    assert "pest_image_contributions" in [e.collection for e in plan.entries if e.action == "delete"]


def test_a_failing_prototype_delete_keeps_the_tenant_and_its_data(pest_index):
    pest_index.failure_status = 503
    storage = MagicMock()
    storage.delete_prefix = AsyncMock(return_value=0)
    repo = _repo()
    service = _tenant_service(dependencies.get_pest_prototype_store(), repo, storage=storage)

    with pytest.raises(ExternalSourceError) as caught:
        service.delete_tenant(TENANT, **authorized(TENANT))

    assert caught.value.status_code == 502
    assert TENANT not in str(caught.value)
    assert service._tenant_erasure_executor.plans == []
    storage.delete_prefix.assert_not_awaited()
    assert "c-promoted" in repo.docs


def test_tenant_deletion_refuses_a_pest_image_repo_without_a_store():
    service = _tenant_service(None, _repo())

    with pytest.raises(FeatureNotConfiguredError):
        service.delete_tenant(TENANT, **authorized(TENANT))
    assert service._tenant_erasure_executor.plans == []
    assert service._tenant_erasure_repo.records == {}


# -- single contribution delete ---------------------------------------------


def _pest_image_service(repo, store) -> PestImageService:  # type: ignore[no-untyped-def]
    attachments = MagicMock()
    attachments.delete = AsyncMock(return_value=True)
    return PestImageService(
        repo=repo,
        attachment_service=attachments,
        ipm_service=MagicMock(),
        prototype_store=store,
    )


async def test_deleting_a_promoted_contribution_deletes_its_prototype(pest_index):
    repo = _repo()
    service = _pest_image_service(repo, dependencies.get_pest_prototype_store())

    assert await service.delete(TENANT, SUBJECT, "c-promoted") is True

    assert "c-promoted" not in {r["source_record_id"] for r in pest_index.rows if r["source"] == "user_contributed"}
    assert "c-promoted" not in repo.docs


async def test_a_failing_prototype_delete_keeps_the_contribution(pest_index):
    pest_index.failure_status = 503
    repo = _repo()
    service = _pest_image_service(repo, dependencies.get_pest_prototype_store())

    with pytest.raises(ExternalSourceError):
        await service.delete(TENANT, SUBJECT, "c-promoted")

    assert "c-promoted" in repo.docs
    service._attachments.delete.assert_not_awaited()


async def test_a_delete_without_a_wired_store_refuses_and_keeps_the_contribution():
    repo = _repo()
    service = _pest_image_service(repo, None)

    with pytest.raises(FeatureNotConfiguredError):
        await service.delete(TENANT, SUBJECT, "c-promoted")
    assert "c-promoted" in repo.docs


async def test_many_contributions_are_erased_in_bounded_requests(pest_index):
    keys = [f"c-bulk-{i}" for i in range(1203)]
    for key in keys:
        pest_index.add_contribution(label="aphid", tenant_key=TENANT, contribution_key=key)
    store = dependencies.get_pest_prototype_store()
    before = len(pest_index.requests)

    assert await store.delete_contributions(keys) == 1203

    sizes = [len(json.loads(r.content)["contribution_keys"]) for r in pest_index.requests[before:]]
    assert sizes == [500, 500, 203]


# -- binding --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("pest", "inference", "binding"),
    [(True, False, "inference_service"), (False, True, "inference_service"), (False, False, "noop")],
)
def test_the_provider_binds_the_store_the_process_can_reach(monkeypatch, pest, inference, binding):
    monkeypatch.setattr(settings, "pest_detection_enabled", pest)
    monkeypatch.setattr(settings, "inference_service_enabled", inference)
    monkeypatch.setattr(dependencies, "get_system_settings_repo", lambda: _Marker(since=None))

    store = dependencies.get_pest_prototype_store()

    assert store.binding == binding
    assert isinstance(store, InferenceServicePestPrototypeStore if binding != "noop" else NoopPestPrototypeStore)


class _Marker:
    def __init__(self, since: datetime | None) -> None:
        self._since = since

    def record_pest_prototype_contributions(self, now: datetime) -> None:
        self._since = self._since or now

    def pest_prototype_contributions_since(self) -> datetime | None:
        return self._since
