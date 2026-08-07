"""The live-state keying rules and the derived single-value view (Issue #977).

Two properties carry these tests:

* the **full** map never loses a reading — that is the whole point of keying it
  on the sensor;
* the **derived** view loses readings on purpose, by a rule that is deliberate,
  deterministic and *reported* — a consumer must always be able to tell that more
  than one reading existed.
"""

from datetime import UTC, datetime

from app.domain.engines.live_state import (
    derive_single_value_view,
    reading_measured_at,
    sort_readings,
)

NOW = datetime(2026, 8, 6, 6, 0, 0, tzinfo=UTC)


def _reading(sensor_key: str, metric_type: str, value: float, **stamps) -> dict:
    return {
        "sensor_key": sensor_key,
        "sensor_name": f"Sensor {sensor_key}",
        "metric_type": metric_type,
        "value": value,
        "entity_id": f"sensor.{sensor_key}",
        "unit": "°C",
        **stamps,
    }


class TestReadingMeasuredAt:
    def test_last_reported_wins_over_the_other_two(self):
        reading = _reading(
            "s-1",
            "temperature_celsius",
            21.0,
            last_reported="2026-08-06T06:00:00Z",
            last_updated="2026-08-06T03:00:00Z",
            last_changed="2026-08-05T22:00:00Z",
        )
        assert reading_measured_at(reading) == NOW

    def test_falls_through_to_last_updated_then_last_changed(self):
        assert (
            reading_measured_at(
                _reading("s-1", "t", 1.0, last_updated="2026-08-06T06:00:00Z", last_changed="2026-08-05T22:00:00Z")
            )
            == NOW
        )
        assert reading_measured_at(_reading("s-1", "t", 1.0, last_changed="2026-08-06T06:00:00Z")) == NOW

    def test_no_timestamp_at_all_is_none(self):
        assert reading_measured_at(_reading("s-1", "t", 1.0)) is None

    def test_unparsable_timestamp_is_treated_as_absent_not_raised(self):
        # Home Assistant is an external system. One malformed stamp must not take
        # a whole live query — and with it a location's entire live state — down.
        reading = _reading("s-1", "t", 1.0, last_reported="not-a-timestamp", last_updated="2026-08-06T06:00:00Z")
        assert reading_measured_at(reading) == NOW

    def test_naive_timestamp_is_read_as_utc(self):
        assert reading_measured_at(_reading("s-1", "t", 1.0, last_reported="2026-08-06T06:00:00")) == NOW


class TestSortReadings:
    def test_freshest_first(self):
        old = _reading("s-old", "temperature_celsius", 20.0, last_reported="2026-08-06T05:00:00Z")
        new = _reading("s-new", "temperature_celsius", 23.0, last_reported="2026-08-06T05:59:00Z")
        assert [r["sensor_key"] for r in sort_readings([old, new])] == ["s-new", "s-old"]
        assert [r["sensor_key"] for r in sort_readings([new, old])] == ["s-new", "s-old"]

    def test_untimestamped_readings_rank_last(self):
        # Unfalsifiable freshness must not beat a dated reading, however old.
        dated = _reading("s-dated", "t", 1.0, last_changed="2020-01-01T00:00:00Z")
        undated = _reading("s-undated", "t", 2.0)
        assert [r["sensor_key"] for r in sort_readings([undated, dated])] == ["s-dated", "s-undated"]

    def test_ties_break_on_sensor_key_never_on_input_order(self):
        stamp = "2026-08-06T06:00:00Z"
        a = _reading("s-a", "t", 1.0, last_reported=stamp)
        b = _reading("s-b", "t", 2.0, last_reported=stamp)
        assert [r["sensor_key"] for r in sort_readings([b, a])] == ["s-a", "s-b"]
        assert [r["sensor_key"] for r in sort_readings([a, b])] == ["s-a", "s-b"]

    def test_untimestamped_ties_also_break_on_sensor_key(self):
        a = _reading("s-a", "t", 1.0)
        b = _reading("s-b", "t", 2.0)
        assert [r["sensor_key"] for r in sort_readings([b, a])] == ["s-a", "s-b"]

    def test_returns_copies_so_the_source_map_is_not_mutated(self):
        source = _reading("s-a", "t", 1.0)
        sorted_first = sort_readings([source])[0]
        sorted_first["value"] = 99.0
        assert source["value"] == 1.0


class TestDeriveSingleValueView:
    def test_single_sensor_per_metric_behaves_exactly_as_before(self):
        readings = {
            "s-temp": _reading("s-temp", "temperature_celsius", 21.4, last_reported="2026-08-06T06:00:00Z"),
            "s-hum": _reading("s-hum", "humidity_percent", 55.0, last_reported="2026-08-06T06:00:00Z"),
        }
        view = derive_single_value_view(readings)
        assert set(view) == {"temperature_celsius", "humidity_percent"}
        assert view["temperature_celsius"]["value"] == 21.4
        assert view["temperature_celsius"]["entity_id"] == "sensor.s-temp"
        # And it says, in-band, that nothing was left out.
        assert view["temperature_celsius"]["sensor_count"] == 1
        assert view["temperature_celsius"]["superseded_sensor_keys"] == []

    def test_two_sensors_of_one_metric_the_freshest_is_shown(self):
        readings = {
            "s-front": _reading("s-front", "temperature_celsius", 21.4, last_reported="2026-08-06T05:50:00Z"),
            "s-back": _reading("s-back", "temperature_celsius", 23.9, last_reported="2026-08-06T05:59:00Z"),
        }
        view = derive_single_value_view(readings)
        assert view["temperature_celsius"]["value"] == 23.9
        assert view["temperature_celsius"]["sensor_key"] == "s-back"

    def test_the_collapse_is_reported_not_silent(self):
        # The point of the derived view: it may show one number, but it may never
        # pretend that one number was all there was.
        readings = {
            "s-front": _reading("s-front", "temperature_celsius", 21.4, last_reported="2026-08-06T05:50:00Z"),
            "s-mid": _reading("s-mid", "temperature_celsius", 22.0, last_reported="2026-08-06T05:55:00Z"),
            "s-back": _reading("s-back", "temperature_celsius", 23.9, last_reported="2026-08-06T05:59:00Z"),
        }
        entry = derive_single_value_view(readings)["temperature_celsius"]
        assert entry["sensor_count"] == 3
        assert entry["superseded_sensor_keys"] == ["s-mid", "s-front"]
        # Every superseded key resolves in the full map — the view points at the
        # readings it does not show rather than merely counting them.
        assert all(key in readings for key in entry["superseded_sensor_keys"])

    def test_view_is_deterministic_for_any_input_order(self):
        a = _reading("s-a", "temperature_celsius", 1.0)
        b = _reading("s-b", "temperature_celsius", 2.0)
        assert derive_single_value_view({"s-a": a, "s-b": b}) == derive_single_value_view({"s-b": b, "s-a": a})

    def test_a_reading_without_a_metric_type_is_skipped_not_invented(self):
        readings = {"s-1": {"sensor_key": "s-1", "value": 1.0}}
        assert derive_single_value_view(readings) == {}

    def test_deriving_does_not_mutate_the_full_map(self):
        readings = {"s-1": _reading("s-1", "temperature_celsius", 21.0)}
        derive_single_value_view(readings)
        assert "sensor_count" not in readings["s-1"]
        assert "superseded_sensor_keys" not in readings["s-1"]

    def test_empty_map_derives_an_empty_view(self):
        assert derive_single_value_view({}) == {}
