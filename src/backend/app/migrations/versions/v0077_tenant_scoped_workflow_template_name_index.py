"""v0077 — move the workflow template name index from collection-wide to per tenant (#2027).

``workflow_templates`` is a hybrid catalogue: global templates (``tenant_key`` empty,
the seeded ones ``is_system``) plus each tenant's own, created through
``POST /api/v1/t/{slug}/tasks/workflows``. Its unique index was nevertheless
collection-wide on ``name``: a tenant was refused a name another tenant or the seed
already holds. Measured on
ArangoDB 3.12 (P0 of #2027): the workflow seed found a tenant's "Cannabis SOG" by
name, rewrote it as a global ``is_system`` template and hung the seed's phases on
the tenant's key. The loader now matches global rows only; this index is what lets
the global row exist beside the tenant's. The key becomes ``(tenant_key, name)``
(:data:`~app.data_access.arango.collections.WORKFLOW_TEMPLATE_NAME_INDEX_FIELDS`),
the global rows forming one scope of their own.

**Order.** The compound index is created first — ``ensure_collections`` already does
so on every boot; this version creates it itself when it is missing so the drop
never depends on the boot order — and only then is the legacy index dropped, through
:func:`~app.migrations.support.legacy_indexes.retire_legacy_index`. There is no
window without a constraint.

**Both legacy spellings.** Until 2026-06-07 ``ensure_collections`` created the
index with ``add_hash_index`` (``516bcd832^:…/collections.py:1168``) and
ArangoDB 3.12 reports it as ``type: "hash"``; since then as ``persistent``. A pre-June volume that booted the
later code carries both (the identical definition created a second index, #2034).
The shared selector recognises every one of them — a ``type == "persistent"`` match
would leave the old constraint in force on every pre-June volume.

**Never without the replacement.** The drop is gated on the re-read index list: if no
unique ``(tenant_key, name)`` index exists after the creation step, nothing is
dropped and the run reports ``precondition_unmet`` with the counts, so the runner
leaves this version pending and a later boot retries it.

**One value moves: a missing ``tenant_key`` becomes ``""``.** Before the index work
every row without ``tenant_key`` (indexed as ``null``) is normalised to ``""``
(:func:`~app.migrations.support.null_tenant_keys.normalise_null_tenant_keys`):
``null`` and ``""`` are two values for the compound index, so a legacy global row
without the field and a later global row with ``""`` of the same name would both be
admitted. A ``null`` row whose name a ``""`` row already holds is counted, not
rewritten. Otherwise no row can violate the compound index: a set unique on
``name`` is unique on any superset of the fields.

Idempotent (M-3): a re-run finds the compound present and no legacy index →
``changed == 0``. Dry-run (M-5) reports the plan and touches no index. Irreversible
(M-6): once a global and a tenant row share a name, the collection-wide index can no
longer be created without renaming somebody's row.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.collection import StandardCollection
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import IndexShape, retire_legacy_index
from app.migrations.support.null_tenant_keys import normalise_null_tenant_keys

logger = structlog.get_logger(__name__)

#: The constraint #2027 retires: one workflow template name across every tenant and the seed.
LEGACY_WORKFLOW_TEMPLATE_NAME_INDEX = IndexShape(
    fields=tuple(col.LEGACY_WORKFLOW_TEMPLATE_NAME_INDEX_FIELDS), unique=True
)

#: Its replacement, as ``ensure_collections`` creates it.
WORKFLOW_TEMPLATE_NAME_INDEX = IndexShape(fields=tuple(col.WORKFLOW_TEMPLATE_NAME_INDEX_FIELDS), unique=True)


def _has_replacement(templates: StandardCollection) -> bool:
    """Whether a unique ``(tenant_key, name)`` index exists (``persistent`` or ``hash``)."""
    rows = templates.indexes()
    return isinstance(rows, list) and any(
        isinstance(idx, dict) and WORKFLOW_TEMPLATE_NAME_INDEX.matches(idx) for idx in rows
    )


def _create_replacement(templates: StandardCollection) -> None:
    """Create the compound unique index; a separate step so the gate after it is testable."""
    templates.add_persistent_index(fields=list(col.WORKFLOW_TEMPLATE_NAME_INDEX_FIELDS), unique=True)


class TenantScopedWorkflowTemplateNameIndexMigration(Migration):
    version = "0077"
    name = "tenant_scoped_workflow_template_name_index"
    description = (
        "Replace the collection-wide unique workflow_templates(name) index with (tenant_key, name), "
        "retiring the legacy index whether it is typed persistent or hash (#2027)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.WORKFLOW_TEMPLATES):
            return MigrationReport(version=self.version, name=self.name, dry_run=dry_run)
        templates = db.collection(col.WORKFLOW_TEMPLATES)

        # Global rows written without the field become ``""`` first, so the compound
        # index sees one value for "global" (null != "" for a unique index).
        nulls = normalise_null_tenant_keys(db, col.WORKFLOW_TEMPLATES, dry_run=dry_run)

        needs_compound = not _has_replacement(templates)
        compound_created = False
        if needs_compound and not dry_run:
            # First the replacement constraint; dropping the old one before it exists
            # would leave a window with no uniqueness at all. Counted from the re-read,
            # not from the call having been made.
            _create_replacement(templates)
            compound_created = _has_replacement(templates)

        outcome = retire_legacy_index(
            templates,
            legacy=LEGACY_WORKFLOW_TEMPLATE_NAME_INDEX,
            replacement=WORKFLOW_TEMPLATE_NAME_INDEX,
            dry_run=dry_run,
        )
        # A dry run does not create the replacement, so the selector sees none; the
        # real run would have created it first — that is the plan, not a refusal.
        refused = outcome.refused and not (dry_run and needs_compound)

        details: dict[str, Any] = {
            **outcome.details(),
            **nulls.details(),
            "refused_without_replacement": refused,
            "compound_created": compound_created,
        }
        if dry_run:
            details["compound_to_create"] = needs_compound
        if refused:
            logger.warning("tenant_scoped_workflow_template_name_index_refused", **details)
        else:
            logger.info("tenant_scoped_workflow_template_name_index", dry_run=dry_run, **details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(outcome.legacy_ids) + int(needs_compound) + nulls.candidates + nulls.conflicts,
            changed=0 if dry_run else int(compound_created) + outcome.dropped + nulls.normalised,
            dry_run=dry_run,
            precondition_unmet=refused,
            details=details,
        )


migration = TenantScopedWorkflowTemplateNameIndexMigration()
