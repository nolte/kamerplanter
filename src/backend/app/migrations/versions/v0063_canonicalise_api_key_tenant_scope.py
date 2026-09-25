"""v0063 — store every API key's ``tenant_scope`` as a tenant key, not a slug (#1852).

Until #1852 ``POST /api/v1/auth/api-keys`` stored ``tenant_scope`` exactly as the
caller typed it, and both enforcement surfaces matched it on the tenant's slug
*or* key. Two consequences for a key scoped by slug:

* the tenant erasure deletes scoped keys by ``doc.tenant_scope == <tenant key>``
  (``tenant_erasure_engine``), so a slug-scoped key survived its tenant;
* a slug is a name, not an identity — a rename re-derives it and a deleted
  tenant's slug can be issued again — so the key followed the name to whichever
  tenant held it now.

Key creation now resolves the scope to a tenant key and ``api_key_scope_admits``
matches the key only. This migration brings the stored scopes to that shape.

**Per scoped key, in this order:**

1. The scope is the key of an existing tenant → left alone.
2. The scope is the slug of an existing tenant **and** the key's owner holds an
   active membership there → rewritten to that tenant's key. That is the tenant
   the key admits today, so nothing the key can reach changes.
3. Anything else (the slug names no tenant, or a tenant the owner is not an
   active member of) → the key is **revoked**. Under the old predicate it
   admitted nothing its owner could reach, and under the new one it never can;
   revoking it makes that visible in the key list instead of leaving a dead
   credential that looks alive. The scope value is kept for the record.

Already-revoked keys are canonicalised by the same rules (so the erasure finds
them), never revoked twice.

**What this cannot decide.** A slug that was re-issued to another tenant the
owner also belongs to is indistinguishable from the original: rule 2 binds the
key to the tenant holding the slug *now* — the tenant the key already admitted
before this migration. It narrows nothing and widens nothing.

**Idempotent (M-3).** After a run every scope is a tenant key or its key is
revoked; a second run changes nothing.

**Dry run (M-5).** Computes the plan and writes nothing.

**Not reversible (M-6).** The typed slug is overwritten; the revocations are
deliberate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ScopePlan:
    """What the migration does to the scoped keys it scanned."""

    rewrite: dict[str, str] = field(default_factory=dict)  # api-key _key -> tenant key
    revoke: list[str] = field(default_factory=list)
    unchanged: int = 0


def plan_scopes(
    keys: list[dict[str, Any]],
    tenants: list[dict[str, Any]],
    active_memberships: set[tuple[str, str]],
) -> ScopePlan:
    """Decide per scoped key (pure, so the rules are testable without a database).

    Args:
        keys: ``{_key, user_key, tenant_scope, revoked}`` of every key whose
            ``tenant_scope`` is non-empty.
        tenants: ``{_key, slug}`` of every tenant.
        active_memberships: ``(user_key, tenant_key)`` of every active membership.
    """
    tenant_keys = {str(t["_key"]) for t in tenants}
    by_slug = {str(t["slug"]): str(t["_key"]) for t in tenants if t.get("slug")}
    rewrite: dict[str, str] = {}
    revoke: list[str] = []
    unchanged = 0
    for doc in keys:
        scope = str(doc["tenant_scope"])
        if scope in tenant_keys:
            unchanged += 1
            continue
        target = by_slug.get(scope)
        if target is not None and (str(doc.get("user_key", "")), target) in active_memberships:
            rewrite[str(doc["_key"])] = target
        elif not doc.get("revoked"):
            revoke.append(str(doc["_key"]))
        else:
            unchanged += 1
    return ScopePlan(rewrite=rewrite, revoke=revoke, unchanged=unchanged)


class CanonicaliseApiKeyTenantScopeMigration(Migration):
    version = "0063"
    name = "canonicalise_api_key_tenant_scope"
    description = (
        "Rewrite slug-form API-key tenant scopes to tenant keys; revoke scopes that resolve to no tenant (#1852)."
    )
    reversible = False

    _KEYS_QUERY = f"""
    FOR k IN {col.API_KEYS}
      FILTER k.tenant_scope != null AND k.tenant_scope != ""
      RETURN {{_key: k._key, user_key: k.user_key, tenant_scope: k.tenant_scope, revoked: k.revoked}}
    """
    _TENANTS_QUERY = f"FOR t IN {col.TENANTS} RETURN {{_key: t._key, slug: t.slug}}"
    #: ``!= false`` rather than ``== true``: a membership written before the flag
    #: existed carries none, and the runtime reads it as active (the model
    #: default; ``membership_repository``). ``== true`` would revoke a key that
    #: works today (/code-review of #1866).
    _MEMBERSHIPS_QUERY = f"""
    FOR m IN {col.MEMBERSHIPS}
      FILTER m.is_active != false
      RETURN [m.user_key, m.tenant_key]
    """

    def _plan(self, db: StandardDatabase) -> tuple[int, ScopePlan]:
        if not db.has_collection(col.API_KEYS):
            return (0, ScopePlan())
        keys = list(db.aql.execute(self._KEYS_QUERY))
        if not keys:
            return (0, ScopePlan())
        tenants = list(db.aql.execute(self._TENANTS_QUERY)) if db.has_collection(col.TENANTS) else []
        memberships = (
            {(str(u), str(t)) for u, t in db.aql.execute(self._MEMBERSHIPS_QUERY)}
            if db.has_collection(col.MEMBERSHIPS)
            else set()
        )
        return (len(keys), plan_scopes(keys, tenants, memberships))

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        scanned, plan = self._plan(db)
        if not dry_run and (plan.rewrite or plan.revoke):
            api_keys = db.collection(col.API_KEYS)
            for key, tenant_key in plan.rewrite.items():
                api_keys.update({"_key": key, "tenant_scope": tenant_key}, silent=True)
            for key in plan.revoke:
                api_keys.update({"_key": key, "revoked": True}, silent=True)
        logger.info(
            "canonicalise_api_key_tenant_scope",
            scanned=scanned,
            rewritten=len(plan.rewrite),
            revoked=len(plan.revoke),
            dry_run=dry_run,
        )
        changed = len(plan.rewrite) + len(plan.revoke)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={
                "rewritten": len(plan.rewrite),
                "revoked": len(plan.revoke),
                "unchanged": plan.unchanged,
                "revoked_keys": plan.revoke,
            },
        )


migration = CanonicaliseApiKeyTenantScopeMigration()
