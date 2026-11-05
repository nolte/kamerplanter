"""REQ-053 WP 8.15 (#2658) — the one per-pair companion rule and its fold.

:func:`judge_neighbour` is the decision the engine, the planting dialog and the plan overlay share; these tests pin
its precedence. :func:`strongest_verdict` folds several verdicts with the same precedence.
"""

from __future__ import annotations

from app.domain.engines.companion_planting_engine import (
    UNKNOWN_VERDICT,
    CompanionVerdict,
    judge_neighbour,
    strongest_verdict,
)


class TestJudgeNeighbour:
    def test_an_incompatible_edge_wins_over_a_compatible_one_between_the_same_species(self) -> None:
        assert judge_neighbour("fennel", {"fennel"}, {"fennel": 0.9}) == CompanionVerdict("incompatible")

    def test_a_compatible_edge_carries_its_score(self) -> None:
        assert judge_neighbour("basil", set(), {"basil": 0.8}) == CompanionVerdict("compatible", 0.8)

    def test_a_compatible_edge_without_a_score_keeps_none(self) -> None:
        assert judge_neighbour("basil", set(), {"basil": None}) == CompanionVerdict("compatible", None)

    def test_no_edge_is_unknown_nothing_is_assumed(self) -> None:
        assert judge_neighbour("carrot", {"fennel"}, {"basil": 0.8}) is UNKNOWN_VERDICT

    def test_an_incompatible_edge_alone_is_incompatible_without_a_score(self) -> None:
        verdict = judge_neighbour("fennel", ["fennel"], {})
        assert (verdict.status, verdict.score) == ("incompatible", None)


class TestStrongestVerdict:
    def test_incompatible_wins_whatever_comes_before_or_after(self) -> None:
        verdicts = [CompanionVerdict("compatible", 0.9), CompanionVerdict("incompatible"), UNKNOWN_VERDICT]
        assert strongest_verdict(verdicts).status == "incompatible"
        assert strongest_verdict(reversed(verdicts)).status == "incompatible"

    def test_of_several_compatible_the_highest_score_is_kept(self) -> None:
        verdicts = [CompanionVerdict("compatible", 0.4), CompanionVerdict("compatible", 0.9), UNKNOWN_VERDICT]
        assert strongest_verdict(verdicts) == CompanionVerdict("compatible", 0.9)

    def test_a_missing_score_ranks_below_any_number(self) -> None:
        verdicts = [CompanionVerdict("compatible", None), CompanionVerdict("compatible", 0.1)]
        assert strongest_verdict(verdicts) == CompanionVerdict("compatible", 0.1)
        assert strongest_verdict([CompanionVerdict("compatible", None)]) == CompanionVerdict("compatible", None)

    def test_compatible_beats_unknown(self) -> None:
        assert strongest_verdict([UNKNOWN_VERDICT, CompanionVerdict("compatible", 0.5)]).status == "compatible"

    def test_nothing_to_fold_is_unknown(self) -> None:
        assert strongest_verdict([]) is UNKNOWN_VERDICT
