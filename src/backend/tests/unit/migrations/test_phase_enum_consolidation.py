"""Guards the consolidated phase-name enum (issue #307).

The 53-value phase vocabulary lives in exactly one place —
``_defs.schema.yaml#/$defs/phase_name`` — and the plant-data seed schemas
(``plant_info`` / ``lifecycles`` / ``fertilizers``) reference it via a cross-file
``$ref`` instead of inline-duplicating it. The reduced task-phase subset in
``activities`` / ``workflows`` is intentionally left inline (out of scope).

The structural assertions are dependency-free (PyYAML only) so they always run in
CI; the runtime ``$ref``-resolution check uses ``jsonschema`` + ``referencing``
via ``importorskip`` so it adds value where those are installed without making
them a hard test dependency.
"""

from pathlib import Path

import pytest
import yaml

import app.migrations

SCHEMAS = Path(app.migrations.__file__).parent / "seed_data" / "schemas"
PHASE_REF = "_defs.schema.yaml#/$defs/phase_name"
CONSUMERS = ("plant_info", "lifecycles", "fertilizers")
REDUCED = ("activities", "workflows")
CANONICAL = (
    "germination",
    "rooting",
    "bolting",
    "bud_break",
    "fruit_development",
    "winter_rest",
    "harvest",
    "repotting_recovery",
)


def _text(name: str) -> str:
    return (SCHEMAS / f"{name}.schema.yaml").read_text()


def _load(name: str) -> dict:
    return yaml.safe_load(_text(name))


def test_defs_is_the_single_phase_name_source() -> None:
    enum = _load("_defs")["$defs"]["phase_name"]["enum"]
    assert len(enum) == 53
    assert len(enum) == len(set(enum)), "phase_name enum has duplicates"
    for value in CANONICAL:
        assert value in enum, f"canonical phase '{value}' missing from _defs phase_name"


@pytest.mark.parametrize("name", CONSUMERS)
def test_consumer_schemas_reference_shared_enum(name: str) -> None:
    text = _text(name)
    assert PHASE_REF in text, f"{name}.schema.yaml must $ref the shared phase_name"
    assert "germination, seedling, vegetative" not in text, (
        f"{name}.schema.yaml still inlines the phase enum instead of $ref"
    )


@pytest.mark.parametrize("name", REDUCED)
def test_reduced_task_phase_enums_untouched(name: str) -> None:
    # activities/workflows keep their reduced inline subset — deliberately out of
    # scope for the consolidation (issue #307).
    text = _text(name)
    assert PHASE_REF not in text, f"{name}.schema.yaml should keep its reduced inline enum"
    assert "germination" in text


def test_phase_name_ref_resolves_and_enforces() -> None:
    """Runtime check: the cross-file $ref resolves under a Draft 2020-12
    validator and actually enforces the enum (invalid phase rejected)."""
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    from referencing.jsonschema import DRAFT202012

    registry = referencing.Registry().with_resources(
        [
            (
                _load(sf.stem.replace(".schema", ""))["$id"],
                referencing.Resource.from_contents(yaml.safe_load(sf.read_text()), default_specification=DRAFT202012),
            )
            for sf in SCHEMAS.glob("*.schema.yaml")
        ]
    )

    resolved = registry.resolver().lookup(PHASE_REF)
    assert len(resolved.contents["enum"]) == 53

    # The plant_info phase_entry.name must accept a valid phase and reject an
    # invalid one through the resolved $ref.
    schema = _load("plant_info")
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    good = {
        "growth_phases": {
            "Test species": [
                {
                    "name": "winter_rest",
                    "display_name": "Winterruhe",
                    "duration_days": 90,
                    "sequence_order": 1,
                    "stress_tolerance": "low",
                    "allows_harvest": False,
                    "is_terminal": False,
                }
            ]
        }
    }
    assert not any(e.absolute_path and e.absolute_path[-1] == "name" for e in validator.iter_errors(good))

    bad = {
        "growth_phases": {
            "Test species": [
                {
                    "name": "not_a_real_phase",
                    "display_name": "x",
                    "duration_days": 1,
                    "sequence_order": 1,
                    "stress_tolerance": "low",
                    "allows_harvest": False,
                    "is_terminal": False,
                }
            ]
        }
    }
    assert any(list(e.absolute_path)[-1:] == ["name"] for e in validator.iter_errors(bad)), (
        "invalid phase name was not rejected via the $ref"
    )
