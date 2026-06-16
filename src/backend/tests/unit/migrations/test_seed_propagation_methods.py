"""Unit tests for propagation handling in the plant-info seeders.

Covers the pure model-construction helpers (_build_species, _build_enrichment,
_build_propagation_configs) without touching the database — verifying that the
seeders adapt the legacy flat propagation fields into structured
``propagation_configs`` and pass native configs through, on both the base and
extended seeder.
"""

from app.common.enums import PropagationMethod, WoodStage
from app.migrations.seed_plant_info import (
    _build_enrichment,
    _build_propagation_configs,
    _build_species,
)
from app.migrations.seed_plant_info_extended import (
    _build_enrichment as _build_enrichment_extended,
)
from app.migrations.seed_plant_info_extended import (
    _build_propagation_configs as _build_propagation_configs_extended,
)
from app.migrations.seed_plant_info_extended import (
    _build_species as _build_species_extended,
)


class TestBaseSeederFlatAdapter:
    def test_flat_methods_become_one_config_each(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Mentha spicata",
                    "genus": "Mentha",
                    "propagation_methods": ["seed", "cutting", "runner"],
                    "propagation_months": [3, 4, 5],
                    "propagation_notes": "Stecklinge wurzeln leicht im Wasserglas.",
                }
            ]
        }
        species = _build_species(data)
        configs = species[0].propagation_configs
        assert [c.method for c in configs] == [
            PropagationMethod.SEED,
            PropagationMethod.CUTTING,
            PropagationMethod.RUNNER,
        ]
        # Timing window is shared across the adapted methods (data-quality split is WP-10).
        assert all(c.months == [3, 4, 5] for c in configs)
        # The single legacy note is attached to the first method only.
        assert configs[0].notes == "Stecklinge wurzeln leicht im Wasserglas."
        assert configs[1].notes is None

    def test_defaults_to_empty(self):
        data = {"new_species": [{"scientific_name": "Genus species", "genus": "Genus"}]}
        species = _build_species(data)
        assert species[0].propagation_configs == []

    def test_native_configs_pass_through(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Rosa canina",
                    "genus": "Rosa",
                    "propagation_configs": [
                        {"method": "cutting", "months": [6, 7], "wood_stage": "softwood"},
                        {"method": "grafting", "months": [8], "difficulty": "difficult"},
                    ],
                }
            ]
        }
        species = _build_species(data)
        configs = species[0].propagation_configs
        assert configs[0].method == PropagationMethod.CUTTING
        assert configs[0].wood_stage == WoodStage.SOFTWOOD
        assert configs[1].method == PropagationMethod.GRAFTING

    def test_enrichment_flat_becomes_configs(self):
        data = {
            "species_enrichment": {
                "Solanum lycopersicum": {
                    "scientific_name": "Solanum lycopersicum",
                    "propagation_methods": ["seed", "cutting"],
                    "propagation_months": [2, 3],
                }
            }
        }
        result = _build_enrichment(data)
        configs = result["Solanum lycopersicum"]["propagation_configs"]
        assert [c.method for c in configs] == [PropagationMethod.SEED, PropagationMethod.CUTTING]
        # Flat keys must not leak through — setattr would fail on the model.
        assert "propagation_methods" not in result["Solanum lycopersicum"]
        assert "propagation_months" not in result["Solanum lycopersicum"]

    def test_enrichment_without_propagation_omits_key(self):
        data = {"species_enrichment": {"Hosta sieboldiana": {"scientific_name": "Hosta sieboldiana", "genus": "Hosta"}}}
        result = _build_enrichment(data)
        assert "propagation_configs" not in result["Hosta sieboldiana"]

    def test_helper_reconciled_method(self):
        configs = _build_propagation_configs({"propagation_methods": ["air_layering", "tissue_culture"]})
        assert [c.method for c in configs] == [
            PropagationMethod.AIR_LAYERING,
            PropagationMethod.TISSUE_CULTURE,
        ]


class TestExtendedSeederFlatAdapter:
    def test_semicolon_string_becomes_configs(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Mentha spicata",
                    "genus": "Mentha",
                    "propagation_methods": "seed; cutting; runner",
                    "propagation_months": [3, 4],
                }
            ]
        }
        species = _build_species_extended(data)
        configs = species[0].propagation_configs
        assert [c.method for c in configs] == [
            PropagationMethod.SEED,
            PropagationMethod.CUTTING,
            PropagationMethod.RUNNER,
        ]
        assert configs[0].months == [3, 4]

    def test_native_configs_pass_through(self):
        configs = _build_propagation_configs_extended(
            {"propagation_configs": [{"method": "division", "months": [9, 10]}]}
        )
        assert configs[0].method == PropagationMethod.DIVISION
        assert configs[0].months == [9, 10]

    def test_enrichment_semicolon_becomes_configs(self):
        data = {
            "species_enrichment": {
                "Mentha spicata": {
                    "scientific_name": "Mentha spicata",
                    "propagation_methods": "seed; cutting",
                }
            }
        }
        result = _build_enrichment_extended(data)
        configs = result["Mentha spicata"]["propagation_configs"]
        assert [c.method for c in configs] == [PropagationMethod.SEED, PropagationMethod.CUTTING]
        assert "propagation_methods" not in result["Mentha spicata"]

    def test_defaults_to_empty(self):
        data = {"new_species": [{"scientific_name": "Genus species", "genus": "Genus"}]}
        species = _build_species_extended(data)
        assert species[0].propagation_configs == []
