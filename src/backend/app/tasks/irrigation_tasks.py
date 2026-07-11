"""REQ-037 §7 — Celery task that materialises the daily irrigation demand.

Runs shortly after the daily weather fetch. For every **outdoor or greenhouse**
site with GPS it takes the most relevant :class:`WeatherForecast`, computes the
FAO-56 reference evapotranspiration ET₀ (Penman-Monteith when humidity+wind are
present, Hargreaves otherwise) and, for each active planting run at the site,
resolves the crop coefficient Kc (phase → species → category → global) and derives
the net irrigation demand. One :class:`IrrigationDemand` per (site, run, day) is
upserted (idempotent).

Indoor sites are intentionally skipped — their watering stays interval-based
(REQ-022). The read/write path is tenant-scoped (records inherit the site's
``tenant_key``); one failing site never aborts the cross-tenant run.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import structlog

from app.config.settings import settings
from app.domain.calculators.crop_coefficient import resolve_kc
from app.domain.calculators.evapotranspiration_calculator import EvapotranspirationCalculator
from app.domain.models.irrigation_demand import IrrigationDemand
from app.tasks import celery_app

logger = structlog.get_logger(__name__)

#: Site types for which an irrigation demand is materialised (open-air growing
#: surfaces exposed to weather); indoor sites keep interval-based watering.
_IRRIGATION_SITE_TYPES = ("outdoor", "greenhouse")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def compute_irrigation_demand(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Compute and upsert the daily irrigation demand for every eligible site/run."""
    if not settings.weather_enabled or not settings.irrigation_demand_enabled:
        return {"status": "skipped", "reason": "irrigation_demand_disabled"}

    from app.common.dependencies import (
        get_irrigation_demand_repo,
        get_lifecycle_repo,
        get_planting_run_repo,
        get_site_repo,
        get_species_repo,
        get_weather_forecast_repo,
    )
    from app.domain.models.site import Site

    site_repo = get_site_repo()
    forecast_repo = get_weather_forecast_repo()
    run_repo = get_planting_run_repo()
    species_repo = get_species_repo()
    lifecycle_repo = get_lifecycle_repo()
    demand_repo = get_irrigation_demand_repo()
    calculator = EvapotranspirationCalculator()

    site_docs = site_repo.find_site_docs_by_types(list(_IRRIGATION_SITE_TYPES))
    today = datetime.now(UTC).date()
    written = 0
    skipped = 0
    errors: list[dict] = []

    for doc in site_docs:
        site = Site(**site_repo._from_doc(doc))  # noqa: SLF001 — cross-tenant iteration
        if not site.key or site.gps_coordinates is None:
            skipped += 1
            continue

        try:
            forecast = _pick_forecast(forecast_repo.find_by_site(site.key, site.tenant_key), today)
            if forecast is None or forecast.temp_min_c is None or forecast.temp_max_c is None:
                skipped += 1
                continue

            latitude, _longitude = site.gps_coordinates
            et0 = calculator.calculate_et0(
                latitude_deg=latitude,
                day_of_year=forecast.forecast_date.timetuple().tm_yday,
                temp_min_c=forecast.temp_min_c,
                temp_max_c=forecast.temp_max_c,
                humidity_percent=forecast.humidity_percent,
                wind_speed_kmh=forecast.wind_speed_kmh,
                solar_radiation_mj_m2=forecast.solar_radiation_mj_m2,
            )

            runs = run_repo.get_runs_at_site(site.key)
            if not runs:
                skipped += 1
                continue

            for run in runs:
                written += _materialise_for_run(
                    site=site,
                    run=run,
                    forecast=forecast,
                    et0=et0,
                    calculator=calculator,
                    species_repo=species_repo,
                    lifecycle_repo=lifecycle_repo,
                    run_repo=run_repo,
                    site_repo=site_repo,
                    demand_repo=demand_repo,
                    today=today,
                )
        except Exception as exc:  # noqa: BLE001 — per-site isolation: one failure never aborts the run
            logger.warning("irrigation_demand_site_failed", site_key=site.key, error=str(exc))
            errors.append({"site_key": site.key, "error": str(exc)})
            continue

    logger.info("irrigation_demand_complete", written=written, skipped=skipped, errors=len(errors))
    return {"status": "ok", "written": written, "skipped": skipped, "errors": len(errors)}


