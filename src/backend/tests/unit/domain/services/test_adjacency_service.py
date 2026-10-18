"""REQ-053 WP 3.3 (#2393) — the recompute of a bed's neighbourhood and the manual edges (GP-FR-130, SR-021).

The graph repository is a recording double with the real reconcile semantics in miniature (derived edges
follow the pairs, manual edges stay), so the tests assert both what the service decided and what reached
the graph.
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError
from app.domain.interfaces.graph_repository import ADJACENCY_SOURCE_MANUAL, AdjacencySync
from app.domain.models.garden_plan import SlotSpeciesHint
from app.domain.models.site import Slot
from app.domain.services.adjacency_service import AdjacencyService, request_adjacency_recompute
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)


class RecordingGraph:
    def __init__(self) -> None:
        self.synced: list[tuple[list[str], list[tuple[str, str, float]]]] = []
        self.manual: list[tuple[str, str, float | None, str]] = []
        self.removed: list[tuple[str, str]] = []
        self.remove_result = 1

    def sync_derived_adjacency(self, slot_keys, pairs):
        self.synced.append((list(slot_keys), list(pairs)))
        return AdjacencySync(created=len(pairs) * 2)

    def set_adjacent_slots(self, a, b, *, distance_cm=None, source="derived"):
        self.manual.append((a, b, distance_cm, source))

    def remove_manual_adjacency(self, a, b):
        self.removed.append((a, b))
        return self.remove_result


def slot(key: str, x: float, y: float, *, location_key: str = "bed", **kw) -> Slot:
    return Slot.model_validate(
        {
            "_key": key,
            "slot_id": key.upper() + "_X",
            "location_key": location_key,
            "geometry": {"kind": "point", "origin": [x, y]},
            **kw,
        }
    )


@pytest.fixture
def world():
    site = make_site()
    other_site = make_site().model_copy(update={"key": "site_2"})
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    sites = FakeSites(site, other_site, foreign)
    repo = FakePlanRepo(sites)
    repo.locations["bed"] = make_location("bed", geometry=rect(1, 1, 3, 1))
    repo.locations["bed2"] = make_location("bed2", geometry=rect(5, 1, 3, 1))
    repo.locations["far"] = make_location("far", geometry=rect(1, 1, 3, 1)).model_copy(update={"site_key": "site_2"})
    repo.locations["alien"] = make_location("alien", geometry=rect(1, 1, 3, 1)).model_copy(
        update={"site_key": "site_foreign"}
    )
    repo.slots = [
        slot("a", 0.0, 0.0, planned_spacing_cm=30),
        slot("b", 0.3, 0.0, planned_spacing_cm=30),
        slot("c", 0.9, 0.0, planned_spacing_cm=30),
        slot("x", 0.0, 0.0, location_key="bed2"),
        slot("f", 0.0, 0.0, location_key="far"),
        slot("z", 0.0, 0.0, location_key="alien"),
    ]
    graph = RecordingGraph()
    return AdjacencyService(sites, repo, graph), repo, graph, site


class TestRecompute:
    def test_derives_the_pairs_of_the_bed_and_hands_every_slot_to_the_reconcile(self, world) -> None:
        service, _repo, graph, _site = world
        result = service.recompute("bed", tenant_key=TENANT)
        assert graph.synced == [(["a", "b", "c"], [("a", "b", 30.0)])]
        assert result.pairs == 1
        assert result.sync.created == 2

    def test_another_beds_slots_never_take_part(self, world) -> None:
        service, _repo, graph, _site = world
        service.recompute("bed", tenant_key=TENANT)
        assert "x" not in graph.synced[0][0]

    def test_the_site_adjacency_factor_sets_the_reach(self, world) -> None:
        service, _repo, graph, site = world
        site.plan = site.plan.model_copy(update={"adjacency_factor": 3.0})
        service.recompute("bed", tenant_key=TENANT)
        assert [(a, b) for a, b, _ in graph.synced[0][1]] == [("a", "b"), ("a", "c"), ("b", "c")]

    def test_an_archived_slot_loses_its_edges_but_gets_none(self, world) -> None:
        from datetime import UTC, datetime

        service, repo, graph, _site = world
        repo.slots[1] = repo.slots[1].model_copy(update={"archived_at": datetime.now(UTC)})
        service.recompute("bed", tenant_key=TENANT)
        keys, pairs = graph.synced[0]
        assert "b" in keys
        assert pairs == []

    def test_a_slot_without_geometry_is_reconciled_but_not_derived(self, world) -> None:
        service, repo, graph, _site = world
        repo.slots[0] = repo.slots[0].model_copy(update={"geometry": None})
        service.recompute("bed", tenant_key=TENANT)
        keys, pairs = graph.synced[0]
        assert "a" in keys
        assert pairs == []

    def test_species_width_gives_the_interaction_radius(self, world) -> None:
        service, repo, graph, _site = world
        repo.slots = [slot("a", 0.0, 0.0), slot("c", 0.9, 0.0)]
        for key in ("a", "c"):
            repo.species_hints.append(
                SlotSpeciesHint(slot_key=key, species_key="sp", mature_width_cm="100", growth_habit="shrub")
            )
        service.recompute("bed", tenant_key=TENANT)
        assert graph.synced[0][1] == [("a", "c", 90.0)]

    def test_species_spacing_is_used_when_the_slot_carries_none(self, world) -> None:
        service, repo, graph, _site = world
        repo.slots = [slot("a", 0.0, 0.0), slot("c", 0.9, 0.0)]
        repo.species_hints.append(SlotSpeciesHint(slot_key="a", species_key="sp", spacing_cm="60--80"))
        service.recompute("bed", tenant_key=TENANT)
        assert graph.synced[0][1] == [("a", "c", 90.0)]

    def test_one_species_without_a_width_voids_the_interaction_radius(self, world) -> None:
        service, repo, graph, _site = world
        repo.slots = [slot("a", 0.0, 0.0), slot("c", 0.9, 0.0)]
        repo.species_hints = [
            SlotSpeciesHint(slot_key="a", species_key="s1", mature_width_cm="100"),
            SlotSpeciesHint(slot_key="a", species_key="s2"),
            SlotSpeciesHint(slot_key="c", species_key="s1", mature_width_cm="100"),
        ]
        service.recompute("bed", tenant_key=TENANT)
        assert graph.synced[0][1] == []

    @pytest.mark.parametrize("location_key", ["alien", "missing", ""])
    def test_a_foreign_or_absent_bed_is_a_404_and_writes_nothing(self, world, location_key) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(NotFoundError):
            service.recompute(location_key, tenant_key=TENANT)
        assert graph.synced == []

    def test_an_empty_tenant_is_no_tenant(self, world) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(NotFoundError):
            service.recompute("bed", tenant_key="")
        assert graph.synced == []


class TestManualEdges:
    def test_sets_a_manual_edge_between_two_slots_of_one_site(self, world) -> None:
        service, _repo, graph, _site = world
        service.set_manual_edge("a", "x", tenant_key=TENANT, role=TenantRole.GROWER, distance_cm=70.0)
        assert graph.manual == [("a", "x", 70.0, ADJACENCY_SOURCE_MANUAL)]

    def test_two_beds_of_one_site_are_allowed(self, world) -> None:
        service, _repo, graph, _site = world
        service.set_manual_edge("c", "x", tenant_key=TENANT, role=TenantRole.LEAD, distance_cm=None)
        assert len(graph.manual) == 1

    def test_a_slot_of_another_site_is_refused_with_422_and_nothing_is_written(self, world) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(PlanError) as exc:
            service.set_manual_edge("a", "f", tenant_key=TENANT, role=TenantRole.GROWER, distance_cm=None)
        assert exc.value.status_code == 422
        assert exc.value.details[0]["code"] == "adjacency.different_site"
        assert graph.manual == []

    def test_a_slot_of_a_foreign_tenant_answers_like_an_unknown_one(self, world) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(NotFoundError) as foreign:
            service.set_manual_edge("a", "z", tenant_key=TENANT, role=TenantRole.GROWER, distance_cm=None)
        with pytest.raises(NotFoundError) as unknown:
            service.set_manual_edge("a", "nope", tenant_key=TENANT, role=TenantRole.GROWER, distance_cm=None)
        assert foreign.value.status_code == unknown.value.status_code == 404
        assert graph.manual == []

    def test_the_first_slot_of_a_foreign_tenant_is_refused_too(self, world) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(NotFoundError):
            service.set_manual_edge("z", "a", tenant_key=TENANT, role=TenantRole.GROWER, distance_cm=None)
        assert graph.manual == []

    def test_an_archived_slot_cannot_be_given_a_neighbour(self, world) -> None:
        from datetime import UTC, datetime

        service, repo, graph, _site = world
        repo.slots[1] = repo.slots[1].model_copy(update={"archived_at": datetime.now(UTC)})
        with pytest.raises(PlanError) as exc:
            service.set_manual_edge("a", "b", tenant_key=TENANT, role=TenantRole.GROWER, distance_cm=None)
        assert exc.value.details[0]["code"] == "adjacency.slot_archived"
        assert graph.manual == []

    def test_a_slot_cannot_neighbour_itself(self, world) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(PlanError) as exc:
            service.set_manual_edge("a", "a", tenant_key=TENANT, role=TenantRole.GROWER, distance_cm=None)
        assert exc.value.details[0]["code"] == "adjacency.same_slot"
        assert graph.manual == []

    def test_a_viewer_may_not_edit(self, world) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(ForbiddenError):
            service.set_manual_edge("a", "b", tenant_key=TENANT, role=TenantRole.VIEWER, distance_cm=None)
        with pytest.raises(ForbiddenError):
            service.remove_manual_edge("a", "b", tenant_key=TENANT, role=TenantRole.VIEWER)
        assert graph.manual == [] and graph.removed == []

    def test_an_absurd_distance_is_refused(self, world) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(PlanError):
            service.set_manual_edge("a", "b", tenant_key=TENANT, role=TenantRole.GROWER, distance_cm=-1.0)
        assert graph.manual == []

    def test_removing_reports_whether_a_manual_edge_existed(self, world) -> None:
        service, _repo, graph, _site = world
        assert service.remove_manual_edge("a", "b", tenant_key=TENANT, role=TenantRole.GROWER) is True
        graph.remove_result = 0
        assert service.remove_manual_edge("a", "b", tenant_key=TENANT, role=TenantRole.GROWER) is False

    def test_removing_checks_both_ends_like_setting(self, world) -> None:
        service, _repo, graph, _site = world
        with pytest.raises(PlanError):
            service.remove_manual_edge("a", "f", tenant_key=TENANT, role=TenantRole.GROWER)
        with pytest.raises(NotFoundError):
            service.remove_manual_edge("a", "z", tenant_key=TENANT, role=TenantRole.GROWER)
        assert graph.removed == []


class TestDispatch:
    def test_hands_the_bed_key_to_the_dispatcher(self) -> None:
        seen: list[str] = []
        request_adjacency_recompute(seen.append, "bed")
        assert seen == ["bed"]

    def test_no_dispatcher_and_no_key_are_quiet(self) -> None:
        request_adjacency_recompute(None, "bed")
        seen: list[str] = []
        request_adjacency_recompute(seen.append, "")
        assert seen == []

    def test_a_failing_broker_does_not_fail_the_write(self) -> None:
        def broken(_key: str) -> None:
            raise ConnectionError("broker down")

        request_adjacency_recompute(broken, "bed")
