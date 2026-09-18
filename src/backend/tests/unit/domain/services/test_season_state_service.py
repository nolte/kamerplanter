"""REQ-047 §3.2/§3.6 — SeasonStateService transition side-effect wiring (C2).

The season transition is the primary trigger for the winter/spring reminders:
entering ``pre_winter`` materialises the profile *and* creates the winter tasks;
entering ``pre_spring`` clears dormancy-care *and* creates the spring_uncover task.
"""

from datetime import date
from unittest.mock import MagicMock

from app.common.enums import SeasonPhase, SiteType
from app.domain.engines.season_state_engine import SeasonStateTransition
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location, Site
from app.domain.services.season_state_service import SeasonStateService


def _plant(key: str = "plant-1", *, location_key: str | None = None, site_key: str = "site-1") -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key="tenant-1",
        instance_id="i1",
        species_key="species-1",
        planted_on=date(2024, 1, 1),
        site_key=site_key,
        location_key=location_key,
    )


def _site(key: str = "site-1", site_type: SiteType = SiteType.OUTDOOR) -> Site:
    return Site(key=key, tenant_key="tenant-1", name="Garden", type=site_type)


def _location(key: str = "loc-1", site_key: str = "site-1", frost_exposed: bool | None = None) -> Location:
    return Location(
        _key=key,
        tenant_key="",
        name="Test Location",
        site_key=site_key,
        area_m2=10.0,
        frost_exposed=frost_exposed,
    )


def _transition(to_phase: SeasonPhase) -> SeasonStateTransition:
    return SeasonStateTransition(
        changed=True,
        from_phase=SeasonPhase.GROWING,
        to_phase=to_phase,
        season_year=2026,
        consecutive_signal_days=0,
        reason_i18n_key="pages.season.trigger.frostForecast",
    )


def _service(
    care_service: MagicMock,
    materializer: MagicMock,
    dormancy: MagicMock,
    *,
    plant_repo: MagicMock | None = None,
    site_repo: MagicMock | None = None,
) -> SeasonStateService:
    if plant_repo is None:
        plant_repo = MagicMock()
        plant_repo.find_by_field.return_value = [_plant()]
    if site_repo is None:
        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = []

    overwintering_repo = MagicMock()
    overwintering_repo.get_profile_by_plant_key.return_value = None
    return SeasonStateService(
        MagicMock(),  # repo
        MagicMock(),  # resolver
        MagicMock(),  # engine
        materializer,
        dormancy,
        care_service,
        overwintering_repo,
        plant_repo,
        site_repo,
    )


class TestApplySideEffects:
    def test_pre_winter_materialises_and_creates_winter_tasks(self) -> None:
        care_service = MagicMock()
        materializer = MagicMock()
        service = _service(care_service, materializer, MagicMock())

        service._apply_side_effects(_site(), _transition(SeasonPhase.PRE_WINTER))

        materializer.materialize.assert_called_once()
        care_service.ensure_seasonal_winter_tasks.assert_called_once_with("plant-1", SeasonPhase.PRE_WINTER)

    def test_pre_spring_leaves_dormancy_and_creates_spring_task(self) -> None:
        care_service = MagicMock()
        dormancy = MagicMock()
        service = _service(care_service, MagicMock(), dormancy)

        service._apply_side_effects(_site(), _transition(SeasonPhase.PRE_SPRING))

        dormancy.deactivate.assert_called_once_with("plant-1")
        care_service.ensure_seasonal_winter_tasks.assert_called_once_with("plant-1", SeasonPhase.PRE_SPRING)

    def test_growing_leaves_dormancy_without_winter_tasks(self) -> None:
        care_service = MagicMock()
        dormancy = MagicMock()
        service = _service(care_service, MagicMock(), dormancy)

        service._apply_side_effects(_site(), _transition(SeasonPhase.GROWING))

        dormancy.deactivate.assert_called_once_with("plant-1")
        care_service.ensure_seasonal_winter_tasks.assert_not_called()

    def test_dormancy_reuses_persisted_profile_without_double_read(self) -> None:
        """K4/efficiency — the persisted profile is loaded once and reused; the
        shared-template resolver is only consulted when there is no per-instance
        profile."""
        care_service = MagicMock()
        dormancy = MagicMock()
        service = _service(care_service, MagicMock(), dormancy)
        persisted = MagicMock(key="ow-1", dormancy_care_active=False)
        service._overwintering_repo.get_profile_by_plant_key.return_value = persisted

        service._apply_side_effects(_site(), _transition(SeasonPhase.WINTER_DORMANCY))

        dormancy.activate.assert_called_once()
        # The persisted profile was reused, so the public template resolver was not.
        care_service.resolve_overwintering_profile.assert_not_called()


