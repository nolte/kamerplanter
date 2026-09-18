#!/usr/bin/env python3
"""Validate every seed YAML against the schema its own header declares.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_seed_schema.py                 # the whole seed tree
    python3 scripts/check_seed_schema.py <file> [...]    # the files pre-commit passes
    python3 scripts/check_seed_schema.py --json          # machine-readable

**The defect it closes (#1406).** Until this script existed the hook layer was an
opt-in list: ``.pre-commit-config.yaml`` carried twelve ``check-jsonschema``
hooks, eleven of them naming one seed file by an anchored regex and one globbing
``plant_info*.yaml``. Measured against the tree, that reached 20 of 36 seed files.
The backend unit test (``tests/unit/migrations/test_seed_schema_conformance.py``)
had already been converted to derive its corpus from the directive in each file's
header (#1030, #1435) and reaches all 32 declaring files, so the two enforcement
paths had *different reach*: a new seed file that declares its schema was checked
by the test and by no hook at all. Two gates over the same rule that disagree on
which files the rule covers is the failure shape this repository keeps paying
for — the narrower one reports green and the reader cannot tell which they are
looking at.

**One source of truth.** This module owns the corpus rules — the directive
pattern, :data:`NO_SCHEMA_DECLARED` and :data:`SCHEMA_DEBT_CEILING` — and the
conformance test imports them from here (by path, the way the other script tests
load their subject). The hook and the test therefore run the *same* discovery and
the *same* validator over the *same* registers, and cannot drift apart into two
reaches again.

What turns it red
-----------------

* a file that declares a schema and violates it beyond its recorded ceiling;
* a file that declares **no** schema and is not named in
  :data:`NO_SCHEMA_DECLARED` — silence must not be a way out of validation;
* a file named in :data:`NO_SCHEMA_DECLARED` that has since gained a directive
  (the register must not outlive what it records);
* a file with a ceiling that now validates cleanly — the debt is paid, the entry
  goes.

**Read the numbers, not the colour.** Green here means "no file is worse than
recorded", not "the seed data validates": twelve files carry a ceiling covering
1 158 known violations, each one a schema-behind-data gap named in the register
below.

Why validation runs in-process and not through ``check-jsonschema``
-------------------------------------------------------------------

The retired hooks shelled out to the ``check-jsonschema`` CLI with
``--base-uri file://./src/backend/app/migrations/seed_data/schemas/``, needed
because every schema declares a **bare** ``$id`` and four of them ``$ref`` a
sibling (``_defs.schema.yaml``). That CLI has no notion of a per-file ceiling, so
routing the twelve debt-carrying files through it would have meant either leaving
them unhooked (the status quo this change removes) or turning the gate red on
every commit that touches them. Building the same ``referencing`` registry the
test builds costs ~20 lines, keeps the two paths byte-identical in verdict, and
resolves the cross-file ``$ref`` without depending on a process working directory.

Traces to issue #1406 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import yaml

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2

#: Path of the seed directory relative to the checkout root.
SEED_DIR = Path("src/backend/app/migrations/seed_data")

#: ``# yaml-language-server: $schema=./schemas/<stem>.schema.yaml``
DIRECTIVE = re.compile(r"^#\s*yaml-language-server:\s*\$schema=\./schemas/([A-Za-z0-9_]+)\.schema\.yaml\s*$")

#: Seed files that deliberately declare no schema. Listed explicitly so that a new
#: file without a directive fails this check instead of disappearing from it.
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
    # change any more — it needs its own one-line data fix.
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


class SeedSchemaError(Exception):
    """Raised when the check cannot run at all (missing tree, unreadable schema)."""


@dataclass(frozen=True)
class Finding:
    """One reason a seed file is refused."""

    path: Path
    reason: str
    detail: str = ""

    def render(self) -> str:
        """Return the human line for this finding, indented detail included."""
        head = f"{self.path.as_posix()}: {self.reason}"
        if not self.detail:
            return head
        indented = "\n".join(f"    {line}" for line in self.detail.splitlines())
        return f"{head}\n{indented}"


def load_yaml(path: Path) -> Any:
    """Parse *path* with libyaml when it is available.

    The ``plant_info*`` family is 9 of the 36 seed files and the bulk of their
    bytes; measured over the whole tree the pure-Python parser costs 3.1 s and
    ``CSafeLoader`` 0.4 s, so the fast loader is most of this hook's runtime
    budget. ``yaml.safe_load`` is kept as the fallback for a PyYAML built without
    the C extension — same accepted dialect, only slower.
    """
    text = path.read_text(encoding="utf-8")
    loader = getattr(yaml, "CSafeLoader", None)
    if loader is None:
        return yaml.safe_load(text)
    return yaml.load(text, Loader=loader)


def find_repo_root(start: Path) -> Path:
    """Walk up from *start* to the checkout root, identified by its markers.

    A marker walk rather than ``parents[N]``: a hard-coded index silently breaks
    the moment this file moves, which has bitten this repository before
    (``backend_import_path_container_crash``).

    Args:
        start: Any path inside the checkout.

    Returns:
        The directory holding both ``Taskfile.yaml`` and ``scripts/``.

    Raises:
        SeedSchemaError: If no such directory is found.
    """
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    raise SeedSchemaError(f"no checkout root above {start} (looked for Taskfile.yaml + scripts/)")


def declared_schema(path: Path) -> str | None:
    """Return the schema stem the file's ``yaml-language-server`` directive names.

    Args:
        path: The seed YAML file to read.

    Returns:
        The schema stem, or ``None`` when the header declares no schema.
    """
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            match = DIRECTIVE.match(line.rstrip("\n"))
            if match:
                return match.group(1)
            if line.strip() and not line.lstrip().startswith("#"):
                # Directives are header comments; stop at the first content line.
                return None
    return None


def seed_files(seed_dir: Path) -> list[Path]:
    """Return every seed YAML in *seed_dir*, sorted, excluding the schemas folder."""
    return sorted(seed_dir.glob("*.yaml"))


@cache
def _registry(schemas_dir: Path) -> Any:
    """Return a ``referencing`` registry over every schema in *schemas_dir*.

    Built once per directory: the twelve schemas are re-parsed for every file
    otherwise, which is the difference between ~0.4 s and several seconds when the
    hook runs over the whole tree.
    """
    import referencing
    from referencing.jsonschema import DRAFT202012

    resources = []
    for schema_file in sorted(schemas_dir.glob("*.schema.yaml")):
        contents = load_yaml(schema_file)
        resources.append(
            (contents["$id"], referencing.Resource.from_contents(contents, default_specification=DRAFT202012))
        )
    return referencing.Registry().with_resources(resources)


@cache
def _validator(schema_stem: str, schemas_dir: Path) -> Any:
    """Return a Draft 2020-12 validator for *schema_stem*, resolved through the registry."""
    import jsonschema

    schema_file = schemas_dir / f"{schema_stem}.schema.yaml"
    if not schema_file.is_file():
        raise SeedSchemaError(f"declared schema does not exist: {schema_file.as_posix()}")
    schema = load_yaml(schema_file)
    return jsonschema.Draft202012Validator(schema, registry=_registry(schemas_dir))


def violations(path: Path, schema_stem: str, schemas_dir: Path) -> list[str]:
    """Return every schema violation of *path* against *schema_stem*, sorted by location.

    Args:
        path: The seed YAML file to validate.
        schema_stem: The schema stem the file declares.
        schemas_dir: Directory holding the ``*.schema.yaml`` files.

    Returns:
        One ``"<json path>: <message>"`` string per violation.
    """
    validator = _validator(schema_stem, schemas_dir)
    data = load_yaml(path) or {}
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    return [f"{list(e.absolute_path)}: {e.message}" for e in errors]


def check_files(paths: list[Path], schemas_dir: Path) -> list[Finding]:
    """Validate each seed file in *paths* against the schema it declares.

    Args:
        paths: Seed YAML files, as pre-commit passes them.
        schemas_dir: Directory holding the ``*.schema.yaml`` files.

    Returns:
        Every finding, in input order. Empty means green.
    """
    findings: list[Finding] = []
    for path in paths:
        stem = declared_schema(path)
        ceiling, debt = SCHEMA_DEBT_CEILING.get(path.name, (0, ""))
        if stem is None:
            if path.name not in NO_SCHEMA_DECLARED:
                findings.append(
                    Finding(
                        path,
                        "carries no '# yaml-language-server: $schema=./schemas/<stem>.schema.yaml' header directive",
                        "Add the directive (preferred), or name the file in NO_SCHEMA_DECLARED "
                        "in scripts/check_seed_schema.py — silence is not an opt-out.",
                    )
                )
            continue
        if path.name in NO_SCHEMA_DECLARED:
            findings.append(
                Finding(
                    path,
                    f"declares '{stem}.schema.yaml' but is still named in NO_SCHEMA_DECLARED",
                    "Remove the entry in scripts/check_seed_schema.py — the register must not outlive what it records.",
                )
            )
            # Still validated below: an entry going stale must not skip the file.
        errors = violations(path, stem, schemas_dir)
        if len(errors) > ceiling:
            headline = (
                f"{len(errors)} schema violations against {stem}.schema.yaml, above its recorded "
                f"ceiling of {ceiling} ({debt}) — fix the new ones, do not raise the ceiling"
                if ceiling
                else f"{len(errors)} schema violations against {stem}.schema.yaml"
            )
            findings.append(Finding(path, headline, "\n".join(errors[:15])))
        elif ceiling and not errors:
            findings.append(
                Finding(
                    path,
                    f"validates cleanly but still carries a SCHEMA_DEBT_CEILING entry ({ceiling}, {debt})",
                    "Remove it from scripts/check_seed_schema.py — the debt is paid.",
                )
            )
    return findings


def _resolve_targets(argv_paths: list[str], root: Path) -> list[Path]:
    """Return the seed files to check: the ones passed, or the whole tree."""
    seed_dir = root / SEED_DIR
    if not seed_dir.is_dir():
        raise SeedSchemaError(f"seed directory not found: {seed_dir.as_posix()}")
    if not argv_paths:
        return seed_files(seed_dir)
    resolved: list[Path] = []
    for raw in argv_paths:
        path = Path(raw)
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            raise SeedSchemaError(f"not a file: {raw}")
        resolved.append(path)
    return resolved


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("paths", nargs="*", help="seed YAML files to check (default: the whole seed tree)")
    parser.add_argument("--json", action="store_true", help="print the findings as JSON instead of the human report")
    parser.add_argument(
        "--seed-dir",
        default=None,
        help="override the seed directory (default: src/backend/app/migrations/seed_data under the checkout root)",
    )
    args = parser.parse_args(argv)

    try:
        root = find_repo_root(Path(__file__).parent)
        if args.seed_dir:
            seed_dir = Path(args.seed_dir).resolve()
            if not seed_dir.is_dir():
                raise SeedSchemaError(f"seed directory not found: {seed_dir.as_posix()}")
            targets = [Path(p).resolve() for p in args.paths] if args.paths else seed_files(seed_dir)
        else:
            targets = _resolve_targets(args.paths, root)
            seed_dir = root / SEED_DIR
        findings = check_files(targets, seed_dir / "schemas")
    except SeedSchemaError as exc:
        print(f"check_seed_schema: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        print(
            json.dumps(
                {
                    "checked": [p.name for p in targets],
                    "findings": [{"file": f.path.name, "reason": f.reason, "detail": f.detail} for f in findings],
                },
                indent=2,
            )
        )
        return EXIT_OK if not findings else EXIT_DEFECTS

    if not findings:
        return EXIT_OK
    print(f"check_seed_schema: {len(findings)} seed file(s) refused\n", file=sys.stderr)
    for finding in findings:
        print(finding.render(), file=sys.stderr)
    return EXIT_DEFECTS


if __name__ == "__main__":
    raise SystemExit(main())
