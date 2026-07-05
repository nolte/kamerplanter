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
        # Day == horizon_days (offset 2 with HORIZON 2) is inside the window.
        result = self._run([_forecast(self.HORIZON, -1.0)])
        assert result["predicted"] is True
        assert result["expected_date"] == TODAY + timedelta(days=self.HORIZON)

    def test_horizon_boundary_day_plus_one_is_excluded(self):
        # Day == horizon_days + 1 is beyond the window → no usable in-horizon frost.
        result = self._run([_forecast(self.HORIZON + 1, -10.0)])
        assert result["predicted"] is None

    def test_past_date_is_ignored(self):
        # forecast_date < today is stale and must not raise a warning.
        result = self._run([_forecast(-1, -10.0)])
        assert result["predicted"] is None

    def test_past_date_ignored_but_in_horizon_frost_still_wins(self):
        result = self._run([_forecast(-1, -10.0), _forecast(1, -2.0)])
        assert result["predicted"] is True
        assert result["expected_date"] == TODAY + timedelta(days=1)

    def test_zero_horizon_only_today(self):
        # HORIZON 0 → only today is scanned; tomorrow's frost is out of window.
        result = self._run([_forecast(1, -5.0)], horizon=0)
        assert result["predicted"] is None
        result_today = self._run([_forecast(0, -1.0)], horizon=0)
        assert result_today["predicted"] is True

    def test_defaults_exposed(self):
        assert DEFAULT_FROST_FORECAST_THRESHOLD_CELSIUS == 2.0
        assert DEFAULT_FROST_FORECAST_HORIZON_DAYS == 2


class TestPickAirTemperature:
    def test_prefers_canonical_temperature_celsius(self):
        values = {
            "temperature_celsius": {"value": 2.5, "entity_id": "sensor.air"},
            "water_temp_celsius": {"value": 18.0, "entity_id": "sensor.water"},
        }
        temp, entity_id = pick_air_temperature(values)
        assert temp == 2.5
        assert entity_id == "sensor.air"

    def test_falls_back_to_water_temp_celsius(self):
        values = {"water_temp_celsius": {"value": 1.0, "entity_id": "sensor.temp"}}
        temp, entity_id = pick_air_temperature(values)
        assert temp == 1.0
        assert entity_id == "sensor.temp"

    def test_no_temperature_metric_returns_none(self):
        values = {"humidity_percent": {"value": 55.0, "entity_id": "sensor.hum"}}
        temp, entity_id = pick_air_temperature(values)
        assert temp is None
        assert entity_id is None

    def test_none_value_skipped(self):
        values = {"temperature_celsius": {"value": None, "entity_id": "sensor.air"}}
        temp, entity_id = pick_air_temperature(values)
        assert temp is None
        assert entity_id is None

    def test_non_numeric_value_skipped_not_raised(self):
        # Home Assistant reports "unavailable"/"unknown" as the entity value; that
        # must not raise ValueError (→ 500 on the frost-warning endpoint).
        for bad in ("unavailable", "unknown", ""):
            values = {"temperature_celsius": {"value": bad, "entity_id": "sensor.air"}}
            temp, entity_id = pick_air_temperature(values)
            assert temp is None
            assert entity_id is None

    def test_non_numeric_primary_falls_back_to_numeric_secondary(self):
        # A non-numeric canonical metric is skipped; the numeric fallback wins.
        values = {
            "temperature_celsius": {"value": "unavailable", "entity_id": "sensor.air"},
            "water_temp_celsius": {"value": 1.5, "entity_id": "sensor.water"},
        }
        temp, entity_id = pick_air_temperature(values)
        assert temp == 1.5
        assert entity_id == "sensor.water"

    def test_numeric_string_is_parsed(self):
        # A numeric HA state delivered as a string still parses.
        values = {"temperature_celsius": {"value": "2.5", "entity_id": "sensor.air"}}
        temp, entity_id = pick_air_temperature(values)
        assert temp == 2.5
        assert entity_id == "sensor.air"

    def test_empty_values(self):
        temp, entity_id = pick_air_temperature({})
        assert temp is None
        assert entity_id is None

    def test_metric_priority_order(self):
        assert AIR_TEMPERATURE_METRIC_TYPES[0] == "temperature_celsius"
