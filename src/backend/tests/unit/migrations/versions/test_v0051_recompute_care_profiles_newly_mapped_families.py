"""Tests for v0051_recompute_care_profiles_newly_mapped_families (#1505).

The fake database, the document builders and the constants are v0050's — imported
rather than copied, because the two migrations run the same machinery and a second
fake would be free to disagree with the first about what a stored profile looks
like. What differs is the *criterion*, and that is what this module exercises.

Nothing here hand-writes an expected interval: the expected values come from
``CareReminderEngine`` itself, so a test cannot certify its own copy of
``FAMILY_CARE_MAP``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.enums import CareStyleType, WateringMethod
from app.data_access.arango import collections as col
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.species import WateringGuide
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions import v0051_recompute_care_profiles_newly_mapped_families as v0051
from app.migrations.versions.v0051_recompute_care_profiles_newly_mapped_families import (
    _PRE_1505_TROPICAL_FALLBACK,
    migration,
    tropical_fallback_drift,
)
from tests.unit.migrations.versions.test_v0050_repair_care_profiles_family_and_guide import (
    FAMILY_KEY,
    PLANT,
    PROFILE,
    SPECIES_KEY,
    _db,
    _plant,
    _species,
    _stored,
    _tropical_document,
)

_ENGINE = CareReminderEngine()

#: A family the map did **not** know before #1505 — the whole population.
NEWLY_MAPPED_FAMILY = "Solanaceae"
#: A family the map knew all along; its profiles are already correct.
ALREADY_MAPPED_FAMILY = "Araceae"

_GUIDE = {
    "interval_days": 4,
    "watering_method": WateringMethod.BOTTOM_WATER.value,
    "water_quality_hint": "Rainwater only",
    "practical_tip": "Keep it dry in winter",
}


def _guide_model() -> WateringGuide:
    return WateringGuide(**{**_GUIDE, "watering_method": WateringMethod.BOTTOM_WATER})


def _family(name: str) -> list[dict[str, Any]]:
    return [{"_key": FAMILY_KEY, "name": name}]


def _guide_document() -> dict[str, Any]:
    """What v0050 left behind for a plant whose species carries a guide.

    Tropical style (its family was unmapped), watering fields from the guide — no
    longer identical to v0050's frozen literal, which is exactly why this migration
    cannot inherit v0050's criterion.
    """
    document = _ENGINE.auto_generate_profile(plant_key=PLANT, watering_guide=_guide_model()).model_dump(
        mode="json", by_alias=True
    )
    document["_key"] = PROFILE
    document["created_at"] = "2026-08-01T00:00:00+00:00"
    return document


class TestTheRecomputation:
    def test_a_tomato_stops_being_a_tropical_houseplant(self) -> None:
        """The #1505 headline, against the stored population."""
        db = _db(families=_family(NEWLY_MAPPED_FAMILY))
        expected = _ENGINE.auto_generate_profile(botanical_family=NEWLY_MAPPED_FAMILY, plant_key=PLANT)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 1
        assert _stored(db).care_style is CareStyleType.OUTDOOR_ANNUAL_VEG == expected.care_style
        assert _stored(db).watering_interval_days == expected.watering_interval_days == 3

    def test_a_profile_v0050_already_repaired_with_a_guide_is_recomputed_too(self) -> None:
        """The class v0050's frozen literal cannot see.

        Red under the inherited criterion: the stored document is not identical to
        ``_BROKEN_BOOTSTRAP_OUTPUT``, so it would have been filed as user-edited and
        the plant would keep the tropical style for good.
        """
        db = _db(
            profiles=[_guide_document()],
            species=[_species(watering_guide=_GUIDE)],
            families=_family(NEWLY_MAPPED_FAMILY),
        )

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 1, report.details["skipped_user_edited"]
        assert _stored(db).care_style is CareStyleType.OUTDOOR_ANNUAL_VEG
        # Tier 1 still wins over the family preset for the watering fields.
        assert _stored(db).watering_interval_days == 4

    def test_a_family_the_map_knew_all_along_is_already_correct(self) -> None:
        db = _db(families=_family(ALREADY_MAPPED_FAMILY))

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["already_correct_total"] == 1
        assert report.details["skipped_user_edited_total"] == 0
        assert not db.writes

    def test_a_family_still_unmapped_is_already_correct_not_repaired(self) -> None:
        """Tier 3 stayed the last tier — an unknown family is correctly tropical."""
        db = _db(families=_family("Nothofagaceae"))

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["already_correct_total"] == 1
        assert not db.writes

    def test_a_hand_edited_profile_is_left_alone(self) -> None:
        db = _db(
            profiles=[_tropical_document(watering_interval_days=11)],
            families=_family(NEWLY_MAPPED_FAMILY),
        )

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["skipped_user_edited_total"] == 1
        assert _stored(db).watering_interval_days == 11
        assert not db.writes

    def test_a_second_run_writes_nothing(self) -> None:
        """M-3 — idempotent."""
        db = _db(families=_family(NEWLY_MAPPED_FAMILY))
        migration.up(db)  # type: ignore[arg-type]
        writes_after_first = len(db.writes)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["already_correct_total"] == 1
        assert len(db.writes) == writes_after_first

    def test_dry_run_reports_the_same_change_and_writes_nothing(self) -> None:
        """M-5."""
        db = _db(families=_family(NEWLY_MAPPED_FAMILY))

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert report.dry_run is True
        assert report.changed == 1
        assert report.details["repaired"][0]["new_care_style"] == CareStyleType.OUTDOOR_ANNUAL_VEG.value
        assert not db.writes
        assert _stored(db).care_style is CareStyleType.TROPICAL


