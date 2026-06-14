"""Unit tests for propagation_methods pass-through in the plant-info seeders.

Covers the pure model-construction helpers (_build_species, _build_enrichment)
without touching the database — verifying that YAML strings are converted to
PropagationMethod enum members on both the base and extended seeder.
"""

from app.common.enums import PropagationMethod
from app.migrations.seed_plant_info import (
    _build_enrichment,
    _build_species,
)
from app.migrations.seed_plant_info_extended import (
    _build_enrichment as _build_enrichment_extended,
)
from app.migrations.seed_plant_info_extended import (
    _build_species as _build_species_extended,
)


class TestBaseSeederPropagationMethods:
    def test_build_species_converts_strings_to_enum(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Mentha spicata",
                    "genus": "Mentha",
                    "propagation_methods": ["seed", "cutting", "runner"],
                }
            ]
        }
        species = _build_species(data)
        assert len(species) == 1
        assert species[0].propagation_methods == [
            PropagationMethod.SEED,
            PropagationMethod.CUTTING,
            PropagationMethod.RUNNER,
        ]

    def test_build_species_defaults_to_empty(self):
        data = {"new_species": [{"scientific_name": "Genus species", "genus": "Genus"}]}
        species = _build_species(data)
        assert species[0].propagation_methods == []

    def test_build_enrichment_converts_strings_to_enum(self):
        data = {
            "species_enrichment": {
                "Solanum lycopersicum": {
                    "scientific_name": "Solanum lycopersicum",
                    "propagation_methods": ["seed", "cutting"],
                }
            }
        }
        result = _build_enrichment(data)
        assert result["Solanum lycopersicum"]["propagation_methods"] == [
            PropagationMethod.SEED,
            PropagationMethod.CUTTING,
        ]


class TestExtendedSeederPropagationMethods:
    def test_build_species_converts_list(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Mentha spicata",
                    "genus": "Mentha",
                    "propagation_methods": ["seed", "division"],
                }
            ]
        }
        species = _build_species_extended(data)
        assert species[0].propagation_methods == [
            PropagationMethod.SEED,
            PropagationMethod.DIVISION,
        ]

    def test_build_species_converts_semicolon_string(self):
        """Extended seeder accepts CSV-derived semicolon-separated strings."""
        data = {
            "new_species": [
                {
                    "scientific_name": "Mentha spicata",
                    "genus": "Mentha",
                    "propagation_methods": "seed; cutting; runner",
                }
            ]
        }
        species = _build_species_extended(data)
        assert species[0].propagation_methods == [
            PropagationMethod.SEED,
            PropagationMethod.CUTTING,
            PropagationMethod.RUNNER,
        ]

    def test_build_enrichment_converts_semicolon_string(self):
        data = {
            "species_enrichment": {
                "Mentha spicata": {
                    "scientific_name": "Mentha spicata",
                    "propagation_methods": "seed; cutting",
                }
            }
        }
        result = _build_enrichment_extended(data)
        assert result["Mentha spicata"]["propagation_methods"] == [
            PropagationMethod.SEED,
            PropagationMethod.CUTTING,
        ]
