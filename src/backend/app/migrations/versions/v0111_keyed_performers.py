"""v0111 — keyed performer fields beside the free-text ones (spec/privacy/09 §5, M-P3, E13).

**Why.** Who watered, filled a tank, serviced it, wrote a nutrient plan or created a workflow template
is stored as typed-in text (``performed_by``, ``author``, ``created_by``). A name is not an account: the
Art. 15 walk and the Art. 17 rules cannot reach it, and deriving a key from it would attribute rows to
whoever happens to carry that name (REQ-025 rule 4, #1662/#1663). ``08`` §3.4 gives each such field a
keyed successor (``*_user_key``, set by the server only) and, where a third party did the work, a label
(``*_label``, ≤ 80). This migration lays the fields down on the existing rows — it never fills a key.

**Steps** (per tenant, **active tenants only** — a data backfill, PRIV-716):

1. ``watering_events``, ``watering_logs``, ``maintenance_logs``, ``tank_fill_events``:
   ``performed_by_user_key = null`` where the attribute is absent, ``performed_by_label =
   performed_by[:80]`` where the label is still null and ``performed_by`` a non-empty string;
2. ``nutrient_plans``: ``author_user_key = null``, ``author_label = author[:80]`` (same rule);
3. ``workflow_templates``: ``created_by_user_key = null``; ``created_by`` stays the label;
4. ``inspections`` whose ``inspector`` starts with ``mcp:``: ``inspected_by_key = <key>`` **only** when
   the field is still null and ``<key>`` is an existing **service** account with a membership in the
   inspection's tenant; then ``inspector = ""``. The ``mcp:`` prefix is the one deterministic spelling
   the MCP server writes (``mcp_server/tools/ipm.py``) — the only exception PRIV-705 admits. A human
   account, an unknown key or one of another tenant leaves the key null (TA-702).

``maintenance_logs`` and ``tank_fill_events`` carry no ``tenant_key`` of their own: the tenant
predicate sits on the anchor, the tank (``tank.tenant_key == @tenant_key``, then ``doc.tank_key ==
tank._key``) — the #706 rule. Every other collection filters ``doc.tenant_key == @tenant_key``; global
catalogue rows (``tenant_key == ""``: system nutrient plans and workflow templates) belong to no tenant
and are left alone. ``rooting_protocols.author`` is **not** part of this migration: the code stamps it
with the creator's account key (``propagation/tenant_router.py``), so it is not a typed name and a label
copy would put an account key where a third party's name belongs (spec/privacy/09 §5, Stand).

The old fields stay (deprecated for one release, ``08`` §3.4); the request schemas do not carry the
new key fields (PRIV-705), the response schemas are unchanged.

**Phases** (``details.phases``, PRIV-718). ``precheck`` — the collections exist, the models of this
build carry the new fields with a ``None`` default and the 80-character label limit, and the
inventory of this build declares each new key field (erasure inventory and tenant export); else
``precondition_unmet`` and nothing is written. ``dry_run`` — the counts, nothing written. ``apply`` —
one stream transaction per tenant for every step; a failing tenant is rolled back, listed in
``tenants_failed``, and the others go on; then ``status = partial`` and the report is ``incomplete``,
so the runner records nothing and the next boot retries. ``verify`` — every step counted again;
anything left is ``verify_failed``.

**Frozen (NFR-016 M-7).** Field names, the label length, the ``mcp:`` prefix, the ``service`` account
type and the ``active`` tenant state are literals here, as the code stood on 2026-11-15.

Idempotent (M-3): a laid-down key is present, a copied label is no longer null, a cleared inspector no
longer starts with ``mcp:`` — a second run changes nothing. Dry run (M-5): counts only. **Reversible**
(``09`` §11): :meth:`down` removes a key field that is ``null`` and a label that is still the copy of
its source, row by row — a key a later path stamped, or a label someone edited, stays. Step 4 is not
reverted: the cleared ``mcp:`` text was a pseudo-key, not a name (``08`` §3.4), and the key it became
was checked against a live service account.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
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

#: Frozen here (M-7): ``PERSON_LABEL_MAX_LENGTH`` of ``app.domain.models.privacy``, the prefix
#: ``mcp_server/tools/ipm.py`` writes, ``AccountType`` ``service`` and ``TenantStatus.ACTIVE`` /
#: ``DELETED`` as they stood on 2026-11-15.
_LABEL_MAX = 80
_MCP_PREFIX = "mcp:"
_SERVICE = "service"
_TENANT_ACTIVE = "active"
_TENANT_DELETED = "deleted"

BUCKET_WATERING_EVENTS = "watering_events.performer_keyed"
BUCKET_WATERING_LOGS = "watering_logs.performer_keyed"
BUCKET_MAINTENANCE_LOGS = "maintenance_logs.performer_keyed"
BUCKET_TANK_FILL_EVENTS = "tank_fill_events.performer_keyed"
BUCKET_NUTRIENT_PLANS = "nutrient_plans.author_keyed"
BUCKET_WORKFLOW_TEMPLATES = "workflow_templates.creator_keyed"
BUCKET_INSPECTOR_CLEARED = "inspections.mcp_inspector_cleared"
#: The subset of :data:`BUCKET_INSPECTOR_CLEARED` whose key was filled from a live service account.
BUCKET_SERVICE_ACCOUNT_KEYED = "inspections.service_account_keyed"


@dataclass(frozen=True)
class CopyStep:
    """One collection of steps 1-3: lay the key field down, copy the free text into the label."""

    bucket: str
    collection: str
    source_field: str
    key_field: str
    #: ``None``: the source field itself stays the label (``workflow_templates.created_by``).
    label_field: str | None
    #: The rows carry no ``tenant_key``; the tenant predicate sits on their tank.
    via_tank: bool = False


#: Frozen (M-7): the collections and fields of ``08`` §3.4, as the models stood on 2026-11-15.
COPY_STEPS: tuple[CopyStep, ...] = (
    CopyStep(BUCKET_WATERING_EVENTS, "watering_events", "performed_by", "performed_by_user_key", "performed_by_label"),
    CopyStep(BUCKET_WATERING_LOGS, "watering_logs", "performed_by", "performed_by_user_key", "performed_by_label"),
    CopyStep(
        BUCKET_MAINTENANCE_LOGS,
        "maintenance_logs",
        "performed_by",
        "performed_by_user_key",
        "performed_by_label",
        via_tank=True,
    ),
    CopyStep(
        BUCKET_TANK_FILL_EVENTS,
        "tank_fill_events",
        "performed_by",
        "performed_by_user_key",
        "performed_by_label",
        via_tank=True,
    ),
    CopyStep(BUCKET_NUTRIENT_PLANS, "nutrient_plans", "author", "author_user_key", "author_label"),
    CopyStep(BUCKET_WORKFLOW_TEMPLATES, "workflow_templates", "created_by", "created_by_user_key", None),
)

#: The buckets ``up`` corrects, in order; ``verify`` counts exactly these again.
STEP_BUCKETS: tuple[str, ...] = (*(step.bucket for step in COPY_STEPS), BUCKET_INSPECTOR_CLEARED)

BUCKET_REMOVED_SUFFIX = ".removed"
#: The buckets ``down`` fills: one per copy step.
REMOVAL_BUCKETS: tuple[str, ...] = tuple(step.bucket + BUCKET_REMOVED_SUFFIX for step in COPY_STEPS)

#: A tenant's transaction carries seven bulk updates; the 10 s default of the helper is sized for a plan batch.
_TENANT_TIME_BUDGET_SECONDS = 600.0

# ── AQL ─────────────────────────────────────────────────────────────

_ACTIVE_TENANT_KEYS = """
FOR t IN @@tenants
  FILTER t.status == @active OR t.status == null
  SORT t._key
  RETURN t._key
