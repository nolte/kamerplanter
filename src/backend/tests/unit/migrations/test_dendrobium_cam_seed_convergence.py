"""Seed↔migration convergence proof for Dendrobium nobile (#680).

Dendrobium nobile must bind to ``cam_succulent_rest`` on a **fresh install** exactly as
the ``v0028`` rebind migration binds it on an **existing** install. Fresh installs derive
the binding from the attribute-driven resolver
(:func:`~app.migrations.perennial_binding.resolve_phase_sequence_name`) fed by the seeded
``lifecycle_configs`` block and the species attributes; ``v0028`` carries the frozen
:data:`_TARGET_SEQUENCE`.

Before the seed fix the species carried ``photosynthesis_type: c3``, so the resolver fell
through to Rule 5 → ``evergreen_foliage_perennial`` — a cycle *without* the cool-dry winter
rest that Dendrobium's bloom depends on (``dormancy_required: false``). The seed fix sets
``cam``, so Rule 3 (CAM) fires → ``cam_succulent_rest`` (``dormancy_required: true``). This
test reads the *real* seed YAML and proves fresh-install and migration now converge.
"""

from __future__ import annotations

from app.migrations.perennial_binding import (
    CAM_SUCCULENT_REST_SEQUENCE,
    resolve_phase_sequence_name,
)
from app.migrations.versions.v0028_rebind_dendrobium_nobile_cam_succulent_rest import (
    _TARGET_SEQUENCE,
)
from app.migrations.yaml_loader import load_yaml

_SCIENTIFIC_NAME = "Dendrobium nobile"

#: Every plant-info seed file the species and lifecycle blocks may live in.
_PLANT_INFO_FILES = (
    "plant_info.yaml",
    "plant_info_indoor_1.yaml",
    "plant_info_indoor_2.yaml",
    "plant_info_indoor_3.yaml",
    "plant_info_indoor_4.yaml",
    "plant_info_supplement_1.yaml",
)

_CAM = "cam"


def _load_seeded_attributes() -> tuple[dict[str, dict], dict[str, dict]]:
    """Return ``(species_attr, lifecycles)`` keyed by scientific name across all seed files."""
    species_attr: dict[str, dict] = {}
    lifecycles: dict[str, dict] = {}
    for filename in _PLANT_INFO_FILES:
        data = load_yaml(filename)
        for species in data.get("new_species") or []:
            species_attr[species["scientific_name"]] = species
        for name, config in (data.get("lifecycle_configs") or {}).items():
            lifecycles[name] = config
    return species_attr, lifecycles


def test_seed_carries_cam_for_dendrobium() -> None:
    """The seed fix must set photosynthesis_type=cam on Dendrobium nobile."""
    species_attr, _ = _load_seeded_attributes()
    assert _SCIENTIFIC_NAME in species_attr, f"{_SCIENTIFIC_NAME} missing from seeded new_species"
    assert species_attr[_SCIENTIFIC_NAME].get("photosynthesis_type") == _CAM


def test_v0028_target_is_cam_succulent_rest() -> None:
    """The frozen migration target must be cam_succulent_rest."""
    assert _TARGET_SEQUENCE[_SCIENTIFIC_NAME] == CAM_SUCCULENT_REST_SEQUENCE


def test_fresh_install_binding_matches_v0028() -> None:
    """Seeded attributes → resolver → ``cam_succulent_rest`` == the frozen v0028 target."""
    species_attr, lifecycles = _load_seeded_attributes()

    species = species_attr[_SCIENTIFIC_NAME]
    lifecycle = lifecycles.get(_SCIENTIFIC_NAME)
    assert lifecycle is not None, f"{_SCIENTIFIC_NAME} missing a seeded lifecycle_configs block"

    resolved = resolve_phase_sequence_name(
        _SCIENTIFIC_NAME,
        cycle_type=lifecycle.get("cycle_type"),
        flowering_strategy=lifecycle.get("flowering_strategy"),
        photosynthesis_type=species.get("photosynthesis_type"),
        photoperiod_type=lifecycle.get("photoperiod_type"),
        growth_habit=species.get("growth_habit"),
    )

    assert resolved == CAM_SUCCULENT_REST_SEQUENCE
    assert resolved == _TARGET_SEQUENCE[_SCIENTIFIC_NAME]
