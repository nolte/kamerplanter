"""REQ-053 WP 3.2 — V-08, the time window of a slot reservation (GP-FR-065, GP-ACC-021, GP-ACC-039)."""

from __future__ import annotations

from datetime import date

import pytest

from app.domain.engines.slot_reservation_engine import (
    CONFLICT_ACTIVE_PLANT,
    CONFLICT_RESERVATION,
    ActivePlant,
    Reservation,
    allocate_slot_ids,
    find_conflicts,
    intersects_year,
    plant_state,
    slot_id_prefix,
    window_overlap,
)

D = date


def reservation(slot: str, run: str, start: date | None, end: date | None, *, status: str = "planned") -> Reservation:
    return Reservation(
        slot_key=slot,
        run_key=run,
        entry_key="e1",
        planned_species_key="sp",
        sequence=1,
        planned_from=start,
        planned_until=end,
        run_status=status,
    )


class TestWindowOverlap:
    def test_disjoint_windows_do_not_overlap(self) -> None:
        assert window_overlap(D(2026, 5, 15), D(2026, 9, 30), D(2026, 10, 5), None) is None

    def test_the_overlap_is_the_intersection(self) -> None:
        assert window_overlap(D(2026, 8, 1), None, D(2026, 5, 15), D(2026, 9, 30)) == (D(2026, 8, 1), D(2026, 9, 30))

    def test_the_last_day_is_still_occupied(self) -> None:
        assert window_overlap(D(2026, 9, 30), None, D(2026, 5, 15), D(2026, 9, 30)) == (D(2026, 9, 30), D(2026, 9, 30))
        assert window_overlap(D(2026, 10, 1), None, D(2026, 5, 15), D(2026, 9, 30)) is None

    def test_two_open_windows_overlap_without_an_end(self) -> None:
        assert window_overlap(D(2026, 5, 1), None, D(2026, 7, 1), None) == (D(2026, 7, 1), None)

    def test_an_open_start_reaches_back_without_limit(self) -> None:
        assert window_overlap(None, D(2026, 6, 1), D(2026, 5, 1), D(2026, 5, 31)) == (D(2026, 5, 1), D(2026, 5, 31))

    @pytest.mark.parametrize(
        ("first", "second"),
        [
            ((D(2026, 1, 1), D(2026, 3, 1)), (D(2026, 2, 1), D(2026, 4, 1))),
            ((D(2026, 1, 1), None), (D(2025, 1, 1), D(2026, 1, 1))),
            ((D(2026, 6, 1), D(2026, 6, 1)), (D(2026, 1, 1), None)),
        ],
    )
    def test_it_is_symmetric(self, first, second) -> None:
        assert window_overlap(*first, *second) == window_overlap(*second, *first)


