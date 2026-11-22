"""v0114 — move the rooting-protocol author's account key out of ``author`` (spec/privacy/09 §5a, #2976).

**Why.** Both write paths of a rooting protocol (``propagation/tenant_router.py``, create and update) stamped
``author = ctx.user_key``: the raw account key of whoever last saved it. The response returned it to every member,
and the erasure never reached it — ``scripts/check_privacy_inventory.py`` R6 finds an account reference by the shape
of its name, and ``author`` has none of them. The code now stamps ``author_user_key`` (the R6 shape; the erasure
writes the marker, the API shows a display name). This migration carries the rows written before.

**Step** (per tenant, every tenant status except ``deleted`` — a privacy correction, PRIV-716): every
``rooting_protocols`` row of the tenant that still carries ``author`` loses it, and ``author_user_key`` becomes

1. the stored ``author_user_key`` when one is already there (a row saved by the new code is never re-keyed);
2. else ``author`` when it names an account that still exists (bucket ``rooting_protocols.author_keyed``);
3. else the marker ``_anonymized`` when ``author`` is a non-empty string — the account it named is erased or gone,
   and the key of an erased account is exactly what the erasure would have replaced
   (``rooting_protocols.author_to_marker``);
4. else ``null`` (``rooting_protocols.author_dropped``; also every row of case 1).

The key is never taken from anything but the stored account key: ``author`` was never a typed name (no request
schema carried it), so PRIV-705 does not apply. Global templates (``tenant_key == ""``) belong to no tenant; no
path wrote an author into one, and they are left alone.

**Phases** (``details.phases``, PRIV-718). ``precheck`` — the collections exist, the model of this build stores
``author_user_key`` (default ``None``) and no longer reads ``author``, and the inventory of this build reaches the
field (an erasure marker rule, an account reference of the tenant export); else ``precondition_unmet`` and nothing
is written. ``dry_run`` — the counts, nothing written. ``apply`` — one stream transaction per tenant; a failing
tenant is rolled back, listed in ``tenants_failed``, and the others go on; then ``status = partial`` and the report
is ``incomplete``, so the runner records nothing and the next boot retries. ``verify`` — the rows still carrying
``author`` counted again; anything left is ``verify_failed``. ``monitor`` — nothing to hand over: the field is gone,
and R6 plus ``test_caller_account_stamps_use_a_reference_shaped_name`` refuse its return.

**Frozen (NFR-016 M-7).** The field names, the marker and the ``deleted`` tenant state are literals here, as the code
stood on 2026-11-16.

Idempotent (M-3): a corrected row carries no ``author``; a second run changes nothing. Dry run (M-5): counts only.
Irreversible (M-6): putting the key back into ``author`` would recreate the leak this corrects; a build before this
one reads a protocol without ``author`` as one without an author. The persisted dry-run report is the evidence
(spec/privacy/09 §11).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.common.log_privacy import log_tenant
from app.data_access.arango import collections as col
from app.data_access.arango.transactions import stream_transaction
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.framework.report_store import MAX_SAMPLES_PER_BUCKET, redact_details

logger = structlog.get_logger(__name__)

#: Frozen here (M-7): ``ANONYMIZED_MARKER`` of ``app.domain.models.privacy`` and ``TenantStatus.DELETED`` as they
#: stood on 2026-11-16, and the two field names of ``RootingProtocol`` before and after #2976.
_MARKER = "_anonymized"
_TENANT_DELETED = "deleted"
_OLD_FIELD = "author"
_KEY_FIELD = "author_user_key"

BUCKET_KEYED = "rooting_protocols.author_keyed"
BUCKET_TO_MARKER = "rooting_protocols.author_to_marker"
BUCKET_DROPPED = "rooting_protocols.author_dropped"
#: Every row the step corrects falls in exactly one of these, in this order.
STEP_BUCKETS: tuple[str, ...] = (BUCKET_KEYED, BUCKET_TO_MARKER, BUCKET_DROPPED)

#: One bulk update per tenant; the 10 s default of the helper is sized for a plan batch.
_TENANT_TIME_BUDGET_SECONDS = 600.0

_REQUIRED_COLLECTIONS: tuple[str, ...] = (col.TENANTS, col.ROOTING_PROTOCOLS, col.USERS)

# ── AQL ─────────────────────────────────────────────────────────────

_TENANT_KEYS = """
FOR t IN @@tenants
  FILTER t.status != @deleted
  SORT t._key
  RETURN t._key
"""

#: The tenant's rows that still carry the old field, with the bucket each one falls in and its new key.
_MATCH = """
FOR doc IN @@collection
  FILTER doc.tenant_key == @tenant_key
  FILTER HAS(doc, @old_field)
  LET author = doc[@old_field]
  LET named = IS_STRING(author) AND author != ""
  LET kept = doc[@key_field]
  LET live = named AND author != @marker AND DOCUMENT(CONCAT(@users, author)) != null
  LET bucket = kept != null ? @dropped : (live ? @keyed : (named ? @to_marker : @dropped))
  LET new_key = kept != null ? kept : (live ? author : (named ? @marker : null))