# ── Issue #713 — Location-aware season state ─────────────────────────────────


class TestSiteHasFrostExposure:
    """Test the site-level frost exposure gate that determines if a site gets a SeasonState.

    AC-5 + AC-None-Parité: a site qualifies when its *type* is frost-exposed
    (outdoor/greenhouse/balcony) OR it owns ≥1 location with an explicit
    ``frost_exposed == true`` override. A ``false`` or ``None`` override never adds
    a site.
    """

    def test_outdoor_site_type_returns_true(self) -> None:
        """Outdoor site type → site qualifies (legacy behaviour)."""
        site = _site(site_type=SiteType.OUTDOOR)
        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = []
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is True

    def test_greenhouse_site_type_returns_true(self) -> None:
        """Greenhouse site type → site qualifies (legacy behaviour)."""
        site = _site(site_type=SiteType.GREENHOUSE)
        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = []
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is True

    def test_balcony_site_type_returns_true(self) -> None:
        """Balcony site type → site qualifies (legacy behaviour)."""
        site = _site(site_type=SiteType.BALCONY)
        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = []
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is True

    def test_indoor_site_type_with_no_locations_returns_false(self) -> None:
        """Indoor site type + no locations → site does not qualify (legacy behaviour)."""
        site = _site(site_type=SiteType.INDOOR)
        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = []
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is False

    def test_windowsill_site_type_with_no_locations_returns_false(self) -> None:
        """Windowsill site type + no locations → site does not qualify."""
        site = _site(site_type=SiteType.WINDOWSILL)
        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = []
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is False

    def test_grow_tent_site_type_with_no_locations_returns_false(self) -> None:
        """Grow tent site type + no locations → site does not qualify."""
        site = _site(site_type=SiteType.GROW_TENT)
        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = []
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is False

    def test_indoor_site_with_frost_exposed_true_location_returns_true(self) -> None:
        """AC-5: Indoor site with ≥1 frost_exposed=true location → site qualifies (new)."""
        site = _site(key="site-1", site_type=SiteType.INDOOR)
        location_with_frost = _location(key="loc-1", site_key="site-1", frost_exposed=True)

        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = [location_with_frost]
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is True

    def test_indoor_site_with_frost_exposed_false_location_returns_false(self) -> None:
        """Indoor site with frost_exposed=false location → site does not qualify."""
        site = _site(key="site-1", site_type=SiteType.INDOOR)
        location_protected = _location(key="loc-1", site_key="site-1", frost_exposed=False)

        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = [location_protected]
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is False

    def test_indoor_site_with_frost_exposed_none_location_returns_false(self) -> None:
        """AC-None-Parité: Indoor site with frost_exposed=None location → site does not qualify."""
        site = _site(key="site-1", site_type=SiteType.INDOOR)
        location_unset = _location(key="loc-1", site_key="site-1", frost_exposed=None)

        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = [location_unset]
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is False

    def test_indoor_site_with_mixed_locations_only_true_matters(self) -> None:
        """Mixed indoor site: only frost_exposed=true location matters."""
        site = _site(key="site-1", site_type=SiteType.INDOOR)
        location_protected = _location(key="loc-1", site_key="site-1", frost_exposed=False)
        location_exposed = _location(key="loc-2", site_key="site-1", frost_exposed=True)

        site_repo = MagicMock()
        site_repo.get_locations_by_site.return_value = [location_protected, location_exposed]
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        assert service._site_has_frost_exposure(site) is True

    def test_site_without_key_still_checks_type(self) -> None:
        """Edge case: site without key still checks type (not locations).

        A site type determines frost exposure even if the site has no key.
        The key is used only for location lookup (optimization), not for type check.
        """
        site = Site(key=None, tenant_key="tenant-1", name="Garden", type=SiteType.OUTDOOR)
        site_repo = MagicMock()

        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        # OUTDOOR type is frost-exposed regardless of key
        assert service._site_has_frost_exposure(site) is True
        # No attempt to look up locations since site.key is None
        site_repo.get_locations_by_site.assert_not_called()

    def test_indoor_site_without_key_returns_false(self) -> None:
        """Indoor site without key → no locations can be fetched, type returns False."""
        site = Site(key=None, tenant_key="tenant-1", name="Garden", type=SiteType.INDOOR)
        site_repo = MagicMock()

        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        # INDOOR type is not frost-exposed, and no locations to check
        assert service._site_has_frost_exposure(site) is False
        site_repo.get_locations_by_site.assert_not_called()


