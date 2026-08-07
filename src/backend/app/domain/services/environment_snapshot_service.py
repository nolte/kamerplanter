"""REQ-013 §2.3a — the environment snapshot captured with a diary entry.

A diary entry records *what the grower saw*. Until now it recorded nothing about
*the conditions the plant was in when they saw it*, although the system usually
already knows: a :class:`~app.domain.models.plant_instance.PlantInstance` names a
site and a location, and a :class:`~app.domain.models.sensor.Sensor` hangs off one
of them. This service is the bridge, and it resolves the values **server-side**
from the plant's own location — never from the request body, because a value the
client can write is a value the client can invent, and this one is meant to be
evidence.

**The chain is REQ-005 §2's, not a new one** (§3.1 of the requirement):

1. the plant's **location** sensors — live through Home Assistant, falling back
   to the latest persisted observation when HA is unconfigured or the entity
   reports ``unavailable`` / ``unknown``;
2. the plant's **site** sensors, for the metrics the location could not answer;
3. **current outdoor conditions** for an outdoor site — the REQ-046
   ``WeatherForecast`` record flagged ``is_current_conditions``, for air
   temperature and humidity only, because that is what such a record carries;
4. **nothing**. No fabricated value, no ``0.0`` — the same promise
   ``get_location_frost_warning`` already keeps when it reports
   ``source: "no_temperature"``.

``slot_key`` has **no** level of its own: a sensor cannot be attached to a slot,
so the chain starts at the location. That is a property of the data model, not an
oversight.

Four properties carry the design:

* **The capture never fails the write.** A grower documenting a problem is the
  worst possible moment to refuse an entry because a sensor is down. Every
  failure mode — HA unreachable, TimescaleDB absent, a repository raising, the
  budget running out — degrades to a snapshot with
  :attr:`~app.common.enums.DiaryEnvironmentStatus.UNAVAILABLE` and whatever
  arrived, and the entry is written regardless.
* **An empty list is never ambiguous.** ``no_source`` (the chain ran and nothing
  covers this plant) and ``unavailable`` (the chain was cut short) are different
  statements, and a reader has to be able to tell them apart — see
  :class:`~app.common.enums.DiaryEnvironmentStatus`.
* **Stale readings are dropped, not stored.** A value whose measurement is older
  than ``settings.diary_environment_max_age_minutes`` is not captured at all. An
  entry that claims "22 °C" from a sensor that last spoke yesterday is worse
  evidence than an entry with no climate at all.
* **The capture is bounded in wall-clock time.** Every outbound read gets at most
  the remainder of ``settings.diary_environment_capture_timeout_seconds``, so the
  create path cannot hang behind a sensor.

**Freshness comes from ``last_reported``, not ``last_changed``.** Home Assistant's
``last_changed`` moves only when the state *string* changes, so a healthy sensor
reporting a constant 22.0 °C carries a ``last_changed`` that is hours old;
``last_updated`` has nearly the same problem. ``last_reported`` (HA ≥ 2024.6)
moves on every report and is the only one that answers "when was this measured".
The three are tried in that order, so an older Home Assistant still works — it is
merely more likely to have its constant readings judged stale, which is the safe
direction to be wrong in. That order lives in
:mod:`app.domain.engines.live_state` now, because the live state's own
single-value view ranks readings by the same instant and the two must not drift.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import structlog

from app.common.datetimes import ensure_aware_utc, now_utc
from app.common.enums import DiaryEnvironmentOrigin, DiaryEnvironmentStatus
from app.common.exceptions import NotFoundError
from app.config.settings import settings
from app.domain.engines.live_state import reading_measured_at, sort_readings
from app.domain.engines.sensor_metrics import is_air_temperature, is_humidity
from app.domain.models.plant_diary_entry import DiaryEnvironmentReading

if TYPE_CHECKING:
    from app.domain.interfaces.observation_repository import IObservationRepository
    from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
    from app.domain.interfaces.sensor_repository import ISensorRepository
    from app.domain.interfaces.site_repository import ISiteRepository
    from app.domain.interfaces.weather_forecast_repository import IWeatherForecastRepository
    from app.domain.models.plant_instance import PlantInstance
    from app.domain.models.sensor import Sensor
    from app.domain.models.weather import WeatherForecast
    from app.domain.services.sensor_service import SensorService

logger = structlog.get_logger(__name__)

#: Metric type stamped on an air temperature taken from a weather record. The
#: canonical location-sensor spelling is reused on purpose: a consumer that plots
#: "the temperature around this entry" must not have to know which level answered.
WEATHER_TEMPERATURE_METRIC_TYPE = "temperature_celsius"
#: Metric type stamped on a humidity taken from a weather record.
WEATHER_HUMIDITY_METRIC_TYPE = "humidity_percent"


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """The result of one capture attempt — readings plus how it went."""

    readings: list[DiaryEnvironmentReading]
    status: DiaryEnvironmentStatus
    #: When the capture ran. ``None`` only when none ran at all, i.e. for
    #: ``not_attempted`` and ``opted_out``.
    captured_at: datetime | None

    @classmethod
    def not_attempted(cls) -> EnvironmentSnapshot:
        return cls(readings=[], status=DiaryEnvironmentStatus.NOT_ATTEMPTED, captured_at=None)

    @classmethod
    def opted_out(cls) -> EnvironmentSnapshot:
        return cls(readings=[], status=DiaryEnvironmentStatus.OPTED_OUT, captured_at=None)


class EnvironmentSnapshotService:
    """Resolves the environment a plant is standing in, right now.

    Every collaborator except the plant and sensor repositories is optional and
    the chain simply skips the level it cannot reach — an installation without
    TimescaleDB, without weather sources or without Home Assistant still produces
    an honest (possibly empty) snapshot rather than an error.

    **Tenant isolation.** The plant is the anchor: it is loaded and its
    ``tenant_key`` compared fail-closed against the caller's before anything else
    happens, so every subsequent lookup starts from a location/site key that
    demonstrably belongs to this tenant. The observation and weather reads are
    additionally tenant-scoped in their own right (they take ``tenant_key``), and
    the site is re-checked against the tenant before its forecast is read. A
    ``Sensor`` carries no ``tenant_key`` of its own — its parent location does —
    which is precisely why the plant check is not optional.
    """

    def __init__(
        self,
        plant_repo: IPlantInstanceRepository,
        sensor_repo: ISensorRepository,
        sensor_service: SensorService,
        observation_repo: IObservationRepository | None = None,
        weather_forecast_repo: IWeatherForecastRepository | None = None,
        site_repo: ISiteRepository | None = None,
    ) -> None:
        self._plant_repo = plant_repo
        self._sensor_repo = sensor_repo
        self._sensor_service = sensor_service
        self._observation_repo = observation_repo
        self._weather_forecast_repo = weather_forecast_repo
        self._site_repo = site_repo

    # ── Public API ───────────────────────────────────────────────────────

    def capture_for_plant(self, plant_key: str, *, tenant_key: str) -> EnvironmentSnapshot:
        """Resolve the snapshot for ``plant_key``, or degrade trying.

        Raises nothing. A ``NotFoundError`` for the plant, a repository that
        blows up, a Home Assistant that hangs — all of it collapses into an
        ``unavailable`` snapshot, because the caller behind this is a diary
        create and it must go through.
        """
        if not settings.diary_environment_capture_enabled:
            return EnvironmentSnapshot.not_attempted()
        started = now_utc()
        deadline = time.monotonic() + settings.diary_environment_capture_timeout_seconds
        try:
            readings, degraded = self._resolve(plant_key, tenant_key=tenant_key, deadline=deadline)
        except Exception as exc:  # noqa: BLE001 — a capture must never fail a write
            logger.warning(
                "diary_environment_capture_failed",
                plant_key=plant_key,
                tenant_key=tenant_key,
                error=str(exc),
            )
            return EnvironmentSnapshot(
                readings=[],
                status=DiaryEnvironmentStatus.UNAVAILABLE,
                captured_at=started,
            )
        if degraded:
            status = DiaryEnvironmentStatus.UNAVAILABLE
        elif readings:
            status = DiaryEnvironmentStatus.CAPTURED
        else:
            status = DiaryEnvironmentStatus.NO_SOURCE
        return EnvironmentSnapshot(readings=readings, status=status, captured_at=started)

    def preview_for_plant(self, plant_key: str, *, tenant_key: str) -> EnvironmentSnapshot:
        """What a capture *would* yield right now — for the create dialog.

        Deliberately the very same code path as :meth:`capture_for_plant`, so the
        preview cannot promise something the capture then does not store. Unlike
        the capture it is reached through an ordinary GET endpoint, where a plant
        of another tenant has to answer 404 rather than an empty snapshot; the
        route resolves the plant itself for that, and this method then re-does the
        check fail-closed anyway.
        """
        return self.capture_for_plant(plant_key, tenant_key=tenant_key)

    # ── The chain ────────────────────────────────────────────────────────

    def _resolve(
        self,
        plant_key: str,
        *,
        tenant_key: str,
        deadline: float,
    ) -> tuple[list[DiaryEnvironmentReading], bool]:
        """Walk the REQ-005 chain. Returns ``(readings, degraded)``."""
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None or plant.tenant_key != tenant_key:
            # Not an error state of the capture: from here there is simply no
            # plant to resolve an environment for. The caller (create/preview)
            # has already refused a foreign plant with a 404 of its own.
            raise NotFoundError("PlantInstance", plant_key)

        max_age = timedelta(minutes=settings.diary_environment_max_age_minutes)
        readings: list[DiaryEnvironmentReading] = []
        degraded = False

        if plant.location_key:
            level_readings, level_degraded = self._read_sensor_level(
                self._sensor_repo.find_by_location(plant.location_key),
                origin=DiaryEnvironmentOrigin.LOCATION,
                tenant_key=tenant_key,
                max_age=max_age,
                deadline=deadline,
                already_answered=set(),
            )
            readings.extend(level_readings)
            degraded = degraded or level_degraded

        if plant.site_key:
            level_readings, level_degraded = self._read_sensor_level(
                self._sensor_repo.find_by_site(plant.site_key),
                origin=DiaryEnvironmentOrigin.SITE,
                tenant_key=tenant_key,
                max_age=max_age,
                deadline=deadline,
                already_answered={r.metric_type for r in readings},
            )
            readings.extend(level_readings)
            degraded = degraded or level_degraded

        weather_readings, weather_degraded = self._read_weather_level(
            plant,
            tenant_key=tenant_key,
            max_age=max_age,
            deadline=deadline,
            captured=readings,
        )
        readings.extend(weather_readings)
        degraded = degraded or weather_degraded

        return readings, degraded

    def _read_sensor_level(
        self,
        sensors: list[Sensor],
        *,
        origin: DiaryEnvironmentOrigin,
        tenant_key: str,
        max_age: timedelta,
        deadline: float,
        already_answered: set[str],
    ) -> tuple[list[DiaryEnvironmentReading], bool]:
        """Read one level of the chain (location or site).

        There is no allow-list of "interesting" metrics. A sensor is on this
        location because the grower put it there, so whatever it measures
        describes the plant's environment, and ``metric_type`` is recorded
        verbatim. Curating the set here would have meant a *third* private
        metric-name heuristic next to the two this change already unified —
        and it would silently drop the CO₂ probe somebody paid for.

        ``already_answered`` carries the metric types the closer level produced:
        the fallback is per metric (REQ-005 §2), so a site humidity sensor still
        contributes when the location only has a thermometer.

        **One reading per metric, chosen deliberately.** A diary entry records
        "the temperature this plant stood in", so the snapshot files one value per
        metric even where the location carries two thermometers — both survive in
        the live state (Issue #977), and the *snapshot* picks among them by the
        shared rule instead of by repository order: the freshest live reading
        wins, and a candidate whose live value is missing, non-numeric or stale
        hands the metric to the next one instead of ending it. Only when no
        candidate of the metric has a usable live reading does the persisted
        fallback run, on the first candidate, as before.
        """
        candidates = [s for s in sensors if s.is_active and s.key and s.metric_type not in already_answered]
        if not candidates:
            return [], False

        degraded = False
        live: dict = {"readings": {}, "values": {}, "errors": [], "source": "unavailable"}
        if time.monotonic() < deadline:
            try:
                live = self._sensor_service.get_live_state_for_sensors(candidates, deadline=deadline)
            except Exception as exc:  # noqa: BLE001 — never fails the write
                logger.warning("diary_environment_live_read_failed", origin=str(origin), error=str(exc))
                degraded = True
        else:
            degraded = True
        if live.get("errors"):
            # HA answered for some entities and not for others, or the budget ran
            # out mid-loop. ``source == "unavailable"`` is NOT an error: it means
            # Home Assistant is not configured, which is a normal deployment.
            degraded = True

        grouped: dict[str, list[Sensor]] = {}
        for sensor in candidates:
            grouped.setdefault(sensor.metric_type, []).append(sensor)

        readings: list[DiaryEnvironmentReading] = []
        for group in grouped.values():
            reading, group_degraded = self._read_metric_group(
                group,
                live_readings=live.get("readings", {}),
                origin=origin,
                tenant_key=tenant_key,
                max_age=max_age,
                deadline=deadline,
            )
            degraded = degraded or group_degraded
            if reading is not None:
                readings.append(reading)
        return readings, degraded

    def _read_metric_group(
        self,
        group: list[Sensor],
        *,
        live_readings: dict,
        origin: DiaryEnvironmentOrigin,
        tenant_key: str,
        max_age: timedelta,
        deadline: float,
    ) -> tuple[DiaryEnvironmentReading | None, bool]:
        """Resolve the one reading for a metric from the sensors that measure it.

        The live lookup is **by sensor key**, so the value a sensor gets is the
        value that sensor reported — full stop. It used to be a lookup by metric
        type followed by an ``entity_id`` comparison, and that comparison was a
        real defect: the live map kept the *last* sensor of a metric while this
        method kept the *first*, so whenever the two disagreed the comparison
        failed and a perfectly good live value was silently replaced by a stored
        observation, or by nothing (Issue #977). Two maps cannot disagree about
        which sensor a reading belongs to when the reading is filed under the
        sensor.
        """
        by_key = {sensor.key: sensor for sensor in group if sensor.key}
        live_for_group = [live_readings[key] for key in by_key if key in live_readings]
        for live in sort_readings(live_for_group):
            sensor = by_key.get(str(live.get("sensor_key")))
            if sensor is None:
                continue
            reading = self._live_reading(sensor, live, origin=origin, max_age=max_age)
            if reading is not None:
                return reading, False

        return self._read_stored_reading(
            group[0],
            origin=origin,
            tenant_key=tenant_key,
            max_age=max_age,
            deadline=deadline,
        )

    @staticmethod
    def _live_reading(
        sensor: Sensor,
        live: dict,
        *,
        origin: DiaryEnvironmentOrigin,
        max_age: timedelta,
    ) -> DiaryEnvironmentReading | None:
        """The live reading of one sensor, or ``None`` when it is unusable.

        Unusable means: no numeric value (Home Assistant reports ``unavailable`` /
        ``unknown`` as the state), no timestamp at all, or older than the
        staleness bound.
        """
        value = _as_float(live.get("value"))
        measured_at = reading_measured_at(live)
        if value is None or measured_at is None or now_utc() - measured_at > max_age:
            return None
        return DiaryEnvironmentReading(
            metric_type=sensor.metric_type,
            value=value,
            unit=live.get("unit") or sensor.unit_of_measurement,
            source="ha_auto",
            measured_at=measured_at,
            sensor_key=sensor.key,
            origin=origin,
        )

    def _read_stored_reading(
        self,
        sensor: Sensor,
        *,
        origin: DiaryEnvironmentOrigin,
        tenant_key: str,
        max_age: timedelta,
        deadline: float,
    ) -> tuple[DiaryEnvironmentReading | None, bool]:
        """The latest persisted observation of one sensor — the second choice.

        The live half is already inside the budget (``get_live_state_for_sensors``
        got the deadline). The persisted half is checked here, because the
        time-series read is only *usually* local — a hung TimescaleDB would
        otherwise walk past a ceiling that is supposed to be absolute.
        """
        now = now_utc()
        if self._observation_repo is None or not sensor.key:
            return None, False
        if time.monotonic() >= deadline:
            return None, True
        try:
            stored = self._observation_repo.get_latest(sensor.key, tenant_key)
        except Exception as exc:  # noqa: BLE001 — never fails the write
            logger.warning("diary_environment_observation_read_failed", sensor_key=sensor.key, error=str(exc))
            return None, True
        if stored is None:
            return None, False
        measured_at = ensure_aware_utc(stored.time)
        if measured_at is None or now - measured_at > max_age:
            return None, False
        return (
            DiaryEnvironmentReading(
                metric_type=sensor.metric_type,
                value=stored.value,
                unit=stored.unit or sensor.unit_of_measurement,
                # The stored provenance verbatim (REQ-005 §2): a persisted
                # ``manual`` reading stays ``manual`` — promoting it to
                # ``ha_auto`` because it came out of the time series would be
                # exactly the provenance loss this feature exists to avoid.
                source=stored.source,
                measured_at=measured_at,
                sensor_key=sensor.key,
                origin=origin,
            ),
            False,
        )

    def _read_weather_level(
        self,
        plant: PlantInstance,
        *,
        tenant_key: str,
        max_age: timedelta,
        deadline: float,
        captured: list[DiaryEnvironmentReading],
    ) -> tuple[list[DiaryEnvironmentReading], bool]:
        """Current outdoor conditions, for the metrics no sensor answered.

        Only air temperature and humidity: a ``WeatherForecast`` record carries
        nothing else that is a *measurement of this plant's surroundings*, and
        precipitation or wind would be a different claim than "the conditions the
        plant was in".

        This is where the shared metric classification earns its keep — deciding
        "has a sensor already answered the temperature?" against an open
        ``metric_type`` vocabulary is the same question the frost warning and the
        winter-quarter check ask, and it is now answered in one place.
        """
        if self._weather_forecast_repo is None or not settings.weather_enabled or not plant.site_key:
            return [], False
        has_temperature = any(is_air_temperature(r.metric_type, accept_aliases=True) for r in captured)
        has_humidity = any(is_humidity(r.metric_type) for r in captured)
        if has_temperature and has_humidity:
            return [], False
        if time.monotonic() >= deadline:
            return [], True

        if self._site_repo is not None:
            site = self._site_repo.get_site_by_key(plant.site_key)
            # Fail closed, unconditionally: an empty ``tenant_key`` (light mode)
            # only ever matches a site whose ``tenant_key`` is likewise empty.
            if site is None or site.tenant_key != tenant_key:
                return [], False

        try:
            records = self._weather_forecast_repo.find_by_site(plant.site_key, tenant_key)
        except Exception as exc:  # noqa: BLE001 — never fails the write
            logger.warning("diary_environment_weather_read_failed", site_key=plant.site_key, error=str(exc))
            return [], True

        now = now_utc()
        current: list[tuple[datetime, WeatherForecast]] = []
        for record in records:
            if not record.is_current_conditions:
                continue
            fetched = ensure_aware_utc(record.fetched_at)
            if fetched is None or now - fetched > max_age:
                continue
            current.append((fetched, record))
        if not current:
            return [], False
        # Freshest wins; a site may carry a current-conditions record per source.
        measured_at, record = max(current, key=lambda pair: pair[0])

        readings: list[DiaryEnvironmentReading] = []
        if not has_temperature:
            # ``temp_max_c`` is what the Home-Assistant adapter writes the current
            # temperature into on a current-conditions record; ``temp_min_c`` is
            # the fallback for a source that only fills that one.
            temperature = record.temp_max_c if record.temp_max_c is not None else record.temp_min_c
            if temperature is not None:
                readings.append(
                    DiaryEnvironmentReading(
                        metric_type=WEATHER_TEMPERATURE_METRIC_TYPE,
                        value=temperature,
                        unit="°C",
                        # The adapter name verbatim (REQ-046). The REQ-005
                        # ``weather_api`` class is already said by ``origin``;
                        # collapsing "open-meteo" into it would throw away which
                        # service answered, and they do not agree with each other.
                        source=record.source,
                        measured_at=measured_at,
                        sensor_key=None,
                        origin=DiaryEnvironmentOrigin.WEATHER,
                    )
                )
        if not has_humidity and record.humidity_percent is not None:
            readings.append(
                DiaryEnvironmentReading(
                    metric_type=WEATHER_HUMIDITY_METRIC_TYPE,
                    value=record.humidity_percent,
                    unit="%",
                    source=record.source,
                    measured_at=measured_at,
                    sensor_key=None,
                    origin=DiaryEnvironmentOrigin.WEATHER,
                )
            )
        return readings, False


def _as_float(value: object) -> float | None:
    """Parse a live state value, tolerating HA's ``unavailable`` / ``unknown``."""
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:  # noqa: F841
        return None
