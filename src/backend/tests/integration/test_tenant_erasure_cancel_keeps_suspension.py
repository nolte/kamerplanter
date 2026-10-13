"""REQ-056 §4.3 (AK-05) — cancelling a deletion restores the state before it, on a real ArangoDB.

Measured on develop before this change: ``cancel_tenant_erasure`` wrote ``active`` whatever the
deletion had frozen. A platform admin scheduled the deletion of a **suspended** tenant, its own
management cancelled through ``POST /tenants/{slug}/erasure/cancel`` (not behind the resolver,
the right proven from the stored membership) and the tenant came back ``active``.

The unit tests (``test_tenant_erasure_grace.py``) drive the rule over a model-validating double.
This one runs the real ``TenantService`` over the real tenant, membership and erasure-record
repositories, so ``status_before_deletion`` has to survive ``update_fields`` and ``get_by_key``
of the ArangoDB repository — a field the repository dropped would make the rule inert.

Measured here, too: ``ArangoTenantRepository.update_fields`` wrote its merge without the
``None`` values, so a cancellation never cleared ``deletion_scheduled_at`` (the reactivated
tenant kept its deletion date) and would have left ``status_before_deletion`` behind. The
double of the unit tests merges through ``model_validate`` and could not show it.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_tenant_erasure_cancel_keeps_suspension.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.enums import TenantStatus
from app.common.exceptions import ForbiddenError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.tenant_erasure import TenantErasureCancelConfirmation
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.tenant_erasure_doubles import AUTHORIZED_REQUESTER, authorized

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the lifecycle fields round-trip through the real tenant repository"),
]

_DB_NAME = run_database_name("tenant_erasure_cancel_keeps_suspension")
NOW = datetime(2026, 10, 11, 9, 0, tzinfo=UTC)
ORG = "t-org"


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _service(db) -> TenantService:  # type: ignore[no-untyped-def]
    return TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        tenant_erasure_repo=ArangoTenantErasureRepository(db),
        tenant_erasure_executor=MagicMock(),
        tombstone_salt="integration-tombstone-salt-0123456789abcdef",
        tenant_erasure_grace_days=90,
        observation_repo=MagicMock(**{"delete_by_tenant.return_value": 0}),
    )


def _seed(db, status: TenantStatus) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.TENANTS).insert(
        {
            "_key": ORG,
            "name": "Lindenhof",
            "slug": ORG,
            "tenant_type": "organization",
            "owner_user_key": AUTHORIZED_REQUESTER.key,
            "status": status.value,
        }
    )
    db.collection(col.USERS).insert(
        {"_key": AUTHORIZED_REQUESTER.key, "email": AUTHORIZED_REQUESTER.email, "display_name": "R", "is_active": True}
    )
    # The requester is the org's management (lead + management) and a platform admin (lead in ``platform``).
    for key, tenant_key, scopes in (("m-org", ORG, ["management"]), ("m-platform", "platform", [])):
        db.collection(col.MEMBERSHIPS).insert(
            {
                "_key": key,
                "user_key": AUTHORIZED_REQUESTER.key,
                "tenant_key": tenant_key,
                "role": "lead",
                "admin_scopes": scopes,
                "is_active": True,
                "joined_at": "2025-01-01T00:00:00+00:00",
            }
        )


def _cancel_kwargs() -> dict[str, Any]:
    from app.domain.services.step_up_service import default_step_up_verifier
    from tests.support.step_up import AdmitEveryTarget

    code, _ = default_step_up_verifier(target_policy=AdmitEveryTarget()).issue_code(
        AUTHORIZED_REQUESTER,
        action="tenant_erasure_cancel",
        target=ORG,
        authenticated_with_api_key=False,
        client_ip="203.0.113.10",
    )
    return {
        "requester": AUTHORIZED_REQUESTER,
        "authenticated_with_api_key": False,
        "confirmation": TenantErasureCancelConfirmation(step_up_code=code),
        "origin": "tenant_management",
        "client_ip": "203.0.113.10",
    }


@pytest.mark.parametrize("before", [TenantStatus.SUSPENDED, TenantStatus.ACTIVE])
def test_the_management_cancelling_restores_the_state_the_deletion_froze(db, before: TenantStatus) -> None:  # type: ignore[no-untyped-def]
    _seed(db, before)
    service = _service(db)
    service.delete_tenant(ORG, **authorized(ORG, origin="platform_admin"), now=NOW)
    stored = db.collection(col.TENANTS).get(ORG)
    assert stored["status"] == TenantStatus.PENDING_DELETION.value
    assert stored["status_before_deletion"] == before.value

    service.cancel_tenant_erasure(ORG, **_cancel_kwargs())

    tenant = ArangoTenantRepository(db).get_by_key(ORG)
    assert tenant is not None
    assert tenant.status == before
    assert tenant.deletion_scheduled_at is None
    assert tenant.status_before_deletion is None


def test_a_pending_document_stored_before_the_field_existed_is_cancelled_by_a_platform_admin_only(db) -> None:  # type: ignore[no-untyped-def]
    """SEC-001 — fail closed: without the remembered state the management cannot cancel."""
    _seed(db, TenantStatus.ACTIVE)
    service = _service(db)
    service.delete_tenant(ORG, **authorized(ORG, origin="platform_admin"), now=NOW)
    db.collection(col.TENANTS).update({"_key": ORG, "status_before_deletion": None}, keep_none=False)
    assert "status_before_deletion" not in db.collection(col.TENANTS).get(ORG)
    kwargs = _cancel_kwargs()

    with pytest.raises(ForbiddenError):
        service.cancel_tenant_erasure(ORG, **kwargs)
    assert db.collection(col.TENANTS).get(ORG)["status"] == TenantStatus.PENDING_DELETION.value

    restored = service.cancel_tenant_erasure(ORG, **{**kwargs, "origin": "platform_admin"})
    assert restored.status == TenantStatus.ACTIVE
    assert "deletion_scheduled_at" not in db.collection(col.TENANTS).get(ORG)  # removed, not null


def test_a_cancellation_over_a_stale_snapshot_is_409_and_moves_nothing(db) -> None:  # type: ignore[no-untyped-def]
    """SEC-002 — the read saw ``pending_deletion``; before the write the run claimed it (``deleted``)."""
    _seed(db, TenantStatus.SUSPENDED)
    service = _service(db)
    service.delete_tenant(ORG, **authorized(ORG, origin="platform_admin"), now=NOW)
    stale = ArangoTenantRepository(db).get_by_key(ORG)
    db.collection(col.TENANTS).update({"_key": ORG, "status": TenantStatus.DELETED.value})
    service._tenant_repo.get_by_key = lambda key: stale  # type: ignore[method-assign]

    with pytest.raises(WriteConflictError):
        service.cancel_tenant_erasure(ORG, **_cancel_kwargs())

    stored = db.collection(col.TENANTS).get(ORG)
    assert stored["status"] == TenantStatus.DELETED.value
    assert stored["status_before_deletion"] == TenantStatus.SUSPENDED.value
    assert db.collection(col.TENANT_ERASURE_RECORDS).get(TenantErasureEngine.record_key(ORG)) is not None


def test_the_suspension_switch_over_a_stale_snapshot_is_409(db) -> None:  # type: ignore[no-untyped-def]
    """SEC-002 — a reactivation read ``suspended``; meanwhile a platform admin scheduled the deletion."""
    _seed(db, TenantStatus.SUSPENDED)
    service = _service(db)
    stale = ArangoTenantRepository(db).get_by_key(ORG)
    service.delete_tenant(ORG, **authorized(ORG, origin="platform_admin"), now=NOW)
    service._tenant_repo.get_by_key = lambda key: stale  # type: ignore[method-assign]
    service._step_up_verifier = MagicMock()

    with pytest.raises(WriteConflictError):
        service.admin_update_tenant(
            ORG,
            {"is_active": True},
            requester=AUTHORIZED_REQUESTER,
            current_password=None,
            step_up_code=None,
            step_up_token=None,
            authenticated_with_api_key=False,
            client_ip=None,
        )
    assert db.collection(col.TENANTS).get(ORG)["status"] == TenantStatus.PENDING_DELETION.value


def test_the_remembered_state_is_the_stored_one_at_the_write_not_the_read(db) -> None:  # type: ignore[no-untyped-def]
    """SEC-002 — ``status_before_deletion`` comes from ``OLD.status`` inside the statement."""
    _seed(db, TenantStatus.ACTIVE)
    repo = ArangoTenantRepository(db)
    db.collection(col.TENANTS).update({"_key": ORG, "status": TenantStatus.SUSPENDED.value})  # after any read

    moved = repo.transition_status(
        ORG,
        expected={TenantStatus.ACTIVE, TenantStatus.SUSPENDED},
        status=TenantStatus.PENDING_DELETION,
        deletion_scheduled_at=NOW,
        previous="remember",
    )

    assert moved is not None and moved.status_before_deletion == TenantStatus.SUSPENDED
    assert (
        repo.transition_status(
            ORG,
            expected={TenantStatus.ACTIVE},
            status=TenantStatus.SUSPENDED,
            deletion_scheduled_at="keep",
            previous="keep",
        )
        is None
    )  # no longer ``active``: nothing matches


def test_update_fields_removes_an_allowlisted_null_and_refuses_any_other(db) -> None:  # type: ignore[no-untyped-def]
    """SEC-005, on the real store: one write; ``description: None`` removes the attribute."""
    _seed(db, TenantStatus.ACTIVE)
    repo = ArangoTenantRepository(db)
    repo.update_fields(ORG, {"description": "Gemeinschaftsgarten"})

    repo.update_fields(ORG, {"description": None, "max_members": 7})

    stored = db.collection(col.TENANTS).get(ORG)
    assert "description" not in stored and stored["max_members"] == 7
    with pytest.raises(ValueError):
        repo.update_fields(ORG, {"name": None})


def test_a_document_still_carrying_the_retired_bool_is_compared_like_the_model_reads_it(db) -> None:  # type: ignore[no-untyped-def]
    """A pre-v0085 document (``is_active: false``, no ``status``) is ``suspended`` for the compare too."""
    db.collection(col.TENANTS).insert(
        {
            "_key": ORG,
            "name": "Alt",
            "slug": ORG,
            "tenant_type": "organization",
            "owner_user_key": "o",
            "is_active": False,
        }
    )
    repo = ArangoTenantRepository(db)

    moved = repo.transition_status(
        ORG,
        expected={TenantStatus.SUSPENDED},
        status=TenantStatus.ACTIVE,
        deletion_scheduled_at="keep",
        previous="keep",
    )

    assert moved is not None and moved.status == TenantStatus.ACTIVE
    stored = db.collection(col.TENANTS).get(ORG)
    assert stored["status"] == "active" and "is_active" not in stored
