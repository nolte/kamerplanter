"""v0109 — correct copied tombstones; the plan-audit actor becomes the marker (spec/privacy/09 §3, M-P1, E04).

**Why.** An erased account leaves its tombstone (``anon_<16hex>``) only where the inventory keeps a
linkable pseudonym (the allowlist, PRIV-204). Copies landed elsewhere: v0104 and the consistency job
copied it into ``care_events`` (v0107 corrected ``performed_by_user_key`` of the first generation only),
and ``garden_plan_audit.user_key`` was itself pseudonymised until DEC-16 moved it to the marker. A
phone's file name in ``attachments.original_filename`` survived the uploader's erasure (PRIV-211).

**Steps** (each per tenant, every tenant status except ``deleted`` — a privacy correction, PRIV-716):

1. ``care_events.performed_by_user_key`` and ``care_events.created_by`` holding a tombstone of either
   generation → ``_anonymized`` (bucket ``care_events.tombstone_to_marker``);
2. ``garden_plan_audit.user_key`` holding a tombstone → ``_anonymized`` (``garden_plan_audit.tombstone_to_marker``);
3. every other account-reference cell outside the allowlist holding a tombstone: **counted only**
   (``undeclared_tombstones``) — a finding for the operator, never corrected here (PRIV-206);
4. ``attachments`` with ``created_by == _anonymized`` and a non-empty ``original_filename`` → ``""``
   (``attachments.filename_cleared``).

**Phases** (``details.phases``, PRIV-718). ``precheck`` — the inventory change of this build is
importable (``garden_plan_audit.user_key`` is a marker rule, ``attachments`` clears
``original_filename``), the live tombstone check recognises both frozen generations, the collections
exist; else ``precondition_unmet`` and nothing is written. ``dry_run`` — the counts, nothing written.
``apply`` — one stream transaction per tenant for steps 1, 2 and 4; a failing tenant is rolled back,
listed in ``tenants_failed``, and the others go on; then ``status = partial`` and the report is
``incomplete``, so the runner records nothing and the next boot retries. ``verify`` — steps 1, 2 and 4
counted again; anything left is ``verify_failed``, equally not recorded. ``monitor`` — bucket 3 is
handed to the daily ``privacy.consistency`` beat.

**Frozen (NFR-016 M-7).** Marker, tombstone pattern and the step-3 cells are literals here, as the
inventory stood when this version was written (``ErasureEngine.tombstone_watch_fields()`` minus the
cells steps 1 and 2 correct). The step-3 count goes through
:func:`app.data_access.arango.tombstone_census.count_tombstones_by_field` — the same AQL the beat runs —
but with these frozen arguments: the shared function holds the query mechanism only, never the policy,
so a later change of the inventory moves the beat and not this migration's result. The precheck is the
one place that reads the live inventory, because PRIV-703 demands exactly that check.

**Tenant binding.** Steps 1, 2 and 4 filter ``doc.tenant_key == @tenant_key`` inside the tenant's own
transaction; the tenant list is read once. Step 3 counts per cell for the installation (several of the
cells are account-scoped and carry no ``tenant_key``); it writes nothing.

Idempotent (M-3): a corrected value no longer matches, a second run changes nothing. Dry run (M-5):
counts only. Irreversible (M-6): the tombstones and file names are destroyed on purpose; the persisted
dry-run report is the evidence (spec/privacy/09 §11).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.tombstone_census import count_tombstones_by_field
from app.data_access.arango.transactions import stream_transaction
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.framework.report_store import MAX_SAMPLES_PER_BUCKET, redact_details

logger = structlog.get_logger(__name__)

#: Frozen here (M-7): the marker and both tombstone generations as ``app.domain.models.privacy`` defined
#: them when this version was written (``ANONYMIZED_MARKER``, ``TOMBSTONE_REGEX``).
_MARKER = "_anonymized"
_TOMBSTONE_REGEX = "^anon_[0-9a-f]{16}$|^anon2_[0-9a-f]{16}$"
#: One sample of each generation, for the precheck that the live check still recognises both.
_GENERATION_SAMPLES = ("anon_0123456789abcdef", "anon2_0123456789abcdef")

_TENANT_DELETED = "deleted"

BUCKET_CARE_EVENTS = "care_events.tombstone_to_marker"
BUCKET_PLAN_AUDIT = "garden_plan_audit.tombstone_to_marker"
BUCKET_FILENAMES = "attachments.filename_cleared"
BUCKET_UNDECLARED = "undeclared_tombstones"
#: The buckets steps 1, 2 and 4 correct, in order; ``verify`` counts exactly these again.
CORRECTED_BUCKETS = (BUCKET_CARE_EVENTS, BUCKET_PLAN_AUDIT, BUCKET_FILENAMES)

#: Frozen (M-7): ``ErasureEngine.tombstone_watch_fields()`` on 2026-11-15 without the three cells steps 1
#: and 2 correct (``care_events.performed_by_user_key``, ``care_events.created_by``,
#: ``garden_plan_audit.user_key``).
UNDECLARED_CELLS: tuple[tuple[str, str], ...] = (
    ("ai_audit_log", "user_key"),
    ("ai_conversations", "user_key"),
    ("ai_tip_cache", "dismissed_by"),
    ("api_keys", "user_key"),
    ("attachments", "created_by"),
    ("auth_providers", "user_key"),
    ("bed_templates", "created_by"),
    ("calendar_feeds", "user_key"),
    ("care_events", "performed_for_user_key"),
    ("care_events", "redacted_by"),
    ("care_events", "voided_by"),
    ("data_export_requests", "user_key"),
    ("email_change_requests", "user_key"),
    ("garden_objects", "created_by"),
    ("identification_requests", "user_key"),
    ("import_jobs", "uploaded_by"),
    ("invitations", "accepted_by_user_key"),
    ("invitations", "invited_by_user_key"),
    ("manual_overrides", "created_by"),
    ("mcp_idempotency_record", "service_account_key"),
    ("memberships", "user_key"),
    ("notification_preferences", "user_key"),
    ("notifications", "user_key"),
    ("onboarding_states", "user_key"),
    ("pest_detections", "user_key"),
    ("pest_image_contributions", "contributed_by"),
    ("pest_image_contributions", "promoted_by"),
    ("plant_diagnosis_requests", "user_key"),
    ("plant_diary_entries", "analysis_claimed_by"),
    ("plant_diary_entries", "analysis_requested_by"),
    ("plant_diary_entries", "created_by"),
    ("processing_restrictions", "user_key"),
    ("refresh_tokens", "user_key"),
    ("sites", "plan.plan_updated_by"),
    ("task_comments", "created_by"),
    ("tasks", "assigned_to_user_key"),
    ("tenant_export_requests", "requested_by_user_key"),
    ("tenant_import_requests", "requested_by_user_key"),
    ("tenants", "owner_user_key"),
    ("user_preferences", "user_key"),
    ("weather_source_configs", "updated_by"),
)

#: A tenant's transaction carries three bulk updates; the 10 s default of the helper is sized for a plan batch.
_TENANT_TIME_BUDGET_SECONDS = 600.0

_TENANT_KEYS = """
FOR t IN @@tenants
  FILTER t.status != @deleted
  SORT t._key
  RETURN t._key
