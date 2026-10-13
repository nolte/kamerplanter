"""Every ``species_names`` entry on a seeded nutrient plan names a seeded species (#1618).

The seed loaders resolve a plan's ``species_names`` (scientific names from the
plan's source document) against the species catalogue and **skip** a name the
catalogue does not hold, with a warning. Skipping is right at runtime — a typo
must not abort the startup — but it is silent in effect: the plan ends up linked
to fewer species, or to none, and then the onboarding wizard never offers it.
This gate moves that failure to commit time.

The catalogue is read from the same seed files the species seeders load — the
``species`` list of ``species.yaml`` and the ``new_species`` lists of
``adventskalender.yaml``, ``plant_info.yaml`` and every file in
``seed_plant_info_extended.YAML_FILES`` — so a species added in any of them
counts, and a plan file is found through the loaders that read it rather than a
second hand-kept list.

Traces to issue #1618 (no TC-ID: a seed-data gate is not a user-facing case).
"""

from __future__ import annotations

from app.migrations import seed_plant_info_extended
from app.migrations.yaml_loader import load_yaml

#: The seed files the five plan loaders read (seed_fertilizers, seed_plagron,
#: seed_gardol, seed_nutrient_plans_outdoor, seed_nutrient_plans_ro).
PLAN_FILES = (
    "fertilizers.yaml",
    "plagron.yaml",
    "gardol.yaml",
    "nutrient_plans_outdoor.yaml",
    "nutrient_plans_ro.yaml",
)


def _catalogue() -> set[str]:
    names = {entry["scientific_name"] for entry in load_yaml("species.yaml")["species"]}
    for file_name in ("adventskalender.yaml", "plant_info.yaml", *seed_plant_info_extended.YAML_FILES):
        names.update(entry["scientific_name"] for entry in load_yaml(file_name).get("new_species", []) or [])
    return names


def _plans() -> list[tuple[str, dict]]:
    return [(file_name, plan) for file_name in PLAN_FILES for plan in load_yaml(file_name)["nutrient_plans"]]


def test_every_species_name_resolves_to_a_seeded_species() -> None:
    catalogue = _catalogue()

    unresolved = [
        f"{file_name}: {plan['name']!r} -> {name!r}"
        for file_name, plan in _plans()
        for name in plan.get("species_names", [])
        if name not in catalogue
    ]

    assert unresolved == []


def test_the_gate_sees_a_name_the_catalogue_does_not_hold() -> None:
    # The gate is not vacuous: the catalogue it reads is populated, and a name
    # outside it would be reported by the comprehension above.
    catalogue = _catalogue()

    assert "Solanum lycopersicum" in catalogue
    assert "Solanum lycopersicum var. imaginarium" not in catalogue


def test_the_relation_is_actually_carried_by_the_seed_files() -> None:
    # A rename of the YAML key would leave every plan unlinked and the first test
    # trivially green; pin that the key is present where the sources name species.
    linked = [plan["name"] for _file, plan in _plans() if plan.get("species_names")]

    assert "Tomate — Plagron Terra + PK 13-14" in linked
    assert len(linked) > len(_plans()) // 2
