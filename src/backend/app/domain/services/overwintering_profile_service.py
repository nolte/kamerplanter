"""REQ-022 §OverwinteringProfile service (G-002).

Tenant-scoped CRUD for overwintering profiles, auto-generation from the winter
hardiness traffic light, D5-invariant validation (HTTP 422 on contradiction) and
the dashboard hardiness overview.
"""

from app.common.enums import (
    FrostTolerance,
    HardinessRating,
    WinterAction,
    WinterHardinessLight,
)
from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import OverwinteringProfileKey
from app.domain.engines.winter_hardiness_engine import (
    derive_winter_path,
    evaluate_winter_hardiness,
    validate_d5_invariant,
)
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.models.overwintering_profile import (
    OverwinteringProfile,
    WinterHardinessOverview,
    WinterHardinessOverviewEntry,
)

_ENTITY = "OverwinteringProfile"

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
    def __init__(self, repo: IOverwinteringProfileRepository) -> None:
        self._repo = repo

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
        created = self._repo.create_profile(profile)
        self._wire_edges(created)
        return created

    def update_profile(self, key: OverwinteringProfileKey, tenant_key: str, updates: dict) -> OverwinteringProfile:
        existing = self.get_profile(key, tenant_key)
        data = existing.model_dump()
        data.update(updates)
        # Preserve identity/ownership fields regardless of the payload.
        data["tenant_key"] = tenant_key
        merged = OverwinteringProfile(**data)
        self._require_single_subject(merged)
        self._validate_d5(merged)
        return self._repo.update_profile(key, merged)

    def delete_profile(self, key: OverwinteringProfileKey, tenant_key: str) -> bool:
        self.get_profile(key, tenant_key)
        return self._repo.delete_profile(key)

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
    ) -> OverwinteringProfile:
        """Derive an overwintering profile from the winter hardiness ampel.

        The traffic light (species frost sensitivity + zone gap) determines both
        the ``hardiness_rating`` and the default ``winter_action`` so the result
        satisfies the D5 invariant by construction.
        """
        light = evaluate_winter_hardiness(frost_sensitivity, species_zone, site_zone)
        rating = _LIGHT_TO_RATING[light]
        action = _LIGHT_TO_ACTION[light]

        profile = OverwinteringProfile(
            plant_key=plant_key,
            planting_run_key=planting_run_key,
            hardiness_zone_min=species_zone,
            hardiness_rating=rating,
            winter_action=action,
            winter_action_month=winter_action_month,
            spring_action=None,
            spring_action_month=(spring_action_month if light != WinterHardinessLight.GREEN else None),
            winter_quarter_key=winter_quarter_key,
            auto_generated=True,
            tenant_key=tenant_key,
        )
        self._require_single_subject(profile)
        validate_d5_invariant(profile, light)
        created = self._repo.create_profile(profile)
        self._wire_edges(created)
        return created

    # ── Dashboard overview ──────────────────────────────────────────────

    def get_hardiness_overview(self, tenant_key: str) -> WinterHardinessOverview:
        """Aggregate profiles per traffic-light colour for the dashboard widget."""
        profiles, _total = self._repo.list_by_tenant(tenant_key, offset=0, limit=1000)
        counts = {WinterHardinessLight.GREEN: 0, WinterHardinessLight.YELLOW: 0, WinterHardinessLight.RED: 0}
        red_plants: list[WinterHardinessOverviewEntry] = []

        for profile in profiles:
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

        return WinterHardinessOverview(
            green=counts[WinterHardinessLight.GREEN],
            yellow=counts[WinterHardinessLight.YELLOW],
            red=counts[WinterHardinessLight.RED],
            total=len(profiles),
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

    def _wire_edges(self, profile: OverwinteringProfile) -> None:
        if not profile.key:
            return
        self._repo.create_subject_edge(
            profile.key,
            plant_key=profile.plant_key,
            planting_run_key=profile.planting_run_key,
        )
        if profile.winter_quarter_key:
            self._repo.create_winter_quarter_edge(profile.key, profile.winter_quarter_key)

    @staticmethod
    def winter_path_for(profile: OverwinteringProfile) -> str:
        """Expose the derived winter path (A/B) for callers (e.g. reminder wiring)."""
        return derive_winter_path(_RATING_TO_LIGHT[profile.hardiness_rating])