"""

_CARE_EVENT_MATCH = """
  FILTER doc.tenant_key == @tenant_key
  FILTER (IS_STRING(doc.performed_by_user_key) AND REGEX_TEST(doc.performed_by_user_key, @pattern))
      OR (IS_STRING(doc.created_by) AND REGEX_TEST(doc.created_by, @pattern))
"""

_PLAN_AUDIT_MATCH = """
  FILTER doc.tenant_key == @tenant_key
  FILTER IS_STRING(doc.user_key) AND REGEX_TEST(doc.user_key, @pattern)
"""

_FILENAME_MATCH = """
  FILTER doc.tenant_key == @tenant_key
  FILTER doc.created_by == @marker AND IS_STRING(doc.original_filename) AND doc.original_filename != ""
"""

_HITS = """
LET hits = (FOR doc IN @@collection {match} RETURN doc._key)
RETURN {{ n: LENGTH(hits), sample: SLICE(hits, 0, @limit) }}
"""

_CARE_EVENT_UPDATE = (
    "FOR doc IN @@collection"
    + _CARE_EVENT_MATCH
    + """
  UPDATE doc WITH MERGE(
    IS_STRING(doc.performed_by_user_key) AND REGEX_TEST(doc.performed_by_user_key, @pattern)
      ? { performed_by_user_key: @marker } : {},
    IS_STRING(doc.created_by) AND REGEX_TEST(doc.created_by, @pattern) ? { created_by: @marker } : {}
  ) IN @@collection
  RETURN 1
