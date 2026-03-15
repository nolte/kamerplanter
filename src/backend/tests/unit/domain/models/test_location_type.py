from app.domain.models.location_type import LocationType


class TestLocationType:
    def test_create_minimal(self):
        lt = LocationType(name="Test Type")
        assert lt.name == "Test Type"
        assert lt.key is None
        assert lt.name_en is None
        assert lt.icon is None
        assert lt.is_indoor is False
        assert lt.is_system is False
        assert lt.sort_order == 0
        assert lt.description is None

    def test_create_full(self):
        lt = LocationType(
            name="Zimmer",
            name_en="Room",
            icon="MeetingRoom",
            is_indoor=True,
            is_system=True,
            sort_order=40,
            description="Ein Raum in einem Gebäude",
        )
        assert lt.name == "Zimmer"
        assert lt.name_en == "Room"
        assert lt.icon == "MeetingRoom"
        assert lt.is_indoor is True
        assert lt.is_system is True
        assert lt.sort_order == 40

    def test_key_alias(self):
        lt = LocationType(_key="room", name="Zimmer")
        assert lt.key == "room"

    def test_populate_by_name(self):
        lt = LocationType(key="room", name="Zimmer")
        assert lt.key == "room"
