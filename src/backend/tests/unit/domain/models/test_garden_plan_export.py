"""REQ-053 WP 5.2 (#2431) — what the JSON plan backup may and may not contain, and that the GDPR export has all of it.

*Exclusion* is structural: the backup is built from the models in ``garden_plan_export``, so the test reads the
models' JSON schema — a field that is not there cannot be filled. *Inclusion* (GP-FR-147: the backup "is part of
the GDPR export cascade") is measured against the manifest the Art. 15/20 export actually walks, not against a
list the test keeps: a column added to the backup without a line in the manifest fails here.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.models.garden_plan_export import (
    ExportGardenObject,
    ExportLocation,
    ExportPlanSettings,
    ExportSite,
    ExportSlot,
    GardenPlanExport,
)

#: Parts of a garden that are not the plan's structure (GP-FR-140): nothing like these may ever be a field.
_FORBIDDEN = {"plants", "plant", "tasks", "task", "events", "care_events", "photos", "attachments", "tenant_key"}


def _property_names(schema: dict[str, Any], defs: dict[str, Any] | None = None) -> set[str]:
    defs = defs if defs is not None else schema.get("$defs", {})
    names: set[str] = set()
    for name, sub in schema.get("properties", {}).items():
        names.add(name)
        names |= _property_names(sub, defs)
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in schema.get(key, []):
            names |= _property_names(sub, defs)
    if "items" in schema:
        names |= _property_names(schema["items"], defs)
    if "$ref" in schema:
        names |= _property_names(defs[schema["$ref"].rsplit("/", 1)[1]], defs)
    return names


class TestWhatTheBackupNeverHolds:
    def test_no_field_anywhere_names_an_account_or_a_tenant(self) -> None:
        names = _property_names(GardenPlanExport.model_json_schema())

        assert names, "the schema walk found nothing"
        assert not [n for n in names if n.endswith(("_by", "_user_key", "_by_name"))], names
        assert not names & _FORBIDDEN, names & _FORBIDDEN

    def test_the_walk_sees_the_nested_models(self) -> None:
        """Non-vacuity: a field of a nested model (a soil profile, a props model) is among the names."""
        names = _property_names(GardenPlanExport.model_json_schema())

        assert {"soil_profile", "ph", "crown_radius_m", "boundary", "default_grid_m"} <= names
        # WP 3.9: the site features of a bed (sun profile, microclimate …) are part of the backup
        assert {"site_conditions", "sun_window", "frost_risk", "wind_exposure"} <= names

    def test_the_site_contributes_its_name_and_type_only(self) -> None:
        assert set(ExportSite.model_fields) == {"name", "type"}

    def test_the_documents_that_carry_an_author_do_not_export_it(self) -> None:
        # ``GardenObject.created_by`` and ``SitePlan.plan_updated_by`` exist on the stored documents.
        assert "created_by" not in ExportGardenObject.model_fields
        assert "plan_updated_by" not in ExportPlanSettings.model_fields
        assert "plan_updated_at" not in ExportPlanSettings.model_fields

    def test_the_slots_carry_geometry_not_state(self) -> None:
        assert not {"currently_occupied", "archived_at", "sown_at", "last_sanitization"} & set(ExportSlot.model_fields)


def _manifest_fields(collection: str) -> set[str]:
    (source,) = [s for s in DataExportEngine.USER_DATA_MANIFEST if s.collection == collection]
    return set(source.fields)


class TestTheGdprExportHasEverythingTheBackupHas:
    @pytest.mark.parametrize(
        ("collection", "model"),
        [("locations", ExportLocation), ("slots", ExportSlot), ("garden_objects", ExportGardenObject)],
    )
    def test_every_field_of_a_collection_is_disclosed(self, collection: str, model: type) -> None:
        exported = {"_key" if name == "key" else name for name in model.model_fields}

        missing = exported - _manifest_fields(collection)

        assert missing == set(), f"in the plan backup but not in the Art. 15/20 export of `{collection}`: {missing}"

    def test_the_site_name_type_and_the_whole_plan_are_disclosed(self) -> None:
        assert {"name", "type", "plan"} <= _manifest_fields("sites")

    def test_the_plan_settings_come_through_the_plan_field(self) -> None:
        # ``plan`` is exported whole; the only thing withheld is the account key of the last editor.
        (source,) = [s for s in DataExportEngine.USER_DATA_MANIFEST if s.collection == "sites"]
        assert source.withhold == ["plan.plan_updated_by"]
        assert set(ExportPlanSettings.model_fields) <= {
            "boundary",
            "north_angle_deg",
            "default_grid_m",
            "adjacency_factor",
            "plan_revision",
        }
