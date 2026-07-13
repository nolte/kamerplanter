"""Tests for PhaseKeyResolver — cross-keyspace phase resolution (#579)."""

from unittest.mock import MagicMock

from app.domain.engines.phase_key_resolver import PhaseKeyResolver
from app.domain.models.lifecycle import GrowthPhase
from app.domain.models.phase_sequence import PhaseDefinition, PhaseSequenceEntry


def _entry(
    key: str = "entry-1",
    *,
    phase_definition_key: str = "pd-1",
    sequence_order: int = 2,
    is_terminal: bool = False,
    phase_sequence_key: str = "seq-1",
) -> PhaseSequenceEntry:
    return PhaseSequenceEntry(
        _key=key,
        phase_definition_key=phase_definition_key,
        sequence_order=sequence_order,
        is_terminal=is_terminal,
        phase_sequence_key=phase_sequence_key,
    )


def _growth_phase(key: str = "gp-1", name: str = "flowering", sequence_order: int = 3) -> GrowthPhase:
    return GrowthPhase(
        _key=key,
        name=name,
        sequence_order=sequence_order,
        lifecycle_key="lc-1",
        typical_duration_days=30,
        is_terminal=True,
    )


class TestPhaseKeyResolver:
    def setup_method(self) -> None:
        self.phase_repo = MagicMock()
        self.phase_seq_repo = MagicMock()

    def test_resolves_phase_sequence_entry_first(self) -> None:
        """An entry key resolves in the PhaseSequenceEntry key-space (authoritative)."""
        self.phase_seq_repo.get_entry_by_key.return_value = _entry(sequence_order=2, is_terminal=True)
        self.phase_seq_repo.get_definition_by_key.return_value = PhaseDefinition(_key="pd-1", name="flowering")

        resolver = PhaseKeyResolver(self.phase_repo, self.phase_seq_repo)
        resolved = resolver.resolve("entry-1")

        assert resolved is not None
        assert resolved.source == "phase_sequence"
        assert resolved.name == "flowering"
        assert resolved.sequence_order == 2
        assert resolved.is_terminal is True
        assert resolved.sequence_key == "seq-1"
        # The legacy GrowthPhase space must not be consulted for an entry key.
        self.phase_repo.get_phase_by_key.assert_not_called()

    def test_falls_back_to_growth_phase(self) -> None:
        """A key absent from the entry space resolves as a legacy GrowthPhase."""
        self.phase_seq_repo.get_entry_by_key.return_value = None
        self.phase_repo.get_phase_by_key.return_value = _growth_phase(name="harvest", sequence_order=3)

        resolver = PhaseKeyResolver(self.phase_repo, self.phase_seq_repo)
        resolved = resolver.resolve("gp-1")

        assert resolved is not None
        assert resolved.source == "growth_phase"
        assert resolved.name == "harvest"
        assert resolved.sequence_order == 3
        assert resolved.lifecycle_key == "lc-1"

    def test_no_seq_repo_uses_growth_phase_only(self) -> None:
        self.phase_repo.get_phase_by_key.return_value = _growth_phase()
        resolver = PhaseKeyResolver(self.phase_repo, None)

        resolved = resolver.resolve("gp-1")
        assert resolved is not None
        assert resolved.source == "growth_phase"

    def test_unknown_key_returns_none(self) -> None:
        self.phase_seq_repo.get_entry_by_key.return_value = None
        self.phase_repo.get_phase_by_key.return_value = None
        resolver = PhaseKeyResolver(self.phase_repo, self.phase_seq_repo)

        assert resolver.resolve("dangling") is None
        assert resolver.resolve(None) is None
        assert resolver.resolve("") is None

    def test_resolve_name_and_is_known(self) -> None:
        self.phase_seq_repo.get_entry_by_key.return_value = _entry()
        self.phase_seq_repo.get_definition_by_key.return_value = PhaseDefinition(_key="pd-1", name="vegetative")
        resolver = PhaseKeyResolver(self.phase_repo, self.phase_seq_repo)

        assert resolver.resolve_name("entry-1") == "vegetative"
        assert resolver.is_known("entry-1") is True

    def test_is_known_false_for_dangling(self) -> None:
        self.phase_seq_repo.get_entry_by_key.return_value = None
        self.phase_repo.get_phase_by_key.return_value = None
        resolver = PhaseKeyResolver(self.phase_repo, self.phase_seq_repo)

        assert resolver.is_known("dangling-entry-key") is False
        assert resolver.resolve_name("dangling-entry-key") == ""
