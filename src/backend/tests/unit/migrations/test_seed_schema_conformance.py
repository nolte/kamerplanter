"""Validate every schema-declaring seed YAML against the schema it declares.

The seed files carry a ``# yaml-language-server: $schema=...`` directive, but
nothing enforced it — the schema had drifted from the data (wrong ``cultivars``
shape, over-strict enums, non-nullable fields, array-only edges, a stale
``seed_type`` enum, …), so ~428 latent violations had accumulated. This test
makes the directive real, with the cross-file ``$ref`` (``_defs.schema.yaml``)
resolved through a registry.

Discovery is derived, not hand-written (#1030)
==============================================

Until 2026-08-08 the parametrisation was a hand-written ``glob("plant_info*.yaml")``
plus two named files: 12 of the 31 schema-declaring seed files were checked, and
the other 19 were not — including ``adventskalender.yaml``, which declares
``plant_info.schema.yaml`` and fell through the glob purely because of its name.
It had accumulated 523 violations that nothing reported (audit 2026-08-08 §3
finding 11). A hand-maintained list makes a *new* file invisible by default,
which is the same fail-open shape as the tenant-scope guard's 6-entry list.

So the file→schema mapping is now read from the directive in each file's own
header. A new seed file that declares a schema is covered the moment it is
added; one that declares none has to be named in :data:`NO_SCHEMA_DECLARED`,
which fails closed rather than silently.

Recorded ceilings, not exemptions
=================================

Twelve files do not validate today. None of them is a *seed data* question this
module may settle — they are schema-vs-dialect gaps in areas this change does not
own (fertilizer/nutrient-plan phase entries, activity restrictions, workflow
phases). Skipping them would report green over 1 158 violations, so each carries
an explicit ceiling in :data:`SCHEMA_DEBT_CEILING` together with what the debt
*is*. The ceiling is a maximum: a file may improve freely, but the moment it
reaches zero the entry is reported as obsolete and must be removed, so the debt
register cannot outlive the debt. Same shape as ``ALLOWED_DISCREPANCIES`` in
``seed_steckbrief_consistency.py`` and as ``scripts/check_schema_examples.py``.

**Read the numbers, not the colour.** A green run here means "no file is worse
than recorded", not "the seed data validates".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

import app.migrations

_SEED = Path(app.migrations.__file__).parent / "seed_data"
_SCHEMAS = _SEED / "schemas"

#: ``# yaml-language-server: $schema=./schemas/<stem>.schema.yaml``
_DIRECTIVE = re.compile(r"^#\s*yaml-language-server:\s*\$schema=\./schemas/([A-Za-z0-9_]+)\.schema\.yaml\s*$")

#: Seed files that deliberately declare no schema. Listed explicitly so that a new
#: file without a directive fails this module instead of disappearing from it.
NO_SCHEMA_DECLARED: frozenset[str] = frozenset(
    {
        "fish_species.yaml",
        "glossary_terms.yaml",
        "hardiness_zones.yaml",
        "substrate_defaults.yaml",
        # "substrates.yaml" removed by #1152: it was the only one of the five that
        # is 636 lines of numeric agronomic data feeding two engines, and the
        # exemption was hiding three physically impossible records.
    }
)

#: file name -> (max tolerated violations, what the debt is).
#:
#: Every entry states the *shape* of the mismatch, so a reviewer can tell a known
#: gap from a new one without re-deriving it. Measured 2026-08-08 and re-measured
#: against the merged #1034 tree: every count is unchanged, because that change
#: corrected harvest/month *values* which were already schema-valid. A ceiling is a
#: maximum, so none of them can be lowered on this evidence.
SCHEMA_DEBT_CEILING: dict[str, tuple[int, str]] = {
    # One stray list item: ``- Lamiaceae`` at adventskalender.yaml:1277 was left
    # uncommented when the ``existing_families_needed`` block above it was commented
    # out, so YAML parses it as ``treatment_disease_edges[6]`` — a bare string where
    # the schema (and every sibling entry) has a ``[treatment, disease]`` pair. Inert
    # today: no Python reads ``treatment_disease_edges`` at all. It survived #1034,
    # which edited this file without touching the line, so it is not blocked on that
    # change any more — it needs its own one-line data fix (out of scope here: this
    # lane authors schemas, tests and backend logic, not seed data).
    "adventskalender.yaml": (1, "stray '- Lamiaceae' parsed as treatment_disease_edges[6]"),
    # The nutrient-plan dialect: phase entries carry ``product_name`` where the
    # schema requires ``fertilizer_product_name``, plus per-plan extras
    # (method_type/method_params, calcium_ppm/magnesium_ppm). One schema question
    # across five files, not five.
    "fertilizers.yaml": (129, "nutrient_plans[] phase-entry dialect + fertilizer storage/shelf-life fields"),
    "nutrient_plans_hydro.yaml": (362, "phase-entry dialect: product_name vs fertilizer_product_name"),
    "nutrient_plans_outdoor.yaml": (267, "nutrient_plans[] phase-entry dialect"),
    "nutrient_plans_ro.yaml": (92, "nutrient_plans[] phase-entry dialect"),
    "plagron.yaml": (182, "nutrient_plans[] phase-entry dialect"),
    "gardol.yaml": (71, "nutrient_plans[] phase-entry dialect + method_type/method_params"),
    # Unmodelled top-level and per-item keys.
    "activities.yaml": (22, "restricted_sub_phases + category values outside the activity_category enum"),
    "workflows.yaml": (31, "top-level workflow_phases + task_templates[].phase_name unmodelled"),
    "botanical_families.yaml": (2, "top-level rotation_edges + families[].nitrogen_fixing unmodelled"),
    "companion_planting.yaml": (1, "top-level family_compatible/family_incompatible unmodelled"),
    "harvest_indicators.yaml": (1, "indicator_type 'days_since_sowing' missing from the enum"),
}


def _declared_schema(path: Path) -> str | None:
    """Return the schema stem the file's ``yaml-language-server`` directive names."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            match = _DIRECTIVE.match(line.rstrip("\n"))
            if match:
                return match.group(1)
            if line.strip() and not line.lstrip().startswith("#"):
                # Directives are header comments; stop at the first content line.
                return None
    return None