"""

_HITS = (
    "LET hits = ("
    + _MATCH
    + """
  RETURN { key: doc._key, bucket: bucket }
)
RETURN {
  keyed: LENGTH(hits[* FILTER CURRENT.bucket == @keyed]),
  to_marker: LENGTH(hits[* FILTER CURRENT.bucket == @to_marker]),
  dropped: LENGTH(hits[* FILTER CURRENT.bucket == @dropped]),
  sample: SLICE(hits[*].key, 0, @limit)
}
"""
)

#: ``UNSET`` takes the old field away; ``REPLACE`` keeps an explicit ``null`` key.
_UPDATE = (
    _MATCH
    + """
  REPLACE doc WITH UNSET(MERGE(doc, { [@key_field]: new_key }), @old_field) IN @@collection
  RETURN bucket
"""
)

_HIT_FIELDS: dict[str, str] = {BUCKET_KEYED: "keyed", BUCKET_TO_MARKER: "to_marker", BUCKET_DROPPED: "dropped"}


def _binds(tenant_key: str) -> dict[str, Any]:
    return {
        "@collection": col.ROOTING_PROTOCOLS,
        "users": f"{col.USERS}/",
        "tenant_key": tenant_key,
        "old_field": _OLD_FIELD,
        "key_field": _KEY_FIELD,
        "marker": _MARKER,
        "keyed": BUCKET_KEYED,
        "to_marker": BUCKET_TO_MARKER,
        "dropped": BUCKET_DROPPED,
        "limit": MAX_SAMPLES_PER_BUCKET,
    }


def _used_binds(query: str, binds: dict[str, Any]) -> dict[str, Any]:
    """ArangoDB refuses a bind parameter the query does not use; keep only the ones it names."""
    return {name: value for name, value in binds.items() if f"@{name}" in query}


class TenantHits:
    """What the step would change in one tenant: the rows per bucket and sample row keys."""

    def __init__(self, counts: dict[str, int], sample: list[str]) -> None:
        self.counts = counts
        self.sample = sample

    @property
    def total(self) -> int:
        return sum(self.counts.values())


class RootingAuthorStore:
    """The AQL of v0114: tenant list, per-tenant counts and the per-tenant transaction."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def missing_collections(self) -> list[str]:
        return [name for name in _REQUIRED_COLLECTIONS if not self._db.has_collection(name)]

    def tenant_keys(self) -> list[str]:
        cursor = self._db.aql.execute(_TENANT_KEYS, bind_vars={"@tenants": col.TENANTS, "deleted": _TENANT_DELETED})
        return [str(key) for key in cast(Cursor, cursor)]

    def hits(self, tenant_key: str) -> TenantHits:
        binds = _used_binds(_HITS, _binds(tenant_key))
        found: dict[str, Any] | None = next(iter(cast(Cursor, self._db.aql.execute(_HITS, bind_vars=binds))), None)
        row: dict[str, Any] = found or {}
        counts = {bucket: int(row.get(field, 0)) for bucket, field in _HIT_FIELDS.items()}
        return TenantHits(counts, [str(key) for key in row.get("sample", [])])

    def apply(self, tenant_key: str) -> dict[str, int]:
        """The step for one tenant in one stream transaction; the count per bucket."""
        changed: dict[str, int] = dict.fromkeys(STEP_BUCKETS, 0)
        with stream_transaction(
            self._db,
            write=(col.ROOTING_PROTOCOLS,),
            read=(col.USERS,),
            entity="rooting_protocol_author_key",
            time_budget_seconds=_TENANT_TIME_BUDGET_SECONDS,
        ) as txn:
            binds = _used_binds(_UPDATE, _binds(tenant_key))
            for bucket in txn.aql.execute(_UPDATE, bind_vars=binds):
                changed[str(bucket)] = changed.get(str(bucket), 0) + 1
        return changed


def _unmet_build() -> list[str]:
    """The model and the inventory of this build carry what v0114 writes (PRIV-718 precheck)."""
    from app.domain.engines.erasure_engine import ErasureEngine
    from app.domain.engines.tenant_export_engine import TenantExportEngine
    from app.domain.models.propagation import RootingProtocol

    unmet: list[str] = []
    fields = RootingProtocol.model_fields
    key_info = fields.get(_KEY_FIELD)
    if key_info is None or key_info.default is not None:
        unmet.append(f"model.rooting_protocols.{_KEY_FIELD}")
    if _OLD_FIELD in fields:
        unmet.append(f"model.rooting_protocols.{_OLD_FIELD}.still_read")
    rules = [
        rule
        for rule in ErasureEngine.ANONYMIZE_COLLECTIONS
        if (rule.collection, rule.user_field) == (col.ROOTING_PROTOCOLS, _KEY_FIELD)
    ]
    if not rules or any(rule.anonymized_value != _MARKER for rule in rules):
        unmet.append(f"inventory.erasure.rooting_protocols.{_KEY_FIELD}.marker")
    reference = TenantExportEngine.references_of(col.ROOTING_PROTOCOLS).get(_KEY_FIELD)
    if reference is None or reference.kind != "account":
        unmet.append(f"inventory.tenant_export.rooting_protocols.{_KEY_FIELD}")
    return unmet


