from datetime import datetime
from typing import Any

import structlog

from app.common.exceptions import NotFoundError
from app.domain.interfaces.observation_repository import IObservationRepository
from app.domain.interfaces.sensor_repository import ISensorRepository
from app.domain.models.observation import AggregatedReading, SensorReading
from app.domain.services.location_ownership import SiteAnchorSource, find_owned_location

logger = structlog.get_logger(__name__)


class ObservationService:
    def __init__(
        self,
        observation_repo: IObservationRepository,
        sensor_repo: ISensorRepository,
        *,
        tank_repo: Any | None = None,
        site_anchors: SiteAnchorSource | None = None,
    ) -> None:
        self._obs_repo = observation_repo
        self._sensor_repo = sensor_repo
        # The reads that decide whose a sensor is (#1871 B6). A sensor carries no
        # tenant_key; its parent does. Without them a reading is refused.
        self._tank_repo = tank_repo
        self._site_anchors = site_anchors

    def _require_owned_sensor(self, sensor_key: str, *, tenant_key: str) -> None:
        """Refuse a sensor that is not the tenant's (#1871 B6).

        The single-reading route checked only that the sensor existed (a foreign
        one answered 201, an unknown one 404), the batch route nothing. The
        sensor's tenant is its parent's: the tank's, the site's, or — through its
        site — the location's (#1397). A sensor without a parent, a foreign one
        and an unknown one all answer the same 404.
        """
        sensor = self._sensor_repo.get(sensor_key) if sensor_key else None
        owner: str | None = None
        if sensor is not None and self._site_anchors is not None:
            if sensor.tank_key and self._tank_repo is not None:
                tank = self._tank_repo.get_by_key(sensor.tank_key)
                owner = tank.tenant_key if tank is not None else None
            elif sensor.site_key:
                site = self._site_anchors.get_site_by_key(sensor.site_key)
                owner = site.tenant_key if site is not None else None
            elif sensor.location_key:
                if find_owned_location(self._site_anchors, sensor.location_key, tenant_key) is not None:
                    owner = tenant_key
        if not tenant_key or owner != tenant_key:
            raise NotFoundError("Sensor", sensor_key)

    def record_reading(self, reading: SensorReading, *, tenant_key: str) -> None:
        self._require_owned_sensor(reading.sensor_key, tenant_key=tenant_key)
        self._obs_repo.insert(reading)

    def record_readings_batch(self, sensor_key: str, readings: list[SensorReading], *, tenant_key: str) -> int:
        """Record ``readings`` for ``sensor_key`` — every reading must name that sensor."""
        self._require_owned_sensor(sensor_key, tenant_key=tenant_key)
        if any(r.sensor_key != sensor_key for r in readings):
            raise NotFoundError("Sensor", sensor_key)
        return self._obs_repo.insert_batch(readings)

    def get_readings(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
        resolution: str = "raw",
    ) -> list[SensorReading] | list[AggregatedReading]:
        if resolution == "hourly":
            return self._obs_repo.query_hourly(sensor_key, start, end, tenant_key)
        if resolution == "daily":
            return self._obs_repo.query_daily(sensor_key, start, end, tenant_key)
        return self._obs_repo.query_raw(sensor_key, start, end, tenant_key)

    def get_latest_reading(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> SensorReading | None:
        return self._obs_repo.get_latest(sensor_key, tenant_key)

    def delete_readings_for_sensor(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> int:
        return self._obs_repo.delete_by_sensor(sensor_key, tenant_key)

    def is_available(self) -> bool:
        return self._obs_repo.is_available()
