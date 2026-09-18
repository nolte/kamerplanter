"""v0051 — move the stored CEC under the key the model has read since #1174 (#1468).

#1174 renamed the substrate field ``cec_meq_per_100g`` → ``cec_meq_per_100cm3`` in
the model and in ``seed_data/substrates.yaml``. Nothing moved the **stored**
documents: ``seed_substrates.py`` identifies a record by ``(type, name_de or
brand)`` and *skips* one that exists (it is a seeder, never an upsert), so a
database seeded before #1174 keeps the old key for its lifetime while every reader
asks for the new one. ``Substrate.cec_meq_per_100cm3`` has no alias, so the whole
catalogue reads as ``None``: ``calculate_mix_properties`` aggregates no CEC at all
and the pH-buffering weight in ``substrate_mix_engine`` falls back to the ordinal
``buffer_capacity`` for every component.

v0047 named this gap and deliberately left it out — "no value changed, a *key*
moved, and it moved for tenant-owned mixes too, which this migration is explicitly
scoped away from". This is that operation.

## Measured before it was written (dev cluster, 2026-09-18)

Read-only, through the backend pod's own connection:

* ``substrates`` holds **29** documents: **27** carry the old key and not the new
  one, **0** carry the new key, **0** carry both, 2 carry neither (the
  ``hydro_solution`` record, which has no CEC in the catalogue either, and a
  hand-made ``soil`` row);
* across all **300** collections, ``cec_meq_per_100g`` and ``cec_meq_per_100cm3``
  appear in ``substrates`` and nowhere else — ``substrate_batches`` references a
  substrate by key and stores no copy of its physics, and no tank recipe embeds
  one. The rename is therefore one collection wide;
* no reader of the old key survives anywhere in the tree (frontend, E2E, MCP,
  HA): the four remaining mentions are one docstring, one test docstring, one
  REQ-019 paragraph and v0047's exclusion note.

The issue says 28 records; 27 is the number, because the catalogue's 28th record
(``Hydrokultur (kein Substrat)``) declares no CEC in the YAML either. The
difference does not change the operation.

## The decision this implements

Operator decision (2026-09-17): **rename in place, no read alias in the model.**
The unit did not change with the name — the values were always volume-based
(#1152 §F) — so there is nothing to convert and nothing to reconcile. A model-side
fallback would have put a second name for one quantity into every reader for a
release and left the same migration to write afterwards.

## Scope: every substrate document, tenant-owned mixes included

Unlike v0047/v0049 this migration does **not** filter to ``tenant_key == ""``.
Those two write *catalogue values*, and a value a tenant chose is theirs. This one
moves a quantity from one attribute name to another without touching what it says,
and a tenant mix stored before #1174 is broken in exactly the same way as a seeded
record — its CEC reads as ``None`` for its owner. Leaving it behind would keep the
defect alive in the only records nobody can re-seed.

## The conflict case, and why it is reported rather than resolved

A document carrying **both** keys is left untouched and named in the report.
``cm3`` is what the model reads today, so it is already the effective value, and
the migration has no way to tell an ``100g`` leftover from a number somebody put
there on purpose. Overwriting either one would be a silent decision about a
quantity; naming the record lets the operator make it. Measured population of this
case on the dev cluster: zero.

Idempotent (M-3): the rename is chosen by ``HAS(old) AND NOT HAS(new)``, which is
false for every document a previous run converted, so a re-run reports
``changed == 0`` and every converted record under ``already_correct`` — except one
that stored ``cec_meq_per_100g: null``, which had no value to move and re-reads as
``no_cec_stored``, the thing it always was.

No document can abort the run (M-4): the scan and the writes are separate round
trips, so a record deleted in between would raise out of ``up`` and take the whole
startup with it. Each write is isolated and a failure is reported under
``write_failed`` with the record named; ``changed`` counts writes that succeeded,
never writes that were planned.

Not reversible (M-6). The inverse is not "rename back": after this runs, a
document carrying ``cec_meq_per_100cm3`` may be one this migration converted, one
the seeder wrote from the post-#1174 catalogue, or one a tenant created through
the API — they are indistinguishable, and a ``down`` would move all three under a
name no reader has asked for since #1174, re-creating the defect for records that
never had it. There is no state worth restoring: the old key is a name the code
abandoned, not data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog
from arango.database import StandardDatabase
from arango.exceptions import ArangoError

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: The attribute #1174 abandoned and the one it introduced.
OLD_KEY = "cec_meq_per_100g"
NEW_KEY = "cec_meq_per_100cm3"

#: How many rows each itemised list carries. Totals are always exact — the same
#: split v0050 uses, so a large installation gets a readable report rather than a
#: truncated count.
_REPORT_SAMPLE_LIMIT = 500

#: Rows the **scan cursor** fetches per round trip — nothing else. Named for what
#: it is after a review read the earlier ``_BATCH_SIZE`` as a write batch: the
#: writes below are one PATCH per document, because the population is a 28-row
#: catalogue plus whatever mixes tenants own, and a per-document round trip is what
#: lets a single failing document be reported instead of taking its batch with it.
_SCAN_BATCH_SIZE = 500

#: Exclusive categories: every scanned document lands in exactly one.
#:
#: ``no_cec_stored`` is not an error — a nutrient solution has no exchange capacity
#: to declare, and the catalogue's own ``Hydrokultur`` record carries neither key.
#:
#: ``old_key_dropped_without_value`` is its own category rather than part of
#: ``renamed`` because nothing is renamed there: a stored ``cec_meq_per_100g: null``
#: says "no CEC", the model reads an absent ``cec_meq_per_100cm3`` as the same
#: ``None``, and all the write does is remove the abandoned attribute. Counting it
#: as a rename would report a value moving that never existed — and the re-run then
#: files the record under ``no_cec_stored``, which is what it has always been.
_CATEGORIES: tuple[str, ...] = (
    "renamed",
    "old_key_dropped_without_value",
    "both_keys_present",
    "already_correct",
    "no_cec_stored",
)

#: Not a category: a document can only land here **after** being classified
#: ``renamed`` or ``old_key_dropped_without_value``, so it is reported beside the
#: exclusive set rather than inside it (v0050 reports ``family_unresolved`` the same
#: way). See :meth:`RenameCecKeyMigration._write`.
_WRITE_FAILED = "write_failed"


@dataclass
class _Plan:
    """What the run would do, computed without writing (M-5)."""

    scanned: int = 0
    totals: dict[str, int] = field(default_factory=lambda: dict.fromkeys(_CATEGORIES, 0))
    rows: dict[str, list[str]] = field(default_factory=lambda: {name: [] for name in _CATEGORIES})
    #: ``(_key, stored value, label)`` per document to convert. The label travels
    #: with the write so a failure can name the record without a second read.
    writes: list[tuple[str, Any, str]] = field(default_factory=list)
    #: Documents the write could not reach — see :data:`_WRITE_FAILED`.
    write_failed: list[str] = field(default_factory=list)

    def count(self, category: str, row: str) -> None:
        """Count one document exactly, and itemise it up to the sample limit.

        Total and list move together on purpose: a capped list beside an exact
        counter is only readable while nothing can update one without the other.
        """
        self.totals[category] += 1
        if len(self.rows[category]) < _REPORT_SAMPLE_LIMIT:
            self.rows[category].append(row)


def _label(doc: dict[str, Any]) -> str:
    """Name a record the way an operator would look it up."""
    name = doc.get("name_de") or doc.get("brand") or ""
    tenant = doc.get("tenant_key") or ""
    scope = f"tenant={tenant}" if tenant else "base catalogue"
    return f"{doc.get('type', '')}/{name!r} [{scope}] key={doc.get('_key', '')}"


class RenameCecKeyMigration(Migration):
    version = "0051"
    name = "rename_cec_key"
    description = (
        "Move the stored substrate CEC from cec_meq_per_100g to cec_meq_per_100cm3, "
        "the key every reader has asked for since #1174 (#1468)."
    )
    reversible = False

    #: Projected, not whole documents: the decision needs two attributes and the
    #: three identity fields the report names a record by. ``HAS`` is evaluated on
    #: the server so a stored ``null`` stays distinguishable from an absent
    #: attribute — ``d.cec_meq_per_100g`` alone would read as ``null`` for both, and
    #: the two cases are different documents.
    #:
    #: No tenant filter, deliberately: see the module docstring.
    _SCAN_QUERY = f"""
    FOR d IN {col.SUBSTRATES}
      RETURN {{
        _key: d._key,
        type: d.type,
        name_de: d.name_de,
        brand: d.brand,
        tenant_key: d.tenant_key,
        has_old: HAS(d, @old),
        has_new: HAS(d, @new),
        old_value: d.@old,
        new_value: d.@new
      }}
    """

    def _plan(self, db: StandardDatabase) -> _Plan:
        """Classify every substrate document without writing.

        Pure, so ``dry_run`` reports the numbers the real run produces. A dry run
        that took its own path would describe a plan nobody executes.
        """
        plan = _Plan()
        if not db.has_collection(col.SUBSTRATES):
            return plan

        cursor = db.aql.execute(
            self._SCAN_QUERY,
            bind_vars={"old": OLD_KEY, "new": NEW_KEY},
            batch_size=_SCAN_BATCH_SIZE,
        )
        for doc in cursor:
            plan.scanned += 1
            has_old = bool(doc.get("has_old"))
            has_new = bool(doc.get("has_new"))
            label = _label(doc)

            if has_old and has_new:
                plan.count(
                    "both_keys_present",
                    f"{label}: {OLD_KEY}={doc.get('old_value')!r}, {NEW_KEY}={doc.get('new_value')!r} — left untouched",
                )
                continue
            if has_new:
                plan.count("already_correct", label)
                continue
            if not has_old:
                plan.count("no_cec_stored", label)
                continue

            value = doc.get("old_value")
            if value is None:
                plan.count("old_key_dropped_without_value", label)
            else:
                plan.count("renamed", f"{label}: {value!r}")
            plan.writes.append((str(doc["_key"]), value, label))

        return plan

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        plan = self._plan(db)
        written = 0 if dry_run else self._write(db, plan)

        logger.info(
            "rename_cec_key",
            scanned=plan.scanned,
            changed=written,
            dry_run=dry_run,
            write_failed_total=len(plan.write_failed),
            **{f"{category}_total": plan.totals[category] for category in _CATEGORIES},
        )

        payload: dict[str, Any] = {}
        for category in _CATEGORIES:
            payload[category] = list(plan.rows[category])
            payload[f"{category}_total"] = plan.totals[category]
        # Named, not counted: a document the write could not reach keeps the old key
        # and needs a human to look at it, and they cannot look at a row nobody names.
        payload[_WRITE_FAILED] = plan.write_failed[:_REPORT_SAMPLE_LIMIT]
        payload[f"{_WRITE_FAILED}_total"] = len(plan.write_failed)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=plan.scanned,
            # Successful writes, not planned ones: a report that counted intentions
            # would say the data moved while a document still holds the old key.
            changed=written,
            dry_run=dry_run,
            details=payload,
        )

    @staticmethod
    def _write(db: StandardDatabase, plan: _Plan) -> int:
        """Move the value and drop the old attribute, one document at a time.

        ``keep_none=False`` is what removes ``cec_meq_per_100g``: python-arango
        passes it as ArangoDB's ``keepNull``, and a patch attribute set to ``null``
        removes the attribute instead of storing a null. It is the whole mechanism
        of the rename, so the integration test measures it against a real server
        rather than against a double.

        The patch carries exactly two attributes, which is why a blanket
        ``keep_none=False`` is safe here: the only ``None`` it can drop besides the
        removal marker is a stored ``cec_meq_per_100g: null``, and for that
        document "value absent under the new name" is what the model reads as
        ``None`` anyway — the old name still goes away, which is the point.

        ``merge=False`` matches v0047/v0049: neither attribute is object-valued, and
        keeping the flag means a later field added here cannot inherit a
        server-default merge nobody chose.

        **No document can abort the run** (M-4, the formulation v0050 uses). The
        scan and the writes are separate round trips, so a mix a tenant deletes in
        between raises ``DocumentUpdateError`` here — and an exception out of ``up``
        is a *fatal startup*, the whole application down because one substrate went
        away. Each document is written on its own and a failure is recorded under
        ``write_failed`` instead; the record keeps the old key and is named for an
        operator, which is a problem about one row rather than about the install.

        Returns:
            The number of documents actually written.
        """
        if not plan.writes:
            return 0
        substrates = db.collection(col.SUBSTRATES)
        written = 0
        for key, value, label in plan.writes:
            try:
                substrates.update(
                    {"_key": key, NEW_KEY: value, OLD_KEY: None},
                    keep_none=False,
                    merge=False,
                )
            except ArangoError as exc:
                plan.write_failed.append(f"{label}: {type(exc).__name__}: {exc}")
                logger.warning("rename_cec_key_write_failed", key=key, error=str(exc))
                continue
            written += 1
        return written


#: Module-level instance the discovery loader binds (framework contract).
migration = RenameCecKeyMigration()
