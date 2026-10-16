import pytest
from pydantic import ValidationError

from app.domain.models.site import Location, Site, Slot


class TestSiteValidation:
    def test_valid_gps(self):
        s = Site(name="Test", gps_coordinates=(52.5, 13.4))
        assert s.gps_coordinates == (52.5, 13.4)

    def test_invalid_latitude(self):
        with pytest.raises(ValidationError):
            Site(name="Test", gps_coordinates=(91.0, 0.0))

    def test_invalid_longitude(self):
        with pytest.raises(ValidationError):
            Site(name="Test", gps_coordinates=(0.0, 181.0))

    def test_none_gps(self):
        s = Site(name="Test", gps_coordinates=None)
        assert s.gps_coordinates is None


class TestSlotValidation:
    def test_valid_slot_id(self):
        s = Slot(slot_id="TENT01_A1")
        assert s.slot_id == "TENT01_A1"

    def test_lowercase_slot_id(self):
        with pytest.raises(ValidationError):
            Slot(slot_id="tent01_a1")

    def test_no_underscore(self):
        with pytest.raises(ValidationError):
            Slot(slot_id="TENT01A1")

    def test_capacity_range(self):
        s = Slot(slot_id="TENT01_A1", capacity_plants=10)
        assert s.capacity_plants == 10

    def test_capacity_too_high(self):
        with pytest.raises(ValidationError):
            Slot(slot_id="TENT01_A1", capacity_plants=21)

    def test_a_stored_legacy_position_is_ignored_on_read(self):
        """REQ-053 WP 1.5 (#2324): v0093 keeps ``position`` in the document, the model drops it.

        Pins the ``extra="ignore"`` default the removal relies on — a later
        ``extra="forbid"`` would turn every pre-M1 slot into a 500 on read.
        """
        s = Slot.model_validate({"_key": "s1", "slot_id": "TENT01_A1", "position": [0, 0]})

        assert not hasattr(s, "position")
        assert "position" not in s.model_dump(by_alias=True)


class TestLocationLegacyDocuments:
    def test_a_stored_legacy_dimensions_triple_is_ignored_on_read(self):
        """REQ-053 WP 1.5 (#2324): v0093 keeps ``dimensions`` in the document, the model drops it."""
        loc = Location.model_validate(
            {"_key": "l1", "name": "Tent", "site_key": "s1", "area_m2": 1.0, "dimensions": [1.2, 1.2, 2.0]}
        )

        assert not hasattr(loc, "dimensions")
        assert "dimensions" not in loc.model_dump(by_alias=True)
