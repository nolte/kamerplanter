"""Guard the frost-sensitivity and propagation-method vocabulary in the
generated ``plant_info*.yaml`` seed data (issue #337).

The knowledge steckbriefe (``spec/knowledge/plants/*.md``) describe frost
sensitivity with the horticultural RHS vocabulary (``tender`` / ``half_hardy``)
and stem cuttings as ``cutting_stem``. The ``plant-info-to-seed-yaml`` agent
maps those onto the seed enums (``tender -> sensitive``, ``half_hardy ->
moderate``, ``cutting_stem -> cutting`` + a ``wood_stage``). That mapping used
to be a documented-but-unenforced convention — #337 was raised because a
straggler could slip through unnoticed.

This test locks it in: every ``frost_sensitivity`` and every
``propagation_configs[].method`` value that actually reaches the seed data must
be a member of its schema enum, and the un-mapped source-doc tokens
(``tender``/``half_hardy``/``cutting_stem``) must never appear as data values.
Comments are ignored automatically because the YAML is parsed, not grepped.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import app.migrations

_SEED = Path(app.migrations.__file__).parent / "seed_data"
_SCHEMA = _SEED / "schemas" / "plant_info.schema.yaml"
_PLANT_INFO_FILES = sorted(_SEED.glob("plant_info*.yaml"))

# Source-doc tokens that must be mapped away before reaching the seed data.
_FORBIDDEN_FROST = {"tender", "half_hardy", "half-hardy", "fully_hardy"}
_FORBIDDEN_PROP = {"cutting_stem"}


def _find_enum_containing(node: object, *required: str) -> set[str] | None:
    """Return the first ``enum`` list in a parsed schema that contains all
    ``required`` sentinel members (so the test tracks the schema without
    hard-coding a brittle property path)."""
    if isinstance(node, dict):
        enum = node.get("enum")
        if isinstance(enum, list) and all(r in enum for r in required):
            return {v for v in enum if isinstance(v, str)}
        for value in node.values():
            found = _find_enum_containing(value, *required)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_enum_containing(value, *required)
            if found is not None:
                return found
    return None


@pytest.fixture(scope="module")
def schema() -> dict:
    return yaml.safe_load(_SCHEMA.read_text())


@pytest.fixture(scope="module")
def frost_enum(schema: dict) -> set[str]:
    enum = _find_enum_containing(schema, "sensitive", "very_hardy")
    assert enum is not None, "frost_sensitivity enum not found in plant_info.schema.yaml"
    return enum


@pytest.fixture(scope="module")
def propagation_enum(schema: dict) -> set[str]:
    enum = _find_enum_containing(schema, "cutting", "self_seeding")
    assert enum is not None, "propagation method enum not found in plant_info.schema.yaml"
    return enum


def test_schema_enums_exclude_source_doc_tokens(frost_enum: set[str], propagation_enum: set[str]) -> None:
    """The schema itself must not have quietly adopted the source-doc tokens."""
    assert _FORBIDDEN_FROST.isdisjoint(frost_enum)
    assert _FORBIDDEN_PROP.isdisjoint(propagation_enum)


def _iter_species_records(data: dict):
    """Yield (label, record-dict) pairs for every species-like block that can
    carry ``frost_sensitivity`` / ``propagation_configs``.

    Both the ``species_enrichment`` map (keyed by scientific_name) *and* the
    ``new_species`` list carry these fields, so the guard must cover both — the
    ``new_species`` block holds the majority of the values.
    """
    enrichment = data.get("species_enrichment") or {}
    if isinstance(enrichment, dict):
        yield from enrichment.items()
    for entry in data.get("new_species") or []:
        if isinstance(entry, dict):
            yield entry.get("scientific_name", "<new_species>"), entry


@pytest.mark.parametrize("path", _PLANT_INFO_FILES, ids=lambda p: p.name)
def test_frost_sensitivity_values_are_enum_members(path: Path, frost_enum: set[str]) -> None:
    data = yaml.safe_load(path.read_text()) or {}
    offenders: list[str] = []
    for sci_name, enrichment in _iter_species_records(data):
        if not isinstance(enrichment, dict):
            continue
        value = enrichment.get("frost_sensitivity")
        if isinstance(value, str) and value not in frost_enum:
            offenders.append(f"{sci_name}: {value!r}")
    assert not offenders, f"{path.name} has non-enum frost_sensitivity values: {offenders}"


@pytest.mark.parametrize("path", _PLANT_INFO_FILES, ids=lambda p: p.name)
def test_propagation_methods_are_enum_members(path: Path, propagation_enum: set[str]) -> None:
    data = yaml.safe_load(path.read_text()) or {}
    offenders: list[str] = []
    for sci_name, enrichment in _iter_species_records(data):
        if not isinstance(enrichment, dict):
            continue
        for cfg in enrichment.get("propagation_configs") or []:
            method = cfg.get("method") if isinstance(cfg, dict) else None
            if isinstance(method, str) and method not in propagation_enum:
                offenders.append(f"{sci_name}: {method!r}")
    assert not offenders, f"{path.name} has non-enum propagation methods (e.g. cutting_stem): {offenders}"
