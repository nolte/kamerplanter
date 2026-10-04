"""MT-014 (#2111): every change of a membership, role or scope leaves one persistent audit row.

The repository doubles are the owned I/O boundary; the audit repository is an in-memory
double that records the entries it was handed, so what is asserted is the *row the service
wrote* - who, whom, which tenant, which roles before/after, which door - not that a method
was called. The class guard ``tests/unit/guards/test_membership_mutations_write_the_security_audit.py``
holds that no mutating method skips it; the real collection is exercised in
``tests/integration/test_security_audit_log_reach.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import structlog
from structlog.testing import capture_logs

from app.common.enums import AdminScope, SecurityAuditAction, SecurityAuditVia, TenantRole
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.interfaces.security_audit_repository import ISecurityAuditRepository
from app.domain.models.invitation import Invitation
from app.domain.models.membership import Membership
from app.domain.models.security_audit import SecurityAuditEntry
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.tenant_service import TenantService
from tests.support.step_up import STEP_UP_PASSED, PassedStepUpVerifier

_ADMIN = MagicMock(key="admin-1")
_STEP_UP = {"requester": _ADMIN, "client_ip": None, **STEP_UP_PASSED}
_STEP_UP_ONLY = {"client_ip": None, **STEP_UP_PASSED}


class _AuditRepo(ISecurityAuditRepository):
    def __init__(self) -> None:
        self.rows: list[SecurityAuditEntry] = []

    def record(self, entry: SecurityAuditEntry) -> str:
        self.rows.append(entry)
        return f"audit-{len(self.rows)}"

    def list_recent(self, *, tenant_key: str | None = None, limit: int = 100) -> list[SecurityAuditEntry]:
        return [r for r in self.rows if tenant_key in (None, r.tenant_key)][:limit]

    def delete_expired(self, *, retention_days: int) -> int:
        return 0

    def count_undated(self) -> int:
        return 0


def _membership(role: TenantRole = TenantRole.GROWER, scopes: list[AdminScope] | None = None) -> Membership:
    return Membership(
        _key="m1", user_key="target-1", tenant_key="t1", role=role, admin_scopes=scopes or [], is_active=True
    )


def _service(membership: Membership | None = None) -> tuple[TenantService, _AuditRepo, MagicMock]:
    audit = _AuditRepo()
    audit_rows = audit.rows
    memberships = MagicMock()
    stored = membership or _membership()
    memberships.get_by_key.return_value = stored
    memberships.get_by_user_and_tenant.return_value = None
    memberships.count_managers.return_value = 2
    memberships.delete.return_value = True
    memberships.update_fields.side_effect = lambda key, fields: stored.model_copy(update=fields)
    memberships.create.side_effect = lambda m: m.model_copy(update={"key": "m-new"})
    tenants = MagicMock()
    tenants.get_by_key.return_value = Tenant(_key="t1", name="Garden", slug="garden", owner_user_key="o")
    tenants.get_by_slug.return_value = None
    tenants.create.side_effect = lambda t: t.model_copy(update={"key": "t-new"})

    def found(tenant, membership, *, audit=None):
        """The transactional founding, as the real repository does it: both stored, the row built from them."""
        stored_tenant = tenant.model_copy(update={"key": "t-new"})
        stored_membership = membership.model_copy(update={"key": "m-new", "tenant_key": "t-new"})
        if audit is not None:
            audit_rows.append(audit(stored_tenant, stored_membership))
        return stored_tenant, stored_membership

    tenants.create_with_lead_membership.side_effect = found
    tenants.count_organizations_by_owner.return_value = 0
    invitations = MagicMock()
    service = TenantService(
        tenant_repo=tenants,
        membership_repo=memberships,
        invitation_repo=invitations,
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        step_up_verifier=PassedStepUpVerifier(),  # type: ignore[arg-type]
        security_audit=SecurityAuditService(audit),
    )
    service._invitations = invitations  # type: ignore[attr-defined]
    return service, audit, memberships


def _only(audit: _AuditRepo) -> SecurityAuditEntry:
    assert len(audit.rows) == 1, audit.rows
    return audit.rows[0]


def test_the_admin_add_writes_who_added_whom_with_which_role() -> None:
    service, audit, _ = _service()

    service.admin_add_membership("t1", "target-1", TenantRole.LEAD, **_STEP_UP)

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_ADDED, SecurityAuditVia.PLATFORM_ADMIN)
    assert (row.actor_user_key, row.target_user_key, row.tenant_key) == ("admin-1", "target-1", "t1")
    assert (row.old_role, row.new_role, row.membership_key) == (None, "lead", "m-new")


def test_the_admin_role_change_writes_the_old_and_the_new_role() -> None:
    service, audit, _ = _service(_membership(TenantRole.GROWER))

    service.admin_change_membership_role(
        "m1",
        TenantRole.VIEWER,
        tenant_key="t1",
        requester=_ADMIN,
        **_STEP_UP_ONLY,
    )

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_ROLE_CHANGED, SecurityAuditVia.PLATFORM_ADMIN)
    assert (row.actor_user_key, row.target_user_key) == ("admin-1", "target-1")
    assert (row.old_role, row.new_role) == ("grower", "viewer")


def test_a_role_re_sent_unchanged_writes_no_row() -> None:
    service, audit, _ = _service(_membership(TenantRole.GROWER))

    service.admin_change_membership_role(
        "m1",
        TenantRole.GROWER,
        tenant_key="t1",
        requester=_ADMIN,
        **_STEP_UP_ONLY,
    )

    assert audit.rows == []


def test_the_admin_removal_writes_the_role_the_member_held() -> None:
    service, audit, _ = _service(_membership(TenantRole.LEAD))

    service.admin_remove_membership("m1", tenant_key="t1", requester=_ADMIN, **_STEP_UP_ONLY)

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_REMOVED, SecurityAuditVia.PLATFORM_ADMIN)
    assert (row.old_role, row.new_role, row.actor_user_key, row.target_user_key) == (
        "lead",
        None,
        "admin-1",
        "target-1",
    )


def test_a_removal_that_removed_nothing_writes_no_row() -> None:
    service, audit, memberships = _service(_membership())
    memberships.delete.return_value = False

    service.admin_remove_membership("m1", tenant_key="t1", requester=_ADMIN, **_STEP_UP_ONLY)

    assert audit.rows == []


def test_the_tenant_role_change_is_attributed_to_the_tenant_admin() -> None:
    service, audit, _ = _service(_membership(TenantRole.VIEWER))

    service.change_member_role(
        "t1", "m1", TenantRole.GROWER, [AdminScope.MANAGEMENT], actor_user_key="secretary-1", **_STEP_UP
    )

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_ROLE_CHANGED, SecurityAuditVia.TENANT_ADMIN)
    assert (row.actor_user_key, row.target_user_key, row.old_role, row.new_role) == (
        "secretary-1",
        "target-1",
        "viewer",
        "grower",
    )


def test_the_scope_change_writes_the_scopes_before_and_after() -> None:
    service, audit, _ = _service(_membership(TenantRole.GROWER, [AdminScope.MANAGEMENT]))

    service.change_member_scopes(
        "t1", "m1", [AdminScope.MANAGEMENT, AdminScope.TECHNICAL], [AdminScope.MANAGEMENT], actor_user_key="secretary-1"
    )

    row = _only(audit)
    assert row.action == SecurityAuditAction.MEMBERSHIP_SCOPES_CHANGED
    assert (row.old_scopes, row.new_scopes) == (["management"], ["management", "technical"])


def test_the_tenant_removal_writes_a_row() -> None:
    service, audit, _ = _service(_membership(TenantRole.GROWER))

    service.remove_member("t1", "m1", [AdminScope.MANAGEMENT], **_STEP_UP)

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_REMOVED, SecurityAuditVia.TENANT_ADMIN)
    assert (row.actor_user_key, row.target_user_key, row.old_role) == ("admin-1", "target-1", "grower")


def test_leaving_writes_a_self_row() -> None:
    service, audit, memberships = _service(_membership(TenantRole.GROWER))
    memberships.get_by_user_and_tenant.return_value = _membership(TenantRole.GROWER)

    service.leave_tenant("t1", "target-1")

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_LEFT, SecurityAuditVia.SELF)
    assert (row.actor_user_key, row.target_user_key, row.old_role) == ("target-1", "target-1", "grower")


def test_the_registration_writes_the_founders_lead_membership() -> None:
    service, audit, _ = _service()

    service.create_personal_tenant("newbie-1", "Newbie")

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_ADDED, SecurityAuditVia.REGISTRATION)
    assert (row.actor_user_key, row.target_user_key, row.tenant_key, row.new_role) == (
        "newbie-1",
        "newbie-1",
        "t-new",
        "lead",
    )
    assert row.new_scopes == ["management", "technical"]


def test_the_organisation_creation_writes_the_founders_lead_membership() -> None:
    service, audit, _ = _service()

    service.create_organization("founder-1", "Community Garden")

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_ADDED, SecurityAuditVia.TENANT_CREATION)
    assert (row.target_user_key, row.new_role) == ("founder-1", "lead")


def test_accepting_an_invitation_writes_the_accepting_account_and_the_invited_role() -> None:
    service, audit, _ = _service()
    invitation = Invitation(
        _key="i1",
        tenant_key="t1",
        invited_by_user_key="lead-1",
        role=TenantRole.GROWER,
        token_hash="x",
        expires_at="2999-01-01T00:00:00+00:00",
        email="a@example.com",
    )
    service._invitations.get_by_token_hash.return_value = invitation  # type: ignore[attr-defined]
    service._invitations.mark_accepted_if_pending.return_value = invitation  # type: ignore[attr-defined]

    service.accept_invitation(
        "raw-token",
        User(
            _key="joiner-1",
            email="a@example.com",
            display_name="J",
            email_verified=True,
            email_confirmed_at="2026-01-01T00:00:00+00:00",
        ),
    )

    row = _only(audit)
    assert (row.action, row.via) == (SecurityAuditAction.MEMBERSHIP_ADDED, SecurityAuditVia.INVITATION)
    assert (row.actor_user_key, row.target_user_key, row.new_role) == ("joiner-1", "joiner-1", "grower")


def test_a_failing_audit_write_is_not_swallowed() -> None:
    service, audit, _ = _service(_membership())
    audit.record = MagicMock(side_effect=RuntimeError("audit store down"))  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="audit store down"):
        service.admin_add_membership("t1", "target-1", TenantRole.VIEWER, **_STEP_UP)


def test_the_row_carries_the_request_id_and_the_log_line_no_raw_key() -> None:
    service, audit, _ = _service()
    structlog.contextvars.bind_contextvars(request_id="req-123")
    try:
        with capture_logs() as logs:
            service.admin_add_membership("t1", "target-1", TenantRole.VIEWER, **_STEP_UP)
    finally:
        structlog.contextvars.clear_contextvars()

    assert _only(audit).request_id == "req-123"
    (line,) = [entry for entry in logs if entry["event"] == "security_audit_recorded"]
    assert line["log_level"] == "warning"
    rendered = repr(line)
    assert "target-1" not in rendered and "admin-1" not in rendered and "'t1'" not in rendered
