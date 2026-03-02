import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.interfaces.location_type_repository import ILocationTypeRepository
from app.domain.models.location_type import LocationType
from app.domain.services.location_type_service import LocationTypeService


class FakeLocationTypeRepository(ILocationTypeRepository):
    def __init__(self) -> None:
        self._store: dict[str, LocationType] = {}
        self._counter = 0

    def get_all(self) -> list[LocationType]:
        return sorted(self._store.values(), key=lambda lt: lt.sort_order)

    def get_by_key(self, key: str) -> LocationType | None:
        return self._store.get(key)

    def create(self, location_type: LocationType) -> LocationType:
        self._counter += 1
        key = str(self._counter)
        lt = location_type.model_copy(update={"key": key})
        self._store[key] = lt
        return lt

    def update(self, key: str, location_type: LocationType) -> LocationType:
        lt = location_type.model_copy(update={"key": key})
        self._store[key] = lt
        return lt

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False


class TestLocationTypeService:
    def setup_method(self):
        self.repo = FakeLocationTypeRepository()
        self.service = LocationTypeService(self.repo)

    def test_create_and_list(self):
        lt = LocationType(name="Garden", sort_order=10)
        created = self.service.create(lt)
        assert created.key is not None
        assert created.name == "Garden"

        all_types = self.service.list_all()
        assert len(all_types) == 1

    def test_get(self):
        lt = LocationType(name="Room")
        created = self.service.create(lt)
        found = self.service.get(created.key)
        assert found.name == "Room"

    def test_get_not_found(self):
        with pytest.raises(NotFoundError):
            self.service.get("nonexistent")

    def test_update(self):
        lt = LocationType(name="Room")
        created = self.service.create(lt)
        updated = self.service.update(created.key, LocationType(name="Updated Room"))
        assert updated.name == "Updated Room"

    def test_delete(self):
        lt = LocationType(name="Temp")
        created = self.service.create(lt)
        result = self.service.delete(created.key)
        assert result is True
        assert len(self.service.list_all()) == 0

    def test_delete_system_raises(self):
        lt = LocationType(name="System Type", is_system=True)
        created = self.service.create(lt)
        with pytest.raises(ValidationError, match="Cannot delete system location type"):
            self.service.delete(created.key)

    def test_list_sorted_by_sort_order(self):
        self.service.create(LocationType(name="C", sort_order=30))
        self.service.create(LocationType(name="A", sort_order=10))
        self.service.create(LocationType(name="B", sort_order=20))
        all_types = self.service.list_all()
        assert [lt.name for lt in all_types] == ["A", "B", "C"]
