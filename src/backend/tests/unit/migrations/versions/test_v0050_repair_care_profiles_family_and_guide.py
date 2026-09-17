"""Tests for v0050_repair_care_profiles_family_and_guide (#1489 / #1481).

**What the fake may and may not decide.** The classification — repaired, user-edited,
already correct — is the migration's own and is exercised here against documents that
differ in exactly one field at a time. What the fake must *not* do is re-implement the
recomputation: the expected values come from ``CareReminderEngine`` itself, because a
test that hand-wrote "21 days for a Cactaceae" would certify its own copy of the map
and go green on the day the preset changes.

The fake cannot certify ArangoDB's update semantics or that the repository's
``_to_doc`` round-trips a profile; ``tests/integration`` covers the real server, and
the v0050 dry-run against the dev cluster is in the PR body.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from app.common.enums import CareStyleType, WateringMethod
from app.data_access.arango import collections as col
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.species import WateringGuide
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0050_repair_care_profiles_family_and_guide import (
    REQUIRED_COLLECTIONS,
    migration,
)

TENANT = "mein-garten"
PLANT = "plant-1"
PROFILE = "cp-1"
SPECIES_KEY = "5551"
CULTIVAR_KEY = "6661"
#: A botanical family ``_key`` as ArangoDB assigns it — numeric, and emphatically
#: not the name ``FAMILY_CARE_MAP`` is keyed by.
FAMILY_KEY = "7242"
FAMILY_NAME = "Cactaceae"


# ── the fake ──────────────────────────────────────────────────────────────────


class _FakeCollection:
    def __init__(self, name: str, documents: list[dict[str, Any]], writes: list[tuple[str, str, Any]]) -> None:
        self._name = name
        self._documents = documents
        self._writes = writes

    def update(self, data: dict[str, Any], return_new: bool = False, keep_none: bool = True):
        key = data["_key"]
        for document in self._documents:
            if document.get("_key") == key:
                document.update(data)
                self._writes.append(("update", self._name, dict(data)))
                return {"new": dict(document)} if return_new else {"_key": key}
        raise AssertionError(f"no document {key!r} in {self._name}")


class _FakeAql:
    """Interprets exactly the five reads the migration issues."""

    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.queries: list[str] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        stripped = query.strip()
        self.queries.append(stripped)

        if stripped.startswith("FOR profile IN"):
            assert col.CARE_PROFILES in stripped
            assert "auto_generated == true" in stripped, (
                "the population must narrow to generated profiles; a hand-made one is nobody's to recompute"
            )
            return iter([dict(p) for p in self._collections.get(col.CARE_PROFILES, []) if p.get("auto_generated")])

        keys = set(bind_vars.get("keys", []))
        if stripped.startswith("FOR plant IN"):
            return iter(
                [
                    {
                        "key": p["_key"],
                        "species": p.get("species_key"),
                        "cultivar": p.get("cultivar_key"),
                        "tenant": p.get("tenant_key"),
                        "removed_on": p.get("removed_on"),
                    }
                    for p in self._collections.get(col.PLANT_INSTANCES, [])
                    if p["_key"] in keys
                ]
            )
        if stripped.startswith("FOR s IN"):
            return iter([dict(s) for s in self._collections.get(col.SPECIES, []) if s["_key"] in keys])
        if stripped.startswith("FOR c IN"):
            return iter([dict(c) for c in self._collections.get(col.CULTIVARS, []) if c["_key"] in keys])
        if stripped.startswith("FOR f IN"):
            return iter(
                [
                    {"key": f["_key"], "name": f.get("name")}
                    for f in self._collections.get(col.BOTANICAL_FAMILIES, [])
                    if f["_key"] in keys
                ]
            )
        raise AssertionError(f"unexpected query: {stripped!r}")


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.collections = collections
        self.aql = _FakeAql(collections)
        self.writes: list[tuple[str, str, Any]] = []
        self._handles: dict[str, _FakeCollection] = {}

    def has_collection(self, name: str) -> bool:
        return name in self.collections

    def collection(self, name: str) -> _FakeCollection:
        if name not in self._handles:
            self._handles[name] = _FakeCollection(name, self.collections.setdefault(name, []), self.writes)
        return self._handles[name]


# ── document builders ─────────────────────────────────────────────────────────

_ENGINE = CareReminderEngine()

#: A four-day guide, so a repaired Cactaceae is distinguishable from BOTH the
#: 7-day tropical fallback it holds and the 21-day family preset.
_GUIDE = {
    "interval_days": 4,
    "watering_method": WateringMethod.BOTTOM_WATER.value,
    "water_quality_hint": "Rainwater only",
    "practical_tip": "Keep it dry in winter",
}


def _tropical_document(**overrides: Any) -> dict[str, Any]:
    """Exactly what the broken bootstrap wrote: the tier-3 fallback, as a document."""
    document = _ENGINE.auto_generate_profile(plant_key=PLANT).model_dump(mode="json", by_alias=True)
    document["_key"] = PROFILE
    document["created_at"] = "2026-08-01T00:00:00+00:00"
    document.update(overrides)
    return document


def _plant(**overrides: Any) -> dict[str, Any]:
    document = {
        "_key": PLANT,
        "tenant_key": TENANT,
        "instance_id": "P-1",
        "species_key": SPECIES_KEY,
        "cultivar_key": None,
        "removed_on": None,
    }
    document.update(overrides)
    return document


def _species(**overrides: Any) -> dict[str, Any]:
    document = {
        "_key": SPECIES_KEY,
        "scientific_name": "Echinocactus grusonii",
        "family_key": FAMILY_KEY,
        "watering_guide": None,
    }
    document.update(overrides)
    return document


def _db(
    profiles: list[dict[str, Any]] | None = None,
    plants: list[dict[str, Any]] | None = None,
    species: list[dict[str, Any]] | None = None,
    cultivars: list[dict[str, Any]] | None = None,
    families: list[dict[str, Any]] | None = None,
) -> _FakeDb:
    return _FakeDb(
        {
            col.CARE_PROFILES: profiles if profiles is not None else [_tropical_document()],
            col.PLANT_INSTANCES: plants if plants is not None else [_plant()],
            col.SPECIES: species if species is not None else [_species()],
            col.CULTIVARS: cultivars if cultivars is not None else [],
            col.BOTANICAL_FAMILIES: families if families is not None else [{"_key": FAMILY_KEY, "name": FAMILY_NAME}],
        }
    )


def _stored(db: _FakeDb) -> CareProfile:
    return CareProfile(**db.collections[col.CARE_PROFILES][0])


# ── the repair ────────────────────────────────────────────────────────────────


class TestTheRepair:
    def test_a_tropical_profile_of_a_cactaceae_is_recomputed(self) -> None:
        db = _db()
        expected = _ENGINE.auto_generate_profile(botanical_family=FAMILY_NAME, plant_key=PLANT)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 1
        assert _stored(db).care_style == CareStyleType.CACTUS == expected.care_style
        assert _stored(db).watering_interval_days == expected.watering_interval_days

    def test_the_species_watering_guide_is_applied_too(self) -> None:
        """#1481's half of the repair: tier 1 never reached any stored profile."""
        db = _db(species=[_species(watering_guide=_GUIDE)])
        guide = WateringGuide(**{**_GUIDE, "watering_method": WateringMethod.BOTTOM_WATER})
        expected = _ENGINE.auto_generate_profile(botanical_family=FAMILY_NAME, plant_key=PLANT, watering_guide=guide)

        migration.up(db)  # type: ignore[arg-type]

        assert _stored(db).watering_interval_days == expected.watering_interval_days == 4
        assert _stored(db).notes == expected.notes

    def test_a_cultivar_override_wins(self) -> None:
        db = _db(
            plants=[_plant(cultivar_key=CULTIVAR_KEY)],
            species=[_species(watering_guide=_GUIDE)],
            cultivars=[
                {
                    "_key": CULTIVAR_KEY,
                    "name": "Nana",
                    "species_key": SPECIES_KEY,
                    "watering_guide_override": {**_GUIDE, "interval_days": 9},
                }
            ],
        )

        migration.up(db)  # type: ignore[arg-type]

        assert _stored(db).watering_interval_days == 9

    def test_the_identity_and_the_season_state_survive_the_repair(self) -> None:
        """``_key``, ``plant_key``, ``created_at`` and the REQ-047 dormancy fields are
        the stored document's; the state machine owns the last three."""
        db = _db(profiles=[_tropical_document(dormancy_care_mode=True, dormancy_watering="minimal")])

        migration.up(db)  # type: ignore[arg-type]

        document = db.collections[col.CARE_PROFILES][0]
        assert document["_key"] == PROFILE
        assert document["plant_key"] == PLANT
        assert CareProfile(**document).created_at == datetime(2026, 8, 1, tzinfo=UTC)
        assert document["dormancy_care_mode"] is True
        assert document["dormancy_watering"] == "minimal"

    def test_the_learned_intervals_are_reset(self) -> None:
        """They were learned around the interval this run replaces — the same reason
        ``update_profile`` clears them on an explicit interval edit (#622)."""
        db = _db(profiles=[_tropical_document(watering_interval_learned=6, fertilizing_interval_learned=16)])

        migration.up(db)  # type: ignore[arg-type]

        assert _stored(db).watering_interval_learned is None
        assert _stored(db).fertilizing_interval_learned is None

    def test_a_learned_interval_does_not_make_a_profile_look_edited(self) -> None:
        """The control for the case above: a plant that is actually being watered is
        exactly the one that must not be skipped."""
        db = _db(profiles=[_tropical_document(watering_interval_learned=6)])

        assert migration.up(db).changed == 1  # type: ignore[arg-type]


