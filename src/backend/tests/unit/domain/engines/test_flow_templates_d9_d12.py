"""Per-template flow-vocab / role / regime tests for REQ-003 D9-D12.

Closes the last acceptance-criteria gap of the Lifecycle-Vollständigkeits-Audit:
a focused unit test *per archetype flow template*. These assert the behaviour that
each template's canonical phase vocabulary (spec/req/REQ-003 §D9-D12 + the D8
mapping table) resolves to the expected engine role, drives the expected resource
regime, and — for the D10 mother — is treated as terminal after flowering.

Only genuine gaps are covered here; the generic vocab/role assertions already made
by ``test_phase_role_map`` / ``test_phase_resource_resolver`` /
``test_cyclic_lifecycle_engine`` are not duplicated.
"""

from app.common.enums import CycleType, FloweringStrategy
from app.domain.engines.cyclic_lifecycle_engine import CyclicLifecycleEngine
from app.domain.engines.phase_resource_resolver import resolve_irrigation, resolve_nutrient
from app.domain.engines.phase_role_map import core_phase, is_productive_phase, is_rest_phase
from app.domain.models.lifecycle import LifecycleConfig


class TestD9CamDoubleRest:
    """D9 — CAM/succulent (double-)rest template.

    ``winter_rest`` / ``summer_rest`` / ``cool_rest`` / ``winter_hull_change`` are
    biologically distinct from perennial ``dormancy`` but share its engine role:
    a no-feed, minimal-water rest.
    """

    def test_all_canonical_rest_phases_map_to_dormancy(self) -> None:
        for name in ("winter_rest", "summer_rest", "cool_rest", "winter_hull_change"):
            assert core_phase(name) == "dormancy"
            assert is_rest_phase(name) is True
            assert is_productive_phase(name) is False

    def test_double_rest_covers_both_seasons(self) -> None:
        # a CAM plant may rest in winter AND summer — both are dormancy-role rests.
        assert is_rest_phase("winter_rest") is True
        assert is_rest_phase("summer_rest") is True

    def test_summer_rest_regime_is_minimal_water_no_feed(self) -> None:
        irr = resolve_irrigation("summer_rest", base_frequency_days=3, base_volume_ml=300)
        assert irr.water_only is True
        assert irr.frequency_days > 3
        assert irr.volume_ml_per_plant < 300
        assert resolve_nutrient("summer_rest").feed is False

    def test_winter_hull_change_regime_is_no_feed(self) -> None:
        # Lithops renew their leaf pair while resting — still a no-feed rest.
        assert resolve_nutrient("winter_hull_change").feed is False


class TestD10PupMonocarpy:
    """D10 — pup-based monocarpy (Agave, Bromelie).

    Years vegetative → one terminal bloom → the mother rosette dies; continuation is
    via clonal pups (new instances, ``descended_from`` — DEFERRED to REQ-017 and NOT
    tested here). Only the phase roles and the terminal-after-flowering decision that
    already exist in the engine are asserted.
    """

    def setup_method(self) -> None:
        self.engine = CyclicLifecycleEngine()

    def _mother(self, **kw) -> LifecycleConfig:
        return LifecycleConfig(
            cycle_type=CycleType.PERENNIAL,
            flowering_strategy=FloweringStrategy.MONOCARPIC,
            **kw,
        )

    def test_template_phases_map_to_expected_roles(self) -> None:
        assert core_phase("pup_establishment") == "seedling"  # pup entry (new instance)
        assert core_phase("juvenile") == "vegetative"  # long vegetative phase
        assert core_phase("mature") == "vegetative"  # bloom-ready, still vegetative role
        assert core_phase("flowering") == "flowering"  # single terminal bloom
        assert core_phase("senescence") == "senescence"  # mother dies

    def test_mother_is_monocarpic(self) -> None:
        assert self.engine.is_monocarpic(self._mother()) is True
        # the mother has no season bound — termination is the single bloom, not max_seasons.
        assert self.engine.effective_max_seasons(self._mother()) is None

    def test_mother_terminates_after_flowering_no_cycle_restart(self) -> None:
        restart, reason = self.engine.should_restart_cycle(
            self._mother(), current_season_number=12, current_phase_name="flowering"
        )
        assert restart is False
        assert "monocarp" in reason.lower()

    def test_polycarpic_perennial_would_restart_by_contrast(self) -> None:
        # a polycarpic perennial with the SAME phase restarts — isolating the
        # monocarpic decision as the reason the D10 mother is terminal.
        polycarpic = LifecycleConfig(cycle_type=CycleType.PERENNIAL, flowering_strategy=FloweringStrategy.POLYCARPIC)
        restart, _ = self.engine.should_restart_cycle(
            polycarpic, current_season_number=12, current_phase_name="flowering"
        )
        assert restart is True


