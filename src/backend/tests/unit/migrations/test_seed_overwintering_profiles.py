"""Validate the overwintering-profile-template seed data (REQ-022).

Covers, without touching the database:

* every entry validates against ``OverwinteringProfileTemplate``;
* ``_key`` values are unique and slug-shaped;
* the file conforms to ``overwintering_profiles.schema.yaml``;
* the committed file matches a fresh extractor run (no manual drift);
* the new collection is registered and the migration imports cleanly.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

import app.migrations
from app.data_access.arango import collections as col
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate

_SEED = Path(app.migrations.__file__).parent / "seed_data"
_SCHEMAS = _SEED / "schemas"
_YAML = _SEED / "overwintering_profiles.yaml"
_REPO_ROOT = Path(app.migrations.__file__).parents[4]
_SCRIPT = _REPO_ROOT / "scripts" / "extract_overwintering_templates.py"


def _entries() -> list[dict]:
    data = yaml.safe_load(_YAML.read_text()) or {}
    return data["overwintering_profiles"]


def test_seed_file_exists_and_non_empty():
    entries = _entries()
    assert len(entries) > 100, "expected the bulk of the 210 Steckbriefe to yield a template"


def test_every_entry_validates_against_model():
    errors = []
    for entry in _entries():
        try:
            OverwinteringProfileTemplate.model_validate(entry)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{entry.get('_key')}: {str(exc).splitlines()[0]}")
    assert not errors, "model validation errors:\n" + "\n".join(errors)


def test_keys_are_unique_and_slug_shaped():
    keys = [e["_key"] for e in _entries()]
    assert len(keys) == len(set(keys)), "duplicate _key values"
    assert all(k == k.lower() and " " not in k for k in keys)


def test_no_min_greater_than_max():
    for e in _entries():
        lo, hi = e.get("winter_quarter_temp_min"), e.get("winter_quarter_temp_max")
        if lo is not None and hi is not None:
            assert lo <= hi, f"{e['_key']}: temp_min {lo} > temp_max {hi}"


def test_seed_matches_schema():
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
    schema = yaml.safe_load((_SCHEMAS / "overwintering_profiles.schema.yaml").read_text())
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    data = yaml.safe_load(_YAML.read_text())
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    formatted = [f"{list(e.absolute_path)}: {e.message}" for e in errors[:15]]
    assert not errors, f"{len(errors)} schema violations:\n" + "\n".join(formatted)


def test_generated_file_is_not_stale():
    """The committed YAML must equal a fresh extractor run (regen, don't hand-edit)."""
    spec = importlib.util.spec_from_file_location("_owx_extractor", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fresh, _entries_list, _warnings = module.build()
    assert fresh == _YAML.read_text(), (
        "overwintering_profiles.yaml is stale — re-run `python3 scripts/extract_overwintering_templates.py`"
    )


def test_collection_registered():
    assert col.OVERWINTERING_PROFILE_TEMPLATES == "overwintering_profile_templates"
    assert col.OVERWINTERING_PROFILE_TEMPLATES in col.DOCUMENT_COLLECTIONS


def test_migration_imports():
    from app.migrations.seed_overwintering_profiles import run_seed_overwintering_profiles

    assert callable(run_seed_overwintering_profiles)
