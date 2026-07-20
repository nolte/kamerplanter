"""Enforce Steckbrief <-> seed consistency for lifecycle-driving attributes.

Source-of-truth contract (Issue #680, master-data-capture-audit-2026-07 UR-2)
============================================================================

There is **no generator** that derives the seed YAMLs from the Steckbriefe.
The two sides are maintained by hand and had silently drifted (the audit found
14 ``growth_habit`` mismatches; the short-day ornamental cohort carried
``photoperiod_type`` only in the Steckbrief). This module makes the contract
explicit and machine-checked:

    **Seed-YAML = Source of Truth. Steckbrief (spec/knowledge/plants/*.md) =
    documentation that must follow the seed.**

The seed values drive the lifecycle resolver (REQ-003 §D14) and the migration
cohorts (v0027), so they are authoritative. When a Steckbrief disagrees, the
Steckbrief is the side that must be corrected -- never the seed -- unless the
disagreement is a *deliberate, documented* one (see ``ALLOWED_DISCREPANCIES``).

Five lifecycle-driving attributes are compared between the KA-field-anchored
tables in every ``spec/knowledge/plants/*.md`` and the seed YAMLs:

    growth_habit         species.yaml:species[] / plant_info*.yaml:new_species[]
    photosynthesis_type  species.yaml:species[] / plant_info*.yaml:new_species[]
    photoperiod_type     plant_info*.yaml:lifecycle_configs[<name>]
    flowering_strategy   species.yaml:lifecycle_overrides[<name>] / lifecycle_configs
    growth_determinacy   species.yaml:lifecycle_overrides[<name>] / lifecycle_configs

Parsing is anchored on the backtick KA-field reference in the third table
column (e.g. ``| Photoperiode | day_neutral | ``lifecycle_configs.photoperiod_type`` |``)
so it ignores the stale ``§8.1`` CSV import blocks and reads HTML-comment
annotations (``<!-- Quelle: ... -->``, ``<!-- KORREKTUR: ... -->``) out of the
value. ``DATEN FEHLEN`` / ``—`` cells count as "no value" (not a drift).

Multiple Steckbriefe may map onto one seeded species (``spp.`` aggregates,
cultivar sheets -- the intended 210->207 delta, audit §6); a Steckbrief whose
scientific name has no seed counterpart is skipped, never a false positive.

Usage
-----
As a standalone gate (exit code != 0 on any non-allowlisted drift)::

    python src/backend/app/migrations/seed_steckbrief_consistency.py
    python -m app.migrations.seed_steckbrief_consistency --verbose

The module has **no** intra-app imports (only stdlib + PyYAML) so it runs both
inside the backend test environment and in an isolated pre-commit venv.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Attribute -> the backtick-quoted KA-field reference that anchors its row in a
# Steckbrief table. Anchoring on the KA field (not a German label) is robust
# against label wording and skips the stale CSV import block entirely.
ATTR_ANCHORS: dict[str, str] = {
    "growth_habit": "species.growth_habit",
    "photoperiod_type": "lifecycle_configs.photoperiod_type",
    "photosynthesis_type": "species.photosynthesis_type",
    "flowering_strategy": "lifecycle_configs.flowering_strategy",
    "growth_determinacy": "lifecycle_configs.growth_determinacy",
}

_SCIENTIFIC_NAME_ANCHOR = "species.scientific_name"

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# Value cells that mean "no value recorded" -- these never count as a drift.
_MISSING_TOKENS = frozenset({"", "—", "-", "–", "n/a", "na", "df", "tbd", "?"})


@dataclass(frozen=True)
class AllowedDiscrepancy:
    """A deliberate, documented Steckbrief<->seed divergence that must not fail.

    Each entry pins the exact (name, attribute, both values) so the allowlist
    can never silently absorb a *different* future drift on the same attribute.
    """

    scientific_name: str
    attribute: str
    steckbrief_value: str
    seed_value: str
    reason: str
    source: str


# --------------------------------------------------------------------------- #
# Allowlist -- deliberate, documented divergences (do NOT break the build)
# --------------------------------------------------------------------------- #
#
# Every entry here is a case where the Steckbrief value is *documented biology*
# that intentionally differs from a *deliberate seed choice* (cohort binding /
# resolver routing). Aligning the doc to the seed would fight sourced botany, so
# the divergence is recorded transparently instead. Entries flagged
# "SEED-FIX PENDING" additionally propose a seed correction that is deferred
# because it needs botanical confirmation and/or would re-route the lifecycle
# resolver -- they are green here only so the gate is not blocked while the
# question is open (see the module report and Issue #680).
ALLOWED_DISCREPANCIES: tuple[AllowedDiscrepancy, ...] = (
    # -- photoperiod_type: short-day ornamental cohort (v0027 / PR #692) ------ #
    AllowedDiscrepancy(
        scientific_name="Stephanotis floribunda",
        attribute="photoperiod_type",
        steckbrief_value="day_neutral",
        seed_value="short_day",
        reason=(
            "Seed carries short_day to reproduce the v0027 photoperiodic_ornamental "
            "cohort binding; the Steckbrief documents day_neutral (bloom is driven by "
            "cool nights ~13-16 C, not day length). Deliberate cohort-vs-biology "
            "divergence -- do not fail. See PR #692 / Issue #676."
        ),
        source="NC State Extension Gardener Plant Toolbox; ourhouseplants; lifetips/Alibaba",
    ),
    AllowedDiscrepancy(
        scientific_name="Aphelandra squarrosa",
        attribute="photoperiod_type",
        steckbrief_value="day_neutral",
        seed_value="short_day",
        reason=(
            "Seed carries short_day for the v0027/PR #692 photoperiodic_ornamental "
            "cohort; the Steckbrief was corrected to day_neutral (bloom triggered by "
            "light intensity / ~3 months bright light, not day length). Same "
            "cohort-vs-documented-biology pattern as Stephanotis."
        ),
        source="aphelandra_squarrosa.md §1.1 Nachtrag (Steckbrief-Erweiterung 2026-06)",
    ),
    AllowedDiscrepancy(
        scientific_name="Jasminum polyanthum",
        attribute="photoperiod_type",
        steckbrief_value="day_neutral",
        seed_value="short_day",
        reason=(
            "Seed carries short_day for the v0027/PR #692 photoperiodic_ornamental "
            "cohort; the Steckbrief documents day_neutral (flower induction is "
            "temperature/cold driven, not photoperiodic). Cohort-vs-biology divergence."
        ),
        source="jasminum_polyanthum.md §1.1 (Steckbrief-Erweiterung 2026-06)",
    ),
    # -- photoperiod_type: CAM succulent routed by photosynthesis_type -------- #
    AllowedDiscrepancy(
        scientific_name="Crassula ovata",
        attribute="photoperiod_type",
        steckbrief_value="short_day",
        seed_value="day_neutral",
        reason=(
            "Crassula ovata is a CAM succulent routed via cam_succulent_rest by "
            "photosynthesis_type=cam, so the seed deliberately keeps photoperiod_type "
            "day_neutral (it is not part of the photoperiodic_ornamental cohort). The "
            "Steckbrief notes a short-day flowering *preference* in its requirement "
            "profiles; the lifecycle axis stays day_neutral by seed design."
        ),
        source="crassula_ovata.md §2.2; seed routing via photosynthesis_type=cam",
    ),
    # -- photoperiod_type: seed value likely stale (SEED-FIX PENDING) --------- #
    AllowedDiscrepancy(
        scientific_name="Nymphaea alba",
        attribute="photoperiod_type",
        steckbrief_value="day_neutral",
        seed_value="long_day",
        reason=(
            "SEED-FIX PENDING: the Steckbrief was sourced-corrected from long_day to "
            "day_neutral (bloom is water-temperature driven, not photoperiodic); the "
            "seed still carries the stale long_day. A seed correction to day_neutral is "
            "resolver-inert (neither value triggers the short_day rule) but is deferred "
            "for botanical confirmation. Allowlisted, not endorsed."
        ),
        source="nymphaea_alba.md §1.1 KORREKTUR (Steckbrief-Erweiterung 2026-06)",
    ),
    AllowedDiscrepancy(
        scientific_name="Brassica oleracea var. sabellica",
        attribute="photoperiod_type",
        steckbrief_value="day_neutral",
        seed_value="long_day",
        reason=(
            "SEED-FIX PENDING: kale bolts in year two by vernalization, not day length; "
            "the Steckbrief records day_neutral per the corpus convention for "
            "vernalization-driven species, while the seed carries long_day. Seed "
            "correction to day_neutral is resolver-inert but deferred for confirmation."
        ),
        source="brassica_oleracea_var_sabellica.md §1.1; PMC8866342 (vernalization/FLC)",
    ),
    AllowedDiscrepancy(
        scientific_name="Streptocarpus ionanthus",
        attribute="photoperiod_type",
        steckbrief_value="day_neutral",
        seed_value="long_day",
        reason=(
            "SEED-FIX PENDING: African violet is day-neutral for flower development; "
            "the Steckbrief was sourced-corrected from long_day to day_neutral, but the "
            "seed lifecycle_config still carries the stale long_day. Seed correction is "
            "resolver-inert and deferred for confirmation. (Steckbrief file: "
            "saintpaulia_ionantha.md; seed key uses the current name Streptocarpus.)"
        ),
        source="saintpaulia_ionantha.md §1.1 KORREKTUR (Steckbrief-Erweiterung 2026-06)",
    ),
    AllowedDiscrepancy(
        scientific_name="Petunia x hybrida",
        attribute="photoperiod_type",
        steckbrief_value="long_day",
        seed_value="day_neutral",
        reason=(
            "The Steckbrief documents Petunia as a facultative long-day plant (flowers "
            "under all day lengths, accelerated by long days; effectively day-neutral "
            "under cool culture), while the seed carries the simplified day_neutral that "
            "fits the free-flowering cultivated F1 hybrid. Documented-biology-vs-seed "
            "nuance; both values are resolver-inert (neither triggers the short_day rule)."
        ),
        source="petunia_x_hybrida.md §1.1 (facultative long-day plant)",
    ),
    # -- photosynthesis_type: documented CAM vs seed c3 (SEED-FIX PENDING) ---- #
    AllowedDiscrepancy(
        scientific_name="Dendrobium nobile",
        attribute="photosynthesis_type",
        steckbrief_value="cam",
        seed_value="c3",
        reason=(
            "SEED-FIX PENDING: the Steckbrief documents CAM for Dendrobium (sourced) "
            "while the seed carries c3. Correcting the seed to cam would re-route the "
            "lifecycle resolver toward cam_succulent_rest, so the change is deferred for "
            "botanical/behavioural confirmation. Allowlisted transparently, not endorsed."
        ),
        source="dendrobium_nobile.md §1.1; Zhang et al. 2019 J. Exp. Bot. 70(22):6611",
    ),
    AllowedDiscrepancy(
        scientific_name="Platycerium bifurcatum",
        attribute="photosynthesis_type",
        steckbrief_value="cam",
        seed_value="c3",
        reason=(
            "SEED-FIX PENDING: the Steckbrief documents facultative/weak CAM (and its "
            "note explicitly states the field is set to cam because the CAM component "
            "drives care behaviour), while the seed carries c3. A seed correction to cam "
            "would re-route the resolver; deferred for confirmation. Allowlisted, not "
            "endorsed."
        ),
        source="platycerium_bifurcatum.md §1.1 Hinweis; Rut et al. 2008; Wai et al. 2023",
    ),
)


# --------------------------------------------------------------------------- #
# Result types
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Drift:
    """A single attribute value that differs between Steckbrief and seed."""

    scientific_name: str
    attribute: str
    steckbrief_value: str
    seed_value: str
    steckbrief_file: str
    seed_source: str


@dataclass
class CheckResult:
    """Outcome of a full consistency check."""

    violations: list[Drift]
    allowlisted: list[Drift]
    unmatched_steckbriefe: list[str]
    obsolete_allowlist: list[AllowedDiscrepancy]

    @property
    def ok(self) -> bool:
        return not self.violations


# --------------------------------------------------------------------------- #
# Path resolution
# --------------------------------------------------------------------------- #


def repo_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` (default: this file) to the repository root.

    The root is the first ancestor that contains both the Steckbrief corpus and
    the seed data, so the tool works from a checkout regardless of cwd.
    """

    here = (start or Path(__file__)).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "spec" / "knowledge" / "plants").is_dir() and (
            candidate / "src" / "backend" / "app" / "migrations" / "seed_data"
        ).is_dir():
            return candidate
    raise RuntimeError("could not locate repository root (spec/ + seed_data/ not found)")