class TestD11PhotoperiodicOrnamental:
    """D11 — photoperiodic ornamental induction (Weihnachtsstern, Kalanchoe).

    active_growth → short_day_induction → bract_coloring → rest_after_bloom ↻.
    The induction/coloring phases carry the flowering role (the ornamental "bloom");
    the post-bloom phase is a dormancy-role rest.
    """

    def test_induction_and_coloring_map_to_flowering(self) -> None:
        for name in ("short_day_induction", "bract_coloring"):
            assert core_phase(name) == "flowering"
            assert is_productive_phase(name) is True
            assert is_rest_phase(name) is False

    def test_rest_after_bloom_is_a_dormancy_rest(self) -> None:
        assert core_phase("rest_after_bloom") == "dormancy"
        assert is_rest_phase("rest_after_bloom") is True

    def test_induction_phases_feed_but_post_bloom_rest_does_not(self) -> None:
        assert resolve_nutrient("short_day_induction").feed is True
        assert resolve_nutrient("bract_coloring").feed is True
        assert resolve_nutrient("rest_after_bloom").feed is False


class TestD12PalmFernGeophyte:
    """D12 — palm, fern & fine-grained geophyte templates."""

    def test_palm_phases_are_vegetative_no_bloom(self) -> None:
        # establishment/young_palm → shaft_growth → active_growth; no flowering/senescence.
        assert core_phase("establishment") == "seedling"
        assert core_phase("young_palm") == "vegetative"
        assert core_phase("shaft_growth") == "vegetative"
        for name in ("young_palm", "shaft_growth"):
            assert is_rest_phase(name) is False
            assert is_productive_phase(name) is False

    def test_fern_leaf_and_rest_phases(self) -> None:
        assert core_phase("leaf_phase") == "active_growth"
        assert is_rest_phase("leaf_phase") is False
        for name in ("rest_phase", "rest"):
            assert core_phase(name) == "dormancy"
            assert is_rest_phase(name) is True

    def test_fern_rest_phase_regime_is_no_feed_minimal_water(self) -> None:
        irr = resolve_irrigation("rest_phase", base_frequency_days=3, base_volume_ml=300)
        assert irr.water_only is True
        assert irr.frequency_days > 3
        assert resolve_nutrient("rest_phase").feed is False

    def test_geophyte_fine_phases_map_to_expected_roles(self) -> None:
        assert core_phase("tuber_formation") == "fruit_development"  # storage-organ build-up
        assert is_productive_phase("tuber_formation") is True
        assert core_phase("corm_ripening") == "senescence"  # storage-organ ripening
        assert is_productive_phase("corm_ripening") is False
        assert core_phase("bulbil_establishment") == "seedling"  # bulbil entry (own instance)
        assert core_phase("dry_storage") == "dormancy"

    def test_geophyte_dry_storage_regime_is_dry(self) -> None:
        # dry_storage (= D7 storage) is honoured as a dry, no-feed regime.
        irr = resolve_irrigation("dry_storage")
        assert irr.volume_ml_per_plant == 0.0
        assert irr.water_only is True
        assert resolve_nutrient("dry_storage").feed is False
