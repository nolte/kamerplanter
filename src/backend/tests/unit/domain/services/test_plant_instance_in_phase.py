"""Tests for listing a tenant's active plant instances in a phase definition.

FIX-01 R1/R8: ``list_active_in_phase_definition`` is a thin, tenant-scoped
delegate onto the repository (which resolves the current_phase→definition
indirection and the active/tenant filters in AQL). The service adds a defence-in-
depth guard that rejects the empty-tenant sentinel before any query runs.
"""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.domain.services.plant_instance_service import PlantInstanceService


def _service(plant_repo: MagicMock) -> PlantInstanceService:
    return PlantInstanceService(plant_repo, MagicMock(), MagicMock(), MagicMock())


class TestListActiveInPhaseDefinition:
    def test_delegates_to_repo_with_tenant_and_key(self) -> None:
        plant_repo = MagicMock()
        rows = [{"key": "p1", "instance_id": "PLANT-1", "species_key": "sp1"}]
        plant_repo.list_active_in_phase_definition.return_value = rows

        result = _service(plant_repo).list_active_in_phase_definition("tenant-a", "pd1")

        assert result == rows
        plant_repo.list_active_in_phase_definition.assert_called_once_with("tenant-a", "pd1")

    def test_empty_result_is_valid(self) -> None:
        plant_repo = MagicMock()
        plant_repo.list_active_in_phase_definition.return_value = []

        assert _service(plant_repo).list_active_in_phase_definition("tenant-a", "pd1") == []

    def test_rejects_empty_tenant_key(self) -> None:
        plant_repo = MagicMock()
        with pytest.raises(ValidationError):
            _service(plant_repo).list_active_in_phase_definition("", "pd1")
        plant_repo.list_active_in_phase_definition.assert_not_called()

    def test_returns_multiple_plants_in_phase(self) -> None:
        """FIX-01 R1: list multiple active plants in the phase definition."""
        plant_repo = MagicMock()
        rows = [
            {
                "key": "pi-1",
                "instance_id": "PLANT-001",
                "plant_name": "Tomato #1",
                "species_key": "sp-1",
                "species_scientific_name": "Solanum lycopersicum",
                "location_name": "Greenhouse A",
                "slot_label": "Row 1, Pos 3",
                "current_phase_started_at": "2024-01-10T12:00:00Z",
            },
            {
                "key": "pi-2",
                "instance_id": "PLANT-002",
                "plant_name": "Tomato #2",
                "species_key": "sp-1",
                "species_scientific_name": "Solanum lycopersicum",
                "location_name": "Greenhouse A",
                "slot_label": "Row 2, Pos 1",
                "current_phase_started_at": "2024-01-12T08:30:00Z",
            },
        ]
        plant_repo.list_active_in_phase_definition.return_value = rows

        result = _service(plant_repo).list_active_in_phase_definition("tenant-1", "pd-vegetative")

        assert len(result) == 2
        assert result[0]["instance_id"] == "PLANT-001"
        assert result[1]["instance_id"] == "PLANT-002"
        assert result[0]["location_name"] == "Greenhouse A"
        assert result[1]["slot_label"] == "Row 2, Pos 1"

    def test_preserves_all_plant_attributes(self) -> None:
        """FIX-01 R2: ensure all plant attributes required by frontend are present."""
        plant_repo = MagicMock()
        plant_data = {
            "key": "pi-42",
            "instance_id": "PLANT-042",
            "plant_name": "My Plant",
            "species_key": "sp-x",
            "species_scientific_name": "Genus species",
            "species_common_names": ["Common Name", "Autre nom"],
            "location_key": "loc-1",
            "location_name": "My Location",
            "slot_key": "slot-x",
            "slot_label": "Shelf 1",
            "current_phase_key": "pd-1",
            "current_phase_started_at": "2024-01-15T10:00:00Z",
        }
        plant_repo.list_active_in_phase_definition.return_value = [plant_data]

        result = _service(plant_repo).list_active_in_phase_definition("tenant-1", "pd-1")

        assert len(result) == 1
        plant = result[0]
        assert plant["key"] == "pi-42"
        assert plant["plant_name"] == "My Plant"
        assert plant["species_scientific_name"] == "Genus species"
        assert plant["current_phase_started_at"] == "2024-01-15T10:00:00Z"