def _seed_files() -> list[tuple[Path, str]]:
    """Return every ``(path, schema_stem)`` pair discovered from the directives."""
    return [(p, stem) for p in sorted(_SEED.glob("*.yaml")) if (stem := _declared_schema(p)) is not None]


_DECLARING_FILES = _seed_files()


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


def _violations(path: Path, schema_stem: str) -> list[str]:
    validator = _build_validator(schema_stem)
    data = yaml.safe_load(path.read_text()) or {}
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    return [f"{list(e.absolute_path)}: {e.message}" for e in errors]


def test_every_seed_file_either_declares_a_schema_or_is_named() -> None:
    """A new seed file must not be able to opt out of validation by silence."""
    declaring = {p.name for p, _ in _DECLARING_FILES}
    undeclared = {p.name for p in _SEED.glob("*.yaml")} - declaring
    unexpected = sorted(undeclared - NO_SCHEMA_DECLARED)
    assert not unexpected, (
        "Seed files carry no '# yaml-language-server: $schema=' directive and are not "
        "listed in NO_SCHEMA_DECLARED — add the directive (preferred) or name them:\n" + "\n".join(unexpected)
    )
    stale = sorted(NO_SCHEMA_DECLARED - undeclared)
    assert not stale, "NO_SCHEMA_DECLARED names files that now declare a schema (remove them):\n" + "\n".join(stale)


def test_schema_coverage_includes_the_files_the_glob_used_to_miss() -> None:
    """Negative control for the #1030 discovery fix.

    ``adventskalender.yaml`` declares ``plant_info.schema.yaml`` and was skipped for
    as long as the parametrisation was ``glob("plant_info*.yaml")``. Pinning it by
    name here means a regression to a name-shaped glob turns this red rather than
    quietly shrinking the corpus again.
    """
    covered = {p.name for p, _ in _DECLARING_FILES}
    for name in ("adventskalender.yaml", "species.yaml", "plant_info.yaml", "ipm.yaml", "workflows.yaml"):
        assert name in covered, f"{name} declares a schema but is not covered by the conformance sweep"
    assert len(covered) >= 31, f"expected the full schema-declaring corpus, discovered only {len(covered)}"


@pytest.mark.parametrize(("path", "schema_stem"), _DECLARING_FILES, ids=lambda v: v.name if isinstance(v, Path) else v)
def test_seed_file_matches_its_declared_schema(path: Path, schema_stem: str) -> None:
    ceiling, debt = SCHEMA_DEBT_CEILING.get(path.name, (0, ""))
    errors = _violations(path, schema_stem)
    detail = "\n".join(errors[:15])
    if ceiling:
        assert len(errors) <= ceiling, (
            f"{path.name} has {len(errors)} schema violations, above its recorded ceiling of "
            f"{ceiling} ({debt}). Fix the new ones — do not raise the ceiling:\n{detail}"
        )
        return
    assert not errors, f"{path.name} has {len(errors)} schema violations:\n{detail}"


