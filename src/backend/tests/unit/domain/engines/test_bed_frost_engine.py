"""WP 8.20 — the bed-level frost rules and the one expression both consumers share (REQ-053 GP-FR-162)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.common.enums import FrostRisk
from app.domain.engines import bed_frost_engine
from app.domain.models.site import Location, Microclimate, SiteConditions
from app.domain.models.weather import WeatherForecast
from app.domain.services import frost_forecast
from app.domain.services.frost_forecast import site_frost_verdict
from app.domain.services.plant_state_inputs import frost_risk_of

TODAY = date(2026, 6, 10)


def bed(risk: FrostRisk | None, key: str = "b", name: str = "Bed") -> Location:
    conditions = None if risk is None else SiteConditions(microclimate=Microclimate(frost_risk=risk))
    return Location(_key=key, name=name, site_key="s", area_m2=1.0, site_conditions=conditions)


def night(temp: float | None, days_ahead: int = 0) -> WeatherForecast:
    return WeatherForecast(
        site_key="s",
        tenant_key="t",
        forecast_date=TODAY + timedelta(days=days_ahead),
        temp_min_c=temp,
        source="open-meteo",
        fetched_at=datetime(2026, 6, 10, tzinfo=UTC),
        data_kind="forecast",
    )


@pytest.mark.parametrize(
    ("risk", "flagged"),
    [
        (FrostRisk.HIGH, True),
        (FrostRisk.LOW, False),
        (FrostRisk.NORMAL, False),
        (FrostRisk.UNKNOWN, False),
        (None, False),
    ],
)
def test_only_a_high_bed_is_flagged(risk, flagged) -> None:
    assert bed_frost_engine.bed_frost_flagged(bed(risk)) is flagged


def test_named_beds_are_the_high_ones_ordered_by_name() -> None:
    beds = [bed(FrostRisk.HIGH, "b2", "beta"), bed(FrostRisk.LOW, "b1", "alpha"), bed(FrostRisk.HIGH, "b3", "Alpha")]
    assert [b.key for b in bed_frost_engine.named_frost_beds(beds)] == ["b3", "b2"]


FORECASTS = [
    [],
    [night(-2.0)],
    [night(5.0)],
    [night(None)],
    [night(-2.0, days_ahead=1)],
    [night(-2.0, days_ahead=5)],
    [night(-2.0, days_ahead=-1)],
    [night(4.0), night(-1.0, days_ahead=1)],
]


@pytest.mark.parametrize("forecasts", FORECASTS)
@pytest.mark.parametrize("risk", list(FrostRisk) + [None])
def test_the_frost_reason_is_the_warning_verdict_on_a_high_bed(risk, forecasts) -> None:
    """The reason of the plant state and the warning's trigger are one expression: reason == high AND predicted."""
    verdict = site_frost_verdict(forecasts, TODAY)
    expected = risk is FrostRisk.HIGH and verdict["predicted"] is True
    assert frost_risk_of(bed(risk), verdict) is expected


def test_the_verdict_runs_through_the_engine_function(monkeypatch) -> None:
    calls: list[int] = []
    real = frost_forecast.evaluate_forecast_frost_warning

    def spy(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(frost_forecast, "evaluate_forecast_frost_warning", spy)
    site_frost_verdict([night(-2.0)], TODAY)
    assert calls == [1]


def test_no_verdict_means_no_reason() -> None:
    assert frost_risk_of(bed(FrostRisk.HIGH), None) is False
