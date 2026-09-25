"""Issue #1753 — Phase 0.5 and the tenant deletion reach the reference index.

Before #1753 ``get_reference_index_store()`` returned the no-op store whatever
the deployment, so an erased user's ``user_contributed`` DINOv2 vectors survived
the account (REQ-025 AK-OS-05) and a deleted tenant's survived the tenant
(REQ-024). These tests drive the erasure and the tenant deletion through the
**provider** with the inference-service enabled and a mock inference-service
behind the real client, and read the outcome off the service's rows:

* the subject's contributions are gone, curated rows and other users' stay;
* a failing reference-index delete stops the erasure before the ArangoDB plan
  and records ``partially_completed`` — and stops the tenant deletion before
  anything else is removed;
* the report, the retained erasure record and the log lines name the binding
  that ran, so a no-op run is distinguishable from a real one.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog.testing

from app.common import dependencies
from app.common.exceptions import ExternalSourceError, FeatureNotConfiguredError
from app.config.settings import settings
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import ErasureRequest
from app.domain.models.storage import StorageErasureResult
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.tenant_service import TenantService
from tests.support.fake_inference_service import FakeInferenceService, route_httpx_post_to
from tests.support.privacy_doubles import FakePersonalTenants, RecordingErasureExecutor
from tests.support.tenant_erasure_doubles import RecordingTenantErasureExecutor, authorized, tenant_service_for_deletion
from tests.support.tenant_erasure_doubles import tenant as tenant_fixture

TOKEN = "svc-token-1753"
SUBJECT = "subject-1753"
TENANT = "tenant1753"
SALT = "s" * 32


@pytest.fixture
def inference(monkeypatch) -> FakeInferenceService:
    """The inference-service enabled, with the subject's, another user's and curated rows."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    monkeypatch.setattr(settings, "inference_service_url", "http://recognition.test:8000")
    monkeypatch.setattr(settings, "internal_service_token", TOKEN)
    fake = FakeInferenceService(token=TOKEN)
    fake.add(source="user_contributed", contributed_by=SUBJECT, tenant_key=TENANT, record="subject")
    fake.add(source="user_contributed", contributed_by=SUBJECT, tenant_key="other-tenant", record="subject-2")
    fake.add(source="user_contributed", contributed_by="other-user", tenant_key=TENANT, record="other")
    fake.add(source="gbif", contributed_by=SUBJECT, tenant_key=TENANT, record="curated")
    route_httpx_post_to(monkeypatch, fake)
    return fake


def _privacy_service(erasure: ErasureRequest, store, executor: RecordingErasureExecutor) -> PrivacyService:
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
        reference_index_store=store,
        erasure_executor=executor,
        tenant_service=FakePersonalTenants(),
        tombstone_salt=SALT,
    )


def _erasure() -> ErasureRequest:
    return ErasureRequest(key="er-1753", user_key=SUBJECT, status="scheduled")


# -- Art. 17 erasure, Phase 0.5 -----------------------------------------------


async def test_the_scheduled_erasure_removes_the_subjects_contributions(inference):
    erasure = _erasure()
    executor = RecordingErasureExecutor()
    service = _privacy_service(erasure, dependencies.get_reference_index_store(), executor)

    finalised = await service.execute_scheduled_erasures(datetime.now(UTC))

    assert finalised == 1
    assert erasure.status == "completed"
    assert inference.records() == {"other", "curated"}
    assert len(executor.runs) == 1


async def test_the_erasure_record_and_report_name_the_binding_that_ran(inference):
    erasure = _erasure()
    service = _privacy_service(erasure, dependencies.get_reference_index_store(), RecordingErasureExecutor())

    with structlog.testing.capture_logs() as logs:
        report = await service.erase_account(SUBJECT)

    assert report.reference_index_binding == "inference_service"
    assert report.reference_index_removed == 2
    by_event = {event["event"]: event for event in logs}
    assert by_event["retention.erasure.reference_index_cleanup"]["binding"] == "inference_service"
    assert by_event["erasure.account_erased"]["reference_index_binding"] == "inference_service"


