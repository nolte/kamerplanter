"""Unit tests for PhaseService sequence-driven auto-advance helpers (#565 WP-2/WP-3).

Covers ``resolve_sequence_auto_target`` (forward step, terminal→restart, bounded
termination), ``find_phase_key_by_name`` and ``resolve_cycle_restart_phase_key`` — the
pieces the auto-transition task and the season coupler build on.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.common.enums import CycleType
from app.domain.models.phase_sequence import PhaseDefinition, PhaseSequence, PhaseSequenceEntry
from app.domain.services.phase_service import PhaseService

_RUNNER = [
    ("establishment", 0, 45, False, False),
    ("sprouting", 1, 21, False, True),
    ("vegetative", 2, 45, False, True),
    ("dormancy", 3, 120, True, True),
]


def _seq_repo(*, is_repeating: bool = True, cycle_restart_entry_order: int | None = 1) -> MagicMock:
    seq = PhaseSequence(
        _key="seq-1",
        name="perennial_runner",
        cycle_type=CycleType.PERENNIAL,
        is_repeating=is_repeating,
        cycle_restart_entry_order=cycle_restart_entry_order,
    )
    entries = []
    defs = {}
    for name, order, duration, is_terminal, is_recurring in _RUNNER:
        def_key = f"def-{name}"
        defs[def_key] = PhaseDefinition(_key=def_key, name=name, typical_duration_days=max(duration, 1))
        entries.append(
            PhaseSequenceEntry(
                _key=f"e-{order}",
                phase_sequence_key="seq-1",
                phase_definition_key=def_key,
                sequence_order=order,
                override_duration_days=duration,
                is_terminal=is_terminal,
                is_recurring=is_recurring,
            )
        )
    repo = MagicMock()
    repo.get_sequence_by_species.return_value = seq
    repo.get_entries_for_sequence.return_value = entries
    repo.get_definition_by_key.side_effect = lambda k: defs.get(k)
    return repo


def _service(seq_repo: MagicMock) -> PhaseService:
    return PhaseService(MagicMock(), MagicMock(), phase_seq_repo=seq_repo)


class TestResolveSequenceAutoTarget:
    def test_forward_step_to_next_entry(self) -> None:
        svc = _service(_seq_repo())
        target = svc.resolve_sequence_auto_target("sp-1", "e-1")  # sprouting → vegetative
        assert target is not None
        assert target.target_phase_key == "e-2"
        assert target.is_restart is False
        assert target.duration_days == 21

    def test_terminal_returns_restart_anchor(self) -> None:
        svc = _service(_seq_repo())
        target = svc.resolve_sequence_auto_target("sp-1", "e-3")  # dormancy → sprouting(restart)
        assert target is not None
        assert target.target_phase_key == "e-1"
        assert target.is_restart is True
        assert target.current_is_terminal is True

    def test_bounded_sequence_terminates(self) -> None:
        """A non-repeating sequence has no restart out of its terminal phase."""
        svc = _service(_seq_repo(is_repeating=False))
        assert svc.resolve_sequence_auto_target("sp-1", "e-3") is None

    def test_missing_restart_anchor_terminates(self) -> None:
        svc = _service(_seq_repo(cycle_restart_entry_order=None))
        assert svc.resolve_sequence_auto_target("sp-1", "e-3") is None

    def test_unknown_current_key_returns_none(self) -> None:
        svc = _service(_seq_repo())
        assert svc.resolve_sequence_auto_target("sp-1", "nope") is None

    def test_no_sequence_returns_none(self) -> None:
        repo = MagicMock()
        repo.get_sequence_by_species.return_value = None
        assert _service(repo).resolve_sequence_auto_target("sp-1", "e-1") is None


class TestPhaseKeyLookups:
    def test_find_phase_key_by_name(self) -> None:
        svc = _service(_seq_repo())
        assert svc.find_phase_key_by_name("sp-1", "dormancy") == "e-3"

    def test_find_phase_key_by_name_absent(self) -> None:
        svc = _service(_seq_repo())
        assert svc.find_phase_key_by_name("sp-1", "flowering") is None

    def test_resolve_cycle_restart_phase_key(self) -> None:
        svc = _service(_seq_repo())
        assert svc.resolve_cycle_restart_phase_key("sp-1") == "e-1"  # order 1 = sprouting

    def test_resolve_cycle_restart_phase_key_none(self) -> None:
        svc = _service(_seq_repo(cycle_restart_entry_order=None))
        assert svc.resolve_cycle_restart_phase_key("sp-1") is None
