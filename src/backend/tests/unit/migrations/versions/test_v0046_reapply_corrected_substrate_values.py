"""v0046 re-applies corrected catalogue values to unmodified seed records (#1368).

The whole point of the migration is what it does *not* touch, so that is where the
tests are: a record a tenant edited keeps the tenant's value, a record that is not
base catalogue is out of scope entirely, and a second run writes nothing.

Two properties are checked against the real seed file rather than against literals
of my own, because the failure this migration exists to fix is precisely a
catalogue and a database drifting apart while a test certifies the catalogue: the
``new`` half of every correction must be what ``substrates.yaml`` says today, and
the ``old`` half must not.

The AQL double answers this migration's own query text and refuses one it does not
recognise. A double that returned ``[]`` for an unknown query would make every
assertion here pass vacuously — including the idempotence one, which is supposed
to observe an empty write list.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0046_reapply_corrected_substrate_values import (
    _ABSENT,
    _CORRECTIONS,
    ReapplyCorrectedSubstrateValuesMigration,
    _same,
)
from app.migrations.yaml_loader import load_yaml

_SUBSTRATES = "substrates"


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.updates: list[dict[str, Any]] = []

    def update(self, patch: dict[str, Any], keep_none: bool = True, merge: bool = True) -> None:
        """Model ArangoDB's PATCH, including the two defaults that bit.

        The parameter names are python-arango's (``keep_none``, not AQL's
        ``keepNull`` — ``keep_null`` raises ``TypeError`` on the real driver), so
        a migration calling the wrong one fails here too and not only live.

        ``merge=True`` is the *server's* default and it merges object-valued
        attributes: patching ``composition`` with the rescaled vector would leave
        the removed ``kalk: 0.05`` behind, the vector would sum to 1.05, and the
        next run would report the record as locally modified. A plain
        ``dict.update`` here — which replaces the nested dict — hid exactly that,
        and a live arangodb:3.12 run found it. This double now certifies what the
        server does rather than what Python does.
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
def migration() -> ReapplyCorrectedSubstrateValuesMigration:
    return ReapplyCorrectedSubstrateValuesMigration()


def _corr(name_de: str):
    return next(c for c in _CORRECTIONS if c.name_de == name_de)


def _seeded(name_de: str, *, field_value: Any, **extra: Any) -> dict[str, Any]:
    """A base-catalogue document carrying ``field_value`` in the corrected field."""
    corr = _corr(name_de)
    return {"type": corr.type, "name_de": name_de, "tenant_key": "", corr.field_name: field_value, **extra}


class TestValueComparison:
    """``_same`` decides who gets rewritten, so its edge cases are the migration's.

    Asserted directly because the early ``_ABSENT`` return in it is *provably
    redundant* — deleting it leaves every case-level test green, since a sentinel
    falls through the remaining branches to ``False`` anyway. A guard no test can
    falsify is a guard nobody can trust to still hold after the next edit, so the
    property it states is pinned here rather than left to coincidence.
    """

    def test_a_missing_field_equals_nothing_not_even_null(self) -> None:
        assert _same(_ABSENT, None) is False
        assert _same(_ABSENT, 100.0) is False
        assert _same(_ABSENT, False) is False
        assert _same(_ABSENT, {}) is False

    def test_null_and_a_number_are_not_the_same_answer(self) -> None:
        assert _same(None, None) is True
        assert _same(None, 0.0) is False
        assert _same(0.0, None) is False

    def test_a_boolean_is_not_compared_as_a_number(self) -> None:
        """``True == 1.0`` in Python, and ``is_amendment`` is one of the fields."""
        assert _same(True, 1.0) is False
        assert _same(1, True) is False
        assert _same(False, False) is True

    def test_floats_survive_the_yaml_json_round_trip(self) -> None:
        assert _same(0.05000000000000001, 0.05) is True
        assert _same(0.06, 0.05) is False

    def test_a_dict_needs_the_same_keys(self) -> None:
        assert _same({"torf": 0.7, "kalk": 0.05}, {"torf": 0.7}) is False
        assert _same({"torf": 0.7}, {"torf": 0.7}) is True


