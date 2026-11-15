"""v0110 — classify the tenants that existed before the classification (spec/privacy/09 §4, M-P2, E09).

**Why.** ``Tenant.settings.record_keeping`` decides which retention class a tenant's statutory fields
fall into (PRIV-401), ``organization_kind`` what kind of organisation it is (PRIV-409). Neither has a
model default (DEC-30, W-03): a *new* tenant must declare them and stays ``undeclared`` until it does.
The tenants that already exist never had the choice; this migration gives them the value that keeps
today's behaviour and says so.

**Steps** (per tenant, every tenant status except ``deleted`` — a privacy correction, PRIV-716):

1. ``settings.record_keeping`` unset → ``legacy`` for an organisation tenant (bucket
   ``tenants.record_keeping_legacy``), ``none`` for a personal tenant (``tenants.record_keeping_none``;
   L-07: private home growing carries no documentation duty, ``06`` PRIV-409);
2. ``settings.organization_kind`` unset on an **organisation** tenant → ``unknown_legacy``
   (``tenants.organization_kind_unknown_legacy``). A personal tenant gets no ``organization_kind``:
   PRIV-409 classifies organisation tenants only (``organization_kind ∈ {association, commercial,
   community, other}``), and ``unknown_legacy`` would claim an organisation nobody knows of.

A value that is present is never overwritten — each field on its own (an organisation tenant with a
declared ``record_keeping`` but no kind gets the kind only). A ``settings`` that is neither absent nor
an object is outside this migration (the model cannot read such a tenant either); it is skipped.
A tenant without ``tenant_type`` is personal, as the model reads it (``TenantType.PERSONAL`` default).

**Phases** (``details.phases``, PRIV-718). ``precheck`` — ``tenants`` exists and the model of this
build reads the values the migration writes and still has no default for them (a stamp the model
cannot parse would fail every read of that tenant); else ``precondition_unmet`` and nothing is
written. ``dry_run`` — the counts, nothing written. ``apply`` — one write per tenant; a tenant's
stamp is one single-document ``UPDATE`` (atomic in ArangoDB, the per-tenant transaction of PRIV-718);
a failing tenant is listed in ``tenants_failed``, the others go on, then ``status = partial`` and the
report is ``incomplete``, so the runner records nothing and the next boot retries. ``verify`` — the
candidates counted again; anything left is ``verify_failed``.

**Frozen (NFR-016 M-7).** The values written, the personal type, the ``deleted`` state and the model's
personal default are literals here, as the model stood when this version was written.

**Tenant binding.** The collection is ``tenants`` itself; the write filters ``t._key == @tenant_key``.

Idempotent (M-3): a stamped field is no longer unset, a second run changes nothing. Dry run (M-5):
counts only. **Reversible** (``09`` §11): :meth:`down` removes ``record_keeping == legacy`` and
``organization_kind == unknown_legacy`` — values only this migration writes (``legacy`` and
``unknown_legacy`` are never a choice at creation, PRIV-409). It leaves ``record_keeping == none`` on
personal tenants: that value is not unambiguously this migration's (the creation path of PRIV-409 sets
the same value on a new personal tenant, and nothing records who wrote it), and it is the correct value
of every personal tenant either way (L-07); removing it would make a correctly classified tenant
``undeclared``.
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
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.framework.report_store import MAX_SAMPLES_PER_BUCKET, redact_details

logger = structlog.get_logger(__name__)

#: Frozen here (M-7): the values of ``RecordKeeping`` / ``OrganizationKind`` / ``TenantType`` /
#: ``TenantStatus`` this migration reads and writes, as ``app.common.enums`` defined them on 2026-11-15.
_LEGACY = "legacy"
_NONE = "none"
_UNKNOWN_LEGACY = "unknown_legacy"
_PERSONAL = "personal"
_TENANT_DELETED = "deleted"

BUCKET_LEGACY = "tenants.record_keeping_legacy"
BUCKET_NONE = "tenants.record_keeping_none"
BUCKET_UNKNOWN_KIND = "tenants.organization_kind_unknown_legacy"
#: The buckets ``up`` fills, in order; ``verify`` counts exactly these again.
STAMP_BUCKETS = (BUCKET_LEGACY, BUCKET_NONE, BUCKET_UNKNOWN_KIND)

BUCKET_LEGACY_REMOVED = "tenants.record_keeping_legacy_removed"
BUCKET_UNKNOWN_KIND_REMOVED = "tenants.organization_kind_unknown_legacy_removed"
#: The buckets ``down`` fills.
REMOVAL_BUCKETS = (BUCKET_LEGACY_REMOVED, BUCKET_UNKNOWN_KIND_REMOVED)

#: The stamp a tenant is missing, decided in AQL so that the count and the write read the same rule.
#: ``rk`` / ``ok`` are the values to set, ``null`` where the field is present (or, for the kind, where
#: the tenant is personal). A model-default tenant without ``tenant_type`` is personal.
_STAMP_RULE = """
  FILTER t.status != @deleted
  FILTER t.settings == null OR IS_OBJECT(t.settings)
  LET s = IS_OBJECT(t.settings) ? t.settings : {}
  LET personal = t.tenant_type == null OR t.tenant_type == @personal
  LET rk = s.record_keeping == null ? (personal ? @none : @legacy) : null
  LET ok = (s.organization_kind == null AND NOT personal) ? @unknown_legacy : null
  FILTER rk != null OR ok != null
