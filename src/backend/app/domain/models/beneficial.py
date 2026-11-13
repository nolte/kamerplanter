"""REQ-044 WP-8 — Nützlings-Stammdaten (analog REQ-010 ``Pest``).

Eine erkannte ``category=beneficial``-Klasse wird gegen diese Collection
gemappt, damit ein Nützling nie als zu bekämpfender Schädling dargestellt wird
(§9.1). Bewusst eigenständig gehalten (kein Eingriff ins REQ-010-Pest-Modell);
``preys_on`` referenziert pest-Slugs.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.models.species_names import normalize_names_i18n


class Beneficial(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    slug: str = Field(min_length=1, max_length=80)
    #: The stored name (German: the seed fills it from ``PestTaxon.common_name_de``).
    common_name: str = Field(min_length=1, max_length=200)
    #: Language code -> names in preference order (REQ-010 v1.8, #2936); only
    #: sourced names (E-10), resolved by ``species_names.localized_catalog_name``.
    common_names_i18n: dict[str, list[str]] = Field(default_factory=dict)
    scientific_name: str = Field(min_length=1, max_length=200)
    gbif_taxon_key: str | None = None
    preys_on: list[str] = Field(default_factory=list)
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("common_names_i18n")
    @classmethod
    def _normalize_common_names_i18n(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        return normalize_names_i18n(value)
