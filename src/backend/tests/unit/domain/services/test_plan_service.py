"""#2142 (REQ-056 §7.6, AK-20, AK-22, AK-23) — the platform admin keeps the plan catalogue.

Create, change, delete, choose the default; every change of the catalogue is audited with the
names of the changed fields and never their values; a plan in use or the default is not deleted.
The store is the in-memory double; the single-statement AQL of the real one (exactly one default,
delete only when unused) is measured in ``tests/integration/test_v0091_tenant_plan_key.py``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import SecurityAuditAction
from app.common.exceptions import DuplicateError, NotFoundError, ResourceInUseError, ValidationError
from app.domain.models.plan import Plan, PlanLimits
from app.domain.models.user import User
from app.domain.services.entitlement_service import EntitlementService
from app.domain.services.plan_service import PlanService
from tests.support.entitlement_doubles import InMemoryPlanRepository, standard_plan

ADMIN = User.model_validate({"_key": "admin-1", "email": "admin@example.org", "display_name": "Admin"})


def _service(*plans: Plan, tenant_plans: dict[str, str] | None = None, ceiling: int = 50):  # type: ignore[no-untyped-def]
    repo = InMemoryPlanRepository([standard_plan(), *plans], tenant_plans=tenant_plans)
    entitlements = EntitlementService(
        plan_repo=repo,
        tenant_repo=None,
        settings=SimpleNamespace(tenant_max_members_ceiling=ceiling),  # type: ignore[arg-type]
    )
    audit = MagicMock()
    return PlanService(plan_repo=repo, entitlements=entitlements, security_audit=audit), repo, audit


def _audited(audit: MagicMock) -> list[tuple[str, str, list[str] | None]]:
    return [
        (call.kwargs["action"], call.kwargs["plan_key"], call.kwargs["changed_fields"])
        for call in audit.record_plan_change.call_args_list
    ]


def test_a_created_plan_is_stored_never_as_default_and_audited() -> None:
    service, repo, audit = _service()

    created = service.create_plan(
        key="community", name="Community", description=None, limits=PlanLimits(members=30), actor=ADMIN
    )

    assert (created.plan.key, created.plan.is_default, created.tenant_count) == ("community", False, 0)
    assert repo.get_default() is not None and repo.get_default().key == "standard"  # type: ignore[union-attr]
    assert _audited(audit) == [(SecurityAuditAction.PLAN_CREATED, "community", None)]


def test_a_taken_key_is_a_conflict() -> None:
    service, _, audit = _service()

    with pytest.raises(DuplicateError):
        service.create_plan(key="standard", name="Again", description=None, limits=PlanLimits(), actor=ADMIN)
    audit.record_plan_change.assert_not_called()


@pytest.mark.parametrize("operation", ["create", "update"])
def test_members_above_the_ceiling_are_refused_on_create_and_update(operation: str) -> None:
    service, repo, audit = _service(Plan(_key="club", name="Club"), ceiling=30)

    with pytest.raises(ValidationError):
        if operation == "create":
            service.create_plan(key="big", name="Big", description=None, limits=PlanLimits(members=31), actor=ADMIN)
        else:
            service.update_plan("club", {"limits": {"members": 31}}, actor=ADMIN)

    assert repo.get("big") is None
    assert repo.get("club").limits.members is None  # type: ignore[union-attr]
    audit.record_plan_change.assert_not_called()


def test_a_change_names_the_changed_fields_and_keeps_the_others() -> None:
    service, repo, audit = _service(Plan(_key="club", name="Club", limits=PlanLimits(storage_mb=100, members=10)))

    updated = service.update_plan("club", {"name": "Club+", "limits": {"storage_mb": 500}}, actor=ADMIN)

    assert updated.plan.name == "Club+"
    assert updated.plan.limits == PlanLimits(storage_mb=500, members=10)
    assert _audited(audit) == [(SecurityAuditAction.PLAN_CHANGED, "club", ["name", "limits.storage_mb"])]


def test_an_explicit_null_returns_a_dimension_to_the_instance_setting() -> None:
    service, _, _ = _service(Plan(_key="club", name="Club", limits=PlanLimits(storage_mb=100)))

    updated = service.update_plan("club", {"limits": {"storage_mb": None}}, actor=ADMIN)

    assert updated.plan.limits.storage_mb is None


def test_a_change_that_changes_nothing_writes_nothing() -> None:
    service, _, audit = _service(Plan(_key="club", name="Club"))

    service.update_plan("club", {"name": "Club"}, actor=ADMIN)

    audit.record_plan_change.assert_not_called()


def test_making_a_plan_default_moves_the_one_default_mark() -> None:
    service, repo, audit = _service(Plan(_key="club", name="Club"))

    service.update_plan("club", {"is_default": True}, actor=ADMIN)

    assert [plan.key for plan in repo.list_all() if plan.is_default] == ["club"]
    assert _audited(audit) == [(SecurityAuditAction.PLAN_CHANGED, "club", ["is_default"])]


def test_unmarking_the_default_is_refused() -> None:
    service, repo, _ = _service()

    with pytest.raises(ValidationError):
        service.update_plan("standard", {"is_default": False}, actor=ADMIN)
    assert repo.get("standard").is_default  # type: ignore[union-attr]


def test_the_default_plan_and_a_plan_in_use_are_not_deleted() -> None:
    service, repo, audit = _service(Plan(_key="club", name="Club"), tenant_plans={"t-1": "club"})

    with pytest.raises(ResourceInUseError):
        service.delete_plan("standard", actor=ADMIN)
    with pytest.raises(ResourceInUseError):
        service.delete_plan("club", actor=ADMIN)

    assert repo.get("standard") is not None and repo.get("club") is not None
    audit.record_plan_change.assert_not_called()


def test_an_unused_plan_is_deleted_and_audited() -> None:
    service, repo, audit = _service(Plan(_key="club", name="Club"))

    service.delete_plan("club", actor=ADMIN)

    assert repo.get("club") is None
    assert _audited(audit) == [(SecurityAuditAction.PLAN_DELETED, "club", None)]


def test_an_unknown_plan_is_404() -> None:
    service, _, _ = _service()

    with pytest.raises(NotFoundError):
        service.update_plan("nope", {"name": "x"}, actor=ADMIN)
    with pytest.raises(NotFoundError):
        service.delete_plan("nope", actor=ADMIN)


def test_the_listing_counts_the_tenants_per_plan() -> None:
    service, _, _ = _service(
        Plan(_key="club", name="Club"), tenant_plans={"t-1": "club", "t-2": "standard", "t-3": "club"}
    )

    assert [(item.plan.key, item.tenant_count) for item in service.list_plans()] == [("club", 2), ("standard", 1)]
