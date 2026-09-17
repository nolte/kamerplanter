"""v0049 re-applies the #1175 sourced catalogue values to unmodified seed records.

Same shape as the v0047 suite, because it is the same operation on four more
values: what the migration does *not* touch is the point, so that is where most of
the tests are — a record a tenant edited keeps the tenant's value, a record that is
not base catalogue is out of scope entirely, and a second run writes nothing.

Two properties are checked against the real seed file rather than against literals
of my own, because the failure this migration exists to fix is precisely a
catalogue and a database drifting apart while a test certifies the catalogue: the
``new`` half of every correction must be what ``substrates.yaml`` says today, and
the ``old`` half must not.

One property is specific to this instalment: three of the four corrections land on
the *same* record, so there is a test that each is judged on its own field rather
than the record being taken or skipped as a whole.

The AQL double answers this migration's own query text and refuses one it does not
recognise. A double that returned ``[]`` for an unknown query would make every
assertion here pass vacuously — including the idempotence one, which is supposed
to observe an empty write list.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0049_reapply_substrate_source_values import (
    _CORRECTIONS,
    ReapplySubstrateSourceValuesMigration,
)
from app.migrations.yaml_loader import load_yaml

_SUBSTRATES = "substrates"
_SPHAGNUM = "Sphagnum-Moos (getrocknet)"
_PON = "Lechuza PON (Mineralsubstrat)"


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.updates: list[dict[str, Any]] = []

    def update(self, patch: dict[str, Any], keep_none: bool = True, merge: bool = True) -> None:
        """Model ArangoDB's PATCH, including the two defaults that bit in v0047.

        The parameter names are python-arango's (``keep_none``, not AQL's
        ``keepNull`` — ``keep_null`` raises ``TypeError`` on the real driver), so a
        migration calling the wrong one fails here too and not only live.
        ``merge=True`` is the *server's* default and merges object-valued
        attributes; none of this migration's four values is an object, and the
        double still models it so the next correction added here cannot inherit a
        double that is laxer than the server.
        """
        self.updates.append(patch)
        values = {k: v for k, v in patch.items() if k != "_key"}
        if not keep_none:
            values = {k: v for k, v in values.items() if v is not None}
        doc = self.docs[patch["_key"]]
        for name, value in values.items():
            if merge and isinstance(value, dict) and isinstance(doc.get(name), dict):
                doc[name] = {**doc[name], **value}
            else:
                doc[name] = value


class _Aql:
    def __init__(self, substrates: _Collection) -> None:
        self._substrates = substrates

    def execute(self, query: str, bind_vars: dict | None = None) -> list[dict[str, Any]]:  # noqa: ARG002
        normalised = re.sub(r"\s+", " ", query).strip()
        if _SUBSTRATES not in normalised:
            raise AssertionError(f"unexpected query, this double cannot answer it: {normalised!r}")
        if '(s.tenant_key || "") == ""' not in normalised:
            raise AssertionError(
                "the migration no longer restricts itself to the base catalogue. A mix a tenant "
                "created for itself is not a seed record, and a catalogue correction must not rewrite it."
            )
        return [{**doc, "_key": key} for key, doc in self._substrates.docs.items() if not (doc.get("tenant_key") or "")]


class _Db:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self._col = _Collection(docs)
        self.aql = _Aql(self._col)

    def has_collection(self, name: str) -> bool:
        return name == _SUBSTRATES

    def collection(self, name: str) -> _Collection:
        assert name == _SUBSTRATES
        return self._col


@pytest.fixture
def migration() -> ReapplySubstrateSourceValuesMigration:
    return ReapplySubstrateSourceValuesMigration()


def _corrections_for(name_de: str) -> list:
    return [c for c in _CORRECTIONS if c.name_de == name_de]


def _seeded_old(name_de: str, **overrides: Any) -> dict[str, Any]:
    """A base-catalogue document carrying the **old** value of every corrected field."""
    corrections = _corrections_for(name_de)
    assert corrections, f"no correction targets {name_de!r}"
    doc: dict[str, Any] = {"type": corrections[0].type, "name_de": name_de, "tenant_key": ""}
    for corr in corrections:
        doc[corr.field_name] = corr.old
    doc.update(overrides)
    return doc


class TestTheCorrectionTableMatchesTheCatalogue:
    """The table is derived from this branch's seed diff; keep it derived.

    Without these, the migration could drift into writing a value the seeder no
    longer writes — a fresh install and a migrated one would then disagree, which
    is the defect it exists to end, moved one layer along.
    """

    @staticmethod
    def _catalogue() -> dict[tuple[str, str], dict[str, Any]]:
        records = load_yaml("substrates.yaml")["substrates"]
        return {(r["type"], r.get("name_de") or r.get("brand") or ""): r for r in records}

    def test_every_new_value_is_what_the_seed_file_says_today(self) -> None:
        catalogue = self._catalogue()
        mismatched = []
        for corr in _CORRECTIONS:
            record = catalogue.get((corr.type, corr.name_de))
            assert record is not None, f"{corr.name_de} is not in substrates.yaml at all"
            stored = record.get(corr.field_name, "<absent>")
            if stored != corr.new:
                mismatched.append(f"{corr.name_de}.{corr.field_name}: yaml={stored!r}, migration new={corr.new!r}")
        assert not mismatched, mismatched

    def test_no_old_value_survives_in_the_seed_file(self) -> None:
        """The counterpart: an ``old`` still present means the YAML edit was reverted.

        The migration would then plan a write to a value a fresh install does not
        get, which is worse than doing nothing.
        """
        catalogue = self._catalogue()
        still_old = [
            f"{c.name_de}.{c.field_name} is still {c.old!r}"
            for c in _CORRECTIONS
            if catalogue[(c.type, c.name_de)].get(c.field_name) == c.old
        ]
        assert not still_old, still_old

    def test_no_correction_is_a_noop(self) -> None:
        assert all(c.old != c.new for c in _CORRECTIONS)

    def test_the_four_values_this_branch_sources_are_all_here(self) -> None:
        """Pins the scope: v0047 could not carry these, and nothing else may be added
        without saying so, because a migration's content is frozen once applied (M-7).
        """
        assert {(c.name_de, c.field_name) for c in _CORRECTIONS} == {
            (_PON, "ph_base"),
            (_SPHAGNUM, "air_porosity_percent"),
            (_SPHAGNUM, "water_holding_capacity_percent"),
            (_SPHAGNUM, "easily_available_water_percent"),
        }


class TestAnUnmodifiedRecordGetsTheCorrectedValue:
    def test_the_pon_ph_is_replaced(self, migration) -> None:
        db = _Db({"s1": _seeded_old(_PON)})

        report = migration.up(db)

        assert db.collection(_SUBSTRATES).docs["s1"]["ph_base"] == 8.2
        assert report.changed == 1
        assert any(_PON in line for line in report.details["applied"])

    def test_all_three_sphagnum_fields_move_in_one_write(self, migration) -> None:
        """They are one measurement on one sample and are meaningless apart.

        ``air 70`` beside the old ``whc 80`` would be 150 % of one pore space —
        worse than the 105 % this correction exists to end — so a partial write is
        the failure mode worth pinning.
        """
        db = _Db({"s1": _seeded_old(_SPHAGNUM)})

        report = migration.up(db)

        doc = db.collection(_SUBSTRATES).docs["s1"]
        assert doc["air_porosity_percent"] == 70.0
        assert doc["water_holding_capacity_percent"] == 28.0
        assert doc["easily_available_water_percent"] == 9.0
        assert len(db.collection(_SUBSTRATES).updates) == 1
        assert report.changed == 1

    def test_both_records_are_corrected_in_one_run(self, migration) -> None:
        db = _Db({"s1": _seeded_old(_PON), "s2": _seeded_old(_SPHAGNUM)})

        report = migration.up(db)

        assert report.changed == 2
        assert len(report.details["applied"]) == 4


class TestEligibilityIsDecidedPerFieldNotPerRecord:
    def test_a_tenant_fix_to_one_field_does_not_block_the_other_two(self, migration) -> None:
        """The impossible ``easily_available_water_percent: 40`` is the one a careful
        operator would already have noticed and changed by hand. Taking the record as
        a whole would punish exactly that operator by leaving the other two wrong.
        """
        db = _Db({"s1": _seeded_old(_SPHAGNUM, easily_available_water_percent=20.0)})

        report = migration.up(db)

        doc = db.collection(_SUBSTRATES).docs["s1"]
        assert doc["air_porosity_percent"] == 70.0
        assert doc["water_holding_capacity_percent"] == 28.0
        assert doc["easily_available_water_percent"] == 20.0, "the tenant's value must survive"
        assert any("easily_available_water_percent" in entry for entry in report.details["locally_modified"])

    def test_a_half_migrated_record_is_completed_not_reported(self, migration) -> None:
        """A run interrupted between the two records, or a value already fixed by
        hand to the sourced number, must not leave the rest behind.
        """
        db = _Db({"s1": _seeded_old(_SPHAGNUM, air_porosity_percent=70.0)})

        report = migration.up(db)

        doc = db.collection(_SUBSTRATES).docs["s1"]
        assert doc["water_holding_capacity_percent"] == 28.0
        assert report.details["already_current"] == 1
        assert not report.details["locally_modified"]


class TestAnEditedRecordIsLeftAloneAndNamed:
    def test_a_tenant_edited_value_is_not_overwritten(self, migration) -> None:
        db = _Db({"s1": _seeded_old(_PON, ph_base=5.5)})

        report = migration.up(db)

        assert db.collection(_SUBSTRATES).docs["s1"]["ph_base"] == 5.5
        assert db.collection(_SUBSTRATES).updates == []
        assert report.changed == 0

    def test_the_edited_record_is_reported_by_name_with_both_values(self, migration) -> None:
        """A count would not be actionable: the operator is the only one who can tell
        a deliberate local value from a record edited for an unrelated reason, and
        they cannot look at a record they cannot name.
        """
        db = _Db({"s1": _seeded_old(_PON, ph_base=5.5)})

        report = migration.up(db)

        (line,) = [entry for entry in report.details["locally_modified"] if _PON in entry]
        assert "5.5" in line
        assert "6.8" in line and "8.2" in line

    def test_a_field_deleted_from_a_record_is_treated_as_modified(self, migration) -> None:
        """All four fields have been written by the seeder since the catalogue was
        created, so a document without one says something happened to it — and a
        migration that filled the gap would be inventing, not correcting.
        """
        db = _Db({"s1": {"type": "pon_mineral", "name_de": _PON, "tenant_key": ""}})

        report = migration.up(db)

        assert "ph_base" not in db.collection(_SUBSTRATES).docs["s1"]
        assert report.changed == 0
        assert any(_PON in entry for entry in report.details["locally_modified"])

    def test_a_tenants_own_mix_is_out_of_scope_even_with_the_same_name(self, migration) -> None:
        """``tenant_key != ""`` is a mix its tenant owns (#1195), not a seed record.

        The value check alone would not save it: a tenant mix named the same and
        carrying the same number would match the old catalogue value exactly.
        """
        db = _Db({"own": _seeded_old(_SPHAGNUM, tenant_key="t_alice")})

        report = migration.up(db)

        assert db.collection(_SUBSTRATES).docs["own"]["water_holding_capacity_percent"] == 80.0
        assert report.changed == 0
        assert report.scanned == 0


class TestIdempotenceAndDryRun:
    def test_a_second_run_writes_nothing(self, migration) -> None:
        db = _Db({"s1": _seeded_old(_PON), "s2": _seeded_old(_SPHAGNUM)})

        first = migration.up(db)
        db.collection(_SUBSTRATES).updates.clear()
        second = migration.up(db)

        assert first.changed == 2
        assert second.changed == 0
        assert db.collection(_SUBSTRATES).updates == []
        assert not second.details["locally_modified"], second.details["locally_modified"]
        assert second.details["already_current"] == len(_CORRECTIONS)

    def test_dry_run_writes_nothing_and_reports_the_same_plan(self, migration) -> None:
        db = _Db({"s1": _seeded_old(_SPHAGNUM)})

        dry = migration.up(db, dry_run=True)

        assert dry.dry_run is True
        assert dry.changed == 0
        assert db.collection(_SUBSTRATES).updates == []
        assert db.collection(_SUBSTRATES).docs["s1"]["water_holding_capacity_percent"] == 80.0
        # The plan itself is the real one — a dry run that took its own path would
        # describe work nobody executes.
        assert len([line for line in dry.details["applied"] if _SPHAGNUM in line]) == 3

    def test_an_absent_catalogue_record_is_reported_not_created(self, migration) -> None:
        """The seeder creates missing records from the current YAML; this does not."""
        db = _Db({})

        report = migration.up(db)

        assert report.changed == 0
        assert len(report.details["absent_from_catalogue"]) == len(_CORRECTIONS)
        assert db.collection(_SUBSTRATES).docs == {}

    def test_a_database_without_the_collection_is_not_an_error(self, migration) -> None:
        class _Empty:
            aql = None

            def has_collection(self, name: str) -> bool:  # noqa: ARG002
                return False

        report = migration.up(_Empty())

        assert report.scanned == 0
        assert report.changed == 0


class TestTheResultingRecordIsPhysicallyPossible:
    """The migrated document has to satisfy the same invariants the seed file does.

    Checking the YAML alone would certify the catalogue while a migrated database
    kept a 105 % pore space — the drift this whole family of migrations is about.
    """

    def test_air_plus_water_no_longer_exceeds_one_pore_space(self, migration) -> None:
        db = _Db({"s1": _seeded_old(_SPHAGNUM)})
        before = db.collection(_SUBSTRATES).docs["s1"]
        assert before["air_porosity_percent"] + before["water_holding_capacity_percent"] > 100.0

        migration.up(db)

        doc = db.collection(_SUBSTRATES).docs["s1"]
        assert doc["air_porosity_percent"] + doc["water_holding_capacity_percent"] <= 100.0

    def test_available_water_no_longer_exceeds_the_water_held(self, migration) -> None:
        """The state to avoid is the *partial* one: the old 40 beside the new 28.

        A plant cannot extract more water than the medium holds, and a migration
        that moved the capacity without the available fraction would create that
        contradiction where the old record merely had two wrong numbers that happened
        to be ordered correctly (40 < 80).
        """
        db = _Db({"s1": _seeded_old(_SPHAGNUM)})

        migration.up(db)

        doc = db.collection(_SUBSTRATES).docs["s1"]
        assert doc["easily_available_water_percent"] <= doc["water_holding_capacity_percent"]


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-q"])
