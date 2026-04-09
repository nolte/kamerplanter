"""Tests for PhaseSequence fallback in services and engines (Phase 2 migration).

Verifies that services prefer PhaseSequence over LifecycleConfig and fall
back gracefully when no PhaseSequence is found.
"""

from unittest.mock import MagicMock

from app.common.enums import CycleType, StressTolerance
from app.domain.engines.dormancy_trigger import DormancyTrigger
from app.domain.engines.phase_transition_engine import PhaseTransitionEngine
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)
from app.domain.models.species import Species
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.phase_service import PhaseService
from app.domain.services.plant_instance_service import PlantInstanceService

# ── Helpers ────────────────────────────────────────────────────────────


def _make_phase_definition(
    key: str = "pd-1",
    name: str = "vegetative",
    typical_duration_days: int = 30,
    watering_interval_days: int | None = 3,
    stress_tolerance: StressTolerance = StressTolerance.MEDIUM,
) -> PhaseDefinition:
    return PhaseDefinition(
        _key=key,
        name=name,
        display_name=name.capitalize(),
        typical_duration_days=typical_duration_days,
        watering_interval_days=watering_interval_days,
        stress_tolerance=stress_tolerance,
    )


def _make_phase_sequence(
    key: str = "seq-1",
    species_key: str = "sp-1",
    cycle_type: CycleType = CycleType.ANNUAL,
    dormancy_required: bool = False,
    cycle_restart_entry_order: int | None = None,
) -> PhaseSequence:
    return PhaseSequence(
        _key=key,
        name="Test Sequence",
        species_key=species_key,
        cycle_type=cycle_type,
        dormancy_required=dormancy_required,
        cycle_restart_entry_order=cycle_restart_entry_order,
    )


def _make_sequence_entry(
    key: str = "entry-1",
    phase_definition_key: str = "pd-1",
    sequence_order: int = 0,
    phase_sequence_key: str = "seq-1",
    is_terminal: bool = False,
    allows_harvest: bool = False,
    override_duration_days: int | None = None,
) -> PhaseSequenceEntry:
    return PhaseSequenceEntry(
        _key=key,
        phase_definition_key=phase_definition_key,
        sequence_order=sequence_order,
        phase_sequence_key=phase_sequence_key,
        is_terminal=is_terminal,
        allows_harvest=allows_harvest,
        override_duration_days=override_duration_days,
    )


def _make_growth_phase(
    key: str = "gp-1",
    name: str = "seedling",
    sequence_order: int = 0,
    lifecycle_key: str = "lc-1",
    watering_interval_days: int | None = None,
) -> GrowthPhase:
    return GrowthPhase(
        _key=key,
        name=name,
        sequence_order=sequence_order,
        lifecycle_key=lifecycle_key,
        typical_duration_days=14,
        watering_interval_days=watering_interval_days,
    )


def _make_lifecycle(
    key: str = "lc-1",
    species_key: str = "sp-1",
    cycle_type: CycleType = CycleType.ANNUAL,
    dormancy_required: bool = False,
) -> LifecycleConfig:
    return LifecycleConfig(
        _key=key,
        species_key=species_key,
        cycle_type=cycle_type,
        dormancy_required=dormancy_required,
    )


# ── PhaseService._resolve_phases_for_species ──────────────────────────