async def test_the_checkpoint_persists_the_binding_and_the_count(inference):
    erasure = _erasure()
    service = _privacy_service(erasure, dependencies.get_reference_index_store(), RecordingErasureExecutor())

    await service.execute_scheduled_erasures(datetime.now(UTC))

    assert erasure.reference_index_binding == "inference_service"
    assert erasure.reference_index_removed == 2
    checkpoint = [
        call.args[1]
        for call in service._erasure_repo.update_fields.call_args_list
        if "pre_arango_completed_at" in call.args[1]
    ]
    assert checkpoint == [
        {
            "status": "in_progress",
            "storage_cleanup_scopes": [],
            "pre_arango_completed_at": checkpoint[0]["pre_arango_completed_at"],
            "reference_index_binding": "inference_service",
            "reference_index_removed": 2,
            # #1770 — Phase 0's hard-delete outcome travels with the checkpoint.
            "storage_objects_removed": 0,
            "storage_objects_retained_shared": 0,
        }
    ]


@pytest.mark.parametrize("status", [401, 500, 503])
async def test_a_failing_reference_index_leaves_the_duty_open_and_arangodb_untouched(inference, status):
    inference.failure_status = status
    erasure = _erasure()
    executor = RecordingErasureExecutor()
    service = _privacy_service(erasure, dependencies.get_reference_index_store(), executor)

    with structlog.testing.capture_logs() as logs:
        finalised = await service.execute_scheduled_erasures(datetime.now(UTC))

    assert finalised == 0
    assert erasure.status == "partially_completed"
    assert erasure.attempt_count == 1
    # The checkpoint was not reached, so the retry repeats Phase 0.5.
    assert erasure.pre_arango_completed_at is None
    assert executor.runs == []
    assert "subject" in inference.records()
    # The reason is persisted on a retained record and logged: no plaintext key.
    assert SUBJECT not in (erasure.error_message or "")
    assert str(status) in (erasure.error_message or "")
    assert not [e for e in logs if any(SUBJECT in str(v) for v in e.values())]


async def test_the_noop_binding_is_reported_as_such(monkeypatch):
    from tests.support.fake_contribution_marker import FakeContributionMarker

    monkeypatch.setattr(settings, "inference_service_enabled", False)
    monkeypatch.setattr(dependencies, "get_system_settings_repo", FakeContributionMarker)
    service = _privacy_service(_erasure(), dependencies.get_reference_index_store(), RecordingErasureExecutor())

    report = await service.erase_account(SUBJECT)

    assert report.reference_index_binding == "noop"
    assert report.reference_index_removed == 0


async def test_a_skipped_phase_reports_no_binding(inference):
    wired = _privacy_service(_erasure(), dependencies.get_reference_index_store(), RecordingErasureExecutor())
    report = await wired.erase_account(SUBJECT, pre_arango_completed=True)
    assert report.reference_index_binding is None
    assert inference.requests == []


# -- REQ-024 tenant deletion ------------------------------------------------


def _tenant_service(store, storage=None) -> TenantService:
    """The deletion wiring of ``get_tenant_service`` (#1769: executor + record store + salt)."""
    return tenant_service_for_deletion(
        existing=tenant_fixture(TENANT),
        executor=RecordingTenantErasureExecutor(),
        storage_adapter=storage,
        reference_index_store=store,
    )


def test_tenant_deletion_removes_the_tenants_contributions(inference):
    service = _tenant_service(dependencies.get_reference_index_store())

    with structlog.testing.capture_logs() as logs:
        assert service.delete_tenant(TENANT, **authorized(TENANT)).status == "completed"

    assert inference.records() == {"subject-2", "curated"}
    (event,) = [e for e in logs if e["event"] == "tenant_reference_index_cleanup"]
    assert event["binding"] == "inference_service"
    assert event["removed"] == 2


def test_a_failing_reference_index_keeps_the_tenant_and_its_data(inference):
    inference.failure_status = 503
    storage = MagicMock()
    storage.delete_prefix = AsyncMock(return_value=0)
    service = _tenant_service(dependencies.get_reference_index_store(), storage=storage)

    with pytest.raises(ExternalSourceError) as caught:
        service.delete_tenant(TENANT, **authorized(TENANT))

    assert caught.value.status_code == 502
    assert TENANT not in str(caught.value)
    # Nothing else was removed: the delete is retryable as a whole.
    assert service._tenant_erasure_executor.plans == []
    storage.delete_prefix.assert_not_awaited()
    assert "other" in inference.records()


