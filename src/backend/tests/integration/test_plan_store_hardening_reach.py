"""#2142 security review (SEC-001, SEC-003, SEC-004) — the plan store on a real ArangoDB.

* **SEC-001** — a stored plan document that does not validate (a value of the wrong type, a
  value out of range) is no plan: the reads log ``entitlement.plan_invalid`` and answer
  ``None``, and the entitlement service takes its fallback chain. Registration (a new
  personal tenant) and the storage check of an upload keep working on a corrupt ``standard``
  instead of answering 500 for every tenant. A limit field this build does not know is
  ignored, the known ones still apply.
* **SEC-003** — a plan change is one ``UPDATE``: ``is_default`` and ``created_at`` stay, and
  two changes of different limits both survive.
* **SEC-004** — assigning a plan writes only while the plan exists and the tenant is not being
  erased; an assignment racing an uncommitted deletion of the same plan is a write conflict,
  not a tenant on a plan that no longer exists.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_plan_store_hardening_reach.py -v
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
import structlog
from arango import ArangoClient

from app.common.enums import EntitlementDimension
from app.common.exceptions import StorageQuotaExceededError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.plan_repository import _DELETE_UNUSED, ArangoPlanRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.plan import DEFAULT_PLAN_KEY
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.entitlement_service import EntitlementService
from app.domain.services.tenant_service import TenantService
from app.migrations.seed_plans import seed_plans
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the plan reads and single-statement writes are AQL over a real server"),
]

_DB_NAME = run_database_name("plan_store_hardening")
MB = 1024 * 1024


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    seed_plans(database)
    yield database
    system.delete_database(_DB_NAME)


def _corrupt_standard(db: Any, **limits: Any) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.PLANS).update({"_key": DEFAULT_PLAN_KEY, "limits": limits}, merge=False)


def _tenant(db: Any, key: str, **fields: Any) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.TENANTS).insert(
        {
            "_key": key,
            "name": key,
            "slug": key,
            "tenant_type": "organization",
            "owner_user_key": "u",
            "status": "active",
            "max_members": 50,
            "plan_key": DEFAULT_PLAN_KEY,
            **fields,
        }
    )


def _entitlements(db: Any) -> EntitlementService:  # type: ignore[no-untyped-def]
    return EntitlementService(plan_repo=ArangoPlanRepository(db), tenant_repo=ArangoTenantRepository(db))


# ── SEC-001 ──────────────────────────────────────────────────────────


def test_a_corrupt_plan_is_read_as_missing_and_logged(db) -> None:  # type: ignore[no-untyped-def]
    _corrupt_standard(db, members="fifty", storage_mb=-5)

    with structlog.testing.capture_logs() as logs:
        plan = ArangoPlanRepository(db).get(DEFAULT_PLAN_KEY)
        default = ArangoPlanRepository(db).get_default()

    assert (plan, default) == (None, None)
    invalid = [entry for entry in logs if entry["event"] == "entitlement.plan_invalid"]
    assert len(invalid) == 2
    assert invalid[0]["fields"] == ["limits.members", "limits.storage_mb"]
    assert "fifty" not in str(invalid)  # field names only, never the stored values


def test_quota_decisions_fall_back_to_the_instance_settings_on_a_corrupt_standard(db) -> None:  # type: ignore[no-untyped-def]
    _corrupt_standard(db, storage_mb="lots")
    _tenant(db, "t-1")

    service = _entitlements(db)

    assert service.limit("t-1", EntitlementDimension.STORAGE_MB) == 2048
    assert service.limit("t-1", EntitlementDimension.MEMBERS) == 50
    assert service.ai_budget_limits("t-1").tenant_calls_per_day == 500


def test_registration_founds_the_personal_tenant_on_a_corrupt_standard(db) -> None:  # type: ignore[no-untyped-def]
    _corrupt_standard(db, members=0)  # below the bound: the stored plan no longer validates
    service = TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        entitlements=_entitlements(db),
    )

    tenant = service.create_personal_tenant("u-new", "New Gardener")

    assert tenant.key
    assert tenant.plan_key == DEFAULT_PLAN_KEY


def test_the_storage_check_of_an_upload_works_on_a_corrupt_standard(db) -> None:  # type: ignore[no-untyped-def]
    from app.config.settings import settings

    _corrupt_standard(db, storage_mb={"nested": True})
    _tenant(db, "t-1")
    attachments = MagicMock()
    attachments.sum_bytes_by_tenant.return_value = 2048 * MB - 10
    service = AttachmentService(
        storage=MagicMock(), attachment_repo=attachments, settings=settings, entitlements=_entitlements(db)
    )

    service._enforce_quota("t-1", incoming_bytes=10)  # exactly at the instance quota: admitted
    with pytest.raises(StorageQuotaExceededError):
        service._enforce_quota("t-1", incoming_bytes=11)


def test_an_unknown_limit_field_is_ignored_and_the_known_ones_apply(db) -> None:  # type: ignore[no-untyped-def]
    _corrupt_standard(db, storage_mb=7, sensors=12)
    _tenant(db, "t-1")

    plan = ArangoPlanRepository(db).get(DEFAULT_PLAN_KEY)

    assert plan is not None and plan.limits.storage_mb == 7
    assert _entitlements(db).limit("t-1", EntitlementDimension.STORAGE_MB) == 7


def test_the_listing_leaves_a_corrupt_plan_out_instead_of_failing(db) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.PLANS).insert({"_key": "broken", "name": "", "limits": {}, "is_default": False})

    assert [plan.key for plan in ArangoPlanRepository(db).list_all()] == [DEFAULT_PLAN_KEY]


# ── SEC-003 ──────────────────────────────────────────────────────────


def test_a_change_keeps_the_default_mark_and_the_creation_time(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoPlanRepository(db)
    before = db.collection(col.PLANS).get(DEFAULT_PLAN_KEY)

    changed = repo.apply_plan_change(DEFAULT_PLAN_KEY, fields={"name": "Basis"}, limit_changes={"storage_mb": 9})

    after = db.collection(col.PLANS).get(DEFAULT_PLAN_KEY)
    assert changed is not None and changed.name == "Basis"
    assert (after["is_default"], after["created_at"]) == (True, before["created_at"])
    assert after["limits"]["storage_mb"] == 9


def test_two_changes_of_different_limits_both_survive(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoPlanRepository(db)

    repo.apply_plan_change(DEFAULT_PLAN_KEY, fields={}, limit_changes={"storage_mb": 9})
    repo.apply_plan_change(DEFAULT_PLAN_KEY, fields={}, limit_changes={"members": 7})

    limits = db.collection(col.PLANS).get(DEFAULT_PLAN_KEY)["limits"]
    assert (limits["storage_mb"], limits["members"]) == (9, 7)


def test_a_null_returns_a_dimension_to_the_instance_setting(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoPlanRepository(db)
    repo.apply_plan_change(DEFAULT_PLAN_KEY, fields={}, limit_changes={"storage_mb": 9})

    plan = repo.apply_plan_change(DEFAULT_PLAN_KEY, fields={}, limit_changes={"storage_mb": None})

    assert plan is not None and plan.limits.storage_mb is None


def test_changing_an_unknown_plan_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    assert ArangoPlanRepository(db).apply_plan_change("nope", fields={"name": "x"}, limit_changes={}) is None
    assert db.collection(col.PLANS).count() == 1


# ── SEC-004 ──────────────────────────────────────────────────────────


def test_a_plan_that_does_not_exist_is_not_assigned(db) -> None:  # type: ignore[no-untyped-def]
    _tenant(db, "t-1")

    assert ArangoPlanRepository(db).assign_to_tenant("t-1", "gone") is False
    assert db.collection(col.TENANTS).get("t-1")["plan_key"] == DEFAULT_PLAN_KEY


def test_a_tenant_being_erased_is_not_assigned(db) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.PLANS).insert({"_key": "club", "name": "Club", "limits": {}, "is_default": False})
    _tenant(db, "t-1", status="deleted")

    assert ArangoPlanRepository(db).assign_to_tenant("t-1", "club") is False
    assert db.collection(col.TENANTS).get("t-1")["plan_key"] == DEFAULT_PLAN_KEY


def test_an_existing_plan_is_assigned(db) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.PLANS).insert({"_key": "club", "name": "Club", "limits": {}, "is_default": False})
    _tenant(db, "t-1")

    assert ArangoPlanRepository(db).assign_to_tenant("t-1", "club") is True
    assert db.collection(col.TENANTS).get("t-1")["plan_key"] == "club"


def test_an_assignment_racing_the_deletion_of_its_plan_is_a_conflict(db) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.PLANS).insert({"_key": "club", "name": "Club", "limits": {}, "is_default": False})
    _tenant(db, "t-1")
    deletion = db.begin_transaction(read=[col.TENANTS], write=[col.PLANS], lock_timeout=1)
    try:
        removed = list(
            deletion.aql.execute(
                _DELETE_UNUSED,
                bind_vars={"@plans": col.PLANS, "@tenants": col.TENANTS, "key": "club", "default_key": "standard"},
            )
        )
        assert removed == ["club"]  # the deletion holds the plan document, not yet committed

        with pytest.raises(WriteConflictError):
            ArangoPlanRepository(db).assign_to_tenant("t-1", "club")
    finally:
        deletion.commit_transaction()

    assert db.collection(col.PLANS).get("club") is None
    assert db.collection(col.TENANTS).get("t-1")["plan_key"] == DEFAULT_PLAN_KEY
