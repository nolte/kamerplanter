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
