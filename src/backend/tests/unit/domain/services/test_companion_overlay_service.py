"""REQ-053 WP 8.15 (#2658) — the companion layer of a bed (GP-FR-134, REQ-028 §7.3).

The service runs over the in-memory plan and site doubles and :class:`FakeRotationGraph`, whose batched reads answer
from the SAME dictionaries as the per-species reads the engine and the planting dialog make. So
:class:`TestSameExpressionAsThePlantingDialog` arranges one world and judges one pair through all three paths: the
overlay may not have a rule of its own.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.common.exceptions import NotFoundError
from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.models.garden_plan import SlotSpeciesHint
from app.domain.models.site import Slot
from app.domain.services import companion_overlay_service as overlay_module
from app.domain.services.bed_rotation_service import BedRotationService
from app.domain.services.care_event_service import CareEventService
from app.domain.services.companion_overlay_service import (
    MAX_COMPANION_EDGES,
    MAX_COMPANION_RELATIONS,
    MAX_JUDGED_PAIRS,
    MAX_SPECIES_PER_SLOT,
    CompanionOverlayService,
)
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.support.rotation_fakes import (
    FakeFamilies,
    FakeRotationGraph,
    FakeRotationHistory,
    FakeSpecies,
    make_family,
    make_species,
)


def slot(key: str, x: float | None = None, y: float | None = None, *, location_key: str = "bed") -> Slot:
    doc: dict = {"_key": key, "slot_id": key.upper() + "_X", "location_key": location_key}
    if x is not None and y is not None:
        doc["geometry"] = {"kind": "point", "origin": [x, y]}
    return Slot.model_validate(doc)


class _ActivePlants:
    """The engine's ``get_active_by_slot`` over the plan double's species hints (the plants standing in a slot)."""

    def __init__(self, plan: FakePlanRepo) -> None:
        self._plan = plan

    def get_active_by_slot(self, slot_key, *, tenant_key):
        return [SimpleNamespace(species_key=h.species_key) for h in self._plan.species_hints if h.slot_key == slot_key]


@pytest.fixture
def world() -> SimpleNamespace:
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", geometry=rect(2.0, 1.0, w=4, h=2))
    plan.locations["alien"] = make_location("alien").model_copy(update={"site_key": "site_foreign"})
    plan.slots = [slot("s1", 0.5, 0.5), slot("s2", 1.0, 0.5), slot("s3", 1.5, 0.5), slot("z1", location_key="alien")]
    graph = FakeRotationGraph()
    species = FakeSpecies(
        *(make_species(key, "fam") for key in ("tomato", "basil", "fennel", "carrot", "dill")),
        make_species("secret", "fam", tenant=OTHER_TENANT),
    )
    care_repo = FakeCareEventRepo()
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    families = FakeFamilies(make_family("fam", pause=None))
    validator = CropRotationValidator(
        None, species, graph, site_repo=sites, family_repo=families, history_repo=FakeRotationHistory(care_repo)
    )
    return SimpleNamespace(
        plan=plan,
        graph=graph,
        overlay=CompanionOverlayService(sites, plan, graph),  # type: ignore[arg-type]
        dialog=BedRotationService(sites, plan, graph, species, families, care, validator),  # type: ignore[arg-type]
        engine=CompanionPlantingEngine(graph, _ActivePlants(plan), species),  # type: ignore[arg-type]
    )


def stand(world, **by_slot: str | list[str]) -> None:  # type: ignore[no-untyped-def]
    world.plan.species_hints = [
        SlotSpeciesHint(slot_key=key, species_key=species)
        for key, value in by_slot.items()
        for species in ([value] if isinstance(value, str) else value)
    ]


def edge_of(world, a: str, b: str):  # type: ignore[no-untyped-def]
    edges = world.overlay.companion_edges("bed", tenant_key=TENANT).edges
    return next(e for e in edges if {e.slot_a.slot_key, e.slot_b.slot_key} == {a, b})


class TestTheJudgedPairs:
    def test_a_compatible_pair_has_its_score_reason_code_and_names(self, world) -> None:
        stand(world, s1="tomato", s2="basil")
        world.graph.adjacent["s1"] = ["s2"]
        world.graph.compatible = {"tomato": {"basil": 0.9}, "basil": {"tomato": 0.9}}

        edge = edge_of(world, "s1", "s2")

        assert (edge.status, edge.reason_code, edge.score, edge.reason) == (
            "compatible",
            "companion.compatible",
            0.9,
            None,
        )
        assert edge.deciding is not None
        assert (edge.deciding.species_a_key, edge.deciding.species_b_key) == ("basil", "tomato")
        assert edge.deciding.species_a_name == "Test basil"

    def test_an_incompatible_pair_carries_the_curated_reason_and_no_score(self, world) -> None:
        stand(world, s1="tomato", s2="fennel")
        world.graph.adjacent["s1"] = ["s2"]
        world.graph.incompatible = {"tomato": ["fennel"], "fennel": ["tomato"]}
        world.graph.reasons[("tomato", "fennel")] = "Fennel inhibits most neighbours."

        edge = edge_of(world, "s1", "s2")

        assert (edge.status, edge.reason_code, edge.score) == ("incompatible", "companion.incompatible", None)
        assert edge.reason == "Fennel inhibits most neighbours."

    def test_no_edge_between_the_species_is_unknown(self, world) -> None:
        stand(world, s1="tomato", s2="carrot")
        world.graph.adjacent["s1"] = ["s2"]

        edge = edge_of(world, "s1", "s2")

        assert (edge.status, edge.reason_code, edge.score, edge.deciding) == (
            "unknown",
            "companion.unknown",
            None,
            None,
        )

    def test_an_edge_stored_in_one_direction_only_still_judges_the_pair(self, world) -> None:
        stand(world, s1="tomato", s2="fennel")
        world.graph.adjacent["s1"] = ["s2"]
        world.graph.incompatible = {"fennel": ["tomato"]}  # only fennel -> tomato

        assert edge_of(world, "s1", "s2").status == "incompatible"

    def test_in_a_slot_with_two_species_the_incompatible_one_wins(self, world) -> None:
        stand(world, s1="tomato", s2=["basil", "fennel"])
        world.graph.adjacent["s1"] = ["s2"]
        world.graph.compatible = {"tomato": {"basil": 0.9}}
        world.graph.incompatible = {"tomato": ["fennel"]}

        edge = edge_of(world, "s1", "s2")

        assert edge.status == "incompatible"
        assert edge.slot_b.species_keys == ["basil", "fennel"] or edge.slot_a.species_keys == ["basil", "fennel"]

    def test_a_pair_with_an_empty_side_is_no_line(self, world) -> None:
        stand(world, s1="tomato")
        world.graph.adjacent["s1"] = ["s2"]

        result = world.overlay.companion_edges("bed", tenant_key=TENANT)

        assert (result.edges, result.total, result.truncated) == ([], 0, False)

    def test_a_species_the_tenant_cannot_read_is_neither_related_nor_named(self, world) -> None:
        stand(world, s1="tomato", s2="secret")
        world.graph.adjacent["s1"] = ["s2"]
        world.graph.incompatible = {"tomato": ["secret"], "secret": ["tomato"]}
        world.graph.hidden = {"secret"}

        edge = edge_of(world, "s1", "s2")

        assert (edge.status, edge.deciding) == ("unknown", None)


class TestPositionsAndReads:
    def test_positions_are_the_slot_anchors_in_plan_coordinates(self, world) -> None:
        stand(world, s1="tomato", s2="basil")
        world.graph.adjacent["s1"] = ["s2"]

        edge = edge_of(world, "s1", "s2")

        # The bed's rect is anchored at (2, 1) without rotation: p_plan = anchor + p_bed.
        assert {edge.slot_a.slot_key: edge.slot_a.position, edge.slot_b.slot_key: edge.slot_b.position} == {
            "s1": (2.5, 1.5),
            "s2": (3.0, 1.5),
        }

    def test_a_rotated_bed_rotates_the_positions(self, world) -> None:
        world.plan.locations["bed"] = make_location("bed", geometry=rect(2.0, 1.0, w=4, h=2, rotation=90))
        stand(world, s1="tomato", s2="basil")
        world.graph.adjacent["s1"] = ["s2"]

        edge = edge_of(world, "s1", "s2")

        assert edge.slot_a.position == (1.5, 1.5)  # (0.5, 0.5) turned by 90 degrees about the anchor

    def test_a_slot_without_geometry_has_no_position(self, world) -> None:
        world.plan.slots.append(slot("s9"))
        stand(world, s1="tomato", s9="basil")
        world.graph.adjacent["s1"] = ["s9"]

        edge = edge_of(world, "s1", "s9")

        assert {edge.slot_a.slot_key: edge.slot_a.position, edge.slot_b.slot_key: edge.slot_b.position}["s9"] is None

    def test_the_graph_is_read_twice_whatever_the_number_of_pairs(self, world) -> None:
        world.plan.slots = [slot(f"s{i:03d}", 0.1 * i, 0.5) for i in range(40)]
        stand(world, **{f"s{i:03d}": "tomato" if i % 2 else "basil" for i in range(40)})
        world.graph.adjacent = {f"s{i:03d}": [f"s{i + 1:03d}"] for i in range(39)}
        world.graph.compatible = {"tomato": {"basil": 0.7}}

        result = world.overlay.companion_edges("bed", tenant_key=TENANT)

        assert result.total == 39
        assert world.graph.calls == ["get_slot_adjacency", "load_companion_relations"]


class TestTheCapAndTheOrder:
    def test_more_than_500_pairs_are_cut_to_500_and_flagged(self, world) -> None:
        count = MAX_COMPANION_EDGES + 2  # 502 slots in a chain: 501 pairs
        world.plan.slots = [slot(f"s{i:04d}", 0.001 * i, 0.5) for i in range(count)]
        stand(world, **{f"s{i:04d}": ("fennel" if i == count - 1 else "carrot") for i in range(count)})
        world.graph.adjacent = {f"s{i:04d}": [f"s{i + 1:04d}"] for i in range(count - 1)}
        world.graph.incompatible = {"carrot": ["fennel"]}

        result = world.overlay.companion_edges("bed", tenant_key=TENANT)

        assert (len(result.edges), result.total, result.truncated) == (500, 501, True)
        # The strongest status survives the cut although its slots sort last.
        assert result.edges[0].status == "incompatible"
        assert {result.edges[0].slot_a.slot_key, result.edges[0].slot_b.slot_key} == {"s0500", "s0501"}

    def test_exactly_500_pairs_are_not_truncated(self, world) -> None:
        count = MAX_COMPANION_EDGES + 1
        world.plan.slots = [slot(f"s{i:04d}", 0.001 * i, 0.5) for i in range(count)]
        stand(world, **{f"s{i:04d}": "carrot" for i in range(count)})
        world.graph.adjacent = {f"s{i:04d}": [f"s{i + 1:04d}"] for i in range(count - 1)}

        result = world.overlay.companion_edges("bed", tenant_key=TENANT)

        assert (len(result.edges), result.total, result.truncated) == (500, 500, False)

    def test_the_order_is_status_then_slot_keys(self, world) -> None:
        stand(world, s1="tomato", s2="basil", s3="fennel")
        world.graph.adjacent = {"s1": ["s2", "s3"], "s2": ["s3"]}
        world.graph.compatible = {"tomato": {"basil": 0.5}}
        world.graph.incompatible = {"basil": ["fennel"]}

        edges = world.overlay.companion_edges("bed", tenant_key=TENANT).edges

        assert [(e.slot_a.slot_key, e.slot_b.slot_key, e.status) for e in edges] == [
            ("s2", "s3", "incompatible"),
            ("s1", "s2", "compatible"),
            ("s1", "s3", "unknown"),
        ]


class TestTheWorkIsBounded:
    """SEC-001: more pairs than the cap are not all read, judged and sorted; the bound is the window, not the answer."""

    @staticmethod
    def _chain(world, count: int, species=lambda i: "carrot") -> None:  # type: ignore[no-untyped-def]
        world.plan.slots = [slot(f"s{i:05d}", 0.0001 * i, 0.5) for i in range(count)]
        stand(world, **{f"s{i:05d}": species(i) for i in range(count)})
        world.graph.adjacent = {f"s{i:05d}": [f"s{i + 1:05d}"] for i in range(count - 1)}

    def test_more_pairs_than_the_window_are_judged_only_up_to_the_window(self, world, monkeypatch) -> None:
        count = MAX_JUDGED_PAIRS + 101  # 2100 pairs
        self._chain(world, count)
        judged: list[str] = []
        real = overlay_module.judge_neighbour

        def counting(other, incompatible, compatible):  # type: ignore[no-untyped-def]
            judged.append(other)
            return real(other, incompatible, compatible)

        monkeypatch.setattr(overlay_module, "judge_neighbour", counting)

        result = world.overlay.companion_edges("bed", tenant_key=TENANT)

        assert world.graph.adjacency_limits == [MAX_JUDGED_PAIRS]  # the cut is asked of the database
        assert (len(result.edges), result.total, result.truncated) == (MAX_COMPANION_EDGES, count - 1, True)
        # One species per side, both directions: two rule calls per judged pair, and only the window is judged.
        assert len(judged) == 2 * MAX_JUDGED_PAIRS

    def test_only_the_slots_of_the_judged_pairs_are_read(self, world) -> None:
        count = MAX_JUDGED_PAIRS + 101
        self._chain(world, count)
        world.plan.locations["bed"] = make_location("bed", geometry=rect(2.0, 1.0, w=4, h=2))

        world.overlay.companion_edges("bed", tenant_key=TENANT)

        (read,) = world.plan.active_slot_reads
        assert read is not None and len(read) == MAX_JUDGED_PAIRS + 1  # 2000 pairs of a chain touch 2001 slots

    def test_within_the_window_the_strongest_survive_the_cap(self, world) -> None:
        count = MAX_JUDGED_PAIRS + 101
        # fennel at 1500 (inside the window) and at 2050 (outside it): the guaranteed order holds for the window only
        self._chain(world, count, species=lambda i: "fennel" if i in (1500, 2050) else "carrot")
        world.graph.incompatible = {"carrot": ["fennel"]}

        result = world.overlay.companion_edges("bed", tenant_key=TENANT)

        statuses = [edge.status for edge in result.edges]
        assert statuses[:2] == ["incompatible", "incompatible"] and set(statuses[2:]) == {"unknown"}
        assert {(e.slot_a.slot_key, e.slot_b.slot_key) for e in result.edges[:2]} == {
            ("s01499", "s01500"),
            ("s01500", "s01501"),
        }
        # The pairs around slot 2050 lie beyond the judged window: not answered, whatever their status.
        assert not any("s02050" in (e.slot_a.slot_key, e.slot_b.slot_key) for e in result.edges)

    def test_the_species_of_a_slot_are_capped_before_the_cross_product(self, world, monkeypatch) -> None:
        many = [f"sp{i:02d}" for i in range(MAX_SPECIES_PER_SLOT + 4)]
        stand(world, s1=many, s2=many)
        world.graph.adjacent = {"s1": ["s2"]}
        calls: list[str] = []
        real = overlay_module.judge_neighbour
        monkeypatch.setattr(overlay_module, "judge_neighbour", lambda o, i, c: calls.append(o) or real(o, i, c))

        (edge,) = world.overlay.companion_edges("bed", tenant_key=TENANT).edges

        assert len(calls) == 2 * MAX_SPECIES_PER_SLOT * MAX_SPECIES_PER_SLOT
        assert edge.slot_a.species_keys == many[:MAX_SPECIES_PER_SLOT] and edge.slot_a.species_truncated is True
        (species_read,) = world.graph.relation_species
        assert species_read == many[:MAX_SPECIES_PER_SLOT]  # the companion read sees only the judged species

    def test_the_companion_read_is_limited(self, world) -> None:
        stand(world, s1="tomato", s2="basil")
        world.graph.adjacent = {"s1": ["s2"]}
        limits: list[int] = []
        real = world.graph.load_companion_relations

        def spy(keys, *, tenant_key, limit):  # type: ignore[no-untyped-def]
            limits.append(limit)
            return real(keys, tenant_key=tenant_key, limit=limit)

        world.graph.load_companion_relations = spy

        world.overlay.companion_edges("bed", tenant_key=TENANT)

        assert limits == [MAX_COMPANION_RELATIONS]


class TestTheBedIsTheTenants:
    def test_another_tenants_bed_is_not_found(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.overlay.companion_edges("alien", tenant_key=TENANT)

    def test_an_unknown_bed_is_not_found(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.overlay.companion_edges("nowhere", tenant_key=TENANT)

    def test_the_owner_of_the_other_bed_is_not_this_tenant(self, world) -> None:
        stand(world, s1="tomato", s2="basil")
        world.graph.adjacent["s1"] = ["s2"]
        with pytest.raises(NotFoundError):
            world.overlay.companion_edges("bed", tenant_key=OTHER_TENANT)


# ── The same expression as the planting dialog and the engine ──────────────────────────────────────────────

_CASES = {
    "compatible": ({"tomato": {"basil": 0.9}, "basil": {"tomato": 0.9}}, {}),
    "incompatible": ({}, {"tomato": ["basil"], "basil": ["tomato"]}),
    # Both edges between the same two species: the precedence of the rule decides.
    "conflicting": ({"tomato": {"basil": 0.9}, "basil": {"tomato": 0.9}}, {"tomato": ["basil"], "basil": ["tomato"]}),
    "unknown": ({}, {}),
}


def _dialog_status(world, planted: str, slot_key: str):  # type: ignore[no-untyped-def]
    """What the planting dialog says when ``planted`` goes into ``slot_key``: status and score of its hint."""
    hints = world.dialog.validate_planting("bed", planted, tenant_key=TENANT, slot_key=slot_key).neighbours
    if not hints:
        return ("unknown", None)
    (hint,) = hints
    return ("incompatible", None) if hint.code == "companion.incompatible" else ("compatible", hint.score)


def _engine_status(world, planted: str, slot_key: str) -> str:
    compatible, warnings, benefits = world.engine.check_compatibility(planted, slot_key, tenant_key=TENANT)
    if not compatible:
        return "incompatible"
    return "compatible" if benefits else "unknown"


class TestSameExpressionAsThePlantingDialog:
    @pytest.mark.parametrize("case", sorted(_CASES))
    def test_the_overlay_status_of_a_pair_equals_the_dialog_and_the_engine(self, world, case) -> None:
        compatible, incompatible = _CASES[case]
        world.graph.compatible, world.graph.incompatible = compatible, incompatible
        world.graph.adjacent = {"s1": ["s2"], "s2": ["s1"]}

        # The overlay sees tomato in s1 next to basil in s2 ...
        stand(world, s1="tomato", s2="basil")
        edge = edge_of(world, "s1", "s2")
        # ... the dialog and the engine judge planting tomato into s1 while basil stands in s2.
        stand(world, s2="basil")
        dialog = _dialog_status(world, "tomato", "s1")
        engine = _engine_status(world, "tomato", "s1")

        assert (edge.status, edge.score) == dialog
        assert edge.status == engine
        assert edge.status == {"conflicting": "incompatible"}.get(case, case)