def _plants_dir(root: Path) -> Path:
    return root / "spec" / "knowledge" / "plants"


def _seed_dir(root: Path) -> Path:
    return root / "src" / "backend" / "app" / "migrations" / "seed_data"


# --------------------------------------------------------------------------- #
# Steckbrief parsing
# --------------------------------------------------------------------------- #


def _normalize_name(name: str) -> str:
    """Normalize a scientific name for cross-source matching."""

    return re.sub(r"\s+", " ", name.replace("×", "x")).strip()


def _clean_value(raw: str) -> str | None:
    """Extract the enum token from a Steckbrief value cell, or ``None``."""

    raw = _HTML_COMMENT.sub("", raw).strip()
    if not raw:
        return None
    if "daten" in raw.lower() and "fehlen" in raw.lower():
        return None
    # Drop any parenthetical / trailing prose after the enum token.
    head = re.split(r"[(,;/]", raw, maxsplit=1)[0].strip()
    tokens = head.split()
    if not tokens:
        return None
    token = tokens[0].strip("`*").lower()
    if token in _MISSING_TOKENS:
        return None
    return token


def _row_cells(line: str) -> list[str] | None:
    """Return the trimmed cells of a Markdown table row, or ``None``."""

    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    return [c.strip() for c in stripped.strip("|").split("|")]