class TestPhaseServiceResolvePhasesForSpecies:
    """Test PhaseService._resolve_phases_for_species dual-path resolution."""

    def setup_method(self):
        self.phase_repo = MagicMock()
        self.plant_repo = MagicMock()
        self.phase_seq_repo = MagicMock()

    def test_prefers_phase_sequence_when_available(self):
        """Should return PhaseSequence data when a sequence exists for the species."""
        seq = _make_phase_sequence(species_key="sp-1")
        entry = _make_sequence_entry(key="entry-1", sequence_order=0)
        defn = _make_phase_definition(key="pd-1", name="germination")

        self.phase_seq_repo.get_sequence_by_species.return_value = seq
        self.phase_seq_repo.get_entries_for_sequence.return_value = [entry]
        self.phase_seq_repo.get_definition_by_key.return_value = defn

        service = PhaseService(self.phase_repo, self.plant_repo, phase_seq_repo=self.phase_seq_repo)
        phases, cycle_type, meta = service._resolve_phases_for_species("sp-1")

        assert len(phases) == 1
        assert phases[0]["name"] == "germination"
        assert cycle_type == "annual"
        assert meta["source"] == "phase_sequence"
        # LifecycleConfig should NOT be queried
        self.phase_repo.get_lifecycle_by_species.assert_not_called()

    def test_falls_back_to_lifecycle_config(self):
        """Should use LifecycleConfig when no PhaseSequence is found."""
        self.phase_seq_repo.get_sequence_by_species.return_value = None
        lc = _make_lifecycle(key="lc-1", species_key="sp-1")
        gp = _make_growth_phase(key="gp-1", name="seedling", lifecycle_key="lc-1")

        self.phase_repo.get_lifecycle_by_species.return_value = lc
        self.phase_repo.get_phases_by_lifecycle.return_value = [gp]

        service = PhaseService(self.phase_repo, self.plant_repo, phase_seq_repo=self.phase_seq_repo)
        phases, cycle_type, meta = service._resolve_phases_for_species("sp-1")

        assert len(phases) == 1
        assert phases[0]["name"] == "seedling"
        assert meta["source"] == "lifecycle_config"

    def test_no_phase_seq_repo_uses_lifecycle(self):
        """When phase_seq_repo is None, should use LifecycleConfig directly."""
        lc = _make_lifecycle()
        gp = _make_growth_phase()
        self.phase_repo.get_lifecycle_by_species.return_value = lc
        self.phase_repo.get_phases_by_lifecycle.return_value = [gp]

        service = PhaseService(self.phase_repo, self.plant_repo, phase_seq_repo=None)
        phases, cycle_type, meta = service._resolve_phases_for_species("sp-1")

        assert len(phases) == 1
        assert meta.get("source") == "lifecycle_config"

    def test_empty_when_no_config_found(self):
        """Should return empty list when neither PhaseSequence nor LifecycleConfig exists."""
        self.phase_seq_repo.get_sequence_by_species.return_value = None
        self.phase_repo.get_lifecycle_by_species.return_value = None

        service = PhaseService(self.phase_repo, self.plant_repo, phase_seq_repo=self.phase_seq_repo)
        phases, cycle_type, meta = service._resolve_phases_for_species("sp-1")

        assert phases == []
        assert cycle_type == "annual"


# ── DormancyTrigger with PhaseSequence ─────────────────────────────────


