"""REQ-047 §3.4 — auto-materialisation of the per-plant overwintering profile.

Derives (and keeps in sync) the instance-level :class:`OverwinteringProfile` from
the species template + the site's winter-hardiness ampel, without any user
interaction. Triggered on the ``growing → pre_winter`` season transition for every
plant at an outdoor/greenhouse site.

Guarantees:

* **Winter-protection guard** — a winter-hardy species (ampel green) gets *no*
  profile and *no* winter-protection reminder (AC-9).
* **Override protection** — a ``user_overridden`` profile is never overwritten;
  only missing provenance fields are filled additively (AC-11).
* **D5** — the derived path / winter action can never contradict the ampel; the
  underlying ``OverwinteringProfileService.auto_generate_profile`` enforces it by
  construction.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from app.common.enums import GrowthHabit, RootType, WinterHardinessLight
from app.domain.engines.winter_hardiness_engine import derive_winter_path, evaluate_winter_hardiness

if TYPE_CHECKING:
    from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
    from app.domain.interfaces.overwintering_profile_template_repository import (
        IOverwinteringProfileTemplateRepository,
    )
    from app.domain.interfaces.species_repository import ISpeciesRepository
    from app.domain.models.overwintering_profile import OverwinteringProfile
    from app.domain.models.plant_instance import PlantInstance
    from app.domain.models.site import Site
    from app.domain.services.overwintering_profile_service import OverwinteringProfileService

logger = structlog.get_logger(__name__)

#: Root types / growth habits that mark a tuber/bulb/corm geophyte (dig-and-store).
_GEOPHYTE_ROOT_TYPES = frozenset({RootType.TUBEROUS, RootType.BULBOUS, RootType.CORM})


def _is_geophyte(species) -> bool:  # noqa: ANN001 — Species (avoid import at runtime)
    return species.root_type in _GEOPHYTE_ROOT_TYPES or species.growth_habit == GrowthHabit.BULB_GEOPHYTE


class OverwinteringMaterializer:
    def __init__(
        self,
        overwintering_service: OverwinteringProfileService,
        overwintering_repo: IOverwinteringProfileRepository,
        species_repo: ISpeciesRepository,
        template_repo: IOverwinteringProfileTemplateRepository | None = None,
    ) -> None:
        self._service = overwintering_service
        self._repo = overwintering_repo
        self._species_repo = species_repo
        self._template_repo = template_repo

    def materialize(self, plant: PlantInstance, site: Site) -> OverwinteringProfile | None:
        """Materialise / refresh the plant's overwintering profile.

        Returns the resulting profile, or ``None`` when no profile is needed
        (winter-hardy species) or the species context cannot be resolved.
        """
        if not plant.key or not plant.species_key:
            return None
        # AC-29 — a plant whose lifecycle has already ended (a monocarpic/biennial
        # that has passed its flowering/senescence phase, or any harvested/died/
        # cancelled instance, REQ-003) never gets a *new* overwintering profile: the
        # next pre_winter transition must not materialise one for a plant that will
        # not see another winter. An already-materialised profile is left untouched.
        if plant.termination_type is not None and self._repo.get_profile_by_plant_key(plant.key) is None:
            logger.info(
                "overwintering_materialize_skipped_terminated",
                plant_key=plant.key,
                termination_type=plant.termination_type.value,
            )
            return None
        species = self._species_repo.get_by_key(plant.species_key)
        if species is None:
            return None

        species_zone = species.hardiness_zones[0] if species.hardiness_zones else None
        # REQ-039: prefer the auto-derived hardiness zone over legacy free-text.
        site_zone = getattr(site, "hardiness_zone", None) or site.climate_zone or None
        # AC-26 — a potted plant (container_volume_liters set) escalates a marginal
        # yellow (in-situ) light to red (relocate), because the root ball freezes in
        # a container. The escalation happens in exactly one place (the service
        # helper) so the derived_path stamped here matches the generated profile.
        is_container = plant.container_volume_liters is not None
        light = self._service.effective_hardiness_light(
            evaluate_winter_hardiness(species.frost_sensitivity, species_zone, site_zone),
            is_container=is_container,
        )
        if light == WinterHardinessLight.GREEN:
            # Winter-protection guard: no profile for a winter-hardy species (AC-9).
            return None

        derived_path = derive_winter_path(light)
        template_key = self._resolve_template_key(plant.species_key)
        existing = self._repo.get_profile_by_plant_key(plant.key)
        if existing is not None:
            return self._ensure_provenance(existing, derived_path, template_key)

        created = self._service.auto_generate_profile(
            site.tenant_key,
            plant_key=plant.key,
            frost_sensitivity=species.frost_sensitivity,
            species_zone=species_zone,
            site_zone=site_zone,
            is_geophyte=_is_geophyte(species),
            is_container=is_container,
            species_key=plant.species_key,
        )
        stamped = created.model_copy(
            update={
                "derived_path": derived_path,
                "materialized_at": datetime.now(UTC),
                "source_template_key": template_key,
            }
        )
        result = self._repo.update_profile(created.key or "", stamped)
        logger.info(
            "overwintering_profile_materialized",
            plant_key=plant.key,
            site_key=site.key,
            derived_path=derived_path,
        )
        return result

    # ── Helpers ─────────────────────────────────────────────────────────

    def _resolve_template_key(self, species_key: str) -> str | None:
        if self._template_repo is None:
            return None
        template = self._template_repo.get_template_by_species_key(species_key)
        return template.key if template is not None else None

    def _ensure_provenance(
        self,
        existing: OverwinteringProfile,
        derived_path: str,
        template_key: str | None,
    ) -> OverwinteringProfile:
        """Fill missing provenance fields additively without touching user values.

        Safe for ``user_overridden`` profiles: only the provenance markers
        (``derived_path`` / ``materialized_at`` / ``source_template_key``) are
        back-filled when absent — never the user's winter action or conditions.
        """
        updates: dict = {}
        if existing.derived_path is None:
            updates["derived_path"] = derived_path
        if existing.materialized_at is None:
            updates["materialized_at"] = datetime.now(UTC)
        if existing.source_template_key is None and template_key is not None:
            updates["source_template_key"] = template_key
        if not updates:
            return existing
        merged = existing.model_copy(update=updates)
        return self._repo.update_profile(existing.key or "", merged)
