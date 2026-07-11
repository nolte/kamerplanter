"""REQ-037 — materialised daily irrigation-demand record.

One :class:`IrrigationDemand` is the persisted output of the
``compute_irrigation_demand`` Celery task for a single (site, run, day): the ET₀
estimate, the resolved crop coefficient, the derived crop water balance and the
recommended irrigation volume. It is tenant-scoped (inherits ``tenant_key`` from
the owning site) and idempotent on ``(site_key, run_key, demand_date)``.

Downstream consumers:

* :class:`~app.domain.services.watering_service.WateringService` reads the latest
  record to drive the REQ-037 ET override of the suggested watering volume.
* the REQ-022 care-reminder logic suppresses the watering reminder when
  ``net_demand_mm_capped == 0`` (rain already covered the demand).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain.calculators.evapotranspiration_calculator import Et0Method, Et0Quality


class IrrigationDemand(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    site_key: str
    #: The planting run the demand was computed for; ``None`` for a site-level
    #: aggregate demand not tied to a specific run.
    run_key: str | None = None
    demand_date: date
    # ── ET₀ / method provenance ──
    et0_mm: float
    et_method: Et0Method
    method_reason: str = ""
    quality: Et0Quality = "medium"
    weather_source: str = ""
    # ── Crop water balance ──
    kc_used: float
    kc_source: str = ""
    etc_mm: float
    effective_precipitation_mm: float = 0.0
    net_demand_mm: float
    net_demand_mm_capped: float
    recommended_volume_liters: float
    area_m2: float = Field(default=1.0, ge=0)
    computed_at: datetime | None = None

    model_config = {"populate_by_name": True}
