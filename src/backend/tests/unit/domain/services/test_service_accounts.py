"""#2137 (MT-041, REQ-023 §5b): a tenant's lead with the technical scope creates, re-keys and removes service accounts.

Before #2137 nothing wrote ``account_type == "service"``. The decisions pinned here, over repository
doubles (the real collections run in ``tests/integration/test_service_accounts_reach.py``):

* **who** — the stored membership holds ``lead`` **and** ``technical``; anyone else is 403 before the
  step-up is asked for, and nothing is written;
* **what is created** — a password-less ``service`` account, one ``viewer``/``grower`` membership through
  the member-limited join door, one key scoped to this tenant carrying the requested controls, one
  security-audit row;
* **quota** — ``SERVICE_ACCOUNT_LIMIT_REACHED`` at ``TENANT_MAX_SERVICE_ACCOUNTS`` active accounts;
* **rotation** — a new key with the predecessor's controls; the live previous keys are revoked
  (overlap 0) or given an end (overlap > 0); audited;
* **removal** — keys here revoked, membership removed (audited, task assignments end), the account
  deactivated once it holds no other membership;
* a service account is never raised to ``lead`` through the member list.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import AdminScope, SecurityAuditAction, SecurityAuditVia, TenantRole
from app.common.exceptions import ForbiddenError, KamerplanterError, NotFoundError, ValidationError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.auth import ApiKey
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService
from tests.support.step_up import STEP_UP_PASSED, PassedStepUpVerifier

TENANT = "t-garden"
LEAD = User.model_validate({"_key": "u-lead", "email": "lead@example.org", "display_name": "Lead"})


def _membership(user_key: str, role: TenantRole, scopes: list[AdminScope] | None = None, **extra: Any) -> Membership:
    return Membership(
        _key=f"m-{user_key}",
        user_key=user_key,
        tenant_key=TENANT,
        role=role,
        admin_scopes=scopes or [],
        is_active=True,
        **extra,
    )


class _Users:
    def __init__(self) -> None:
        self.rows: dict[str, User] = {"u-lead": LEAD}
        self.deleted: list[str] = []
        self.updates: list[tuple[str, dict[str, Any]]] = []

    def create(self, user: User) -> User:
        stored = user.model_copy(update={"key": f"sa-{len(self.rows)}"})
        self.rows[stored.key or ""] = stored
        return stored

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)

    def delete(self, key: str) -> bool:
        self.deleted.append(key)
        self.rows.pop(key, None)
        return True

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        self.updates.append((key, fields))
        self.rows[key] = self.rows[key].model_copy(update=fields)
        return self.rows[key]


class _Keys:
    def __init__(self) -> None:
        self.rows: list[ApiKey] = []
        self.revoked: list[str] = []
        self.ended: list[tuple[str, datetime]] = []

    def create(self, api_key: ApiKey) -> ApiKey:
        stored = api_key.model_copy(update={"key": f"ak-{len(self.rows) + 1}", "created_at": datetime.now(UTC)})
        self.rows.append(stored)
        return stored

    def list_by_user(self, user_key: str) -> list[ApiKey]:
        return [k for k in self.rows if k.user_key == user_key]

    def revoke(self, key: str) -> bool:
        self.revoked.append(key)
        return True

    def expire_no_later_than(self, key: str, at: datetime) -> bool:
        self.ended.append((key, at))
        return True


class _World:
    def __init__(
        self,
        *,
        actor_role: TenantRole = TenantRole.LEAD,
        actor_scopes: list[AdminScope] | None = None,
        service_accounts: int = 0,
        members: int = 1,
        max_members: int = 50,
        light_mode: bool = False,
    ) -> None:
        scopes = [AdminScope.MANAGEMENT, AdminScope.TECHNICAL] if actor_scopes is None else actor_scopes
        self.users = _Users()
        self.keys = _Keys()
        self.memberships_by_user: dict[str, Membership] = {"u-lead": _membership("u-lead", actor_role, scopes)}
        self.memberships = MagicMock()
        self.memberships.get_by_user_and_tenant.side_effect = lambda user_key, tenant_key: (
            self.memberships_by_user.get(user_key) if tenant_key == TENANT else None
        )
        self.memberships.get_by_key.side_effect = lambda key: next(
            (m for m in self.memberships_by_user.values() if m.key == key), None
        )
        self.memberships.active_service_account_memberships.return_value = [
            _membership(f"sa-old-{i}", TenantRole.GROWER) for i in range(service_accounts)
        ]
        self.memberships.count_active_members.return_value = members
        self.memberships.create.side_effect = self._create_membership
        self.memberships.delete.return_value = True
        self.memberships.list_by_user.side_effect = lambda user_key: [
            m for m in self.memberships_by_user.values() if m.user_key == user_key
        ]
        tenants = MagicMock()
        tenants.get_by_key.return_value = Tenant(
            _key=TENANT, name="Garden", slug="garden", owner_user_key="u-lead", max_members=max_members
        )
        self.audit = MagicMock()
        self.tasks = MagicMock()
        self.step_up = PassedStepUpVerifier()
        self.service = TenantService(
            tenant_repo=tenants,
            membership_repo=self.memberships,
            invitation_repo=MagicMock(),
            assignment_repo=MagicMock(),
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
            security_audit=self.audit,
            step_up_verifier=self.step_up,  # type: ignore[arg-type]
            task_repo=self.tasks,
            user_repo=self.users,  # type: ignore[arg-type]
            api_key_repo=self.keys,  # type: ignore[arg-type]
            max_service_accounts=3,
            light_mode=light_mode,
        )

    def _create_membership(self, membership: Membership) -> Membership:
        stored = membership.model_copy(update={"key": f"m-{membership.user_key}"})
        self.memberships_by_user[membership.user_key] = stored
        return stored

    def create(self, **overrides: Any) -> Any:
        arguments: dict[str, Any] = {
            "name": "Home Assistant",
            "role": TenantRole.GROWER,
            "ip_allowlist": ["192.168.1.0/24"],
            "rate_limit_per_minute": 600,
            "expires_at": None,
            **overrides,
        }
        return self.service.create_service_account(
            TENANT, requester=LEAD, client_ip=None, **arguments, **STEP_UP_PASSED
        )

    def rotate(self, account_key: str, *, overlap_minutes: int = 0, expires_at: datetime | None = None) -> Any:
        return self.service.rotate_service_account_key(
            TENANT,
            account_key,
            overlap_minutes=overlap_minutes,
            expires_at=expires_at,
            requester=LEAD,
            client_ip=None,
            **STEP_UP_PASSED,
        )

    def remove(self, account_key: str) -> None:
        self.service.remove_service_account(TENANT, account_key, requester=LEAD, client_ip=None, **STEP_UP_PASSED)

    def nothing_written(self) -> bool:
        return (
            len(self.users.rows) == 1
            and not self.memberships.create.called
            and self.keys.rows == []
            and not self.audit.record_membership_change.called
            and self.step_up.actions == []
        )


# ── creation ────────────────────────────────────────────────────────────────


def test_a_lead_with_the_technical_scope_creates_a_service_account() -> None:
    world = _World()

    created = world.create()

    account = world.users.rows[created.key]
    assert account.account_type == "service"
    assert account.password_hash is None
    assert account.display_name == "Home Assistant"
    membership = world.memberships_by_user[created.key]
    assert (membership.role, membership.admin_scopes, membership.tenant_key) == (TenantRole.GROWER, [], TENANT)
    (key,) = world.keys.rows
    assert key.user_key == created.key
    assert key.tenant_scope == TENANT, "a service-account key is always scoped to its tenant"
    assert (key.ip_allowlist, key.rate_limit_per_minute) == (["192.168.1.0/24"], 600)
    assert created.api_key.raw_key.startswith("kp_")
    assert world.step_up.actions == ["service_account_change"]
    assert world.step_up.targets == [TENANT]
    audited = world.audit.record_membership_change.call_args.kwargs
    assert (audited["action"], audited["via"], audited["actor_user_key"], audited["target_user_key"]) == (
        SecurityAuditAction.MEMBERSHIP_ADDED,
        SecurityAuditVia.TENANT_ADMIN,
        "u-lead",
        created.key,
    )


def test_the_account_address_is_undeliverable_and_names_nothing() -> None:
    world = _World()

    created = world.create(name="Grafana Monitoring")

    email = world.users.rows[created.key].email
    assert email.endswith("@service.example.com")
    assert "grafana" not in email.lower() and "garden" not in email.lower()


@pytest.mark.parametrize(
    ("role", "scopes"),
    [
        (TenantRole.LEAD, [AdminScope.MANAGEMENT]),
        (TenantRole.GROWER, [AdminScope.TECHNICAL]),
        (TenantRole.VIEWER, [AdminScope.MANAGEMENT, AdminScope.TECHNICAL]),
    ],
    ids=["lead-without-technical", "technical-grower", "both-scopes-viewer"],
)
def test_anyone_but_a_lead_with_technical_is_refused_before_the_step_up(
    role: TenantRole, scopes: list[AdminScope]
) -> None:
    world = _World(actor_role=role, actor_scopes=scopes)

    with pytest.raises(ForbiddenError):
        world.create()

    assert world.nothing_written()


def test_a_service_account_is_never_created_as_lead() -> None:
    world = _World()

    with pytest.raises(ValidationError):
        world.create(role=TenantRole.LEAD)

    assert world.nothing_written()


def test_an_invalid_control_is_refused_before_the_step_up() -> None:
    world = _World()

    with pytest.raises(ValidationError):
        world.create(ip_allowlist=["0.0.0.0/0"])

    assert world.nothing_written()


def test_the_quota_refuses_the_next_service_account() -> None:
    world = _World(service_accounts=3)

    with pytest.raises(KamerplanterError) as refused:
        world.create()

    assert (refused.value.status_code, refused.value.error_code) == (422, "SERVICE_ACCOUNT_LIMIT_REACHED")
    assert world.nothing_written()


def test_a_service_account_takes_a_seat_of_the_member_limit() -> None:
    world = _World(members=5, max_members=5)

    with pytest.raises(KamerplanterError) as refused:
        world.create()

    assert refused.value.error_code == "MEMBER_LIMIT_REACHED"
    assert world.nothing_written()


def test_a_join_that_does_not_stand_takes_the_account_back() -> None:
    world = _World()
    world.memberships.create.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError):
        world.create()

    assert world.users.deleted == ["sa-1"]
    assert world.keys.rows == []


def test_light_mode_has_no_service_accounts() -> None:
    world = _World(light_mode=True)

    with pytest.raises(ForbiddenError):
        world.create()

    assert world.nothing_written()


# ── rotation ────────────────────────────────────────────────────────────────


def test_a_rotation_without_overlap_revokes_the_previous_keys_and_keeps_the_controls() -> None:
    world = _World()
    created = world.create()
    first_key = world.keys.rows[0].key

    rotated = world.rotate(created.key)

    assert world.keys.revoked == [first_key]
    new_key = world.keys.rows[-1]
    assert (new_key.ip_allowlist, new_key.rate_limit_per_minute, new_key.tenant_scope) == (
        ["192.168.1.0/24"],
        600,
        TENANT,
    )
    assert rotated.previous_keys_end_at is None
    assert rotated.replaced_key_count == 1
    assert world.step_up.targets[-1] == f"{TENANT}|{created.key}"
    assert world.audit.record_membership_change.call_args.kwargs["action"] == (
        SecurityAuditAction.SERVICE_ACCOUNT_KEY_ROTATED
    )


def test_a_rotation_with_overlap_gives_the_previous_keys_an_end_instead() -> None:
    world = _World()
    created = world.create()
    first_key = world.keys.rows[0].key
    before = datetime.now(UTC)

    rotated = world.rotate(created.key, overlap_minutes=30)

    assert world.keys.revoked == []
    ((ended_key, ends_at),) = world.keys.ended
    assert ended_key == first_key
    assert before + timedelta(minutes=30) <= ends_at <= datetime.now(UTC) + timedelta(minutes=30)
    assert rotated.previous_keys_end_at == ends_at


def test_a_rotation_leaves_revoked_and_expired_keys_alone() -> None:
    world = _World()
    created = world.create()
    world.keys.rows.append(
        world.keys.rows[0].model_copy(update={"key": "ak-old", "expires_at": datetime.now(UTC) - timedelta(days=1)})
    )
    world.keys.rows.append(world.keys.rows[0].model_copy(update={"key": "ak-revoked", "revoked": True}))

    world.rotate(created.key)

    assert world.keys.revoked == ["ak-1"]


@pytest.mark.parametrize("overlap", [-1, 1441])
def test_an_overlap_outside_a_day_is_refused(overlap: int) -> None:
    world = _World()
    created = world.create()

    with pytest.raises(ValidationError):
        world.rotate(created.key, overlap_minutes=overlap)

    assert len(world.keys.rows) == 1


@pytest.mark.parametrize("target", ["u-lead", "nobody"], ids=["a-person", "unknown"])
def test_only_a_service_account_of_this_tenant_is_rotated(target: str) -> None:
    world = _World()

    with pytest.raises(NotFoundError):
        world.rotate(target)

    assert world.keys.rows == []
    assert world.step_up.actions == []


# ── removal ─────────────────────────────────────────────────────────────────


def test_removal_revokes_the_keys_ends_the_membership_and_deactivates_the_account() -> None:
    world = _World()
    created = world.create()
    world.memberships.delete.side_effect = lambda key: world.memberships_by_user.pop(created.key) is not None

    world.remove(created.key)

    assert world.keys.revoked == ["ak-1"]
    world.memberships.delete.assert_called_once_with(f"m-{created.key}")
    assert world.audit.record_membership_change.call_args.kwargs["action"] == SecurityAuditAction.MEMBERSHIP_REMOVED
    world.tasks.clear_assignee.assert_called_once_with(tenant_key=TENANT, user_key=created.key)
    assert world.users.rows[created.key].is_active is False


def test_removal_keeps_an_account_that_still_belongs_to_another_tenant() -> None:
    world = _World()
    created = world.create()
    elsewhere = Membership(
        _key="m-elsewhere", user_key=created.key, tenant_key="t-other", role=TenantRole.VIEWER, is_active=True
    )
    world.memberships.list_by_user.side_effect = lambda user_key: [elsewhere]

    world.remove(created.key)

    assert world.users.updates == []


# ── a service account is never raised to lead ───────────────────────────────


@pytest.mark.parametrize(("account_type", "refused"), [("service", True), ("human", False)])
def test_the_member_list_does_not_raise_a_service_account_to_lead(account_type: str, refused: bool) -> None:
    world = _World()
    world.users.rows["u-member"] = User.model_validate(
        {"_key": "u-member", "email": "m@example.org", "display_name": "M", "account_type": account_type}
    )
    world.memberships_by_user["u-member"] = _membership("u-member", TenantRole.GROWER)

    def change() -> Any:
        return world.service.change_member_role(
            TENANT,
            "m-u-member",
            TenantRole.LEAD,
            [AdminScope.MANAGEMENT],
            actor_user_key="u-lead",
            requester=LEAD,
            client_ip=None,
            **STEP_UP_PASSED,
        )

    if refused:
        with pytest.raises(ForbiddenError):
            change()
        assert world.step_up.actions == []
    else:
        change()
        assert world.step_up.actions == ["tenant_member_role_change"]
