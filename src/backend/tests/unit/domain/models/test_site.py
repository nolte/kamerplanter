import pytest
from pydantic import ValidationError

from app.domain.models.site import Site, Slot


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