def test_the_noop_tenant_binding_is_logged(monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    service = _tenant_service(NoopReferenceIndexStore())

    with structlog.testing.capture_logs() as logs:
        service.delete_tenant(TENANT, **authorized(TENANT))

    (event,) = [e for e in logs if e["event"] == "tenant_reference_index_cleanup"]
    assert event["binding"] == "noop"


# -- GDPR-001/002: a no-op binding while contributions exist; SEC-002: unwired ----


def _noop_with_contributions() -> NoopReferenceIndexStore:
    from tests.support.fake_contribution_marker import FakeContributionMarker

    return NoopReferenceIndexStore(marker=FakeContributionMarker(since=datetime(2026, 9, 1, tzinfo=UTC)))


@pytest.mark.parametrize("store_factory", [_noop_with_contributions, lambda: None], ids=["noop+marker", "unwired"])
async def test_the_scheduled_run_holds_the_request_without_spending_an_attempt(store_factory):
    erasure = _erasure()
    executor = RecordingErasureExecutor()
    service = _privacy_service(erasure, store_factory(), executor)

    with structlog.testing.capture_logs() as logs:
        finalised = await service.execute_scheduled_erasures(datetime.now(UTC))

    assert finalised == 0
    assert erasure.status == "partially_completed"
    # A configuration fault, not a failure of this request (#1666 semantics).
    assert erasure.attempt_count == 0
    assert erasure.next_attempt_at is None
    assert erasure.pre_arango_completed_at is None
    assert executor.runs == []
    assert "reference" in (erasure.error_message or "").lower()
    assert [e for e in logs if e["log_level"] == "error"], "the held duty must be loud"


@pytest.mark.parametrize("store_factory", [_noop_with_contributions, lambda: None], ids=["noop+marker", "unwired"])
async def test_a_direct_finalize_records_a_failed_attempt(store_factory):
    erasure = _erasure()
    executor = RecordingErasureExecutor()
    service = _privacy_service(erasure, store_factory(), executor)

    assert await service._finalize_erasure(erasure, datetime.now(UTC)) is False

    assert erasure.status == "partially_completed"
    assert erasure.attempt_count == 1
    assert erasure.pre_arango_completed_at is None
    assert executor.runs == []


@pytest.mark.parametrize("store_factory", [_noop_with_contributions, lambda: None], ids=["noop+marker", "unwired"])
async def test_erase_account_refuses_before_touching_anything(store_factory):
    executor = RecordingErasureExecutor()
    storage = MagicMock()
    storage.delete_for_user = AsyncMock(return_value=StorageErasureResult(removed=0))
    service = _privacy_service(_erasure(), store_factory(), executor)
    service._storage_adapter = storage

    with pytest.raises(FeatureNotConfiguredError):
        await service.erase_account(SUBJECT)

    storage.delete_for_user.assert_not_awaited()
    assert executor.runs == []


async def test_a_retry_past_the_checkpoint_does_not_need_the_index():
    """Phase 0.5 already ran for this request; only the ArangoDB plan is left."""
    executor = RecordingErasureExecutor()
    service = _privacy_service(_erasure(), _noop_with_contributions(), executor)

    report = await service.erase_account(SUBJECT, pre_arango_completed=True)

    assert len(executor.runs) == 1
    assert report.reference_index_binding is None


def test_tenant_deletion_refuses_while_contributions_are_unreachable():
    storage = MagicMock()
    storage.delete_prefix = AsyncMock(return_value=0)
    service = _tenant_service(_noop_with_contributions(), storage=storage)

    with pytest.raises(FeatureNotConfiguredError):
        service.delete_tenant(TENANT, **authorized(TENANT))

    assert service._tenant_erasure_executor.plans == []
    assert service._tenant_erasure_repo.records == {}
    service._membership_repo.deactivate_all_for_tenant.assert_not_called()
    storage.delete_prefix.assert_not_awaited()