class TestTheCorrectionTableMatchesTheCatalogue:
    """The table is derived from the seed file's history; keep it derived.

    Without these two, the migration could drift into writing a value the seeder
    no longer writes — a fresh install and a migrated one would then disagree,
    which is the defect it exists to end, moved one layer along.
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
            if corr.field_name == "is_amendment":
                stored = record.get(corr.field_name, False)
            if stored != corr.new:
                mismatched.append(f"{corr.name_de}.{corr.field_name}: yaml={stored!r}, migration new={corr.new!r}")
            for companion, value in corr.companions.items():
                if record.get(companion, []) != value:
                    mismatched.append(
                        f"{corr.name_de}.{companion}: yaml={record.get(companion)!r}, migration={value!r}"
                    )
        assert not mismatched, mismatched

    def test_no_correction_is_a_noop(self) -> None:
        assert all(c.old != c.new for c in _CORRECTIONS)


class TestAnUnmodifiedRecordGetsTheCorrectedValue:
    def test_a_scalar_value_is_replaced(self, migration) -> None:
        db = _Db({"s1": _seeded("Steinwollmatte", field_value=40.0)})

        report = migration.up(db)

        assert db.collection(_SUBSTRATES).docs["s1"]["air_porosity_percent"] == 12.0
        assert report.changed == 1
        assert any("Steinwollmatte" in line for line in report.details["applied"])

    def test_a_correction_to_null_is_written_as_null(self, migration) -> None:
        """ "Not applicable" is a value here, and it has to survive the driver.

        ``air_porosity_percent: 100.0`` was a placeholder that every consumer read
        as a measurement — volume-weighted into mixes, rendered as "100.0 %".
        """
        db = _Db({"s1": _seeded("Hydrokultur (kein Substrat)", field_value=100.0)})

        migration.up(db)

        doc = db.collection(_SUBSTRATES).docs["s1"]
        assert "air_porosity_percent" in doc
        assert doc["air_porosity_percent"] is None

    def test_composition_and_additives_move_together(self, migration) -> None:
        """Neither half of that correction means anything alone.

        Lime left the normalised volume vector and arrived in ``additives`` in one
        edit; a record with the rescaled vector but no ``additives`` would have
        lost the information that the medium is limed.
        """
        corr = _corr("Plagron Promix")
        db = _Db({"s1": _seeded("Plagron Promix", field_value=dict(corr.old))})

        migration.up(db)

        doc = db.collection(_SUBSTRATES).docs["s1"]
        assert doc["composition"] == {"torf": 0.74, "perlit": 0.16, "fasern": 0.10}
        assert doc["additives"] == ["kalk"]

    def test_an_absent_field_that_never_existed_counts_as_the_old_state(self, migration) -> None:
        """``is_amendment`` was added by the correction itself.

        Before #1332 the field did not exist, and its absence meant exactly what
        ``False`` means — so a document without it is unmodified, not edited.
        """
        db = _Db({"s1": {"type": "peat", "name_de": "BioBizz Pre·Mix (Bodenverbesserer)", "tenant_key": ""}})

        migration.up(db)

        assert db.collection(_SUBSTRATES).docs["s1"]["is_amendment"] is True


class TestAnEditedRecordIsLeftAloneAndNamed:
    def test_a_tenant_edited_value_is_not_overwritten(self, migration) -> None:
        db = _Db({"s1": _seeded("Steinwollmatte", field_value=33.0)})

        report = migration.up(db)

        assert db.collection(_SUBSTRATES).docs["s1"]["air_porosity_percent"] == 33.0
        assert db.collection(_SUBSTRATES).updates == []
        assert report.changed == 0

    def test_the_edited_record_is_reported_by_name_with_both_values(self, migration) -> None:
        """A count would not be actionable.

        The operator is the only one who can tell a deliberate local value from a
        record that was seeded before the correction and edited for an unrelated
        reason, and they cannot look at a record they cannot name.
        """
        db = _Db({"s1": _seeded("Steinwollmatte", field_value=33.0)})

        report = migration.up(db)

        (line,) = [entry for entry in report.details["locally_modified"] if "Steinwollmatte" in entry]
        assert "33.0" in line
        assert "40.0" in line and "12.0" in line

    def test_a_field_deleted_from_a_record_is_treated_as_modified(self, migration) -> None:
        """An absent field is only "the old state" where it never existed.

        ``air_porosity_percent`` has been written by the seeder since the catalogue
        was created, so a document without it says something happened to it — and a
        migration that filled the gap would be inventing, not correcting.
        """
        db = _Db({"s1": {"type": "rockwool_slab", "name_de": "Steinwollmatte", "tenant_key": ""}})

        report = migration.up(db)

        assert "air_porosity_percent" not in db.collection(_SUBSTRATES).docs["s1"]
        assert report.changed == 0
        assert any("Steinwollmatte" in entry for entry in report.details["locally_modified"])

    def test_a_tenants_own_mix_is_out_of_scope_even_with_the_same_name(self, migration) -> None:
        """``tenant_key != ""`` is a mix its tenant owns (#1195), not a seed record.

        The value check alone would not save it: a tenant mix named the same and
        carrying the same number would match the old catalogue value exactly.
        """
        db = _Db(
            {
                "own": {
                    "type": "rockwool_slab",
                    "name_de": "Steinwollmatte",
                    "tenant_key": "t_alice",
                    "air_porosity_percent": 40.0,
                }
            }
        )

        report = migration.up(db)

        assert db.collection(_SUBSTRATES).docs["own"]["air_porosity_percent"] == 40.0
        assert report.changed == 0
        assert report.scanned == 0


class TestIdempotenceAndDryRun:
    def test_a_second_run_writes_nothing(self, migration) -> None:
        db = _Db(
            {
                "s1": _seeded("Steinwollmatte", field_value=40.0),
                "s2": _seeded("Hydrokultur (kein Substrat)", field_value=100.0),
                "s3": _seeded("Plagron Promix", field_value=dict(_corr("Plagron Promix").old)),
            }
        )

        first = migration.up(db)
        db.collection(_SUBSTRATES).updates.clear()
        second = migration.up(db)

        assert first.changed == 3
        assert second.changed == 0
        assert db.collection(_SUBSTRATES).updates == []
        assert not second.details["locally_modified"], second.details["locally_modified"]

    def test_the_null_correction_is_not_re_planned_on_a_second_run(self, migration) -> None:
        """A stored ``null`` and a missing key are different answers.

        If they were conflated, the already-corrected Hydrokultur record would read
        as "the field is gone" and be reported as locally modified forever.
        """
        db = _Db({"s1": _seeded("Hydrokultur (kein Substrat)", field_value=100.0)})

        migration.up(db)
        second = migration.up(db)

        assert second.changed == 0
        assert not second.details["locally_modified"]

    def test_dry_run_writes_nothing_and_reports_the_same_plan(self, migration) -> None:
        db = _Db({"s1": _seeded("Steinwollmatte", field_value=40.0)})

        dry = migration.up(db, dry_run=True)

        assert dry.dry_run is True
        assert dry.changed == 0
        assert db.collection(_SUBSTRATES).updates == []
        assert db.collection(_SUBSTRATES).docs["s1"]["air_porosity_percent"] == 40.0
        # The plan itself is the real one — a dry run that took its own path would
        # describe work nobody executes.
        assert any("Steinwollmatte" in line for line in dry.details["applied"])

    def test_an_absent_catalogue_record_is_reported_not_created(self, migration) -> None:
        """The seeder creates missing records from the current YAML; this does not."""
        db = _Db({})

        report = migration.up(db)

        assert report.changed == 0
        assert len(report.details["absent_from_catalogue"]) == len(_CORRECTIONS)
        assert db.collection(_SUBSTRATES).docs == {}


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-q"])
