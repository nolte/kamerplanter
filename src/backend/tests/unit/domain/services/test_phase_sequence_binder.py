"""The runtime half of the seed's phase-sequence binding (#1006).

Only the seed ever bound a species to a ``PhaseSequence``. A species minted at
runtime — identify → ``create_species`` (REQ-048) or a CSV import — got none, so
every plant created for it resolved no initial phase and was stored with
``current_phase_key: null``. These tests cover the binder itself and the two write
paths that now call it.

The binder deliberately reuses ``resolve_phase_sequence_name``, the same pure
classifier the seed and the rebind migrations use, so the runtime paths cannot drift
onto a second rule.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.common.enums import CycleType, GrowthHabit
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.phase_sequence import PhaseSequence
from app.domain.models.species import Species
from app.domain.services.phase_sequence_binder import PhaseSequenceBinder

_CATALOGUE = [
    PhaseSequence(_key="seq-indoor", name="indoor_default"),
    PhaseSequence(_key="seq-evergreen", name="evergreen_foliage_perennial"),
    PhaseSequence(_key="seq-cam", name="cam_succulent_rest"),
]


def _species(**kwargs) -> Species:
    defaults = {
        "_key": "sp-1",
        "scientific_name": "Dracaena reflexa",
        "growth_habit": GrowthHabit.SHRUB,
    }
    return Species(**{**defaults, **kwargs})


@pytest.fixture
def repos():
    seq_repo = MagicMock()
    seq_repo.get_sequence_by_species.return_value = None
    seq_repo.get_all_sequences.return_value = (_CATALOGUE, len(_CATALOGUE))
    phase_repo = MagicMock()
    phase_repo.get_lifecycle_by_species.return_value = None
    return seq_repo, phase_repo


class TestBindDefault:
    def test_unresolvable_species_lands_on_the_repeating_perennial_cycle(self, repos) -> None:
        """No LifecycleConfig means *no answer*, never "annual" (#949 step 7)."""
        seq_repo, phase_repo = repos

        bound = PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species())

        assert bound == "evergreen_foliage_perennial"
        seq_repo.set_species_sequence.assert_called_once_with("sp-1", "seq-evergreen")

    def test_known_annual_lands_on_the_blanket(self, repos) -> None:
        seq_repo, phase_repo = repos
        phase_repo.get_lifecycle_by_species.return_value = LifecycleConfig(
            _key="lc-1", species_key="sp-1", cycle_type=CycleType.ANNUAL
        )

        bound = PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species())

        assert bound == "indoor_default"
        seq_repo.set_species_sequence.assert_called_once_with("sp-1", "seq-indoor")

    def test_cam_succulent_lands_on_its_cohort_sequence(self, repos) -> None:
        seq_repo, phase_repo = repos

        bound = PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species(photosynthesis_type="cam"))

        assert bound == "cam_succulent_rest"
        seq_repo.set_species_sequence.assert_called_once_with("sp-1", "seq-cam")

    def test_practised_cycle_wins_over_the_botanical_one(self, repos) -> None:
        """ADR-006 E1: a tender perennial cultivated as an annual belongs on the blanket."""
        seq_repo, phase_repo = repos
        phase_repo.get_lifecycle_by_species.return_value = LifecycleConfig(
            _key="lc-1",
            species_key="sp-1",
            cycle_type=CycleType.PERENNIAL,
            cultivation_cycle_type=CycleType.ANNUAL,
        )

        assert PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species()) == "indoor_default"

    def test_existing_binding_is_never_overridden(self, repos) -> None:
        """Idempotent — an explicit/precise binding must survive a re-run."""
        seq_repo, phase_repo = repos
        seq_repo.get_sequence_by_species.return_value = PhaseSequence(_key="seq-x", name="perennial_runner")

        assert PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species()) is None
        seq_repo.set_species_sequence.assert_not_called()

    def test_species_without_a_key_is_skipped(self, repos) -> None:
        seq_repo, phase_repo = repos
        assert PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species(_key=None)) is None
        seq_repo.set_species_sequence.assert_not_called()

    def test_a_target_that_is_not_seeded_is_reported_and_falls_back(self, repos) -> None:
        """#949: the resolver picking an unseeded sequence is a defect, not a fallback."""
        seq_repo, phase_repo = repos
        seq_repo.get_all_sequences.return_value = ([PhaseSequence(_key="seq-indoor", name="indoor_default")], 1)

        with patch("app.domain.services.phase_sequence_binder.logger") as log:
            bound = PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species())

        assert bound == "indoor_default"
        seq_repo.set_species_sequence.assert_called_once_with("sp-1", "seq-indoor")
        assert any(call.args[0] == "phase_sequence_target_not_seeded" for call in log.warning.call_args_list)

    def test_an_empty_catalogue_binds_nothing_and_says_so(self, repos) -> None:
        seq_repo, phase_repo = repos
        seq_repo.get_all_sequences.return_value = ([], 0)

        with patch("app.domain.services.phase_sequence_binder.logger") as log:
            assert PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species()) is None

        seq_repo.set_species_sequence.assert_not_called()
        assert any(call.args[0] == "phase_sequence_binding_skipped" for call in log.warning.call_args_list)

    def test_a_repository_failure_never_fails_the_species_write(self, repos) -> None:
        seq_repo, phase_repo = repos
        seq_repo.get_all_sequences.side_effect = RuntimeError("arango is down")

        with patch("app.domain.services.phase_sequence_binder.logger") as log:
            assert PhaseSequenceBinder(seq_repo, phase_repo).bind_default(_species()) is None

        assert any(call.args[0] == "phase_sequence_binding_failed" for call in log.warning.call_args_list)


class TestSpeciesServiceWiring:
    def test_create_species_binds_the_default_sequence(self) -> None:
        from app.domain.services.species_service import SpeciesService

        species_repo = MagicMock()
        created = _species()
        species_repo.upsert_by_normalized_scientific_name.return_value = created
        binder = MagicMock()

        service = SpeciesService(species_repo, MagicMock(), binder)
        result = service.create_species(_species())

        assert result is created
        binder.bind_default.assert_called_once_with(created)

    def test_create_species_still_works_without_a_binder(self) -> None:
        """The binder is optional so read-path constructions keep working."""
        from app.domain.services.species_service import SpeciesService

        species_repo = MagicMock()
        species_repo.upsert_by_normalized_scientific_name.return_value = _species()

        assert SpeciesService(species_repo, MagicMock()).create_species(_species()) is not None


class TestImportServiceWiring:
    def _service(self, binder):
        from app.common.enums import EntityType
        from app.domain.services.import_service import ImportService

        species_repo = MagicMock()
        species_repo.upsert_by_normalized_scientific_name.return_value = _species()
        service = ImportService(MagicMock(), species_repo, MagicMock(), binder)
        return service, species_repo, EntityType

    def test_imported_species_is_bound(self) -> None:
        binder = MagicMock()
        service, species_repo, entity_type = self._service(binder)

        create_fn = service._get_create_fn(entity_type.SPECIES)
        create_fn({"scientific_name": "Dracaena reflexa"})

        species_repo.upsert_by_normalized_scientific_name.assert_called_once()
        binder.bind_default.assert_called_once()

    def test_import_without_a_binder_still_creates(self) -> None:
        service, species_repo, entity_type = self._service(None)

        service._get_create_fn(entity_type.SPECIES)({"scientific_name": "Dracaena reflexa"})

        species_repo.upsert_by_normalized_scientific_name.assert_called_once()