"""

_LIVE_TENANT_KEYS = """
FOR t IN @@tenants
  FILTER t.status != @deleted
  SORT t._key
  RETURN t._key
"""

#: The tenant predicate on the row itself.
_BY_TENANT = """
FOR doc IN @@collection
  FILTER doc.tenant_key == @tenant_key
"""

#: The tenant predicate on the anchor: the row carries no ``tenant_key``, its tank does (#706).
_BY_TANK = """
FOR tank IN @@tanks
  FILTER tank.tenant_key == @tenant_key
  FOR doc IN @@collection
    FILTER doc.tank_key == tank._key
"""

_KEY_AND_LABEL_RULE = """
  LET source = doc[@source_field]
  LET needs_key = NOT HAS(doc, @key_field)
  LET needs_label = doc[@label_field] == null AND IS_STRING(source) AND source != ""
  FILTER needs_key OR needs_label
"""

_KEY_ONLY_RULE = """
  FILTER NOT HAS(doc, @key_field)
"""

_KEY_AND_LABEL_UPDATE = """
  UPDATE doc WITH MERGE(
    needs_key ? { [@key_field]: null } : {},
    needs_label ? { [@label_field]: SUBSTRING(source, 0, @label_max) } : {}
  ) IN @@collection
  RETURN 1
