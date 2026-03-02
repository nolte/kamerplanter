from app.common.exceptions import NotFoundError, ValidationError
from app.domain.interfaces.location_type_repository import ILocationTypeRepository
from app.domain.models.location_type import LocationType


class LocationTypeService:
    def __init__(self, repo: ILocationTypeRepository) -> None:
        self._repo = repo

    def list_all(self) -> list[LocationType]:
        return self._repo.get_all()

    def get(self, key: str) -> LocationType:
        lt = self._repo.get_by_key(key)
        if lt is None:
            raise NotFoundError("LocationType", key)
        return lt

    def create(self, location_type: LocationType) -> LocationType:
        return self._repo.create(location_type)

    def update(self, key: str, location_type: LocationType) -> LocationType:
        self.get(key)
        return self._repo.update(key, location_type)

    def delete(self, key: str) -> bool:
        existing = self.get(key)
        if existing.is_system:
            raise ValidationError("Cannot delete system location type")
        return self._repo.delete(key)
