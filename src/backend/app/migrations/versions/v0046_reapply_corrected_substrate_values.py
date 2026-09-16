"""v0046 — re-apply corrected substrate catalogue values to unmodified seed records (#1368).

``seed_substrates.py`` skips any record whose ``(type, name_de or brand)`` already
exists. It is a seeder, never an upsert — so every installation seeded before a
catalogue correction keeps the *old* numbers for its lifetime, while the test
suite certifies the YAML as fixed. #1174 and #1332 both corrected values that way,
and nothing carried the correction into a running database.

**Operator decision, 2026-09-12 (#1368): a migration, not an upsert.** The seeder
keeps its skip-if-exists behaviour. Corrected values are re-applied here, and only
to records that still carry the *old catalogue value* of the field in question.

**"Unmodified" is defined per field, not per record.** A record is eligible for a
given correction when the stored value of that one field equals the value the
seeder originally wrote. Then, and only then, the new catalogue value is written.
Anything else — an edited value, a value already corrected, a field that is not
there — is left untouched and reported. This is deliberately narrower than a
per-record check: a tenant who fixed one number by hand still gets the other
corrections, and a tenant who changed the number this migration is about keeps
their change. The alternative, a ``catalogue_version`` stamp per record, is what
the decision rejected: it needs machinery in the seeder, the model and the API to
tell "seeded, untouched" from "seeded, then edited", all to answer a question the
value itself already answers.

**Only the base catalogue.** Rows are filtered to ``tenant_key == ""`` — the
hybrid-catalogue marker for the seeded catalogue every tenant reads (#1195). A mix
a tenant created for itself is not a seed record even if it happens to be named
``Steinwollmatte``, and must not be rewritten by a catalogue correction. A record
seeded before #1195, whose document has no ``tenant_key`` at all, reads as ``""``
here — it predates the marker, so it is base catalogue by definition.

**The corrections, with their provenance.** Each pair below is the literal before
and after of one commit to ``app/migrations/seed_data/substrates.yaml``; see
:data:`_CORRECTIONS`.

**Deliberately NOT in this migration: the ``cec_meq_per_100g`` →
``cec_meq_per_100cm3`` rename (#1174).** All 28 seeded records carry it, and a
database seeded before #1174 stores the old key while every reader now asks for
the new one — so the CEC of the whole catalogue reads as ``None`` and
``calculate_mix_properties`` aggregates nothing. That is real, and it is a
different operation: no value changed, a *key* moved, and it moved for
tenant-owned mixes too, which this migration is explicitly scoped away from. It
needs its own decision about records this one must not touch, so it gets its own
issue rather than a silent ride here.

**Also not in this migration: the sphagnum water-holding capacity.** #1368's other
half is the engine fix (the ``water_retention`` enum now decides the watering
modifier); the sourced 28 vol-% value itself arrives with PR #1348 and is not on
``develop`` yet. Only values already corrected on ``develop`` are migrated — a
migration that wrote a number the seed file does not contain would make a fresh
install and a migrated one disagree, which is the defect this exists to end.

**On the version number.** ``0047`` was asked for, because an unmerged branch
(``fix/2026-09-16-task-photo-refs``) already carries a ``v0046``. It is not
available: ``discovery.validate_sequence`` enforces gapless numbering from
``0001`` (M-1), so a ``0047`` with no ``0046`` beside it makes *every* discovery —
application startup included — raise ``MigrationDiscoveryError: Non-contiguous
version numbering: expected 0046, got 0047``. Measured on this branch before
renumbering. Two open branches that each add a migration always collide this way;
whichever lands second renames its module and its ``version`` string, which is
mechanical and has no data implications while neither has been applied anywhere.

Idempotent (M-3): a re-run finds every eligible record already carrying the new
value, so nothing matches the old one and ``changed == 0``.

Not reversible (M-6): writing the old value back would be indistinguishable from a
tenant deliberately setting it, and the old values are wrong — ``air 40 + whc 80``
is 120 % of one pore space, and a 5 % lime fraction in a normalised volume vector
is two orders of magnitude off. There is no state worth restoring.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Sentinel for "this document has no such key", kept distinct from a stored
#: ``null``. ``Hydrokultur``'s corrected ``air_porosity_percent`` *is* ``None``,
#: so "absent" and "null" have to be two different answers or that record would
#: look already-migrated on a database that never had the field.
_ABSENT = object()


@dataclass(frozen=True)
class _Correction:
    """One field of one catalogue record, with the values it moved between."""

    #: Identity, as ``seed_substrates._identity`` computes it.
    type: str
    name_de: str
    #: The single field whose stored value decides eligibility *and* is rewritten.
    field_name: str
    #: What the seeder originally wrote. Only a record still carrying this is touched.
    old: Any
    #: What the current catalogue says.
    new: Any
    #: Provenance: the commit that changed the seed file.
    issue: str
    #: Fields written together with :attr:`field_name` when it matches. Used where
    #: one correction moved data between two fields and neither half is meaningful
    #: alone: the additives left ``composition`` and arrived in ``additives`` in the
    #: same edit, so the composition vector is the fingerprint for both.
    companions: dict[str, Any] = field(default_factory=dict)
    #: ``True`` where a missing key in the stored document means the old value.
    #: ``is_amendment`` did not exist before #1332, and its absence meant exactly
    #: what ``False`` means. For every other correction below the field has always
    #: been written by the seeder, so an absent key is a local modification, not
    #: the old state.
    absent_means_old: bool = False


#: The corrected values, each derived from the diff of the named commit on
#: ``app/migrations/seed_data/substrates.yaml``.
_CORRECTIONS: tuple[_Correction, ...] = (
    # ── #1174 (07403c500): air porosity at container capacity ──────────────
    # 40.0 was dry *total* porosity carried into a container-capacity field. With
    # the record's water_holding_capacity_percent 80 it summed to 120 % of one
    # pore space. At container capacity a rockwool slab holds ~80 % water and
    # 10–15 % air.
    _Correction(
        type="rockwool_slab",
        name_de="Steinwollmatte",
        field_name="air_porosity_percent",
        old=40.0,
        new=12.0,
        issue="#1174",
    ),
    # Same defect: 35.0 with water_holding 85 summed to 120 %. A propagation plug
    # is denser and holds more water than a slab, so it takes the low end of the
    # 10–15 % band.
    _Correction(
        type="rockwool_plug",
        name_de="Steinwollwürfel (Anzucht)",
        field_name="air_porosity_percent",
        old=35.0,
        new=10.0,
        issue="#1174",
    ),
    # ── #1332 (961e5cf29): sourced values and the additive separation ──────
    # 0.0 contradicted the 5 % controlled-release fertiliser the same record
    # lists. LECHUZA's EU 2019/1009 declaration publishes "Elektrische
    # Leitfähigkeit (EC): 5 mS/m" = 0.05 mS/cm, so the zero was the wrong half.
    # ``ec_base_ms`` is subtracted as EC-net in ``calculate_mixing_protocol``, so
    # a stale 0.0 doses a plant as though the substrate contributed nothing.
    _Correction(
        type="pon_mineral",
        name_de="Lechuza PON (Mineralsubstrat)",
        field_name="ec_base_ms",
        old=0.0,
        new=0.05,
        issue="#1332",
    ),
    # 100.0 was "not applicable" written as a number, and no consumer could tell
    # it from a measurement: it was volume-weighted into every mix containing the
    # entry and rendered as "100.0 %". A nutrient solution has no pore space.
    _Correction(
        type="hydro_solution",
        name_de="Hydrokultur (kein Substrat)",
        field_name="air_porosity_percent",
        old=100.0,
        new=None,
        issue="#1332",
    ),
    # Lime was a bulk fraction — five percent by volume, where lime goes in at
    # single-digit kg/m³. It moved to ``additives`` (named, unquantified) and the
    # remaining components were rescaled over 0.95, preserving their ratios.
    _Correction(
        type="soil",
        name_de="Plagron Promix",
        field_name="composition",
        old={"torf": 0.70, "perlit": 0.15, "fasern": 0.10, "kalk": 0.05},
        new={"torf": 0.74, "perlit": 0.16, "fasern": 0.10},
        companions={"additives": ["kalk"]},
        issue="#1332",
    ),
    # Ten percent lime — which contradicts the record's own ph_base 6.2 — plus
    # trace elements, which are ppm by definition. Both moved to ``additives``;
    # peat and perlite were rescaled over 0.85 with their 0.55 : 0.30 ratio intact.
    _Correction(
        type="soil",
        name_de="BioBizz Light·Mix",
        field_name="composition",
        old={"torf": 0.55, "perlit": 0.30, "kalk": 0.10, "spurenelemente": 0.05},
        new={"torf": 0.65, "perlit": 0.35},
        companions={"additives": ["kalk", "spurenelemente"]},
        issue="#1332",
    ),
    # Same correction as Light·Mix; ``pre_mix`` stays a bulk component because it
    # is a fifteen-percent share of a real product, not a kg/m³ amendment.
    _Correction(
        type="soil",
        name_de="BioBizz All·Mix",
        field_name="composition",
        old={"torf": 0.40, "wurmhumus": 0.20, "perlit": 0.20, "pre_mix": 0.15, "kalk": 0.05},
        new={"torf": 0.42, "wurmhumus": 0.21, "perlit": 0.21, "pre_mix": 0.16},
        companions={"additives": ["kalk"]},
        issue="#1332",
    ),
    # A soil conditioner, not a medium — it was selectable as a plant's growing
    # medium. The flag gates selection; the field did not exist before #1332, so
    # its absence is the old state rather than a local edit.
    _Correction(
        type="peat",
        name_de="BioBizz Pre·Mix (Bodenverbesserer)",
        field_name="is_amendment",
        old=False,
        new=True,
        issue="#1332",
        absent_means_old=True,
    ),
)


def _same(stored: Any, expected: Any) -> bool:
    """Return ``True`` when a stored value equals a catalogue value.

    Floats are compared with a tolerance because they made the round trip through
    YAML, Pydantic and ArangoDB's JSON; ``0.05`` is not guaranteed to come back
    bit-identical, and an exact ``==`` would silently classify an unmodified
    record as locally modified — the failure direction that leaves the defect in
    place while reporting success.

    ``bool`` is checked before ``float`` on purpose: ``True == 1.0`` in Python, so
    a numeric comparison would make ``is_amendment`` answer nonsense.
    """
    if stored is _ABSENT:
        return False
    if expected is None or stored is None:
        return expected is None and stored is None
    if isinstance(expected, bool) or isinstance(stored, bool):
        return isinstance(stored, bool) and stored is expected
    if isinstance(expected, int | float) and isinstance(stored, int | float):
        return math.isclose(float(stored), float(expected), rel_tol=0.0, abs_tol=1e-9)
    if isinstance(expected, dict):
        if not isinstance(stored, dict) or set(stored) != set(expected):
            return False
        return all(_same(stored[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        if not isinstance(stored, list) or len(stored) != len(expected):
            return False
        return all(_same(s, e) for s, e in zip(stored, expected, strict=True))
    return bool(stored == expected)


@dataclass
class _Plan:
    """What :meth:`up` would do, computed without writing."""

    writes: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    already_current: list[str] = field(default_factory=list)
    locally_modified: list[str] = field(default_factory=list)
    absent: list[str] = field(default_factory=list)
    scanned: int = 0


class ReapplyCorrectedSubstrateValuesMigration(Migration):
    version = "0046"
    name = "reapply_corrected_substrate_values"
    description = "Re-apply corrected substrate catalogue values to unmodified seed records (#1368)."
    reversible = False

    #: One statement, and it returns the *whole* base-catalogue record rather than
    #: a projection: the fields in scope differ per correction, and a projection
    #: built from ``_CORRECTIONS`` would have to be kept in step with it. The
    #: catalogue is 28 documents.
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
                # itself (M-3). The two catalogue values are never equal, so the
                # order costs nothing where it does not matter.
                plan.already_current.append(label)
                continue
            if not _same(stored, corr.old):
                plan.locally_modified.append(f"{label}: stored={stored!r}, catalogue {corr.old!r}→{corr.new!r}")
                continue

            key = str(doc["_key"])
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
                # Both keywords are load-bearing, and both were established
                # against a real arangodb:3.12 rather than reasoned about.
                #
                # ``keep_none=True``: the Hydrokultur correction writes ``None`` on
                # purpose, and a driver that dropped it would turn that record into
                # a silent no-op this migration re-plans on every boot. (The
                # keyword is python-arango's ``keep_none``, not AQL's ``keepNull``;
                # ``keep_null`` raises ``TypeError``.)
                #
                # ``merge=False``: an ArangoDB update **merges** object-valued
                # attributes by default, so patching ``composition`` with the
                # rescaled vector left the removed ``kalk: 0.05`` in place — the
                # vector then summed to 1.05, the additive was in the bulk vector
                # after all, and the next run reported the record as locally
                # modified. That is the exact defect this migration exists to fix,
                # reintroduced by the write. Observed live; the unit double models
                # both semantics so it cannot pass again by accident.
                substrates.update({"_key": key, **patch}, keep_none=True, merge=False)

        logger.info(
            "reapply_corrected_substrate_values",
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
migration = ReapplyCorrectedSubstrateValuesMigration()
