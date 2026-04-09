from unittest.mock import MagicMock

import pytest

from app.common.enums import CycleType, StressTolerance
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)
from app.domain.services.phase_sequence_service import PhaseSequenceService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return PhaseSequenceService(mock_repo)


# ── PhaseDefinition tests ──


class TestListDefinitions:
    def test_returns_definitions(self, service, mock_repo):
        defn = PhaseDefinition(name="Vegetative", typical_duration_days=28)
        mock_repo.get_all_definitions.return_value = ([defn], 1)

        items, total = service.list_definitions(0, 50)

        assert len(items) == 1
        assert total == 1
        assert items[0].name == "Vegetative"
        mock_repo.get_all_definitions.assert_called_once_with(0, 50, None)

    def test_with_name_filter(self, service, mock_repo):
        mock_repo.get_all_definitions.return_value = ([], 0)

        service.list_definitions(0, 50, name_filter="veg")

        mock_repo.get_all_definitions.assert_called_once_with(0, 50, "veg")


class TestGetDefinition:
    def test_found(self, service, mock_repo):
        defn = PhaseDefinition(name="Flowering", typical_duration_days=56)
        defn.key = "pd1"
        mock_repo.get_definition_by_key.return_value = defn

        result = service.get_definition("pd1")

        assert result.name == "Flowering"

    def test_not_found(self, service, mock_repo):
        mock_repo.get_definition_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.get_definition("nonexistent")


class TestCreateDefinition:
    def test_creates(self, service, mock_repo):
        defn = PhaseDefinition(name="Seedling", typical_duration_days=14)
        mock_repo.create_definition.return_value = defn

        result = service.create_definition(defn)

        assert result.name == "Seedling"
        mock_repo.create_definition.assert_called_once_with(defn)


class TestUpdateDefinition:
    def test_updates(self, service, mock_repo):
        defn = PhaseDefinition(name="Vegetative", typical_duration_days=28)
        defn.key = "pd1"
        mock_repo.get_definition_by_key.return_value = defn
        mock_repo.update_definition.return_value = PhaseDefinition(
            name="Vegetative Updated",
            typical_duration_days=30,
        )

        service.update_definition("pd1", {"name": "Vegetative Updated", "typical_duration_days": 30})

        assert mock_repo.update_definition.called

    def test_not_found(self, service, mock_repo):
        mock_repo.get_definition_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.update_definition("nonexistent", {"name": "x"})


class TestDeleteDefinition:
    def test_deletes(self, service, mock_repo):
        defn = PhaseDefinition(name="Old Phase", typical_duration_days=7, is_system=False)
        defn.key = "pd1"
        mock_repo.get_definition_by_key.return_value = defn
        mock_repo.get_definition_usage_count.return_value = 0
        mock_repo.delete_definition.return_value = True

        result = service.delete_definition("pd1")

        assert result is True

    def test_rejects_system(self, service, mock_repo):
        defn = PhaseDefinition(name="System Phase", typical_duration_days=7, is_system=True)
        defn.key = "pd1"
        mock_repo.get_definition_by_key.return_value = defn

        with pytest.raises(ValidationError, match="system"):
            service.delete_definition("pd1")

    def test_rejects_in_use(self, service, mock_repo):
        defn = PhaseDefinition(name="Used Phase", typical_duration_days=7, is_system=False)
        defn.key = "pd1"
        mock_repo.get_definition_by_key.return_value = defn
        mock_repo.get_definition_usage_count.return_value = 3

        with pytest.raises(ValidationError, match="referenced"):
            service.delete_definition("pd1")


# ── PhaseSequence tests ──


class TestListSequences:
    def test_returns_sequences(self, service, mock_repo):
        seq = PhaseSequence(name="Cannabis Annual")
        mock_repo.get_all_sequences.return_value = ([seq], 1)

        items, total = service.list_sequences()

        assert len(items) == 1
        assert total == 1


class TestGetSequence:
    def test_found(self, service, mock_repo):
        seq = PhaseSequence(name="Cannabis Annual")
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq

        result = service.get_sequence("ps1")

        assert result.name == "Cannabis Annual"

    def test_not_found(self, service, mock_repo):
        mock_repo.get_sequence_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.get_sequence("nonexistent")


class TestGetFullSequence:
    def test_returns_enriched(self, service, mock_repo):
        seq = PhaseSequence(name="Cannabis Annual", cycle_type=CycleType.ANNUAL)
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq

        entry = PhaseSequenceEntry(
            phase_sequence_key="ps1",
            phase_definition_key="pd1",
            sequence_order=0,
            override_duration_days=None,
        )
        entry.key = "pse1"
        mock_repo.get_entries_for_sequence.return_value = [entry]

        defn = PhaseDefinition(
            name="Vegetative",
            typical_duration_days=28,
            stress_tolerance=StressTolerance.MEDIUM,
        )
        defn.key = "pd1"
        mock_repo.get_definition_by_key.return_value = defn

        result = service.get_full_sequence("ps1")

        assert result["name"] == "Cannabis Annual"
        assert len(result["entries"]) == 1
        assert result["entries"][0]["effective_duration_days"] == 28
        assert result["entries"][0]["phase_definition"]["name"] == "Vegetative"

    def test_effective_duration_uses_override(self, service, mock_repo):
        seq = PhaseSequence(name="Custom")
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq

        entry = PhaseSequenceEntry(
            phase_sequence_key="ps1",
            phase_definition_key="pd1",
            sequence_order=0,
            override_duration_days=42,
        )
        entry.key = "pse1"
        mock_repo.get_entries_for_sequence.return_value = [entry]

        defn = PhaseDefinition(name="Flowering", typical_duration_days=56)
        defn.key = "pd1"
        mock_repo.get_definition_by_key.return_value = defn

        result = service.get_full_sequence("ps1")

        assert result["entries"][0]["effective_duration_days"] == 42


