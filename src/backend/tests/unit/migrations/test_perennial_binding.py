"""Tests for the shared perennial→sequence classifiers (ADR-006 E2, #565 / #616)."""

from __future__ import annotations

import pytest

from app.migrations.perennial_binding import (
    CAM_DOUBLE_REST_SEQUENCE,
    CAM_SUCCULENT_REST_SEQUENCE,
    CLONAL_MONOCARP_SEQUENCE,
    EVERGREEN_PERENNIAL_SEQUENCE,
    FERN_SPORE_SEQUENCE,
    GEOPHYTE_FINE_SEQUENCE,
    PALM_EVERGREEN_SEQUENCE,
    PHOTOPERIODIC_ORNAMENTAL_SEQUENCE,
    RUNNER_PERENNIAL_SEQUENCE,
    resolve_perennial_sequence_name,
    resolve_phase_sequence_name,
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


# Short aliases keep the parametrize table within the line-length budget.
_CAM = CAM_SUCCULENT_REST_SEQUENCE
_CAM2 = CAM_DOUBLE_REST_SEQUENCE
_CLONAL = CLONAL_MONOCARP_SEQUENCE
_PHOTO = PHOTOPERIODIC_ORNAMENTAL_SEQUENCE
_PALM = PALM_EVERGREEN_SEQUENCE
_FERN = FERN_SPORE_SEQUENCE
_GEO = GEOPHYTE_FINE_SEQUENCE
_EVER = EVERGREEN_PERENNIAL_SEQUENCE
_RUNNER = RUNNER_PERENNIAL_SEQUENCE


@pytest.mark.parametrize(
    ("name", "cycle", "flowering", "photo_syn", "photoperiod", "habit", "expected"),
    [
        # -- D9: CAM succulents (winter rest); Lithops gets the double rest --
        ("Aloe vera", "perennial", "polycarpic", "cam", "day_neutral", "succulent", _CAM),
        ("Zamioculcas zamiifolia", "perennial", "polycarpic", "cam", "day_neutral", "succulent", _CAM),
        # Epiphytic CAM orchid that is *not* monocarpic → still CAM rest, not clonal.
        ("Phalaenopsis hybrida", "perennial", "polycarpic", "cam", "day_neutral", "epiphyte", _CAM),
        ("Lithops spp.", "perennial", "polycarpic", "cam", "day_neutral", "succulent", _CAM2),
        # -- D10: monocarpic perennial epiphytes (bromeliads) → clonal continuation --
        ("Aechmea fasciata", "perennial", "monocarpic", "cam", "day_neutral", "epiphyte", _CLONAL),
        ("Guzmania lingulata", "perennial", "monocarpic", None, "day_neutral", "epiphyte", _CLONAL),
        # -- D11: short-day PERENNIAL ornamentals (beats CAM and monocarpic) --
        ("Euphorbia pulcherrima", "perennial", "polycarpic", None, "short_day", "shrub", _PHOTO),
        ("Kalanchoe blossfeldiana", "perennial", "polycarpic", "cam", "short_day", "succulent", _PHOTO),
        ("Kalanchoe daigremontiana", "perennial", "monocarpic", "cam", "short_day", "succulent", _PHOTO),
        # short-day beats the bulb_geophyte habit (Dahlia).
        ("Dahlia pinnata", "perennial", "polycarpic", None, "short_day", "bulb_geophyte", _PHOTO),
        # Annual short-day CROP (cannabis) stays on the blanket — no ornamental cycle.
        ("Cannabis sativa", "annual", None, None, "short_day", "herb", None),
        # -- D12: growth-habit fine typing --
        ("Adiantum raddianum", "perennial", None, None, "day_neutral", "fern", _FERN),
        ("Clivia miniata", "perennial", "polycarpic", None, "day_neutral", "bulb_geophyte", _GEO),
        ("Chamaedorea elegans", "perennial", "polycarpic", None, "day_neutral", "tree", _PALM),
        ("Howea forsteriana", "perennial", "polycarpic", None, "day_neutral", "tree", _PALM),
        # A non-palm tree is NOT a palm → generic evergreen.
        ("Ficus benjamina", "perennial", "polycarpic", None, "day_neutral", "tree", _EVER),
        # -- Fallbacks --
        ("Monstera deliciosa", "perennial", "polycarpic", None, "day_neutral", "vine", _EVER),
        ("Fragaria x ananassa", "perennial", "polycarpic", None, "day_neutral", "groundcover", _RUNNER),
        ("Lactuca sativa", "annual", None, None, "long_day", "herb", None),
        ("Solanum lycopersicum", "annual", "polycarpic", None, "day_neutral", "herb", None),
    ],
)
def test_resolve_phase_sequence_name(name, cycle, flowering, photo_syn, photoperiod, habit, expected) -> None:
    assert (
        resolve_phase_sequence_name(
            name,
            cycle_type=cycle,
            flowering_strategy=flowering,
            photosynthesis_type=photo_syn,
            photoperiod_type=photoperiod,
            growth_habit=habit,
        )
        == expected
    )