class TestDormancyTriggerWithPhaseSequence:
    """Test DormancyTrigger prefers PhaseSequence for dormancy config."""

    def setup_method(self):
        self.phase_repo = MagicMock()
        self.species_repo = MagicMock()
        self.phase_seq_repo = MagicMock()
        self.trigger = DormancyTrigger(self.phase_repo, self.species_repo, phase_seq_repo=self.phase_seq_repo)

    def test_uses_phase_sequence_dormancy_config(self):
        """Should use PhaseSequence for dormancy_required and critical_day_length."""
        seq = _make_phase_sequence(dormancy_required=True)
        seq.critical_day_length_hours = 10.0
        self.phase_seq_repo.get_sequence_by_species.return_value = seq
        species = Species(scientific_name="Testus plantus", genus="Testus", base_temp=5.0, _key="sp-1")
        self.species_repo.get_by_key.return_value = species

        result = self.trigger.should_trigger_dormancy("sp-1", 2.0, 8.0)
        assert result is True
        # LifecycleConfig should NOT be queried
        self.phase_repo.get_lifecycle_by_species.assert_not_called()

    def test_falls_back_to_lifecycle_for_dormancy(self):
        """When no PhaseSequence exists, should fall back to LifecycleConfig."""
        self.phase_seq_repo.get_sequence_by_species.return_value = None
        lc = MagicMock()
        lc.dormancy_required = True
        lc.critical_day_length_hours = 10.0
        self.phase_repo.get_lifecycle_by_species.return_value = lc
        species = Species(scientific_name="Testus plantus", genus="Testus", base_temp=5.0, _key="sp-1")
        self.species_repo.get_by_key.return_value = species

        result = self.trigger.should_trigger_dormancy("sp-1", 2.0, 8.0)
        assert result is True

    def test_get_dormancy_phase_key_from_sequence(self):
        """Should resolve dormancy phase key from PhaseSequence entries."""
        seq = _make_phase_sequence()
        dormancy_defn = _make_phase_definition(key="pd-dormancy", name="dormancy")
        dormancy_entry = _make_sequence_entry(
            key="entry-dormancy",
            phase_definition_key="pd-dormancy",
            sequence_order=3,
        )
        other_defn = _make_phase_definition(key="pd-veg", name="vegetative")
        other_entry = _make_sequence_entry(
            key="entry-veg",
            phase_definition_key="pd-veg",
            sequence_order=1,
        )

        self.phase_seq_repo.get_sequence_by_species.return_value = seq
        self.phase_seq_repo.get_entries_for_sequence.return_value = [other_entry, dormancy_entry]

        def get_defn(key):
            return {"pd-dormancy": dormancy_defn, "pd-veg": other_defn}.get(key)

        self.phase_seq_repo.get_definition_by_key.side_effect = get_defn

        result = self.trigger.get_dormancy_phase_key("sp-1")
        assert result == "entry-dormancy"

    def test_get_dormancy_phase_key_fallback_lifecycle(self):
        """Should fall back to LifecycleConfig when no PhaseSequence exists."""
        self.phase_seq_repo.get_sequence_by_species.return_value = None

        lc = MagicMock()
        lc.key = "lc-1"
        self.phase_repo.get_lifecycle_by_species.return_value = lc
        dormancy_gp = _make_growth_phase(key="gp-dormancy", name="dormancy")
        self.phase_repo.get_phases_by_lifecycle.return_value = [dormancy_gp]

        result = self.trigger.get_dormancy_phase_key("sp-1")
        assert result == "gp-dormancy"


# ── PhaseTransitionEngine with PhaseSequence ──────────────────────────


class TestPhaseTransitionEngineWithPhaseSequence:
    """Test PhaseTransitionEngine uses PhaseSequence for cycle restart checks."""

    def setup_method(self):
        self.phase_repo = MagicMock()
        self.plant_repo = MagicMock()
        self.phase_seq_repo = MagicMock()
        self.engine = PhaseTransitionEngine(self.phase_repo, self.plant_repo, phase_seq_repo=self.phase_seq_repo)

    def test_perennial_restart_from_phase_sequence(self):
        """Should use PhaseSequence cycle_restart_entry_order for perennial restart check."""
        current_phase = _make_growth_phase(key="gp-terminal", name="harvest", sequence_order=3, lifecycle_key="lc-1")
        current_phase.is_terminal = True

        lc = _make_lifecycle(key="lc-1", species_key="sp-1", cycle_type=CycleType.PERENNIAL)

        seq = _make_phase_sequence(
            key="seq-1",
            species_key="sp-1",
            cycle_type=CycleType.PERENNIAL,
            cycle_restart_entry_order=1,
        )

        self.phase_repo.get_phase_by_key.return_value = current_phase
        self.phase_repo.get_lifecycle_by_key.return_value = lc
        self.phase_seq_repo.get_sequence_by_species.return_value = seq

        result = self.engine._is_perennial_cycle_restart("gp-terminal", 1)
        assert result is True

    def test_perennial_restart_fallback_lifecycle(self):
        """When no PhaseSequence, should fall back to LifecycleConfig."""
        current_phase = _make_growth_phase(key="gp-terminal", name="harvest", sequence_order=3, lifecycle_key="lc-1")
        current_phase.is_terminal = True

        lc = _make_lifecycle(key="lc-1", species_key="sp-1", cycle_type=CycleType.PERENNIAL)
        lc.cycle_restart_phase_order = 1

        self.phase_repo.get_phase_by_key.return_value = current_phase
        self.phase_repo.get_lifecycle_by_key.return_value = lc
        self.phase_seq_repo.get_sequence_by_species.return_value = None

        result = self.engine._is_perennial_cycle_restart("gp-terminal", 1)
        assert result is True


