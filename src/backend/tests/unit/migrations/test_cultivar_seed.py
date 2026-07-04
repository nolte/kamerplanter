"""Unit tests for the shared cultivar seed builder.

``build_cultivar`` is the single source of truth for turning a seed YAML cultivar
entry into a ``Cultivar`` model, used by every plant seeder. These tests pin the
field mapping — most importantly that fields which used to be silently dropped by
individual loaders (``breeding_year``, ``disease_resistances``,
``phase_watering_overrides``, …) now survive the round trip (issue #302, B5.6).
"""

from __future__ import annotations

from app.common.enums import DtmReference, PlantTrait
from app.migrations.cultivar_seed import build_cultivar


def test_full_entry_maps_every_field() -> None:
    entry = {
        "name": "Yolo Wonder",
        "breeder": "PetoSeed",
        "breeding_year": 1952,
        "patent_status": "expired",
        "days_to_maturity": 75,
        "dtm_reference": "transplant",
        "bearing_start_year_min": 1,
        "bearing_start_year_max": 2,
        "traits": ["disease_resistant", "high_yield"],
        "seed_type": "open_pollinated",
        "disease_resistances": ["TMV", "PVY"],
        "phase_watering_overrides": {"flowering": 3},
        "watering_guide_override": {"interval_days": 4, "volume_ml_min": 200, "volume_ml_max": 600},
    }

    cultivar = build_cultivar(entry, species_key="sp-123")

    assert cultivar.name == "Yolo Wonder"
    assert cultivar.species_key == "sp-123"
    assert cultivar.breeder == "PetoSeed"
    assert cultivar.breeding_year == 1952
    assert cultivar.patent_status == "expired"
    assert cultivar.days_to_maturity == 75
    assert cultivar.dtm_reference is DtmReference.TRANSPLANT
    assert cultivar.bearing_start_year_min == 1
    assert cultivar.bearing_start_year_max == 2
    assert cultivar.traits == [PlantTrait.DISEASE_RESISTANT, PlantTrait.HIGH_YIELD]
    assert cultivar.seed_type == "open_pollinated"
    assert cultivar.disease_resistances == ["TMV", "PVY"]
    assert cultivar.phase_watering_overrides == {"flowering": 3}
    assert cultivar.watering_guide_override is not None
    assert cultivar.watering_guide_override.interval_days == 4


def test_breeding_year_survives_minimal_entry() -> None:
    """Regression: breeding_year present in data must not be dropped on import."""
    cultivar = build_cultivar({"name": "Marketmore 76", "breeding_year": 1976}, species_key="sp-9")

    assert cultivar.breeding_year == 1976


def test_missing_optional_fields_default_cleanly() -> None:
    cultivar = build_cultivar({"name": "Bare"}, species_key="sp-1")

    assert cultivar.breeding_year is None
    assert cultivar.patent_status == ""
    assert cultivar.dtm_reference is None
    assert cultivar.days_to_maturity is None
    assert cultivar.traits == []
    assert cultivar.disease_resistances == []
    assert cultivar.watering_guide_override is None
    assert cultivar.phase_watering_overrides is None


def test_unknown_traits_are_skipped_not_raised() -> None:
    cultivar = build_cultivar(
        {"name": "Mixed", "traits": ["compact", "not_a_real_trait", "heirloom"]},
        species_key="sp-1",
    )

    assert cultivar.traits == [PlantTrait.COMPACT, PlantTrait.HEIRLOOM]


def test_null_dtm_reference_is_none() -> None:
    cultivar = build_cultivar({"name": "X", "dtm_reference": None}, species_key="sp-1")

    assert cultivar.dtm_reference is None


def test_nonpositive_days_to_maturity_coerced_to_none() -> None:
    """The model enforces ge=1; a stray 0/negative (e.g. ornamentals) must not crash."""
    assert build_cultivar({"name": "Zero", "days_to_maturity": 0}, species_key="sp-1").days_to_maturity is None
    assert build_cultivar({"name": "Neg", "days_to_maturity": -5}, species_key="sp-1").days_to_maturity is None
    assert build_cultivar({"name": "Ok", "days_to_maturity": 60}, species_key="sp-1").days_to_maturity == 60
