"""``create_with_lead_membership``: a tenant exists with founder, edges and audit row, or not at all (#2118).

The behaviour against a real server - what a failure between two of the five writes leaves behind - is measured
in ``tests/integration/test_tenant_founding_atomicity_reach.py``. What is doubled here is the plumbing: that
every collection written is declared to the transaction, that **a failure on any one write aborts and commits
nothing**, that a unique-index rejection is typed, and that a failing abort never masks the primary error.
The fake transaction stages documents and only a commit publishes them, so "no tenant document" is read off
what survived, not off a call count.
"""

from __future__ import annotations

import itertools
from typing import Any

import pytest

from app.common.enums import AdminScope, SecurityAuditAction, SecurityAuditVia, TenantRole, TenantType
from app.common.exceptions import DuplicateError
from app.data_access.arango import collections as col
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.models.membership import Membership
from app.domain.models.security_audit import SecurityAuditEntry
from app.domain.models.tenant import Tenant
from tests.unit.data_access.arango.test_care_profile_linked_write import _insert_error


class _Collection:
    def __init__(self, name: str, tx: _Transaction) -> None:
        self._name, self._tx = name, tx

    def insert(self, data: dict[str, Any], return_new: bool = False):
        if self._name in self._tx.refuse:
            raise self._tx.refuse[self._name]
        document = dict(data)
        document.pop("_key", None)
        document["_key"] = f"{self._name[:2]}-{next(self._tx.keys)}"
        document["_id"] = f"{self._name}/{document['_key']}"
        self._tx.staged.setdefault(self._name, []).append(document)
        return {"new": dict(document)} if return_new else {"_key": document["_key"]}


class _Transaction:
    def __init__(self, refuse: dict[str, Exception], abort_error: Exception | None) -> None:
        self.refuse, self.abort_error = refuse, abort_error
        self.staged: dict[str, list[dict[str, Any]]] = {}
        self.keys = itertools.count(1)
        self.committed = self.aborted = False

    def collection(self, name: str) -> _Collection:
        return _Collection(name, self)

    def commit_transaction(self) -> None:
        self.committed = True

    def abort_transaction(self) -> None:
        self.aborted = True
        if self.abort_error is not None:
            raise self.abort_error


class _Db:
    def __init__(self, refuse: dict[str, Exception], abort_error: Exception | None) -> None:
        self._refuse, self._abort_error = refuse, abort_error
        self.transaction: _Transaction | None = None
        self.declared: list[str] = []

    def collection(self, name: str) -> Any:  # pragma: no cover
        raise AssertionError(f"the founding must not write {name!r} outside the transaction")

    def begin_transaction(self, write: list[str] | None = None, **_: Any) -> _Transaction:
        self.declared = list(write or [])
        self.transaction = _Transaction(self._refuse, self._abort_error)
        return self.transaction


def _found(
    *, refuse: dict[str, Exception] | None = None, abort_error: Exception | None = None, audit: bool = True
) -> tuple[_Db, tuple[Tenant, Membership]]:
    db = _Db(refuse or {}, abort_error)
    repo = ArangoTenantRepository(db)  # type: ignore[arg-type]
    tenant = Tenant(name="Garden", slug="garden", tenant_type=TenantType.PERSONAL, owner_user_key="u-1", max_members=1)
    membership = Membership(
        user_key="u-1", tenant_key="", role=TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT], is_active=True
    )

    def row(stored_tenant: Tenant, stored_membership: Membership) -> SecurityAuditEntry:
        return SecurityAuditEntry(
            action=SecurityAuditAction.MEMBERSHIP_ADDED,
            via=SecurityAuditVia.REGISTRATION,
            actor_user_key="u-1",
            target_user_key="u-1",
            tenant_key=stored_tenant.key or "",
            membership_key=stored_membership.key,
        )

    return db, repo.create_with_lead_membership(tenant, membership, audit=row if audit else None)