def _materialise_for_run(
    *,
    site,  # noqa: ANN001
    run,  # noqa: ANN001
    forecast,  # noqa: ANN001
    et0,  # noqa: ANN001
    calculator: EvapotranspirationCalculator,
    species_repo,  # noqa: ANN001
    lifecycle_repo,  # noqa: ANN001
    run_repo,  # noqa: ANN001
    site_repo,  # noqa: ANN001
    demand_repo,  # noqa: ANN001
    today: date,
) -> int:
    """Resolve Kc + area for one run, compute the balance and upsert. Returns 1."""
    phase_kc = _resolve_phase_kc(run, lifecycle_repo)
    species_kc, plant_category = _resolve_species_kc(run, run_repo, species_repo)
    kc, kc_source = resolve_kc(phase_kc=phase_kc, species_kc=species_kc, plant_category=plant_category)

    area_m2 = _resolve_area_m2(run, site_repo)
    balance = calculator.calculate_water_balance(
        et0_mm=et0.et0_mm,
        crop_coefficient_kc=kc,
        precipitation_mm=forecast.precipitation_mm or 0.0,
        water_holding_capacity_mm=None,
        area_m2=area_m2,
    )

    demand = IrrigationDemand(
        tenant_key=site.tenant_key,
        site_key=site.key,
        run_key=run.key,
        demand_date=today,
        et0_mm=et0.et0_mm,
        et_method=et0.method,
        method_reason=et0.method_reason,
        quality=et0.quality,
        weather_source=forecast.source,
        kc_used=balance.kc_used,
        kc_source=kc_source,
        etc_mm=balance.etc_mm,
        effective_precipitation_mm=balance.effective_precipitation_mm,
        net_demand_mm=balance.net_demand_mm,
        net_demand_mm_capped=balance.net_demand_mm_capped,
        recommended_volume_liters=balance.recommended_volume_liters,
        area_m2=area_m2,
        computed_at=datetime.now(UTC),
    )
    demand_repo.upsert(demand)
    return 1


def _pick_forecast(forecasts: list, reference: date):  # noqa: ANN001, ANN201
    """Pick the forecast for ``reference`` day, else the nearest available one."""
    if not forecasts:
        return None
    exact = [f for f in forecasts if f.forecast_date == reference]
    if exact:
        return exact[0]
    return min(forecasts, key=lambda f: abs((f.forecast_date - reference).days))


def _resolve_phase_kc(run, lifecycle_repo) -> float | None:  # noqa: ANN001
    if not run.current_phase_key or lifecycle_repo is None:
        return None
    phase = lifecycle_repo.get_phase_by_key(run.current_phase_key)
    return getattr(phase, "crop_coefficient_kc", None) if phase else None


def _resolve_species_kc(run, run_repo, species_repo):  # noqa: ANN001, ANN201
    """Return ``(species_default_kc, plant_category)`` for the run's first species."""
    entries = run_repo.get_entries(run.key) if run.key else []
    if not entries:
        return None, None
    species = species_repo.get_by_key(entries[0].species_key)
    if species is None:
        return None, None
    return getattr(species, "default_crop_coefficient_kc", None), getattr(species, "plant_category", None)


def _resolve_area_m2(run, site_repo) -> float:  # noqa: ANN001
    """Growing area for the run — the location area, defaulting to 1 m²."""
    if not run.location_key:
        return 1.0
    location = site_repo.get_location_by_key(run.location_key)
    if location is None or not location.area_m2:
        return 1.0
    return float(location.area_m2)