class TestFindConflicts:
    """GP-ACC-039: run A holds 2026-05-15 … 2026-09-30."""

    A = reservation("s1", "run_a", D(2026, 5, 15), D(2026, 9, 30))

    def test_a_follow_up_crop_after_the_window_is_allowed(self) -> None:
        found = find_conflicts(
            ["s1"],
            run_key="run_b",
            planned_from=D(2026, 10, 5),
            planned_until=None,
            reservations=[self.A],
            plants=[],
        )
        assert found == []

    def test_an_overlapping_window_names_the_other_run_and_the_overlap(self) -> None:
        (conflict,) = find_conflicts(
            ["s1"],
            run_key="run_c",
            planned_from=D(2026, 8, 1),
            planned_until=None,
            reservations=[self.A],
            plants=[],
        )
        assert (conflict.kind, conflict.conflicting_run_key) == (CONFLICT_RESERVATION, "run_a")
        assert (conflict.overlap_from, conflict.overlap_until) == (D(2026, 8, 1), D(2026, 9, 30))
        assert conflict.as_detail()["overlap_until"] == "2026-09-30"

    def test_a_slot_of_another_run_with_the_same_window_is_a_conflict_but_the_runs_own_edge_is_not(self) -> None:
        own = reservation("s1", "run_b", D(2026, 5, 15), D(2026, 9, 30))
        assert (
            find_conflicts(
                ["s1"],
                run_key="run_b",
                planned_from=D(2026, 5, 15),
                planned_until=D(2026, 9, 30),
                reservations=[own],
                plants=[],
            )
            == []
        )
        assert find_conflicts(
            ["s1"],
            run_key="run_c",
            planned_from=D(2026, 5, 15),
            planned_until=D(2026, 9, 30),
            reservations=[own],
            plants=[],
        )

    def test_another_entry_of_the_same_run_conflicts_but_the_same_entry_does_not(self) -> None:
        """One position cannot hold two entries of a run; replacing an entry's own reservation is the normal path."""
        other_entry = Reservation("s1", "run_b", "e_other", "sp", 1, D(2026, 10, 5), None)
        kwargs = {"run_key": "run_b", "planned_from": D(2026, 10, 5), "planned_until": None, "plants": []}

        (conflict,) = find_conflicts(["s1"], reservations=[other_entry], entry_key="e_mine", **kwargs)
        assert (conflict.kind, conflict.conflicting_run_key) == (CONFLICT_RESERVATION, "run_b")
        assert find_conflicts(["s1"], reservations=[other_entry], entry_key="e_other", **kwargs) == []
        # without an entry every reservation of the run is its own (the pre-WP-3.2 reading)
        assert find_conflicts(["s1"], reservations=[other_entry], **kwargs) == []

    def test_a_reservation_of_an_ended_run_does_not_count(self) -> None:
        ended = reservation("s1", "run_a", D(2026, 5, 15), D(2026, 9, 30), status="completed")
        assert (
            find_conflicts(
                ["s1"], run_key="run_c", planned_from=D(2026, 6, 1), planned_until=None, reservations=[ended], plants=[]
            )
            == []
        )

    def test_only_the_requested_slots_are_judged_and_each_gets_its_first_conflict(self) -> None:
        other = reservation("s2", "run_x", D(2026, 1, 1), None)
        found = find_conflicts(
            ["s1", "s2", "s3"],
            run_key="run_c",
            planned_from=D(2026, 6, 1),
            planned_until=D(2026, 6, 30),
            reservations=[self.A, other],
            plants=[],
        )
        assert [c.slot_key for c in found] == ["s1", "s2"]

    def test_an_active_plant_blocks_a_reservation_that_starts_before_its_runs_end(self) -> None:
        plant = ActivePlant("s1", "pi_1", "run_a", D(2026, 9, 30))
        (conflict,) = find_conflicts(
            ["s1"], run_key="run_b", planned_from=D(2026, 9, 1), planned_until=None, reservations=[], plants=[plant]
        )
        assert conflict.kind == CONFLICT_ACTIVE_PLANT
        assert (conflict.conflicting_run_key, conflict.overlap_from, conflict.overlap_until) == (
            "run_a",
            D(2026, 9, 1),
            D(2026, 9, 30),
        )

    def test_a_reservation_after_the_plants_expected_end_is_allowed(self) -> None:
        plant = ActivePlant("s1", "pi_1", "run_a", D(2026, 9, 30))
        assert (
            find_conflicts(
                ["s1"],
                run_key="run_b",
                planned_from=D(2026, 10, 1),
                planned_until=None,
                reservations=[],
                plants=[plant],
            )
            == []
        )

    def test_a_plant_without_a_known_end_blocks_every_start(self) -> None:
        loose = ActivePlant("s1", "pi_1", None, None)
        assert find_conflicts(
            ["s1"], run_key="run_b", planned_from=D(2030, 1, 1), planned_until=None, reservations=[], plants=[loose]
        )

    def test_the_runs_own_plants_never_block_it(self) -> None:
        own = ActivePlant("s1", "pi_1", "run_b", None)
        assert (
            find_conflicts(
                ["s1"], run_key="run_b", planned_from=D(2026, 6, 1), planned_until=None, reservations=[], plants=[own]
            )
            == []
        )


class TestSlotIds:
    def test_the_prefix_is_the_beds_name_in_capitals(self) -> None:
        assert slot_id_prefix("Beet 3 (Süd)", "77") == "BEET3SD"  # a character outside A-Z is dropped
        assert slot_id_prefix("Hochbeet 3", "77") == "HOCHBEET3"

    def test_a_name_without_letters_falls_back_to_the_key(self) -> None:
        assert slot_id_prefix("---", "k9") == "LK9"

    def test_ids_continue_after_the_highest_in_use_archived_ones_included(self) -> None:
        taken = {"BEET3_001", "BEET3_002", "BEET3_007", "OTHER_050"}
        assert allocate_slot_ids("BEET3", taken, 3) == ["BEET3_008", "BEET3_009", "BEET3_010"]

    def test_the_first_ids_of_an_empty_bed(self) -> None:
        assert allocate_slot_ids("BEET3", set(), 2) == ["BEET3_001", "BEET3_002"]


class TestStates:
    def test_a_standing_plant_is_active(self) -> None:
        assert plant_state(None, None) == "active"

    def test_a_harvested_plant_and_any_other_removal(self) -> None:
        assert plant_state(D(2026, 9, 1), "harvested") == "harvested"
        assert plant_state(D(2026, 9, 1), "died") == "historical"
        assert plant_state(D(2026, 9, 1), None) == "historical"

    def test_a_window_touches_a_year(self) -> None:
        assert intersects_year(D(2025, 11, 1), D(2026, 2, 1), 2026)
        assert not intersects_year(D(2025, 11, 1), D(2025, 12, 31), 2026)
        assert intersects_year(D(2026, 5, 1), None, 2031)
