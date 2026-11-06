"""Gathers the inputs of a bed's nutrient hint and asks the engine (REQ-053 GP-FR-125; WP 8.10, #2653).

The bed summary (``GET /locations/{key}/summary``, :meth:`GardenResourceService.get_summary`) carries the hint; there
is no route of its own. The rules are :mod:`app.domain.engines.nutrient_hint_engine`; this service only reads:

* the stored ``nutrient_demand`` of each species standing in the bed, only for species the tenant may read
  (:func:`~app.domain.services.species_visibility.readable_species`) - a species without one stays ``None``, no
  family value is put in its place (hint-only list: no silent default);
* whether the preceding crop fixes nitrogen: the newest year of the bed's rotation history (the reader behind
  ``GET /locations/{key}/rotation``) before the current one, main crop or green manure, without the species standing
  now; ``Species.nitrogen_fixing``, else the family's flag. A standing species that fixes nitrogen is a flag of its
  own;
* from the care log (``care_events`` carry ``tenant_key``): the newest N input (any feeding, or an amendment with
  manure or horn shavings - not compost, R-005), the newest N-binding mulch - both within the configured read window
  - and the newest lab content classes by CAL (no window). Every read is bounded.

Read-only. :meth:`NutrientHintService.assess` takes a location its caller already resolved through
:mod:`~app.domain.services.location_ownership` (a bed has no ``tenant_key`` of its own, #2107) and the tenant
keyword-only, without a default; every read below is scoped by that tenant.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from app.common.datetimes import now_utc
from app.common.enums import NutrientDemand, PlanRole
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.engines.nutrient_hint_engine import (
    DEFAULT_CONFIG,
    NutrientHintConfig,
    NutrientHintInputs,
    assess,
    is_n_binding_mulch,
    is_n_input_amendment,
    lab_content_classes,
)
from app.domain.interfaces.care_event_repository import CareEventFilter, ICareEventRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.nutrient_hint import NutrientHint
from app.domain.models.site import Location
from app.domain.models.species import Species
from app.domain.services.species_visibility import readable_species

#: Feedings, amendments and mulchings are read ``NutrientHintConfig.read_window_days`` back; soil analyses without a
#: window (a lab analysis is repeated every few years; its validity is research item R-016).
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
        at = now if now is not None else now_utc()
        location_key = location.key or ""
        standing = list(species_keys)[:MAX_SPECIES]
        readable = self._readable(standing, tenant_key=tenant_key)
        demands: list[NutrientDemand | None] = [
            readable[key].nutrient_demand if key in readable else None for key in standing
        ]
        inputs = NutrientHintInputs(
            now=at,
            growing_medium_kind=location.soil_profile.growing_medium_kind if location.soil_profile else None,
            species_demands=demands,
            unreadable_species=len(standing) - len(readable),
            preceding_nitrogen_fixing=self._preceding_nitrogen_fixing(
                location, set(standing), at.year, tenant_key=tenant_key
            ),
            standing_nitrogen_fixing=self._standing_nitrogen_fixing(readable, tenant_key=tenant_key),
            last_nutrient_input_at=self._last_nutrient_input(location_key, at, tenant_key=tenant_key),
            last_n_binding_mulch_at=self._last_n_binding_mulch(location_key, at, tenant_key=tenant_key),
            content_classes=self._content_classes(location_key, at, tenant_key=tenant_key),
            soil_profile=location.soil_profile,
        )
        return assess(inputs, self._config)

    # ── Reads ────────────────────────────────────────────────────────────────

    def _readable(self, species_keys: Sequence[str], *, tenant_key: str) -> dict[str, Species]:
        found: dict[str, Species] = {}
        for key in species_keys:
            species = readable_species(self._species, key, tenant_key)
            if species is not None:
                found[key] = species
        return found

    def _standing_nitrogen_fixing(self, readable: dict[str, Species], *, tenant_key: str) -> bool:
        if not readable:
            return False
        resolver = self._validator.timeline_resolver(tenant_key)
        return any(_fixes_nitrogen(species, resolver.family(species.family_key)) for species in readable.values())

    def _preceding_nitrogen_fixing(
        self, location: Location, standing: set[str], this_year: int, *, tenant_key: str
    ) -> bool:
        """Whether the preceding crop fixes nitrogen: the newest rotation year before the current one.

        Only main crops and green manures count (a fallow year has no crop), and a species standing in the bed now is
        not its own preceding crop - it is the ``standing_nitrogen_fixing`` flag instead.
        """
        entries, _reset_at = self._validator.bed_rotation_entries(location, tenant_key=tenant_key)
        earlier = [
            entry
            for entry in entries
            if entry.year < this_year
            and entry.plan_role in _CROP_ROLES
            and (entry.species_key is None or entry.species_key not in standing)
        ]
        if not earlier:
            return False
        newest = max(entry.year for entry in earlier)
        resolver = self._validator.timeline_resolver(tenant_key)
        return any(
            _fixes_nitrogen(resolver.species(entry.species_key), resolver.family(entry.family_key))
            for entry in earlier
            if entry.year == newest
        )

    def _read(
        self, location_key: str, category: str, at: datetime, limit: int, *, tenant_key: str, windowed: bool = True
    ) -> list[tuple[datetime, str | None, list[dict[str, Any]] | None]]:
        rows = self._events.list_events(
            CareEventFilter(
                location_key=location_key,
                category=category,
                performed_from=at - timedelta(days=self._config.read_window_days) if windowed else None,
                performed_to=at,
                exclude_voided=True,
            ),
            tenant_key=tenant_key,
            offset=0,
            limit=limit,
        )
        return [(row.event.performed_at, row.event.material, row.event.measurements) for row in rows]

    def _last_nutrient_input(self, location_key: str, at: datetime, *, tenant_key: str) -> datetime | None:
        """The newest N input: any ``feeding`` (a pure-K one too, until a feeding carries an N field), or a
        ``soil_amendment`` with manure or horn shavings - compost is no N supplier (R-005)."""
        found = [performed for performed, _m, _x in self._read(location_key, "feeding", at, 1, tenant_key=tenant_key)]
        found += [
            performed
            for performed, material, _x in self._read(
                location_key, "soil_amendment", at, MAX_AMENDMENTS, tenant_key=tenant_key
            )
            if is_n_input_amendment(material)
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


#: Rotation roles with a crop: a fallow year has none.
_CROP_ROLES: frozenset[str] = frozenset({PlanRole.MAIN_CROP.value, PlanRole.GREEN_MANURE.value})


def _fixes_nitrogen(species: Species | None, family: BotanicalFamily | None) -> bool:
    """``Species.nitrogen_fixing`` when the species states it, else the family's flag."""
    if species is not None and species.nitrogen_fixing is not None:
        return species.nitrogen_fixing
    return family is not None and family.nitrogen_fixing
