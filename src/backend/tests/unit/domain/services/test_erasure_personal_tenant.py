"""#1788 — the account erasure runs the tenant-erasure inventory on the subject's personal tenant.

Before #1788 ``PrivacyService.erase_account`` kept the personal tenant created at
registration (REQ-024): the ``tenants`` rule replaced its owner and renamed it,
and no path ever deleted it, so the subject's own garden — sites with
coordinates, plants, diary text, tasks — outlived the account. The tenant-erasure
inventory of #1769 was never called from the account erasure.

Pinned here through the production entries (:meth:`PrivacyService.erase_account_now`
and the daily beat :meth:`PrivacyService.execute_scheduled_erasures`) with the
faithful :class:`FakeErasureRepo` and :class:`FakePersonalTenants`:

* the personal tenant is erased **before** the account's ArangoDB plan, which
  replaces the owner reference the tenant is found by;
* the request is ``completed`` only when every personal tenant is accounted for,
  and names each one with what happened to it;
* a personal tenant another account uses is kept, with the reason recorded;
* a deployment that cannot erase a tenant is held before anything changes;
* a failed tenant erasure leaves the request open, and the retry still reaches
  the tenant through the keys the request recorded.

The :class:`TenantService` side (which tenant is erased, which is kept) is
pinned in ``TestTheTenantServiceDecides`` over its repositories.
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantType
from app.common.exceptions import (
    ExternalSourceError,
    FeatureNotConfiguredError,
    ForbiddenError,
    TenantErasureIncompleteError,
    ValidationError,
    WriteConflictError,
)
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.privacy import ErasureRequest
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantErasureRecord
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.tenant_service import TenantService
from tests.support.privacy_doubles import FakeErasureRepo, FakePersonalTenants, RecordingErasureExecutor

SALT = "s" * 32
LOG_SALT = "log-pseudonym-test-salt-not-a-secret-01234"


@pytest.fixture(autouse=True)
def _log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """#1812: log pseudonyms are keyed with LOG_PSEUDONYM_SALT, not with the tombstone salt the services get."""
    from app.config.settings import settings

    monkeypatch.setattr(settings, "log_pseudonym_salt", LOG_SALT)


USER = "u-1"
PERSONAL = "t-personal"
NOW = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)


def _service(
    repo: FakeErasureRepo,
    executor: RecordingErasureExecutor,
    tenants: FakePersonalTenants | None,
) -> PrivacyService:
    export_repo = MagicMock()
    export_repo.list_by_user.return_value = []
    user_repo = MagicMock()
    user_repo.get_by_key.return_value = SimpleNamespace(key=USER, email_verified=False)
    kwargs: dict[str, Any] = {
        "export_repo": export_repo,
        "consent_repo": MagicMock(),
        "restriction_repo": MagicMock(),
        "erasure_repo": repo,
        "email_change_repo": MagicMock(),
        "user_repo": user_repo,
        "refresh_token_repo": MagicMock(),
        "data_export_engine": DataExportEngine(),
        "erasure_engine": ErasureEngine(),
        "consent_engine": ConsentEngine(),
        "password_engine": MagicMock(),
        "token_engine": MagicMock(),
        "email_service": MagicMock(),
        "frontend_url": "https://app.test",
        "reference_index_store": NoopReferenceIndexStore(),
        "erasure_executor": executor,
        "tenant_service": tenants,
        "tombstone_salt": SALT,
    }
    # Ran red against the service before #1788, which took no tenant service:
    # the assertions below said so, not a TypeError.
    accepted = inspect.signature(PrivacyService).parameters
    return PrivacyService(**{name: value for name, value in kwargs.items() if name in accepted})


def _ordered(tenants: FakePersonalTenants, executor: RecordingErasureExecutor) -> None:
    inner = executor.run_erasure_plan

    def _run(plan, *, tombstone, executors=None):  # type: ignore[no-untyped-def]
        tenants.events.append("account-plan")
        return inner(plan, tombstone=tombstone, executors=executors)

    executor.run_erasure_plan = _run  # type: ignore[method-assign]


def _only(repo: FakeErasureRepo) -> ErasureRequest:
    (request,) = repo.stored.values()
    return request