"""

_KEY_ONLY_UPDATE = """
  UPDATE doc WITH { [@key_field]: null } IN @@collection
  RETURN 1
"""

#: What ``down`` takes away: a key that is ``null``, a label that is still the copy of its source.
_KEY_AND_LABEL_REMOVAL_RULE = """
  LET drop = APPEND(
    HAS(doc, @key_field) AND doc[@key_field] == null ? [@key_field] : [],
    IS_STRING(doc[@label_field]) AND IS_STRING(doc[@source_field])
      AND doc[@label_field] == SUBSTRING(doc[@source_field], 0, @label_max) ? [@label_field] : []
  )
  FILTER LENGTH(drop) > 0
"""

_KEY_ONLY_REMOVAL_RULE = """
  LET drop = HAS(doc, @key_field) AND doc[@key_field] == null ? [@key_field] : []
  FILTER LENGTH(drop) > 0
"""

#: ``keepNull: false`` turns ``{field: null}`` into the removal of the attribute.
_REMOVE_TAIL = """
  UPDATE doc WITH ZIP(drop, (FOR name IN drop RETURN null)) IN @@collection OPTIONS { keepNull: false }
  RETURN 1
"""

_HITS_HEAD = "LET hits = ("
_HITS_TAIL = """
  RETURN doc._key
)
RETURN { n: LENGTH(hits), sample: SLICE(hits, 0, @limit) }
"""

#: Step 4. The key is filled only when the field is null and the account behind the prefix is a service
#: account that is a member of the inspection's tenant; any other text leaves it null (PRIV-705).
_INSPECTION_MATCH = """
FOR doc IN @@collection
  FILTER doc.tenant_key == @tenant_key
  FILTER IS_STRING(doc.inspector) AND STARTS_WITH(doc.inspector, @mcp_prefix)
  LET account_key = SUBSTRING(doc.inspector, LENGTH(@mcp_prefix))
  LET service_key = doc.inspected_by_key != null ? null : FIRST(
    FOR u IN @@users
      FILTER u._key == account_key AND u.account_type == @service
      FOR m IN @@memberships
        FILTER m.user_key == u._key AND m.tenant_key == @tenant_key AND m.is_active != false
        LIMIT 1
        RETURN u._key
  )
"""

_INSPECTION_HITS = (
    "LET hits = ("
    + _INSPECTION_MATCH
    + """
  RETURN { key: doc._key, keyed: service_key != null }
)
RETURN { n: LENGTH(hits), keyed: LENGTH(hits[* FILTER CURRENT.keyed]), sample: SLICE(hits[*].key, 0, @limit) }
"""
)

_INSPECTION_UPDATE = (
    _INSPECTION_MATCH
    + """
  UPDATE doc WITH MERGE({ inspector: "" }, service_key != null ? { inspected_by_key: service_key } : {})
    IN @@collection
  RETURN service_key != null
