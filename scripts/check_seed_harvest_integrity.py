#!/usr/bin/env python3
"""Refuse seed species records whose harvest and month facts cannot be consumed.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_seed_harvest_integrity.py
    python3 scripts/check_seed_harvest_integrity.py --list   # name every record
    python3 scripts/check_seed_harvest_integrity.py --json   # machine-readable

Two invariants, one family
--------------------------

Both closed defects are the same shape: a seed record *asserts* something about
harvest or timing that no consumer can act on.

**A — ``allows_harvest`` without a harvest date (#1002).** ``allows_harvest:
true`` tells every consumer that a harvest exists, which makes every pre-harvest
safety interval (Karenz) a question that must be answered before a treatment is
recommended. A record supplying no harvest month gives that question no date to
resolve against, so the check is not "not applicable" — it is *undecidable*. A
conservative consumer then refuses every treatment carrying a non-zero
``safety_interval_days`` (on the reported *Dracaena reflexa* that excluded
Kaliseife, Neemöl and Pyrethrin — the whole biological-spray tier — for a plant
nobody eats). An optimistic one clears a treatment it cannot clear, which on a
plant that *is* harvested is a food-safety error rather than a gardening one.

**B — top-level months that are not the union of the growing periods (#1008).**
A species may carry several ``growing_periods`` (summer vs winter leek, spring
vs winter wheat) *and* flat top-level month lists. ``get_sowing_calendar`` reads
the periods; ``get_species_info`` hands out the flat fields. When the two
disagree, which one a consumer happens to read decides the answer. On *Allium
porrum* the flat ``direct_sow_months`` omitted ``[5, 6]`` — the entire sowing
window of the winter crop — so a consumer reading only the top level either
never sows it or sows it three months early.

Why the default matters more than the explicit values
-----------------------------------------------------

``app.domain.models.species.Species`` declares ``allows_harvest: bool = True``.
A seed record that simply *omits* the key is therefore loaded as
``allows_harvest=True`` — indistinguishable, at every consumer, from one that
states it. That is why invariant A is evaluated on the **effective** value
(:data:`ALLOWS_HARVEST_DEFAULT`) rather than on the literal YAML: on the tree
this check was written against, 44 of the 45 offending records carried no
``allows_harvest`` key at all, and a literal reading would have found one.

The constant is duplicated here rather than imported because this module must
run in an isolated pre-commit venv carrying nothing but PyYAML (the same
constraint ``seed_steckbrief_consistency.py`` works under). The duplication is
not left unguarded: ``tests/unit/test_seed_harvest_integrity_check.py`` asserts
it still equals the model's declared default, so flipping the model without
flipping this file goes red in the backend suite.

Why no numeric baseline
-----------------------

``check_schema_examples.py`` carries a recorded ceiling because its debt is real
and cannot be paid off in one change. This one has no debt after the data fix
that landed with it, so a ratchet would be dead machinery — and #973 recorded
what a hand-maintained count costs besides: every concurrent pull request that
moves the number edits the same line of the same file and conflicts on an
integer carrying no review value. Both invariants here are booleans. A record
either supplies a harvest date or it does not.

How a species record is assembled
---------------------------------

A consumer never sees one YAML record; it sees the merge the seeders produce:

1. **Base records** — ``species.yaml:species[]``, ``plant_info*.yaml:new_species[]``
   and ``adventskalender.yaml:new_species[]``.
2. **Enrichment** — ``<file>:species_enrichment[<name>]``. The seeders
   (``seed_plant_info.py``, ``seed_plant_info_extended.py``,
   ``seed_adventskalender.py``) apply an enrichment field only where the stored
   value is ``None`` / ``""`` / ``[]``, so enrichment *fills* and never
   overwrites. This module mirrors that fill-if-empty rule.

That merge is the point, not a convenience: #1008's *Allium porrum* is exactly a
record whose ``growing_periods`` come from one file (``adventskalender.yaml``)
and whose flat month lists come from another (``plant_info_outdoor_1.yaml``).
Neither file is wrong when read alone; only the merged record is.

What invariant B deliberately does not cover
--------------------------------------------

Only ``direct_sow_months`` and ``harvest_months`` are compared, and only when at
least one growing period carries a non-empty list for that field. ``bloom_months``
is excluded: the ``GrowingPeriod`` model carries it, but no seed record splits
bloom per period, so asserting union equality there would demand the value be
duplicated into every period to say nothing new. Where no period carries a field,
the top level is the only source and there is nothing to disagree with — silence
is the truthful result, not a missed finding. A check with false positives gets
suppressed within a week, and a suppressed check guards nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

#: Mirrors ``app.domain.models.species.Species.allows_harvest``'s declared
#: default. A seed record omitting the key is loaded with this value, so the
#: invariant is evaluated against it. Pinned by
#: ``tests/unit/test_seed_harvest_integrity_check.py``.
ALLOWS_HARVEST_DEFAULT = True

#: Mapping keys under which a *base* species record may appear.
BASE_RECORD_KEYS = ("species", "new_species")

#: Mapping key holding fill-if-empty enrichment, addressed by scientific name.
ENRICHMENT_KEY = "species_enrichment"

#: Month fields compared between the top level and the union of the periods.
UNION_FIELDS = ("direct_sow_months", "harvest_months")

#: Values the seeders treat as "no value recorded" when applying enrichment.
_EMPTY = (None, "", [], {})


# --------------------------------------------------------------------------- #
# Findings
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Finding:
    """One violated invariant on one merged species record."""

    scientific_name: str
    invariant: str
    detail: str
    sources: tuple[str, ...]

    def render(self) -> str:
        """Return a one-line, reviewable rendering of the finding."""
        where = ", ".join(self.sources) or "<unknown>"
        return f"{self.scientific_name}: {self.detail}  [{self.invariant}; {where}]"


@dataclass
class MergedSpecies:
    """A species as a consumer sees it: base records plus fill-if-empty enrichment."""

    scientific_name: str
    fields: dict[str, Any] = field(default_factory=dict)
    #: field name -> the seed file the surviving value came from
    origin: dict[str, str] = field(default_factory=dict)

    @property
    def sources(self) -> tuple[str, ...]:
        """Return the seed files that contributed a surviving value, in order."""
        seen: dict[str, None] = {}
        for name in self.origin.values():
            seen.setdefault(name, None)
        return tuple(seen)

    def absorb(self, values: dict[str, Any], source: str) -> None:
        """Fill fields that are absent or empty, mirroring the seeders' rule.

        Args:
            values: The record (or enrichment block) to merge in.
            source: The seed file name the values came from.
        """
        for key, value in values.items():
            if key not in self.fields or self.fields[key] in _EMPTY:
                self.fields[key] = value
                self.origin[key] = source


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


def _month_list(value: Any) -> list[int]:
    """Coerce a YAML month field to a list of ints, tolerating null and scalars."""
    if isinstance(value, list):
        return [m for m in value if isinstance(m, int)]
    return []


def load_seed_species(seed_dir: Path) -> dict[str, MergedSpecies]:
    """Merge every species record in *seed_dir* the way the seeders do.

    Args:
        seed_dir: The ``seed_data`` directory holding the YAML files.

    Returns:
        Scientific name -> merged record, in first-seen order.

    Raises:
        FileNotFoundError: If *seed_dir* does not exist.
    """
    if not seed_dir.is_dir():
        raise FileNotFoundError(f"seed data directory not found: {seed_dir}")

    merged: dict[str, MergedSpecies] = {}
    documents: list[tuple[str, dict[str, Any]]] = []

    for path in sorted(seed_dir.glob("*.yaml")):
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if isinstance(data, dict):
            documents.append((path.name, data))

    # Base records first: enrichment fills gaps, it never creates a species.
    for name, data in documents:
        for key in BASE_RECORD_KEYS:
            for record in data.get(key) or []:
                if not isinstance(record, dict):
                    continue
                scientific_name = record.get("scientific_name")
                if not isinstance(scientific_name, str) or not scientific_name:
                    continue
                entry = merged.setdefault(scientific_name, MergedSpecies(scientific_name))
                entry.absorb(record, name)

    for name, data in documents:
        for scientific_name, values in (data.get(ENRICHMENT_KEY) or {}).items():
            if not isinstance(values, dict):
                continue
            entry = merged.get(scientific_name)
            if entry is None:
                # The seeders log ``enrichment_species_not_found`` and move on;
                # an orphan enrichment block seeds nothing and is not this
                # check's business.
                continue
            entry.absorb(values, name)

    return merged


# --------------------------------------------------------------------------- #
# Invariants
# --------------------------------------------------------------------------- #


def _periods(entry: MergedSpecies) -> list[dict[str, Any]]:
    """Return the record's growing periods, ignoring malformed entries."""
    raw = entry.fields.get("growing_periods")
    if not isinstance(raw, list):
        return []
    return [period for period in raw if isinstance(period, dict)]


