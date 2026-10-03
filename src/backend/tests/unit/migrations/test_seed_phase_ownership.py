"""#2002 — which seed file owns a species' growth phases, read off the shipped seed YAML.

*Cichorium intybus* is the measured case: ``adventskalender.yaml`` carries its phases,
``plant_info_outdoor_1.yaml`` only its lifecycle. The extended loader used to delete
the phases it found and write none; the adventskalender loader wrote them back on the
next start.
"""

from __future__ import annotations

from app.migrations.seed_phase_ownership import phases_owned_elsewhere, species_with_seeded_phases
from app.migrations.seed_plant_info_extended import YAML_FILES
from app.migrations.yaml_loader import load_yaml

_SPECIES = "Cichorium intybus"


def _phase_data(filename: str) -> dict[str, object]:
    return dict(load_yaml(filename).get("growth_phases") or {})


def test_the_extended_loader_leaves_the_phases_the_adventskalender_file_carries() -> None:
    assert _SPECIES not in _phase_data("plant_info_outdoor_1.yaml")
    assert _SPECIES in _phase_data("adventskalender.yaml")

    assert phases_owned_elsewhere(_SPECIES, _phase_data("plant_info_outdoor_1.yaml"))


def test_the_file_that_carries_the_phases_owns_them() -> None:
    assert not phases_owned_elsewhere(_SPECIES, _phase_data("adventskalender.yaml"))


def test_a_species_no_file_gives_phases_keeps_the_previous_behaviour() -> None:
    """``Coriandrum sativum``: a lifecycle in the extended files, phases in none — not owned elsewhere."""
    assert "Coriandrum sativum" not in species_with_seeded_phases()
    assert not phases_owned_elsewhere("Coriandrum sativum", {})


def test_every_phase_source_file_is_read() -> None:
    expected: set[str] = set()
    for filename in ("adventskalender.yaml", "plant_info.yaml", *YAML_FILES):
        expected.update(name for name, phases in _phase_data(filename).items() if phases)

    assert species_with_seeded_phases() == expected