class TestWhatIsNotTouched:
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("watering_interval_days", 5),
            ("care_style", CareStyleType.SUCCULENT.value),
            ("fertilizing_interval_days", 21),
            ("humidity_check_enabled", False),
            ("auto_create_watering_task", False),
            ("notes", "I water this one on Sundays"),
        ],
        ids=["interval", "style", "fertilizing", "humidity", "auto-task", "notes"],
    )
    def test_any_deviation_from_the_fallback_is_reported_not_overwritten(self, field: str, value: Any) -> None:
        """One changed field is enough. A user who moved one slider and left the rest
        keeps the whole profile: the moment it stops being exactly the value nobody
        chose, this migration cannot tell which part was deliberate."""
        db = _db(profiles=[_tropical_document(**{field: value})])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["skipped_user_edited_total"] == 1
        assert db.writes == []
        assert db.collections[col.CARE_PROFILES][0][field] == value

    def test_a_profile_that_is_not_auto_generated_is_outside_the_population(self) -> None:
        db = _db(profiles=[_tropical_document(auto_generated=False)])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 0
        assert db.writes == []

    def test_a_correctly_tropical_profile_is_reported_as_already_correct(self) -> None:
        """A plant whose family maps to TROPICAL anyway. Counting it as a change
        would make the report claim work it did not do."""
        db = _db(families=[{"_key": FAMILY_KEY, "name": "Araceae"}])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["already_correct_total"] == 1
        assert db.writes == []

    def test_a_removed_plant_is_skipped(self) -> None:
        db = _db(plants=[_plant(removed_on="2026-09-01")])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["plant_missing"][0]["reason"] == "plant_removed"

    def test_a_profile_whose_plant_is_gone_is_skipped(self) -> None:
        db = _db(plants=[])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["plant_missing"][0]["reason"] == "plant_document_missing"
        assert db.writes == []

    def test_an_unresolvable_numeric_family_leaves_the_profile_tropical(self) -> None:
        """The engine refuses a document key since #1489, so a dangling reference
        must be dropped before it gets there — a crash here would abort the boot."""
        db = _db(families=[])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["already_correct_total"] == 1


