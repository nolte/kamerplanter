"""REQ-039 — canonical plant hardiness-zone reference entry.

One document per USDA half-zone (``1a`` … ``13b``) in the global, *not*
tenant-scoped ``hardiness_zones`` collection (analogous to
:class:`app.domain.models.botanical_family.BotanicalFamily`). The temperature
bounds are derived from the license-free USDA zone *schema* (see
:mod:`app.domain.engines.hardiness_zone_resolver`); the German descriptions,
representative regions and frost-date defaults are project-curated content — no
proprietary USDA/PHZM/PRISM data set is embedded.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

#: ``MM-DD`` calendar anchor for a typical frost date (year-agnostic).
_MONTH_DAY_PATTERN = re.compile(r"^\d{2}-\d{2}$")
#: ``<number><a|b>`` zone label, e.g. ``7a`` / ``13b``.
_ZONE_PATTERN = re.compile(r"^\d{1,2}[ab]$")


class HardinessZone(BaseModel):
    """A single canonical hardiness zone (reference data, global)."""

    key: str | None = Field(default=None, alias="_key")
    #: Canonical label and ``_key`` (e.g. ``"7a"``).
    zone: str
    zone_number: int = Field(ge=1, le=13)
    subzone: Literal["a", "b"]
    #: Temperature band of the mean annual minimum (°C / °F), from the schema.
    temp_min_c: float
    temp_max_c: float
    temp_min_f: float
    temp_max_f: float
    #: Curated, human-facing German content (empty for non-DACH zones).
    description_de: str = ""
    representative_regions_de: list[str] = Field(default_factory=list)
    #: Year-agnostic frost-date defaults (``MM-DD``) used to pre-fill the REQ-015
    #: frost anchors of a site when nothing more specific is known. ``None`` for
    #: zones without a curated default.
    typical_last_frost_md: str | None = None
    typical_first_frost_md: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("zone")
    @classmethod
    def validate_zone(cls, v: str) -> str:
        if not _ZONE_PATTERN.match(v):
            raise ValueError(f"Zonen-Label '{v}' muss dem Format '<Zahl><a|b>' entsprechen (z. B. '7a')")
        return v

    @field_validator("typical_last_frost_md", "typical_first_frost_md")
    @classmethod
    def validate_month_day(cls, v: str | None) -> str | None:
        if v is not None and not _MONTH_DAY_PATTERN.match(v):
            raise ValueError(f"Frostdatum '{v}' muss dem Format 'MM-TT' entsprechen (z. B. '05-15')")
        return v