def parse_steckbrief(path: Path) -> dict[str, str]:
    """Extract scientific name + the five lifecycle attributes from a Steckbrief.

    Values are read from the KA-field-anchored table rows only; the stale CSV
    import block (§8.1) is intentionally ignored.
    """

    text = path.read_text(encoding="utf-8")
    result: dict[str, str] = {}

    for line in text.splitlines():
        if f"`{_SCIENTIFIC_NAME_ANCHOR}`" not in line:
            continue
        cells = _row_cells(line)
        if cells and len(cells) >= 2:
            name = _HTML_COMMENT.sub("", cells[1]).strip()
            if name:
                result["scientific_name"] = _normalize_name(name)
        break

    for attr, anchor in ATTR_ANCHORS.items():
        for line in text.splitlines():
            if f"`{anchor}`" not in line:
                continue
            cells = _row_cells(line)
            if cells and len(cells) >= 2:
                value = _clean_value(cells[1])
                if value is not None:
                    result[attr] = value
            break

    return result


# --------------------------------------------------------------------------- #
# Seed parsing
# --------------------------------------------------------------------------- #


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _record(
    seed: dict[str, dict[str, tuple[str, str]]],
    name: str | None,
    attr: str,
    value: Any,
    source: str,
) -> None:
    if not name or value is None:
        return
    normalized = _normalize_name(str(name))
    seed.setdefault(normalized, {}).setdefault(attr, (str(value).strip().lower(), source))