# ── framework obligations ─────────────────────────────────────────────────────


class TestTheFrameworkContract:
    def test_the_dry_run_writes_nothing_and_reports_the_same(self) -> None:
        wet, dry = _db(), _db()

        wet_report = migration.up(wet)  # type: ignore[arg-type]
        dry_report = migration.up(dry, dry_run=True)  # type: ignore[arg-type]

        assert dry.writes == []
        assert dry_report.dry_run is True
        assert (dry_report.scanned, dry_report.changed) == (wet_report.scanned, wet_report.changed)
        assert dry_report.details["repaired"] == wet_report.details["repaired"]

    def test_a_second_run_changes_nothing(self) -> None:
        """M-3. The repaired profile no longer equals the fallback, so the criterion
        that selected it no longer holds."""
        db = _db()

        assert migration.up(db).changed == 1  # type: ignore[arg-type]
        second = migration.up(db)  # type: ignore[arg-type]

        assert second.changed == 0
        assert second.details["skipped_user_edited_total"] == 1

    def test_an_empty_database_is_a_noop(self) -> None:
        db = _db(profiles=[])

        report = migration.up(db)  # type: ignore[arg-type]

        assert (report.scanned, report.changed) == (0, 0)
        assert report.details["repaired"] == []

    @pytest.mark.parametrize("missing", list(REQUIRED_COLLECTIONS))
    def test_a_missing_collection_leaves_the_migration_pending(self, missing: str) -> None:
        """M-1. Without the catalogues every profile would look correct and stay
        tropical, so the run must not be recorded as applied."""
        db = _db()
        db.collections.pop(missing)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.precondition_unmet is True
        assert report.details["missing_collections"] == [missing]
        assert db.writes == []

    def test_it_is_not_reversible(self) -> None:
        """M-6. The previous values are the defect, and restoring them would be
        indistinguishable from overwriting an edit made in between."""
        assert migration.reversible is False
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_db())  # type: ignore[arg-type]

    def test_the_totals_are_exact_while_the_lists_are_capped(self) -> None:
        """The cap is what keeps a 10 000-plant installation's report readable; the
        counters it is paired with must not be capped with it."""
        from app.migrations.versions import v0050_repair_care_profiles_family_and_guide as module

        limit = module._REPORT_SAMPLE_LIMIT
        profiles = []
        plants = []
        for index in range(limit + 7):
            plant_key = f"plant-{index}"
            profiles.append(_tropical_document(_key=f"cp-{index}", plant_key=plant_key))
            plants.append(_plant(_key=plant_key))
        db = _db(profiles=profiles, plants=plants)

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert report.details["repaired_total"] == limit + 7
        assert len(report.details["repaired"]) == limit


class TestTheResolutionIsNotCopied:
    """The identity check the v0048 tests pin for the population predicate, for the
    thing this migration must not re-implement: three places resolved the family and
    the one that mattered did not, so a fourth copy here would be the defect again."""

    def test_it_uses_the_shared_resolver(self) -> None:
        from app.domain.services import care_reminder_service
        from app.migrations.versions import v0050_repair_care_profiles_family_and_guide as module

        assert module.resolve_care_inputs is care_reminder_service.resolve_care_inputs
