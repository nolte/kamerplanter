"""Key-stability of the PhaseSequence seeder (#579).

A re-seed MUST preserve every PhaseSequenceEntry ``_key`` so a plant's
``current_phase_key`` (an entry key) never dangles across re-seeds. Before #579
the seeder deleted and recreated every entry, minting fresh keys each run. These
tests run the seeder twice against an in-memory repo and assert the entry keys are
stable, while still reflecting sequence content changes.
"""

from __future__ import annotations

from itertools import count
from unittest.mock import patch

from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)
from app.migrations.seed_phase_sequences import run_seed_phase_sequences


class _FakeRepo:
    """Minimal in-memory PhaseSequence repository with monotonic key minting."""

    def __init__(self) -> None:
        self.definitions: dict[str, PhaseDefinition] = {}
        self.sequences: dict[str, PhaseSequence] = {}
        self.entries: dict[str, PhaseSequenceEntry] = {}
        self._ids = count(1)

    def _next(self, prefix: str) -> str:
        return f"{prefix}-{next(self._ids)}"

    # ── definitions ──
    def get_definition_by_name(self, name: str) -> PhaseDefinition | None:
        return next((d for d in self.definitions.values() if d.name == name), None)

    def create_definition(self, defn: PhaseDefinition) -> PhaseDefinition:
        key = self._next("def")
        stored = defn.model_copy(update={"key": key})
        self.definitions[key] = stored
        return stored

    def update_definition(self, key: str, defn: PhaseDefinition) -> PhaseDefinition:
        stored = defn.model_copy(update={"key": key})
        self.definitions[key] = stored
        return stored

    # ── sequences ──
    def get_all_sequences(self, offset: int, limit: int) -> tuple[list[PhaseSequence], int]:
        items = list(self.sequences.values())
        return items[offset : offset + limit], len(items)

    def create_sequence(self, seq: PhaseSequence) -> PhaseSequence:
        key = self._next("seq")
        stored = seq.model_copy(update={"key": key})
        self.sequences[key] = stored
        return stored

    def update_sequence(self, key: str, seq: PhaseSequence) -> PhaseSequence:
        stored = seq.model_copy(update={"key": key})
        self.sequences[key] = stored
        return stored

    # ── entries ──
    def get_entries_for_sequence(self, seq_key: str) -> list[PhaseSequenceEntry]:
        return sorted(
            (e for e in self.entries.values() if e.phase_sequence_key == seq_key),
            key=lambda e: e.sequence_order,
        )

    def create_entry(self, entry: PhaseSequenceEntry) -> PhaseSequenceEntry:
        key = self._next("entry")
        stored = entry.model_copy(update={"key": key})
        self.entries[key] = stored
        return stored

    def update_entry(self, key: str, entry: PhaseSequenceEntry) -> PhaseSequenceEntry:
        stored = entry.model_copy(update={"key": key})
        self.entries[key] = stored
        return stored

    def delete_entry(self, key: str) -> bool:
        return self.entries.pop(key, None) is not None

    # ── snapshot helper for the assertions ──
    def entry_key_map(self) -> dict[tuple[str, str], str]:
        """Map ``(phase_sequence_key, phase_definition_key)`` → entry ``_key``."""
        return {(e.phase_sequence_key, e.phase_definition_key): (e.key or "") for e in self.entries.values()}


def _run(repo: _FakeRepo) -> None:
    with patch("app.migrations.seed_phase_sequences.get_phase_sequence_repo", return_value=repo):
        run_seed_phase_sequences()


class TestSeedKeyStability:
    def test_entry_keys_are_stable_across_reseed(self) -> None:
        repo = _FakeRepo()
        _run(repo)
        first = repo.entry_key_map()
        assert first, "the seeder must create at least one entry from the YAML"

        _run(repo)
        second = repo.entry_key_map()

        # Every (sequence, definition) that survived the re-seed keeps its key.
        assert first == second

    def test_reseed_does_not_multiply_entries(self) -> None:
        repo = _FakeRepo()
        _run(repo)
        count_after_first = len(repo.entries)

        _run(repo)
        assert len(repo.entries) == count_after_first