class TestLoadPlantLocation:
    """Test the plant-location loader that validates ownership and site alignment."""

    def test_plant_with_matching_location_returns_location(self) -> None:
        """Plant with location_key on matching site → location is loaded."""
        plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        site = _site(key="site-1")
        location = _location(key="loc-1", site_key="site-1")

        site_repo = MagicMock()
        site_repo.get_location_by_key.return_value = location
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        result = service._load_plant_location(plant, site)

        assert result == location
        site_repo.get_location_by_key.assert_called_once_with("loc-1")

    def test_plant_without_location_key_returns_none(self) -> None:
        """Plant without location_key → returns None (fallback to site type)."""
        plant = _plant(key="p1", location_key=None, site_key="site-1")
        site = _site(key="site-1")

        site_repo = MagicMock()
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        result = service._load_plant_location(plant, site)

        assert result is None
        site_repo.get_location_by_key.assert_not_called()

    def test_plant_without_site_key_returns_none(self) -> None:
        """Plant without site_key → returns None."""
        plant = PlantInstance(
            _key="p1",
            tenant_key="tenant-1",
            instance_id="i1",
            species_key="species-1",
            planted_on=date(2024, 1, 1),
            site_key=None,
            location_key="loc-1",
        )
        site = _site(key="site-1")

        site_repo = MagicMock()
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        result = service._load_plant_location(plant, site)

        assert result is None

    def test_plant_site_key_mismatch_returns_none(self) -> None:
        """Plant's site_key ≠ site.key → returns None (cross-site protection)."""
        plant = _plant(key="p1", location_key="loc-1", site_key="site-2")
        site = _site(key="site-1")

        site_repo = MagicMock()
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        result = service._load_plant_location(plant, site)

        assert result is None
        site_repo.get_location_by_key.assert_not_called()

    def test_location_not_found_returns_none(self) -> None:
        """Location does not exist → returns None."""
        plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        site = _site(key="site-1")

        site_repo = MagicMock()
        site_repo.get_location_by_key.return_value = None
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        result = service._load_plant_location(plant, site)

        assert result is None

    def test_location_site_key_mismatch_returns_none(self) -> None:
        """Location belongs to different site → returns None (cross-site protection)."""
        plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        site = _site(key="site-1")
        location = _location(key="loc-1", site_key="site-2")  # Foreign site!

        site_repo = MagicMock()
        site_repo.get_location_by_key.return_value = location
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        result = service._load_plant_location(plant, site)

        assert result is None

    def test_location_without_site_key_returns_none(self) -> None:
        """Location without site_key → returns None (malformed)."""
        plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        site = _site(key="site-1")
        location = Location(
            _key="loc-1",
            tenant_key="",
            name="Test",
            site_key="",  # Empty site_key!
            area_m2=10.0,
        )

        site_repo = MagicMock()
        site_repo.get_location_by_key.return_value = location
        service = _service(MagicMock(), MagicMock(), MagicMock(), site_repo=site_repo)

        result = service._load_plant_location(plant, site)

        assert result is None


