"""Gathers the inputs of a bed's nutrient hint and asks the engine (REQ-053 GP-FR-125; WP 8.10, #2653).

The bed summary (``GET /locations/{key}/summary``, :meth:`GardenResourceService.get_summary`) carries the hint; there
is no route of its own. The rules are :mod:`app.domain.engines.nutrient_hint_engine`; this service only reads:

* the stored ``nutrient_demand`` of each species standing in the bed, only for species the tenant may read
  (:func:`~app.domain.services.species_visibility.readable_species`) - a species without one stays ``None``, no
  family value is put in its place (hint-only list: no silent default);
* whether the crop of the previous year fixes nitrogen: the bed's rotation history (the reader behind
  ``GET /locations/{key}/rotation``), ``Species.nitrogen_fixing``, else the family's flag;
* from the care log (``care_events`` carry ``tenant_key``): the newest feeding or nutrient amendment, the newest
  N-binding mulch and the newest lab content classes - each read bounded and within :data:`READ_WINDOW_DAYS`.

Read-only. :meth:`NutrientHintService.assess` takes a location its caller already resolved through
:mod:`~app.domain.services.location_ownership` (a bed has no ``tenant_key`` of its own, #2107) and the tenant
keyword-only, without a default; every read below is scoped by that tenant.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from app.common.datetimes import today_utc
from app.common.enums import NutrientDemand, PlanRole
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.engines.nutrient_hint_engine import (
    DEFAULT_CONFIG,
    NutrientHintConfig,
    NutrientHintInputs,
    assess,
    is_n_binding_mulch,
    lab_content_classes,
)
from app.domain.engines.task_completion_engine import NUTRIENT_MATERIALS
from app.domain.interfaces.care_event_repository import CareEventFilter, ICareEventRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.nutrient_hint import NutrientHint
from app.domain.models.site import Location
from app.domain.services.species_visibility import readable_species

#: Feedings, amendments and mulchings are read this far back: an input older than a year counts as "not recorded".
#: Soil analyses are read without a window (a lab analysis is repeated every few years).
READ_WINDOW_DAYS = 365
#: At most this many events are read per category (the reads are bounded).
MAX_AMENDMENTS = 50
MAX_MULCHINGS = 20
MAX_ANALYSES = 20
#: At most this many current species are looked up (a bed summary lists every species, a bed holds few).
MAX_SPECIES = 50


class NutrientHintService:
    def __init__(
        self,
        species_repo: ISpeciesRepository,
        care_event_repo: ICareEventRepository,
        validator: CropRotationValidator,
        config: NutrientHintConfig = DEFAULT_CONFIG,
    ) -> None:
        self._species = species_repo
        self._events = care_event_repo
        self._validator = validator
        self._config = config

    def assess(
        self,
        location: Location,
        species_keys: Sequence[str],
        *,
        tenant_key: str,
        now: datetime | None = None,
    ) -> NutrientHint:
        """The hint of an owned bed whose standing species are ``species_keys``."""
        at = now or datetime.now(UTC)
        location_key = location.key or ""
        inputs = NutrientHintInputs(
            now=at,
            growing_medium_kind=location.soil_profile.growing_medium_kind if location.soil_profile else None,
            species_demands=self._demands(species_keys, tenant_key=tenant_key),
            preceding_nitrogen_fixing=self._preceding_nitrogen_fixing(location, tenant_key=tenant_key),
            last_nutrient_input_at=self._last_nutrient_input(location_key, at, tenant_key=tenant_key),
            last_n_binding_mulch_at=self._last_n_binding_mulch(location_key, at, tenant_key=tenant_key),
            content_classes=self._content_classes(location_key, at, tenant_key=tenant_key),
        )
        return assess(inputs, self._config)

    # ── Reads ────────────────────────────────────────────────────────────────

    def _demands(self, species_keys: Sequence[str], *, tenant_key: str) -> list[NutrientDemand | None]:
        demands: list[NutrientDemand | None] = []
        for key in list(species_keys)[:MAX_SPECIES]:
            species = readable_species(self._species, key, tenant_key)
            demands += [species.nutrient_demand if species is not None else None]
        return demands

    def _preceding_nitrogen_fixing(self, location: Location, *, tenant_key: str) -> bool:
        """Whether a crop of the previous calendar year fixes nitrogen (a main crop or a green manure)."""
        previous = today_utc().year - 1
        entries, _reset_at = self._validator.bed_rotation_entries(location, tenant_key=tenant_key)
        resolver = self._validator.timeline_resolver(tenant_key)
        for entry in entries:
            if entry.year != previous or entry.plan_role == PlanRole.FALLOW.value:
                continue
            species = resolver.species(entry.species_key)
            if species is not None and species.nitrogen_fixing is not None:
                if species.nitrogen_fixing:
                    return True
                continue
            family = resolver.family(entry.family_key)
            if family is not None and family.nitrogen_fixing:
                return True
        return False

    def _read(
        self, location_key: str, category: str, at: datetime, limit: int, *, tenant_key: str, windowed: bool = True
    ) -> list[tuple[datetime, str | None, list[dict[str, Any]] | None]]:
        rows = self._events.list_events(
            CareEventFilter(
                location_key=location_key,
                category=category,
                performed_from=at - timedelta(days=READ_WINDOW_DAYS) if windowed else None,
                performed_to=at,
                exclude_voided=True,
            ),
            tenant_key=tenant_key,
            offset=0,
            limit=limit,
        )
        return [(row.event.performed_at, row.event.material, row.event.measurements) for row in rows]

    def _last_nutrient_input(self, location_key: str, at: datetime, *, tenant_key: str) -> datetime | None:
        """The newest ``feeding``, or ``soil_amendment`` with a nutrient material (§12.1, W-007)."""
        found = [performed for performed, _m, _x in self._read(location_key, "feeding", at, 1, tenant_key=tenant_key)]
        found += [
            performed
            for performed, material, _x in self._read(
                location_key, "soil_amendment", at, MAX_AMENDMENTS, tenant_key=tenant_key
            )
            if material is not None and material.strip().lower() in NUTRIENT_MATERIALS
        ]
        return max(found, default=None)

    def _last_n_binding_mulch(self, location_key: str, at: datetime, *, tenant_key: str) -> datetime | None:
        rows = self._read(location_key, "mulching", at, MAX_MULCHINGS, tenant_key=tenant_key)
        return max((performed for performed, material, _x in rows if is_n_binding_mulch(material)), default=None)

    def _content_classes(self, location_key: str, at: datetime, *, tenant_key: str) -> dict[str, str]:
        # A lab analysis is taken every few years: the newest ones count whatever their age (no window).
        rows = self._read(location_key, "soil_analysis", at, MAX_ANALYSES, tenant_key=tenant_key, windowed=False)
        ordered = sorted(rows, key=lambda row: row[0], reverse=True)
        return lab_content_classes(measurements or [] for _p, _m, measurements in ordered)
