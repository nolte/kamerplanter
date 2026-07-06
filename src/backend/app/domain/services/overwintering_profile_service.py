"""REQ-022 §OverwinteringProfile service (G-002).

Tenant-scoped CRUD for overwintering profiles, auto-generation from the winter
hardiness traffic light, D5-invariant validation (HTTP 422 on contradiction) and
the dashboard hardiness overview.
"""

from pydantic import ValidationError as PydanticValidationError

from app.common.enums import (
    FrostTolerance,
    GrowthHabit,
    HardinessRating,
    RootType,
    SpringAction,
    WinterAction,
    WinterHardinessLight,
)
from app.common.exceptions import DuplicateError, NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import OverwinteringProfileKey
from app.domain.engines.winter_hardiness_engine import (
    derive_winter_path,
    evaluate_winter_hardiness,
    validate_d5_invariant,
)
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.interfaces.overwintering_profile_template_repository import (
    IOverwinteringProfileTemplateRepository,
)
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.overwintering_profile import (
    OverwinteringProfile,
    WinterHardinessOverview,
    WinterHardinessOverviewEntry,
)
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate

_ENTITY = "OverwinteringProfile"

#: Root types / growth habits that mark a tuber/bulb/corm geophyte (dig-and-store).
_GEOPHYTE_ROOT_TYPES = frozenset({RootType.TUBEROUS, RootType.BULBOUS, RootType.CORM})

#: Maps a stored ``hardiness_rating`` back onto the traffic light so the D5
#: invariant can be re-checked without re-resolving species/site context.
_RATING_TO_LIGHT: dict[HardinessRating, WinterHardinessLight] = {
    HardinessRating.HARDY: WinterHardinessLight.GREEN,
    HardinessRating.NEEDS_PROTECTION: WinterHardinessLight.YELLOW,
    HardinessRating.FROST_FREE: WinterHardinessLight.RED,
    HardinessRating.DIG_AND_STORE: WinterHardinessLight.RED,
}

#: Default rating/action per traffic light for auto-generation.
_LIGHT_TO_RATING: dict[WinterHardinessLight, HardinessRating] = {
    WinterHardinessLight.GREEN: HardinessRating.HARDY,
    WinterHardinessLight.YELLOW: HardinessRating.NEEDS_PROTECTION,
    WinterHardinessLight.RED: HardinessRating.FROST_FREE,
}

_LIGHT_TO_ACTION: dict[WinterHardinessLight, WinterAction] = {
    WinterHardinessLight.GREEN: WinterAction.NONE,
    WinterHardinessLight.YELLOW: WinterAction.MULCH,
    WinterHardinessLight.RED: WinterAction.MOVE_INDOORS,
}