class TestActivePlants:
    """Test the per-plant frost-exposure filtering for side effects (AC-1, AC-2, AC-3)."""

    def test_ac1_frost_exposed_location_on_indoor_site_included(self) -> None:
        """AC-1: Plant on frost_exposed=true location under indoor site → included."""
        plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        site = _site(key="site-1", site_type=SiteType.INDOOR)
        location = _location(key="loc-1", site_key="site-1", frost_exposed=True)

        plant_repo = MagicMock()
        plant_repo.find_by_field.return_value = [plant]

        site_repo = MagicMock()
        site_repo.get_location_by_key.return_value = location

        service = _service(MagicMock(), MagicMock(), MagicMock(), plant_repo=plant_repo, site_repo=site_repo)

        active = service._active_plants(site)

        assert len(active) == 1
        assert active[0].key == "p1"

    def test_ac2_indoor_plant_on_mixed_site_excluded(self) -> None:
        """AC-2: Genuinely indoor plant (frost_exposed=false) on mixed site → excluded."""
        indoor_plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        frost_exposed_plant = _plant(key="p2", location_key="loc-2", site_key="site-1")
        site = _site(key="site-1", site_type=SiteType.INDOOR)

        indoor_location = _location(key="loc-1", site_key="site-1", frost_exposed=False)
        frost_exposed_location = _location(key="loc-2", site_key="site-1", frost_exposed=True)

        plant_repo = MagicMock()
        plant_repo.find_by_field.return_value = [indoor_plant, frost_exposed_plant]

        site_repo = MagicMock()

        def get_location_side_effect(key: str):
            if key == "loc-1":
                return indoor_location
            elif key == "loc-2":
                return frost_exposed_location
            return None

        site_repo.get_location_by_key.side_effect = get_location_side_effect

        service = _service(MagicMock(), MagicMock(), MagicMock(), plant_repo=plant_repo, site_repo=site_repo)

        active = service._active_plants(site)

        assert len(active) == 1
        assert active[0].key == "p2"

    def test_ac3_protected_location_on_outdoor_site_excluded(self) -> None:
        """AC-3: Plant with frost_exposed=false location on outdoor site → excluded."""
        protected_plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        exposed_plant = _plant(key="p2", location_key="loc-2", site_key="site-1")
        site = _site(key="site-1", site_type=SiteType.OUTDOOR)

        protected_location = _location(key="loc-1", site_key="site-1", frost_exposed=False)
        exposed_location = _location(key="loc-2", site_key="site-1", frost_exposed=None)  # Inherits from site

        plant_repo = MagicMock()
        plant_repo.find_by_field.return_value = [protected_plant, exposed_plant]

        site_repo = MagicMock()

        def get_location_side_effect(key: str):
            if key == "loc-1":
                return protected_location
            elif key == "loc-2":
                return exposed_location
            return None

        site_repo.get_location_by_key.side_effect = get_location_side_effect

        service = _service(MagicMock(), MagicMock(), MagicMock(), plant_repo=plant_repo, site_repo=site_repo)

        active = service._active_plants(site)

        assert len(active) == 1
        assert active[0].key == "p2"

    def test_ac_none_parity_no_location_uses_site_type(self) -> None:
        """AC-None-Parité: Plant with no location on outdoor site → included (legacy)."""
        plant = _plant(key="p1", location_key=None, site_key="site-1")
        site = _site(key="site-1", site_type=SiteType.OUTDOOR)

        plant_repo = MagicMock()
        plant_repo.find_by_field.return_value = [plant]

        site_repo = MagicMock()

        service = _service(MagicMock(), MagicMock(), MagicMock(), plant_repo=plant_repo, site_repo=site_repo)

        active = service._active_plants(site)

        assert len(active) == 1
        assert active[0].key == "p1"

    def test_ac_none_parity_none_location_uses_site_type(self) -> None:
        """AC-None-Parité: Plant on frost_exposed=None location on outdoor site → included."""
        plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        site = _site(key="site-1", site_type=SiteType.OUTDOOR)
        location = _location(key="loc-1", site_key="site-1", frost_exposed=None)

        plant_repo = MagicMock()
        plant_repo.find_by_field.return_value = [plant]

        site_repo = MagicMock()
        site_repo.get_location_by_key.return_value = location

        service = _service(MagicMock(), MagicMock(), MagicMock(), plant_repo=plant_repo, site_repo=site_repo)

        active = service._active_plants(site)

        assert len(active) == 1

    def test_removed_plants_are_excluded(self) -> None:
        """Removed plants are never included in side effects."""
        active_plant = _plant(key="p1", location_key="loc-1", site_key="site-1")
        removed_plant = _plant(key="p2", location_key="loc-1", site_key="site-1")
        removed_plant.removed_on = date(2024, 1, 1)

        site = _site(key="site-1", site_type=SiteType.OUTDOOR)
        location = _location(key="loc-1", site_key="site-1", frost_exposed=None)

        plant_repo = MagicMock()
        plant_repo.find_by_field.return_value = [active_plant, removed_plant]

        site_repo = MagicMock()
        site_repo.get_location_by_key.return_value = location

        service = _service(MagicMock(), MagicMock(), MagicMock(), plant_repo=plant_repo, site_repo=site_repo)

        active = service._active_plants(site)

        assert len(active) == 1
        assert active[0].key == "p1"