@pytest.mark.asyncio
class TestTheAccountErasureTakesThePersonalTenant:
    async def test_the_personal_tenant_is_erased_before_the_account_plan(self):
        repo, executor, tenants = FakeErasureRepo(), RecordingErasureExecutor(), FakePersonalTenants(PERSONAL)
        _ordered(tenants, executor)

        await _service(repo, executor, tenants).erase_account_now(USER, origin="platform_admin", now=NOW)

        assert tenants.erased == [PERSONAL]
        assert tenants.events == [f"tenant:{PERSONAL}", "account-plan"]

    async def test_the_completed_request_names_the_tenant_and_its_deletion_record(self):
        repo = FakeErasureRepo()
        tenants = FakePersonalTenants(PERSONAL)

        await _service(repo, RecordingErasureExecutor(), tenants).erase_account_now(
            USER, origin="platform_admin", now=NOW
        )

        request = _only(repo)
        assert request.status == "completed"
        assert request.personal_tenant_keys == [PERSONAL]
        assert [(t.tenant_key, t.outcome, t.tenant_erasure_record_key) for t in request.personal_tenants] == [
            (PERSONAL, "erased", TenantErasureEngine.record_key(PERSONAL))
        ]

    async def test_a_personal_tenant_someone_else_uses_is_kept_and_the_reason_recorded(self):
        repo = FakeErasureRepo()
        tenants = FakePersonalTenants(PERSONAL, others={PERSONAL: 1})

        await _service(repo, RecordingErasureExecutor(), tenants).erase_account_now(
            USER, origin="platform_admin", now=NOW
        )

        request = _only(repo)
        assert tenants.erased == []
        assert request.status == "completed"
        (outcome,) = request.personal_tenants
        assert (outcome.outcome, bool(outcome.reason)) == ("retained_other_members", True)

    async def test_a_deployment_that_cannot_erase_a_tenant_changes_nothing(self):
        repo, executor = FakeErasureRepo(), RecordingErasureExecutor()
        tenants = FakePersonalTenants(PERSONAL, configuration_error="No sensor-reading store is wired.")

        with pytest.raises(FeatureNotConfiguredError):
            await _service(repo, executor, tenants).erase_account_now(USER, origin="platform_admin", now=NOW)

        assert repo.stored == {}
        assert executor.runs == []
        assert tenants.calls == []

    async def test_no_tenant_service_is_a_configuration_error_too(self):
        repo, executor = FakeErasureRepo(), RecordingErasureExecutor()

        with pytest.raises(FeatureNotConfiguredError):
            await _service(repo, executor, None).erase_account_now(USER, origin="platform_admin", now=NOW)

        assert repo.stored == {}
        assert executor.runs == []

    async def test_a_failed_tenant_erasure_leaves_the_request_open_and_the_account_plan_unrun(self):
        repo, executor = FakeErasureRepo(), RecordingErasureExecutor()
        tenants = FakePersonalTenants(PERSONAL, fail_with=ExternalSourceError("inference-service", "down"))

        with pytest.raises(ExternalSourceError):
            await _service(repo, executor, tenants).erase_account_now(USER, origin="platform_admin", now=NOW)

        request = _only(repo)
        assert request.status == "partially_completed"
        assert request.attempt_count == 1
        assert request.personal_tenant_keys == [PERSONAL], "recorded before the tenant was touched"
        assert executor.runs == []

    async def test_the_retry_reaches_a_tenant_the_owner_listing_no_longer_shows(self):
        """The first attempt erased the tenant, then the account plan failed; the retry must still prove it."""
        tenants = FakePersonalTenants(PERSONAL)
        repo = FakeErasureRepo()
        failing = RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted"))
        with pytest.raises(RuntimeError):
            await _service(repo, failing, tenants).erase_account_now(USER, origin="platform_admin", now=NOW)
        assert tenants.owned == [], "the tenant is gone, so listing by owner finds nothing"

        request = _only(repo)
        retry_clock = request.next_attempt_at + timedelta(minutes=1)
        finalised = await _service(repo, RecordingErasureExecutor(), tenants).execute_scheduled_erasures(retry_clock)

        assert finalised == 1
        request = _only(repo)
        assert request.status == "completed"
        assert [(t.tenant_key, t.outcome) for t in request.personal_tenants] == [(PERSONAL, "erased")]

    async def test_the_daily_beat_erases_the_personal_tenant_of_a_self_service_request(self):
        request = ErasureRequest(
            _key="e-1",
            user_key=USER,
            status="scheduled",
            hard_delete_scheduled_at=NOW - timedelta(days=1),
        )
        repo, tenants = FakeErasureRepo(request), FakePersonalTenants(PERSONAL)

        finalised = await _service(repo, RecordingErasureExecutor(), tenants).execute_scheduled_erasures(NOW)

        assert finalised == 1
        assert tenants.erased == [PERSONAL]
        assert _only(repo).status == "completed"

    async def test_the_daily_beat_holds_every_request_while_tenants_cannot_be_erased(self):
        request = ErasureRequest(
            _key="e-1",
            user_key=USER,
            status="scheduled",
            hard_delete_scheduled_at=NOW - timedelta(days=1),
        )
        repo, executor = FakeErasureRepo(request), RecordingErasureExecutor()
        tenants = FakePersonalTenants(PERSONAL, configuration_error="Set ERASURE_TOMBSTONE_SALT.")

        finalised = await _service(repo, executor, tenants).execute_scheduled_erasures(NOW)

        assert finalised == 0
        assert executor.runs == []
        assert tenants.calls == []
        held = _only(repo)
        assert held.status == "partially_completed"
        assert held.attempt_count == 0, "a configuration hold spends no attempt (#1666)"


