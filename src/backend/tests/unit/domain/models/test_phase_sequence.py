import pytest
from pydantic import ValidationError

from app.common.enums import CycleType, StressTolerance
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)


class TestPhaseDefinition:
    def test_create_minimal(self):
        defn = PhaseDefinition(name="Vegetative")
        assert defn.name == "Vegetative"
        assert defn.typical_duration_days == 1
        assert defn.stress_tolerance == StressTolerance.MEDIUM
        assert defn.tags == []
        assert defn.is_system is False

    def test_create_full(self):
        defn = PhaseDefinition(
            name="Flowering",
            display_name="Flowering Phase",
            display_name_de="Bluetephase",
            description="The flowering stage",
            description_de="Die Bluetephase",
            typical_duration_days=56,
            stress_tolerance=StressTolerance.LOW,
            watering_interval_days=3,
            tags=["cannabis", "flowering"],
            is_system=True,
        )
        assert defn.typical_duration_days == 56
        assert defn.stress_tolerance == StressTolerance.LOW
        assert defn.watering_interval_days == 3
        assert len(defn.tags) == 2

    def test_name_min_length(self):
        with pytest.raises(ValidationError):
            PhaseDefinition(name="")

    def test_name_max_length(self):
        with pytest.raises(ValidationError):
            PhaseDefinition(name="x" * 101)

    def test_typical_duration_days_min(self):
        with pytest.raises(ValidationError):
            PhaseDefinition(name="Test", typical_duration_days=0)

    def test_watering_interval_bounds(self):
        with pytest.raises(ValidationError):
            PhaseDefinition(name="Test", watering_interval_days=0)
        with pytest.raises(ValidationError):
            PhaseDefinition(name="Test", watering_interval_days=91)

    def test_alias(self):
        defn = PhaseDefinition(**{"_key": "pd1", "name": "Test"})
        assert defn.key == "pd1"


class TestPhaseSequence:
    def test_create_minimal(self):
        seq = PhaseSequence(name="Annual Cannabis")
        assert seq.name == "Annual Cannabis"
        assert seq.cycle_type == CycleType.ANNUAL
        assert seq.is_repeating is False
        assert seq.is_system is False
        assert seq.tags == []

    def test_create_perennial(self):
        seq = PhaseSequence(
            name="Perennial Herbs",
            cycle_type=CycleType.PERENNIAL,
            is_repeating=True,
            cycle_restart_entry_order=2,
        )
        assert seq.cycle_type == CycleType.PERENNIAL
        assert seq.is_repeating is True
        assert seq.cycle_restart_entry_order == 2

    def test_name_min_length(self):
        with pytest.raises(ValidationError):
            PhaseSequence(name="")

    def test_name_max_length(self):
        with pytest.raises(ValidationError):
            PhaseSequence(name="x" * 201)


class TestPhaseSequenceEntry:
    def test_create_minimal(self):
        entry = PhaseSequenceEntry()
        assert entry.phase_sequence_key == ""
        assert entry.phase_definition_key == ""
        assert entry.sequence_order == 0
        assert entry.override_duration_days is None
        assert entry.is_terminal is False
        assert entry.allows_harvest is False
        assert entry.is_recurring is False

    def test_create_full(self):
        entry = PhaseSequenceEntry(
            phase_sequence_key="ps1",
            phase_definition_key="pd1",
            sequence_order=3,
            override_duration_days=42,
            is_terminal=True,
            allows_harvest=True,
            is_recurring=False,
        )
        assert entry.sequence_order == 3
        assert entry.override_duration_days == 42
        assert entry.is_terminal is True
        assert entry.allows_harvest is True

    def test_sequence_order_min(self):
        with pytest.raises(ValidationError):
            PhaseSequenceEntry(sequence_order=-1)

    def test_override_duration_min(self):
        with pytest.raises(ValidationError):
            PhaseSequenceEntry(override_duration_days=0)
