"""Issue #714 P2 — Null-preserving Location update to inherit from parent site.

AC-1–6: Tests for _LocationRepository.update which allows resetting
frost_exposed and other nullable fields to None (inherit from parent).
The override uses exclude_none=False and keep_none=False to ensure
null attributes are removed from the ArangoDB document.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from arango.exceptions import DocumentUpdateError

from app.common.enums import IrrigationSystem, LightType, Orientation
from app.common.exceptions import NotFoundError
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.site import Location


@pytest.fixture
def mock_db():
    """Mock ArangoDB database connection."""
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    """Instantiate ArangoSiteRepository with mock database."""
    return ArangoSiteRepository(mock_db)


def _make_location(**overrides) -> Location:
    """Factory for Location test instances."""
    data = {
        "name": "Test Location",
        "site_key": "site-1",
        "area_m2": 10.0,
        "light_type": LightType.NATURAL,
        "irrigation_system": IrrigationSystem.MANUAL,
        "frost_exposed": None,
    }
    data.update(overrides)
    return Location(**data)


class TestLocationUpdateNullReset:
    """AC-1: Resetting nullable fields (frost_exposed) to None inherits from parent."""

    def test_reset_frost_exposed_to_none_from_true(self, repo, mock_db):
        """Update a Location with frost_exposed=true to frost_exposed=None.

        The update payload must include frost_exposed: None (exclude_none=False).
        ArangoDB's keep_none=False removes the attribute, causing re-read to be None.
        """
        coll = mock_db.collection.return_value
        location = _make_location(frost_exposed=None)

        # Mock return: ArangoDB removes the attribute when keep_none=False
        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Test Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                # frost_exposed is absent (removed by keep_none=False)
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-1", location)

        # Verify the update call was made
        coll.update.assert_called_once()
        call_args = coll.update.call_args

        # Verify keep_none=False was passed
        assert call_args.kwargs.get("keep_none") is False

        # Verify return_new=True was passed
        assert call_args.kwargs.get("return_new") is True

        # Verify the payload contains frost_exposed: None
        payload = call_args.args[0]
        assert "frost_exposed" in payload
        assert payload["frost_exposed"] is None

        # Verify the result reads back with frost_exposed=None
        assert result.frost_exposed is None

    def test_reset_frost_exposed_to_none_from_false(self, repo, mock_db):
        """Update a Location with frost_exposed=false to frost_exposed=None."""
        coll = mock_db.collection.return_value
        location = _make_location(frost_exposed=None)

        coll.update.return_value = {
            "new": {
                "_key": "loc-2",
                "name": "Indoor Location",
                "site_key": "site-1",
                "area_m2": 5.0,
                "light_type": "led",
                "irrigation_system": IrrigationSystem.DRIP,
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-2", location)

        # Payload must include frost_exposed: None
        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["frost_exposed"] is None

        # Result reads back as None
        assert result.frost_exposed is None


class TestLocationUpdateTrueFalseToggle:
    """AC-2: Setting frost_exposed to true or false persists correctly."""

    def test_set_frost_exposed_to_true(self, repo, mock_db):
        """Update frost_exposed from None to true."""
        coll = mock_db.collection.return_value
        location = _make_location(frost_exposed=True)

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Test Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "frost_exposed": True,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-1", location)

        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["frost_exposed"] is True

        assert result.frost_exposed is True

    def test_set_frost_exposed_to_false(self, repo, mock_db):
        """Update frost_exposed from None/true to false."""
        coll = mock_db.collection.return_value
        location = _make_location(frost_exposed=False)

        coll.update.return_value = {
            "new": {
                "_key": "loc-2",
                "name": "Protected Location",
                "site_key": "site-1",
                "area_m2": 8.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "frost_exposed": False,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-2", location)

        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["frost_exposed"] is False

        assert result.frost_exposed is False


class TestLocationUpdateOtherNullableFields:
    """AC-3: Other nullable fields (tank_key, orientation) can be reset to None."""

    def test_reset_tank_key_to_none(self, repo, mock_db):
        """Update tank_key from a value to None."""
        coll = mock_db.collection.return_value
        location = _make_location(tank_key=None)

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Test Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                # tank_key absent (removed by keep_none=False)
                "frost_exposed": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-1", location)

        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["tank_key"] is None

        assert result.tank_key is None

    def test_set_tank_key_to_value(self, repo, mock_db):
        """Update tank_key from None to a value."""
        coll = mock_db.collection.return_value
        location = _make_location(tank_key="tank-123")

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Test Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": "tank-123",
                "frost_exposed": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-1", location)

        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["tank_key"] == "tank-123"

        assert result.tank_key == "tank-123"

    def test_reset_orientation_to_none(self, repo, mock_db):
        """Update orientation from a value to None."""
        coll = mock_db.collection.return_value
        location = _make_location(orientation=None)

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Test Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                # orientation absent (removed by keep_none=False)
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "frost_exposed": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-1", location)

        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["orientation"] is None

        assert result.orientation is None

    def test_set_orientation_to_value(self, repo, mock_db):
        """Update orientation from None to a value."""
        coll = mock_db.collection.return_value
        location = _make_location(orientation=Orientation.NORTH)

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Test Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": "north",
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "frost_exposed": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-1", location)

        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["orientation"] == "north"

        assert result.orientation == Orientation.NORTH


class TestLocationUpdateNonNullFields:
    """AC-4: Non-nullable fields (name, area_m2, light_type, irrigation_system) survive update."""

    def test_non_null_fields_survive_round_trip(self, repo, mock_db):
        """Update location with non-null fields — they persist unchanged."""
        coll = mock_db.collection.return_value
        location = _make_location(
            name="Greenhouse A",
            area_m2=25.5,
            light_type=LightType.LED,
            irrigation_system=IrrigationSystem.DRIP,
        )

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Greenhouse A",
                "site_key": "site-1",
                "area_m2": 25.5,
                "light_type": "led",
                "irrigation_system": "drip",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "frost_exposed": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-1", location)

        # Non-null fields are in the payload
        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["name"] == "Greenhouse A"
        assert payload["area_m2"] == 25.5
        assert payload["light_type"] == "led"
        assert payload["irrigation_system"] == "drip"

        # Non-null fields survive the round trip
        assert result.name == "Greenhouse A"
        assert result.area_m2 == 25.5
        assert result.light_type == LightType.LED
        assert result.irrigation_system == IrrigationSystem.DRIP


class TestLocationUpdateComputedFields:
    """AC-5: Computed fields (site_key, depth, path) are not corrupted by update."""

    def test_computed_fields_preserved(self, repo, mock_db):
        """Update location — computed/structural fields remain as-is."""
        coll = mock_db.collection.return_value
        location = _make_location(
            site_key="site-1",
            depth=2,
            path="site-1.bed-1.shelf-1",
        )

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Shelf Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": "bed-1",
                "location_type_key": "",
                "depth": 2,
                "path": "site-1.bed-1.shelf-1",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "frost_exposed": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        result = repo.update_location("loc-1", location)

        # Computed fields are in the payload (for consistency)
        call_args = coll.update.call_args
        payload = call_args.args[0]
        assert payload["site_key"] == "site-1"
        assert payload["depth"] == 2
        assert payload["path"] == "site-1.bed-1.shelf-1"

        # Computed fields survive the round trip
        assert result.site_key == "site-1"
        assert result.depth == 2
        assert result.path == "site-1.bed-1.shelf-1"


class TestLocationUpdateNotFound:
    """AC-6: Update on non-existent location raises NotFoundError."""

    def _make_document_update_error(self, error_code: int) -> DocumentUpdateError:
        """Create a DocumentUpdateError with the given error_code for testing.

        Since DocumentUpdateError requires Response/Request objects, we construct
        a minimal subclass that simulates the error_code attribute.
        """

        class TestDocumentUpdateError(DocumentUpdateError):
            def __init__(self, error_code: int):
                # Don't call parent __init__ to avoid needing Response/Request
                self.error_code = error_code

        return TestDocumentUpdateError(error_code)

    def test_update_nonexistent_location_raises_not_found(self, repo, mock_db):
        """Update a location with unknown key — raises NotFoundError."""
        coll = mock_db.collection.return_value
        location = _make_location()

        # Simulate ArangoDB error 1202 (document not found).
        coll.update.side_effect = self._make_document_update_error(1202)

        with pytest.raises(NotFoundError) as exc_info:
            repo.update_location("nonexistent-key", location)

        assert exc_info.value.error_code == "ENTITY_NOT_FOUND"
        assert "nonexistent-key" in str(exc_info.value)

    def test_update_other_arango_error_propagates(self, repo, mock_db):
        """Update encountering other ArangoDB errors (not 1202) re-raises."""
        coll = mock_db.collection.return_value
        location = _make_location()

        # Simulate some other ArangoDB error (e.g., 400 bad request).
        # This tests that only error_code==1202 triggers NotFoundError conversion;
        # other DocumentUpdateErrors are re-raised.
        coll.update.side_effect = self._make_document_update_error(400)

        with pytest.raises(DocumentUpdateError) as exc_info:
            repo.update_location("loc-1", location)

        # Verify it's not NotFoundError (which would have been raised for 1202)
        assert not isinstance(exc_info.value, NotFoundError)
        # Verify the exact exception was the one we set up (error_code=400)
        assert exc_info.value.error_code == 400


class TestLocationUpdateExcludeNoneAndKeepNoneFlags:
    """Verify the null-handling flags in the update call."""

    def test_exclude_none_false_in_payload(self, repo, mock_db):
        """The _LocationRepository.update uses exclude_none=False in model_dump."""
        coll = mock_db.collection.return_value
        location = _make_location(
            frost_exposed=None,
            tank_key=None,
            orientation=None,
        )

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Test Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "frost_exposed": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        repo.update_location("loc-1", location)

        call_args = coll.update.call_args
        payload = call_args.args[0]

        # All nullable fields must be present in the payload with None value
        assert "frost_exposed" in payload
        assert payload["frost_exposed"] is None
        assert "tank_key" in payload
        assert payload["tank_key"] is None
        assert "orientation" in payload
        assert payload["orientation"] is None

    def test_keep_none_false_passed_to_collection_update(self, repo, mock_db):
        """The _LocationRepository.update passes keep_none=False to collection.update."""
        coll = mock_db.collection.return_value
        location = _make_location(frost_exposed=None)

        coll.update.return_value = {
            "new": {
                "_key": "loc-1",
                "name": "Test Location",
                "site_key": "site-1",
                "area_m2": 10.0,
                "light_type": "natural",
                "irrigation_system": "manual",
                "tenant_key": "",
                "parent_location_key": None,
                "location_type_key": "",
                "depth": 0,
                "path": "",
                "orientation": None,
                "dimensions": [0.0, 0.0, 0.0],
                "lights_on": None,
                "lights_off": None,
                "use_dynamic_sunrise": False,
                "tank_key": None,
                "frost_exposed": None,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        }

        repo.update_location("loc-1", location)

        call_args = coll.update.call_args
        assert call_args.kwargs.get("keep_none") is False
