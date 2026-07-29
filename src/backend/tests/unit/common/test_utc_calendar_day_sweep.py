"""The converted call sites answer in UTC, proven under a non-UTC process TZ.

``tests/unit/common/test_clock_contract.py`` covers the *helper*
(:func:`app.common.datetimes.today_utc`). This module covers the **call sites**
that #858 converted, and it is the falsifiability evidence for that sweep: every
test here runs inside :func:`tests.support.timezones.local_timezone` on a zone
that sits on the far side of midnight from UTC, so a call site that resolves its
calendar day from ``date.today()`` produces a date one day off and the assertion
fails. On a UTC container — which is what CI is — the two clocks agree and the
same assertions pass for the wrong reason, which is precisely why the defect
survived three sweeps (#772, #812, #858).

Two properties make these tests real rather than decorative:

* **freezegun cannot substitute for the harness.** Its ``tz_offset`` shifts
  ``date.today()`` and ``datetime.now(UTC)`` by the same amount, so the gap the
  bug lives in closes. The harness sets ``TZ`` + ``time.tzset()`` for real.
* **They are direction-agnostic.** :func:`timezone_on_another_calendar_day`
  returns whichever of UTC+14 / UTC-12 currently crosses the date line, so the
  local date may be *ahead* or *behind* UTC depending on the hour of the run.
  Every assertion below therefore compares against ``today_utc()`` itself rather
  than against a threshold that only one direction would cross — except
  :class:`TestWaterMeasurementAge`, which deliberately pins **both** sides of the
  365-day boundary so one of its two cases fails whichever way the local day
  points.

Assert against ``today_utc()``, never against ``date.today()``: a test written
the second way passes on a UTC CI runner no matter which clock the production
code reads, and four such tests had already accumulated in this repository
before #858 removed them.

Traces to issue #858 (no TC-ID: a clock-contract regression guard is not a
user-facing test case).
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.datetimes import today_utc
from app.data_access.external.dwd_weather_adapter import DwdWeatherAdapter
from app.data_access.external.home_assistant_weather_adapter import HomeAssistantWeatherAdapter
from app.domain.engines.water_mix_engine import WaterSourceValidator
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import TapWaterProfile
from app.domain.models.weather import HaSensorMapping, WeatherSourceHaConfig
from app.domain.services.plant_instance_service import PlantInstanceService
from tests.conftest import wire_get_or_raise
from tests.support.timezones import local_timezone, timezone_on_another_calendar_day


class TestRemovedOnIsAUtcDay:
    """``plant_instance_service`` stamps ``removed_on`` (#858)."""

    @staticmethod
    def _service() -> tuple[PlantInstanceService, PlantInstance]:
        plant = PlantInstance(
            _key="plant-1",
            tenant_key="tenant_anna",
            instance_id="P-1",
            species_key="species1",
            planted_on=date(2026, 6, 1),
        )
        plant_repo = MagicMock()
        plant_repo.get_by_key.return_value = plant
        wire_get_or_raise(plant_repo, "PlantInstance")
        plant_repo.update.side_effect = lambda _key, p: p
        service = PlantInstanceService(plant_repo, MagicMock(), MagicMock(), MagicMock())
        return service, plant

    def test_remove_plant_stamps_the_utc_day(self) -> None:
        """``removed_on`` is read back against UTC-stamped rows, so it is UTC.

        Fails on the pre-#858 code: ``date.today()`` returns the local day, which
        under this TZ is not ``today_utc()``.
        """
        service, _ = self._service()

        with local_timezone(timezone_on_another_calendar_day()):
            updated = service.remove_plant("plant-1")

            assert updated.removed_on == today_utc()


class TestWaterMeasurementAge:
    """``water_mix_engine.validate_measurement_age`` — the ``today=None`` fallback.

    That fallback is **not** dead code: ``nutrient_calculations/router.py`` calls
    ``validate_all(tap, ro)`` without a reference date, so a production request
    reaches it.

    Both sides of the 365-day boundary are pinned, which is what makes the case
    direction-agnostic: a local day *ahead* of UTC ages the ``-365`` profile into
    a warning, a local day *behind* UTC rejuvenates the ``-366`` profile out of
    one. Whichever way the harness's zone points, one of the two assertions
    catches a local-clock reading.
    """

    @staticmethod
    def _profile(age_days: int) -> TapWaterProfile:
        return TapWaterProfile(ec_ms=0.4, ph=7.2, measurement_date=today_utc() - timedelta(days=age_days))

    def test_the_age_boundary_is_measured_from_the_utc_day(self) -> None:
        validator = WaterSourceValidator()

        with local_timezone(timezone_on_another_calendar_day()):
            exactly_a_year = validator.validate_measurement_age(self._profile(365))
            a_day_over = validator.validate_measurement_age(self._profile(366))

        assert exactly_a_year == [], "365 days is not yet 'older than 12 months'"
        assert [w.code for w in a_day_over] == ["measurement_age"]


class TestObservedWeatherDay:
    """``home_assistant_weather_adapter`` stamps ``forecast_date`` (#858).

    The record is the clearest mixed-clock case in the sweep: it carried a UTC
    ``fetched_at`` next to a local-date ``forecast_date``, and its consumers
    (``sensor_service``, ``frost_warning_engine``) filter it with
    ``today <= forecast_date <= horizon_end`` where ``today`` is
    ``datetime.now(UTC).date()``. A record stamped a day ahead of that window
    was simply invisible to the frost warning.
    """

    @pytest.mark.asyncio
    async def test_sensor_mapping_record_carries_the_utc_day(self) -> None:
        ha = MagicMock()
        ha.get_state.side_effect = lambda eid: {"sensor.temp_min": {"value": 11.0}}.get(eid)
        adapter = HomeAssistantWeatherAdapter(ha)
        config = WeatherSourceHaConfig(
            mode="sensor_mapping",
            sensor_mapping=HaSensorMapping(temp_min_entity="sensor.temp_min"),
        )

        with local_timezone(timezone_on_another_calendar_day()):
            records = await adapter.fetch_daily(latitude=0.0, longitude=0.0, config=config)

            assert len(records) == 1
            assert records[0].forecast_date == today_utc()
            # The mixed clock the conversion removed: both halves of one record.
            assert records[0].fetched_at.date() == records[0].forecast_date


class TestForecastWindowStart:
    """``dwd_weather_adapter`` picks the Brightsky window start (#858).

    A start *later* than the consumer's UTC "today" drops today's forecast from
    the frost horizon entirely; a start earlier merely fetches a day that is then
    filtered out. The local server date can do either, depending on the host.
    """

    @pytest.mark.asyncio
    async def test_window_starts_on_the_utc_day(self) -> None:
        adapter = DwdWeatherAdapter(base_url="https://brightsky.test")
        response = MagicMock()
        response.json.return_value = {"weather": []}
        response.raise_for_status = MagicMock()

        with local_timezone(timezone_on_another_calendar_day()):
            with patch("app.data_access.external.dwd_weather_adapter.httpx.AsyncClient") as mock_cls:
                client = AsyncMock()
                client.get.return_value = response
                client.__aenter__ = AsyncMock(return_value=client)
                client.__aexit__ = AsyncMock(return_value=False)
                mock_cls.return_value = client

                await adapter.fetch_daily(latitude=52.5, longitude=13.4)

            params = client.get.call_args.kwargs["params"]
            assert params["date"] == today_utc().isoformat()
            # The window still spans the configured number of days.
            assert params["last_date"] > params["date"]
