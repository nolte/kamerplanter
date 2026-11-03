"""REQ-053 WP 3.7 — the plant states of a bed (GP-API-054, GP-FR-192).

The repository is a recording double: what these tests prove is the service's own behaviour — ownership is resolved
before any read (a foreign and an absent bed answer the same 404 and **nothing** reaches the repository), the tenant
reaches the read, and the facts become the calculator's state. The AQL itself is proven against a real ArangoDB in
``tests/integration/test_plant_state_repository.py``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.common.enums import FrostRisk
from app.common.exceptions import NotFoundError
from app.domain.calculators.plant_state_calculator import OpenTask
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, NextTask, PlantStateSource
from app.domain.interfaces.weather_forecast_repository import IWeatherForecastRepository
from app.domain.models.site import Microclimate, SiteConditions
from app.domain.models.weather import WeatherForecast
from app.domain.services.plant_state_service import PlantStateService
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT, FakePlanRepo, FakeSites, make_location, make_site

NOW = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)


class RecordingRepo(IPlantStateRepository):
    def __init__(self, rows: list[PlantStateSource]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, str, int, int]] = []

    def list_bed_plants(
        self, location_key: str, *, tenant_key: str, now: datetime, offset: int, limit: int
    ) -> list[PlantStateSource]:
        self.calls.append((location_key, tenant_key, offset, limit))
        return self.rows

    def list_plants_in_beds(
        self, bed_keys: list[str], *, tenant_key: str, now: datetime, offset: int, limit: int
    ) -> list[PlantStateSource]:
        raise AssertionError("the plant-states API reads one bed, never the site-wide window")


def row(**overrides: object) -> PlantStateSource:
    fields: dict[str, object] = {
        "plant_key": "p1",
        "instance_id": "TOM-1",
        "species_key": "tomato",
        "planted_on": date(2026, 4, 1),
        "phase_key": "flower",
        "phase_started_on": date(2026, 5, 20),
        "phase_typical_days": 60,
    }
    fields.update(overrides)
    return PlantStateSource(**fields)  # type: ignore[arg-type]


@pytest.fixture
def world():
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed")
    plan.locations["alien"] = make_location("alien").model_copy(update={"site_key": "site_foreign"})
    repo = RecordingRepo([row()])
    return PlantStateService(sites, repo), repo


class TestOwnership:
    def test_the_tenant_and_the_window_reach_the_read(self, world) -> None:
        service, repo = world
        service.list_plant_states("bed", tenant_key=TENANT, offset=10, limit=25, now=NOW)
        assert repo.calls == [("bed", TENANT, 10, 25)]

    @pytest.mark.parametrize("key", ["alien", "missing"])
    def test_a_foreign_and_an_absent_bed_answer_alike_and_read_nothing(self, world, key: str) -> None:
        service, repo = world
        with pytest.raises(NotFoundError) as caught:
            service.list_plant_states(key, tenant_key=TENANT, now=NOW)
        assert "site_foreign" not in str(caught.value)
        assert repo.calls == []


class TestState:
    def test_acc_050_through_the_service(self, world) -> None:
        service, repo = world
        repo.rows = [
            row(
                open_tasks=(OpenTask("watering", date(2026, 6, 7)), OpenTask("pruning", date(2026, 6, 9))),
                open_finding_count=1,
                finding_label="Aphids",
                next_task=NextTask("Water", "watering", date(2026, 6, 7)),
            )
        ]
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert entry.state.lifecycle == "active"
        assert [item.reason for item in entry.state.attention] == ["problem", "overdue"]
        assert entry.state.phase_progress is not None
        assert entry.state.phase_progress.elapsed_d == 21

    def test_a_plant_without_a_phase_start_counts_from_the_planting_day(self, world) -> None:
        service, repo = world
        repo.rows = [row(phase_started_on=None)]
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert entry.state.phase_progress is not None
        assert entry.state.phase_progress.elapsed_d == 70

    def test_a_plant_without_a_phase_has_none(self, world) -> None:
        service, repo = world
        repo.rows = [row(phase_key=None, phase_started_on=None)]
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert entry.state.phase_key is None
        assert entry.state.phase_progress is None
        assert entry.state.harvest_ready is False

    def test_a_partial_harvest_batch_makes_the_plant_harvesting(self, world) -> None:
        service, repo = world
        repo.rows = [row(harvest_batch_count=1, phase_allows_harvest=True)]
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert entry.state.lifecycle == "harvesting"
        assert entry.state.harvest_ready is True

    def test_the_frost_reason_is_absent_without_a_forecast_source(self, world) -> None:
        service, _ = world
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert all(item.reason != "frost" for item in entry.state.attention)
        assert entry.frost_risk is False


class FakeForecasts(IWeatherForecastRepository):
    def __init__(self, forecasts: list[WeatherForecast]) -> None:
        self.forecasts = forecasts
        self.calls: list[tuple[str, str]] = []

    def upsert_daily(self, forecast: WeatherForecast) -> WeatherForecast:
        raise AssertionError("read only")

    def find_by_site(self, site_key: str, tenant_key: str) -> list[WeatherForecast]:
        self.calls.append((site_key, tenant_key))
        return self.forecasts


def _frost_night(temp_min: float | None = -2.0, *, days_ahead: int = 0) -> WeatherForecast:
    return WeatherForecast(
        site_key="site1",
        tenant_key=TENANT,
        forecast_date=NOW.date() + timedelta(days=days_ahead),
        temp_min_c=temp_min,
        source="open-meteo",
        fetched_at=NOW,
        data_kind="forecast",
    )


def _frost_world(risk: FrostRisk | None, forecasts: list[WeatherForecast] | None):
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location(
        "bed", site_conditions=SiteConditions(microclimate=Microclimate(frost_risk=risk)) if risk else None
    )
    source = None if forecasts is None else FakeForecasts(forecasts)
    return PlantStateService(sites, RecordingRepo([row()]), source), source


class TestFrostReason:
    """WP 8.20 / GP-FR-162: a ``high`` bed with a frost predicted for its site carries the frost reason."""

    def test_a_high_bed_with_a_predicted_frost_carries_the_reason(self) -> None:
        service, source = _frost_world(FrostRisk.HIGH, [_frost_night()])
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert entry.frost_risk is True
        assert any(item.reason == "frost" for item in entry.state.attention)
        assert source is not None and source.calls == [(make_location("bed").site_key, TENANT)]

    @pytest.mark.parametrize(
        "forecasts", [[], [_frost_night(5.0)], [_frost_night(None)], [_frost_night(-3.0, days_ahead=9)]]
    )
    def test_without_a_predicted_frost_there_is_no_reason(self, forecasts) -> None:
        service, _ = _frost_world(FrostRisk.HIGH, forecasts)
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert entry.frost_risk is False
        assert all(item.reason != "frost" for item in entry.state.attention)

    @pytest.mark.parametrize("risk", [FrostRisk.LOW, FrostRisk.NORMAL, FrostRisk.UNKNOWN, None])
    def test_a_bed_that_is_not_high_never_carries_the_reason_even_with_a_frost(self, risk) -> None:
        service, _ = _frost_world(risk, [_frost_night()])
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert entry.frost_risk is False
        assert all(item.reason != "frost" for item in entry.state.attention)

    def test_an_unreadable_forecast_drops_the_reason_not_the_state(self) -> None:
        service, source = _frost_world(FrostRisk.HIGH, [_frost_night()])

        def down(*_a, **_k):
            raise RuntimeError("store down")

        source.find_by_site = down  # type: ignore[union-attr,method-assign]
        [entry] = service.list_plant_states("bed", tenant_key=TENANT, now=NOW)
        assert entry.frost_risk is False

    def test_an_empty_window_reads_no_forecast(self) -> None:
        service, source = _frost_world(FrostRisk.HIGH, [_frost_night()])
        service._repo.rows = []  # type: ignore[attr-defined]
        assert service.list_plant_states("bed", tenant_key=TENANT, now=NOW) == []
        assert source is not None and source.calls == []