"""

_PENDING = (
    "FOR t IN @@tenants"
    + _STAMP_RULE
    + """
  SORT t._key
  RETURN { key: t._key, record_keeping: rk, organization_kind: ok }
"""
)

_STAMP = (
    "FOR t IN @@tenants\n  FILTER t._key == @tenant_key"
    + _STAMP_RULE
    + """
  UPDATE t WITH {
    settings: MERGE(s, rk != null ? { record_keeping: rk } : {}, ok != null ? { organization_kind: ok } : {})
  } IN @@tenants OPTIONS { mergeObjects: false }
  RETURN { record_keeping: rk, organization_kind: ok }
"""
)

_REMOVAL_RULE = """
  FILTER t.status != @deleted
  FILTER IS_OBJECT(t.settings)
  LET drop = APPEND(
    t.settings.record_keeping == @legacy ? ["record_keeping"] : [],
    t.settings.organization_kind == @unknown_legacy ? ["organization_kind"] : []
  )
  FILTER LENGTH(drop) > 0
"""

_REMOVABLE = "FOR t IN @@tenants" + _REMOVAL_RULE + "  SORT t._key\n  RETURN { key: t._key, drop: drop }\n"

_REMOVE = (
    "FOR t IN @@tenants"
    + _REMOVAL_RULE
    + """  UPDATE t WITH { settings: UNSET(t.settings, drop) } IN @@tenants OPTIONS { mergeObjects: false }
  RETURN { key: t._key, drop: drop }
