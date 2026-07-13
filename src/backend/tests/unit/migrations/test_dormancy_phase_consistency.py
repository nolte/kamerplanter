"""Guard the lifecycle master-data invariant that every species declaring
``dormancy_required: true`` also carries a real dormancy phase model (WP-8, #565).

The perennial-outdoor analysis (``spec/analysis/perennial-outdoor-lifecycle-modelling.md``)
found species that declared ``dormancy_required`` but had **no** dormancy phase in
their phase model — either no ``growth_phases`` at all (10 outdoor stubs) or, on the
seed level, no phase sequence carrying a dormancy phase. Such a flag can never fire
because the phase machine has nothing to transition into.

This test locks the sweep in: for every species with ``dormancy_required: true`` in
any ``lifecycle_configs`` block (``plant_info*.yaml`` / ``adventskalender.yaml``) or in
``lifecycles_outdoor.yaml``, a dormancy-type phase must be reachable through **one** of:

* its ``plant_info`` ``growth_phases`` list, or
* its ``lifecycles_outdoor`` inline ``phases`` list, or
* the ``phase_sequence`` it is bound to in ``lifecycles_outdoor.yaml``.

A *dormancy-type* phase is any member of :data:`_DORMANCY_PHASES` — the flag does not
require the literal ``dormancy`` name, because botanically distinct rest phases
(``winter_rest``/``cool_rest``/``summer_dormancy``/``dry_storage`` …) are legitimate
dormancy models and must not be collapsed to one name.

The YAML is parsed, not grepped, so comments and structure variants are handled.
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

import yaml

import app.migrations

_SEED = Path(app.migrations.__file__).parent / "seed_data"

# Phase names that constitute a genuine dormancy / rest model. All are members of
# the canonical ``phase_name`` enum in ``schemas/_defs.schema.yaml``.
_DORMANCY_PHASES = frozenset(
    {
        "dormancy",
        "winter_rest",
        "cool_rest",
        "summer_rest",
        "winter_dormancy",
        "summer_dormancy",
        "dry_storage",
        "winter_hull_change",
        "rest_phase",
        "rest",
        "rest_after_bloom",
    }
)


def _phase_names(phases: object) -> list[str]:
    """Extract phase names from a growth-phase list, tolerating both the flat
    (``- name: dormancy``) and the nested (``- phase: {name: dormancy}``) shapes
    that appear across the seed files."""
    names: list[str] = []
    if not isinstance(phases, list):
        return names
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        if "name" in phase:
            names.append(phase["name"])
        elif isinstance(phase.get("phase"), dict):
            names.append(phase["phase"].get("name"))
    return names


def _load(name: str) -> dict:
    data = yaml.safe_load((_SEED / name).read_text())
    return data if isinstance(data, dict) else {}


def _collect() -> tuple[
    dict[str, str],
    dict[str, list[str]],
    dict[str, tuple[str | None, list[str]]],
    dict[str, set[str]],
]:
    """Return (dormancy_required species -> source file, growth_phases,
    outdoor lifecycles, phase_sequence -> phase-name set)."""
    dorm_required: dict[str, str] = {}
    growth_phases: dict[str, list[str]] = {}
    outdoor: dict[str, tuple[str | None, list[str]]] = {}

    seq_phase_names: dict[str, set[str]] = {}
    for seq in _load("phase_sequences.yaml").get("phase_sequences", []):
        seq_phase_names[seq["name"]] = {e["phase_name"] for e in seq.get("entries", [])}

    for path in sorted(glob.glob(str(_SEED / "*.yaml"))):
        base = os.path.basename(path)
        if base == "lifecycles_outdoor.yaml":
            continue
        data = yaml.safe_load(Path(path).read_text())
        if not isinstance(data, dict):
            continue
        for species, cfg in (data.get("lifecycle_configs") or {}).items():
            if isinstance(cfg, dict) and cfg.get("dormancy_required") is True:
                dorm_required[species] = base
        for species, phases in (data.get("growth_phases") or {}).items():
            growth_phases[species] = _phase_names(phases)

    for entry in _load("lifecycles_outdoor.yaml").get("lifecycles", []):
        species = entry["scientific_name"]
        outdoor[species] = (entry.get("phase_sequence"), _phase_names(entry.get("phases", [])))
        if entry.get("dormancy_required") is True:
            dorm_required[species] = "lifecycles_outdoor.yaml"

    return dorm_required, growth_phases, outdoor, seq_phase_names


def test_dormancy_required_species_have_a_dormancy_phase_model() -> None:
    dorm_required, growth_phases, outdoor, seq_phase_names = _collect()
    assert dorm_required, "expected at least one dormancy_required species in the seed data"

    offenders: list[str] = []
    for species in sorted(dorm_required):
        if any(name in _DORMANCY_PHASES for name in growth_phases.get(species, [])):
            continue
        sequence_name, inline_phases = outdoor.get(species, (None, []))
        if any(name in _DORMANCY_PHASES for name in inline_phases):
            continue
        if sequence_name and (seq_phase_names.get(sequence_name, set()) & _DORMANCY_PHASES):
            continue
        offenders.append(f"{species} [{dorm_required[species]}]")

    assert not offenders, (
        "Species declare dormancy_required: true but have no reachable dormancy-type "
        "phase (growth_phases / lifecycles_outdoor phases / bound phase_sequence):\n" + "\n".join(offenders)
    )
