"""v0036 — species tenant_key cutover: default every existing species to global (#808).

``Species`` grew a ``tenant_key`` field (REQ-001 v4.0, F-3): an empty string ``""``
means the record belongs to the global/system catalogue every tenant may read; a
non-empty value binds it to one owning tenant. New writes now set it — the
interactive create stamps the caller's tenant, every global path (seed, import,
enrichment, the normalization UPSERT) leaves it ``""``. This migration establishes
the field on the *existing* population so F-5's read predicate
(``tenant_key == @caller OR tenant_key == "" OR tenant_key == null``) has a
well-defined value to match on every legacy document.

The cutover policy — a no-owner-stamp migration (R6)
---------------------------------------------------
Every existing species — whether ``origin: system`` seed data or ``origin: tenant``
user-created data — is defaulted to ``tenant_key == ""`` (global). It is
**deliberately** the case that ``origin: tenant`` species are left **without an
owner** and stay part of the shared catalogue:

* which tenant created a legacy ``origin: tenant`` species was **never recorded**
  (there was no ``tenant_key`` field and no creator edge on species), so there is
  no owner to recover — guessing one would be inventing data;
* stamping a *default* tenant onto them is exactly the #324 regression (R6
  forbids it verbatim): every tenant but one would lose the species they see
  today. That default-stamp path is ``backfill_tenant_key.py`` — and this is why
  ``SPECIES`` is **not**, and must never be, in its ``TOP_LEVEL_COLLECTIONS``.

So the only defensible cutover value is ``""``: it keeps the catalogue exactly as
visible as it is today (nothing narrows), and only *newly* created species bind to
their creator going forward. This is a known, bounded limitation, not a
regression.

Idempotency (M-3) — keyed on the attribute being absent
-------------------------------------------------------
``""`` is a legitimate *final* value here (global is a real answer), so idempotency
cannot key on ``tenant_key == ""`` the way the owner-recovering backfills
(``v0004``, ``v0020``, ``v0034``) do. It keys on the attribute being **absent**
(``doc.tenant_key == null``): a species already carrying the field — including one
this migration set to ``""`` — is skipped, so a re-run finds no attribute-less row
and writes nothing (``changed == 0``). Dry-run (M-5) computes the full plan and
writes nothing. Irreversible (M-6): the pre-cutover absent attribute is not
recoverable once written, so there is no honest inverse.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: ``{"key": …}`` rows ready for a batched UPDATE to ``tenant_key == ""``.
type UpdateKeys = list[dict[str, str]]


class CutoverSpeciesTenantKeyMigration(Migration):
    version = "0036"
    name = "cutover_species_tenant_key"
    description = (
        "Default existing species to global tenant_key '' — no owner stamped, origin:tenant stays global (#808)."
    )
    reversible = False

    def _attributeless(self, db: StandardDatabase) -> list[dict[str, Any]]:
        """Species whose ``tenant_key`` attribute is absent (read-only).

        The filter is ``== null`` on purpose, not ``== ''``: ``""`` is a
        legitimate final value here (global), so only rows predating the field —
        where the attribute is missing entirely — are candidates. ``origin`` is
        projected purely so the report can show that ``origin: tenant`` rows are
        deliberately left global; it never changes the stamped value.
        """
        if not db.has_collection(col.SPECIES):
            return []
        return list(
            db.aql.execute(
                "FOR doc IN @@collection FILTER doc.tenant_key == null RETURN {key: doc._key, origin: doc.origin}",
                bind_vars={"@collection": col.SPECIES},
            )
        )

    @staticmethod
    def _apply(db: StandardDatabase, keys: UpdateKeys) -> None:
        if not keys:
            return
        db.aql.execute(
            "FOR row IN @rows UPDATE {_key: row.key, tenant_key: ''} IN @@collection",
            bind_vars={"rows": keys, "@collection": col.SPECIES},
        )

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        origin_tenant = 0
        origin_other = 0
        keys: UpdateKeys = []
        for species in self._attributeless(db):
            keys.append({"key": species["key"]})
            if species.get("origin") == "tenant":
                origin_tenant += 1
            else:
                origin_other += 1

        if not dry_run:
            self._apply(db, keys)

        changed = len(keys)
        details = {
            # Every candidate is defaulted to the same "" — split by origin only to
            # make the R6 policy legible: these origin:tenant rows stay global.
            "defaulted_global": changed,
            "origin_tenant_left_global": origin_tenant,
            "origin_other_left_global": origin_other,
        }
        logger.info(
            "cutover_species_tenant_key_dry_run" if dry_run else "cutover_species_tenant_key_applied",
            scanned=changed,
            changed=0 if dry_run else changed,
            to_update=changed,
            origin_tenant_left_global=origin_tenant,
            origin_other_left_global=origin_other,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=changed,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={"to_update": changed, **details} if dry_run else details,
        )


migration = CutoverSpeciesTenantKeyMigration()
