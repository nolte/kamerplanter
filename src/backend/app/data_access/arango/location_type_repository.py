from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.location_type_repository import ILocationTypeRepository
from app.domain.models.location_type import LocationType


class ArangoLocationTypeRepository(ILocationTypeRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.LOCATION_TYPES)

    def get_all(self) -> list[LocationType]:
        query = f"FOR doc IN {col.LOCATION_TYPES} SORT doc.sort_order ASC RETURN doc"
        cursor = self._db.aql.execute(query)
        return [LocationType(**self._from_doc(doc)) for doc in cursor]

    def get_by_key(self, key: str) -> LocationType | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return LocationType(**doc) if doc else None

    def create(self, location_type: LocationType) -> LocationType:
        doc = BaseArangoRepository.create(self, location_type)
        return LocationType(**doc)

    def update(self, key: str, location_type: LocationType) -> LocationType:
        doc = BaseArangoRepository.update(self, key, location_type)
        return LocationType(**doc)

    def delete(self, key: str) -> bool:
        return BaseArangoRepository.delete(self, key)