class TestTheDriftGuard:
    def test_the_fallback_has_not_moved_today(self) -> None:
        assert tropical_fallback_drift(_ENGINE) == []

    def test_a_moved_fallback_refuses_the_run_instead_of_sweeping_it(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The criterion asks today's engine what the old code produced.

        That is only true while the tropical preset has not moved. When it has, the
        run must say so — not report a clean installation over a population it can
        no longer identify.
        """
        moved = {**_PRE_1505_TROPICAL_FALLBACK, "watering_interval_days": 9}
        monkeypatch.setattr(v0051, "_PRE_1505_TROPICAL_FALLBACK", moved)
        db = _db(families=_family(NEWLY_MAPPED_FAMILY))

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.precondition_unmet is True
        assert report.details["reason"] == "tropical_fallback_moved"
        assert report.details["changed_fields"] == ["watering_interval_days"]
        assert not db.writes

    def test_the_frozen_fallback_matches_the_engine_field_for_field(self) -> None:
        """A named comparison, so the drift is readable when this goes red."""
        current = _ENGINE.auto_generate_profile(botanical_family=None, plant_key="")
        for field, expected in _PRE_1505_TROPICAL_FALLBACK.items():
            assert current.model_dump(mode="json")[field] == expected, field


class TestTheFrameworkContract:
    def test_it_is_the_fifty_first_migration(self) -> None:
        assert migration.version == "0051"

    def test_it_is_not_reversible(self) -> None:
        assert migration.reversible is False
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_db())  # type: ignore[arg-type]

    def test_a_missing_collection_leaves_it_pending(self) -> None:
        db = _db()
        del db.collections[col.SPECIES]

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.precondition_unmet is True
        assert report.details["reason"] == "required_collections_missing"

    def test_an_empty_installation_is_a_noop(self) -> None:
        db = _db(profiles=[], plants=[], species=[], families=[])

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 0
        assert report.changed == 0

    def test_a_removed_plant_is_not_recomputed(self) -> None:
        db = _db(plants=[_plant(removed_on="2026-09-01")], families=_family(NEWLY_MAPPED_FAMILY))

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["plant_missing_total"] == 1

    def test_the_species_key_still_resolves_the_family_by_name(self) -> None:
        """#1489's lesson: the engine is handed the name, never the document key."""
        db = _db(species=[_species(family_key=FAMILY_KEY)], families=_family(NEWLY_MAPPED_FAMILY))

        migration.up(db)  # type: ignore[arg-type]

        assert SPECIES_KEY  # the species is read by key …
        assert _stored(db).care_style is CareStyleType.OUTDOOR_ANNUAL_VEG  # … and the family by name
