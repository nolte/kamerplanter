from datetime import datetime
from typing import Any

import structlog

from app.common.exceptions import NotFoundError
from app.domain.interfaces.observation_repository import IObservationRepository
from app.domain.interfaces.sensor_repository import ISensorRepository
from app.domain.models.observation import AggregatedReading, SensorReading
from app.domain.services.location_ownership import SiteAnchorSource

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

    def _owner_of(self, sensor_key: str) -> str | None:
        """The tenant a sensor belongs to — its parent's — or ``None`` when it has none or is on its way out (#1871 B6).

        A sensor carries no ``tenant_key``; its parent does: the tank's, the
        site's, or — through its site — the location's (#1397). A sensor whose
        delete began (``deletion_pending``, #1944) has no owner for ingest: its
        series is being erased and must not grow back.
        """
        sensor = self._sensor_repo.get(sensor_key) if sensor_key else None
        if sensor is None or sensor.deletion_pending or self._site_anchors is None:
            return None
        if sensor.tank_key and self._tank_repo is not None:
            tank = self._tank_repo.get_by_key(sensor.tank_key)
            return tank.tenant_key if tank is not None else None
        if sensor.site_key:
            site = self._site_anchors.get_site_by_key(sensor.site_key)
            return site.tenant_key if site is not None else None
        if sensor.location_key:
            location = self._site_anchors.get_location_by_key(sensor.location_key)
            site = self._site_anchors.get_site_by_key(location.site_key) if location and location.site_key else None
            return site.tenant_key if site is not None else None
        return None

    def owning_tenant_key(self, sensor_key: str) -> str | None:
        """The tenant a sensor's readings are stored under, or ``None`` when the sensor takes none (#1944).

        For the callers that have the sensor but not a request context — the Home
        Assistant poll. A sensor document has no ``tenant_key`` of its own; a poll
        that read ``doc.get("tenant_key", "")`` stored every reading under ``''``,
        which no tenant or sensor erasure reaches.
        """
        return self._owner_of(sensor_key) or None

    def _require_owned_sensor(self, sensor_key: str, *, tenant_key: str) -> None:
        """Refuse a sensor that is not the tenant's (#1871 B6).

        The single-reading route checked only that the sensor existed (a foreign
        one answered 201, an unknown one 404), the batch route nothing. A sensor
        without a parent, a foreign one, an unknown one and one whose delete began
        all answer the same 404.
        """
        owner = self._owner_of(sensor_key)
        if not tenant_key or owner != tenant_key:
            raise NotFoundError("Sensor", sensor_key)

    def _settle_after_insert(self, sensor_key: str, *, tenant_key: str) -> None:
        """Ask again once the readings are in, and take them back if the sensor went meanwhile (#1944).

        The ownership check before the insert and the insert are two steps: a
        sensor or tenant erasure that ran between them — the ArangoDB phase of a
        tenant erasure removes the sensors *before* its readings purge, and a
        sensor delete purges the readings and then the document — would have its
        purge overtaken by a reading that creates a raw row and, once the
        aggregates refresh, buckets for an owner nothing reaches again. A reading
        that finds its sensor gone is purged together with whatever else the
        series holds (it is the sensor's own series, being erased anyway) and the
        request answers like a refused one.
        """
        try:
            self._require_owned_sensor(sensor_key, tenant_key=tenant_key)
        except NotFoundError:
            self._obs_repo.delete_by_sensor(sensor_key, tenant_key)
            raise

    def record_reading(self, reading: SensorReading, *, tenant_key: str) -> None:
        self._require_owned_sensor(reading.sensor_key, tenant_key=tenant_key)
        self._obs_repo.insert(reading)
        self._settle_after_insert(reading.sensor_key, tenant_key=tenant_key)

    def record_readings_batch(self, sensor_key: str, readings: list[SensorReading], *, tenant_key: str) -> int:
        """Record ``readings`` for ``sensor_key`` — every reading must name that sensor."""
        self._require_owned_sensor(sensor_key, tenant_key=tenant_key)
        if any(r.sensor_key != sensor_key for r in readings):
            raise NotFoundError("Sensor", sensor_key)
        inserted = self._obs_repo.insert_batch(readings)
        self._settle_after_insert(sensor_key, tenant_key=tenant_key)
        return inserted

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
