"""Every seed species must resolve to a phase sequence that is actually seeded (#1006).

Plant ``DRACA-0616-OWL`` sat at ``current_phase_key: null`` two months after planting.
The phase machine had nothing to run against, and the record could not be told apart
from "between phases". One of the two roots is master data: a species that resolves to
no ``PhaseSequence`` gives every plant created for it a null phase.

What is checked, statically
===========================

The runtime binding is a database walk (``seed_data.link_indoor_species_to_phase_sequence``),
but the *decision* is pure: ``resolve_phase_sequence_name`` maps a species' seeded
attributes onto a sequence **name**. So the invariant is checkable from the YAML alone:

    for every species in the seed corpus, the name the resolver picks must exist in
    ``phase_sequences.yaml``.

A name that does not exist is not a harmless fallback. The linker then drops the species
onto the annual ``indoor_default`` blanket — a 126-day cycle ending in a terminal,
harvest-allowing phase — which is exactly the mis-binding #949 describes: an evergreen
perennial scheduled to be lifecycle-complete four months after planting. Today the seed
logs a warning for it; nothing failed a build over it, and nothing checked it before a
seed run.

Also pinned: the explicit ``phase_sequence`` bindings in ``lifecycles_outdoor.yaml`` name
sequences that exist, and ``indoor_default`` itself is seeded (without it the linker
returns early and binds *nothing at all*).

The attribute cascade is mirrored, not guessed
----------------------------------------------

``cycle_type`` is the **effective** one — ``cultivation_cycle_type`` over ``cycle_type``
(ADR-006 E1, ``resolve_effective_cycle``) — because that is what the linker passes. A
tender perennial cultivated as an annual belongs on the harvest-terminated blanket, and
reading the botanical axis instead would test a rule the seed does not apply.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

import app.migrations
from app.domain.engines.phase_sequence_resolver import (
    INDOOR_DEFAULT_SEQUENCE,
    resolve_phase_sequence_name,
)

_SEED = Path(app.migrations.__file__).parent / "seed_data"

#: Seed species that cannot be resolved onto a seeded sequence. Empty by design: the
#: corpus resolves cleanly today, and a new species that does not must be either fixed
#: or named here with the reason — never absorbed by the blanket in silence.
UNRESOLVABLE_SPECIES: dict[str, str] = {}


def _load(name: str) -> dict[str, Any]:
    data = yaml.safe_load((_SEED / name).read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _species_files() -> list[Path]:
    return [*sorted(_SEED.glob("plant_info*.yaml")), _SEED / "adventskalender.yaml"]


def _seeded_sequence_names() -> set[str]:
    return {s["name"] for s in _load("phase_sequences.yaml").get("phase_sequences", []) or []}


def _species_attributes() -> dict[str, dict[str, Any]]:
    """Return ``{scientific_name: {growth_habit, photosynthesis_type}}`` for the corpus."""
    attributes: dict[str, dict[str, Any]] = {}

    def absorb(name: str, entry: dict[str, Any]) -> None:
        target = attributes.setdefault(name, {})
        for field in ("growth_habit", "photosynthesis_type"):
            if entry.get(field) and not target.get(field):
                target[field] = entry[field]

    for entry in _load("species.yaml").get("species", []) or []:
        if isinstance(entry, dict) and entry.get("scientific_name"):
            absorb(entry["scientific_name"], entry)
    for path in _species_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for entry in document.get("new_species", []) or []:
            if isinstance(entry, dict) and entry.get("scientific_name"):
                absorb(entry["scientific_name"], entry)
        for name, entry in (document.get("species_enrichment") or {}).items():
            if isinstance(entry, dict) and name in attributes:
                absorb(str(name), entry)
    return attributes


def _lifecycle_attributes() -> dict[str, dict[str, Any]]:
    """Return the lifecycle axes the linker feeds the resolver, per species."""
    lifecycles: dict[str, dict[str, Any]] = {}

    def absorb(name: str, source: dict[str, Any]) -> None:
        target = lifecycles.setdefault(name, {})
        for field in ("cycle_type", "cultivation_cycle_type", "flowering_strategy", "photoperiod_type"):
            if source.get(field) is not None and field not in target:
                target[field] = source[field]

    # species.yaml/lifecycle_overrides is authoritative (applied first by seed_data.py).
    for name, override in (_load("species.yaml").get("lifecycle_overrides") or {}).items():
        if isinstance(override, dict):
            absorb(str(name), override)
    for path in _species_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for name, config in (document.get("lifecycle_configs") or {}).items():
            if isinstance(config, dict):
                absorb(str(name), config)
    for entry in _load("lifecycles_outdoor.yaml").get("lifecycles", []) or []:
        if isinstance(entry, dict) and entry.get("scientific_name"):
            absorb(entry["scientific_name"], entry)
    return lifecycles


def _effective_cycle(name: str, lifecycle: dict[str, Any], perennials: set[str]) -> str | None:
    """Mirror ``resolve_effective_cycle``: practised cycle over botanical cycle."""
    return (
        lifecycle.get("cultivation_cycle_type")
        or lifecycle.get("cycle_type")
        or ("perennial" if name in perennials else None)
    )


def _resolved_targets() -> dict[str, str | None]:
    """Return ``{scientific_name: resolved sequence name or None}`` for the corpus."""
    attributes = _species_attributes()
    lifecycles = _lifecycle_attributes()
    perennials = set(_load("species.yaml").get("perennial_species", []) or [])

    return {
        name: resolve_phase_sequence_name(
            name,
            cycle_type=_effective_cycle(name, lifecycles.get(name, {}), perennials),
            flowering_strategy=lifecycles.get(name, {}).get("flowering_strategy"),
            photosynthesis_type=fields.get("photosynthesis_type"),
            photoperiod_type=lifecycles.get(name, {}).get("photoperiod_type"),
            growth_habit=fields.get("growth_habit"),
        )
        for name, fields in attributes.items()
    }


def _offenders(
    targets: dict[str, str | None],
    seeded: set[str],
    allowlist: dict[str, str],
) -> list[str]:
    """Return ``name -> target`` for every species whose target is not seeded.

    The one predicate both the corpus test and its negative control drive, so the
    control proves something about the check that actually runs.
    """
    return sorted(
        f"{name} -> {target}"
        for name, target in targets.items()
        if target is not None and target not in seeded and name not in allowlist
    )


def test_the_blanket_sequence_itself_is_seeded() -> None:
    """Without ``indoor_default`` the linker returns early and binds *nothing*."""
    assert INDOOR_DEFAULT_SEQUENCE in _seeded_sequence_names(), (
        f"{INDOOR_DEFAULT_SEQUENCE} is not in phase_sequences.yaml — "
        "link_indoor_species_to_phase_sequence would return before binding a single species"
    )


def test_every_seed_species_resolves_to_a_seeded_phase_sequence() -> None:
    seeded = _seeded_sequence_names()
    targets = _resolved_targets()
    assert len(targets) >= 200, f"expected the full species corpus, collected only {len(targets)}"

    offenders = _offenders(targets, seeded, UNRESOLVABLE_SPECIES)
    assert not offenders, (
        "Species resolve onto a phase sequence that is not seeded. The linker silently "
        f"drops them onto the annual '{INDOOR_DEFAULT_SEQUENCE}' blanket — a harvest-"
        "terminated cycle for plants that do not terminate (#949/#1006). Seed the "
        "sequence, correct the attributes, or name the species in UNRESOLVABLE_SPECIES "
        "with the reason:\n" + "\n".join(offenders)
    )


def test_outdoor_lifecycles_bind_only_sequences_that_exist() -> None:
    seeded = _seeded_sequence_names()
    offenders = sorted(
        f"{entry['scientific_name']} -> {entry['phase_sequence']}"
        for entry in _load("lifecycles_outdoor.yaml").get("lifecycles", []) or []
        if entry.get("phase_sequence") and entry["phase_sequence"] not in seeded
    )
    assert not offenders, "lifecycles_outdoor.yaml binds species to phase sequences that are not seeded:\n" + "\n".join(
        offenders
    )


def test_unresolvable_allowlist_has_no_obsolete_entries() -> None:
    seeded = _seeded_sequence_names()
    targets = _resolved_targets()
    obsolete = sorted(
        f"{name} ({reason})"
        for name, reason in UNRESOLVABLE_SPECIES.items()
        if name not in targets or targets.get(name) is None or targets[name] in seeded
    )
    assert not obsolete, "UNRESOLVABLE_SPECIES names species that now resolve cleanly — remove them:\n" + "\n".join(
        obsolete
    )


@pytest.mark.parametrize(
    ("attributes", "expected"),
    [
        # The #949 shape: the resolver picks a cohort sequence, the seed cannot find it,
        # and the species lands on the annual blanket instead.
        ({"photosynthesis_type": "cam", "cycle_type": "perennial"}, "cam_succulent_rest"),
        ({"cycle_type": "perennial"}, "evergreen_foliage_perennial"),
        ({"growth_habit": "fern"}, "fern_spore"),
        # Unresolvable (no LifecycleConfig at all) still targets a real sequence.
        ({}, "evergreen_foliage_perennial"),
    ],
)
def test_the_resolvability_check_can_fail(attributes: dict[str, Any], expected: str) -> None:
    """Negative control: the invariant must be able to detect a missing sequence.

    The corpus resolves cleanly today, so the corpus assertion never fires on real data
    — which on its own says nothing about whether it *could*. This drives the same
    :func:`_offenders` predicate against a catalogue that lacks the target.
    """
    target = resolve_phase_sequence_name(
        "Synthetica probans",
        cycle_type=attributes.get("cycle_type"),
        flowering_strategy=attributes.get("flowering_strategy"),
        photosynthesis_type=attributes.get("photosynthesis_type"),
        photoperiod_type=attributes.get("photoperiod_type"),
        growth_habit=attributes.get("growth_habit"),
    )
    assert target == expected

    targets = {"Synthetica probans": target}
    catalogue_without_it = {INDOOR_DEFAULT_SEQUENCE}
    assert _offenders(targets, catalogue_without_it, {}) == [f"Synthetica probans -> {expected}"]
    # Seeding the sequence clears it; so does naming the species in the allowlist.
    assert _offenders(targets, catalogue_without_it | {expected}, {}) == []
    assert _offenders(targets, catalogue_without_it, {"Synthetica probans": "documented gap"}) == []
