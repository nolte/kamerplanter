"""#1516 SCR-001 — closing a phase must hand the repository the *stored* entry.

``phase_histories`` is full-replace since #1516: a field absent from the model the
repository is handed is **removed** from the stored document. ``PhaseTransitionEngine``
closes the open phase-history entry on both of its write paths, and it used to build
the model it writes by re-listing ten of :class:`PhaseHistory`'s twelve fields. That
list had already drifted — ``performance_score`` was not on it — so under full-replace
every phase transition would have erased it.

**Why this file exists next to the integration measurement.** The integration test
``test_merge_mode_null_clearing.py`` reproduces the *write* against a real ArangoDB,
but it constructs that write itself; it never calls ``execute_transition`` or
``terminate``. An engine that went back to re-listing fields would leave it green.
This file measures the engine's own call, field by field, so the rule is anchored on
the code that has to keep it:

    every field of the stored entry except ``exited_at``, ``actual_duration_days``
    and ``transition_reason`` reaches the repository unchanged

— which is a property of the whole model, not of the two fields anybody remembers.
A new field on ``PhaseHistory`` is covered the day it is added, without this test
being touched, because the comparison iterates ``PhaseHistory.model_fields``.

**What the falsification showed, and why the assertion stays wide.** Restoring the
re-listing turns this file red on **three** fields, not one: ``performance_score``,
``created_at`` and ``updated_at``. Only the first reaches storage as a loss —
``_update_doc`` pops ``created_at`` in full-replace mode and stamps ``updated_at``
itself, so those two are absorbed downstream. The assertion is deliberately not
narrowed to ``performance_score``: this test measures the model the *engine* hands
over, and "the repository happens to repair it" is a second component's property
that can change without notice. A writer that drops a field it was never asked to
touch is the defect, wherever it is caught.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import TerminationType
from app.domain.engines.phase_transition_engine import PhaseTransitionEngine
from app.domain.models.lifecycle import GrowthPhase
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance

#: The three fields closing a phase is *allowed* to change. Everything else on the
#: model has to arrive as it was stored.
_CLOSING_WRITES = {"exited_at", "actual_duration_days", "transition_reason"}


def _phase(key: str, name: str, order: int) -> GrowthPhase:
    return GrowthPhase(
        key=key,
        name=name,
        sequence_order=order,
        lifecycle_key="lc-1",
        typical_duration_days=30,
    )


def _stored_history() -> PhaseHistory:
    """An open entry with **every** field carrying a non-default value.

    A default would make "preserved" and "rewritten with the default" the same
    observation — the distinction this test exists for. ``performance_score`` is the
    field the re-listing actually lost; ``is_premature`` and ``cycle_number`` are
    there so a re-listing that merely forgot a different one is caught too.
    """
    return PhaseHistory(
        key="h-open",
        plant_instance_key="plant-1",
        phase_key="ph-1",
        phase_name="vegetative",
        entered_at=datetime(2026, 1, 1, tzinfo=UTC),
        exited_at=None,
        actual_duration_days=None,
        cycle_number=3,
        transition_reason="seasonal_restart",
        is_premature=True,
        performance_score=82.5,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


class _Engine:
    """Engine plus the recording double its phase repository is replaced by."""

    def __init__(self) -> None:
        self.phase_repo = MagicMock()
        self.plant_repo = MagicMock()
        self.engine = PhaseTransitionEngine(self.phase_repo, self.plant_repo)

        self.stored = _stored_history()
        self.phase_repo.get_phase_history.return_value = [self.stored]
        self.phase_repo.get_transition_rules.return_value = []
        self.phase_repo.get_phase_by_key.side_effect = lambda k: {
            "ph-1": _phase("ph-1", "vegetative", 1),
            "ph-2": _phase("ph-2", "flowering", 2),
        }.get(k)

        plant = MagicMock(spec=PlantInstance)
        plant.key = "plant-1"
        plant.species_key = "sp-1"
        plant.current_phase_key = "ph-1"
        plant.current_phase_started_at = datetime(2026, 1, 1, tzinfo=UTC)
        plant.cultivation_cycle_type = None
        plant.reversion_count = 0
        self.plant_repo.get_by_key.return_value = plant
        self.plant_repo.update.return_value = plant

    def written(self) -> PhaseHistory:
        """The model the engine handed to ``update_phase_history``."""
        assert self.phase_repo.update_phase_history.call_count == 1, (
            "the engine did not close exactly one open phase-history entry; this test "
            "measures that write and has nothing to look at"
        )
        key, model = self.phase_repo.update_phase_history.call_args[0]
        assert key == "h-open"
        return model


@pytest.fixture
def harness() -> _Engine:
    return _Engine()


def _preserved_fields() -> list[str]:
    return sorted(set(PhaseHistory.model_fields) - _CLOSING_WRITES)


class TestExecuteTransitionCarriesTheStoredEntry:
    @pytest.mark.parametrize("field", _preserved_fields())
    def test_it_arrives_unchanged(self, harness: _Engine, field: str) -> None:
        """Against the re-listing this went red for ``performance_score`` (82.5 → None)."""
        harness.engine.execute_transition("plant-1", "ph-2", reason="manual")

        assert getattr(harness.written(), field) == getattr(harness.stored, field), (
            f"closing a phase rewrote {field}; under full-replace that removes the stored value"
        )

    def test_it_still_closes_the_entry(self, harness: _Engine) -> None:
        """The other half: the three fields it *may* change must actually change.

        Without this the parametrised test above would pass on an engine that wrote
        the stored entry back verbatim and never closed anything.
        """
        harness.engine.execute_transition("plant-1", "ph-2", reason="manual")

        written = harness.written()
        assert written.exited_at is not None
        assert written.actual_duration_days is not None
        assert written.transition_reason == "manual"


class TestTerminateCarriesTheStoredEntry:
    """``terminate`` freezes the open phase with its own copy of the same write."""

    @pytest.mark.parametrize("field", _preserved_fields())
    def test_it_arrives_unchanged(self, harness: _Engine, field: str) -> None:
        harness.engine.terminate("plant-1", TerminationType.HARVESTED)

        assert getattr(harness.written(), field) == getattr(harness.stored, field), (
            f"terminating a plant rewrote {field}; under full-replace that removes the stored value"
        )

    def test_it_still_closes_the_entry(self, harness: _Engine) -> None:
        harness.engine.terminate("plant-1", TerminationType.HARVESTED)

        written = harness.written()
        assert written.exited_at is not None
        assert written.transition_reason == TerminationType.HARVESTED.value
