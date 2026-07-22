"""REQ-047 §3.6 — orchestration of the per-site season evaluation.

For one site the service runs the cascade → engine → (on a transition) the
side-effects: materialise overwintering profiles, switch the dormancy-care mode
and persist the resulting :class:`SeasonState` (idempotent — the state is also
persisted without a transition to record ``evaluated_at`` and the hysteresis
counter).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

import structlog

from app.common.enums import SeasonPhase
from app.common.exceptions import NotFoundError, SeasonStateUnavailableError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.engines.frost_exposure_resolver import resolve_frost_exposure
from app.domain.engines.season_state_engine import SeasonStateEngine, SeasonStateTransition
from app.domain.models.season_state import SeasonState
from app.domain.services.season_signal_resolver import SeasonSignalResolver, hemisphere_from_site

if TYPE_CHECKING:
    from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
    from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
    from app.domain.interfaces.season_state_repository import ISeasonStateRepository
    from app.domain.interfaces.site_repository import ISiteRepository
    from app.domain.models.plant_instance import PlantInstance
    from app.domain.models.site import Location, Site
    from app.domain.services.care_reminder_service import CareReminderService
    from app.domain.services.dormancy_care_activator import DormancyCareActivator
    from app.domain.services.overwintering_materializer import OverwinteringMaterializer
    from app.domain.services.season_phase_coupler import SeasonPhaseCoupler

logger = structlog.get_logger(__name__)

_ENTITY = "SeasonState"


class SeasonStateService:
    def __init__(
        self,
        repo: ISeasonStateRepository,
        resolver: SeasonSignalResolver,
        engine: SeasonStateEngine,
        materializer: OverwinteringMaterializer,
        dormancy_activator: DormancyCareActivator,
        care_service: CareReminderService,
        overwintering_repo: IOverwinteringProfileRepository,
        plant_repo: IPlantInstanceRepository,
        site_repo: ISiteRepository,
        phase_coupler: SeasonPhaseCoupler | None = None,
    ) -> None:
        self._repo = repo
        self._resolver = resolver
        self._engine = engine
        self._materializer = materializer
        self._dormancy = dormancy_activator
        self._care_service = care_service
        self._overwintering_repo = overwintering_repo
        self._plant_repo = plant_repo
        self._site_repo = site_repo
        # ADR-006 E3 — couples the season transition to the REQ-003 growth phase.
        # Optional so existing callers/tests that build the service without the
        # coupler keep the care-only behaviour (the coupling is then a no-op).
        self._phase_coupler = phase_coupler

    # ── Evaluation ──────────────────────────────────────────────────────

    def evaluate_site(self, site: Site, on_date: date | None = None) -> SeasonState | None:
        """Evaluate and persist the season state of one site (idempotent).

        Returns ``None`` for a non-outdoor/greenhouse site (no season). A second
        run on the same day neither re-transitions nor duplicates side effects.
        """
        state, _changed = self.evaluate_site_detailed(site, on_date)
        return state

    def evaluate_site_detailed(self, site: Site, on_date: date | None = None) -> tuple[SeasonState | None, bool]:
        """Like :meth:`evaluate_site` but also reports whether the phase changed.

        Lets the daily batch task detect (and log) a transition without a second
        ``get_by_site`` read of its own.
        """
        # Site-level gate (Issue #713): the season stays a per-site concept, but a
        # site now qualifies when its *type* is frost-exposed OR it owns ≥1 location
        # with an explicit ``frost_exposed == true`` override — so a frost-exposed
        # corner under an otherwise indoor site still gets a season state. Both gate
        # stances share :meth:`_site_has_frost_exposure` (no second hardcoded site-type
        # set). The per-plant ``Location.frost_exposed`` overrides then narrow the
        # side-effects to the actually-exposed plants (see :meth:`_active_plants`).
        if not self._site_has_frost_exposure(site) or not site.key:
            return None, False
        if on_date is None:
            on_date = datetime.now(UTC).date()

        signal = self._resolver.resolve(site, on_date)
        state = self._repo.get_by_site(site.key, site.tenant_key) or SeasonState(
            season_state_id=f"season-{uuid.uuid4().hex[:12]}",
            site_key=site.key,
            tenant_key=site.tenant_key,
            phase=SeasonPhase.GROWING,
        )

        transition = self._engine.next_phase(state, signal, on_date)
        now = datetime.now(UTC)

        state.trigger_tier = signal.tier
        state.trigger_reason_i18n_key = signal.reason_i18n_key
        state.last_min_temp_c = signal.min_temp_c
        state.forecast_first_frost_date = signal.forecast_first_frost_date
        state.estimated_first_frost_md = signal.estimated_first_frost_md
        state.estimated_last_frost_md = signal.estimated_last_frost_md
        state.consecutive_signal_days = transition.consecutive_signal_days
        state.season_year = transition.season_year
        state.evaluated_at = now

        if transition.changed:
            state.phase = transition.to_phase
            state.entered_phase_at = now
            self._apply_side_effects(site, transition)

        return self._repo.upsert(state), transition.changed

    def _apply_side_effects(self, site: Site, transition: SeasonStateTransition) -> None:
        """Run the per-transition side effects for every active plant of the site.

        REQ-047 §3.2 — the season transition is the *primary* trigger for the
        winter/spring protection reminders: entering ``pre_winter`` materialises the
        overwintering profile and creates the winter_protection / tuber_dig tasks;
        entering ``pre_spring`` clears dormancy-care and creates the spring_uncover
        task. Both go through the idempotent care-reminder task path.
        """
        to_phase = transition.to_phase
        if to_phase == SeasonPhase.PRE_WINTER:
            for plant in self._active_plants(site):
                # Materialise first so the freshly derived profile is available to
                # the winter-reminder gate that follows.
                self._safe(self._materializer.materialize, plant, site, plant_key=plant.key)
                self._safe(
                    self._care_service.ensure_seasonal_winter_tasks, plant.key or "", to_phase, plant_key=plant.key
                )
        elif to_phase == SeasonPhase.WINTER_DORMANCY:
            for plant in self._active_plants(site):
                self._safe(self._enter_dormancy, plant.key, plant_key=plant.key)
                # ADR-006 E3 — also drive the biological growth phase to dormancy for
                # effectively-perennial plants (not just the care mode above).
                if self._phase_coupler is not None:
                    self._safe(self._phase_coupler.enter_dormancy, plant, plant_key=plant.key)
        elif to_phase == SeasonPhase.PRE_SPRING:
            for plant in self._active_plants(site):
                self._safe(self._leave_dormancy, plant.key, plant_key=plant.key)
                # ADR-006 E3 — restart the perennial growth-phase cycle in lockstep
                # with the season's spring reactivation (not two decoupled cycles).
                if self._phase_coupler is not None:
                    self._safe(self._phase_coupler.restart_cycle, plant, plant_key=plant.key)
                self._safe(
                    self._care_service.ensure_seasonal_winter_tasks, plant.key or "", to_phase, plant_key=plant.key
                )
        elif to_phase == SeasonPhase.GROWING:
            for plant in self._active_plants(site):
                self._safe(self._leave_dormancy, plant.key, plant_key=plant.key)

    def _enter_dormancy(self, plant_key: str) -> None:
        persisted = self._overwintering_repo.get_profile_by_plant_key(plant_key)
        # Reuse the persisted per-instance profile when present; only fall back to the
        # shared species-template adapter when there is none (no double read). The
        # public resolver keeps the N:1 template logic encapsulated (C3).
        profile = persisted if persisted is not None else self._care_service.resolve_overwintering_profile(plant_key)
        self._dormancy.activate(plant_key, profile)
        if persisted is not None and persisted.key:
            self._overwintering_repo.update_profile(
                persisted.key, persisted.model_copy(update={"dormancy_care_active": True})
            )

    def _leave_dormancy(self, plant_key: str) -> None:
        self._dormancy.deactivate(plant_key)
        persisted = self._overwintering_repo.get_profile_by_plant_key(plant_key)
        if persisted is not None and persisted.key and persisted.dormancy_care_active:
            self._overwintering_repo.update_profile(
                persisted.key, persisted.model_copy(update={"dormancy_care_active": False})
            )

    def _site_has_frost_exposure(self, site: Site) -> bool:
        """Whether the site qualifies for a season state (Issue #713).

        ``True`` when the site *type* is frost-exposed (legacy behaviour via
        ``resolve_frost_exposure(None, site)``) OR the site owns ≥1 location whose
        ``frost_exposed`` override is explicitly ``True``. A ``False``/``None`` override
        never adds a site: ``None`` is not collapsed to ``False`` here — it simply does
        not contribute, so the site-type fallback is what decides. Shared by both gate
        stances so the "second hardcoded site-type set" never reappears.
        """
        if resolve_frost_exposure(None, site):
            return True
        if not site.key:
            return False
        return any(loc.frost_exposed is True for loc in self._site_repo.get_locations_by_site(site.key))

    def _active_plants(self, site: Site) -> list[PlantInstance]:
        """Active plants of the site that are actually frost-exposed (Issue #713).

        The side effects (dormancy / winter care / season reminders) must only reach a
        plant that is itself exposed to outdoor frost. Because a ``frost_exposed=false``
        location can *exclude* a plant even on an outdoor site — and a
        ``frost_exposed=true`` location can *include* one on an indoor site — the
        exposure is resolved per plant (never assumed from the site alone). ``None`` /
        no location falls through to the site-type classification (bit-for-bit legacy
        behaviour when no override exists anywhere).
        """
        plants = self._plant_repo.find_by_field(
            "site_key",
            site.key,
            extra_filters=[("tenant_key", "==", site.tenant_key)],
        )
        return [
            p
            for p in plants
            if p.removed_on is None and resolve_frost_exposure(self._load_plant_location(p, site), site)
        ]

    def _load_plant_location(self, plant: PlantInstance, site: Site) -> Location | None:
        """Load the plant's location for the frost resolver, tenant/site-safe (#706).

        Returns ``None`` — so the resolver falls back to the site type — when the plant
        carries no ``location_key``/``site_key``, the location is unknown, or it does not
        belong to the plant's own site. Ownership is anchored on the SITE (already
        tenant-verified by the caller), not on ``location.tenant_key`` (persisted empty):
        requiring ``location.site_key == plant.site_key == site.key`` keeps a location
        under a foreign site from ever contributing its ``frost_exposed`` override.
        """
        if not plant.location_key or not plant.site_key or plant.site_key != site.key:
            return None
        location = self._site_repo.get_location_by_key(plant.location_key)
        if location is None or not location.site_key or location.site_key != plant.site_key:
            return None
        return location

    @staticmethod
    def _safe(fn, *args, plant_key: str | None = None) -> None:
        """Run a per-plant side effect, logging (not raising) on failure.

        One malformed plant must not abort the whole site evaluation (AC-18).
        """
        try:
            fn(*args)
        except Exception as exc:  # noqa: BLE001 — resilient per-plant processing
            logger.warning("season_side_effect_failed", plant_key=plant_key, error=str(exc))

    # ── Reads (API) ─────────────────────────────────────────────────────

    def get_state_for_site(self, site_key: str, tenant_key: str) -> SeasonState:
        """Return the site's season state, evaluating it lazily if absent.

        Raises 404 for an unknown site, 409 for a pure indoor site (no season).
        """
        site = self._site_repo.get_site_by_key(site_key)
        if site is None:
            raise NotFoundError("Site", site_key)
        verify_tenant_ownership(site, tenant_key, "Site")
        # Site-level gate (see :meth:`evaluate_site_detailed`): available when the site
        # type is frost-exposed OR the site owns ≥1 frost-exposed location (Issue #713).
        if not self._site_has_frost_exposure(site):
            raise SeasonStateUnavailableError(site_key)

        state = self._repo.get_by_site(site_key, tenant_key)
        if state is None:
            evaluated = self.evaluate_site(site)
            if evaluated is None:
                raise SeasonStateUnavailableError(site_key)
            return evaluated
        return state

    def get_overview(self, tenant_key: str) -> list[SeasonState]:
        """Aggregated season states over all outdoor/greenhouse sites of a tenant."""
        states, _total = self._repo.list_for_tenant(tenant_key)
        return states

    @staticmethod
    def hemisphere_for(site: Site) -> str:
        return hemisphere_from_site(site)