def _published(db: _Db) -> dict[str, list[dict[str, Any]]]:
    """What another connection could see: staged documents appear only after a commit."""
    assert db.transaction is not None
    return db.transaction.staged if db.transaction.committed else {}


def test_all_five_documents_are_declared_written_and_committed_together() -> None:
    db, (tenant, membership) = _found()

    assert sorted(db.declared) == sorted(
        [col.TENANTS, col.MEMBERSHIPS, col.HAS_MEMBERSHIP, col.MEMBERSHIP_IN, col.SECURITY_AUDIT_LOG]
    ), "a collection written inside a stream transaction but not declared makes ArangoDB refuse the write"
    assert db.transaction is not None and db.transaction.committed and not db.transaction.aborted
    staged = _published(db)
    assert {name: len(rows) for name, rows in staged.items()} == {
        col.TENANTS: 1,
        col.MEMBERSHIPS: 1,
        col.HAS_MEMBERSHIP: 1,
        col.MEMBERSHIP_IN: 1,
        col.SECURITY_AUDIT_LOG: 1,
    }
    # the membership is the *new* tenant's, and the edges join the three keys
    assert membership.tenant_key == tenant.key
    (has,) = staged[col.HAS_MEMBERSHIP]
    (into,) = staged[col.MEMBERSHIP_IN]
    assert (has["_from"], has["_to"]) == (f"{col.USERS}/u-1", f"{col.MEMBERSHIPS}/{membership.key}")
    assert (into["_from"], into["_to"]) == (f"{col.MEMBERSHIPS}/{membership.key}", f"{col.TENANTS}/{tenant.key}")
    (audit_row,) = staged[col.SECURITY_AUDIT_LOG]
    assert audit_row["tenant_key"] == tenant.key and audit_row["membership_key"] == membership.key
    assert "created_at" in audit_row


def test_without_an_audit_builder_no_audit_row_is_written() -> None:
    db, _ = _found(audit=False)

    assert col.SECURITY_AUDIT_LOG not in _published(db)


@pytest.mark.parametrize(
    "failing",
    [
        pytest.param(col.TENANTS, id="the tenant"),
        pytest.param(col.MEMBERSHIPS, id="the membership (the 2nd insert)"),
        pytest.param(col.HAS_MEMBERSHIP, id="the first edge"),
        pytest.param(col.MEMBERSHIP_IN, id="the second edge"),
        pytest.param(col.SECURITY_AUDIT_LOG, id="the audit row"),
    ],
)
def test_a_failure_on_any_one_write_publishes_none_of_them(failing: str) -> None:
    db = _Db({failing: RuntimeError("injected failure")}, None)
    repo = ArangoTenantRepository(db)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="injected"):
        repo.create_with_lead_membership(
            Tenant(name="G", slug="g", tenant_type=TenantType.PERSONAL, owner_user_key="u-1"),
            Membership(user_key="u-1", tenant_key=""),
            audit=lambda t, m: SecurityAuditEntry(
                action=SecurityAuditAction.MEMBERSHIP_ADDED,
                via=SecurityAuditVia.REGISTRATION,
                actor_user_key="u-1",
                target_user_key="u-1",
                tenant_key=t.key or "",
            ),
        )

    assert db.transaction is not None
    assert db.transaction.aborted and not db.transaction.committed
    assert _published(db) == {}, "a failure between two writes must leave no tenant document, no member, no edge"


def test_a_taken_slug_is_a_typed_duplicate_not_a_driver_error() -> None:
    with pytest.raises(DuplicateError):
        _found(refuse={col.TENANTS: _insert_error(1210)})


def test_a_failing_abort_does_not_mask_the_error_that_got_us_there() -> None:
    with pytest.raises(RuntimeError, match="the write failed"):
        _found(refuse={col.MEMBERSHIP_IN: RuntimeError("the write failed")}, abort_error=ConnectionError("gone"))
