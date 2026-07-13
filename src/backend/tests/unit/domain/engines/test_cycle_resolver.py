"""Unit tests for the single cycle-of-truth cascade (ADR-006 E1, #565 Phase 2).

``resolve_effective_cycle`` is the ONE place every consumer resolves the effective
cultivation cycle. Priority (most specific wins): instance override → species
cultivation_cycle_type → species botanical cycle_type → PhaseSequence cycle_type.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.common.enums import CycleType
from app.domain.engines.cycle_resolver import resolve_effective_cycle
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.phase_sequence import PhaseSequence
from app.domain.models.plant_instance import PlantInstance


def _instance(cultivation_cycle_type: CycleType | None) -> PlantInstance:
    return PlantInstance(
        _key="p1",
        tenant_key="t1",
        instance_id="i1",
        species_key="sp-1",
        planted_on=date(2026, 1, 1),
        cultivation_cycle_type=cultivation_cycle_type,
    )


def _biennial_lc() -> LifecycleConfig:
    # Biennials require vernalization per the model validator.
    return LifecycleConfig(species_key="sp-1", cycle_type=CycleType.BIENNIAL, vernalization_required=True)


class TestInstanceTierWins:
    def test_instance_override_beats_perennial_species(self) -> None:
        lc = LifecycleConfig(species_key="sp-1", cycle_type=CycleType.PERENNIAL)
        assert resolve_effective_cycle(_instance(CycleType.ANNUAL), lc) == CycleType.ANNUAL

    def test_instance_override_beats_annual_species(self) -> None:
        lc = LifecycleConfig(species_key="sp-1", cycle_type=CycleType.ANNUAL)
        assert resolve_effective_cycle(_instance(CycleType.PERENNIAL), lc) == CycleType.PERENNIAL

    def test_instance_override_beats_species_cultivation_axis(self) -> None:
        lc = LifecycleConfig(
            species_key="sp-1", cycle_type=CycleType.PERENNIAL, cultivation_cycle_type=CycleType.ANNUAL
        )
        assert resolve_effective_cycle(_instance(CycleType.PERENNIAL), lc) == CycleType.PERENNIAL


class TestSpeciesTier:
    def test_no_override_uses_species_cultivation_axis(self) -> None:
        lc = LifecycleConfig(
            species_key="sp-1", cycle_type=CycleType.PERENNIAL, cultivation_cycle_type=CycleType.ANNUAL
        )
        assert resolve_effective_cycle(_instance(None), lc) == CycleType.ANNUAL

    def test_no_override_no_cultivation_axis_uses_botanical(self) -> None:
        assert resolve_effective_cycle(_instance(None), _biennial_lc()) == CycleType.BIENNIAL

    def test_none_instance_starts_at_species_tier(self) -> None:
        lc = LifecycleConfig(species_key="sp-1", cycle_type=CycleType.PERENNIAL)
        assert resolve_effective_cycle(None, lc) == CycleType.PERENNIAL


class TestSequenceFallback:
    def test_no_lifecycle_uses_sequence_cycle(self) -> None:
        seq = PhaseSequence(_key="seq-1", name="perennial_runner", cycle_type=CycleType.PERENNIAL)
        assert resolve_effective_cycle(_instance(None), None, seq) == CycleType.PERENNIAL

    def test_instance_override_beats_sequence(self) -> None:
        seq = PhaseSequence(_key="seq-1", name="perennial_runner", cycle_type=CycleType.PERENNIAL)
        assert resolve_effective_cycle(_instance(CycleType.ANNUAL), None, seq) == CycleType.ANNUAL

    def test_lifecycle_beats_sequence_when_both_present(self) -> None:
        lc = LifecycleConfig(species_key="sp-1", cycle_type=CycleType.ANNUAL)
        seq = PhaseSequence(_key="seq-1", name="perennial_runner", cycle_type=CycleType.PERENNIAL)
        assert resolve_effective_cycle(_instance(None), lc, seq) == CycleType.ANNUAL


class TestUnknown:
    def test_no_source_returns_none(self) -> None:
        assert resolve_effective_cycle(_instance(None), None, None) is None

    @pytest.mark.parametrize("cycle", [CycleType.ANNUAL, CycleType.PERENNIAL])
    def test_override_resolves_even_without_species_data(self, cycle: CycleType) -> None:
        assert resolve_effective_cycle(_instance(cycle), None, None) == cycle