def load_seed_attributes(seed_dir: Path) -> dict[str, dict[str, tuple[str, str]]]:
    """Build ``{scientific_name: {attribute: (value, source)}}`` from the seed YAMLs."""

    seed: dict[str, dict[str, tuple[str, str]]] = {}

    species_doc = _load_yaml(seed_dir / "species.yaml")
    for entry in species_doc.get("species", []) or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("scientific_name")
        _record(seed, name, "growth_habit", entry.get("growth_habit"), "species.yaml:species")
        _record(seed, name, "photosynthesis_type", entry.get("photosynthesis_type"), "species.yaml:species")
    override_src = "species.yaml:lifecycle_overrides"
    for name, override in (species_doc.get("lifecycle_overrides") or {}).items():
        if not isinstance(override, dict):
            continue
        _record(seed, name, "flowering_strategy", override.get("flowering_strategy"), override_src)
        _record(seed, name, "growth_determinacy", override.get("growth_determinacy"), override_src)

    for path in sorted(seed_dir.glob("plant_info*.yaml")):
        doc = _load_yaml(path)
        source = path.name
        for entry in doc.get("new_species", []) or []:
            if not isinstance(entry, dict):
                continue
            name = entry.get("scientific_name")
            _record(seed, name, "growth_habit", entry.get("growth_habit"), f"{source}:new_species")
            _record(seed, name, "photosynthesis_type", entry.get("photosynthesis_type"), f"{source}:new_species")
        lifecycle_configs = doc.get("lifecycle_configs") or {}
        if isinstance(lifecycle_configs, dict):
            config_src = f"{source}:lifecycle_configs"
            for name, config in lifecycle_configs.items():
                if not isinstance(config, dict):
                    continue
                _record(seed, name, "photoperiod_type", config.get("photoperiod_type"), config_src)
                _record(seed, name, "flowering_strategy", config.get("flowering_strategy"), config_src)
                _record(seed, name, "growth_determinacy", config.get("growth_determinacy"), config_src)

    return seed


# --------------------------------------------------------------------------- #
# Comparison
# --------------------------------------------------------------------------- #


def find_drifts(
    plants_dir: Path,
    seed: dict[str, dict[str, tuple[str, str]]],
) -> tuple[list[Drift], list[str]]:
    """Compare every Steckbrief against the seed map.

    Returns ``(drifts, unmatched_steckbriefe)``. A Steckbrief whose scientific
    name has no seed counterpart is reported as unmatched, never as a drift.
    """

    drifts: list[Drift] = []
    unmatched: list[str] = []

    for path in sorted(plants_dir.glob("*.md")):
        parsed = parse_steckbrief(path)
        name = parsed.get("scientific_name")
        if not name:
            continue
        seed_attrs = seed.get(name)
        if seed_attrs is None:
            unmatched.append(f"{path.name} ({name})")
            continue
        for attr in ATTR_ANCHORS:
            steckbrief_value = parsed.get(attr)
            seed_pair = seed_attrs.get(attr)
            if steckbrief_value is None or seed_pair is None:
                continue
            seed_value, seed_source = seed_pair
            if steckbrief_value != seed_value:
                drifts.append(
                    Drift(
                        scientific_name=name,
                        attribute=attr,
                        steckbrief_value=steckbrief_value,
                        seed_value=seed_value,
                        steckbrief_file=path.name,
                        seed_source=seed_source,
                    )
                )

    return drifts, unmatched


