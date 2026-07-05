"""Validate the plant-data seed YAML against its JSON Schema.

The seed files carry a ``# yaml-language-server: $schema=...`` directive, but
nothing enforced it — the schema had drifted from the data (wrong ``cultivars``
shape, over-strict enums, non-nullable fields, array-only edges, a stale
``seed_type`` enum, …), so ~428 latent violations had accumulated. This test
makes the directive real: every ``plant_info*.yaml`` must validate against
``plant_info.schema.yaml`` and ``species.yaml`` against ``species.schema.yaml``,
with the cross-file ``$ref`` (``_defs.schema.yaml``) resolved through a registry.

Keeping this green means the schema and the seed data cannot silently diverge
again.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import app.migrations

_SEED = Path(app.migrations.__file__).parent / "seed_data"
_SCHEMAS = _SEED / "schemas"
_PLANT_INFO_FILES = sorted(_SEED.glob("plant_info*.yaml"))


def _build_validator(schema_stem: str):
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    from referencing.jsonschema import DRAFT202012

    registry = referencing.Registry().with_resources(
        [
            (
                yaml.safe_load(sf.read_text())["$id"],
                referencing.Resource.from_contents(yaml.safe_load(sf.read_text()), default_specification=DRAFT202012),
            )
            for sf in _SCHEMAS.glob("*.schema.yaml")
        ]
    )
    schema = yaml.safe_load((_SCHEMAS / f"{schema_stem}.schema.yaml").read_text())
    return jsonschema.Draft202012Validator(schema, registry=registry)


@pytest.mark.parametrize("path", _PLANT_INFO_FILES, ids=lambda p: p.name)
def test_plant_info_seed_matches_schema(path: Path) -> None:
    validator = _build_validator("plant_info")
    data = yaml.safe_load(path.read_text()) or {}
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    formatted = [f"{list(e.absolute_path)}: {e.message}" for e in errors[:15]]
    assert not errors, f"{path.name} has {len(errors)} schema violations:\n" + "\n".join(formatted)


def test_species_seed_matches_schema() -> None:
    validator = _build_validator("species")
    data = yaml.safe_load((_SEED / "species.yaml").read_text()) or {}
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    formatted = [f"{list(e.absolute_path)}: {e.message}" for e in errors[:15]]
    assert not errors, f"species.yaml has {len(errors)} schema violations:\n" + "\n".join(formatted)


# ── Model ↔ schema field consistency (issue #302, drift B5.6) ──────────────────
#
# Data ↔ schema conformance (above) does not catch a field that lives on the
# Cultivar domain model but is missing from the cultivar schema — such a field is
# silently dropped by the seed loader (this is exactly how ``breeding_year`` used
# to be lost). This test pins the cultivar schema and the ``Cultivar`` model to
# the same field set in both directions.

# Model fields that are never carried in the seed YAML (persistence/runtime only).
# ``origin`` is a derived data-provenance marker (REQ-011/#367): it defaults to
# ``system`` for seed data and is set by the enrichment engine / create endpoints,
# never sourced from the seed YAML.
_CULTIVAR_MODEL_RUNTIME_ONLY = {"key", "created_at", "updated_at", "origin"}
# The model's ``species_key`` is supplied through the seed-format map key ``species_name``.
_CULTIVAR_FIELD_ALIASES = {"species_key": "species_name"}
# Schema properties that are intentionally descriptive-only (no model counterpart,
# tolerated by ``additionalProperties: true``). Keep this list explicit so a new
# property that *should* be on the model cannot be added unnoticed.
_CULTIVAR_SCHEMA_FREEFORM_ONLY = {
    "species_name",
    "description",
    "cycle_type",
    "photoperiod_type",
    "typical_yield",
    "flavor_profile",
    "flower_color",
    "fruit_color",
    "notes",
    "tags",
}


def _cultivar_schema_properties() -> set[str]:
    schema = yaml.safe_load((_SCHEMAS / "plant_info.schema.yaml").read_text())
    return set(schema["$defs"]["cultivar"]["properties"])


def test_cultivar_model_fields_have_schema_property() -> None:
    from app.domain.models.species import Cultivar

    props = _cultivar_schema_properties()
    missing = []
    for field in sorted(set(Cultivar.model_fields) - _CULTIVAR_MODEL_RUNTIME_ONLY):
        expected = _CULTIVAR_FIELD_ALIASES.get(field, field)
        if expected not in props:
            missing.append(f"{field} -> expected schema property '{expected}'")
    assert not missing, (
        "Cultivar model fields without a cultivar schema property (schema↔model drift; "
        "the seed loader would silently drop these):\n" + "\n".join(missing)
    )


def test_cultivar_schema_properties_map_to_model() -> None:
    from app.domain.models.species import Cultivar

    model_fields = set(Cultivar.model_fields) - _CULTIVAR_MODEL_RUNTIME_ONLY
    unexpected = []
    for prop in sorted(_cultivar_schema_properties()):
        if prop in _CULTIVAR_SCHEMA_FREEFORM_ONLY:
            continue
        if prop not in model_fields:
            unexpected.append(prop)
    assert not unexpected, (
        "Cultivar schema properties with no Cultivar model field and not declared "
        "free-form (add to the model or to _CULTIVAR_SCHEMA_FREEFORM_ONLY):\n" + "\n".join(unexpected)
    )
