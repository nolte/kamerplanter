"""Issue #949 — the species→sequence assignment point actually persists something.

Two defects are pinned here, both of which returned ``200`` while doing nothing
durable:

* ``PhaseSequence.species_key`` was writable through ``PUT /phase-sequences/{key}``
  but nothing resolves against it — the lifecycle engine reads the
  ``HAS_PHASE_SEQUENCE`` **edge**. Writing the field alone was a no-op with a
  success status.
* ``LifecycleConfig.phase_sequence_key`` appears in every lifecycle *response* but
  was absent from the write schema, so a ``PUT`` wrote ``None`` over the stored
  binding — a silent, destructive drop rather than the 422 it should have been.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import CycleType
from app.common.exceptions import NotFoundError
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.phase_sequence import PhaseSequence
from app.domain.services.phase_service import PhaseService

_EVERGREEN = PhaseSequence(
    _key="seq-evergreen",
    name="evergreen_foliage_perennial",
    cycle_type=CycleType.PERENNIAL,
    is_repeating=True,
)


def _service(*, lifecycle: LifecycleConfig | None = None, previous: str | None = "seq-indoor-default"):
    phase_repo = MagicMock()
    phase_repo.get_lifecycle_by_species.return_value = lifecycle
    phase_repo.get_lifecycle_or_raise.return_value = lifecycle
    phase_repo.update_lifecycle.side_effect = lambda _key, config: config

    seq_repo = MagicMock()
    seq_repo.get_sequence_by_key.side_effect = lambda key: _EVERGREEN if key == "seq-evergreen" else None
    seq_repo.set_species_sequence.return_value = previous

    return PhaseService(phase_repo, MagicMock(), phase_seq_repo=seq_repo), phase_repo, seq_repo


class TestAssignPhaseSequence:
    def test_it_writes_the_edge_that_the_engine_actually_resolves_against(self) -> None:
        service, _phase_repo, seq_repo = _service()

        result = service.assign_phase_sequence("sp-yucca", "seq-evergreen")

        seq_repo.set_species_sequence.assert_called_once_with("sp-yucca", "seq-evergreen")
        assert result["sequence_key"] == "seq-evergreen"

    def test_it_reports_the_binding_it_replaced(self) -> None:
        service, _phase_repo, _seq_repo = _service(previous="seq-indoor-default")

        result = service.assign_phase_sequence("sp-yucca", "seq-evergreen")

        # A rebind is destructive on the old edge; naming what was replaced is what
        # lets a caller (and the MCP dry run) say so before and after the fact.
        assert result["previous_sequence_key"] == "seq-indoor-default"

    def test_a_species_that_had_no_binding_reports_none_rather_than_a_blank(self) -> None:
        service, _phase_repo, _seq_repo = _service(previous=None)

        assert service.assign_phase_sequence("sp-yucca", "seq-evergreen")["previous_sequence_key"] is None

    def test_it_syncs_the_lifecycle_field_so_the_two_records_cannot_diverge(self) -> None:
        lifecycle = LifecycleConfig(_key="lc-1", species_key="sp-yucca", cycle_type=CycleType.PERENNIAL)
        service, phase_repo, _seq_repo = _service(lifecycle=lifecycle)

        result = service.assign_phase_sequence("sp-yucca", "seq-evergreen")

        assert result["lifecycle_key"] == "lc-1"
        _key, written = phase_repo.update_lifecycle.call_args.args
        assert written.phase_sequence_key == "seq-evergreen"

    def test_a_species_without_a_lifecycle_still_binds(self) -> None:
        """The edge alone drives the engine; a missing lifecycle is a valid state."""

        service, phase_repo, seq_repo = _service(lifecycle=None)

        result = service.assign_phase_sequence("sp-yucca", "seq-evergreen")

        assert result["lifecycle_key"] is None
        seq_repo.set_species_sequence.assert_called_once()
        phase_repo.update_lifecycle.assert_not_called()

    def test_an_unknown_sequence_raises_instead_of_stranding_a_dangling_edge(self) -> None:
        service, _phase_repo, seq_repo = _service()

        with pytest.raises(NotFoundError):
            service.assign_phase_sequence("sp-yucca", "seq-typo")

        seq_repo.set_species_sequence.assert_not_called()


class TestUpdateLifecyclePreservesTheBinding:
    """A PUT that omits ``phase_sequence_key`` must not erase it."""

    def test_an_omitted_phase_sequence_key_keeps_the_stored_one(self) -> None:
        stored = LifecycleConfig(
            _key="lc-1",
            species_key="sp-yucca",
            cycle_type=CycleType.PERENNIAL,
            phase_sequence_key="seq-evergreen",
        )
        service, phase_repo, _seq_repo = _service(lifecycle=stored)

        # What the router builds from a PUT body that never mentions the field.
        incoming = LifecycleConfig(species_key="sp-yucca", cycle_type=CycleType.PERENNIAL)
        assert incoming.phase_sequence_key is None

        updated = service.update_lifecycle("lc-1", incoming)

        assert updated.phase_sequence_key == "seq-evergreen", (
            "A PUT without the field silently dropped the binding and returned 200 — "
            "the defect issue #949 calls worse than a 422."
        )

    def test_an_explicit_phase_sequence_key_still_wins(self) -> None:
        stored = LifecycleConfig(
            _key="lc-1",
            species_key="sp-yucca",
            cycle_type=CycleType.PERENNIAL,
            phase_sequence_key="seq-indoor-default",
        )
        service, _phase_repo, _seq_repo = _service(lifecycle=stored)

        incoming = LifecycleConfig(
            species_key="sp-yucca",
            cycle_type=CycleType.PERENNIAL,
            phase_sequence_key="seq-evergreen",
        )
        assert service.update_lifecycle("lc-1", incoming).phase_sequence_key == "seq-evergreen"


class TestLifecycleWriteSchema:
    def test_cycle_type_is_required_rather_than_defaulting_to_annual(self) -> None:
        """#949: an unknown cycle must be a 422, not a silent ``annual``.

        ``cycle_type`` is what the phase-sequence resolver keys on, so a default
        here is the same defect as the resolver's own annual fallback — it records
        the strongest possible assertion on behalf of a caller who did not make it.
        """

        from pydantic import ValidationError as PydanticValidationError

        from app.api.v1.lifecycle_configs.schemas import LifecycleCreate

        with pytest.raises(PydanticValidationError):
            LifecycleCreate(species_key="sp-yucca")

    def test_phase_sequence_key_is_part_of_the_write_schema(self) -> None:
        """It appeared in every response but in no write body — so it was unwritable."""

        from app.api.v1.lifecycle_configs.schemas import LifecycleCreate

        assert "phase_sequence_key" in LifecycleCreate.model_fields