# ── PlantInstanceService initial phase from PhaseSequence ──────────────


class TestPlantInstanceServicePhaseSequenceFallback:
    """Test PlantInstanceService resolves initial phase from PhaseSequence."""

    def setup_method(self):
        self.plant_repo = MagicMock()
        self.site_repo = MagicMock()
        self.rotation = MagicMock()
        self.companion = MagicMock()
        self.phase_repo = MagicMock()
        self.phase_seq_repo = MagicMock()

    def test_initial_phase_from_sequence(self):
        """Should resolve initial phase from PhaseSequence when available."""
        seq = _make_phase_sequence(species_key="sp-1")
        entry1 = _make_sequence_entry(key="entry-0", sequence_order=0)
        entry2 = _make_sequence_entry(key="entry-1", sequence_order=1)

        self.phase_seq_repo.get_sequence_by_species.return_value = seq
        self.phase_seq_repo.get_entries_for_sequence.return_value = [entry2, entry1]

        service = PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            phase_repo=self.phase_repo,
            phase_seq_repo=self.phase_seq_repo,
        )

        result = service._resolve_initial_phase_key("sp-1")
        assert result == "entry-0"

    def test_initial_phase_fallback_lifecycle(self):
        """Should fall back to LifecycleConfig when no PhaseSequence."""
        self.phase_seq_repo.get_sequence_by_species.return_value = None
        gp = _make_growth_phase(key="gp-first", sequence_order=0)
        lc = _make_lifecycle()
        self.phase_repo.get_lifecycle_by_species.return_value = lc
        self.phase_repo.get_phases_by_lifecycle.return_value = [gp]

        service = PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            phase_repo=self.phase_repo,
            phase_seq_repo=self.phase_seq_repo,
        )

        result = service._resolve_initial_phase_key("sp-1")
        assert result == "gp-first"


# ── CareReminderService phase watering interval from PhaseSequence ────


class TestCareReminderServicePhaseSequenceFallback:
    """Test CareReminderService resolves watering interval from PhaseSequence."""

    def setup_method(self):
        self.care_repo = MagicMock()
        self.engine = MagicMock()
        self.plant_repo = MagicMock()
        self.lifecycle_repo = MagicMock()
        self.phase_seq_repo = MagicMock()

    def test_watering_interval_from_phase_sequence(self):
        """Should resolve watering_interval_days from PhaseSequence entry/definition."""
        plant = MagicMock()
        plant.current_phase_key = "entry-1"
        self.plant_repo.get_by_key.return_value = plant

        entry = _make_sequence_entry(key="entry-1", phase_definition_key="pd-1")
        defn = _make_phase_definition(key="pd-1", watering_interval_days=5)
        self.phase_seq_repo.get_entry_by_key.return_value = entry
        self.phase_seq_repo.get_definition_by_key.return_value = defn

        service = CareReminderService(
            self.care_repo,
            self.engine,
            plant_repo=self.plant_repo,
            lifecycle_repo=self.lifecycle_repo,
            phase_seq_repo=self.phase_seq_repo,
        )

        result = service._get_phase_watering_interval("plant-1")
        assert result == 5
        # LifecycleConfig should NOT be queried
        self.lifecycle_repo.get_phase_by_key.assert_not_called()

    def test_watering_interval_fallback_lifecycle(self):
        """Should fall back to LifecycleConfig when entry not in PhaseSequence."""
        plant = MagicMock()
        plant.current_phase_key = "gp-1"
        self.plant_repo.get_by_key.return_value = plant

        self.phase_seq_repo.get_entry_by_key.return_value = None
        gp = _make_growth_phase(key="gp-1", watering_interval_days=7)
        self.lifecycle_repo.get_phase_by_key.return_value = gp

        service = CareReminderService(
            self.care_repo,
            self.engine,
            plant_repo=self.plant_repo,
            lifecycle_repo=self.lifecycle_repo,
            phase_seq_repo=self.phase_seq_repo,
        )

        result = service._get_phase_watering_interval("plant-1")
        assert result == 7
