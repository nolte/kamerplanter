"""Unit tests for the frost-warning engine (REQ-005/018/039, Issue #392)."""

from datetime import date, datetime, timedelta

from app.domain.engines.frost_warning_engine import (
    AIR_TEMPERATURE_METRIC_TYPES,
    DEFAULT_FROST_FORECAST_HORIZON_DAYS,
    DEFAULT_FROST_FORECAST_THRESHOLD_CELSIUS,
    DEFAULT_FROST_WARNING_THRESHOLD_CELSIUS,
    evaluate_forecast_frost_warning,
    evaluate_frost_warning,
    pick_air_temperature,
)
from app.domain.models.weather import WeatherForecast

TODAY = date(2026, 7, 5)
_FETCHED_AT = datetime(2026, 7, 5, 6, 0, 0)


def _forecast(day_offset: int, temp_min_c: float | None, source: str = "open-meteo") -> WeatherForecast:
    return WeatherForecast(
        site_key="site-1",
        forecast_date=TODAY + timedelta(days=day_offset),
        temp_min_c=temp_min_c,
        temp_max_c=None if temp_min_c is None else temp_min_c + 8.0,
        source=source,
        fetched_at=_FETCHED_AT,
    )


class TestEvaluateFrostWarning:
    def test_below_threshold_warns(self):
        assert evaluate_frost_warning(-2.0) is True

    def test_at_threshold_warns(self):
        assert evaluate_frost_warning(DEFAULT_FROST_WARNING_THRESHOLD_CELSIUS) is True

    def test_above_threshold_no_warning(self):
        assert evaluate_frost_warning(5.0) is False

    def test_none_temperature_is_unknown_not_false(self):
        # Honest unknown — never fabricate "no frost" from a missing reading.
        assert evaluate_frost_warning(None) is None

    def test_custom_threshold(self):
        assert evaluate_frost_warning(1.0, threshold_celsius=0.0) is False
        assert evaluate_frost_warning(0.0, threshold_celsius=0.0) is True

    def test_default_threshold_is_three_celsius(self):
        assert DEFAULT_FROST_WARNING_THRESHOLD_CELSIUS == 3.0


