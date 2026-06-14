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


class TestBaseSeederPropagationMonths:
    def test_build_species_passes_months_as_int_list(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Anemone hupehensis",
                    "genus": "Anemone",
                    "propagation_months": [3, 4],
                }
            ]
        }
        species = _build_species(data)
        assert species[0].propagation_months == [3, 4]

    def test_build_species_months_default_to_empty(self):
        data = {"new_species": [{"scientific_name": "Genus species", "genus": "Genus"}]}
        species = _build_species(data)
        assert species[0].propagation_months == []

    def test_build_species_months_dedup_and_sort(self):
        """The Species validator deduplicates and sorts month lists."""
        data = {
            "new_species": [
                {
                    "scientific_name": "Genus species",
                    "genus": "Genus",
                    "propagation_months": [4, 3, 3],
                }
            ]
        }
        species = _build_species(data)
        assert species[0].propagation_months == [3, 4]

    def test_build_enrichment_passes_months_through(self):
        data = {
            "species_enrichment": {
                "Hosta sieboldiana": {
                    "scientific_name": "Hosta sieboldiana",
                    "propagation_months": [3, 4, 9],
                }
            }
        }
        result = _build_enrichment(data)
        assert result["Hosta sieboldiana"]["propagation_months"] == [3, 4, 9]


class TestBaseSeederPropagationNotes:
    def test_build_species_passes_notes_through(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Hosta sieboldiana",
                    "genus": "Hosta",
                    "propagation_notes": "Im Frühjahr teilen, jeder Teil braucht ein Auge.",
                }
            ]
        }
        species = _build_species(data)
        assert species[0].propagation_notes == "Im Frühjahr teilen, jeder Teil braucht ein Auge."

    def test_build_species_notes_default_to_none(self):
        data = {"new_species": [{"scientific_name": "Genus species", "genus": "Genus"}]}
        species = _build_species(data)
        assert species[0].propagation_notes is None

    def test_build_enrichment_passes_notes_through(self):
        data = {
            "species_enrichment": {
                "Mentha spicata": {
                    "scientific_name": "Mentha spicata",
                    "propagation_notes": "Stecklinge wurzeln leicht im Wasserglas.",
                }
            }
        }
        result = _build_enrichment(data)
        assert result["Mentha spicata"]["propagation_notes"] == "Stecklinge wurzeln leicht im Wasserglas."


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


class TestExtendedSeederPropagationMonths:
    def test_build_species_passes_months_as_int_list(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Anemone hupehensis",
                    "genus": "Anemone",
                    "propagation_months": [3, 4],
                }
            ]
        }
        species = _build_species_extended(data)
        assert species[0].propagation_months == [3, 4]

    def test_build_species_months_default_to_empty(self):
        data = {"new_species": [{"scientific_name": "Genus species", "genus": "Genus"}]}
        species = _build_species_extended(data)
        assert species[0].propagation_months == []

    def test_build_enrichment_passes_months_through(self):
        data = {
            "species_enrichment": {
                "Hosta sieboldiana": {
                    "scientific_name": "Hosta sieboldiana",
                    "propagation_months": [3, 4, 9],
                }
            }
        }
        result = _build_enrichment_extended(data)
        assert result["Hosta sieboldiana"]["propagation_months"] == [3, 4, 9]


class TestExtendedSeederPropagationNotes:
    def test_build_species_passes_notes_through(self):
        data = {
            "new_species": [
                {
                    "scientific_name": "Hosta sieboldiana",
                    "genus": "Hosta",
                    "propagation_notes": "Im Frühjahr teilen, jeder Teil braucht ein Auge.",
                }
            ]
        }
        species = _build_species_extended(data)
        assert species[0].propagation_notes == "Im Frühjahr teilen, jeder Teil braucht ein Auge."

    def test_build_species_notes_default_to_none(self):
        data = {"new_species": [{"scientific_name": "Genus species", "genus": "Genus"}]}
        species = _build_species_extended(data)
        assert species[0].propagation_notes is None

    def test_build_enrichment_passes_notes_through(self):
        data = {
            "species_enrichment": {
                "Mentha spicata": {
                    "scientific_name": "Mentha spicata",
                    "propagation_notes": "Stecklinge wurzeln leicht im Wasserglas.",
                }
            }
        }
        result = _build_enrichment_extended(data)
        assert result["Mentha spicata"]["propagation_notes"] == "Stecklinge wurzeln leicht im Wasserglas."
