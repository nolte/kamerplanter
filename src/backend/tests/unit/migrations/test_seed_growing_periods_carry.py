"""Pin that every seeder carries ``growing_periods`` from YAML onto the model.

Modelling ``growing_periods`` in the seed schemas (REQ-015-A, audit 2026-08-08 §3
finding 9) is only half the pipeline. The other half is that the loader actually
imports the field — and ``seed_plant_info._build_species`` is **whitelist-driven**:
it names every field it carries, so an unnamed one is dropped without a word. That
is precisely how ``breeding_year`` was once lost.

Before this change, a growing period authored in any ``plant_info*.yaml`` would
have been accepted by the schema, accepted by YAML, and then silently discarded on
import — the species would come out of the seeder with a single, wrong cultivation
window. ``seed_adventskalender._build_species`` derives its carry set from
``Species.model_fields`` and never had the gap, which is why *Allium porrum*'s two
windows do reach the database while a ``plant_info*.yaml`` species' would not have.

The enrichment path needs its own coverage for a second reason: enrichment is
applied with a bare ``setattr`` (fill-if-empty, ``seed_plant_info.py`` §S3), which
runs no Pydantic validation. Raw dicts left un-coerced there would be persisted
straight into ArangoDB.
"""

from __future__ import annotations

from app.domain.models.species import GrowingPeriod
from app.migrations.seed_adventskalender import _build_species as _build_species_adventskalender
from app.migrations.seed_plant_info import _build_enrichment, _build_species
from app.migrations.seed_plant_info_extended import (
    _build_enrichment as _build_enrichment_extended,
)
from app.migrations.seed_plant_info_extended import (
    _build_species as _build_species_extended,
)

#: Mirrors the ``Allium porrum`` shape in adventskalender.yaml — two genuine
#: cultivation windows whose sowing months do not overlap (#1008).
_TWO_WINDOW_ENTRY = {
    "scientific_name": "Allium porrum",
    "genus": "Allium",
    "growth_habit": "herb",
    "root_type": "fibrous",
    "growing_periods": [
        {"label": "Sommerporree", "direct_sow_months": [2, 3], "harvest_months": [8, 9, 10, 11]},
        {"label": "Winterporree", "direct_sow_months": [5, 6], "harvest_months": [12, 1, 2, 3]},
    ],
}


class TestNewSpeciesCarry:
    def test_plant_info_loader_carries_growing_periods(self) -> None:
        (species,) = _build_species({"new_species": [_TWO_WINDOW_ENTRY]})

        assert len(species.growing_periods) == 2, (
            "seed_plant_info._build_species dropped the growing periods — the whitelist "
            "does not name the field, so both cultivation windows are lost on import"
        )
        assert [p.label for p in species.growing_periods] == ["Sommerporree", "Winterporree"]
        assert species.growing_periods[1].direct_sow_months == [5, 6]

    def test_plant_info_loader_defaults_to_no_periods(self) -> None:
        species_list = _build_species(
            {"new_species": [{k: v for k, v in _TWO_WINDOW_ENTRY.items() if k != "growing_periods"}]}
        )
        assert species_list[0].growing_periods == []

    def test_extended_loader_carries_growing_periods(self) -> None:
        (species,) = _build_species_extended({"new_species": [_TWO_WINDOW_ENTRY]})
        assert len(species.growing_periods) == 2

    def test_adventskalender_loader_carries_growing_periods(self) -> None:
        (species,) = _build_species_adventskalender({"new_species": [_TWO_WINDOW_ENTRY]})
        assert len(species.growing_periods) == 2


class TestEnrichmentCarry:
    def test_enrichment_coerces_growing_periods_into_models(self) -> None:
        enrichment = _build_enrichment({"species_enrichment": {"Allium porrum": _TWO_WINDOW_ENTRY}})
        periods = enrichment["Allium porrum"]["growing_periods"]

        assert all(isinstance(p, GrowingPeriod) for p in periods), (
            "enrichment must coerce growing periods to GrowingPeriod — the seeder applies "
            "enrichment with a bare setattr, which validates nothing"
        )
        assert [p.label for p in periods] == ["Sommerporree", "Winterporree"]

    def test_extended_enrichment_coerces_growing_periods_into_models(self) -> None:
        enrichment = _build_enrichment_extended({"species_enrichment": {"Allium porrum": _TWO_WINDOW_ENTRY}})
        periods = enrichment["Allium porrum"]["growing_periods"]
        assert all(isinstance(p, GrowingPeriod) for p in periods)
        assert len(periods) == 2

    def test_enrichment_leaves_an_absent_field_absent(self) -> None:
        enrichment = _build_enrichment({"species_enrichment": {"Allium porrum": {"genus": "Allium"}}})
        assert "growing_periods" not in enrichment["Allium porrum"]