"""
)


@dataclass(frozen=True)
class Stamp:
    """What one tenant is missing: the value to set per field, ``None`` where nothing is set."""

    tenant_key: str
    record_keeping: str | None
    organization_kind: str | None

    def buckets(self) -> list[str]:
        out: list[str] = []
        if self.record_keeping == _LEGACY:
            out.append(BUCKET_LEGACY)
        elif self.record_keeping == _NONE:
            out.append(BUCKET_NONE)
        if self.organization_kind == _UNKNOWN_LEGACY:
            out.append(BUCKET_UNKNOWN_KIND)
        return out


def _removed_buckets(drop: list[str]) -> list[str]:
    out: list[str] = []
    if "record_keeping" in drop:
        out.append(BUCKET_LEGACY_REMOVED)
    if "organization_kind" in drop:
        out.append(BUCKET_UNKNOWN_KIND_REMOVED)
    return out


def _binds(query: str, **extra: Any) -> dict[str, Any]:
    """The frozen values plus *extra*, reduced to the ones *query* names (ArangoDB refuses an unused bind)."""
    binds: dict[str, Any] = {
        "@tenants": col.TENANTS,
        "deleted": _TENANT_DELETED,
        "personal": _PERSONAL,
        "none": _NONE,
        "legacy": _LEGACY,
        "unknown_legacy": _UNKNOWN_LEGACY,
        **extra,
    }
    return {name: value for name, value in binds.items() if f"@{name}" in query}


def _stamp_of(tenant_key: str, row: dict[str, Any]) -> Stamp:
    return Stamp(tenant_key, row.get("record_keeping"), row.get("organization_kind"))


class RecordKeepingStore:
    """The AQL of v0110: the tenants missing a stamp, the per-tenant stamp, and the removal of ``down``."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def missing_collections(self) -> list[str]:
        return [] if self._db.has_collection(col.TENANTS) else [col.TENANTS]

    def pending(self) -> list[Stamp]:
        cursor = self._db.aql.execute(_PENDING, bind_vars=_binds(_PENDING))
        return [_stamp_of(str(row["key"]), row) for row in cast(Cursor, cursor)]

    def stamp(self, tenant_key: str) -> Stamp | None:
        """Stamp one tenant in one single-document ``UPDATE``; ``None`` when it was missing nothing by now."""
        cursor = self._db.aql.execute(_STAMP, bind_vars=_binds(_STAMP, tenant_key=tenant_key))
        row = next(iter(cast(Cursor, cursor)), None)
        if row is None:
            return None
        return _stamp_of(tenant_key, row)

    def removable(self) -> list[tuple[str, list[str]]]:
        cursor = self._db.aql.execute(_REMOVABLE, bind_vars=_binds(_REMOVABLE))
        return [(str(row["key"]), list(row["drop"])) for row in cast(Cursor, cursor)]

    def remove(self) -> list[tuple[str, list[str]]]:
        cursor = self._db.aql.execute(_REMOVE, bind_vars=_binds(_REMOVE))
        return [(str(row["key"]), list(row["drop"])) for row in cast(Cursor, cursor)]


def _unmet_model() -> list[str]:
    """The model of this build reads every value v0110 writes, and has no default for either field (DEC-30)."""
    from pydantic import ValidationError

    from app.domain.models.tenant import TenantSettings

    unmet: list[str] = []
    undeclared = TenantSettings()
    for field_name in ("record_keeping", "organization_kind"):
        if field_name not in TenantSettings.model_fields:
            unmet.append(f"model.tenant_settings.{field_name}")
        elif getattr(undeclared, field_name) is not None:
            unmet.append(f"model.tenant_settings.{field_name}.no_default")
    if unmet:
        return unmet
    for field_name, value in (
        ("record_keeping", _LEGACY),
        ("record_keeping", _NONE),
        ("organization_kind", _UNKNOWN_LEGACY),
    ):
        try:
            parsed = getattr(TenantSettings(**{field_name: value}), field_name)
        except ValidationError:
            parsed = None
        if parsed != value:
            unmet.append(f"model.tenant_settings.{field_name}.{value}")
    return unmet


