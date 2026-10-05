"""#2134 (MT-038) — an account erasure never leaves an organisation without anybody who can administer it.

Measured before this change: the account erasure's ArangoDB plan removes every
membership of the subject (``ErasureStep memberships``, ``executor="account_cascade"``)
without the INV-1 guard that ``remove_member`` / ``leave_tenant`` /
``change_member_scopes`` apply (``TenantService._guard_last_manager``). An organisation
whose only ``management`` holder — or only member — was the subject lived on with
nobody able to invite, administer or delete it; its sites (GPS), photos and sensor data
without any retention.

Operator decision 2026-10-04:

* the erasure preview names "last management in org X" / "last member in org Y";
* on erasure the longest-serving remaining ``lead`` receives ``management``
  (audited, the members are told);
* without a remaining ``lead`` (or without any other member) the organisation becomes
  ``orphaned`` and runs into the tenant-deletion grace (#2123), visible in the admin
  panel; its members and the platform admins are told.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import AdminScope, SecurityAuditVia, TenantRole, TenantStatus, TenantType
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from tests.support.tenant_erasure_doubles import FakeTenantErasureRepository, tenant_service_for_deletion

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
SUBJECT = "subject-1"
ORG = "org-1"
GRACE_DAYS = 90


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


def _m(
    user_key: str,
    role: TenantRole,
    scopes: list[AdminScope] | None = None,
    *,
    joined: str | None = "2026-01-01T00:00:00+00:00",
    tenant_key: str = ORG,
    key: str | None = None,
) -> Membership:
    return Membership.model_validate(
        {
            "_key": key or f"m-{user_key}-{tenant_key}",
            "user_key": user_key,
            "tenant_key": tenant_key,
            "role": role,
            "admin_scopes": scopes or [],
            "joined_at": joined,
        }
    )


# ── The decision (pure) ──────────────────────────────────────────────────────


class TestTheDecision:
    def test_a_member_who_is_neither_last_manager_nor_last_member_changes_nothing(self) -> None:
        subject = _m(SUBJECT, TenantRole.GROWER)
        others = [_m("lead-1", TenantRole.LEAD, [AdminScope.MANAGEMENT])]

        assert MembershipEngine.departure_settlement(subject, others) == ("unaffected", None)

    def test_another_management_holder_keeps_the_organisation_administrable(self) -> None:
        subject = _m(SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT])
        others = [_m("sec-1", TenantRole.VIEWER, [AdminScope.MANAGEMENT])]

        assert MembershipEngine.departure_settlement(subject, others) == ("unaffected", None)

    def test_the_last_manager_hands_management_to_the_longest_serving_lead(self) -> None:
        subject = _m(SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT])
        young = _m("lead-young", TenantRole.LEAD, joined="2026-06-01T00:00:00+00:00")
        old = _m("lead-old", TenantRole.LEAD, [AdminScope.TECHNICAL], joined="2025-03-01T00:00:00+00:00")
        grower = _m("grower-oldest", TenantRole.GROWER, joined="2024-01-01T00:00:00+00:00")

        outcome, heir = MembershipEngine.departure_settlement(subject, [young, grower, old])

        assert outcome == "management_passes_to_lead"
        assert heir is not None and heir.user_key == "lead-old"

    def test_a_lead_without_a_recorded_start_comes_after_every_recorded_one(self) -> None:
        subject = _m(SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT])
        unknown = _m("lead-unknown", TenantRole.LEAD, joined=None)
        known = _m("lead-known", TenantRole.LEAD, joined="2026-09-01T00:00:00+00:00")

        _outcome, heir = MembershipEngine.departure_settlement(subject, [unknown, known])

        assert heir is not None and heir.user_key == "lead-known"

    def test_the_last_manager_without_a_lead_left_orphans_the_organisation(self) -> None:
        subject = _m(SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT])
        others = [_m("grower-1", TenantRole.GROWER), _m("viewer-1", TenantRole.VIEWER)]

        assert MembershipEngine.departure_settlement(subject, others) == ("orphaned", None)

    def test_the_last_member_orphans_the_organisation_whatever_its_scopes(self) -> None:
        assert MembershipEngine.departure_settlement(_m(SUBJECT, TenantRole.VIEWER), []) == ("orphaned", None)


# ── The service ──────────────────────────────────────────────────────────────


class _World:
    """One organisation (plus the subject's personal tenant and the platform tenant) around the real service."""

    def __init__(self, members: list[Membership], *, org_status: TenantStatus = TenantStatus.ACTIVE) -> None:
        self.tenants = {
            ORG: Tenant.model_validate(
                {
                    "_key": ORG,
                    "name": "Lindenhof",
                    "slug": "lindenhof",
                    "tenant_type": TenantType.ORGANIZATION,
                    "owner_user_key": SUBJECT,
                    "status": org_status,
                }
            ),
            "personal-1": Tenant.model_validate(
                {"_key": "personal-1", "name": "Subject", "slug": "subject", "owner_user_key": SUBJECT}
            ),
            "platform": Tenant.model_validate(
                {
                    "_key": "platform",
                    "name": "Platform",
                    "slug": "platform",
                    "tenant_type": TenantType.ORGANIZATION,
                    "owner_user_key": "admin-1",
                    "is_platform": True,
                }
            ),
        }
        self.memberships = {m.key: m for m in members}
        self.memberships["m-admin-platform"] = _m(
            "admin-1", TenantRole.LEAD, [AdminScope.MANAGEMENT], tenant_key="platform", key="m-admin-platform"
        )
        self.memberships["m-subject-personal"] = _m(
            SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT], tenant_key="personal-1", key="m-subject-personal"
        )
        tenant_repo = MagicMock()
        tenant_repo.get_by_key.side_effect = self.tenants.get

        def update_tenant(key: str, fields: dict[str, Any]) -> Tenant | None:
            if key not in self.tenants:
                return None
            self.tenants[key] = Tenant.model_validate({**self.tenants[key].model_dump(by_alias=True), **fields})
            return self.tenants[key]

        tenant_repo.update_fields.side_effect = update_tenant
        membership_repo = MagicMock()
        membership_repo.list_by_user.side_effect = lambda user_key: [
            m for m in self.memberships.values() if m.user_key == user_key
        ]
        membership_repo.active_memberships_of.side_effect = lambda *, tenant_key: [
            m for m in self.memberships.values() if m.tenant_key == tenant_key and m.is_active and m.user_key != SUBJECT
        ]
        membership_repo.active_member_user_keys.side_effect = lambda *, tenant_key: [
            m.user_key for m in membership_repo.active_memberships_of(tenant_key=tenant_key)
        ]

        def update_membership(key: str, fields: dict[str, Any]) -> Membership | None:
            current = self.memberships.get(key)
            if current is None:
                return None
            self.memberships[key] = Membership.model_validate({**current.model_dump(by_alias=True), **fields})
            return self.memberships[key]

        membership_repo.update_fields.side_effect = update_membership
        membership_repo.get_by_user_and_tenant.side_effect = lambda user_key, tenant_key: next(
            (m for m in self.memberships.values() if m.user_key == user_key and m.tenant_key == tenant_key), None
        )
        self.mailer = MagicMock()
        users = MagicMock()
        users.get_by_key.side_effect = lambda key: User.model_validate(
            {"_key": key, "email": f"{key}@example.org", "display_name": key}
        )
        self.audit = MagicMock()
        self.records = FakeTenantErasureRepository()
        self.service = tenant_service_for_deletion(
            tenant_repo=tenant_repo,
            membership_repo=membership_repo,
            record_repo=self.records,
            tenant_erasure_grace_days=GRACE_DAYS,
            email_service=self.mailer,
            user_repo=users,
            security_audit=self.audit,
            membership_engine=MembershipEngine(),
        )

    def mailed(self) -> set[str]:
        return {call.kwargs["to_email"] for call in self.mailer.send_notification_email.call_args_list}


