
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.sensor_repository import ISensorRepository
from app.domain.models.sensor import Sensor

if TYPE_CHECKING:
    from arango.database import StandardDatabase


class ArangoSensorRepository(ISensorRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.SENSORS)

    def create(self, sensor: Sensor) -> Sensor:
        doc = BaseArangoRepository.create(self, sensor)
        created = Sensor(**doc)
        sensor_id = f"{col.SENSORS}/{doc['_key']}"
        # Create monitors_tank edge
        if sensor.tank_key:
            to_id = f"{col.TANKS}/{sensor.tank_key}"
            self.create_edge(col.MONITORS_TANK, sensor_id, to_id)
        # Create located_at edge for site or location
        if sensor.site_key:
            to_id = f"{col.SITES}/{sensor.site_key}"
            self.create_edge(col.LOCATED_AT, sensor_id, to_id)
        elif sensor.location_key:
            to_id = f"{col.LOCATIONS}/{sensor.location_key}"
            self.create_edge(col.LOCATED_AT, sensor_id, to_id)
        return created

    def get(self, key: str) -> Sensor | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Sensor(**doc) if doc else None

    def update(self, key: str, sensor: Sensor) -> Sensor:
        doc = BaseArangoRepository.update(self, key, sensor)
        return Sensor(**doc)

    def find_by_tank(self, tank_key: str) -> list[Sensor]:
        query = """
        FOR s IN @@collection
          FILTER s.tank_key == @tank_key AND s.is_active == true
          RETURN s
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.SENSORS,
            "tank_key": tank_key,
        })
        return [Sensor(**self._from_doc(doc)) for doc in cursor]

    def find_by_site(self, site_key: str) -> list[Sensor]:
        query = """
        FOR s IN @@collection
          FILTER s.site_key == @site_key AND s.is_active == true
          RETURN s
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.SENSORS,
            "site_key": site_key,
        })
        return [Sensor(**self._from_doc(doc)) for doc in cursor]

    def find_by_location(self, location_key: str) -> list[Sensor]:
        query = """
        FOR s IN @@collection
          FILTER s.location_key == @location_key AND s.is_active == true
          RETURN s
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.SENSORS,
            "location_key": location_key,
        })
        return [Sensor(**self._from_doc(doc)) for doc in cursor]

    def delete(self, key: str) -> bool:
        # Clean up monitors_tank and located_at edges
        sensor_id = f"{col.SENSORS}/{key}"
        self.delete_edges(col.MONITORS_TANK, sensor_id)
        self.delete_edges(col.LOCATED_AT, sensor_id)
        return BaseArangoRepository.delete(self, key)
