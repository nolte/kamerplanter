"""A plant's phase must be reachable from its species' live sequence (#1150).

Three plants on the reference instance report a phase whose `PhaseSequenceEntry`
belongs to a sequence generation that no longer exists — `indoor_default` was
deleted and recreated during the fine-typing work (#616 / v0027), the old entry
documents survived, and the plants pointing at them were never re-pointed. A
sunflower and a *Monstera deliciosa* share one entry key; the Monstera is reported
as `flowering` one month after planting, through the sunflower's phase.

**The distinction this module exists for.** `v0021` heals a key that resolves in
*neither* key space. These keys do resolve — the documents are still there. They
are **orphaned**, not **dangling**, and v0021's predicate is exactly one step too
narrow: it tests document existence where what matters is reachability from a live
sequence.

That is why `KIND_DANGLING` is still reported here as its own kind. Asserting the
two are told apart is what proves the gap is *closed* rather than *duplicated* —
without it, a detector that simply re-implemented v0021 would look identical from
the outside.

Every fixture below is the shape measured on the instance, not an invented one.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.domain.engines.phase_reachability import (
    KIND_DANGLING,
    KIND_FOREIGN_SEQUENCE,
    KIND_GROWTH_PHASE_SPACE,
    KIND_ORPHANED_ENTRY,
    KIND_SPECIES_UNBOUND,
    find_unreachable_phases,
)

#: The live generation, as on the instance: `indoor_default` is 21507465.
_LIVE_SEQUENCE = "21507465"
#: The generation that was deleted; its entry documents survived.
_DEAD_SEQUENCE = "18132186"


def _plant(key: str, *, phase: str | None, species: str = "sp_monstera", instance_id: str = "") -> dict[str, Any]:
    return {
        "_key": key,
        "instance_id": instance_id or key,
        "species_key": species,
        "current_phase_key": phase,
    }


def _entry(key: str, sequence_key: str) -> dict[str, Any]:
    return {"_key": key, "phase_sequence_key": sequence_key}


def _edge(species_key: str, sequence_key: str) -> dict[str, Any]:
    return {"_from": f"species/{species_key}", "_to": f"phase_sequences/{sequence_key}"}


def _find(**overrides: Any):
    kwargs: dict[str, Any] = {
        "plants": [],
        "entries": [],
        "sequences": [{"_key": _LIVE_SEQUENCE}],
        "growth_phases": [],
        "species_sequence_edges": [],
    }
    kwargs.update(overrides)
    return find_unreachable_phases(**kwargs)


# ── the defect ───────────────────────────────────────────────────────────────


def test_an_entry_whose_sequence_is_gone_is_reported() -> None:
    """The measured case: the document resolves, the sequence behind it does not."""
    findings = _find(
        plants=[_plant("p1", phase="18132838", instance_id="MONST-0713-WG7")],
        entries=[_entry("18132838", _DEAD_SEQUENCE)],
        species_sequence_edges=[_edge("sp_monstera", _LIVE_SEQUENCE)],
    )

    assert [(f.plant_id, f.kind) for f in findings] == [("MONST-0713-WG7", KIND_ORPHANED_ENTRY)]


def test_two_plants_sharing_one_orphaned_entry_are_both_reported() -> None:
    """A sunflower and a Monstera held the same key. Reporting one would hide the other."""
    findings = _find(
        plants=[
            _plant("p1", phase="18132838", species="sp_monstera", instance_id="MONST-0713-WG7"),
            _plant("p2", phase="18132838", species="sp_helianthus", instance_id="HELIA-0710-E5A"),
        ],
        entries=[_entry("18132838", _DEAD_SEQUENCE)],
    )

    assert {f.plant_id for f in findings} == {"MONST-0713-WG7", "HELIA-0710-E5A"}


def test_a_plant_whose_species_has_no_sequence_is_reported() -> None:
    """All three measured plants were in this state as well.

    It is the *combination* that makes the phase unverifiable: with no bound
    sequence there is nothing to check reachability against.
    """
    findings = _find(
        plants=[_plant("p1", phase="e1")],
        entries=[_entry("e1", _LIVE_SEQUENCE)],
        species_sequence_edges=[],
    )

    assert [f.kind for f in findings] == [KIND_SPECIES_UNBOUND]


def test_an_orphaned_entry_outranks_an_unbound_species() -> None:
    """One plant, one finding, and it names the reason a repair must act on.

    Binding the species would not by itself make an orphaned phase reachable, so
    reporting `species_unbound` here would point a repair at the wrong lever.
    """
    findings = _find(
        plants=[_plant("p1", phase="18132838")],
        entries=[_entry("18132838", _DEAD_SEQUENCE)],
        species_sequence_edges=[],
    )

    assert [f.kind for f in findings] == [KIND_ORPHANED_ENTRY]


# ── the boundary against v0021 ───────────────────────────────────────────────


def test_a_dangling_key_is_reported_as_a_different_kind() -> None:
    """v0021's case, kept distinguishable.

    If both arrived as one kind, a detector that merely re-implemented v0021 would
    be indistinguishable from one that closed the orphaned gap — which is the whole
    claim of #1150.
    """
    findings = _find(plants=[_plant("p1", phase="does-not-exist")], entries=[])

    assert [f.kind for f in findings] == [KIND_DANGLING]


def test_orphaned_and_dangling_are_reported_separately_in_one_pass() -> None:
    findings = _find(
        plants=[
            _plant("p1", phase="18132838", instance_id="ORPHAN"),
            _plant("p2", phase="ghost", instance_id="DANGLE"),
        ],
        entries=[_entry("18132838", _DEAD_SEQUENCE)],
    )

    assert {(f.plant_id, f.kind) for f in findings} == {
        ("ORPHAN", KIND_ORPHANED_ENTRY),
        ("DANGLE", KIND_DANGLING),
    }


# ── what must NOT be reported ────────────────────────────────────────────────


def test_a_reachable_phase_is_not_reported() -> None:
    """The half that stops this flagging the whole catalogue.

    `YUCCA-0617-DIJ` on a live entry of its species' bound sequence is the
    measured healthy case.
    """
    findings = _find(
        plants=[_plant("p1", phase="21507470", species="sp_yucca")],
        entries=[_entry("21507470", _LIVE_SEQUENCE)],
        species_sequence_edges=[_edge("sp_yucca", _LIVE_SEQUENCE)],
    )

    assert findings == []


def test_a_plant_that_has_not_entered_a_phase_is_not_reported() -> None:
    """`current_phase_key: null` is a different condition, already reported elsewhere."""
    assert _find(plants=[_plant("p1", phase=None)]) == []


def test_a_growth_phase_plant_on_an_unbound_species_is_not_reported() -> None:
    """The pre-sequence model, used consistently. Nothing is wrong with it here."""
    findings = _find(
        plants=[_plant("p1", phase="13949", species="sp_spath")],
        growth_phases=[{"_key": "13949"}],
        species_sequence_edges=[],
    )

    assert findings == []


# ── the second population, reported rather than silently covered ─────────────


def test_a_growth_phase_plant_whose_species_is_bound_to_a_sequence_is_reported() -> None:
    """`DAHLI-0710-3LN`: resolves in the old key space while its species moved on.

    Not the same defect — v0021 acknowledges the GrowthPhase space explicitly —
    but the same question. Given its own kind so whatever repair lands has to state
    what it does with it, instead of covering one space and calling the issue
    closed.
    """
    findings = _find(
        plants=[_plant("p1", phase="14195", species="sp_dahlia", instance_id="DAHLI-0710-3LN")],
        growth_phases=[{"_key": "14195"}],
        species_sequence_edges=[_edge("sp_dahlia", _LIVE_SEQUENCE)],
    )

    assert [(f.plant_id, f.kind) for f in findings] == [("DAHLI-0710-3LN", KIND_GROWTH_PHASE_SPACE)]


def test_an_entry_from_a_foreign_live_sequence_is_reported() -> None:
    """Not observed on the instance; one rebind away, and free to check."""
    other_live = "26733349"
    findings = _find(
        plants=[_plant("p1", phase="e-other", species="sp_x")],
        entries=[_entry("e-other", other_live)],
        sequences=[{"_key": _LIVE_SEQUENCE}, {"_key": other_live}],
        species_sequence_edges=[_edge("sp_x", _LIVE_SEQUENCE)],
    )

    assert [f.kind for f in findings] == [KIND_FOREIGN_SEQUENCE]


# ── shape ────────────────────────────────────────────────────────────────────


def test_each_finding_explains_itself() -> None:
    """A kind alone does not tell an operator what to do; the detail carries the why."""
    findings = _find(
        plants=[_plant("p1", phase="18132838")],
        entries=[_entry("18132838", _DEAD_SEQUENCE)],
    )

    assert "next_phase is null" in findings[0].detail
    assert _DEAD_SEQUENCE in findings[0].detail


@pytest.mark.parametrize("collection", ["species", "master_species"])
def test_the_edge_prefix_is_not_hardcoded(collection: str) -> None:
    """The edge `_from` carries a collection name; assuming one would make the
    whole detector silently find nothing if it ever changed."""
    findings = find_unreachable_phases(
        plants=[_plant("p1", phase="e1", species="sp_x")],
        entries=[_entry("e1", _LIVE_SEQUENCE)],
        sequences=[{"_key": _LIVE_SEQUENCE}],
        growth_phases=[],
        species_sequence_edges=[{"_from": f"{collection}/sp_x", "_to": f"phase_sequences/{_LIVE_SEQUENCE}"}],
        species_collection=collection,
    )

    assert findings == []
