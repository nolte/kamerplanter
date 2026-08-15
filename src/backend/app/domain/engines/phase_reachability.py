"""Is a plant's current phase reachable from its species' live sequence? (#1150)

Three plants on the reference instance report a phase whose ``PhaseSequenceEntry``
belongs to a sequence generation that no longer exists. A sunflower and a
*Monstera deliciosa* share one entry key; the Monstera is reported as
``flowering`` one month after planting, through a sunflower's phase.

**Why nothing caught it.** ``v0021`` heals a plant whose ``current_phase_key``
resolves in *neither* key space. These keys **do** resolve — the entry documents
survived a delete-and-recreate of ``indoor_default`` during the fine-typing work
(#616 / v0027) — so they are *orphaned*, not *dangling*. v0021's predicate tests
document existence; what matters is **reachability from a live sequence**, which
is one step further.

Everything downstream reads the phase as authoritative: ``get_plant_phase_status``
answers ``in_phase`` with a phase name, watering intervals and harvest readiness
key on it, and ``next_phase`` is ``null`` because the engine cannot name a
successor in a sequence that is gone. The strongest possible "this is fine"
signal, over a phase the plant is not in.

This module is the **detector** only. Repair means moving a plant into a phase of
its species' live sequence, which is plant-visible lifecycle state and shares its
placement rule with #1146 (name anchor, then elapsed days, with a backdated
``entered_at``) — one rule for both repairs, not two, so it belongs with that work
rather than here.

Pure: dicts in, findings out. No I/O, no clock (BACKEND.md §2.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: The plant's ``current_phase_key`` matches no live document in either key space.
#: ``v0021``'s scope. Reported as a distinct kind so that closing the orphaned gap
#: is provably *not* a second implementation of the dangling one.
KIND_DANGLING = "dangling"

#: The entry document exists, but no live ``PhaseSequence`` references it — the
#: sequence generation it belonged to was deleted. This is #1150's defect.
KIND_ORPHANED_ENTRY = "orphaned_entry"

#: The entry is live and reachable, but from a *different* sequence than the one
#: the plant's species is bound to. Not observed on the reference instance; the
#: check costs nothing and the shape is one rebind away.
KIND_FOREIGN_SEQUENCE = "foreign_sequence"

#: The plant holds a resolving phase key while its species is bound to no sequence
#: at all. All three measured plants are in this state, and it is the *combination*
#: that makes the phase unverifiable: there is nothing to check reachability against.
KIND_SPECIES_UNBOUND = "species_unbound"

#: The plant resolves through the pre-sequence ``GrowthPhase`` space while its
#: species *is* bound to a sequence. Not the same defect — v0021 acknowledges that
#: space explicitly — but the same question, and reported rather than silently
#: covered so whatever repair lands has to say what it does with it.
KIND_GROWTH_PHASE_SPACE = "growth_phase_space"


@dataclass(frozen=True)
class PhaseReachabilityFinding:
    """One plant whose current phase cannot be verified against its species."""

    plant_key: str
    plant_id: str
    species_key: str
    current_phase_key: str
    kind: str
    detail: str


def find_unreachable_phases(
    *,
    plants: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    sequences: list[dict[str, Any]],
    growth_phases: list[dict[str, Any]],
    species_sequence_edges: list[dict[str, Any]],
    species_collection: str = "species",
    sequence_collection: str = "phase_sequences",
) -> list[PhaseReachabilityFinding]:
    """Return every plant whose current phase is not reachable from its species.

    Args:
        plants: ``plant_instances`` documents.
        entries: ``phase_sequence_entries`` documents.
        sequences: ``phase_sequences`` documents — the *live* generations.
        growth_phases: ``growth_phases`` documents (the pre-sequence key space).
        species_sequence_edges: ``has_phase_sequence`` edge documents.
        species_collection: Collection name used to build the edge ``_from`` id.
        sequence_collection: Collection name used to read the edge ``_to`` id.

    A plant with no ``current_phase_key`` is not a finding: it has not entered a
    phase, which is a different (and already reported) condition.
    """
    live_sequence_keys = {s["_key"] for s in sequences}
    entry_by_key = {e["_key"]: e for e in entries}
    growth_phase_keys = {g["_key"] for g in growth_phases}

    sequence_by_species: dict[str, str] = {}
    for edge in species_sequence_edges:
        species_key = str(edge.get("_from", "")).removeprefix(f"{species_collection}/")
        sequence_key = str(edge.get("_to", "")).removeprefix(f"{sequence_collection}/")
        if species_key and sequence_key:
            sequence_by_species[species_key] = sequence_key

    findings: list[PhaseReachabilityFinding] = []
    for plant in plants:
        current = plant.get("current_phase_key")
        if not current:
            continue

        species_key = plant.get("species_key") or ""
        bound_sequence = sequence_by_species.get(species_key)
        entry = entry_by_key.get(current)

        kind, detail = _classify(
            current=current,
            entry=entry,
            in_growth_phase_space=current in growth_phase_keys,
            live_sequence_keys=live_sequence_keys,
            bound_sequence=bound_sequence,
        )
        if kind is None:
            continue

        findings.append(
            PhaseReachabilityFinding(
                plant_key=plant.get("_key", ""),
                plant_id=plant.get("instance_id") or plant.get("plant_name") or "",
                species_key=species_key,
                current_phase_key=str(current),
                kind=kind,
                detail=detail,
            )
        )

    findings.sort(key=lambda f: (f.kind, f.plant_id, f.plant_key))
    return findings


def _classify(
    *,
    current: str,
    entry: dict[str, Any] | None,
    in_growth_phase_space: bool,
    live_sequence_keys: set[str],
    bound_sequence: str | None,
) -> tuple[str | None, str]:
    """Return ``(kind, detail)``, or ``(None, "")`` when the phase is verifiable.

    Order matters and is not arbitrary. The *most specific* explanation wins, so a
    plant is reported once with the reason a repair would have to act on — an
    orphaned entry under an unbound species is an orphaned entry first, because
    binding the species would not by itself make the phase reachable.
    """
    if entry is None and not in_growth_phase_space:
        return KIND_DANGLING, "current_phase_key matches no live entry and no live growth phase (v0021's scope)"

    if entry is not None:
        entry_sequence = entry.get("phase_sequence_key") or ""
        if entry_sequence not in live_sequence_keys:
            return (
                KIND_ORPHANED_ENTRY,
                f"entry {current} survives but its sequence {entry_sequence or '<unset>'} does not — "
                "the phase resolves and is unreachable, so next_phase is null and the lifecycle cannot advance",
            )
        if bound_sequence is None:
            return (
                KIND_SPECIES_UNBOUND,
                "the species is bound to no sequence, so there is nothing to verify the phase against",
            )
        if entry_sequence != bound_sequence:
            return (
                KIND_FOREIGN_SEQUENCE,
                f"entry belongs to sequence {entry_sequence}, but the species is bound to {bound_sequence}",
            )
        return None, ""

    # Resolves in the GrowthPhase space.
    if bound_sequence is not None:
        return (
            KIND_GROWTH_PHASE_SPACE,
            f"phase resolves through the pre-sequence GrowthPhase space while the species is bound to "
            f"sequence {bound_sequence}",
        )
    return None, ""