"""
)


@dataclass(frozen=True)
class StepQueries:
    """The AQL of one copy step: count, write, and the two halves of ``down``."""

    hits: str
    update: str
    removable: str
    remove: str


def _queries_of(step: CopyStep) -> StepQueries:
    anchor = _BY_TANK if step.via_tank else _BY_TENANT
    if step.label_field is None:
        rule, update, removal = _KEY_ONLY_RULE, _KEY_ONLY_UPDATE, _KEY_ONLY_REMOVAL_RULE
    else:
        rule, update, removal = _KEY_AND_LABEL_RULE, _KEY_AND_LABEL_UPDATE, _KEY_AND_LABEL_REMOVAL_RULE
    return StepQueries(
        hits=_HITS_HEAD + anchor + rule + _HITS_TAIL,
        update=anchor + rule + update,
        removable=_HITS_HEAD + anchor + removal + _HITS_TAIL,
        remove=anchor + removal + _REMOVE_TAIL,
    )


#: bucket -> the step and its AQL; built once at import from the constants above.
_STEP_BY_BUCKET: dict[str, CopyStep] = {step.bucket: step for step in COPY_STEPS}
_COPY_QUERIES: dict[str, StepQueries] = {step.bucket: _queries_of(step) for step in COPY_STEPS}

#: Every collection a tenant's transaction writes, and the ones it only reads.
_WRITTEN_COLLECTIONS: tuple[str, ...] = (*(step.collection for step in COPY_STEPS), col.INSPECTIONS)
_READ_COLLECTIONS: tuple[str, ...] = (col.TANKS, col.USERS, col.MEMBERSHIPS)
_REQUIRED_COLLECTIONS: tuple[str, ...] = (col.TENANTS, *_WRITTEN_COLLECTIONS, *_READ_COLLECTIONS)


def _used_binds(query: str, binds: dict[str, Any]) -> dict[str, Any]:
    """ArangoDB refuses a bind parameter the query does not use; keep only the ones it names."""
    return {name: value for name, value in binds.items() if f"@{name}" in query}


def _step_binds(step: CopyStep, tenant_key: str) -> dict[str, Any]:
    return {
        "@collection": step.collection,
        "@tanks": col.TANKS,
        "tenant_key": tenant_key,
        "source_field": step.source_field,
        "key_field": step.key_field,
        "label_field": step.label_field,
        "label_max": _LABEL_MAX,
        "limit": MAX_SAMPLES_PER_BUCKET,
    }


def _inspection_binds(tenant_key: str) -> dict[str, Any]:
    return {
        "@collection": col.INSPECTIONS,
        "@users": col.USERS,
        "@memberships": col.MEMBERSHIPS,
        "tenant_key": tenant_key,
        "mcp_prefix": _MCP_PREFIX,
        "service": _SERVICE,
        "limit": MAX_SAMPLES_PER_BUCKET,
    }


@dataclass(frozen=True)
class Hits:
    """What one step would change in one tenant: the row count, sample row keys, and (step 4) how many get a key."""

    count: int
    sample: list[str]
    keyed: int = 0


def _hits_of(row: dict[str, Any] | None) -> Hits:
    found: dict[str, Any] = row or {}
    return Hits(int(found.get("n", 0)), [str(key) for key in found.get("sample", [])], int(found.get("keyed", 0)))


class KeyedPerformerStore:
    """The AQL of v0111: tenant lists, per-tenant counts, the per-tenant transaction and ``down``."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def missing_collections(self) -> list[str]:
        return [name for name in _REQUIRED_COLLECTIONS if not self._db.has_collection(name)]

    def tenant_keys(self, *, active_only: bool) -> list[str]:
        """The tenants ``up`` walks (active only, PRIV-716) or ``down`` walks (every one not deleted)."""
        if active_only:
            cursor = self._db.aql.execute(
                _ACTIVE_TENANT_KEYS, bind_vars={"@tenants": col.TENANTS, "active": _TENANT_ACTIVE}
            )
        else:
            cursor = self._db.aql.execute(
                _LIVE_TENANT_KEYS, bind_vars={"@tenants": col.TENANTS, "deleted": _TENANT_DELETED}
            )
        return [str(key) for key in cast(Cursor, cursor)]

    def hits(self, bucket: str, tenant_key: str) -> Hits:
        """The tenant's rows step *bucket* would change."""
        if bucket == BUCKET_INSPECTOR_CLEARED:
            binds = _used_binds(_INSPECTION_HITS, _inspection_binds(tenant_key))
            cursor = self._db.aql.execute(_INSPECTION_HITS, bind_vars=binds)
            return _hits_of(next(iter(cast(Cursor, cursor)), None))
        step: CopyStep = _STEP_BY_BUCKET[bucket]
        queries: StepQueries = _COPY_QUERIES[bucket]
        binds = _used_binds(queries.hits, _step_binds(step, tenant_key))
        cursor = self._db.aql.execute(queries.hits, bind_vars=binds)
        return _hits_of(next(iter(cast(Cursor, cursor)), None))

    def apply(self, tenant_key: str) -> dict[str, int]:
        """Every step for one tenant in one stream transaction; any failure rolls all of them back."""
        changed: dict[str, int] = {}
        with stream_transaction(
            self._db,
            write=_WRITTEN_COLLECTIONS,
            read=_READ_COLLECTIONS,
            entity="keyed_performers",
            time_budget_seconds=_TENANT_TIME_BUDGET_SECONDS,
        ) as txn:
            for step in COPY_STEPS:
                queries: StepQueries = _COPY_QUERIES[step.bucket]
                binds = _used_binds(queries.update, _step_binds(step, tenant_key))
                changed[step.bucket] = sum(1 for _ in txn.aql.execute(queries.update, bind_vars=binds))
            inspection_binds = _used_binds(_INSPECTION_UPDATE, _inspection_binds(tenant_key))
            keyed_flags: list[bool] = [
                bool(flag) for flag in txn.aql.execute(_INSPECTION_UPDATE, bind_vars=inspection_binds)
            ]
            changed[BUCKET_INSPECTOR_CLEARED] = len(keyed_flags)
            changed[BUCKET_SERVICE_ACCOUNT_KEYED] = sum(1 for flag in keyed_flags if flag)
        return changed

    def removable(self, tenant_key: str) -> dict[str, Hits]:
        """Per copy step, the tenant's rows :meth:`remove` would touch."""
        out: dict[str, Hits] = {}
        for step in COPY_STEPS:
            queries: StepQueries = _COPY_QUERIES[step.bucket]
            binds = _used_binds(queries.removable, _step_binds(step, tenant_key))
            cursor = self._db.aql.execute(queries.removable, bind_vars=binds)
            out[step.bucket] = _hits_of(next(iter(cast(Cursor, cursor)), None))
        return out

    def remove(self, tenant_key: str) -> dict[str, int]:
        """``down`` for one tenant in one stream transaction."""
        removed: dict[str, int] = {}
        with stream_transaction(
            self._db,
            write=_WRITTEN_COLLECTIONS,
            read=_READ_COLLECTIONS,
            entity="keyed_performers",
            time_budget_seconds=_TENANT_TIME_BUDGET_SECONDS,
        ) as txn:
            for step in COPY_STEPS:
                queries: StepQueries = _COPY_QUERIES[step.bucket]
                binds = _used_binds(queries.remove, _step_binds(step, tenant_key))
                removed[step.bucket] = sum(1 for _ in txn.aql.execute(queries.remove, bind_vars=binds))
        return removed


