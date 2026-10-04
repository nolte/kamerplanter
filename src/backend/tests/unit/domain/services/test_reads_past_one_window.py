"""#2025 — request-path reads see every row, not one fixed window of the collection.

Each read here used to call a list method once with a literal window
(``get_all_indicators(0, 1000)``, ``list_by_tenant(..., offset=0, limit=1000)``,
``get_all_sites(0, 200)``, ``list_for_tenant(tenant_key)`` with its default 200,
``get_all_sequences(0, _SEQUENCE_PAGE)``, ``list_plants(offset=0, limit=10000)``)
and treated the page as the collection. Every double below pages **like the real
repository** — it honours ``offset``/``limit`` and reports the whole ``total`` — and
holds more rows than the old window, so the old code reads short against it.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common.enums import (
    CycleType,
    GrowthHabit,
    HardinessRating,
    HarvestIndicatorType,
    SeasonPhase,
    SiteType,
    WinterAction,
)
from app.domain.engines.season_state_engine import SeasonStateTransition
from app.domain.models.harvest import HarvestIndicator, HarvestObservation
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.phase_sequence import PhaseSequence
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.season_state import SeasonState
from app.domain.models.site import Location, Site
from app.domain.models.species import Species
from app.domain.services.harvest_service import HarvestService
from app.domain.services.overwintering_profile_service import OverwinteringProfileService
from app.domain.services.phase_sequence_binder import PhaseSequenceBinder
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.season_state_service import SeasonStateService

TENANT = "tenant-1"


def _paged(rows: list):
    """A ``(offset, limit) -> (page, total)`` read over ``rows``, as the repositories page."""

    def read(offset: int = 0, limit: int = 50, *_args, **_kwargs):
        return rows[offset : offset + limit], len(rows)

    return read


class TestHarvestReadinessReadsEveryIndicator:
    """``assess_readiness`` re-read one page of 1000 indicators per observed key."""

    def _service(self, indicators: list[HarvestIndicator], observed_key: str):
        repo = MagicMock()
        repo.get_latest_observations_by_indicator.return_value = [
            HarvestObservation(plant_key="p1", indicator_key=observed_key)
        ]
        repo.get_all_indicators.side_effect = _paged(indicators)
        readiness = MagicMock()
        readiness.assess_readiness.return_value = {"overall_score": 1}
        service = HarvestService(repo=repo, ipm_service=MagicMock(), readiness_engine=readiness, quality_engine=None)
        return service, repo, readiness

    def test_an_indicator_past_the_first_thousand_supplies_its_reliability(self) -> None:
        indicators = [
            HarvestIndicator(_key=f"ind-{i:05d}", indicator_type=HarvestIndicatorType.COLOR, reliability_score=0.5)
            for i in range(1500)
        ]
        indicators[1200] = indicators[1200].model_copy(update={"reliability_score": 0.9})
        service, repo, readiness = self._service(indicators, "ind-01200")

        service.assess_readiness("p1", tenant_key=TENANT)

        reliabilities = readiness.assess_readiness.call_args.args[1]
        assert reliabilities == {"ind-01200": 0.9}
        assert repo.get_all_indicators.call_count == 2, "two pages, read once — not one page per observed key"


class TestHardinessOverviewCountsEveryProfile:
    def test_more_than_a_thousand_profiles_are_all_counted(self) -> None:
        profiles = [
            OverwinteringProfile(
                _key=f"ow{i:05d}",
                tenant_key=TENANT,
                plant_key=f"p{i}",
                hardiness_rating=HardinessRating.HARDY,
                winter_action=WinterAction.NONE,
                winter_action_month=10,
            )
            for i in range(1250)
        ]
        repo = MagicMock()
        repo.list_by_tenant.side_effect = lambda tenant_key, offset=0, limit=50: _paged(profiles)(offset, limit)

        overview = OverwinteringProfileService(repo).get_hardiness_overview(TENANT)

        assert (overview.total, overview.green) == (1250, 1250)


class TestSeasonOverviewReadsEverySiteAndState:
    def _service(self, *, sites: list[Site], stored: list[SeasonState]) -> SeasonStateService:
        from app.common.enums import SeasonTriggerTier
        from app.domain.services.season_signal_resolver import SeasonSignal

        repo = MagicMock()
        repo.list_for_tenant.side_effect = lambda tenant_key, offset=0, limit=200: _paged(stored)(offset, limit)
        site_repo = MagicMock()
        site_repo.get_all_sites.side_effect = lambda offset=0, limit=50, *, tenant_key: _paged(sites)(offset, limit)
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
        engine.next_phase.return_value = SeasonStateTransition(
            changed=True,
            from_phase=SeasonPhase.GROWING,
            to_phase=SeasonPhase.PRE_WINTER,
            season_year=2026,
            consecutive_signal_days=0,
            reason_i18n_key="pages.season.trigger.calendar",
        )
        return SeasonStateService(
            repo, resolver, engine, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), site_repo
        )

    def test_a_frost_exposed_site_past_the_first_two_hundred_is_in_the_overview(self) -> None:
        sites = [Site(key=f"site-{i:04d}", tenant_key=TENANT, name=f"S{i}", type=SiteType.OUTDOOR) for i in range(250)]

        overview = self._service(sites=sites, stored=[]).get_overview(TENANT)

        assert len(overview) == 250
        assert "site-0249" in {state.site_key for state in overview}

    def test_a_stored_state_past_the_default_page_of_two_hundred_is_in_the_overview(self) -> None:
        stored = [
            SeasonState(
                _key=f"ss-{i:04d}",
                season_state_id=f"season-{i}",
                site_key=f"gone-{i:04d}",
                tenant_key=TENANT,
                phase=SeasonPhase.GROWING,
            )
            for i in range(250)
        ]

        overview = self._service(sites=[], stored=stored).get_overview(TENANT)

        assert len(overview) == 250


class TestBinderSeesEverySequence:
    def test_a_target_sequence_past_the_first_five_hundred_is_bound(self) -> None:
        catalogue = [PhaseSequence(_key="seq-indoor", name="indoor_default")]
        catalogue += [PhaseSequence(_key=f"seq-f{i:04d}", name=f"filler_{i:04d}") for i in range(550)]
        catalogue.append(PhaseSequence(_key="seq-evergreen", name="evergreen_foliage_perennial"))
        seq_repo = MagicMock()
        seq_repo.get_sequence_by_species.return_value = None
        seq_repo.get_all_sequences.side_effect = _paged(catalogue)
        phase_repo = MagicMock()
        phase_repo.get_lifecycle_by_species.return_value = LifecycleConfig(
            species_key="sp-1", cycle_type=CycleType.PERENNIAL
        )
        species = Species(_key="sp-1", scientific_name="Dracaena reflexa", growth_habit=GrowthHabit.SHRUB)

        bound = PhaseSequenceBinder(seq_repo, phase_repo).bind_default(species)

        assert bound == "evergreen_foliage_perennial"
        seq_repo.set_species_sequence.assert_called_once_with("sp-1", "seq-evergreen")


class TestPlantsPerLocationCountsEveryPlant:
    """``GET /t/{slug}/sites/{key}/tree`` counted plants from one window of 10000."""

    def test_the_location_tree_counts_a_plant_past_the_first_ten_thousand(self) -> None:
        from app.api.v1.sites.tenant_router import get_location_tree

        plants = [
            PlantInstance(
                _key=f"pl{i:06d}",
                tenant_key=TENANT,
                instance_id=f"P{i}",
                species_key="sp",
                planted_on=date(2026, 1, 1),
                location_key="loc-a" if i < 10_000 else "loc-b",
            )
            for i in range(10_050)
        ]
        plant_repo = MagicMock()
        plant_repo.get_all.side_effect = lambda offset=0, limit=50, tenant_key=None, **_: _paged(plants)(offset, limit)
        plant_service = PlantInstanceService(plant_repo, MagicMock(), MagicMock(), MagicMock())
        site_service = MagicMock()
        site_service.get_location_tree.return_value = [
            Location(_key="loc-a", tenant_key="", name="A", site_key="site-1", area_m2=1.0),
            Location(_key="loc-b", tenant_key="", name="B", site_key="site-1", area_m2=1.0),
        ]
        site_service.list_slots.return_value = []

        tree = get_location_tree(
            "site-1",
            ctx=SimpleNamespace(tenant_key=TENANT),
            service=site_service,
            plant_service=plant_service,
            tank_service=MagicMock(),
        )

        counts = {node.key: node.active_plant_count for node in tree}
        assert counts == {"loc-a": 10_000, "loc-b": 50}