class RootingProtocolAuthorKeyMigration(Migration):
    version = "0114"
    name = "rooting_protocol_author_key"
    description = (
        "Move the account key of rooting_protocols.author into author_user_key (the marker when the account is "
        "gone) and drop author, so the erasure reaches it and the API no longer shows it "
        "(spec/privacy/09 section 5a, #2976)."
    )
    reversible = False
    kind = "privacy_correction"

    #: Seam for the unit tests: the AQL lives in :class:`RootingAuthorStore`, the phases here.
    store_factory: Callable[[StandardDatabase], RootingAuthorStore] = RootingAuthorStore

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        open_store: Callable[[StandardDatabase], RootingAuthorStore] = type(self).store_factory
        store: RootingAuthorStore = open_store(db)
        phases: dict[str, Any] = {}

        unmet: list[str] = store.missing_collections() + _unmet_build()
        if unmet:
            phases["precheck"] = {"ok": False, "unmet": unmet, "candidates": {}}
            return self._report(dry_run, "precondition_unmet", phases, {}, {}, scanned=0, changed=0)

        tenants: list[str] = store.tenant_keys()
        buckets: dict[str, Any] = {bucket: {} for bucket in STEP_BUCKETS}
        samples: dict[str, list[str]] = {"rooting_protocols": []}
        candidates: dict[str, int] = {}
        for tenant_key in tenants:
            found: TenantHits = store.hits(tenant_key)
            if not found.total:
                continue
            candidates[tenant_key] = found.total
            for bucket, count in found.counts.items():
                if count:
                    buckets[bucket][tenant_key] = count
            room = MAX_SAMPLES_PER_BUCKET - len(samples["rooting_protocols"])
            samples["rooting_protocols"].extend(found.sample[: max(room, 0)])
        scanned = sum(candidates.values())
        phases["precheck"] = {"ok": True, "unmet": [], "candidates": candidates}
        phases["dry_run"] = {"would_change": {bucket: sum(buckets[bucket].values()) for bucket in STEP_BUCKETS}}

        if dry_run:
            return self._report(dry_run, "dry_run", phases, buckets, samples, scanned=scanned, changed=0)

        done: list[str] = []
        failed: list[str] = []
        changed = 0
        applied: dict[str, dict[str, int]] = {bucket: {} for bucket in STEP_BUCKETS}
        for tenant_key in tenants:
            if tenant_key not in candidates:
                done.append(tenant_key)
                continue
            try:
                changed_by_bucket: dict[str, int] = store.apply(tenant_key)
            except Exception as exc:  # noqa: BLE001 — one tenant's failure must not stop the others (PRIV-718)
                failed.append(tenant_key)
                logger.warning(
                    "rooting_protocol_author_key.tenant_failed",
                    tenant=log_tenant(tenant_key),
                    error_type=type(exc).__name__,
                )
                continue
            done.append(tenant_key)
            for bucket in STEP_BUCKETS:
                count = changed_by_bucket.get(bucket, 0)
                if count:
                    applied[bucket][tenant_key] = count
                    changed += count
        phases["apply"] = {
            "tenants_done": done,
            "tenants_failed": failed,
            "changed": {bucket: sum(applied[bucket].values()) for bucket in STEP_BUCKETS},
        }
        buckets.update(applied)

        residual = sum(store.hits(tenant_key).total for tenant_key in tenants)
        phases["verify"] = {"residual": {"rooting_protocols.author": residual}}

        if failed:
            status = "partial"
        elif residual:
            status = "verify_failed"
        else:
            status = "applied"
        return self._report(dry_run, status, phases, buckets, samples, scanned=scanned, changed=changed)

    def _report(
        self,
        dry_run: bool,
        status: str,
        phases: dict[str, Any],
        buckets: dict[str, Any],
        samples: dict[str, list[str]],
        *,
        scanned: int,
        changed: int,
    ) -> MigrationReport:
        details: dict[str, Any] = {"status": status, "phases": phases, "buckets": buckets, "samples": samples}
        logged, _dropped = redact_details(details)
        log = logger.warning if status in ("partial", "verify_failed", "precondition_unmet") else logger.info
        log("rooting_protocol_author_key", dry_run=dry_run, **logged)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=dry_run,
            precondition_unmet=status == "precondition_unmet",
            incomplete=status in ("partial", "verify_failed"),
            details=details,
        )


migration = RootingProtocolAuthorKeyMigration()
