"""#2165 — the Art. 15 bundle of the personal garden carries its readings and its tank, watering and feeding logs.

Measured before this change (origin/develop b709f0b6d): ``DataExportEngine.USER_DATA_MANIFEST``
had no source for ``sensors``, ``tanks``, ``tank_states``, ``tank_fill_events``,
``maintenance_logs``, ``watering_events``, ``watering_logs`` or ``feeding_events``, and none
for the TimescaleDB tables ``sensor_readings`` / ``sensor_hourly`` / ``sensor_daily`` — the
walk only reached ArangoDB. The tenant-erasure inventory deletes all of them with the
personal tenant, so the garden was erased more completely than it was disclosed.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.models.privacy import (
    DataSourceDefinition,
    PersonalTenantHop,
    PersonalTenantScope,
    TimeSeriesScope,
    TimeSeriesSlice,
)

TIME_SERIES = ("sensor_readings", "sensor_hourly", "sensor_daily")
LOGS = (
    "tanks",
    "tank_states",
    "tank_fill_events",
    "maintenance_logs",
    "watering_events",
    "watering_logs",
    "feeding_events",
)


def _by_collection() -> dict[str, DataSourceDefinition]:
    return {
        s.collection: s for s in DataExportEngine().build_export_manifest("u1") if s.personal_tenant_scope is not None
    }


def test_every_log_and_the_sensors_are_personal_garden_sources() -> None:
    found = _by_collection()

    assert set(LOGS) | {"sensors"} <= set(found)
    assert all(found[name].time_series is None for name in (*LOGS, "sensors"))


def test_a_sensor_is_reached_through_whichever_parent_it_hangs_off() -> None:
    """A sensor carries no ``tenant_key``; it hangs off one tank, site or location (the tenant-erasure anchors)."""
    sensors = _by_collection()["sensors"]

    chains = {tuple((hop.field, hop.collection) for hop in chain) for chain in sensors.personal_tenant_scope.chains}  # type: ignore[union-attr]

    assert chains == {
        (("tank_key", "tanks"),),
        (("site_key", "sites"),),
        (("location_key", "locations"), ("site_key", "sites")),
    }


def test_the_three_reading_tiers_are_time_series_of_the_garden() -> None:
    found = _by_collection()

    for name in TIME_SERIES:
        source = found[name]
        assert source.time_series is not None, name
        assert source.time_series.series_source == "sensors", name
        assert "sensor_key" in source.fields, name
        # the subject's own personal tenant key adds nothing to the copy
        assert "tenant_key" not in source.fields, name
        assert source.attribution_gap, f"{name}: the pre-#2076 readings must be stated"
    assert found["sensor_readings"].time_series.time_column == "time"  # type: ignore[union-attr]
    assert found["sensor_hourly"].time_series.time_column == "bucket"  # type: ignore[union-attr]


def test_the_sensors_are_walked_before_their_readings() -> None:
    """The walk takes the garden's sensor keys from the sensors section, so it must come first."""
    order = [s.collection for s in DataExportEngine().build_export_manifest("u1")]

    assert all(order.index("sensors") < order.index(name) for name in TIME_SERIES)


def test_a_time_series_must_be_anchored_on_its_own_tenant_key() -> None:
    with pytest.raises(ValidationError, match="anchored on its own tenant_key"):
        DataSourceDefinition(
            collection="sensor_readings",
            label="X",
            fields=["time"],
            personal_tenant_scope=PersonalTenantScope(via=(PersonalTenantHop(field="tank_key", collection="tanks"),)),
            time_series=TimeSeriesScope(time_column="time"),
        )
    with pytest.raises(ValidationError, match="anchored on its own tenant_key"):
        DataSourceDefinition(
            collection="sensor_readings",
            label="X",
            fields=["time"],
            filter_field="user_key",
            time_series=TimeSeriesScope(time_column="time"),
        )


def test_a_time_series_must_export_its_time_column() -> None:
    with pytest.raises(ValidationError, match="time column"):
        DataSourceDefinition(
            collection="sensor_readings",
            label="X",
            fields=["value"],
            personal_tenant_scope=PersonalTenantScope(),
            time_series=TimeSeriesScope(time_column="time"),
        )


def test_a_chain_longer_than_two_parents_is_refused_in_any_alternative() -> None:
    hop = PersonalTenantHop(field="x_key", collection="xs")
    with pytest.raises(ValidationError, match="more than two parents"):
        DataSourceDefinition(
            collection="sensors",
            label="X",
            fields=["_key"],
            personal_tenant_scope=PersonalTenantScope(or_via=((hop, hop, hop),)),
        )


def test_a_slice_cannot_carry_more_rows_than_its_total() -> None:
    with pytest.raises(ValidationError):
        TimeSeriesSlice(records=[{"time": 1}, {"time": 2}], total=1)


class TestTheBundleStatesWhatABoundedSectionLeavesOut:
    @staticmethod
    def _bundle(omitted: dict[str, int], records: int = 2) -> dict:
        readings = _by_collection()["sensor_readings"]
        sites = _by_collection()["sites"]
        return DataExportEngine().build_bundle(
            "u1",
            datetime(2026, 10, 10, tzinfo=UTC),
            [(sites, [{"name": "Balkon"}]), (readings, [{"time": "t", "value": 1.0}] * records)],
            controller_name="c",
            controller_email="c@example.invalid",
            omitted=omitted,
        )

    def test_a_bounded_section_says_how_many_it_leaves_out(self) -> None:
        bundle = self._bundle({"sensor_readings": 7})

        sites, readings = bundle["sections"]
        assert readings["record_count"] == 2
        assert readings["records_omitted"] == 7
        assert "9 records" in readings["omission_note"]
        assert "the 2 newest" in readings["omission_note"]
        assert sites["records_omitted"] == 0
        assert sites["omission_note"] is None
        assert bundle["format_version"] == "1.2"

    def test_a_complete_section_carries_no_note(self) -> None:
        (_sites, readings) = self._bundle({"sensor_readings": 0})["sections"]

        assert readings["records_omitted"] == 0
        assert readings["omission_note"] is None

    def test_only_a_time_series_section_can_leave_rows_out(self) -> None:
        with pytest.raises(ValueError, match="only a time-series section"):
            self._bundle({"sites": 3})

    def test_a_negative_count_is_refused(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            self._bundle({"sensor_readings": -1})
