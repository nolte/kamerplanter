"""v0096 (#2325, REQ-053 M6, GP-ACC-037/049): the NutrientDemand split on a fake volume.

The fake dispatches the three scans and the batched ``UPDATE`` on their text and
applies the AQL filters itself; the real AQL is measured in
``tests/integration/test_v0096_v0097_req053_m5_m6.py``. The model side — the renamed
enum reads the rewritten rows, the species validator refuses a heavy-feeding nitrogen
fixer — is pinned here too.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.common.enums import NutrientDemand, PlanRole
from app.data_access.arango import collections as col
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions import v0096_nutrient_demand_split as module
from app.migrations.versions.v0096_nutrient_demand_split import migration


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db
        self.updates: list[tuple[str, list[dict[str, Any]]]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = bind_vars or {}
        collection = bind_vars["@collection"]
        docs = self.db.collections[collection]
        if "UPDATE u._key" in query:
            self.updates.append((collection, list(bind_vars["updates"])))
            for update in bind_vars["updates"]:
                for field, value in update["patch"].items():
                    if value is None:
                        docs[update["_key"]].pop(field, None)
                    else:
                        docs[update["_key"]][field] = value
            return iter(())
        if "f.typical_nutrient_demand IN @legacy" in query:
            return iter(
                {"_key": d["_key"], "value": d["typical_nutrient_demand"]}
                for d in docs.values()
                if d.get("typical_nutrient_demand") in bind_vars["legacy"]
            )
        if "s.nutrient_demand_level == @fixer" in query:
            fixer = bind_vars["fixer"]
            rows = [
                {
                    "_key": d["_key"],
                    "scientific_name": d.get("scientific_name"),
                    "is_fixer": d.get("nutrient_demand_level") == fixer,
                    "has_nitrogen_fixing": d.get("nitrogen_fixing") is not None,
                    "has_nutrient_demand": d.get("nutrient_demand") is not None,
                }
                for d in docs.values()
                if d.get("nutrient_demand_level") == fixer or d.get("nutrient_demand") is None
            ]
            return iter(sorted(rows, key=lambda r: r["scientific_name"] or ""))
        if "p.demand_level != null" in query:
            return iter(
                {"_key": d["_key"], "demand_level": d["demand_level"]}
                for d in docs.values()
                if d.get("demand_level") is not None
            )
        raise AssertionError(f"unexpected query: {query}")


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.collections: dict[str, dict[str, dict[str, Any]]] = {
            name: {d["_key"]: dict(d) for d in docs} for name, docs in collections.items()
        }
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.collections

    def snapshot(self) -> dict[str, dict[str, dict[str, Any]]]:
        return {name: {k: dict(d) for k, d in docs.items()} for name, docs in self.collections.items()}


def _pre_m6_volume(*, with_rotation_plans: bool = False) -> _FakeDb:
    collections: dict[str, list[dict[str, Any]]] = {
        col.BOTANICAL_FAMILIES: [
            {"_key": "fabaceae", "name": "Fabaceae", "typical_nutrient_demand": "light", "nitrogen_fixing": True},
            {"_key": "solanaceae", "name": "Solanaceae", "typical_nutrient_demand": "heavy"},
            {"_key": "apiaceae", "name": "Apiaceae", "typical_nutrient_demand": "medium"},
            # Seeded by a newer image already — not matched.
            {"_key": "rosaceae", "name": "Rosaceae", "typical_nutrient_demand": "medium_feeder"},
        ],
        col.SPECIES: [
            # GP-ACC-049: the pea — legacy nitrogen_fixer, Steckbrief value light_feeder already seeded.
            {
                "_key": "pea",
                "scientific_name": "Pisum sativum",
                "nutrient_demand_level": "nitrogen_fixer",
                "nutrient_demand": "light_feeder",
            },
            # A fixer without a sourced feeder level: flagged, listed, never defaulted.
            {"_key": "lupin", "scientific_name": "Lupinus albus", "nutrient_demand_level": "nitrogen_fixer"},
            # A fixer whose flag was already set (false — a claim) stays as stored.
            {
                "_key": "alder",
                "scientific_name": "Alnus glutinosa",
                "nutrient_demand_level": "nitrogen_fixer",
                "nitrogen_fixing": False,
                "nutrient_demand": "light_feeder",
            },
            # A heavy feeder without the new field: listed only (E-10 — never mapped from the legacy level).
            {"_key": "tomato", "scientific_name": "Solanum lycopersicum", "nutrient_demand_level": "heavy_feeder"},
            # Fully sourced: not matched at all.
            {"_key": "carrot", "scientific_name": "Daucus carota", "nutrient_demand": "medium_feeder"},
        ],
    }
    if with_rotation_plans:
        collections[module.CROP_ROTATION_PLANS] = [
            {"_key": "y1", "demand_level": "heavy_feeder"},
            {"_key": "y2", "demand_level": "green_manure"},
            {"_key": "y3", "demand_level": "fallow"},
            {"_key": "y4", "nutrient_demand": "light_feeder", "plan_role": "main_crop"},
            {"_key": "y5", "demand_level": "nitrogen_fixer"},
        ]
    return _FakeDb(collections)


class TestFamilies:
    def test_legacy_levels_are_renamed(self) -> None:
        db = _pre_m6_volume()

        report = migration.up(db)

        families = db.collections[col.BOTANICAL_FAMILIES]
        assert families["fabaceae"]["typical_nutrient_demand"] == "light_feeder"
        assert families["solanaceae"]["typical_nutrient_demand"] == "heavy_feeder"
        assert families["apiaceae"]["typical_nutrient_demand"] == "medium_feeder"
        assert families["rosaceae"]["typical_nutrient_demand"] == "medium_feeder"
        assert report.details[col.BOTANICAL_FAMILIES] == {
            "scanned": 3,
            "renamed": {"light": 1, "medium": 1, "heavy": 1},
            "updated": 3,
        }
        for doc in families.values():
            assert BotanicalFamily.model_validate(doc) is not None  # the renamed enum reads every rewritten row


class TestSpecies:
    def test_a_nitrogen_fixer_gets_the_flag_and_keeps_its_sourced_level(self) -> None:
        """GP-ACC-049."""
        db = _pre_m6_volume()

        migration.up(db)

        pea = db.collections[col.SPECIES]["pea"]
        assert pea["nitrogen_fixing"] is True
        assert pea["nutrient_demand"] == "light_feeder"
        assert pea["nutrient_demand_level"] == "nitrogen_fixer", "the legacy field stays — the EC resolver reads it"
        species = Species.model_validate({**pea, "genus": "Pisum"})
        assert species.nitrogen_fixing is True and species.nutrient_demand is NutrientDemand.LIGHT_FEEDER

    def test_nothing_is_derived_for_a_species_without_a_sourced_level(self) -> None:
        db = _pre_m6_volume()

        report = migration.up(db)

        species = db.collections[col.SPECIES]
        assert species["lupin"]["nitrogen_fixing"] is True and "nutrient_demand" not in species["lupin"]
        assert "nutrient_demand" not in species["tomato"] and "nitrogen_fixing" not in species["tomato"]
        assert species["alder"]["nitrogen_fixing"] is False, "a stored claim is kept"
        assert report.details[col.SPECIES] == {
            "scanned": 4,
            "nitrogen_fixing_stamped": 2,
            "nitrogen_fixer_already_flagged": 1,
            "without_nutrient_demand": {"count": 2, "listed": ["Lupinus albus", "Solanum lycopersicum"]},
            "updated": 2,
        }

    def test_the_gap_list_is_capped_but_counted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(module, "_LISTED_NAMES", 1)

        report = migration.up(_pre_m6_volume(), dry_run=True)

        assert report.details[col.SPECIES]["without_nutrient_demand"] == {"count": 2, "listed": ["Lupinus albus"]}


class TestRotationPlans:
    def test_demand_level_becomes_nutrient_demand_and_plan_role(self) -> None:
        db = _pre_m6_volume(with_rotation_plans=True)

        report = migration.up(db)

        plans = db.collections[module.CROP_ROTATION_PLANS]
        assert plans["y1"] == {"_key": "y1", "nutrient_demand": "heavy_feeder", "plan_role": "main_crop"}
        assert plans["y2"] == {"_key": "y2", "plan_role": "green_manure"}
        assert plans["y3"] == {"_key": "y3", "plan_role": "fallow"}
        assert plans["y4"] == {"_key": "y4", "nutrient_demand": "light_feeder", "plan_role": "main_crop"}
        assert plans["y5"] == {"_key": "y5", "demand_level": "nitrogen_fixer"}, "unknown: listed, not guessed"
        assert report.details[module.CROP_ROTATION_PLANS] == {
            "collection_present": True,
            "scanned": 4,
            "converted": {"main_crop": 1, "green_manure": 1, "fallow": 1},
            "refused_unknown_demand_level": {"count": 1, "listed": ["y5"]},
            "updated": 3,
        }
        assert {PlanRole(p["plan_role"]) for p in plans.values() if "plan_role" in p} == set(PlanRole)

    def test_the_collection_is_absent_on_shipped_volumes(self) -> None:
        report = migration.up(_pre_m6_volume())

        assert report.details[module.CROP_ROTATION_PLANS]["collection_present"] is False
        assert report.details[module.CROP_ROTATION_PLANS]["updated"] == 0


class TestRunSemantics:
    def test_second_run_changes_nothing(self) -> None:
        db = _pre_m6_volume(with_rotation_plans=True)
        migration.up(db)
        before = db.snapshot()

        report = migration.up(db)

        assert report.changed == 0 and report.noop is True
        assert db.snapshot() == before
        # The gap list is a report, not a change: still listed on the second run.
        assert report.details[col.SPECIES]["without_nutrient_demand"]["count"] == 2

    def test_dry_run_reports_and_writes_nothing(self) -> None:
        db = _pre_m6_volume(with_rotation_plans=True)
        before = db.snapshot()

        report = migration.up(db, dry_run=True)

        assert report.dry_run is True and report.changed == 0 and report.scanned == 3 + 4 + (3 + 1)
        assert report.details[col.BOTANICAL_FAMILIES]["will_update"] == 3
        assert report.details[col.SPECIES]["will_update"] == 2
        assert report.details[module.CROP_ROTATION_PLANS]["will_update"] == 3
        assert db.snapshot() == before and db.aql.updates == []

    def test_a_volume_without_the_collections_is_a_noop(self) -> None:
        report = migration.up(_FakeDb({}))

        assert report.changed == 0 and report.scanned == 0

    def test_down_is_refused(self) -> None:
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb({}))


class TestModelSide:
    def test_the_enum_is_the_feeder_triple(self) -> None:
        assert {m.value for m in NutrientDemand} == {"heavy_feeder", "medium_feeder", "light_feeder"}
        assert set(NutrientDemand) == {NutrientDemand(v) for v in module.FAMILY_DEMAND_MAP.values()}

    def test_a_species_refuses_nitrogen_fixer_and_fallow_as_a_level(self) -> None:
        for bad in ("nitrogen_fixer", "fallow", "green_manure", "heavy"):
            with pytest.raises(ValidationError):
                Species(scientific_name="Pisum sativum", genus="Pisum", nutrient_demand=bad)

    def test_a_family_refuses_the_legacy_spelling(self) -> None:
        with pytest.raises(ValidationError):
            BotanicalFamily(name="Fabaceae", typical_nutrient_demand="light")

    def test_a_heavy_feeding_nitrogen_fixer_is_refused_on_species_and_family(self) -> None:
        pea = {"scientific_name": "Pisum sativum", "genus": "Pisum", "nitrogen_fixing": True}
        with pytest.raises(ValidationError):
            Species(**pea, nutrient_demand="heavy_feeder")
        with pytest.raises(ValidationError):
            BotanicalFamily(name="Fabaceae", nitrogen_fixing=True, typical_nutrient_demand="heavy_feeder")
        assert Species(**pea, nutrient_demand="light_feeder").nitrogen_fixing is True

    def test_the_sourced_fields_round_trip_and_unsourced_stay_null(self) -> None:
        species = Species(
            scientific_name="Daucus carota",
            genus="Daucus",
            nutrient_demand="medium_feeder",
            nutrient_demand_source="https://example.org/carrot",
            nutrient_demand_confidence="high",
            rotation_pause_years=3,
            row_spacing_cm="25--30",
            light_requirement="full_sun",
        )
        dumped = species.model_dump()
        assert dumped["nutrient_demand"] == "medium_feeder" and dumped["row_spacing_cm"] == "25--30"
        assert dumped["nitrogen_fixing"] is None, "unsourced — never defaulted to false"
        with pytest.raises(ValidationError):
            Species(scientific_name="Daucus carota", genus="Daucus", row_spacing_cm="wide")
        with pytest.raises(ValidationError):
            Species(scientific_name="Daucus carota", genus="Daucus", rotation_pause_years=9)