"""
)

_PLAN_AUDIT_UPDATE = (
    "FOR doc IN @@collection"
    + _PLAN_AUDIT_MATCH
    + "  UPDATE doc WITH { user_key: @marker } IN @@collection\n  RETURN 1\n"
)

_FILENAME_UPDATE = (
    "FOR doc IN @@collection" + _FILENAME_MATCH + '  UPDATE doc WITH { original_filename: "" } IN @@collection\n'
    "  RETURN 1\n"
)

#: bucket -> (collection, match clause, update statement)
_STEPS: dict[str, tuple[str, str, str]] = {
    BUCKET_CARE_EVENTS: (col.CARE_EVENTS, _CARE_EVENT_MATCH, _CARE_EVENT_UPDATE),
    BUCKET_PLAN_AUDIT: (col.GARDEN_PLAN_AUDIT, _PLAN_AUDIT_MATCH, _PLAN_AUDIT_UPDATE),
    BUCKET_FILENAMES: (col.ATTACHMENTS, _FILENAME_MATCH, _FILENAME_UPDATE),
}

_REQUIRED_COLLECTIONS = (col.TENANTS, col.CARE_EVENTS, col.GARDEN_PLAN_AUDIT, col.ATTACHMENTS)


def _binds(collection: str, tenant_key: str) -> dict[str, Any]:
    return {"@collection": collection, "tenant_key": tenant_key, "pattern": _TOMBSTONE_REGEX, "marker": _MARKER}


def _used_binds(query: str, binds: dict[str, Any]) -> dict[str, Any]:
    """ArangoDB refuses a bind parameter the query does not use; keep only the ones it names."""
    return {name: value for name, value in binds.items() if (f"@{name}" in query)}


class TombstoneCopyStore:
    """The AQL of v0109: tenant list, per-tenant counts and the per-tenant transaction, bound and tenant-filtered."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def missing_collections(self) -> list[str]:
        return [name for name in _REQUIRED_COLLECTIONS if not self._db.has_collection(name)]

    def tenant_keys(self) -> list[str]:
        cursor = self._db.aql.execute(_TENANT_KEYS, bind_vars={"@tenants": col.TENANTS, "deleted": _TENANT_DELETED})
        return [str(key) for key in cast(Cursor, cursor)]

    def hits(self, bucket: str, tenant_key: str) -> tuple[int, list[str]]:
        """``(count, up to MAX_SAMPLES_PER_BUCKET row keys)`` of the tenant's rows step *bucket* would change."""
        collection, match, _update = _STEPS[bucket]
        query = _HITS.format(match=match)
        binds = _used_binds(query, _binds(collection, tenant_key)) | {"limit": MAX_SAMPLES_PER_BUCKET}
        row = next(iter(cast(Cursor, self._db.aql.execute(query, bind_vars=binds))), None) or {}
        return int(row.get("n", 0)), [str(key) for key in row.get("sample", [])]

    def apply(self, tenant_key: str) -> dict[str, int]:
        """Steps 1, 2 and 4 for one tenant in one stream transaction; any failure rolls all three back."""
        changed: dict[str, int] = {}
        with stream_transaction(
            self._db,
            write=tuple(collection for collection, _match, _update in _STEPS.values()),
            entity="privacy_tombstone_copies",
            time_budget_seconds=_TENANT_TIME_BUDGET_SECONDS,
        ) as txn:
            for bucket, (collection, _match, update) in _STEPS.items():
                binds = _used_binds(update, _binds(collection, tenant_key))
                changed[bucket] = sum(1 for _ in txn.aql.execute(update, bind_vars=binds))
        return changed

    def count_undeclared(self) -> dict[str, int]:
        return count_tombstones_by_field(self._db, UNDECLARED_CELLS, _TOMBSTONE_REGEX)


def _unmet_inventory() -> list[str]:
    """PRIV-703 (a)/(b): the inventory change of this build, and the live tombstone check, are in place."""
    from app.domain.engines.erasure_engine import ErasureEngine
    from app.domain.models.privacy import is_tombstone

    unmet: list[str] = []
    plan_audit = [
        rule
        for rule in ErasureEngine.ANONYMIZE_COLLECTIONS
        if (rule.collection, rule.user_field) == ("garden_plan_audit", "user_key")
    ]
    if not plan_audit or any(
        rule.replacement_strategy != "marker" or rule.anonymized_value != _MARKER for rule in plan_audit
    ):
        unmet.append("rule.garden_plan_audit.user_key.marker")
    if any(rule.collection == "garden_plan_audit" for rule in ErasureEngine.PSEUDONYMIZE_AUDIT_COLLECTIONS):
        unmet.append("rule.garden_plan_audit.user_key.not_pseudonymized")
    attachments = [
        rule
        for rule in ErasureEngine.ANONYMIZE_COLLECTIONS
        if (rule.collection, rule.user_field) == ("attachments", "created_by")
    ]
    if not attachments or not all("original_filename" in rule.clear_fields for rule in attachments):
        unmet.append("rule.attachments.clear_fields.original_filename")
    if not all(is_tombstone(sample) for sample in _GENERATION_SAMPLES):
        unmet.append("privacy.tombstone_regex.both_generations")
    return unmet