class TestReadingTheSeasonStateDoesNotPersist:
    """#1461 — ``GET …/sites/{key}/season-state`` no longer evaluates and writes.

    ``get_state_for_site`` used to fall through to ``evaluate_site`` when nothing
    was stored yet. That upserted the computed ``SeasonState`` *and* ran
    ``_apply_side_effects`` — materialising overwintering profiles and creating
    winter/spring care tasks — all while answering a plain ``GET``. Entry 10 of
    the #1443 detector inventory.

    Both halves are asserted here rather than only the upsert: the side effects
    are the expensive part, and a repair that stopped the upsert while leaving the
    task creation in place would be green in a test that only counted documents.
    """

    def _service_for_a_stateless_site(self, care_service: MagicMock, materializer: MagicMock) -> SeasonStateService:
        from app.common.enums import SeasonTriggerTier
        from app.domain.services.season_signal_resolver import SeasonSignal

        repo = MagicMock()
        repo.get_by_site.return_value = None

        site_repo = MagicMock()
        site_repo.get_site_by_key.return_value = _site()
        site_repo.get_locations_by_site.return_value = []

        resolver = MagicMock()
        resolver.resolve.return_value = SeasonSignal(
            tier=SeasonTriggerTier.CALENDAR,
            reason_i18n_key="pages.season.trigger.calendar",
            min_temp_c=None,
            forecast_first_frost_date=None,
            estimated_first_frost_md=None,
            estimated_last_frost_md=None,
        )

        engine = MagicMock()
        engine.next_phase.return_value = _transition(SeasonPhase.PRE_WINTER)

        plant_repo = MagicMock()
        plant_repo.find_by_field.return_value = [_plant()]

        overwintering_repo = MagicMock()
        overwintering_repo.get_profile_by_plant_key.return_value = None

        return SeasonStateService(
            repo,
            resolver,
            engine,
            materializer,
            MagicMock(),
            care_service,
            overwintering_repo,
            plant_repo,
            site_repo,
        )

    def test_the_read_answers_a_computed_state_and_upserts_nothing(self) -> None:
        care_service, materializer = MagicMock(), MagicMock()
        service = self._service_for_a_stateless_site(care_service, materializer)

        state = service.get_state_for_site("site-1", "tenant-1")

        assert state.site_key == "site-1"
        assert state.phase == SeasonPhase.PRE_WINTER
        assert state.key is None, "the answer carries a document key, so something persisted it"
        service._repo.upsert.assert_not_called()

    def test_the_read_fires_no_transition_side_effects(self) -> None:
        care_service, materializer = MagicMock(), MagicMock()
        service = self._service_for_a_stateless_site(care_service, materializer)

        service.get_state_for_site("site-1", "tenant-1")

        materializer.materialize.assert_not_called()
        care_service.ensure_seasonal_winter_tasks.assert_not_called()

    def test_the_scheduled_evaluation_still_persists_and_still_fires_them(self) -> None:
        """The control. Without it the two assertions above are satisfied by a
        service that has simply stopped working — the daily Celery task is the
        caller the write and the side effects belong to, and it must be unchanged.
        """
        care_service, materializer = MagicMock(), MagicMock()
        service = self._service_for_a_stateless_site(care_service, materializer)

        state, changed = service.evaluate_site_detailed(_site())

        assert changed is True
        service._repo.upsert.assert_called_once()
        assert state is service._repo.upsert.return_value
        materializer.materialize.assert_called_once()
        care_service.ensure_seasonal_winter_tasks.assert_called_once_with("plant-1", SeasonPhase.PRE_WINTER)


