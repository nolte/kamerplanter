"""#2123 (MT-027, REQ-024 AK-52) — a tenant deletion is scheduled, cancellable, and erased only after its grace.

Until #2123 ``delete_tenant`` froze every membership and dispatched the erasure at
once: a misclick by the management (or a platform admin) was an irreversible loss,
and the members had no window to export what was theirs (Art. 20). These tests
drive the status model that replaced ``is_active`` and the grace around it:

* the request schedules — nothing erased, no membership touched, no dispatch;
* a stray dispatch and the beat leave a scheduled record alone until it is due;
* after the grace the beat claims it and the tenant becomes ``deleted``;
* the management (lead + ``management``) or a platform admin cancels with a step-up
  and every membership is back as it was;
* ``Tenant.is_active`` is ``True`` for ``active`` only — every other state resolves
  for nobody through the #2105 resolvers.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import AdminScope, TenantRole, TenantStatus
from app.common.exceptions import ForbiddenError, InvalidStatusTransitionError
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantErasureCancelConfirmation
from app.domain.models.user import User
from tests.support.tenant_erasure_doubles import (
    AUTHORIZED_REQUESTER,
    FakeTenantErasureRepository,
    RecordingTenantErasureExecutor,
    authorized,
    tenant_service_for_deletion,
)

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
GRACE_DAYS = 90
KEY = "t-1"
RECORD = TenantErasureEngine.record_key(KEY)


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


class _TenantStore:
    """The tenant document as ``update_fields`` / ``get_by_key`` see it — the state round-trips."""

    def __init__(self, tenant: Tenant) -> None:
        self.doc = tenant

    def repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_by_key.side_effect = lambda key: self.doc if key == self.doc.key else None
        repo.get_by_slug.side_effect = lambda slug: self.doc if slug == self.doc.slug else None

        def update_fields(key: str, fields: dict[str, Any]) -> Tenant | None:
            if key != self.doc.key:
                return None
            self.doc = Tenant.model_validate({**self.doc.model_dump(by_alias=True), **fields})
            return self.doc

        repo.update_fields.side_effect = update_fields
        return repo


def _org(status: TenantStatus = TenantStatus.ACTIVE) -> Tenant:
    return Tenant.model_validate(
        {
            "_key": KEY,
            "name": "Lindenhof",
            "slug": KEY,
            "tenant_type": "organization",
            "owner_user_key": "owner-1",
            "status": status,
        }
    )


def _service(*, grace_days: int = GRACE_DAYS, store: _TenantStore | None = None, **overrides: Any):  # type: ignore[no-untyped-def]
    store = store or _TenantStore(_org())
    executor = overrides.pop("executor", RecordingTenantErasureExecutor())
    repo = overrides.pop("record_repo", FakeTenantErasureRepository())
    service = tenant_service_for_deletion(
        executor=executor,
        record_repo=repo,
        tenant_repo=store.repo(),
        tenant_erasure_grace_days=grace_days,
        **overrides,
    )
    return service, store, executor, repo


def _cancel_kwargs(*, origin: str = "tenant_management", api_key: bool = False) -> dict[str, Any]:
    from app.domain.services.step_up_service import default_step_up_verifier
    from tests.support.step_up import AdmitEveryTarget

    code, _ = default_step_up_verifier(target_policy=AdmitEveryTarget()).issue_code(
        AUTHORIZED_REQUESTER,
        action="tenant_erasure_cancel",
        target=KEY,
        authenticated_with_api_key=False,
        client_ip="203.0.113.10",
    )
    return {
        "requester": AUTHORIZED_REQUESTER,
        "authenticated_with_api_key": api_key,
        "confirmation": TenantErasureCancelConfirmation(step_up_code=code),
        "origin": origin,
        "client_ip": "203.0.113.10",
    }


# ── The status model ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("status", list(TenantStatus))
def test_only_an_active_tenant_is_active(status: TenantStatus) -> None:
    assert _org(status).is_active is (status == TenantStatus.ACTIVE)


def test_the_stored_document_carries_the_status_and_no_bool() -> None:
    dumped = _org(TenantStatus.SUSPENDED).model_dump(by_alias=True)

    assert dumped["status"] == "suspended"
    assert "is_active" not in dumped


# ── The request schedules ────────────────────────────────────────────────────


class TestTheRequestSchedules:
    def test_nothing_is_erased_no_membership_frozen_and_nothing_dispatched(self) -> None:
        service, store, executor, repo = _service()

        accepted = service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert accepted.status == "scheduled"
        assert accepted.scheduled_for == NOW + timedelta(days=GRACE_DAYS)
        assert executor.plans == []
        assert service.dispatched == []
        service._membership_repo.deactivate_all_for_tenant.assert_not_called()
        assert repo.records[RECORD]["last_attempt_at"] is None

    def test_the_tenant_is_pending_deletion_until_the_scheduled_date(self) -> None:
        service, store, _executor, _repo = _service()

        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert store.doc.status == TenantStatus.PENDING_DELETION
        assert store.doc.deletion_scheduled_at == NOW + timedelta(days=GRACE_DAYS)
        assert store.doc.is_active is False  # resolves for nobody (#2105)

    def test_the_members_are_told_the_date_except_the_requester(self) -> None:
        mailer = MagicMock()
        users = MagicMock()
        users.get_by_key.side_effect = lambda key: User.model_validate(
            {"_key": key, "email": f"{key}@example.org", "display_name": key}
        )
        service, _store, _executor, _repo = _service(email_service=mailer, user_repo=users)
        service._membership_repo.active_member_user_keys.return_value = [AUTHORIZED_REQUESTER.key, "member-2"]

        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        (call,) = mailer.send_notification_email.call_args_list
        assert call.kwargs["to_email"] == "member-2@example.org"
        body = call.kwargs["html_body"]
        assert (NOW + timedelta(days=GRACE_DAYS)).strftime("%Y-%m-%d") in body
        assert "Lindenhof" in body  # an organisation is named ...
        assert "personal data export" in body  # ... and the Art. 20 window is offered

    def test_a_failing_mailbox_does_not_undo_the_schedule(self) -> None:
        mailer = MagicMock()
        mailer.send_notification_email.side_effect = OSError("smtp down")
        users = MagicMock()
        users.get_by_key.return_value = User.model_validate(
            {"_key": "m", "email": "m@example.org", "display_name": "M"}
        )
        service, store, _executor, _repo = _service(email_service=mailer, user_repo=users)
        service._membership_repo.active_member_user_keys.return_value = ["member-2"]

        accepted = service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert accepted.status == "scheduled"
        assert store.doc.status == TenantStatus.PENDING_DELETION

    def test_a_repeated_request_inside_the_grace_keeps_the_first_date(self) -> None:
        service, store, _executor, _repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        again = service.delete_tenant(KEY, **authorized(KEY), now=NOW + timedelta(days=10))

        assert again.scheduled_for == NOW + timedelta(days=GRACE_DAYS)
        assert store.doc.deletion_scheduled_at == NOW + timedelta(days=GRACE_DAYS)
        assert service.dispatched == []

    def test_a_zero_grace_keeps_the_immediate_erasure(self) -> None:
        service, store, _executor, _repo = _service(grace_days=0)

        accepted = service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert accepted.status == "in_progress"
        assert service.dispatched == [RECORD]
        service._membership_repo.deactivate_all_for_tenant.assert_called_once_with(KEY)
        assert store.doc.status == TenantStatus.DELETED

    def test_an_unwired_grace_reads_the_setting_default_of_ninety_days(self) -> None:
        from app.config.settings import Settings

        assert Settings().retention_tenant_erasure_grace_days == 90
        service, _store, _executor, _repo = _service(grace_days=None)  # type: ignore[arg-type]

        assert service.delete_tenant(KEY, **authorized(KEY), now=NOW).status == "scheduled"


# ── Only after the grace ─────────────────────────────────────────────────────


class TestOnlyAfterTheGrace:
    def test_a_stray_dispatch_inside_the_grace_runs_nothing(self) -> None:
        service, store, executor, _repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        outcome = service.run_tenant_erasure_task(RECORD, NOW + timedelta(days=1))

        assert outcome["outcome"] == "scheduled"
        assert executor.plans == []
        assert store.doc.status == TenantStatus.PENDING_DELETION

    def test_the_beat_leaves_it_alone_until_the_grace_has_ended(self) -> None:
        service, _store, executor, _repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        early = service.resume_tenant_erasures(NOW + timedelta(days=GRACE_DAYS) - timedelta(minutes=1))

        assert early["candidates"] == 0
        assert executor.plans == []

    def test_after_the_grace_the_beat_freezes_marks_deleted_and_erases(self) -> None:
        service, store, executor, repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        due = service.resume_tenant_erasures(NOW + timedelta(days=GRACE_DAYS, minutes=1))

        assert due["completed"] == 1
        assert [plan.tenant_key for plan in executor.plans] == [KEY]
        service._membership_repo.deactivate_all_for_tenant.assert_called_once_with(KEY)
        assert store.doc.status == TenantStatus.DELETED
        assert repo.records[RECORD]["status"] == "completed"


# ── Cancellation ─────────────────────────────────────────────────────────────


class TestCancellation:
    def test_the_management_cancels_and_the_tenant_is_active_again(self) -> None:
        service, store, executor, repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        restored = service.cancel_tenant_erasure(KEY, **_cancel_kwargs())

        assert restored.status == TenantStatus.ACTIVE
        assert restored.deletion_scheduled_at is None
        assert RECORD not in repo.records
        # nothing ran afterwards either
        service.resume_tenant_erasures(NOW + timedelta(days=GRACE_DAYS + 1))
        assert executor.plans == []
        service._membership_repo.deactivate_all_for_tenant.assert_not_called()

    def test_a_platform_admin_cancels_too(self) -> None:
        service, store, _executor, _repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        service.cancel_tenant_erasure(KEY, **_cancel_kwargs(origin="platform_admin"))

        assert store.doc.status == TenantStatus.ACTIVE

    def test_the_slug_route_cancels_through_the_same_rule(self) -> None:
        service, store, _executor, _repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        service.cancel_tenant_erasure_by_slug(KEY, **_cancel_kwargs())

        assert store.doc.status == TenantStatus.ACTIVE

    def test_an_unknown_slug_answers_like_a_forbidden_tenant(self) -> None:
        service, _store, _executor, _repo = _service()

        kwargs = _cancel_kwargs()
        with pytest.raises(ForbiddenError) as unknown:
            service.cancel_tenant_erasure_by_slug("no-such-garden", **kwargs)
        outsider = User.model_validate({"_key": "outsider", "email": "o@example.org", "display_name": "O"})
        with pytest.raises(ForbiddenError) as forbidden:
            service.cancel_tenant_erasure_by_slug(KEY, **{**kwargs, "requester": outsider})

        assert str(unknown.value) == str(forbidden.value)

    @pytest.mark.parametrize(
        ("role", "scopes"),
        [(TenantRole.LEAD, []), (TenantRole.GROWER, [AdminScope.MANAGEMENT]), (TenantRole.VIEWER, [])],
    )
    def test_without_lead_and_management_nobody_cancels(self, role: TenantRole, scopes: list[AdminScope]) -> None:
        memberships = MagicMock()
        memberships.get_by_user_and_tenant.return_value = Membership(
            user_key=AUTHORIZED_REQUESTER.key or "", tenant_key=KEY, role=role, admin_scopes=scopes
        )
        service, store, _executor, _repo = _service(membership_repo=memberships)
        store.doc = _org(TenantStatus.PENDING_DELETION)

        with pytest.raises(ForbiddenError):
            service.cancel_tenant_erasure(KEY, **_cancel_kwargs())
        assert store.doc.status == TenantStatus.PENDING_DELETION

    def test_never_with_an_api_key(self) -> None:
        service, store, _executor, _repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        with pytest.raises(ForbiddenError):
            service.cancel_tenant_erasure(KEY, **_cancel_kwargs(api_key=True))
        assert store.doc.status == TenantStatus.PENDING_DELETION

    def test_a_wrong_step_up_changes_nothing(self) -> None:
        from app.common.exceptions import UnauthorizedError

        service, store, _executor, repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        kwargs = {**_cancel_kwargs(), "confirmation": TenantErasureCancelConfirmation(step_up_code="00000000")}

        with pytest.raises(UnauthorizedError):
            service.cancel_tenant_erasure(KEY, **kwargs)
        assert store.doc.status == TenantStatus.PENDING_DELETION
        assert RECORD in repo.records

    def test_once_the_run_holds_it_nothing_is_cancelled(self) -> None:
        service, store, _executor, repo = _service(executor=RecordingTenantErasureExecutor(unreached=["sites"]))
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        service.resume_tenant_erasures(NOW + timedelta(days=GRACE_DAYS + 1))  # claimed, residue left: open

        with pytest.raises(InvalidStatusTransitionError):
            service.cancel_tenant_erasure(KEY, **_cancel_kwargs())
        assert store.doc.status == TenantStatus.DELETED
        assert RECORD in repo.records

    def test_a_claim_between_the_read_and_the_remove_wins(self) -> None:
        service, store, _executor, repo = _service()
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        repo.records[RECORD].update(status="in_progress", last_attempt_at=NOW.isoformat())  # the beat's claim

        with pytest.raises(InvalidStatusTransitionError):
            service.cancel_tenant_erasure(KEY, **_cancel_kwargs())
        assert RECORD in repo.records
        assert store.doc.status == TenantStatus.PENDING_DELETION  # the run marks it ``deleted`` next

    def test_an_active_tenant_has_nothing_to_cancel(self) -> None:
        service, _store, _executor, _repo = _service()

        with pytest.raises(InvalidStatusTransitionError):
            service.cancel_tenant_erasure(KEY, **_cancel_kwargs())


# ── The admin's suspension switch ────────────────────────────────────────────


class TestTheSuspensionSwitch:
    def _admin_update(self, service, is_active: bool):  # type: ignore[no-untyped-def]
        service._step_up_verifier = MagicMock()
        return service.admin_update_tenant(
            KEY,
            {"is_active": is_active},
            requester=AUTHORIZED_REQUESTER,
            current_password=None,
            step_up_code=None,
            step_up_token=None,
            authenticated_with_api_key=False,
            client_ip=None,
        )

    def test_deactivating_suspends_and_reactivating_restores(self) -> None:
        service, store, _executor, _repo = _service()

        self._admin_update(service, False)
        assert store.doc.status == TenantStatus.SUSPENDED
        self._admin_update(service, True)
        assert store.doc.status == TenantStatus.ACTIVE

    @pytest.mark.parametrize("status", [TenantStatus.PENDING_DELETION, TenantStatus.ORPHANED, TenantStatus.DELETED])
    def test_a_tenant_whose_deletion_is_scheduled_or_running_is_not_reactivated(self, status: TenantStatus) -> None:
        service, store, _executor, _repo = _service()
        store.doc = _org(status)

        with pytest.raises(InvalidStatusTransitionError):
            self._admin_update(service, True)
        assert store.doc.status == status

    def test_the_tenant_update_path_refuses_every_lifecycle_field(self) -> None:
        service, _store, _executor, _repo = _service()

        for field, value in (("status", "active"), ("deletion_scheduled_at", None), ("is_active", True)):
            with pytest.raises(ValueError, match="lifecycle"):
                service.update_tenant(KEY, {field: value})


@pytest.mark.parametrize(
    ("legacy", "expected"),
    [
        ({"is_active": False}, TenantStatus.SUSPENDED),
        ({"is_active": True}, TenantStatus.ACTIVE),
        ({"is_active": False, "status": "pending_deletion"}, TenantStatus.PENDING_DELETION),
    ],
)
def test_a_document_still_carrying_the_retired_bool_never_reads_active_when_it_was_not(
    legacy: dict[str, Any], expected: TenantStatus
) -> None:
    doc = {"_key": KEY, "name": "Lindenhof", "slug": KEY, "owner_user_key": "owner-1", **legacy}

    assert Tenant.model_validate(doc).status == expected
