"""The garden-plan reach helpers of #2448: the build's request bodies and the observation's facts.

``scripts/reach/seed_garden_plan.py`` builds a small plan through the API for the
``endpoint-sites-plan-read-model-answers`` probe (REQ-053 GP-API-001), and
``scripts/reach/observe_garden_plan.py`` turns the ``GET /plan`` answer into one
fact per line. Their proof is the run against the reach stack; what is pinned
here is what a test can honestly stand in for:

* **The build speaks the API's contract.** Every body it sends is validated by the
  model the route itself parses it with, so a renamed or tightened field stops
  this test instead of turning the probe into *not probed* at the next audit.
  The bed holds the planted count at the build's spacing, so each plant gets a
  slot (the layout calculator the quick planting uses decides that).
* **The observation prints what the answer holds, never a verdict.** A missing
  part, a zero counter or a plant without a phase shows up as a different fact,
  and an empty answer is printed as such rather than as silence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from app.api.v1.garden_plan.schemas import PlanBatchRequest, PlanBoundaryRequest
from app.api.v1.irrigation_zones.schemas import IrrigationZoneCreate, IrrigationZoneLocationsUpdate
from app.api.v1.locations.schemas import QuickPlantingRequest
from app.api.v1.sites.schemas import SiteCreate
from app.api.v1.tasks.schemas import TaskCreate
from app.common.enums import LayoutStrategy
from app.domain.calculators.planting_layout_calculator import EntryLayout, compute_layout
from app.domain.models.garden_plan import PlanOperationAdapter
from app.domain.models.geometry import GeometryAdapter
from tests.support.repo_scripts import find_repo_root, load_repo_script

seed = load_repo_script("reach/seed_garden_plan")
observe = load_repo_script("reach/observe_garden_plan")


# ── seed_garden_plan: the bodies the build sends ───────────────────────────────


def test_the_site_and_boundary_bodies_are_what_the_routes_accept():
    assert SiteCreate.model_validate(seed.site_body()).type == "outdoor"
    boundary = PlanBoundaryRequest.model_validate(seed.boundary_body())
    assert boundary.boundary.kind == "rect"


def test_every_batch_operation_parses_as_a_plan_operation():
    body = seed.batch_body(1)
    request = PlanBatchRequest.model_validate(body)
    assert request.expected_revision == 1
    operations = [PlanOperationAdapter.validate_python(raw) for raw in body["operations"]]
    assert [op.op for op in operations] == ["create_location", "create_garden_object"]
    assert {op.temp_key for op in operations} == {"bed", "compost"}


def test_the_bed_holds_every_plant_on_its_own_slot():
    bed = next(op for op in seed.batch_body(1)["operations"] if op["temp_key"] == "bed")
    planting = QuickPlantingRequest.model_validate(seed.quick_planting_body("sp_tomato"))
    assert planting.quantity == seed.PLANT_COUNT
    layout = compute_layout(
        GeometryAdapter.validate_python(bed["data"]["geometry"]),
        EntryLayout(
            layout_strategy=LayoutStrategy.GRID,
            spacing_cm=planting.spacing_cm,
            row_spacing_cm=planting.row_spacing_cm,
        ),
    )
    assert layout.capacity_max >= seed.PLANT_COUNT


def test_the_task_and_zone_bodies_are_what_the_routes_accept():
    task = TaskCreate.model_validate(seed.task_body("loc_bed"))
    assert (task.entity_type, task.entity_key, task.for_each_plant) == ("location", "loc_bed", False)
    assert IrrigationZoneCreate.model_validate(seed.zone_body()).name == seed.ZONE_NAME
    assert IrrigationZoneLocationsUpdate.model_validate(seed.zone_locations_body("loc_bed")).location_keys == [
        "loc_bed"
    ]


def test_the_species_is_found_by_its_scientific_name_and_a_missing_one_stops_the_build():
    listing = {
        "items": [
            {"key": "sp_1", "scientific_name": "Daucus carota"},
            {"key": "sp_2", "scientific_name": "Solanum lycopersicum"},
        ]
    }
    assert seed.species_key_of(listing) == "sp_2"
    with pytest.raises(seed.ReachError):
        seed.species_key_of({"items": [{"key": "sp_1", "scientific_name": "Daucus carota"}]})


def test_a_fresh_account_must_belong_to_exactly_one_tenant():
    assert seed.personal_slug_of([{"slug": "jane-garden"}]) == "jane-garden"
    for listing in ([], [{"slug": "a"}, {"slug": "b"}], {"slug": "a"}):
        with pytest.raises(seed.ReachError):
            seed.personal_slug_of(listing)


# ── observe_garden_plan: the facts of one answer ───────────────────────────────


def _rect() -> dict[str, Any]:
    return {"kind": "rect", "origin": [1, 1], "width_m": 2, "length_m": 1, "rotation_deg": 0}


def _answer(**overrides: Any) -> dict[str, Any]:
    answer: dict[str, Any] = {
        "plan": {"boundary": {**_rect(), "width_m": 10, "length_m": 10}},
        "locations": [{"key": "loc_1", "name": "reach-bed", "geometry": _rect(), "open_task_count": 1}],
        "garden_objects": [{"key": "go_1", "object_type": "compost", "label": "reach-compost", "geometry": _rect()}],
        "slots": [
            {"key": f"sl_{n}", "location_key": "loc_1", "plan_geometry": {"origin": [1.2 + n * 0.4, 1.2]}}
            for n in range(3)
        ],
        "plants": [
            {
                "key": f"pl_{n}",
                "instance_id": f"TOM-{n}",
                "species_key": "sp_2",
                "phase_key": "ph_g",
                "slot_key": f"sl_{n}",
            }
            for n in range(3)
        ],
        "zones": [{"key": "z_1", "name": "reach-zone", "location_keys": ["loc_1"]}],
    }
    answer.update(overrides)
    return answer


#: What the facts of the plan the build makes read; the probe's expected set is this list.
EXPECTED = [
    "garden-object/compost/reach-compost/geometry=rect",
    "location/reach-bed/geometry=rect",
    "open-tasks/reach-bed=1",
    "plan/boundary=rect",
    "plant-field/instance_id=3",
    "plant-field/key=3",
    "plant-field/phase_key=3",
    "plant-field/slot_key=3",
    "plant-field/species_key=3",
    "plants/reach-bed=3",
    "slots/reach-bed=3",
    "zone/reach-zone=reach-bed",
]


def test_a_complete_answer_yields_one_fact_per_declared_part():
    assert observe.plan_facts(_answer()) == EXPECTED


def test_the_probe_expects_exactly_the_facts_of_a_complete_answer():
    """The committed probe and this test describe the same plan; a drift between them is a broken probe."""
    root = find_repo_root(Path(__file__).resolve())
    assert root is not None
    probe = yaml.safe_load(
        (root / "project/reach-probes/endpoint-sites-plan-read-model-answers.yml").read_text("utf-8")
    )
    assert sorted(probe["expected"]["values"]) == EXPECTED


def test_a_plant_without_a_phase_and_a_zero_counter_read_as_different_facts():
    plants = _answer()["plants"]
    plants[0]["phase_key"] = None
    location = {**_answer()["locations"][0], "open_task_count": 0}
    facts = observe.plan_facts(_answer(plants=plants, locations=[location]))
    assert "plant-field/phase_key=2" in facts
    assert not any(fact.startswith("open-tasks/") for fact in facts)


def test_a_missing_part_is_absent_from_the_facts_not_reported_as_present():
    facts = observe.plan_facts(_answer(zones=[], plants=[], plan=None))
    assert not any(fact.startswith(("zone/", "plants/", "plant-field/", "plan/")) for fact in facts)
    assert "slots/reach-bed=3" in facts


def test_a_slot_without_plan_geometry_is_not_counted_and_a_slotless_plant_counts_at_its_location():
    slots = _answer()["slots"]
    slots[2]["plan_geometry"] = None
    plants = [{"key": "pl_x", "instance_id": "TOM-X", "species_key": "sp_2", "location_key": "loc_1"}]
    facts = observe.plan_facts(_answer(slots=slots, plants=plants))
    assert "slots/reach-bed=2" in facts
    assert "plants/reach-bed=1" in facts
    assert "plant-field/slot_key=0" in facts


def test_a_body_that_is_no_plan_yields_no_facts():
    assert observe.plan_facts("not json") == []
    assert observe.plan_facts({}) == []
