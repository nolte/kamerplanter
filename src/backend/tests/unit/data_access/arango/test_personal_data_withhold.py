"""REQ-053 WP 1.8 review F-07 — the Art. 15 export of a personal garden carries no other account's key.

``plan.plan_updated_by`` is the key of whoever saved the plan last. On a personal tenant that can be a member
who joined later, and ``KEEP(doc, ["plan"])`` projects the whole object, so the field has to be withheld after
the read.
"""

from __future__ import annotations

from app.data_access.arango.personal_data_repository import _without_paths
from app.domain.engines.data_export_engine import DataExportEngine


def test_the_editor_key_is_removed_and_the_rest_of_the_plan_stays() -> None:
    row = {"_key": "site_1", "plan": {"plan_revision": 4, "plan_updated_by": "u_other", "north_angle_deg": 15.0}}
    cleaned = _without_paths(row, ["plan.plan_updated_by"])
    assert cleaned == {"_key": "site_1", "plan": {"plan_revision": 4, "north_angle_deg": 15.0}}


def test_the_read_result_is_not_mutated() -> None:
    row = {"plan": {"plan_updated_by": "u_other", "plan_revision": 1}}
    _without_paths(row, ["plan.plan_updated_by"])
    assert row["plan"]["plan_updated_by"] == "u_other"


def test_a_row_without_a_plan_passes_unchanged() -> None:
    assert _without_paths({"_key": "s", "plan": None}, ["plan.plan_updated_by"]) == {"_key": "s", "plan": None}
    assert _without_paths({"_key": "s"}, ["plan.plan_updated_by"]) == {"_key": "s"}


def test_the_sites_source_of_the_manifest_declares_it() -> None:
    sources = [s for s in DataExportEngine().build_export_manifest("u1") if s.collection == "sites"]
    withheld = [s for s in sources if "plan.plan_updated_by" in s.withhold]
    assert withheld and all("plan" in s.fields for s in withheld)
