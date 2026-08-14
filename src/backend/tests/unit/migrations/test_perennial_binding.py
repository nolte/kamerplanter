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
        # A short-day GEOPHYTE is not a photoperiodic ornamental (#1149). This case
        # previously asserted `_PHOTO` — "short-day beats the bulb_geophyte habit" —
        # and that was the defect, not the contract: `photoperiodic_ornamental` runs
        # active_growth → short_day_induction → bract_coloring → rest_phase, and a
        # dahlia has no bracts. The two phases its year turns on, tuber_formation and
        # dry_storage, exist only in `geophyte_fine`, so on the old binding nothing
        # ever prompted lifting the tubers of a frost-sensitive species.
        ("Dahlia pinnata", "perennial", "polycarpic", None, "short_day", "bulb_geophyte", _GEO),
        # The rest of D11 is untouched: a short-day perennial that is *not* a geophyte
        # still takes the ornamental cycle. Pinned next to the change so a later reader
        # can see the rule was narrowed, not inverted.
        ("Schlumbergera truncata", "perennial", "polycarpic", None, "short_day", "epiphyte", _PHOTO),
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
        # -- A KNOWN biennial is still a determinate cycle → blanket is correct --
        ("Daucus carota", "biennial", "monocarpic", None, "long_day", "herb", None),
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


class TestUnresolvableSpeciesNeverFallToTheAnnualBlanket:
    """Issue #949 — a null ``cycle_type`` is *no answer*, not ``annual``.

    A species with no ``LifecycleConfig`` reaches the resolver with every
    lifecycle-derived input null. Routing it to ``indoor_default`` asserted a
    126-day cycle ending in a terminal, harvest-allowing phase — which is how a
    *Yucca gigantea* (evergreen, perennial, polycarpic tree) came to be scheduled
    harvest-ready and lifecycle-complete 126 days after planting.
    """

    def test_a_species_with_no_lifecycle_at_all_lands_on_the_repeating_cycle(self) -> None:
        # Exactly the Yucca gigantea input: tenant record, empty photosynthesis_type,
        # no LifecycleConfig, so cycle_type/flowering/photoperiod all arrive as None.
        assert (
            resolve_phase_sequence_name(
                "Yucca gigantea",
                cycle_type=None,
                flowering_strategy=None,
                photosynthesis_type=None,
                photoperiod_type=None,
                growth_habit=None,
            )
            == EVERGREEN_PERENNIAL_SEQUENCE
        )

    @pytest.mark.parametrize("name", ["Aglaonema modestum", "Dracaena reflexa"])
    def test_the_other_two_species_from_the_same_bucket_move_too(self, name: str) -> None:
        # Both sat on ``indoor_default`` alongside Rosenkohl and Porree — the
        # template collision the issue's reverse lookup surfaced.
        assert (
            resolve_phase_sequence_name(
                name,
                cycle_type=None,
                flowering_strategy=None,
                photosynthesis_type=None,
                photoperiod_type=None,
                growth_habit=None,
            )
            == EVERGREEN_PERENNIAL_SEQUENCE
        )

    def test_an_unknown_cycle_string_is_also_treated_as_unresolved(self) -> None:
        # Defensive: a cycle value the resolver does not know is absence of an
        # answer too, and must not be read as a licence to schedule a harvest.
        assert (
            resolve_phase_sequence_name(
                "Some novum",
                cycle_type="not_a_real_cycle",
                flowering_strategy=None,
                photosynthesis_type=None,
                photoperiod_type=None,
                growth_habit=None,
            )
            == EVERGREEN_PERENNIAL_SEQUENCE
        )

    @pytest.mark.parametrize("cycle", ["annual", "biennial"])
    def test_a_known_determinate_cycle_still_takes_the_blanket(self, cycle: str) -> None:
        """The fix must not sweep genuine annuals off their harvest-terminated cycle.

        ``None`` is the signal being changed, not ``annual`` — a lettuce really
        does end after one season and belongs on ``indoor_default``.
        """
        assert (
            resolve_phase_sequence_name(
                "Lactuca sativa",
                cycle_type=cycle,
                flowering_strategy=None,
                photosynthesis_type=None,
                photoperiod_type=None,
                growth_habit="herb",
            )
            is None
        )
