"""Tests for start-phase handling at plant creation (REQ-003 #539).

A caller may capture the plant's *actual current state* by supplying
``current_phase_key`` at creation. The service:

* validates the supplied phase against the species' phase set — a foreign key
  (from another species) or a garbage key is rejected with a 422
  (``ValidationError``);
* accepts a valid non-first phase and marks the initial phase-history entry as
  an actual-state capture (``transition_reason="initial_actual_state"``);
* still auto-resolves the species' first phase (``transition_reason="initial"``)
  when no phase is supplied.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase_sequence import PhaseSequence, PhaseSequenceEntry
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService


def _plant(current_phase_key: str | None = None) -> PlantInstance:
    return PlantInstance(
        _key="plant-1",
        instance_id="P-1",
        species_key="sp-1",
        planted_on=date(2025, 1, 1),
        current_phase_key=current_phase_key,
    )


def _sequence() -> PhaseSequence:
    return PhaseSequence(_key="seq-1", name="Seq", species_key="sp-1")


def _entry(key: str, order: int) -> PhaseSequenceEntry:
    return PhaseSequenceEntry(
        _key=key,
        phase_definition_key=f"pd-{key}",
        sequence_order=order,
        phase_sequence_key="seq-1",
    )


def _lifecycle() -> LifecycleConfig:
    return LifecycleConfig(_key="lc-1", species_key="sp-1")


def _growth_phase(key: str, name: str, order: int) -> GrowthPhase:
    return GrowthPhase(_key=key, name=name, sequence_order=order, lifecycle_key="lc-1", typical_duration_days=14)


class TestCreatePlantStartPhase:
    def setup_method(self) -> None:
        self.plant_repo = MagicMock()
        self.site_repo = MagicMock()
        self.rotation = MagicMock()
        self.companion = MagicMock()
        self.phase_repo = MagicMock()
        self.phase_seq_repo = MagicMock()

        # create() echoes the plant back (already carries a key for history).
        self.plant_repo.create.side_effect = lambda p: p
        # Phase name resolution is not under test here.
        self.phase_repo.get_phase_by_key.return_value = None

        # Default species phase set: germination(0) → vegetative(1) → flowering(2).
        self.phase_seq_repo.get_sequence_by_species.return_value = _sequence()
        self.phase_seq_repo.get_entries_for_sequence.return_value = [
            _entry("entry-germ", 0),
            _entry("entry-veg", 1),
            _entry("entry-flower", 2),
        ]

        self.service = PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            phase_repo=self.phase_repo,
            phase_seq_repo=self.phase_seq_repo,
        )

    def _written_history(self):
        assert self.phase_repo.create_phase_history.called
        return self.phase_repo.create_phase_history.call_args.args[0]

    # ── auto-resolution (no phase supplied) ──────────────────────────────

    def test_no_phase_auto_resolves_first_and_marks_initial(self) -> None:
        created = self.service.create_plant(_plant(current_phase_key=None))

        assert created.current_phase_key == "entry-germ"
        assert self._written_history().transition_reason == "initial"

    # ── valid supplied phase ─────────────────────────────────────────────

    def test_valid_first_phase_is_accepted_as_plain_initial(self) -> None:
        created = self.service.create_plant(_plant(current_phase_key="entry-germ"))

        assert created.current_phase_key == "entry-germ"
        # Choosing the first phase is not an actual-state capture.
        assert self._written_history().transition_reason == "initial"

    def test_valid_non_first_phase_marks_actual_state_capture(self) -> None:
        created = self.service.create_plant(_plant(current_phase_key="entry-flower"))

        assert created.current_phase_key == "entry-flower"
        assert self._written_history().transition_reason == "initial_actual_state"

    # ── rejection of unknown / foreign phase ─────────────────────────────

    def test_garbage_phase_key_is_rejected_with_422(self) -> None:
        with pytest.raises(ValidationError) as exc:
            self.service.create_plant(_plant(current_phase_key="does-not-exist"))

        assert exc.value.status_code == 422
        assert exc.value.details[0]["code"] == "PHASE_NOT_IN_SEQUENCE"
        # Nothing persisted for a rejected creation.
        self.plant_repo.create.assert_not_called()

    def test_foreign_species_phase_key_is_rejected_with_422(self) -> None:
        # A key that belongs to a *different* species' sequence is not in this
        # species' phase set and must be rejected just like a garbage key.
        with pytest.raises(ValidationError) as exc:
            self.service.create_plant(_plant(current_phase_key="entry-from-other-species"))

        assert exc.value.status_code == 422
        self.plant_repo.create.assert_not_called()

    # ── LifecycleConfig fallback path ────────────────────────────────────

    def test_validation_uses_lifecycle_config_fallback(self) -> None:
        self.phase_seq_repo.get_sequence_by_species.return_value = None
        self.phase_repo.get_lifecycle_by_species.return_value = _lifecycle()
        self.phase_repo.get_phases_by_lifecycle.return_value = [
            _growth_phase("gp-seed", "seedling", 0),
            _growth_phase("gp-flower", "flowering", 1),
        ]

        created = self.service.create_plant(_plant(current_phase_key="gp-flower"))
        assert created.current_phase_key == "gp-flower"
        assert self._written_history().transition_reason == "initial_actual_state"

        with pytest.raises(ValidationError):
            self.service.create_plant(_plant(current_phase_key="gp-bogus"))

    def test_unconfigured_species_leaves_supplied_phase_untouched(self) -> None:
        # No PhaseSequence and no LifecycleConfig → empty valid set → cannot reject.
        self.phase_seq_repo.get_sequence_by_species.return_value = None
        self.phase_repo.get_lifecycle_by_species.return_value = None

        created = self.service.create_plant(_plant(current_phase_key="anything"))
        assert created.current_phase_key == "anything"
        # No first phase to compare against → plain initial.
        assert self._written_history().transition_reason == "initial"
