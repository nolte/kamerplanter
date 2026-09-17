"""v0049 — re-apply the #1175 sourced substrate values to unmodified seed records (#1175).

Second instalment of the operation v0047 performs, for the four values #1175 sources.
``seed_substrates.py`` skips any record whose ``(type, name_de or brand)`` already
exists — it is a seeder, never an upsert — so an installation seeded before this
correction keeps the old numbers for its lifetime while the test suite certifies
the YAML as fixed. v0047 closed that gap for the eight values corrected under #1174
and #1332; it explicitly could not close it for these four, because they were not
on ``develop`` when it was written:

    "Also not in this migration: the sphagnum water-holding capacity. […] the
    sourced 28 vol-% value itself arrives with PR #1348 and is not on ``develop``
    yet. Only values already corrected on ``develop`` are migrated — a migration
    that wrote a number the seed file does not contain would make a fresh install
    and a migrated one disagree, which is the defect this exists to end."

They arrive with this branch, so they get their migration here. An applied
migration is immutable (M-7 checksum), so extending ``v0047._CORRECTIONS`` was
never an option even though the mechanism is identical.

**The same mechanism, deliberately imported rather than copied.** ``_Correction``,
``_ABSENT`` and ``_same`` come from v0047. ``_same`` in particular is subtle — it
checks ``bool`` before ``float`` because ``True == 1.0``, tolerates the float
round trip through YAML/Pydantic/ArangoDB, and keeps "absent" distinct from a
stored ``null`` — and it was settled against a live ``arangodb:3.12``. A second
copy of it would be a second thing to drift. The import is safe in the direction
that matters: v0047 is applied and therefore frozen by its checksum, so the
behaviour this module borrows cannot move under it. (Cross-version imports have
precedent: ``v0026`` imports ``v0010``'s migration object.)

**"Unmodified" is per field, not per record**, as in v0047: a record is eligible
for a given correction when the stored value of that one field still equals what
the seeder originally wrote. Three of the four corrections below are on the *same*
record, and they are still judged one by one — a tenant who hand-fixed the
impossible ``easily_available_water_percent`` still gets the other two.

**Only the base catalogue**: rows are filtered to ``tenant_key == ""`` (#1195). A
mix a tenant created for itself is not a seed record even when it carries the same
name, and a catalogue correction must not rewrite it. A record seeded before #1195
has no ``tenant_key`` at all and reads as ``""`` here, which is what it is.

**On the version number.** ``0049`` is the next free number *on this branch*.
``discovery.validate_sequence`` enforces both uniqueness and gapless numbering
from ``0001`` (M-1), and it is the second half that decides this: a module
numbered ``0050`` with no ``0049`` beside it fails ``load_migrations()`` outright
— ``MigrationDiscoveryError: Non-contiguous version numbering: expected 0049, got
0050`` — and that call is on the application's startup path, so the number cannot
be reserved ahead of a branch that has not landed. If the other open branch that
adds a migration lands first, this module and its ``version`` string are renamed
to ``0050`` after merging ``develop`` in, which is mechanical and has no data
implications while neither has been applied anywhere. v0047 was renumbered from
``0046`` for exactly this reason and describes the duplicate-version half of the
same collision.

Idempotent (M-3): a re-run finds every eligible record already carrying the new
value, so nothing matches the old one and ``changed == 0``.

Not reversible (M-6): the old values are wrong, not merely different. Sphagnum's
``air 25 + whc 80`` is 105 % of one pore space, and its
``easily_available_water_percent: 40`` claims a plant can extract more water than
the medium holds. Writing them back would be indistinguishable from a tenant
setting them on purpose, and there is no state worth restoring.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.versions.v0047_reapply_corrected_substrate_values import (
    _ABSENT,
    _Correction,
    _Plan,
    _same,
)

logger = structlog.get_logger(__name__)

#: The corrected values, each the literal before and after of one hunk in this
#: branch's diff of ``app/migrations/seed_data/substrates.yaml``. The provenance of
#: every ``new`` value is a citation in the record itself; the test holds each one
#: against the seed file so the table cannot drift away from what a fresh install
#: gets.
_CORRECTIONS: tuple[_Correction, ...] = (
    # ── #1175: the pH convention, applied to the one record that declares two ──
    # 6.8 matched neither figure LECHUZA publishes. Its EU 2019/1009 declaration
    # states "pH-Wert (H₂O): 8,2" and "pH-Wert (CaCl₂): 7,1"; #1332 left the value
    # alone because the catalogue did not say which convention ``ph_base`` uses.
    # This branch's seed header states it (water extract), which settles the record
    # as well as the field.
    _Correction(
        type="pon_mineral",
        name_de="Lechuza PON (Mineralsubstrat)",
        field_name="ph_base",
        old=6.8,
        new=8.2,
        issue="#1175",
    ),
    # ── #1175: the sphagnum air/water pair, sourced at the record's own density ──
    # 25 with water_holding 80 summed to 105 % of one pore space — the last
    # ``_KNOWN_OPEN`` entry in ``test_substrate_invariants.py``, unsourced until
    # now. Kämäräinen et al. (2018) measure loosely packed 40 mm fibres at ≈30 g/dm³
    # (this record's bulk density) with total porosity 97.4–97.8 % and ≈28 vol-%
    # water at pF 1; air capacity is their own definition, total pore volume minus
    # water at pF 1, so 97.6 − 28 ≈ 70.
    _Correction(
        type="sphagnum",
        name_de="Sphagnum-Moos (getrocknet)",
        field_name="air_porosity_percent",
        old=25.0,
        new=70.0,
        issue="#1175",
    ),
    # 80 was the other convention, not a typo: saturate-and-drain (Müller & Glatzel
    # 2021, 28.4 g/g at 0.03 g/cm³ = 85 vol-%). The field is defined at container
    # capacity (−10 hPa / pF 1), which is 28. ``water_retention: high`` stays — since
    # #1368 the enum is the only signal the watering modifier reads, and it is a
    # per-type statement (REQ-019), deliberately not derived from this number.
    _Correction(
        type="sphagnum",
        name_de="Sphagnum-Moos (getrocknet)",
        field_name="water_holding_capacity_percent",
        old=80.0,
        new=28.0,
        issue="#1175",
    ),
    # 40 is impossible beside a WHC of 28: a plant cannot extract more water than
    # the medium holds. Same sample, same figure: water between pF 1 and pF 2 is
    # 28 − 19 ≈ 9 vol-%.
    _Correction(
        type="sphagnum",
        name_de="Sphagnum-Moos (getrocknet)",
        field_name="easily_available_water_percent",
        old=40.0,
        new=9.0,
        issue="#1175",
    ),
)


class ReapplySubstrateSourceValuesMigration(Migration):
    version = "0049"
    name = "reapply_substrate_source_values"
    description = "Re-apply the #1175 sourced substrate catalogue values to unmodified seed records."
    reversible = False

    #: One statement returning whole base-catalogue records: the fields in scope
    #: differ per correction, and a projection built from ``_CORRECTIONS`` would
    #: have to be kept in step with it. The catalogue is 28 documents.
    #:
    #: ``s.tenant_key || ""`` treats a document seeded before #1195 — which has no
    #: such key — as base catalogue, which is what it is.
    _SCAN_QUERY = f"""
    FOR s IN {col.SUBSTRATES}
      FILTER (s.tenant_key || "") == ""
      RETURN s
    """

    def _plan(self, db: StandardDatabase) -> _Plan:
        """Return the plan without writing.

        Pure, so ``dry_run`` reports the numbers the real run would produce. A dry
        run that took its own path would describe a plan nobody executes.
        """
        plan = _Plan()
        if not db.has_collection(col.SUBSTRATES):
            return plan

        by_identity: dict[tuple[str, str], dict[str, Any]] = {}
        for doc in db.aql.execute(self._SCAN_QUERY):
            plan.scanned += 1
            identity = (str(doc.get("type", "")), str(doc.get("name_de") or doc.get("brand") or ""))
            # First one wins: a duplicated identity is not this migration's
            # business, and picking a different one per run would make it
            # non-deterministic.
            by_identity.setdefault(identity, doc)

        patches: dict[str, dict[str, Any]] = {}
        for corr in _CORRECTIONS:
            label = f"{corr.name_de} [{corr.field_name}]"
            doc = by_identity.get((corr.type, corr.name_de))
            if doc is None:
                plan.absent.append(label)
                continue

            stored = doc.get(corr.field_name, _ABSENT)
            if stored is _ABSENT and corr.absent_means_old:
                stored = corr.old

            if _same(stored, corr.new):
                # Checked before the old value, so a re-run is a no-op rather than
                # a report full of "locally modified" rows this migration wrote
                # itself (M-3).
                plan.already_current.append(label)
                continue
            if not _same(stored, corr.old):
                plan.locally_modified.append(f"{label}: stored={stored!r}, catalogue {corr.old!r}→{corr.new!r}")
                continue

            key = str(doc["_key"])
            # Three of the four corrections are on the sphagnum record, so this
            # accumulates into one patch — and each of them had to pass its own
            # eligibility check to get here.
            patch = patches.setdefault(key, {})
            patch[corr.field_name] = corr.new
            patch.update(corr.companions)
            plan.applied.append(f"{label} {corr.old!r}→{corr.new!r} ({corr.issue})")

        plan.writes = sorted(patches.items())
        return plan

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        plan = self._plan(db)

        if not dry_run and plan.writes:
            substrates = db.collection(col.SUBSTRATES)
            for key, patch in plan.writes:
                # Both keywords carry v0047's live findings against arangodb:3.12.
                # ``keep_none=True`` is python-arango's spelling (``keep_null``
                # raises ``TypeError``); ``merge=False`` stops the server merging
                # object-valued attributes instead of replacing them. Neither is
                # exercised by the four scalar corrections here, and both are kept
                # so this write behaves identically to the one it continues rather
                # than differing in a way the next correction would inherit.
                substrates.update({"_key": key, **patch}, keep_none=True, merge=False)

        logger.info(
            "reapply_substrate_source_values",
            scanned=plan.scanned,
            applied=len(plan.applied),
            documents=len(plan.writes),
            already_current=len(plan.already_current),
            locally_modified=len(plan.locally_modified),
            absent=len(plan.absent),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=plan.scanned,
            changed=0 if dry_run else len(plan.writes),
            dry_run=dry_run,
            details={
                "applied": plan.applied,
                "already_current": len(plan.already_current),
                # Named, not counted: a record whose value a tenant changed keeps
                # their value by decision, and the operator is the only one who can
                # tell "deliberate" from "seeded before the correction and edited
                # since". They cannot look at a record they cannot name.
                "locally_modified": plan.locally_modified,
                # A catalogue record that is not in the database at all — the
                # seeder will create it from the current YAML, so this is expected
                # on a partially seeded volume and not an error.
                "absent_from_catalogue": plan.absent,
            },
        )


#: Module-level instance the discovery loader binds (framework contract).
migration = ReapplySubstrateSourceValuesMigration()