class TenantRecordKeepingDefaultMigration(Migration):
    version = "0110"
    name = "tenant_record_keeping_default"
    description = (
        "Stamp every existing tenant without a classification: record_keeping legacy (personal tenants none), "
        "organization_kind unknown_legacy on organisation tenants; never overwrite a value "
        "(spec/privacy/09 section 4, M-P2)."
    )
    reversible = True
    kind = "privacy_correction"

    #: Seam for the unit tests: the AQL lives in :class:`RecordKeepingStore`, the phases here.
    store_factory: Callable[[StandardDatabase], RecordKeepingStore] = RecordKeepingStore

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        open_store: Callable[[StandardDatabase], RecordKeepingStore] = type(self).store_factory
        store: RecordKeepingStore = open_store(db)
        phases: dict[str, Any] = {}

        unmet: list[str] = store.missing_collections() + _unmet_model()
        if unmet:
            phases["precheck"] = {"ok": False, "unmet": unmet, "candidates": {}}
            return self._report(dry_run, "precondition_unmet", phases, {}, {}, scanned=0, changed=0)

        pending: list[Stamp] = store.pending()
        candidates: dict[str, int] = {}
        buckets: dict[str, Any] = {bucket: {} for bucket in STAMP_BUCKETS}
        samples: dict[str, list[str]] = {bucket: [] for bucket in STAMP_BUCKETS}
        for stamp in pending:
            stamp_buckets: list[str] = stamp.buckets()
            candidates[stamp.tenant_key] = len(stamp_buckets)
            for bucket in stamp_buckets:
                buckets[bucket][stamp.tenant_key] = 1
                if len(samples[bucket]) < MAX_SAMPLES_PER_BUCKET:
                    samples[bucket].append(stamp.tenant_key)
        phases["precheck"] = {
            "ok": True,
            "unmet": [],
            "candidates": candidates,
        }
        phases["dry_run"] = {"would_change": {bucket: len(buckets[bucket]) for bucket in STAMP_BUCKETS}}

        if dry_run:
            return self._report(dry_run, "dry_run", phases, buckets, samples, scanned=len(pending), changed=0)

        done: list[str] = []
        failed: list[str] = []
        applied: dict[str, dict[str, int]] = {bucket: {} for bucket in STAMP_BUCKETS}
        changed_tenants: set[str] = set()
        for candidate in pending:
            try:
                written: Stamp | None = store.stamp(candidate.tenant_key)
            except Exception as exc:  # noqa: BLE001 — one tenant's failure must not stop the others (PRIV-718)
                failed.append(candidate.tenant_key)
                logger.warning(
                    "tenant_record_keeping_default.tenant_failed",
                    tenant=log_tenant(candidate.tenant_key),
                    error_type=type(exc).__name__,
                )
                continue
            done.append(candidate.tenant_key)
            if written is None:
                continue
            written_buckets: list[str] = written.buckets()
            for bucket in written_buckets:
                applied[bucket][candidate.tenant_key] = 1
                changed_tenants.add(candidate.tenant_key)
        changed = len(changed_tenants)
        phases["apply"] = {
            "tenants_done": done,
            "tenants_failed": failed,
            "changed": {bucket: len(applied[bucket]) for bucket in STAMP_BUCKETS},
        }
        buckets.update(applied)

        residual: dict[str, int] = {bucket: 0 for bucket in STAMP_BUCKETS}
        left: list[Stamp] = store.pending()
        for remaining in left:
            remaining_buckets: list[str] = remaining.buckets()
            for bucket in remaining_buckets:
                residual[bucket] += 1
        phases["verify"] = {"residual": residual}

        if failed:
            status = "partial"
        elif any(residual[bucket] for bucket in STAMP_BUCKETS):
            status = "verify_failed"
        else:
            status = "applied"
        return self._report(dry_run, status, phases, buckets, samples, scanned=len(pending), changed=changed)

    def down(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        """Remove ``legacy`` / ``unknown_legacy`` again; ``none`` on personal tenants stays (module docstring)."""
        open_store: Callable[[StandardDatabase], RecordKeepingStore] = type(self).store_factory
        store: RecordKeepingStore = open_store(db)
        rows: list[tuple[str, list[str]]] = store.removable() if dry_run else store.remove()
        buckets: dict[str, Any] = {bucket: {} for bucket in REMOVAL_BUCKETS}
        samples: dict[str, list[str]] = {bucket: [] for bucket in REMOVAL_BUCKETS}
        for tenant_key, drop in rows:
            for bucket in _removed_buckets(drop):
                buckets[bucket][tenant_key] = 1
                if len(samples[bucket]) < MAX_SAMPLES_PER_BUCKET:
                    samples[bucket].append(tenant_key)
        status = "dry_run" if dry_run else "applied"
        return self._report(
            dry_run, status, {}, buckets, samples, scanned=len(rows), changed=0 if dry_run else len(rows)
        )

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
        log("tenant_record_keeping_default", dry_run=dry_run, **logged)
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


migration = TenantRecordKeepingDefaultMigration()