def _tenant_service(
    *,
    tenant: Tenant | None,
    record: TenantErasureRecord | None = None,
    members: list[str] | None = None,
) -> tuple[TenantService, MagicMock]:
    tenant_repo = MagicMock()
    tenant_repo.get_by_key.return_value = tenant
    tenant_repo.list_by_owner.return_value = [tenant] if tenant is not None else []
    membership_repo = MagicMock()
    membership_repo.active_member_user_keys.return_value = members if members is not None else [USER]
    erasure_repo = MagicMock()
    erasure_repo.get.return_value = record
    service = TenantService(
        tenant_repo=tenant_repo,
        membership_repo=membership_repo,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=MagicMock(),
        membership_engine=MagicMock(),
        invitation_engine=MagicMock(),
        tenant_erasure_executor=MagicMock(),
        tenant_erasure_repo=erasure_repo,
        tombstone_salt=SALT,
    )
    delete = MagicMock(
        return_value=TenantErasureRecord(tenant_key=PERSONAL, tenant_type="personal", origin="account_erasure")
    )
    delete.return_value.status = "completed"
    service._erase_tenant_for_account_erasure = delete  # type: ignore[method-assign]
    return service, delete


def _personal(owner: str = USER, tenant_type: TenantType = TenantType.PERSONAL) -> Tenant:
    return Tenant(_key=PERSONAL, name="Garden", slug="garden", tenant_type=tenant_type, owner_user_key=owner)


class TestTheTenantServiceDecides:
    def test_the_personal_tenants_are_listed_by_owner_and_type_in_the_query(self):
        service, _ = _tenant_service(tenant=_personal())
        service._tenant_repo.personal_tenant_keys_by_owner.return_value = [PERSONAL]

        assert service.personal_tenant_keys_of(USER) == [PERSONAL]
        service._tenant_repo.personal_tenant_keys_by_owner.assert_called_once_with(USER)

    def test_the_sole_member_tenant_goes_through_the_tenant_inventory(self):
        tenant = _personal()
        service, delete = _tenant_service(tenant=tenant, members=[USER])

        outcome = service.erase_personal_tenant_of(USER, PERSONAL, now=NOW)

        delete.assert_called_once_with(PERSONAL, tenant, None, subject_user_key=USER, now=NOW)
        assert (outcome.outcome, outcome.tenant_erasure_record_key) == (
            "erased",
            TenantErasureEngine.record_key(PERSONAL),
        )

    def test_another_active_member_keeps_the_tenant(self):
        service, delete = _tenant_service(tenant=_personal(), members=[USER, "u-2"])

        outcome = service.erase_personal_tenant_of(USER, PERSONAL, now=NOW)

        delete.assert_not_called()
        assert outcome.outcome == "retained_other_members"
        assert "1 other active member" in (outcome.reason or "")

    def test_an_open_deletion_is_resumed_whatever_the_frozen_memberships_say(self):
        record = TenantErasureRecord(
            tenant_key=PERSONAL, tenant_type="personal", origin="account_erasure", status="partially_completed"
        )
        service, delete = _tenant_service(tenant=None, record=record, members=["u-2"])

        outcome = service.erase_personal_tenant_of(USER, PERSONAL, now=NOW)

        delete.assert_called_once()
        assert outcome.outcome == "erased"

    def test_a_completed_deletion_is_not_run_again(self):
        record = TenantErasureRecord(
            tenant_key=PERSONAL, tenant_type="personal", origin="tenant_management", status="completed"
        )
        service, delete = _tenant_service(tenant=None, record=record)

        assert service.erase_personal_tenant_of(USER, PERSONAL).outcome == "erased"
        delete.assert_not_called()

    def test_nothing_left_is_absent(self):
        service, delete = _tenant_service(tenant=None)

        assert service.erase_personal_tenant_of(USER, PERSONAL).outcome == "absent"
        delete.assert_not_called()

    def test_a_tenant_that_is_not_the_subjects_personal_one_stops_the_erasure(self):
        service, delete = _tenant_service(tenant=_personal(owner="someone-else"))

        with pytest.raises(ValidationError):
            service.erase_personal_tenant_of(USER, PERSONAL)
        delete.assert_not_called()

    def test_a_retry_after_the_account_plan_handed_the_tenant_over_does_not_fail(self):
        """#1788 code review — the plan replaced the owner of a retained tenant; the retry keeps it retained."""
        from app.domain.engines.erasure_engine import ANONYMIZED_MARKER

        service, delete = _tenant_service(tenant=_personal(owner=ANONYMIZED_MARKER), members=["u-2"])

        outcome = service.erase_personal_tenant_of(USER, PERSONAL)

        assert outcome.outcome == "retained_other_members"
        delete.assert_not_called()

    def test_an_incomplete_deletion_is_not_reported_erased(self):
        service, delete = _tenant_service(tenant=_personal())
        delete.return_value.status = "partially_completed"
        delete.return_value.unreached = ["undeclared:legacy"]

        with pytest.raises(TenantErasureIncompleteError):
            service.erase_personal_tenant_of(USER, PERSONAL)


