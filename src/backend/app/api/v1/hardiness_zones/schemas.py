"""REQ-039 — API schemas for the hardiness-zone catalog and per-site resolution."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.domain.models.site import HardinessZoneSource


class HardinessZoneResponse(BaseModel):
    """One canonical hardiness zone (global reference data)."""

    zone: str
    zone_number: int
    subzone: str
    temp_min_c: float
    temp_max_c: float
    temp_min_f: float
    temp_max_f: float
    description_de: str
    representative_regions_de: list[str]
    typical_last_frost_md: str | None = None
    typical_first_frost_md: str | None = None


class SiteHardinessResponse(BaseModel):
    """A site's resolved hardiness zone plus the matching catalog entry."""

    site_key: str
    hardiness_zone: str | None
    hardiness_zone_source: HardinessZoneSource
    hardiness_zone_resolved_at: datetime | None
    mean_annual_minimum_c: float | None
    last_frost_date_avg: date | None
    first_frost_date_avg: date | None
    zone: HardinessZoneResponse | None = None