class TestEvaluateForecastFrostWarning:
    THRESHOLD = 2.0
    HORIZON = 2

    def _run(self, forecasts, threshold=None, horizon=None):
        return evaluate_forecast_frost_warning(
            forecasts,
            self.THRESHOLD if threshold is None else threshold,
            self.HORIZON if horizon is None else horizon,
            TODAY,
        )

    def test_predicted_true_in_horizon_below_threshold(self):
        result = self._run([_forecast(0, 8.0), _forecast(1, -1.0)])
        assert result["predicted"] is True
        assert result["min_temp"] == -1.0
        assert result["expected_date"] == TODAY + timedelta(days=1)
        assert result["source"] == "open-meteo"

    def test_predicted_true_at_threshold_is_inclusive(self):
        result = self._run([_forecast(0, self.THRESHOLD)])
        assert result["predicted"] is True
        assert result["expected_date"] == TODAY

    def test_predicted_false_when_all_above_threshold(self):
        result = self._run([_forecast(0, 6.0), _forecast(1, 4.5), _forecast(2, 3.0)])
        assert result["predicted"] is False
        assert result["min_temp"] is None
        assert result["expected_date"] is None
        assert result["source"] is None

    def test_predicted_none_on_empty_list(self):
        result = self._run([])
        assert result == {"predicted": None, "min_temp": None, "expected_date": None, "source": None}

    def test_predicted_none_when_all_temp_min_none(self):
        result = self._run([_forecast(0, None), _forecast(1, None)])
        assert result["predicted"] is None

    def test_mixed_none_and_values_evaluates_known_records(self):
        # A record with temp_min_c=None must not mask a real in-horizon frost.
        result = self._run([_forecast(0, None), _forecast(1, -2.0)])
        assert result["predicted"] is True
        assert result["expected_date"] == TODAY + timedelta(days=1)

    def test_earliest_frost_day_wins(self):
        result = self._run([_forecast(2, -5.0), _forecast(1, -1.0), _forecast(0, 1.0)])
        assert result["predicted"] is True
        # Earliest in-horizon frost day is today (1.0 <= 2.0), not the colder days.
        assert result["expected_date"] == TODAY
        assert result["min_temp"] == 1.0

    def test_tie_on_same_date_picks_lowest_temp(self):
        result = self._run(
            [
                _forecast(1, 0.5, source="dwd"),
                _forecast(1, -3.0, source="open-meteo"),
            ]
        )
        assert result["expected_date"] == TODAY + timedelta(days=1)
        assert result["min_temp"] == -3.0
        assert result["source"] == "open-meteo"

    def test_horizon_boundary_day_is_inclusive(self):
        # horizon_days counts calendar days from today, so the last in-window day
        # is offset HORIZON - 1 (offset 1 with HORIZON 2 = today + tomorrow).
        result = self._run([_forecast(self.HORIZON - 1, -1.0)])
        assert result["predicted"] is True
        assert result["expected_date"] == TODAY + timedelta(days=self.HORIZON - 1)

    def test_horizon_boundary_day_plus_one_is_excluded(self):
        # Day == horizon_days (offset 2 with HORIZON 2) is the first day beyond the
        # window → no usable in-horizon frost.
        result = self._run([_forecast(self.HORIZON, -10.0)])
        assert result["predicted"] is None

    def test_past_date_is_ignored(self):
        # forecast_date < today is stale and must not raise a warning.
        result = self._run([_forecast(-1, -10.0)])
        assert result["predicted"] is None

    def test_past_date_ignored_but_in_horizon_frost_still_wins(self):
        result = self._run([_forecast(-1, -10.0), _forecast(1, -2.0)])
        assert result["predicted"] is True
        assert result["expected_date"] == TODAY + timedelta(days=1)

    def test_horizon_one_scans_only_today(self):
        # horizon_days 1 → only today is scanned; tomorrow's frost is out of window.
        result = self._run([_forecast(1, -5.0)], horizon=1)
        assert result["predicted"] is None
        result_today = self._run([_forecast(0, -1.0)], horizon=1)
        assert result_today["predicted"] is True

    def test_zero_horizon_scans_no_day(self):
        # horizon_days 0 scans no calendar day at all — not even today.
        result = self._run([_forecast(0, -5.0)], horizon=0)
        assert result["predicted"] is None

    def test_defaults_exposed(self):
        assert DEFAULT_FROST_FORECAST_THRESHOLD_CELSIUS == 2.0
        assert DEFAULT_FROST_FORECAST_HORIZON_DAYS == 2

    def test_reanalysis_record_never_triggers_warning(self):
        # REQ-041 — a NASA POWER reanalysis record (data_kind="reanalysis") on an
        # in-horizon date with a hard frost must NOT raise a proactive warning; it
        # describes the past, not the future.
        reanalysis = WeatherForecast(
            site_key="site-1",
            forecast_date=TODAY,
            temp_min_c=-8.0,
            source="nasa-power",
            fetched_at=_FETCHED_AT,
            data_kind="reanalysis",
        )
        result = self._run([reanalysis])
        assert result["predicted"] is None

    def test_reanalysis_ignored_but_real_forecast_still_wins(self):
        reanalysis = WeatherForecast(
            site_key="site-1",
            forecast_date=TODAY,
            temp_min_c=-8.0,
            source="nasa-power",
            fetched_at=_FETCHED_AT,
            data_kind="reanalysis",
        )
        result = self._run([reanalysis, _forecast(1, -2.0)])
        assert result["predicted"] is True
        assert result["expected_date"] == TODAY + timedelta(days=1)
        assert result["source"] == "open-meteo"


def _reading(metric_type: str, value, entity_id: str, **extra) -> dict:
    """One entry of the sensor-keyed live-state ``readings`` map."""
    return {"metric_type": metric_type, "value": value, "entity_id": entity_id, **extra}