class TestTheOverviewAgreesWithTheDetailRead:
    """Review SCR-003 — one source for a site with no stored state yet.

    #1461 made ``get_state_for_site`` compute transiently instead of evaluating
    and upserting. ``get_overview`` kept reading only ``list_for_tenant``, so the
    two reads disagreed for exactly the site the change was about: a freshly
    created outdoor site showed a phase on its detail page and was **absent** from
    the dashboard widget until the nightly task had written a row.

    Both halves are asserted, because "the overview contains it" is also satisfied
    by an overview that invents states for sites that have none.
    """

    def _service(self, *, stored: list, sites: list) -> SeasonStateService:
        from app.common.enums import SeasonTriggerTier
        from app.domain.services.season_signal_resolver import SeasonSignal

        repo = MagicMock()
        repo.list_for_tenant.return_value = (stored, len(stored))

        site_repo = MagicMock()
        site_repo.get_all_sites.return_value = (sites, len(sites))
        site_repo.get_locations_by_site.return_value = []

        resolver = MagicMock()
        resolver.resolve.return_value = SeasonSignal(
            tier=SeasonTriggerTier.CALENDAR,
            reason_i18n_key="pages.season.trigger.calendar",
            min_temp_c=None,
            forecast_first_frost_date=None,
            estimated_first_frost_md=None,
            estimated_last_frost_md=None,
        )

        engine = MagicMock()
        engine.next_phase.return_value = _transition(SeasonPhase.PRE_WINTER)

        return SeasonStateService(
            repo,
            resolver,
            engine,
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            site_repo,
        )

    def test_a_site_without_a_stored_state_appears_in_the_overview(self) -> None:
        service = self._service(stored=[], sites=[_site("site-new")])

        overview = service.get_overview("tenant-1")

        assert [state.site_key for state in overview] == ["site-new"]
        assert overview[0].phase == SeasonPhase.PRE_WINTER
        assert overview[0].key is None, "the overview persisted a state"
        service._repo.upsert.assert_not_called()

    def test_an_indoor_site_still_contributes_nothing(self) -> None:
        """The control: the overview does not invent a season for every site."""
        service = self._service(stored=[], sites=[_site("site-indoor", SiteType.INDOOR)])

        assert service.get_overview("tenant-1") == []

    def test_a_stored_state_is_answered_from_storage(self) -> None:
        """The stored row keeps its key, so the two sources stay distinguishable."""
        from app.domain.models.season_state import SeasonState

        stored = SeasonState(
            _key="ss-1",
            season_state_id="season-abc",
            site_key="site-1",
            tenant_key="tenant-1",
            phase=SeasonPhase.GROWING,
        )
        service = self._service(stored=[stored], sites=[_site("site-1")])

        overview = service.get_overview("tenant-1")

        assert [state.key for state in overview] == ["ss-1"]

    def test_a_stored_state_beyond_the_site_page_is_not_dropped(self) -> None:
        """Shortening the answer would be a regression dressed as a refinement."""
        from app.domain.models.season_state import SeasonState

        orphan = SeasonState(
            _key="ss-9",
            season_state_id="season-xyz",
            site_key="site-not-listed",
            tenant_key="tenant-1",
            phase=SeasonPhase.WINTER_DORMANCY,
        )
        service = self._service(stored=[orphan], sites=[])

        assert [state.key for state in service.get_overview("tenant-1")] == ["ss-9"]

    def test_the_detail_read_and_the_overview_answer_the_same_phase(self) -> None:
        """The property SCR-003 is about, asserted as the equality it really is."""
        site = _site("site-new")
        service = self._service(stored=[], sites=[site])
        service._repo.get_by_site.return_value = None
        service._site_repo.get_site_by_key.return_value = site

        detail = service.get_state_for_site("site-new", "tenant-1")
        overview = service.get_overview("tenant-1")

        assert detail.phase == overview[0].phase
        assert detail.site_key == overview[0].site_key