class TestTheAccountErasurePathKeepsTheTenantDeletionsProof:
    """``_erase_tenant_for_account_erasure`` — the record, claim, freeze and run of ``delete_tenant``."""

    def _service(self, *, light_mode: bool = False, configuration_error: str | None = None):
        erasure_repo = MagicMock()
        claimed = TenantErasureRecord(tenant_key=PERSONAL, tenant_type="personal", origin="account_erasure")
        erasure_repo.claim_for_run.return_value = claimed
        membership_repo = MagicMock()
        service = TenantService(
            tenant_repo=MagicMock(),
            membership_repo=membership_repo,
            invitation_repo=MagicMock(),
            assignment_repo=MagicMock(),
            tenant_engine=MagicMock(),
            membership_engine=MagicMock(),
            invitation_engine=MagicMock(),
            tenant_erasure_executor=MagicMock(),
            tenant_erasure_repo=erasure_repo,
            tombstone_salt=SALT,
            light_mode=light_mode,
        )
        service._tenant_erasure_configuration_error = MagicMock(return_value=configuration_error)  # type: ignore[method-assign]
        run = MagicMock(return_value=claimed.model_copy(update={"status": "completed"}))
        service._run_tenant_erasure = run  # type: ignore[method-assign]
        return service, erasure_repo, membership_repo, run, claimed

    def test_it_persists_an_account_erasure_record_then_claims_freezes_and_runs(self):
        service, erasure_repo, membership_repo, run, claimed = self._service()

        finished = service._erase_tenant_for_account_erasure(
            PERSONAL, _personal(), None, subject_user_key=USER, now=NOW
        )

        (created, key), _ = erasure_repo.create_with_key.call_args
        assert (created.origin, created.tenant_key, key) == (
            "account_erasure",
            PERSONAL,
            TenantErasureEngine.record_key(PERSONAL),
        )
        membership_repo.deactivate_all_for_tenant.assert_called_once_with(PERSONAL)
        run.assert_called_once_with(claimed, NOW, raise_on_failure=True)
        # #1791 provenance fields, stated for a deletion nobody asked for interactively.
        assert created.step_up == "account_erasure_no_interactive_step_up"
        assert created.requested_by_subject == ErasureEngine.log_subject(USER, LOG_SALT)
        assert USER not in created.requested_by_subject
        assert created.slug_digest == service._tenant_slug_digest(_personal().slug)
        assert finished.status == "completed"

    def test_an_open_record_is_resumed_not_recreated(self):
        service, erasure_repo, _, run, _ = self._service()
        open_record = TenantErasureRecord(
            tenant_key=PERSONAL, tenant_type="personal", origin="account_erasure", status="partially_completed"
        )

        service._erase_tenant_for_account_erasure(PERSONAL, None, open_record, subject_user_key=USER, now=NOW)

        erasure_repo.create_with_key.assert_not_called()
        run.assert_called_once()

    def test_a_deployment_that_cannot_erase_changes_nothing(self):
        service, erasure_repo, membership_repo, run, _ = self._service(configuration_error="no store")

        with pytest.raises(FeatureNotConfiguredError):
            service._erase_tenant_for_account_erasure(PERSONAL, _personal(), None, subject_user_key=USER, now=NOW)

        erasure_repo.create_with_key.assert_not_called()
        membership_repo.deactivate_all_for_tenant.assert_not_called()
        run.assert_not_called()

    def test_a_held_claim_is_a_conflict_and_nothing_runs(self):
        service, erasure_repo, membership_repo, run, _ = self._service()
        erasure_repo.claim_for_run.return_value = None

        with pytest.raises(WriteConflictError):
            service._erase_tenant_for_account_erasure(PERSONAL, _personal(), None, subject_user_key=USER, now=NOW)

        membership_repo.deactivate_all_for_tenant.assert_not_called()
        run.assert_not_called()

    def test_the_light_mode_tenant_is_refused(self):
        service, erasure_repo, _, run, _ = self._service(light_mode=True)

        with pytest.raises(ForbiddenError):
            service._erase_tenant_for_account_erasure(PERSONAL, _personal(), None, subject_user_key=USER, now=NOW)

        erasure_repo.create_with_key.assert_not_called()
        run.assert_not_called()
