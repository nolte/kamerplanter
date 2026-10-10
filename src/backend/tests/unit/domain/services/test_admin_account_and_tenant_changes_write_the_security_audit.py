"""MT-014 (#2111): a platform admin's change of an account's trust flags and every change of a tenant's
lifecycle leave one persistent audit row.

#2149 closed the membership class. What stayed unrecorded: ``UserService.admin_update_user``
deactivating, reactivating, verifying or un-verifying an account, ``TenantService.admin_update_tenant``
suspending or reactivating a tenant, and ``TenantService.delete_tenant`` / ``cancel_tenant_erasure``
accepting or withdrawing a tenant's deletion - the withdrawal even removes the erasure record, so before
this nothing at all was left of the request.

The services run with their real wiring; the audit repository is an in-memory double that keeps the rows
it was handed, so what is asserted is the *row* - who, whom or which tenant, which door, no personal data
- not that a method was called. The class guard
``tests/unit/guards/test_account_and_tenant_mutations_write_the_security_audit.py`` holds that no sibling
skips it; the real collection is exercised in ``tests/integration/test_security_audit_log_reach.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.enums import SecurityAuditAction, SecurityAuditVia, TenantStatus
from app.common.exceptions import NotFoundError, UnauthorizedError, ValidationError
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.interfaces.security_audit_repository import ISecurityAuditRepository
from app.domain.models.security_audit import SecurityAuditEntry
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantErasureCancelConfirmation
from app.domain.models.user import User
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.user_service import UserService
from tests.support.step_up import STEP_UP_PASSED, PassedStepUpVerifier
from tests.support.tenant_erasure_doubles import AUTHORIZED_REQUESTER, authorized, tenant_service_for_deletion

NOW = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
KEY = "t-1"
ADMIN = User(_key="admin-1", email="admin-1@example.org", display_name="Admin One")


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


class _AuditRepo(ISecurityAuditRepository):
    def __init__(self, *, fail: bool = False) -> None:
        self.rows: list[SecurityAuditEntry] = []
        self._fail = fail

    def record(self, entry: SecurityAuditEntry) -> str:
        if self._fail:
            raise ConnectionError("audit store down")
        self.rows.append(entry)
        return f"audit-{len(self.rows)}"

    def list_recent(self, *, tenant_key: str | None = None, limit: int = 100) -> list[SecurityAuditEntry]:
        return [r for r in reversed(self.rows) if tenant_key is None or r.tenant_key == tenant_key][:limit]

    def delete_expired(self, *, retention_days: int) -> int:
        return 0

    def count_undated(self) -> int:
        return 0


def _assert_no_personal_data(row: SecurityAuditEntry, *people: User) -> None:
    """NFR-011 R-38: the row names accounts by their opaque key only - no address, no name."""
    dumped = str(row.model_dump(mode="json"))
    assert "@" not in dumped
    for person in people:
        assert person.display_name not in dumped


# ── Accounts: UserService.admin_update_user ──────────────────────────────────


def _target(*, active: bool = True, verified: bool = False) -> User:
    return User(
        _key="u-2", email="grower@example.org", display_name="Grower Two", is_active=active, email_verified=verified
    )


def _user_service(target: User, audit: _AuditRepo) -> tuple[UserService, MagicMock]:
    users = {"u-2": target, "admin-1": ADMIN}
    repo = MagicMock()
    repo.get_or_raise.side_effect = lambda key: users[key]
    repo.get_by_key.side_effect = users.get
    repo.update_fields.side_effect = lambda key, data: users[key].model_copy(update=data)
    memberships = MagicMock()
    memberships.active_memberships_of.return_value = []
    service = UserService(
        repo,
        step_up_verifier=PassedStepUpVerifier(),  # type: ignore[arg-type]
        refresh_token_repo=MagicMock(),
        membership_repo=memberships,
        security_audit=SecurityAuditService(audit),
    )
    return service, repo


def _admin_update_user(service: UserService, data: dict[str, Any]) -> User:
    return service.admin_update_user("u-2", data, requester=ADMIN, client_ip=None, **STEP_UP_PASSED)


class TestAccountTrustFlags:
    def test_a_deactivation_writes_who_deactivated_whom_and_no_tenant(self) -> None:
        audit = _AuditRepo()
        service, _ = _user_service(_target(), audit)

        _admin_update_user(service, {"is_active": False})

        (row,) = audit.rows
        assert (row.action, row.via) == (SecurityAuditAction.ACCOUNT_DEACTIVATED, SecurityAuditVia.PLATFORM_ADMIN)
        assert (row.actor_user_key, row.target_user_key, row.tenant_key) == ("admin-1", "u-2", None)
        assert row.created_at is not None
        _assert_no_personal_data(row, ADMIN, _target())

    def test_raising_both_flags_writes_one_row_per_flag(self) -> None:
        audit = _AuditRepo()
        service, _ = _user_service(_target(active=False, verified=False), audit)

        _admin_update_user(service, {"is_active": True, "email_verified": True})

        assert sorted(str(r.action) for r in audit.rows) == ["account_email_verified", "account_reactivated"]
        assert {r.target_user_key for r in audit.rows} == {"u-2"}

    def test_lowering_the_verification_writes_the_unverified_row(self) -> None:
        audit = _AuditRepo()
        service, _ = _user_service(_target(verified=True), audit)

        _admin_update_user(service, {"email_verified": False})

        (row,) = audit.rows
        assert row.action == SecurityAuditAction.ACCOUNT_EMAIL_UNVERIFIED

    def test_a_re_sent_value_and_a_name_edit_write_no_row(self) -> None:
        audit = _AuditRepo()
        service, repo = _user_service(_target(active=True, verified=True), audit)

        _admin_update_user(service, {"is_active": True, "email_verified": True, "display_name": "Renamed"})

        repo.update_fields.assert_called_once()
        assert audit.rows == []

    def test_an_update_that_did_not_store_writes_no_row(self) -> None:
        audit = _AuditRepo()
        service, repo = _user_service(_target(), audit)
        repo.update_fields.side_effect = lambda key, data: None

        with pytest.raises(NotFoundError):
            _admin_update_user(service, {"is_active": False})
        assert audit.rows == []

    def test_a_refused_deactivation_writes_no_row(self) -> None:
        audit = _AuditRepo()
        service, _ = _user_service(_target(), audit)

        with pytest.raises(ValidationError, match="own account"):
            service.admin_update_user(
                "admin-1", {"is_active": False}, requester=ADMIN, client_ip=None, **STEP_UP_PASSED
            )
        assert audit.rows == []

    def test_a_failing_audit_write_is_not_swallowed(self) -> None:
        service, _ = _user_service(_target(), _AuditRepo(fail=True))

        with pytest.raises(ConnectionError):
            _admin_update_user(service, {"is_active": False})


# ── Tenants: admin_update_tenant, delete_tenant, cancel_tenant_erasure ───────


class _TenantStore:
    def __init__(self, status: TenantStatus = TenantStatus.ACTIVE) -> None:
        self.doc = Tenant.model_validate(
            {
                "_key": KEY,
                "name": "Lindenhof",
                "slug": KEY,
                "tenant_type": "organization",
                "owner_user_key": "owner-1",
                "status": status,
            }
        )

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


def _tenant_service(audit: _AuditRepo, *, grace_days: int = 90, store: _TenantStore | None = None):  # type: ignore[no-untyped-def]
    store = store or _TenantStore()
    service = tenant_service_for_deletion(
        tenant_repo=store.repo(),
        tenant_erasure_grace_days=grace_days,
        tenant_engine=TenantEngine(),
        security_audit=SecurityAuditService(audit),
    )
    return service, store


def _admin_update_tenant(service, data: dict[str, Any]) -> Tenant:  # type: ignore[no-untyped-def]
    service._step_up_verifier = PassedStepUpVerifier()
    return service.admin_update_tenant(KEY, data, requester=ADMIN, client_ip=None, **STEP_UP_PASSED)


def _cancel_kwargs(*, origin: str = "tenant_management", code: str | None = None) -> dict[str, Any]:
    from app.domain.services.step_up_service import default_step_up_verifier
    from tests.support.step_up import AdmitEveryTarget

    if code is None:
        code, _ = default_step_up_verifier(target_policy=AdmitEveryTarget()).issue_code(
            AUTHORIZED_REQUESTER,
            action="tenant_erasure_cancel",
            target=KEY,
            authenticated_with_api_key=False,
            client_ip="203.0.113.10",
        )
    return {
        "requester": AUTHORIZED_REQUESTER,
        "authenticated_with_api_key": False,
        "confirmation": TenantErasureCancelConfirmation(step_up_code=code),
        "origin": origin,
        "client_ip": "203.0.113.10",
    }


class TestTenantLifecycle:
    def test_a_suspension_and_a_reactivation_each_write_a_row_naming_the_tenant_and_no_account(self) -> None:
        audit = _AuditRepo()
        service, store = _tenant_service(audit)

        _admin_update_tenant(service, {"is_active": False})
        assert store.doc.status == TenantStatus.SUSPENDED
        _admin_update_tenant(service, {"is_active": True})

        assert [(str(r.action), str(r.via)) for r in audit.rows] == [
            ("tenant_suspended", "platform_admin"),
            ("tenant_reactivated", "platform_admin"),
        ]
        assert {(r.actor_user_key, r.tenant_key, r.target_user_key) for r in audit.rows} == {("admin-1", KEY, None)}
        _assert_no_personal_data(audit.rows[0], ADMIN)

    def test_a_rename_a_limit_edit_and_a_re_sent_state_write_no_row(self) -> None:
        audit = _AuditRepo()
        service, _ = _tenant_service(audit)

        _admin_update_tenant(service, {"name": "Lindenhof Nord", "max_members": 10, "is_active": True})

        assert audit.rows == []

    def test_an_accepted_deletion_writes_one_row_and_a_repeat_none(self) -> None:
        audit = _AuditRepo()
        service, store = _tenant_service(audit)

        service.delete_tenant(KEY, **authorized(KEY), now=NOW)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert store.doc.status == TenantStatus.PENDING_DELETION
        (row,) = audit.rows
        assert (row.action, row.via) == (SecurityAuditAction.TENANT_DELETION_REQUESTED, SecurityAuditVia.TENANT_ADMIN)
        assert (row.actor_user_key, row.tenant_key, row.target_user_key) == (AUTHORIZED_REQUESTER.key, KEY, None)
        _assert_no_personal_data(row, AUTHORIZED_REQUESTER)

    def test_a_platform_admins_deletion_is_attributed_to_the_platform_panel(self) -> None:
        audit = _AuditRepo()
        service, _ = _tenant_service(audit)

        service.delete_tenant(KEY, **authorized(KEY, origin="platform_admin"), now=NOW)

        (row,) = audit.rows
        assert row.via == SecurityAuditVia.PLATFORM_ADMIN

    def test_an_immediate_deletion_writes_the_row_too(self) -> None:
        audit = _AuditRepo()
        service, store = _tenant_service(audit, grace_days=0)

        accepted = service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert accepted.status == "in_progress"
        assert store.doc.status == TenantStatus.DELETED
        assert [str(r.action) for r in audit.rows] == ["tenant_deletion_requested"]

    def test_a_withdrawn_deletion_writes_the_cancellation_row(self) -> None:
        audit = _AuditRepo()
        service, store = _tenant_service(audit)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        service.cancel_tenant_erasure(KEY, **_cancel_kwargs())

        assert store.doc.status == TenantStatus.ACTIVE
        assert [(str(r.action), str(r.via)) for r in audit.rows] == [
            ("tenant_deletion_requested", "tenant_admin"),
            ("tenant_deletion_cancelled", "tenant_admin"),
        ]
        assert audit.rows[1].tenant_key == KEY

    def test_a_refused_cancellation_writes_no_row(self) -> None:
        audit = _AuditRepo()
        service, store = _tenant_service(audit)
        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        with pytest.raises(UnauthorizedError):
            service.cancel_tenant_erasure(KEY, **_cancel_kwargs(code="00000000"))

        assert store.doc.status == TenantStatus.PENDING_DELETION
        assert [str(r.action) for r in audit.rows] == ["tenant_deletion_requested"]


# ── The platform admin reads the rows ────────────────────────────────────────


def test_the_admin_read_route_returns_the_account_and_the_tenant_rows() -> None:
    """``GET /admin/platform/security-audit`` serves a row without a tenant and one without a target."""
    from app.api.v1.admin.platform import router as mod
    from app.common.auth import require_platform_admin
    from app.common.dependencies import get_security_audit_service, get_tenant_service, get_user_service
    from app.common.error_handlers import app_error_handler
    from app.common.exceptions import KamerplanterError

    audit = _AuditRepo()
    users, _ = _user_service(_target(), audit)
    tenants, _store = _tenant_service(audit)
    tenants.list_user_memberships = MagicMock(return_value=[])  # the route's roles block; not under test
    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: ADMIN
    app.dependency_overrides[get_user_service] = lambda: users
    app.dependency_overrides[get_tenant_service] = lambda: tenants
    app.dependency_overrides[get_security_audit_service] = lambda: SecurityAuditService(audit)
    client = TestClient(app, raise_server_exceptions=False)

    deactivated = client.patch("/api/v1/admin/platform/users/u-2", json={"is_active": False, "current_password": "x"})
    assert deactivated.status_code == 200, deactivated.text
    _admin_update_tenant(tenants, {"is_active": False})

    listed = client.get("/api/v1/admin/platform/security-audit")
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert [(r["action"], r["actor_user_key"], r["target_user_key"], r["tenant_key"]) for r in body] == [
        ("tenant_suspended", "admin-1", None, KEY),
        ("account_deactivated", "admin-1", "u-2", None),
    ]
    assert "@" not in listed.text
    of_tenant = client.get("/api/v1/admin/platform/security-audit", params={"tenant_key": KEY}).json()
    assert [r["action"] for r in of_tenant] == ["tenant_suspended"]