class TestTheErasureSettlesEveryOrganisation:
    def test_the_longest_serving_lead_receives_management_audited_and_told(self) -> None:
        world = _World(
            [
                _m(SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT]),
                _m("lead-old", TenantRole.LEAD, joined="2025-01-01T00:00:00+00:00"),
                _m("lead-young", TenantRole.LEAD, joined="2026-05-01T00:00:00+00:00"),
                _m("grower-1", TenantRole.GROWER),
            ]
        )

        outcomes = world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

        assert [(o.tenant_key, o.outcome) for o in outcomes] == [(ORG, "management_passes_to_lead")]
        assert AdminScope.MANAGEMENT in world.memberships[f"m-lead-old-{ORG}"].admin_scopes
        assert AdminScope.MANAGEMENT not in world.memberships[f"m-lead-young-{ORG}"].admin_scopes
        assert world.tenants[ORG].status == TenantStatus.ACTIVE
        (audit_call,) = world.audit.record_membership_change.call_args_list
        assert audit_call.kwargs["via"] == SecurityAuditVia.ACCOUNT_ERASURE
        assert audit_call.kwargs["target_user_key"] == "lead-old"
        assert world.mailed() == {"lead-old@example.org", "lead-young@example.org", "grower-1@example.org"}

    def test_without_a_lead_left_the_organisation_is_orphaned_and_scheduled(self) -> None:
        world = _World([_m(SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT]), _m("grower-1", TenantRole.GROWER)])

        outcomes = world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

        assert [(o.tenant_key, o.outcome) for o in outcomes] == [(ORG, "orphaned")]
        assert world.tenants[ORG].status == TenantStatus.ORPHANED
        assert world.tenants[ORG].deletion_scheduled_at == NOW + timedelta(days=GRACE_DAYS)
        record = world.records.get(TenantErasureEngine.record_key(ORG))
        assert record is not None
        assert (record.status, record.origin) == ("scheduled", "orphaned_organisation")
        assert record.scheduled_for == NOW + timedelta(days=GRACE_DAYS)
        # the remaining member and the platform admin are told; the subject is not
        assert world.mailed() == {"grower-1@example.org", "admin-1@example.org"}

    def test_the_only_member_orphans_the_organisation(self) -> None:
        world = _World([_m(SUBJECT, TenantRole.VIEWER)])

        outcomes = world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

        assert [(o.tenant_key, o.outcome) for o in outcomes] == [(ORG, "orphaned")]
        assert world.mailed() == {"admin-1@example.org"}

    def test_after_the_grace_the_beat_erases_the_orphaned_organisation(self) -> None:
        world = _World([_m(SUBJECT, TenantRole.VIEWER)])
        world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

        result = world.service.resume_tenant_erasures(NOW + timedelta(days=GRACE_DAYS, hours=1))

        assert result["completed"] == 1
        assert world.records.get(TenantErasureEngine.record_key(ORG)).status == "completed"  # type: ignore[union-attr]

    def test_a_retry_changes_nothing_twice(self) -> None:
        world = _World(
            [
                _m(SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT]),
                _m("lead-old", TenantRole.LEAD),
            ]
        )
        world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW)
        world.mailer.reset_mock()
        world.audit.reset_mock()

        again = world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW + timedelta(hours=1))

        assert [o.outcome for o in again] == ["unaffected"]
        world.audit.record_membership_change.assert_not_called()
        world.mailer.send_notification_email.assert_not_called()

    def test_an_already_orphaned_organisation_is_not_scheduled_again(self) -> None:
        world = _World([_m(SUBJECT, TenantRole.VIEWER)])
        world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

        again = world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW + timedelta(days=1))

        assert again == []  # an orphaned organisation's lifecycle is decided; it is not looked at again
        assert world.tenants[ORG].deletion_scheduled_at == NOW + timedelta(days=GRACE_DAYS)

    def test_personal_and_platform_tenants_are_not_settled_here(self) -> None:
        world = _World([_m(SUBJECT, TenantRole.GROWER), _m("lead-1", TenantRole.LEAD, [AdminScope.MANAGEMENT])])

        outcomes = world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

        assert {o.tenant_key for o in outcomes} == {ORG}

    def test_an_orphaned_organisation_cannot_be_cancelled_back_to_life(self) -> None:
        from app.common.exceptions import InvalidStatusTransitionError
        from app.domain.models.tenant_erasure import TenantErasureCancelConfirmation

        world = _World([_m(SUBJECT, TenantRole.VIEWER)])
        world.service.settle_organisations_of_erased_account(SUBJECT, now=NOW)
        admin = User.model_validate({"_key": "admin-1", "email": "a@example.org", "display_name": "A"})
        world.service._step_up_verifier = MagicMock()

        with pytest.raises(InvalidStatusTransitionError):
            world.service.cancel_tenant_erasure(
                ORG,
                requester=admin,
                authenticated_with_api_key=False,
                confirmation=TenantErasureCancelConfirmation(),
                origin="platform_admin",
                client_ip=None,
            )
        assert world.tenants[ORG].status == TenantStatus.ORPHANED


class TestThePreviewNamesWhatTheErasureWillDo:
    def test_last_manager_and_last_member_are_named_per_organisation(self) -> None:
        world = _World(
            [
                _m(SUBJECT, TenantRole.LEAD, [AdminScope.MANAGEMENT]),
                _m("lead-old", TenantRole.LEAD),
            ]
        )
        second = Tenant.model_validate(
            {
                "_key": "org-2",
                "name": "Kleingarten",
                "slug": "kleingarten",
                "tenant_type": TenantType.ORGANIZATION,
                "owner_user_key": "x",
            }
        )
        world.tenants["org-2"] = second
        world.memberships["m-subject-org-2"] = _m(SUBJECT, TenantRole.VIEWER, tenant_key="org-2", key="m-subject-org-2")

        preview = world.service.organisation_erasure_preview(SUBJECT)

        assert sorted((p.name, p.outcome) for p in preview) == [
            ("Kleingarten", "orphaned"),
            ("Lindenhof", "management_passes_to_lead"),
        ]
        # read-only: nothing changed
        assert AdminScope.MANAGEMENT not in world.memberships[f"m-lead-old-{ORG}"].admin_scopes
        assert world.tenants["org-2"].status == TenantStatus.ACTIVE