class OverwinteringProfileService:
    def __init__(
        self,
        repo: IOverwinteringProfileRepository,
        site_repo: ISiteRepository | None = None,
        plant_repo: IPlantInstanceRepository | None = None,
        planting_run_repo: IPlantingRunRepository | None = None,
        template_repo: IOverwinteringProfileTemplateRepository | None = None,
        species_repo: ISpeciesRepository | None = None,
    ) -> None:
        self._repo = repo
        self._site_repo = site_repo
        self._plant_repo = plant_repo
        self._planting_run_repo = planting_run_repo
        self._template_repo = template_repo
        self._species_repo = species_repo

    # ── CRUD ────────────────────────────────────────────────────────────

    def list_profiles(
        self, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> tuple[list[OverwinteringProfile], int]:
        return self._repo.list_by_tenant(tenant_key, offset, limit)

    def get_profile(self, key: OverwinteringProfileKey, tenant_key: str) -> OverwinteringProfile:
        profile = self._repo.get_profile_by_key(key)
        if profile is None:
            raise NotFoundError(_ENTITY, key)
        verify_tenant_ownership(profile, tenant_key, _ENTITY)
        return profile

    def create_profile(self, profile: OverwinteringProfile, tenant_key: str) -> OverwinteringProfile:
        self._require_single_subject(profile)
        profile.tenant_key = tenant_key
        self._validate_d5(profile)
        self._verify_subject_ownership(profile, tenant_key)
        self._verify_winter_quarter_ownership(profile, tenant_key)
        self._require_no_existing_profile(profile)
        created = self._repo.create_profile(profile)
        self._wire_edges_or_rollback(created)
        return created

    def update_profile(self, key: OverwinteringProfileKey, tenant_key: str, updates: dict) -> OverwinteringProfile:
        existing = self.get_profile(key, tenant_key)
        data = existing.model_dump()
        data.update(updates)
        # Preserve identity/ownership fields regardless of the payload.
        data["tenant_key"] = tenant_key
        # Cross-field model validators (e.g. tuber_status ↔ hardiness_rating) raise
        # a raw pydantic error on the merged result; translate it to a 422 domain
        # error so the PUT merge path returns 422 instead of 500 (B2).
        try:
            merged = OverwinteringProfile(**data)
        except PydanticValidationError as exc:
            raise ValidationError(
                "The overwintering profile update is invalid.",
                details=[
                    {
                        "field": ".".join(str(loc) for loc in err["loc"]) or "body",
                        "reason": err["msg"],
                        "code": err["type"],
                    }
                    for err in exc.errors()
                ],
            ) from exc
        self._require_single_subject(merged)
        self._validate_d5(merged)
        self._verify_winter_quarter_ownership(merged, tenant_key)
        return self._repo.update_profile(key, merged)

    def delete_profile(self, key: OverwinteringProfileKey, tenant_key: str) -> bool:
        self.get_profile(key, tenant_key)
        return self._repo.delete_profile(key)

    # ── REQ-047 per-plant profile access / override ─────────────────────

    def get_plant_profile(self, plant_key: str, tenant_key: str) -> OverwinteringProfile:
        """Return the plant's (auto-materialised) overwintering profile.

        Raises :class:`NotFoundError` (404) when the plant has no profile yet.
        """
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            raise NotFoundError(_ENTITY, plant_key)
        verify_tenant_ownership(profile, tenant_key, _ENTITY)
        return profile

    def override_plant_profile(self, plant_key: str, tenant_key: str, updates: dict) -> OverwinteringProfile:
        """Override individual fields of the plant's profile (sets ``user_overridden``).

        A contradiction with the hardiness-derived winter path (D5) is rejected
        with 422; an otherwise invalid merge with 422 (never a 500).
        """
        profile = self.get_plant_profile(plant_key, tenant_key)
        data = profile.model_dump()
        data.update(updates)
        data["tenant_key"] = tenant_key
        data["user_overridden"] = True
        try:
            merged = OverwinteringProfile(**data)
        except PydanticValidationError as exc:
            raise ValidationError(
                "The overwintering profile update is invalid.",
                details=[
                    {
                        "field": ".".join(str(loc) for loc in err["loc"]) or "body",
                        "reason": err["msg"],
                        "code": err["type"],
                    }
                    for err in exc.errors()
                ],
            ) from exc
        self._require_single_subject(merged)
        self._validate_d5(merged)
        # B1 — an override may (re)point ``winter_quarter_key`` at a location; reject
        # a foreign/unknown one with the same 404 as every other write path, so a
        # tenant can never reference another tenant's location via PATCH.
        self._verify_winter_quarter_ownership(merged, tenant_key)
        return self._repo.update_profile(profile.key or "", merged)

    def rematerialize_plant_profile(
        self,
        plant_key: str,
        tenant_key: str,
        *,
        frost_sensitivity: FrostTolerance | None = None,
        species_zone: str | None = None,
        site_zone: str | None = None,
        is_geophyte: bool = False,
        species_key: str | None = None,
        winter_action_month: int = 10,
        spring_action_month: int = 3,
    ) -> OverwinteringProfile:
        """Reset the plant's profile to the automatic derivation (``user_overridden=False``).

        Re-derives ``hardiness_rating`` / ``winter_action`` / ``spring_action`` and
        the winter-quarter fields from the ampel + species template, in place,
        satisfying the D5 invariant by construction.
        """
        from datetime import UTC, datetime

        profile = self.get_plant_profile(plant_key, tenant_key)
        light = evaluate_winter_hardiness(frost_sensitivity, species_zone, site_zone)
        rating = _LIGHT_TO_RATING[light]
        action = _LIGHT_TO_ACTION[light]
        if light == WinterHardinessLight.RED and is_geophyte:
            rating = HardinessRating.DIG_AND_STORE
            action = WinterAction.DIG_STORE

        spring_action, spring_month = self._derive_spring_action(light, action, spring_action_month)
        template = self._resolve_template(species_key)
        quarter = self._template_quarter_fields(template, action)

        merged = profile.model_copy(
            update={
                "hardiness_zone_min": species_zone,
                "hardiness_rating": rating,
                "winter_action": action,
                "winter_action_month": winter_action_month,
                "spring_action": spring_action,
                "spring_action_month": spring_month,
                "user_overridden": False,
                "auto_generated": True,
                "derived_path": derive_winter_path(light),
                "materialized_at": datetime.now(UTC),
                "source_template_key": template.key if template is not None else None,
                **quarter,
            }
        )
        validate_d5_invariant(merged, light)
        # B1 — the reset keeps the existing ``winter_quarter_key`` (it is not part of
        # the re-derivation). Re-verify ownership so a foreign reference injected
        # before this guard existed is not silently retained; a stale/foreign one is
        # rejected with the same 404 as the other write paths.
        self._verify_winter_quarter_ownership(merged, tenant_key)
        return self._repo.update_profile(profile.key or "", merged)

    # ── REQ-047 reset orchestration (NFR-001: domain logic out of the router) ──

    def reset_plant_profile(self, plant_key: str, tenant_key: str) -> OverwinteringProfile:
        """Reset a plant's profile to the automatic derivation (C1).

        Resolves the species / site context the derivation needs (frost
        sensitivity, hardiness zones, geophyte classification, site climate zone)
        inside the service instead of the API layer, then delegates to
        :meth:`rematerialize_plant_profile`. The router only forwards the identifiers.
        """
        # Ensure the profile exists and belongs to the tenant (404 otherwise).
        self.get_plant_profile(plant_key, tenant_key)
        plant = self._require_owned_plant(plant_key, tenant_key)

        frost_sensitivity, species_zone, is_geophyte = self._resolve_species_context(plant.species_key)
        site_zone = self._resolve_site_zone(plant, tenant_key)

        return self.rematerialize_plant_profile(
            plant_key,
            tenant_key,
            frost_sensitivity=frost_sensitivity,
            species_zone=species_zone,
            site_zone=site_zone,
            is_geophyte=is_geophyte,
            species_key=plant.species_key,
        )

    def _require_owned_plant(self, plant_key: str, tenant_key: str):  # noqa: ANN202 — PlantInstance (avoid import cycle)
        if self._plant_repo is None:
            raise NotFoundError("PlantInstance", plant_key)
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None or plant.tenant_key != tenant_key:
            raise NotFoundError("PlantInstance", plant_key)
        return plant

    def _resolve_species_context(self, species_key: str | None) -> tuple[FrostTolerance | None, str | None, bool]:
        """Resolve (frost_sensitivity, species_zone, is_geophyte) for a species."""
        if not species_key or self._species_repo is None:
            return None, None, False
        species = self._species_repo.get_by_key(species_key)
        if species is None:
            return None, None, False
        species_zone = species.hardiness_zones[0] if species.hardiness_zones else None
        is_geophyte = species.root_type in _GEOPHYTE_ROOT_TYPES or species.growth_habit == GrowthHabit.BULB_GEOPHYTE
        return species.frost_sensitivity, species_zone, is_geophyte

    def _resolve_site_zone(self, plant, tenant_key: str) -> str | None:  # noqa: ANN001 — PlantInstance
        """Resolve the owning site's climate zone (tenant-guarded)."""
        if not plant.site_key or self._site_repo is None:
            return None
        site = self._site_repo.get_site_by_key(plant.site_key)
        if site is not None and site.tenant_key == tenant_key and site.climate_zone:
            return site.climate_zone
        return None

    # ── Auto-generation ─────────────────────────────────────────────────

    def auto_generate_profile(
        self,
        tenant_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
        frost_sensitivity: FrostTolerance | None = None,
        species_zone: str | None = None,
        site_zone: str | None = None,
        winter_action_month: int = 10,
        spring_action_month: int = 3,
        winter_quarter_key: str | None = None,
        is_geophyte: bool = False,
        species_key: str | None = None,
    ) -> OverwinteringProfile:
        """Derive an overwintering profile from the winter hardiness ampel.

        The traffic light (species frost sensitivity + zone gap) determines both
        the ``hardiness_rating`` and the default ``winter_action`` so the result
        satisfies the D5 invariant by construction. A frost-tender geophyte
        (tuber/bulb/corm) on the red path is stored as ``dig_and_store`` rather
        than moved indoors, so the tuber-dig / storage-check reminders can fire
        (B3).

        When ``species_key`` resolves a species-level template, its curated
        winter-quarter conditions (temperature range, watering) and tuber-storage
        details replace the generic defaults — but only on a relocation path
        (``move_indoors`` / ``dig_store``), so the enrichment can never contradict
        the derived D5 path.
        """
        light = evaluate_winter_hardiness(frost_sensitivity, species_zone, site_zone)
        rating = _LIGHT_TO_RATING[light]
        action = _LIGHT_TO_ACTION[light]

        # Red-path geophytes are dug up and stored, not relocated as a container.
        if light == WinterHardinessLight.RED and is_geophyte:
            rating = HardinessRating.DIG_AND_STORE
            action = WinterAction.DIG_STORE

        spring_action, spring_month = self._derive_spring_action(light, action, spring_action_month)

        template = self._resolve_template(species_key)
        quarter = self._template_quarter_fields(template, action)

        profile = OverwinteringProfile(
            plant_key=plant_key,
            planting_run_key=planting_run_key,
            hardiness_zone_min=species_zone,
            hardiness_rating=rating,
            winter_action=action,
            winter_action_month=winter_action_month,
            spring_action=spring_action,
            spring_action_month=spring_month,
            winter_quarter_key=winter_quarter_key,
            auto_generated=True,
            tenant_key=tenant_key,
            **quarter,
        )
        self._require_single_subject(profile)
        validate_d5_invariant(profile, light)
        self._verify_subject_ownership(profile, tenant_key)
        self._verify_winter_quarter_ownership(profile, tenant_key)
        self._require_no_existing_profile(profile)
        created = self._repo.create_profile(profile)
        self._wire_edges_or_rollback(created)
        return created

    @staticmethod
    def _derive_spring_action(
        light: WinterHardinessLight,
        winter_action: WinterAction,
        spring_action_month: int,
    ) -> tuple[SpringAction | None, int | None]:
        """Pick a spring action consistent with the winter path (B3).

        Green (in-situ, hardy) needs no spring action, so both action and month
        stay ``None``; otherwise the action is paired with its month so a month is
        never set without an action.
        """
        if light == WinterHardinessLight.GREEN:
            return None, None
        if winter_action == WinterAction.DIG_STORE:
            spring_action = SpringAction.REPLANT
        elif winter_action == WinterAction.MOVE_INDOORS:
            spring_action = SpringAction.MOVE_OUTDOORS
        else:
            spring_action = SpringAction.UNCOVER
        return spring_action, spring_action_month

    def _resolve_template(self, species_key: str | None) -> OverwinteringProfileTemplate | None:
        if not species_key or self._template_repo is None:
            return None
        return self._template_repo.get_template_by_species_key(species_key)

    @staticmethod
    def _template_quarter_fields(
        template: OverwinteringProfileTemplate | None,
        action: WinterAction,
    ) -> dict:
        """Species-accurate winter-quarter / storage fields for a relocation path.

        Enriches only when the template's *own* winter action equals the derived
        action, so a dig-and-store template's cold-storage numbers (e.g. 0–2 °C)
        never graft onto a move-indoors profile — and nothing leaks onto an in-situ
        (none/mulch/fleece/…) path.
        """
        if (
            template is None
            or template.winter_action != action
            or action not in {WinterAction.MOVE_INDOORS, WinterAction.DIG_STORE}
        ):
            return {}
        return template.winter_quarter_fields()

    # ── Shared reusable templates (N subjects → 1 template) ─────────────

    def _require_template_repo(self) -> IOverwinteringProfileTemplateRepository:
        if self._template_repo is None:
            raise ValueError("OverwinteringProfileService was constructed without a template repository.")
        return self._template_repo

    @staticmethod
    def _require_single_subject_keys(plant_key: str | None, planting_run_key: str | None) -> None:
        """Reject a subject that names neither or both of plant / planting run (422)."""
        if bool(plant_key) == bool(planting_run_key):
            raise ValidationError("Exactly one of plant_key / planting_run_key must be given.")

    def link_shared_template(
        self,
        tenant_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
        template_key: str | None = None,
        species_key: str | None = None,
        scientific_name: str | None = None,
    ) -> OverwinteringProfileTemplate:
        """Point a subject at the shared, reusable template for its species (N:1).

        Reuses one template document across every instance of the species instead
        of minting a per-instance profile. Idempotent: re-linking replaces the
        previous reference. Resolution prefers the unambiguous ``template_key`` slug;
        ``species_key`` and ``scientific_name`` are convenience fallbacks that can be
        ambiguous when several cultivar templates map to one species.
        """
        repo = self._require_template_repo()
        self._require_single_subject_keys(plant_key, planting_run_key)
        self._verify_subject_keys(tenant_key, plant_key=plant_key, planting_run_key=planting_run_key)

        template: OverwinteringProfileTemplate | None = None
        if template_key:
            template = repo.get_template_by_key(template_key)
        if template is None and species_key:
            template = repo.get_template_by_species_key(species_key)
        if template is None and scientific_name:
            template = repo.get_template_by_scientific_name(scientific_name)
        if template is None or not template.key:
            raise NotFoundError("OverwinteringProfileTemplate", template_key or species_key or scientific_name or "")

        repo.link_subject(template.key, plant_key=plant_key, planting_run_key=planting_run_key)
        return template

    def get_shared_template_for_subject(
        self,
        tenant_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> OverwinteringProfileTemplate | None:
        """Resolve the shared template a subject currently reuses, if any."""
        repo = self._require_template_repo()
        self._require_single_subject_keys(plant_key, planting_run_key)
        self._verify_subject_keys(tenant_key, plant_key=plant_key, planting_run_key=planting_run_key)
        return repo.get_template_for_subject(plant_key=plant_key, planting_run_key=planting_run_key)

    def unlink_shared_template(
        self,
        tenant_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> bool:
        """Drop a subject's shared-template reference. Returns True when one existed."""
        repo = self._require_template_repo()
        self._require_single_subject_keys(plant_key, planting_run_key)
        self._verify_subject_keys(tenant_key, plant_key=plant_key, planting_run_key=planting_run_key)
        return repo.unlink_subject(plant_key=plant_key, planting_run_key=planting_run_key) > 0

    # ── Dashboard overview ──────────────────────────────────────────────

    def get_hardiness_overview(self, tenant_key: str) -> WinterHardinessOverview:
        """Aggregate profiles per traffic-light colour for the dashboard widget.

        Counts each subject once: a per-instance profile (user override) wins over a
        shared-template reference, so a subject that has both is not double-counted.
        """
        profiles, _total = self._repo.list_by_tenant(tenant_key, offset=0, limit=1000)
        counts = {WinterHardinessLight.GREEN: 0, WinterHardinessLight.YELLOW: 0, WinterHardinessLight.RED: 0}
        red_plants: list[WinterHardinessOverviewEntry] = []
        seen_subjects: set[tuple[str | None, str | None]] = set()
        total = 0

        for profile in profiles:
            seen_subjects.add((profile.plant_key, profile.planting_run_key))
            total += 1
            light = _RATING_TO_LIGHT[profile.hardiness_rating]
            counts[light] += 1
            if light == WinterHardinessLight.RED:
                red_plants.append(
                    WinterHardinessOverviewEntry(
                        profile_key=profile.key or "",
                        plant_key=profile.plant_key,
                        planting_run_key=profile.planting_run_key,
                        hardiness_rating=profile.hardiness_rating,
                        winter_action=profile.winter_action,
                    )
                )

        if self._template_repo is not None:
            for plant_key, planting_run_key, template in self._template_repo.list_links_for_tenant(tenant_key):
                if (plant_key, planting_run_key) in seen_subjects:
                    continue  # per-instance profile already counted this subject
                seen_subjects.add((plant_key, planting_run_key))
                total += 1
                light = _RATING_TO_LIGHT[template.hardiness_rating]
                counts[light] += 1
                if light == WinterHardinessLight.RED:
                    red_plants.append(
                        WinterHardinessOverviewEntry(
                            profile_key=template.key or "",
                            plant_key=plant_key,
                            planting_run_key=planting_run_key,
                            hardiness_rating=template.hardiness_rating,
                            winter_action=template.winter_action,
                        )
                    )

        return WinterHardinessOverview(
            green=counts[WinterHardinessLight.GREEN],
            yellow=counts[WinterHardinessLight.YELLOW],
            red=counts[WinterHardinessLight.RED],
            total=total,
            red_plants=red_plants,
        )

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _require_single_subject(profile: OverwinteringProfile) -> None:
        """Exactly one of plant_key / planting_run_key must identify the subject."""
        has_plant = bool(profile.plant_key)
        has_run = bool(profile.planting_run_key)
        if has_plant == has_run:
            raise ValidationError(
                "Exactly one of 'plant_key' or 'planting_run_key' must be set.",
                details=[
                    {
                        "field": "plant_key",
                        "reason": "Provide either plant_key or planting_run_key (not both, not neither).",
                        "code": "INVALID_SUBJECT",
                    }
                ],
            )

    @staticmethod
    def _validate_d5(profile: OverwinteringProfile) -> None:
        """Re-check the D5 invariant using the light implied by the rating."""
        light = _RATING_TO_LIGHT[profile.hardiness_rating]
        validate_d5_invariant(profile, light)

    def _require_no_existing_profile(self, profile: OverwinteringProfile) -> None:
        """Reject a second profile for the same subject with 409 (B4).

        The ``has_overwintering_profile`` edge carries a unique ``_from`` index, so
        a duplicate would otherwise fail at edge insertion and leave the profile
        document orphaned. Guarding here keeps the write atomic.
        """
        existing: OverwinteringProfile | None = None
        if profile.plant_key:
            existing = self._repo.get_profile_by_plant_key(profile.plant_key)
        elif profile.planting_run_key:
            existing = self._repo.get_profile_by_run_key(profile.planting_run_key)
        if existing is not None:
            raise DuplicateError(_ENTITY, "subject", profile.plant_key or profile.planting_run_key or "")

    def _verify_subject_ownership(self, profile: OverwinteringProfile, tenant_key: str) -> None:
        """Reject a subject (plant / planting run) owned by another tenant (B5)."""
        self._verify_subject_keys(
            tenant_key,
            plant_key=profile.plant_key,
            planting_run_key=profile.planting_run_key,
        )

    def _verify_subject_keys(
        self,
        tenant_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> None:
        """Reject a subject (plant / planting run) owned by another tenant (B5)."""
        if plant_key and self._plant_repo is not None:
            plant = self._plant_repo.get_by_key(plant_key)
            if plant is None or plant.tenant_key != tenant_key:
                raise NotFoundError("PlantInstance", plant_key)
        if planting_run_key and self._planting_run_repo is not None:
            run = self._planting_run_repo.get_by_key(planting_run_key)
            if run is None or run.tenant_key != tenant_key:
                raise NotFoundError("PlantingRun", planting_run_key)

    def _verify_winter_quarter_ownership(self, profile: OverwinteringProfile, tenant_key: str) -> None:
        """Reject a winter quarter (location) owned by another tenant (B5)."""
        if profile.winter_quarter_key and self._site_repo is not None:
            location = self._site_repo.get_location_by_key(profile.winter_quarter_key)
            if location is None or location.tenant_key != tenant_key:
                raise NotFoundError("Location", profile.winter_quarter_key)

    def _wire_edges_or_rollback(self, profile: OverwinteringProfile) -> None:
        """Wire the subject / winter-quarter edges, rolling back on failure (B4).

        If the unique subject-edge index rejects the insert (a duplicate that
        slipped past :meth:`_require_no_existing_profile` under a race), the freshly
        created profile document is deleted so no orphan remains, and the caller
        sees a 409 instead of a 500.
        """
        if not profile.key:
            return
        try:
            self._repo.create_subject_edge(
                profile.key,
                plant_key=profile.plant_key,
                planting_run_key=profile.planting_run_key,
            )
            if profile.winter_quarter_key:
                self._repo.create_winter_quarter_edge(profile.key, profile.winter_quarter_key)
        except Exception as exc:
            self._repo.delete_profile(profile.key)
            raise DuplicateError(_ENTITY, "subject", profile.plant_key or profile.planting_run_key or "") from exc

    @staticmethod
    def winter_path_for(profile: OverwinteringProfile) -> str:
        """Expose the derived winter path (A/B) for callers (e.g. reminder wiring)."""
        return derive_winter_path(_RATING_TO_LIGHT[profile.hardiness_rating])