def _allowlist_index() -> dict[tuple[str, str], AllowedDiscrepancy]:
    return {(_normalize_name(a.scientific_name), a.attribute): a for a in ALLOWED_DISCREPANCIES}


def check(root: Path | None = None) -> CheckResult:
    """Run the full Steckbrief<->seed consistency check."""

    root = root or repo_root()
    seed = load_seed_attributes(_seed_dir(root))
    drifts, unmatched = find_drifts(_plants_dir(root), seed)

    allow = _allowlist_index()
    matched_keys: set[tuple[str, str]] = set()
    violations: list[Drift] = []
    allowlisted: list[Drift] = []

    for drift in drifts:
        key = (_normalize_name(drift.scientific_name), drift.attribute)
        entry = allow.get(key)
        if (
            entry is not None
            and entry.steckbrief_value.lower() == drift.steckbrief_value
            and entry.seed_value.lower() == drift.seed_value
        ):
            allowlisted.append(drift)
            matched_keys.add(key)
        else:
            violations.append(drift)

    obsolete = [
        a for a in ALLOWED_DISCREPANCIES if (_normalize_name(a.scientific_name), a.attribute) not in matched_keys
    ]

    return CheckResult(
        violations=sorted(violations, key=lambda d: (d.attribute, d.scientific_name)),
        allowlisted=sorted(allowlisted, key=lambda d: (d.attribute, d.scientific_name)),
        unmatched_steckbriefe=unmatched,
        obsolete_allowlist=obsolete,
    )


# --------------------------------------------------------------------------- #
# Reporting / CLI
# --------------------------------------------------------------------------- #


def format_report(result: CheckResult, *, verbose: bool = False) -> str:
    """Render a human-readable report of the check outcome."""

    lines: list[str] = []
    lines.append("Steckbrief <-> seed consistency (Issue #680)")
    lines.append("SSOT: seed YAML = source of truth, Steckbrief = documentation that follows it.")
    lines.append("")

    if result.violations:
        lines.append(f"DRIFT -- {len(result.violations)} non-allowlisted mismatch(es):")
        for d in result.violations:
            lines.append(
                f"  [{d.attribute}] {d.scientific_name}: steckbrief={d.steckbrief_value!r} "
                f"!= seed={d.seed_value!r} (seed: {d.seed_source}, doc: {d.steckbrief_file})"
            )
        lines.append("")
        lines.append("Fix: align the Steckbrief to the seed value, or add a documented")
        lines.append("ALLOWED_DISCREPANCIES entry in seed_steckbrief_consistency.py.")
    else:
        lines.append("OK -- no non-allowlisted drift.")

    if result.allowlisted:
        lines.append("")
        lines.append(f"Allowlisted (deliberate, documented) -- {len(result.allowlisted)}:")
        for d in result.allowlisted:
            lines.append(
                f"  [{d.attribute}] {d.scientific_name}: steckbrief={d.steckbrief_value!r} vs seed={d.seed_value!r}"
            )

    if result.obsolete_allowlist:
        lines.append("")
        lines.append(f"WARNING -- {len(result.obsolete_allowlist)} allowlist entr(y/ies) no longer match a drift:")
        for a in result.obsolete_allowlist:
            lines.append(f"  [{a.attribute}] {a.scientific_name} (remove or update this entry)")

    if verbose and result.unmatched_steckbriefe:
        count = len(result.unmatched_steckbriefe)
        lines.append("")
        lines.append(f"Steckbriefe without a seed counterpart (expected -- spp./cultivar sheets) -- {count}:")
        for item in result.unmatched_steckbriefe:
            lines.append(f"  {item}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns non-zero on any non-allowlisted drift."""

    parser = argparse.ArgumentParser(description="Enforce Steckbrief<->seed consistency (Issue #680).")
    parser.add_argument("--verbose", "-v", action="store_true", help="also list Steckbriefe without a seed counterpart")
    args = parser.parse_args(argv)

    result = check()
    print(format_report(result, verbose=args.verbose))
    return 1 if result.violations else 0


if __name__ == "__main__":
    sys.exit(main())
