from app.common.exceptions import ValidationError
from app.domain.interfaces.location_type_repository import ILocationTypeRepository
from app.domain.models.location_type import LocationType
from app.domain.services.fields_kept_on_edit import keep_stored_fields

#: Location-type fields ``PUT /location-types/{key}`` does not carry, so
#: :meth:`LocationTypeService.update` takes them from the stored type. The route
#: rebuilds the model from ``LocationTypeUpdate``, which has no ``is_system``: every
#: edit wrote ``is_system=False``, and the next ``DELETE`` removed a seeded system
#: type the delete guard below exists to protect. Only the seed sets the flag.
LOCATION_TYPE_FIELDS_KEPT_ON_EDIT: tuple[str, ...] = ("is_system",)


class LocationTypeService:
    def __init__(self, repo: ILocationTypeRepository) -> None:
        self._repo = repo

    def list_all(self) -> list[LocationType]:
        return self._repo.get_all()

    def get(self, key: str) -> LocationType:
        lt = self._repo.get_or_raise(key)
        return lt

    def create(self, location_type: LocationType) -> LocationType:
        return self._repo.create(location_type)

    def update(self, key: str, location_type: LocationType) -> LocationType:
        """Rewrite a location type; a system type stays a system type."""
        existing = self.get(key)
        keep_stored_fields(location_type, existing, LOCATION_TYPE_FIELDS_KEPT_ON_EDIT)
        return self._repo.update(key, location_type)

    def delete(self, key: str) -> bool:
        existing = self.get(key)
        if existing.is_system:
            raise ValidationError("Cannot delete system location type")
        return self._repo.delete(key)