def check_harvest_data_present(entry: MergedSpecies) -> Finding | None:
    """Invariant A: an effective ``allows_harvest`` needs a harvest month (#1002).

    Args:
        entry: The merged species record.

    Returns:
        A finding when the record claims a harvest it supplies no date for.
    """
    declared = entry.fields.get("allows_harvest")
    effective = ALLOWS_HARVEST_DEFAULT if declared is None else bool(declared)
    if not effective:
        return None

    if _month_list(entry.fields.get("harvest_months")):
        return None
    if any(_month_list(period.get("harvest_months")) for period in _periods(entry)):
        return None

    stated = "allows_harvest: true" if declared is True else "allows_harvest defaulted to true"
    return Finding(
        scientific_name=entry.scientific_name,
        invariant="allows-harvest-without-harvest-months",
        detail=(
            f"{stated} but no harvest_months (neither top level nor in any growing "
            f"period) — every pre-harvest interval is undecidable. Set "
            f"allows_harvest: false for an ornamental, or add the harvest months "
            f"from its Steckbrief."
        ),
        sources=entry.sources,
    )


def check_top_level_is_period_union(entry: MergedSpecies) -> list[Finding]:
    """Invariant B: flat month fields equal the union of the periods (#1008).

    Args:
        entry: The merged species record.

    Returns:
        One finding per disagreeing month field; empty when they agree.
    """
    periods = _periods(entry)
    if not periods:
        return []

    findings: list[Finding] = []
    for name in UNION_FIELDS:
        union: set[int] = set()
        for period in periods:
            union |= set(_month_list(period.get(name)))
        if not union:
            # No period carries this field — the top level is the only source.
            continue

        top = set(_month_list(entry.fields.get(name)))
        if top == union:
            continue

        missing = sorted(union - top)
        extra = sorted(top - union)
        parts = []
        if missing:
            parts.append(f"missing from the top level: {missing}")
        if extra:
            parts.append(f"present only at the top level: {extra}")
        findings.append(
            Finding(
                scientific_name=entry.scientific_name,
                invariant="top-level-months-not-period-union",
                detail=(
                    f"{name} top level {sorted(top)} != union of "
                    f"{len(periods)} growing_periods {sorted(union)} — " + "; ".join(parts)
                ),
                sources=entry.sources,
            )
        )
    return findings