class TestCreateSequence:
    def test_creates(self, service, mock_repo):
        seq = PhaseSequence(name="New Sequence")
        mock_repo.create_sequence.return_value = seq

        result = service.create_sequence(seq)

        assert result.name == "New Sequence"


class TestDeleteSequence:
    def test_deletes(self, service, mock_repo):
        seq = PhaseSequence(name="Old Sequence", is_system=False)
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq
        mock_repo.get_sequence_usage_count.return_value = 0
        mock_repo.delete_sequence.return_value = True

        result = service.delete_sequence("ps1")

        assert result is True

    def test_rejects_system(self, service, mock_repo):
        seq = PhaseSequence(name="System Sequence", is_system=True)
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq

        with pytest.raises(ValidationError, match="system"):
            service.delete_sequence("ps1")

    def test_rejects_in_use(self, service, mock_repo):
        seq = PhaseSequence(name="Used Sequence", is_system=False)
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq
        mock_repo.get_sequence_usage_count.return_value = 2

        with pytest.raises(ValidationError, match="referenced"):
            service.delete_sequence("ps1")


# ── PhaseSequenceEntry tests ──


class TestCreateEntry:
    def test_validates_references(self, service, mock_repo):
        seq = PhaseSequence(name="Test")
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq

        defn = PhaseDefinition(name="Flowering", typical_duration_days=56)
        defn.key = "pd1"
        mock_repo.get_definition_by_key.return_value = defn

        entry = PhaseSequenceEntry(
            phase_sequence_key="ps1",
            phase_definition_key="pd1",
            sequence_order=0,
        )
        mock_repo.create_entry.return_value = entry

        result = service.create_entry(entry)

        mock_repo.get_sequence_by_key.assert_called_with("ps1")
        mock_repo.get_definition_by_key.assert_called_with("pd1")
        assert result.phase_definition_key == "pd1"

    def test_rejects_missing_sequence(self, service, mock_repo):
        mock_repo.get_sequence_by_key.return_value = None

        entry = PhaseSequenceEntry(
            phase_sequence_key="nonexistent",
            phase_definition_key="pd1",
        )

        with pytest.raises(NotFoundError):
            service.create_entry(entry)

    def test_rejects_missing_definition(self, service, mock_repo):
        seq = PhaseSequence(name="Test")
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq
        mock_repo.get_definition_by_key.return_value = None

        entry = PhaseSequenceEntry(
            phase_sequence_key="ps1",
            phase_definition_key="nonexistent",
        )

        with pytest.raises(NotFoundError):
            service.create_entry(entry)


class TestUpdateEntry:
    def test_validates_new_definition(self, service, mock_repo):
        existing = PhaseSequenceEntry(
            phase_sequence_key="ps1",
            phase_definition_key="pd1",
            sequence_order=0,
        )
        existing.key = "pse1"
        mock_repo.get_entry_by_key.return_value = existing

        new_defn = PhaseDefinition(name="Harvest", typical_duration_days=7)
        new_defn.key = "pd2"
        mock_repo.get_definition_by_key.return_value = new_defn
        mock_repo.update_entry.return_value = existing

        service.update_entry("pse1", {"phase_definition_key": "pd2"})

        mock_repo.get_definition_by_key.assert_called_with("pd2")


class TestDeleteEntry:
    def test_deletes(self, service, mock_repo):
        entry = PhaseSequenceEntry(phase_sequence_key="ps1", phase_definition_key="pd1")
        entry.key = "pse1"
        mock_repo.get_entry_by_key.return_value = entry
        mock_repo.delete_entry.return_value = True

        result = service.delete_entry("pse1")

        assert result is True

    def test_not_found(self, service, mock_repo):
        mock_repo.get_entry_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.delete_entry("nonexistent")


class TestReorderEntries:
    def test_reorders(self, service, mock_repo):
        seq = PhaseSequence(name="Test")
        seq.key = "ps1"
        mock_repo.get_sequence_by_key.return_value = seq

        entries = [
            PhaseSequenceEntry(phase_sequence_key="ps1", phase_definition_key="pd1", sequence_order=0),
            PhaseSequenceEntry(phase_sequence_key="ps1", phase_definition_key="pd2", sequence_order=1),
        ]
        mock_repo.reorder_entries.return_value = entries

        orders = [{"key": "pse1", "sequence_order": 1}, {"key": "pse2", "sequence_order": 0}]
        result = service.reorder_entries("ps1", orders)

        assert len(result) == 2
        mock_repo.reorder_entries.assert_called_once_with("ps1", orders)
