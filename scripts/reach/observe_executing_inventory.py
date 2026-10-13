#!/usr/bin/env python3
"""Compare what the export and the erasure actually executed with each declared inventory (#1680).

Observation step of the ``personal-data-inventories`` reach probe (the #1622
class: two declared inventories of a subject's personal data, and the one that
executes is not the one that is maintained).

The executed enumeration is read from **ArangoDB's own query log**. The reach
stack tracks every query (slow-query threshold one microsecond) with its bind
variables and data sources, and the act helpers bracket their runs with marker
queries (``reach-marker:export:begin`` … ``reach-marker:erasure:end``). For each
bracket this script collects the collections the queries used — the entry's
``dataSources``, collection bind parameters (``@@collection``, ``@@edge``),
string bind values that name a collection (the traversal's target), and
collections spelled in the query text after ``IN`` / ``INTO`` — keeping only
queries of the phase's effect:

* export: queries that **project fields for disclosure** (``KEEP(``) — the shape
  of a personal-data read, as opposed to the request bookkeeping around it;
* erasure: queries that **write** — ArangoDB's ``modificationQuery`` flag, or
  ``REMOVE`` / ``UPDATE`` / ``REPLACE`` in the text where the flag is absent.

The declared inventories come from the running backend
(``declared_privacy_inventories.py``: the builders the executing paths call).

Output, one member per line (the runner compares; this script states no verdict):

* ``export-manifest`` — every collection the export manifest declares was named
  by a disclosure read during the export;
* ``erasure-plan`` — every collection the erasure plan declares was named by a
  write during the erasure;
* ``executed/<phase>=<n>`` — how many collections each phase named, always
  printed, so an empty log is an observation and never silence.

``--detail`` adds ``declared/<inventory>=<n>`` and
``missing/<inventory>/<collection>`` for every declared collection the executed
enumeration did not name.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, Arango, ReachError, read_stack, repo_root, run_in_backend  # noqa: E402

MARKER_BIND = "reach_marker"
_WRITE = re.compile(r"\b(REMOVE|UPDATE|REPLACE)\b")
_DISCLOSURE = re.compile(r"\bKEEP\s*\(")
_LITERAL_COLLECTION = re.compile(r"\b(?:IN|INTO)\s+([A-Za-z][A-Za-z0-9_-]*)\b")

#: Which declared inventory each phase's executed enumeration is compared with,
#: and which queries of the phase count.
PHASES = {
    "export": ("export-manifest", _DISCLOSURE),
    "erasure": ("erasure-plan", _WRITE),
}


def query_collections(entry: dict[str, Any], known: set[str]) -> set[str]:
    """Collections one tracked query used: ArangoDB's data sources, bind parameters, bound and literal names."""
    names: set[str] = {name for name in entry.get("dataSources") or [] if name in known}
    for name, value in (entry.get("bindVars") or {}).items():
        if isinstance(value, str) and (name.startswith("@") or value in known):
            names.add(value)
    names |= {match for match in _LITERAL_COLLECTION.findall(entry.get("query", "")) if match in known}
    return names


def _in_order(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Entries in execution order: by query id, which ArangoDB assigns increasing.

    ``started`` has a resolution of one second, too coarse to order a marker
    against the queries around it. Without numeric ids the log's own order stands.
    """
    if entries and all(str(entry.get("id", "")).isdigit() for entry in entries):
        return sorted(entries, key=lambda entry: int(entry["id"]))
    return list(entries)


def phase_window(entries: list[dict[str, Any]], phase: str) -> list[dict[str, Any]]:
    """The tracked queries between the phase's begin and end markers."""
    ordered = _in_order(entries)
    begin = end = None
    for index, entry in enumerate(ordered):
        marker = (entry.get("bindVars") or {}).get(MARKER_BIND)
        if marker == f"reach-marker:{phase}:begin":
            begin = index
        elif marker == f"reach-marker:{phase}:end" and begin is not None:
            end = index
    if begin is None or end is None:
        return []
    return ordered[begin + 1 : end]


def _has_effect(entry: dict[str, Any], phase: str, effect: re.Pattern[str]) -> bool:
    if phase == "erasure" and "modificationQuery" in entry:
        return bool(entry["modificationQuery"])  # ArangoDB's own classification of the query
    return bool(effect.search(entry.get("query", "")))


def executed(entries: list[dict[str, Any]], phase: str, effect: re.Pattern[str], known: set[str]) -> set[str]:
    names: set[str] = set()
    for entry in phase_window(entries, phase):
        if _has_effect(entry, phase, effect):
            names |= query_collections(entry, known)
    return names


def observe(
    entries: list[dict[str, Any]], declared: dict[str, list[str]], known: set[str], *, detail: bool = False
) -> list[str]:
    """Member lines for the tracked *entries* against the *declared* inventories (pure; unit-tested)."""
    lines: list[str] = []
    context: list[str] = []
    missing_lines: list[str] = []
    for phase, (inventory, effect) in PHASES.items():
        names = executed(entries, phase, effect, known)
        context.append(f"executed/{phase}={len(names)}")
        missing = sorted(set(declared.get(inventory, [])) - names)
        if names and not missing:
            lines.append(inventory)
        missing_lines.append(f"declared/{inventory}={len(declared.get(inventory, []))}")
        missing_lines += [f"missing/{inventory}/{name}" for name in missing]
    return lines + context + (missing_lines if detail else [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    parser.add_argument("--detail", action="store_true", help="list declared collections the run did not name")
    args = parser.parse_args(argv)
    try:
        arango = Arango(read_stack())
        entries = arango.slow_queries()
        known = arango.collections()
        script = repo_root() / "scripts" / "reach" / "declared_privacy_inventories.py"
        declared = json.loads(run_in_backend(script, "--subject", args.subject, timeout=120))
    except ReachError as exc:
        print(f"observe inventory: {exc}", file=sys.stderr)
        return 1
    for line in observe(entries, declared, known, detail=args.detail):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