def collect_findings(entries: Iterable[MergedSpecies]) -> list[Finding]:
    """Run both invariants over *entries* and return every violation."""
    findings: list[Finding] = []
    for entry in entries:
        harvest = check_harvest_data_present(entry)
        if harvest is not None:
            findings.append(harvest)
        findings.extend(check_top_level_is_period_union(entry))
    return findings


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _default_seed_dir() -> Path:
    """Locate ``seed_data`` from this script's position in the checkout."""
    return Path(__file__).resolve().parent.parent / "src/backend/app/migrations/seed_data"


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns 0 when both invariants hold, 1 otherwise."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--seed-dir",
        type=Path,
        default=_default_seed_dir(),
        help="seed_data directory to check (default: the one in this checkout)",
    )
    parser.add_argument("--list", action="store_true", help="name every record checked")
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = parser.parse_args(argv)

    entries = load_seed_species(args.seed_dir)
    findings = collect_findings(entries.values())

    if args.json:
        print(
            json.dumps(
                {
                    "species_checked": len(entries),
                    "findings": [
                        {
                            "scientific_name": f.scientific_name,
                            "invariant": f.invariant,
                            "detail": f.detail,
                            "sources": list(f.sources),
                        }
                        for f in findings
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1 if findings else 0

    if args.list:
        for name in entries:
            print(f"  checked: {name}")

    if not findings:
        print(f"OK: {len(entries)} seed species records — harvest and month facts are consumable.")
        return 0

    print(f"FAIL: {len(findings)} finding(s) over {len(entries)} seed species records.\n")
    for finding in findings:
        print(f"  - {finding.render()}")
    print(
        "\nEach record above asserts a harvest or sowing fact no consumer can act on.\n"
        "The Steckbrief (spec/knowledge/plants/*.md) settles which correction is right;\n"
        "never invent harvest months to clear this check."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
