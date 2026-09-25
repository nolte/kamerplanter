"""v0063 rewrites slug-form API-key scopes to tenant keys and revokes dead ones (#1852).

The rules live in the pure ``plan_scopes`` so they are decided without a database;
``up`` is checked through a double that answers exactly this migration's three
queries and refuses any other, so an unexpected query cannot pass vacuously.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0063_canonicalise_api_key_tenant_scope import (
    CanonicaliseApiKeyTenantScopeMigration,
    plan_scopes,
)

_TENANTS = [{"_key": "t_a", "slug": "club-a"}, {"_key": "t_b", "slug": "club-b"}]
_MEMBERS = {("owner", "t_a"), ("owner", "t_b")}


def _key(key: str, scope: str, *, user: str = "owner", revoked: bool = False) -> dict[str, Any]:
    return {"_key": key, "user_key": user, "tenant_scope": scope, "revoked": revoked}


def test_a_tenant_key_scope_is_left_alone() -> None:
    plan = plan_scopes([_key("k1", "t_a")], _TENANTS, _MEMBERS)

    assert (plan.rewrite, plan.revoke, plan.unchanged) == ({}, [], 1)


def test_a_slug_scope_of_a_tenant_the_owner_is_in_becomes_its_key() -> None:
    plan = plan_scopes([_key("k1", "club-b")], _TENANTS, _MEMBERS)

    assert plan.rewrite == {"k1": "t_b"}
    assert plan.revoke == []


@pytest.mark.parametrize(
    ("scope", "user"),
    [("gone-slug", "owner"), ("club-a", "stranger")],
    ids=["slug-of-no-tenant", "owner-not-a-member"],
)
def test_a_scope_that_resolves_to_nothing_the_owner_reaches_is_revoked(scope: str, user: str) -> None:
    plan = plan_scopes([_key("k1", scope, user=user)], _TENANTS, _MEMBERS)

    assert plan.rewrite == {}
    assert plan.revoke == ["k1"]


def test_an_already_revoked_key_is_canonicalised_but_not_revoked_again() -> None:
    plan = plan_scopes(
        [_key("k1", "club-a", revoked=True), _key("k2", "gone", revoked=True)],
        _TENANTS,
        _MEMBERS,
    )

    assert plan.rewrite == {"k1": "t_a"}
    assert plan.revoke == []
    assert plan.unchanged == 1


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs

    def update(self, patch: dict[str, Any], **kwargs: Any) -> None:  # noqa: ARG002
        self.docs[patch["_key"]].update({k: v for k, v in patch.items() if k != "_key"})


class _Db:
    def __init__(self, keys: dict[str, dict[str, Any]], memberships: list[dict[str, Any]] | None = None) -> None:
        self.keys = _Collection(keys)
        self.aql = self
        self.memberships = (
            memberships
            if memberships is not None
            else [{"user_key": u, "tenant_key": t, "is_active": True} for u, t in sorted(_MEMBERS)]
        )

    def has_collection(self, name: str) -> bool:
        return name in {"api_keys", "tenants", "memberships"}

    def collection(self, name: str) -> _Collection:
        assert name == "api_keys"
        return self.keys

    def execute(self, query: str, bind_vars: dict | None = None, **kwargs: Any) -> list[Any]:  # noqa: ARG002
        q = re.sub(r"\s+", " ", query).strip()
        if q.startswith("FOR k IN api_keys"):
            return [
                {"_key": k, **{f: d.get(f) for f in ("user_key", "tenant_scope", "revoked")}}
                for k, d in self.keys.docs.items()
                if d.get("tenant_scope")
            ]
        if q.startswith("FOR t IN tenants"):
            return list(_TENANTS)
        if q.startswith("FOR m IN memberships"):
            # Evaluate the filter the migration wrote against documents in the
            # three shapes that exist: flag true, flag false, flag absent. The
            # runtime (``Membership.is_active`` defaults to True; the repository
            # treats a missing flag as active) admits the absent one too.
            if "m.is_active != false" in q:
                admit = lambda doc: doc.get("is_active") is not False  # noqa: E731
            elif "m.is_active == true" in q:
                admit = lambda doc: doc.get("is_active") is True  # noqa: E731
            else:
                raise AssertionError(f"unexpected membership filter: {q}")
            return [[d["user_key"], d["tenant_key"]] for d in self.memberships if admit(d)]
        raise AssertionError(f"unexpected query: {q}")


def _db() -> _Db:
    return _Db(
        {
            "k_key": {"user_key": "owner", "tenant_scope": "t_a", "revoked": False},
            "k_slug": {"user_key": "owner", "tenant_scope": "club-b", "revoked": False},
            "k_dead": {"user_key": "owner", "tenant_scope": "gone", "revoked": False},
            "k_none": {"user_key": "owner", "tenant_scope": None, "revoked": False},
        }
    )


def test_up_writes_the_plan_and_a_second_run_is_a_no_op() -> None:
    db = _db()
    migration = CanonicaliseApiKeyTenantScopeMigration()

    first = migration.up(db)  # type: ignore[arg-type]
    second = migration.up(db)  # type: ignore[arg-type]

    assert db.keys.docs["k_slug"]["tenant_scope"] == "t_b"
    assert db.keys.docs["k_dead"]["revoked"] is True
    assert db.keys.docs["k_key"] == {"user_key": "owner", "tenant_scope": "t_a", "revoked": False}
    assert db.keys.docs["k_none"]["tenant_scope"] is None
    assert (first.changed, first.details["rewritten"], first.details["revoked"]) == (2, 1, 1)
    assert second.changed == 0


def test_dry_run_writes_nothing() -> None:
    db = _db()
    before = {k: dict(v) for k, v in db.keys.docs.items()}

    report = CanonicaliseApiKeyTenantScopeMigration().up(db, dry_run=True)  # type: ignore[arg-type]

    assert db.keys.docs == before
    assert report.changed == 0
    assert report.details["rewritten"] == 1


def test_a_membership_without_the_flag_counts_as_active_as_at_runtime() -> None:
    # /code-review of #1866: a legacy membership document carries no ``is_active``;
    # the runtime reads it as active, so the key works today. The migration must
    # rewrite its slug scope, not revoke it.
    db = _Db(
        {"k": {"user_key": "owner", "tenant_scope": "club-b", "revoked": False}},
        memberships=[
            {"user_key": "owner", "tenant_key": "t_b"},
            {"user_key": "owner", "tenant_key": "t_a", "is_active": False},
        ],
    )

    CanonicaliseApiKeyTenantScopeMigration().up(db)  # type: ignore[arg-type]

    assert db.keys.docs["k"] == {"user_key": "owner", "tenant_scope": "t_b", "revoked": False}


def test_an_explicitly_inactive_membership_does_not_rescue_the_key() -> None:
    db = _Db(
        {"k": {"user_key": "owner", "tenant_scope": "club-a", "revoked": False}},
        memberships=[{"user_key": "owner", "tenant_key": "t_a", "is_active": False}],
    )

    CanonicaliseApiKeyTenantScopeMigration().up(db)  # type: ignore[arg-type]

    assert db.keys.docs["k"]["revoked"] is True
