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
        #: The key sets the per-batch document read was asked for, in order.
        self.batches: list[list[str]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        stripped = query.strip()
        self.queries.append(stripped)

        if stripped.startswith("FOR profile IN"):
            assert col.CARE_PROFILES in stripped
            profiles = self._collections.get(col.CARE_PROFILES, [])
            if stripped.endswith("RETURN profile._key"):
                # The population read: keys only, narrowed to generated profiles.
                assert "auto_generated == true" in stripped, (
                    "the population must narrow to generated profiles; a hand-made one is nobody's to recompute"
                )
                return iter([p["_key"] for p in profiles if p.get("auto_generated")])
            # The per-batch document read.
            batch = set(bind_vars["keys"])
            self.batches.append(sorted(batch))
            return iter([dict(p) for p in profiles if p["_key"] in batch])

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

    def test_a_second_run_reports_the_repaired_row_as_already_correct(self) -> None:
        """M-3, and the review finding SCR-002 in one case.

        The repaired profile no longer equals the broken output, so a run that asks
        "does this still look untouched?" **before** "is this already what it should
        be?" files every row it repaired under ``skipped_user_edited`` — and an
        operator reading a second run would see an installation of hand-edited
        profiles that nobody edited. Both orders write nothing the second time; only
        one of them says so truthfully.
        """
        db = _db()

        assert migration.up(db).changed == 1  # type: ignore[arg-type]
        second = migration.up(db)  # type: ignore[arg-type]

        assert second.changed == 0
        assert second.details["already_correct_total"] == 1
        assert second.details["skipped_user_edited_total"] == 0, (
            "a row this migration repaired itself is not a user edit — that was the classification "
            "the reversed comparison order produced (SCR-002)"
        )
        assert db.writes[len(db.writes) :] == []

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


# ── the review findings ───────────────────────────────────────────────────────


class TestTheFrozenBrokenOutput:
    """SCR-003. The population is historical, so the value that recognises it must
    be historical too — not whatever the current engine happens to return."""

    def test_the_literal_still_matches_todays_engine(self) -> None:
        """The tripwire, and it is deliberately **not** self-updating.

        When this goes red, ``CARE_STYLE_PRESETS[TROPICAL]`` (or a ``CareProfile``
        default) has moved. That is the moment to decide whether the remaining
        damaged population is still worth repairing — not the moment to paste the
        new values in. Had the migration kept computing the old output from the live
        engine, the same change would have made every damaged profile look
        user-edited and this migration would have repaired nothing, silently.
        """
        from app.migrations.versions import v0050_repair_care_profiles_family_and_guide as module

        live = module._comparable(_ENGINE.auto_generate_profile(plant_key=PLANT))

        assert live == module._BROKEN_BOOTSTRAP_OUTPUT, (
            "the frozen tier-3 output no longer matches the engine's. The presets changed: decide "
            "whether profiles still holding the 2026-08 values are to be repaired, then update the "
            "literal deliberately — do not sync it to make this pass."
        )

    def test_a_preset_change_does_not_make_the_migration_inert(self, monkeypatch) -> None:
        """The property the literal buys, measured rather than argued.

        The engine's TROPICAL preset is moved under the migration's feet. A run that
        derived the broken output from the live engine would now see stored != output
        and skip the row as user-edited; against the literal the repair still happens.
        """
        from app.domain.engines import care_reminder_engine as engine_module

        # The stored document is built FIRST, from the historical preset — it is the
        # 2026-08 row this migration exists for. Building it after the change would
        # have been the test writing the future into the past.
        db = _db()
        moved = {**engine_module.CARE_STYLE_PRESETS[CareStyleType.TROPICAL], "watering_interval_days": 6}
        monkeypatch.setitem(engine_module.CARE_STYLE_PRESETS, CareStyleType.TROPICAL, moved)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 1, "the damaged row is still recognised after a preset change"
        assert report.details["skipped_user_edited_total"] == 0


class TestAnUnreadableDocumentDoesNotAbortTheRun:
    """SCR-004. ``up()`` raising is a fatal startup (M-4, `framework/runner.py`), so
    one legacy document must not cost an installation its boot."""

    def test_a_profile_that_violates_the_model_is_reported(self) -> None:
        db = _db(profiles=[_tropical_document(watering_interval_days=999)])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["unreadable_total"] == 1
        assert report.details["unreadable"][0]["reason"] == "profile_document_unreadable"
        assert db.writes == []

    def test_an_unreadable_species_is_reported_not_silently_tropical(self) -> None:
        """Without the species the recomputation equals the stored fallback, so the
        row would otherwise be filed as ``already_correct`` — "we could not read it"
        reported as "it is fine"."""
        db = _db(species=[_species(watering_guide={"interval_days": 999})])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["unreadable_total"] == 1
        assert report.details["unreadable"][0]["reason"] == "species_unreadable"
        assert report.details["already_correct_total"] == 0
        assert db.writes == []

    def test_an_unreadable_cultivar_is_reported(self) -> None:
        db = _db(
            plants=[_plant(cultivar_key=CULTIVAR_KEY)],
            cultivars=[
                {
                    "_key": CULTIVAR_KEY,
                    "name": "Nana",
                    "species_key": SPECIES_KEY,
                    # Out of the `WateringGuide.interval_days` bound (1..90) — the
                    # shape a document stored before a constraint tightened has.
                    "watering_guide_override": {"interval_days": 999},
                }
            ],
        )

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["unreadable_total"] == 1
        assert report.details["unreadable"][0]["reason"] == "cultivar_unreadable"

    def test_a_readable_neighbour_in_the_same_batch_is_still_repaired(self) -> None:
        """The control: skipping the bad row must not skip the batch."""
        db = _db(
            profiles=[
                _tropical_document(_key="cp-bad", plant_key="plant-bad", watering_interval_days=999),
                _tropical_document(_key="cp-good", plant_key="plant-good"),
            ],
            plants=[_plant(_key="plant-bad"), _plant(_key="plant-good")],
        )

        report = migration.up(db)  # type: ignore[arg-type]

        assert (report.details["unreadable_total"], report.details["repaired_total"]) == (1, 1)


class TestTheFamilyReporting:
    """SCR-010."""

    def test_a_dangling_family_key_is_reported(self) -> None:
        db = _db(families=[])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["family_unresolved_total"] == 1
        assert report.details["family_unresolved"][0]["family_key"] == FAMILY_KEY
        assert report.details["already_correct_total"] == 1, (
            "the verdict stands beside the observation: TROPICAL is all an unresolvable family can give"
        )

    def test_a_resolved_family_is_not_reported_as_unresolved(self) -> None:
        report = migration.up(_db())  # type: ignore[arg-type]

        assert report.details["family_unresolved_total"] == 0

    def test_a_nameless_family_document_does_not_travel_as_an_empty_name(self) -> None:
        """An empty ``name`` matches no map entry either — but it would be reported
        as a resolved family, and the engine would be handed ``""``."""
        db = _db(families=[{"_key": FAMILY_KEY, "name": ""}])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["family_unresolved_total"] == 1
        assert report.details["already_correct"][0]["family_name"] is None


class TestTheBatching:
    """SCR-013: the run is batched, and the batching is observable."""

    def test_the_population_is_fetched_in_batches(self) -> None:
        from app.migrations.versions import v0050_repair_care_profiles_family_and_guide as module

        size = module._BATCH_SIZE
        profiles, plants = [], []
        for index in range(size + 3):
            plant_key = f"plant-{index}"
            profiles.append(_tropical_document(_key=f"cp-{index}", plant_key=plant_key))
            plants.append(_plant(_key=plant_key))
        db = _db(profiles=profiles, plants=plants)

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert report.scanned == size + 3
        assert [len(batch) for batch in db.aql.batches] == [size, 3]


class TestEachMissingPieceOnItsOwn:
    """SCR-008. The default fixture coupled three absences into one case: a plant
    whose species document was missing was also a plant whose family was missing and
    whose profile therefore could not be recomputed, so a single assertion stood for
    three different data states. Each is now its own case, and each says what the
    migration does **not** write."""

    def test_a_species_key_naming_no_document(self) -> None:
        db = _db(species=[])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["already_correct_total"] == 1, "nothing to resolve, so TROPICAL stands"
        assert report.details["family_unresolved_total"] == 0, "the species is gone, not its family"
        assert db.writes == []

    def test_a_plant_with_no_species_key_at_all(self) -> None:
        db = _db(plants=[_plant(species_key=None)])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["already_correct_total"] == 1
        assert db.writes == []

    def test_a_cultivar_key_naming_no_document(self) -> None:
        """The species still resolves, so this is the one of the three that is still
        repaired — which is exactly what coupling them hid."""
        db = _db(plants=[_plant(cultivar_key="no-such-cultivar")])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["repaired_total"] == 1
        assert _stored(db).care_style == CareStyleType.CACTUS

    def test_a_species_whose_family_key_is_empty(self) -> None:
        db = _db(species=[_species(family_key=None)])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["already_correct_total"] == 1
        assert report.details["family_unresolved_total"] == 0, "no family was named, so none is unresolved"
        assert db.writes == []
