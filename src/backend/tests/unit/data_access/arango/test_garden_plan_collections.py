"""REQ-053 §20.14 (M1, #2323) — the garden-plan collections, edges and indexes are registered for the bootstrap."""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col

_DOCUMENTS = (col.GARDEN_OBJECTS, col.CARE_EVENTS, col.IRRIGATION_ZONES, col.GARDEN_PLAN_AUDIT, col.BED_TEMPLATES)


def test_document_collections_registered() -> None:
    assert _DOCUMENTS == ("garden_objects", "care_events", "irrigation_zones", "garden_plan_audit", "bed_templates")
    assert all(name in col.DOCUMENT_COLLECTIONS for name in _DOCUMENTS)


def test_edge_collections_registered() -> None:
    assert col.GARDEN_PLAN_EDGE_COLLECTIONS == (
        "has_garden_object",
        "run_planned_at",
        "care_event_at",
        "task_logged_as",
        "has_irrigation_zone",
        "zone_covers",
        "zone_supplied_by",
        "zone_actuated_by",
    )
    assert all(name in col.EDGE_COLLECTIONS for name in col.GARDEN_PLAN_EDGE_COLLECTIONS)


def _definitions() -> dict[str, dict[str, Any]]:
    return {definition["edge_collection"]: definition for definition in col.GRAPH_EDGE_DEFINITIONS}


def test_new_graph_edge_definitions_point_the_way_the_spec_draws_them() -> None:
    defs = _definitions()
    expected = {
        col.HAS_GARDEN_OBJECT: ([col.SITES], [col.GARDEN_OBJECTS]),
        col.RUN_PLANNED_AT: ([col.PLANTING_RUNS], [col.SLOTS]),  # GP-FR-065: planned occupancy of a slot
        col.CARE_EVENT_AT: ([col.CARE_EVENTS], [col.LOCATIONS]),
        col.TASK_LOGGED_AS: ([col.TASKS], [col.CARE_EVENTS]),
        col.HAS_IRRIGATION_ZONE: ([col.SITES], [col.IRRIGATION_ZONES]),
        col.ZONE_COVERS: ([col.IRRIGATION_ZONES], [col.LOCATIONS]),
        col.ZONE_SUPPLIED_BY: ([col.IRRIGATION_ZONES], [col.GARDEN_OBJECTS]),
        col.ZONE_ACTUATED_BY: ([col.IRRIGATION_ZONES], [col.ACTUATORS]),
    }
    for edge, (sources, targets) in expected.items():
        assert defs[edge]["from_vertex_collections"] == sources, edge
        assert defs[edge]["to_vertex_collections"] == targets, edge


def test_widened_definitions_carry_the_new_sources_and_garden_objects_stay_off_the_tenant_edge() -> None:
    defs = _definitions()
    tenant_sources = defs[col.BELONGS_TO_TENANT]["from_vertex_collections"]

    assert {col.CARE_EVENTS, col.IRRIGATION_ZONES, col.BED_TEMPLATES} <= set(tenant_sources)
    assert col.GARDEN_OBJECTS not in tenant_sources  # E-01: the site is the anchor
    assert col.CARE_EVENTS in defs[col.CARE_EVENT_FOR]["from_vertex_collections"]
    assert col.GARDEN_OBJECTS in defs[col.HAS_TASK]["from_vertex_collections"]


def test_no_tenant_key_index_fields_on_locations_slots_or_garden_objects() -> None:
    # E-01 (#2107): the index constants of the three site-anchored collections start at the parent key.
    assert col.LOCATION_BED_STATUS_INDEX_FIELDS == ["site_key", "bed_status"]
    assert col.GARDEN_OBJECT_TYPE_INDEX_FIELDS == ["site_key", "object_type"]
    assert col.SLOT_ROLE_INDEX_FIELDS == ["location_key", "slot_role"]


def test_care_event_indexes_follow_section_20_10_with_the_unique_one_scoped_to_the_tenant() -> None:
    assert col.CARE_EVENT_LOCATION_HISTORY_INDEX_FIELDS == ["tenant_key", "location_key", "performed_at"]
    assert col.CARE_EVENT_TENANT_HISTORY_INDEX_FIELDS == ["tenant_key", "performed_at"]
    assert col.CARE_EVENT_TASK_INDEX_FIELDS == ["task_key"]
    assert col.CARE_EVENT_SOURCE_REF_INDEX_FIELDS == ["tenant_key", "source_ref.collection", "source_ref.key"]