class PrivacyTombstoneCopiesMigration(Migration):
    version = "0109"
    name = "privacy_tombstone_copies"
    description = (
        "Replace copied erased-account tombstones (both generations) in care_events and garden_plan_audit by the "
        "_anonymized marker, clear original_filename of anonymised attachments, count tombstones outside the "
        "allowlist (spec/privacy/09 section 3, M-P1)."
    )
    reversible = False
    kind = "privacy_correction"

    #: Seam for the unit tests: the AQL lives in :class:`TombstoneCopyStore`, the phases here.
    store_factory: Callable[[StandardDatabase], TombstoneCopyStore] = TombstoneCopyStore

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        store = type(self).store_factory(db)
        phases: dict[str, Any] = {}

        unmet = store.missing_collections() + _unmet_inventory()
        if unmet:
            phases["precheck"] = {"ok": False, "unmet": unmet, "candidates": {}}
            return self._report(dry_run, "precondition_unmet", phases, {}, {}, scanned=0, changed=0)

        tenants = store.tenant_keys()
        buckets: dict[str, Any] = {bucket: {} for bucket in CORRECTED_BUCKETS}
        samples: dict[str, list[str]] = {bucket: [] for bucket in CORRECTED_BUCKETS}
        candidates: dict[str, int] = {}
        for tenant_key in tenants:
            for bucket in CORRECTED_BUCKETS:
                count, sample = store.hits(bucket, tenant_key)
                if count:
                    buckets[bucket][tenant_key] = count
                    candidates[tenant_key] = candidates.get(tenant_key, 0) + count
                    room = MAX_SAMPLES_PER_BUCKET - len(samples[bucket])
                    samples[bucket].extend(sample[: max(room, 0)])
        undeclared = store.count_undeclared()
        buckets[BUCKET_UNDECLARED] = {cell: count for cell, count in undeclared.items() if count}
        scanned = sum(candidates.values())
        phases["precheck"] = {"ok": True, "unmet": [], "candidates": candidates}
        phases["dry_run"] = {"would_change": {bucket: sum(buckets[bucket].values()) for bucket in CORRECTED_BUCKETS}}
        phases["monitor"] = {"handed_to": "privacy.consistency"}

        if dry_run:
            return self._report(dry_run, "dry_run", phases, buckets, samples, scanned=scanned, changed=0)

        done: list[str] = []
        failed: list[str] = []
        applied: dict[str, Any] = {bucket: {} for bucket in CORRECTED_BUCKETS}
        for tenant_key in tenants:
            if tenant_key not in candidates:
                done.append(tenant_key)
                continue
            try:
                changed_by_bucket = store.apply(tenant_key)
            except Exception as exc:  # noqa: BLE001 — one tenant's failure must not stop the others (PRIV-718)
                failed.append(tenant_key)
                logger.warning(
                    "privacy_tombstone_copies.tenant_failed", tenant_key=tenant_key, error_type=type(exc).__name__
                )
                continue
            done.append(tenant_key)
            for bucket, count in changed_by_bucket.items():
                if count:
                    applied[bucket][tenant_key] = count
        changed = sum(sum(per_tenant.values()) for per_tenant in applied.values())
        phases["apply"] = {
            "tenants_done": done,
            "tenants_failed": failed,
            "changed": {bucket: sum(applied[bucket].values()) for bucket in CORRECTED_BUCKETS},
        }
        buckets.update(applied)

        residual = {bucket: 0 for bucket in CORRECTED_BUCKETS}
        for tenant_key in tenants:
            for bucket in CORRECTED_BUCKETS:
                residual[bucket] += store.hits(bucket, tenant_key)[0]
        phases["verify"] = {"residual": residual}

        if failed:
            status = "partial"
        elif any(residual.values()):
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
        log("privacy_tombstone_copies", dry_run=dry_run, **logged)
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


migration = PrivacyTombstoneCopiesMigration()