class TestPickAirTemperature:
    """The picker reads the sensor-keyed ``readings`` map (Issue #977).

    Metric priority is unchanged; what is new is that several sensors can report
    the same metric, and the frost warning answers that with the *coldest* of
    them rather than with whichever one the map happened to keep.
    """

    def test_prefers_canonical_temperature_celsius(self):
        readings = {
            "s-air": _reading("temperature_celsius", 2.5, "sensor.air"),
            "s-water": _reading("water_temp_celsius", 18.0, "sensor.water"),
        }
        temp, entity_id = pick_air_temperature(readings)
        assert temp == 2.5
        assert entity_id == "sensor.air"

    def test_falls_back_to_water_temp_celsius(self):
        readings = {"s-1": _reading("water_temp_celsius", 1.0, "sensor.temp")}
        temp, entity_id = pick_air_temperature(readings)
        assert temp == 1.0
        assert entity_id == "sensor.temp"

    def test_no_temperature_metric_returns_none(self):
        readings = {"s-hum": _reading("humidity_percent", 55.0, "sensor.hum")}
        temp, entity_id = pick_air_temperature(readings)
        assert temp is None
        assert entity_id is None

    def test_none_value_skipped(self):
        readings = {"s-air": _reading("temperature_celsius", None, "sensor.air")}
        temp, entity_id = pick_air_temperature(readings)
        assert temp is None
        assert entity_id is None

    def test_non_numeric_value_skipped_not_raised(self):
        # Home Assistant reports "unavailable"/"unknown" as the entity value; that
        # must not raise ValueError (→ 500 on the frost-warning endpoint).
        for bad in ("unavailable", "unknown", ""):
            readings = {"s-air": _reading("temperature_celsius", bad, "sensor.air")}
            temp, entity_id = pick_air_temperature(readings)
            assert temp is None
            assert entity_id is None

    def test_non_numeric_primary_falls_back_to_numeric_secondary(self):
        # A non-numeric canonical metric is skipped; the numeric fallback wins.
        readings = {
            "s-air": _reading("temperature_celsius", "unavailable", "sensor.air"),
            "s-water": _reading("water_temp_celsius", 1.5, "sensor.water"),
        }
        temp, entity_id = pick_air_temperature(readings)
        assert temp == 1.5
        assert entity_id == "sensor.water"

    def test_numeric_string_is_parsed(self):
        # A numeric HA state delivered as a string still parses.
        readings = {"s-air": _reading("temperature_celsius", "2.5", "sensor.air")}
        temp, entity_id = pick_air_temperature(readings)
        assert temp == 2.5
        assert entity_id == "sensor.air"

    def test_empty_values(self):
        temp, entity_id = pick_air_temperature({})
        assert temp is None
        assert entity_id is None

    def test_two_thermometers_the_coldest_warns(self):
        # Two thermometers at opposite ends of one tent: the warm end must not
        # silence the cold one. The freshest-wins rule of the derived view would
        # have reported 6.0 °C here — right for a gauge, wrong for a warning.
        readings = {
            "s-front": _reading("temperature_celsius", 6.0, "sensor.front", last_reported="2026-08-06T06:05:00Z"),
            "s-back": _reading("temperature_celsius", 1.2, "sensor.back", last_reported="2026-08-06T06:01:00Z"),
        }
        temp, entity_id = pick_air_temperature(readings)
        assert temp == 1.2
        assert entity_id == "sensor.back"

    def test_coldest_wins_independently_of_map_order(self):
        cold = _reading("temperature_celsius", -1.0, "sensor.cold")
        warm = _reading("temperature_celsius", 14.0, "sensor.warm")
        assert pick_air_temperature({"s-a": cold, "s-b": warm}) == (-1.0, "sensor.cold")
        assert pick_air_temperature({"s-b": warm, "s-a": cold}) == (-1.0, "sensor.cold")

    def test_equal_temperatures_break_the_tie_on_sensor_key(self):
        # Same reading twice: the reported entity must not depend on dict order.
        first = _reading("temperature_celsius", 2.0, "sensor.one")
        second = _reading("temperature_celsius", 2.0, "sensor.two")
        assert pick_air_temperature({"s-1": first, "s-2": second}) == (2.0, "sensor.one")
        assert pick_air_temperature({"s-2": second, "s-1": first}) == (2.0, "sensor.one")

    def test_a_colder_alias_never_outranks_a_canonical_metric(self):
        # Priority still decides *which metric* answers; coldest only decides
        # between the sensors of that metric. A cold water probe must not take
        # over from a warm air thermometer.
        readings = {
            "s-air": _reading("temperature_celsius", 12.0, "sensor.air"),
            "s-water": _reading("water_temp_celsius", -3.0, "sensor.water"),
        }
        temp, entity_id = pick_air_temperature(readings)
        assert temp == 12.0
        assert entity_id == "sensor.air"

    def test_metric_priority_order(self):
        assert AIR_TEMPERATURE_METRIC_TYPES[0] == "temperature_celsius"