def _unmet_build() -> list[str]:
    """The models and the inventory of this build carry what v0111 writes (PRIV-718 precheck)."""
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo

    from app.domain.engines.erasure_engine import ErasureEngine
    from app.domain.engines.tenant_export_engine import TenantExportEngine
    from app.domain.models.nutrient_plan import NutrientPlan
    from app.domain.models.tank import MaintenanceLog, TankFillEvent
    from app.domain.models.task import WorkflowTemplate
    from app.domain.models.watering_event import WateringEvent
    from app.domain.models.watering_log import WateringLog

    models: dict[str, type[BaseModel]] = {
        "watering_events": WateringEvent,
        "watering_logs": WateringLog,
        "maintenance_logs": MaintenanceLog,
        "tank_fill_events": TankFillEvent,
        "nutrient_plans": NutrientPlan,
        "workflow_templates": WorkflowTemplate,
    }
    declared: set[tuple[str, str]] = set(ErasureEngine.account_reference_fields())
    declared |= {(entry.collection, entry.user_field) for entry in ErasureEngine.EXCLUDED_USER_REFERENCES}
    unmet: list[str] = []
    for step in COPY_STEPS:
        fields: dict[str, FieldInfo] = models[step.collection].model_fields
        key_info = fields.get(step.key_field)
        if key_info is None or key_info.default is not None:
            unmet.append(f"model.{step.collection}.{step.key_field}")
        if step.label_field is not None:
            label_info = fields.get(step.label_field)
            limits = [getattr(meta, "max_length", None) for meta in (label_info.metadata if label_info else [])]
            if label_info is None or label_info.default is not None or _LABEL_MAX not in limits:
                unmet.append(f"model.{step.collection}.{step.label_field}")
        if (step.collection, step.key_field) not in declared:
            unmet.append(f"inventory.erasure.{step.collection}.{step.key_field}")
        if step.key_field not in TenantExportEngine.references_of(step.collection):
            unmet.append(f"inventory.tenant_export.{step.collection}.{step.key_field}")
    return unmet


