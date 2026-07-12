"""Tests for the shared perennial→sequence classifier (ADR-006 E2, #565)."""

from __future__ import annotations

import pytest

from app.migrations.perennial_binding import (
    EVERGREEN_PERENNIAL_SEQUENCE,
    RUNNER_PERENNIAL_SEQUENCE,
    resolve_perennial_sequence_name,
)


@pytest.mark.parametrize(
    ("scientific_name", "cycle_type", "flowering_strategy", "expected"),
    [
        ("Fragaria x ananassa", "perennial", "polycarpic", RUNNER_PERENNIAL_SEQUENCE),
        ("Ficus benjamina", "perennial", "polycarpic", EVERGREEN_PERENNIAL_SEQUENCE),
        ("Monstera deliciosa", "perennial", None, EVERGREEN_PERENNIAL_SEQUENCE),
        ("Lactuca sativa", "annual", None, None),
        ("Daucus carota", "biennial", "monocarpic", None),
        ("Agave americana", "perennial", "monocarpic", None),
        ("Unknown", None, None, None),
    ],
)
def test_resolve_perennial_sequence_name(scientific_name, cycle_type, flowering_strategy, expected) -> None:
    assert resolve_perennial_sequence_name(scientific_name, cycle_type, flowering_strategy) == expected
