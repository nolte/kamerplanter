"""v0035 — backfill tenant_key on task templates from their parent workflow (#965 item 1).

``TaskTemplate`` grew its own ``tenant_key`` field so a template's write can be
tenant-verified on the entity itself instead of only through its parent
``WorkflowTemplate`` (which is what left #965 item 1 open: a standalone template
had no anchor at all). Rows created before the field existed carry no
``tenant_key`` attribute; this migration stamps one on each so the new
entity-level guard in ``update``/``delete_task_template`` has something to check.

Where the owner comes from
--------------------------
* **Template of a tenant-owned workflow** → that workflow's ``tenant_key``. The
  parent is read off the denormalised ``workflow_template_key`` field the template
  already carries, so no graph traversal is needed.
* **Template of a system workflow** (parent ``is_system``, ``tenant_key == ""``)
  → ``""`` (global). The catalogue must stay readable, instantiable and
  duplicatable by every tenant (#324); an empty owner is exactly that row.
* **Template of an auto-generated / shared plan** (parent ``tenant_key == ""``,
  not ``is_system``) → ``""`` (global). This is the copy-on-write source #1003
  every tenant reads; it stays shared until a tenant's first edit forks a private
  copy, so its templates must remain global too.

Standalone templates — the honest limitation
--------------------------------------------
A template with **no** ``workflow_template_key`` (a supported standalone state
before this change) has **no stored owner to recover**. Standalone templates were
previously creatable by any tenant with nothing recorded about who created them:
there is no creator field, no owning edge, no parent to inherit from. Guessing an
owner would be inventing data. The only defensible backfill value is therefore
``""`` (global) — the same value a system/shared parent yields, and the value the
service's read-guard treats as the writable-by-all global catalogue. This is a
**known limitation**: such rows stay editable by every tenant exactly as they
were before item 1. It is not a regression (nothing narrowed), and it is bounded
— **newly** created standalone templates are stamped with the caller's tenant by
``TaskService.create_task_template`` and are properly owned. A template whose
``workflow_template_key`` points at a workflow that no longer exists (a dangling
reference) is treated the same way: the owner cannot be sourced, so it falls to
``""`` and is reported under ``dangling_parent`` rather than guessed at.

Idempotency (M-3) — why the empty string is not the sentinel here
-----------------------------------------------------------------
Every other tenant-key backfill (``v0004``, ``v0020``, ``v0034``) treats
``tenant_key == ""`` as "not yet done", because for those collections an empty
owner is never a legitimate final value. Here it **is** — global is a real
answer. So this migration keys idempotency on the *attribute being absent*
(``doc.tenant_key == null``), not on it being empty: a row already backfilled to
``""`` has the attribute present and is skipped on a re-run. A second run finds no
attribute-less row and writes nothing (``changed == 0``). Dry-run (M-5) computes
the full plan and writes nothing. Irreversible (M-6): the pre-fix absent
attribute is not recoverable once written, so there is no honest inverse.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: ``{"key": …, "tenant_key": …}`` pairs ready for a batched UPDATE.
type UpdatePairs = list[dict[str, str]]


class BackfillTaskTemplateTenantKeyMigration(Migration):
    version = "0035"
    name = "backfill_task_template_tenant_key"
    description = "Stamp tenant_key on task templates from their parent workflow; standalone/system → global (#965)."
    reversible = False

    def _attributeless(self, db: StandardDatabase) -> list[dict[str, Any]]:
        """Task templates whose ``tenant_key`` attribute is absent (read-only).

        The filter is ``== null`` on purpose, not ``== ''``: an empty string is a
        legitimate final value here (global), so only rows predating the field —
        where the attribute is missing entirely — are candidates. ``workflow_
        template_key`` is projected so the owner can be resolved without a second
        read; it is a code literal, safe to interpolate, while the collection is
        bound as ``@@collection``.
        """
        if not db.has_collection(col.TASK_TEMPLATES):
            return []
        return list(
            db.aql.execute(
                "FOR doc IN @@collection "
                "FILTER doc.tenant_key == null "
                "RETURN {key: doc._key, workflow_template_key: doc.workflow_template_key}",
                bind_vars={"@collection": col.TASK_TEMPLATES},
            )
        )

    def _workflow(self, db: StandardDatabase, key: str) -> dict[str, Any] | None:
        """The parent workflow document, or ``None`` if the key is unset/dangling."""
        if not key or not db.has_collection(col.WORKFLOW_TEMPLATES):
            return None
        return db.collection(col.WORKFLOW_TEMPLATES).get(key)

    def _resolve_owner(
        self,
        db: StandardDatabase,
        parent_key: str,
        counters: dict[str, int],
    ) -> str:
        """Owner to stamp on a template, counting the reason into ``counters``.

        Returns the parent's ``tenant_key`` for a tenant-owned parent; ``""`` for
        a system/shared parent, a standalone template (no parent key) or a
        dangling parent reference — the three cases with no recoverable owner.
        """
        if not parent_key:
            counters["standalone"] += 1
            return ""
        parent = self._workflow(db, parent_key)
        if parent is None:
            counters["dangling_parent"] += 1
            return ""
        owner = parent.get("tenant_key") or ""
        if owner:
            counters["from_tenant_parent"] += 1
        else:
            counters["system_or_shared_parent"] += 1
        return owner

    @staticmethod
    def _apply(db: StandardDatabase, updates: UpdatePairs) -> None:
        if not updates:
            return
        db.aql.execute(
            "FOR pair IN @pairs UPDATE {_key: pair.key, tenant_key: pair.tenant_key} IN @@collection",
            bind_vars={"pairs": updates, "@collection": col.TASK_TEMPLATES},
        )

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        counters = {
            "from_tenant_parent": 0,
            "system_or_shared_parent": 0,
            "standalone": 0,
            "dangling_parent": 0,
        }
        updates: UpdatePairs = []
        for template in self._attributeless(db):
            owner = self._resolve_owner(db, template.get("workflow_template_key") or "", counters)
            updates.append({"key": template["key"], "tenant_key": owner})

        if not dry_run:
            self._apply(db, updates)

        changed = len(updates)
        details = {**counters}
        logger.info(
            "backfill_task_template_tenant_key_dry_run" if dry_run else "backfill_task_template_tenant_key_applied",
            scanned=changed,
            changed=0 if dry_run else changed,
            to_update=changed,
            **counters,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=changed,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={"to_update": changed, **details} if dry_run else details,
        )


migration = BackfillTaskTemplateTenantKeyMigration()
