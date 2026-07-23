"""Call-site guard for the ADR-006 E1 effective-cycle binding fix in the seed linker.

The seed phase-sequence linker (:func:`app.migrations.seed_data.link_indoor_species_to_phase_sequence`)
must classify a species on its **effective** (cultivation-aware) cycle, not the raw
botanical one. A tender perennial (tomato) is botanically ``perennial`` but cultivated as
an annual (``cultivation_cycle_type = annual``): it must land on the harvest-bearing
``indoor_default`` blanket, NOT on the harvest-less cyclic ``evergreen_foliage_perennial``.

These tests exercise the real linker with mocked repositories/DB so they prove the
call-site wiring (``resolve_effective_cycle`` → ``resolve_phase_sequence_name``), not just
the pure resolver. They are data-independent (they construct their own lifecycle), so they
are green before the seed data reclassifies the 11 tender perennials.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import CycleType, FloweringStrategy, PhotoperiodType
from app.domain.models.lifecycle import LifecycleConfig
from app.migrations import seed_data
from app.migrations.perennial_binding import (
    EVERGREEN_PERENNIAL_SEQUENCE,
    INDOOR_DEFAULT_SEQUENCE,
)

#: Phase sequences the mocked repo exposes — only the two the fix chooses between.
_SEQUENCES = (
    SimpleNamespace(name=INDOOR_DEFAULT_SEQUENCE, key="idk"),
    SimpleNamespace(name=EVERGREEN_PERENNIAL_SEQUENCE, key="evk"),
)
_SEQ_KEY_BY_NAME = {s.name: s.key for s in _SEQUENCES}


def _run_linker_for(lifecycle: LifecycleConfig, monkeypatch: pytest.MonkeyPatch) -> str:
    """Run the real seed linker for a single tomato-like species and return the bound sequence name."""
    species = SimpleNamespace(
        key="sp1",
        scientific_name="Solanum lycopersicum",
        photosynthesis_type=None,  # C3 herb — never triggers the CAM rule
        growth_habit=None,  # not fern/geophyte/palm
    )

    ps_repo = MagicMock()
    ps_repo.get_all_sequences.return_value = (list(_SEQUENCES), None)
    species_repo = MagicMock()
    species_repo.get_all.return_value = ([species], None)
    lifecycle_repo = MagicMock()
    lifecycle_repo.get_lifecycle_by_species.return_value = lifecycle

    edge_col = MagicMock()
    db = MagicMock()
    db.aql.execute.return_value = []  # no pre-existing HAS_PHASE_SEQUENCE edge
    db.collection.return_value = edge_col

    monkeypatch.setattr(seed_data, "get_phase_sequence_repo", lambda: ps_repo)
    monkeypatch.setattr(seed_data, "get_species_repo", lambda: species_repo)
    monkeypatch.setattr(seed_data, "get_lifecycle_repo", lambda: lifecycle_repo)
    monkeypatch.setattr(seed_data, "get_db", lambda: db)

    seed_data.link_indoor_species_to_phase_sequence()

    edge_col.insert.assert_called_once()
    inserted_to = edge_col.insert.call_args.args[0]["_to"]
    bound_key = inserted_to.split("/", 1)[1]
    # Invert the key→name map so the assertion reads in sequence names.
    return next(name for name, key in _SEQ_KEY_BY_NAME.items() if key == bound_key)


def test_effective_annual_perennial_binds_indoor_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Botanical perennial + cultivation annual ⇒ indoor_default (the FIX)."""
    lifecycle = LifecycleConfig(
        species_key="sp1",
        cycle_type=CycleType.PERENNIAL,
        cultivation_cycle_type=CycleType.ANNUAL,
        flowering_strategy=FloweringStrategy.POLYCARPIC,
        photoperiod_type=PhotoperiodType.DAY_NEUTRAL,
    )
    assert _run_linker_for(lifecycle, monkeypatch) == INDOOR_DEFAULT_SEQUENCE


def test_pure_botanical_perennial_still_binds_evergreen(monkeypatch: pytest.MonkeyPatch) -> None:
    """Negative control: without the cultivation override, a botanical perennial stays evergreen.

    Proves the divergence is driven by ``cultivation_cycle_type`` alone — the fix is inert
    for genuine perennials, so existing perennial bindings do not regress.
    """
    lifecycle = LifecycleConfig(
        species_key="sp1",
        cycle_type=CycleType.PERENNIAL,
        cultivation_cycle_type=None,
        flowering_strategy=FloweringStrategy.POLYCARPIC,
        photoperiod_type=PhotoperiodType.DAY_NEUTRAL,
    )
    assert _run_linker_for(lifecycle, monkeypatch) == EVERGREEN_PERENNIAL_SEQUENCE