class KeyedPerformersMigration(Migration):
    version = "0111"
    name = "keyed_performers"
    description = (
        "Lay down the keyed performer/author/creator fields (null) beside the free-text ones and copy the "
        "text into the label; MCP inspections get the service account key only when it exists "
        "(spec/privacy/09 section 5, M-P3)."
    )
    reversible = True
    kind = "data_backfill"

    #: Seam for the unit tests: the AQL lives in :class:`KeyedPerformerStore`, the phases here.
    store_factory: Callable[[StandardDatabase], KeyedPerformerStore] = KeyedPerformerStore

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        open_store: Callable[[StandardDatabase], KeyedPerformerStore] = type(self).store_factory
        store: KeyedPerformerStore = open_store(db)
        phases: dict[str, Any] = {}

        unmet: list[str] = store.missing_collections() + _unmet_build()
        if unmet:
            phases["precheck"] = {"ok": False, "unmet": unmet, "candidates": {}}
            return self._report(dry_run, "precondition_unmet", phases, {}, {}, scanned=0, changed=0)

        tenants: list[str] = store.tenant_keys(active_only=True)
        buckets: dict[str, Any] = {bucket: {} for bucket in (*STEP_BUCKETS, BUCKET_SERVICE_ACCOUNT_KEYED)}
        samples: dict[str, list[str]] = {bucket: [] for bucket in STEP_BUCKETS}
        candidates: dict[str, int] = {}
        for tenant_key in tenants:
            for bucket in STEP_BUCKETS:
                found: Hits = store.hits(bucket, tenant_key)
                if not found.count:
                    continue
                buckets[bucket][tenant_key] = found.count
                candidates[tenant_key] = candidates.get(tenant_key, 0) + found.count
                room = MAX_SAMPLES_PER_BUCKET - len(samples[bucket])
                samples[bucket].extend(found.sample[: max(room, 0)])
                if found.keyed:
                    buckets[BUCKET_SERVICE_ACCOUNT_KEYED][tenant_key] = found.keyed
        scanned = sum(candidates.values())
        phases["precheck"] = {"ok": True, "unmet": [], "candidates": candidates}
        phases["dry_run"] = {
            "would_change": {
                bucket: sum(buckets[bucket].values()) for bucket in (*STEP_BUCKETS, BUCKET_SERVICE_ACCOUNT_KEYED)
            }
        }

        if dry_run:
            return self._report(dry_run, "dry_run", phases, buckets, samples, scanned=scanned, changed=0)

        done: list[str] = []
        failed: list[str] = []
        changed = 0
        applied: dict[str, dict[str, int]] = {bucket: {} for bucket in (*STEP_BUCKETS, BUCKET_SERVICE_ACCOUNT_KEYED)}
        for tenant_key in tenants:
            if tenant_key not in candidates:
                done.append(tenant_key)
                continue
            try:
                changed_by_bucket: dict[str, int] = store.apply(tenant_key)
            except Exception as exc:  # noqa: BLE001 — one tenant's failure must not stop the others (PRIV-718)
                failed.append(tenant_key)
                logger.warning(
                    "keyed_performers.tenant_failed",
                    tenant=log_tenant(tenant_key),
                    error_type=type(exc).__name__,
                )
                continue
            done.append(tenant_key)
            for bucket, count in changed_by_bucket.items():
                if count:
                    applied[bucket][tenant_key] = count
            changed += sum(changed_by_bucket.get(bucket, 0) for bucket in STEP_BUCKETS)
        phases["apply"] = {
            "tenants_done": done,
            "tenants_failed": failed,
            "changed": {bucket: sum(rows.values()) for bucket, rows in applied.items()},
        }
        buckets.update(applied)

        residual: dict[str, int] = {bucket: 0 for bucket in STEP_BUCKETS}
        for tenant_key in tenants:
            for bucket in STEP_BUCKETS:
                left: Hits = store.hits(bucket, tenant_key)
                residual[bucket] += left.count
        phases["verify"] = {"residual": residual}

        if failed:
            status = "partial"
        elif any(residual.values()):
            status = "verify_failed"
        else:
            status = "applied"
        return self._report(dry_run, status, phases, buckets, samples, scanned=scanned, changed=changed)

    def down(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        """Remove ``null`` key fields and labels that are still copies; step 4 stays (module docstring)."""
        open_store: Callable[[StandardDatabase], KeyedPerformerStore] = type(self).store_factory
        store: KeyedPerformerStore = open_store(db)
        tenants: list[str] = store.tenant_keys(active_only=False)
        buckets: dict[str, Any] = {bucket: {} for bucket in REMOVAL_BUCKETS}
        samples: dict[str, list[str]] = {bucket: [] for bucket in REMOVAL_BUCKETS}
        done: list[str] = []
        failed: list[str] = []
        scanned = 0
        changed = 0
        for tenant_key in tenants:
            found: dict[str, Hits] = store.removable(tenant_key)
            for bucket, hits in found.items():
                if not hits.count:
                    continue
                removal_bucket = bucket + BUCKET_REMOVED_SUFFIX
                buckets[removal_bucket][tenant_key] = hits.count
                scanned += hits.count
                room = MAX_SAMPLES_PER_BUCKET - len(samples[removal_bucket])
                samples[removal_bucket].extend(hits.sample[: max(room, 0)])
            if dry_run or not any(hits.count for hits in found.values()):
                done.append(tenant_key)
                continue
            try:
                removed: dict[str, int] = store.remove(tenant_key)
            except Exception as exc:  # noqa: BLE001 — one tenant's failure must not stop the others (PRIV-718)
                failed.append(tenant_key)
                logger.warning(
                    "keyed_performers.down_tenant_failed",
                    tenant=log_tenant(tenant_key),
                    error_type=type(exc).__name__,
                )
                continue
            done.append(tenant_key)
            changed += sum(removed.values())
        phases: dict[str, Any] = {}
        if not dry_run:
            phases["apply"] = {"tenants_done": done, "tenants_failed": failed, "changed": {"rows": changed}}
        if dry_run:
            status = "dry_run"
        elif failed:
            status = "partial"
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
        log("keyed_performers", dry_run=dry_run, **logged)
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


migration = KeyedPerformersMigration()