def test_schema_debt_ceilings_are_still_needed() -> None:
    """A ceiling whose file now validates is obsolete and must be removed.

    Without this the register would outlive the debt, and the next file to regress
    into an already-listed name would land inside a ceiling nobody re-derived.
    """
    by_name = {p.name: stem for p, stem in _DECLARING_FILES}
    obsolete: list[str] = []
    unknown: list[str] = []
    for name, (ceiling, debt) in sorted(SCHEMA_DEBT_CEILING.items()):
        stem = by_name.get(name)
        if stem is None:
            unknown.append(name)
            continue
        count = len(_violations(Path(_SEED / name), stem))
        if count == 0:
            obsolete.append(f"{name} (ceiling {ceiling}, {debt}) now validates cleanly")
    assert not unknown, "SCHEMA_DEBT_CEILING names files that do not declare a schema:\n" + "\n".join(unknown)
    assert not obsolete, "Remove these SCHEMA_DEBT_CEILING entries — the debt is paid:\n" + "\n".join(obsolete)


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
# ``tenant_key`` is server-managed tenant ownership (#1090, the Cultivar pendant of
# ``Species.tenant_key``/#808). It belongs here rather than in the cultivar schema
# *by design*: a seed YAML file that could name an owning tenant would let data
# claim ownership of catalogue rows, and the seed path must stay a purely global
# write path (``tenant_key == ""``, pinned by
# ``test_seed_cultivar_global_tenant_key.py``). Adding the property to the schema
# to silence this guard would be the wrong fix.
_CULTIVAR_MODEL_RUNTIME_ONLY = {"key", "created_at", "updated_at", "origin", "tenant_key"}
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


# ── growing_periods: model ↔ schema (REQ-015-A, #1030) ────────────────────────
#
# ``growing_periods`` lived on the ``Species`` domain model and in the data
# (species.yaml Triticum aestivum, adventskalender.yaml Allium porrum) but in no
# schema — it survived on ``additionalProperties: true`` alone, so no
# schema-driven tool, template or authoring agent could see that a second
# cultivation window is expressible at all (audit 2026-08-08 §3 finding 9). Now
# that it is modelled, these two tests keep the definition and the model from
# drifting the way the cultivar shape once did.


def _growing_period_schema_properties() -> set[str]:
    schema = yaml.safe_load((_SCHEMAS / "_defs.schema.yaml").read_text())
    return set(schema["$defs"]["growing_period"]["properties"])


def test_growing_period_model_fields_have_schema_property() -> None:
    from app.domain.models.species import GrowingPeriod

    props = _growing_period_schema_properties()
    missing = sorted(set(GrowingPeriod.model_fields) - props)
    assert not missing, (
        "GrowingPeriod model fields without a growing_period schema property — a seed "
        "author cannot express these and a validator would reject them:\n" + "\n".join(missing)
    )


def test_growing_period_schema_properties_map_to_model() -> None:
    from app.domain.models.species import GrowingPeriod

    unexpected = sorted(_growing_period_schema_properties() - set(GrowingPeriod.model_fields))
    assert not unexpected, (
        "growing_period schema properties with no GrowingPeriod model field — the seed "
        "loader would drop these silently:\n" + "\n".join(unexpected)
    )


@pytest.mark.parametrize("schema_file", ["plant_info.schema.yaml", "species.schema.yaml"])
def test_species_schemas_expose_growing_periods(schema_file: str) -> None:
    """Both species-carrying schemas must offer the multi-window shape.

    Negative control for the finding: before #1030 this assertion failed on both
    files, which is precisely why a second cultivation window could not be authored
    through the pipeline.
    """
    schema = yaml.safe_load((_SCHEMAS / schema_file).read_text())
    species_def = schema["$defs"]["species"]
    assert "growing_periods" in species_def["properties"], (
        f"{schema_file} $defs.species does not model growing_periods — a species with two "
        "cultivation windows cannot be authored against it"
    )
    ref = species_def["properties"]["growing_periods"]["items"]["$ref"]
    assert ref == "_defs.schema.yaml#/$defs/growing_period", (
        f"{schema_file} must reuse the shared growing_period definition, got {ref!r}"
    )
