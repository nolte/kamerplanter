"""Selftest for the replaying database double's predicate parser (#1503).

The double is a measuring instrument, and the failure class that keeps costing
is the *instrument* having the gap rather than the guard: a predicate shape it
does not recognise is silently ignored, so it hands back rows the real query
would have filtered out. For a query that also carries a ``LIMIT`` that is not a
harmless false green but a false **red** — the unfiltered rows fill the page and
the row the filter existed to surface is paged away again.

``IN @bind`` is the shape #1503 added to the hand-written task AQL. These cases
pin it *and* re-pin the equality shape beside it, so a future edit to one regex
cannot quietly drop the other.
"""

from __future__ import annotations

from tests.support.tenant_replay import apply_predicates, paginate, rows_and_count

ROWS = [
    {"_key": "a", "tenant_key": "t1", "origin": "user", "status": "pending"},
    {"_key": "b", "tenant_key": "t1", "origin": "system", "status": "pending"},
    {"_key": "c", "tenant_key": "t1", "origin": "pipeline", "status": "done"},
    {"_key": "d", "tenant_key": "t2", "origin": "pipeline", "status": "pending"},
]


def _keys(rows: list[dict]) -> list[str]:
    return [row["_key"] for row in rows]


class TestTheInShape:
    def test_a_single_valued_list_selects_only_that_value(self):
        result = apply_predicates(ROWS, "FOR doc IN tasks FILTER doc.origin IN @origins", {"origins": ["system"]})

        assert _keys(result) == ["b"]

    def test_a_multi_valued_list_selects_their_union(self):
        result = apply_predicates(
            ROWS,
            "FOR doc IN tasks FILTER doc.origin IN @origins",
            {"origins": ["system", "pipeline"]},
        )

        assert _keys(result) == ["b", "c", "d"]

    def test_an_empty_list_selects_nothing(self):
        """AQL's answer, not "no filter given": an empty list is a predicate
        nothing satisfies, and treating it as absent would be the widening the
        #324 class is made of."""
        result = apply_predicates(ROWS, "FOR doc IN tasks FILTER doc.origin IN @origins", {"origins": []})

        assert result == []

    def test_a_row_missing_the_attribute_is_not_selected(self):
        rows = [*ROWS, {"_key": "legacy", "tenant_key": "t1"}]

        result = apply_predicates(rows, "FOR doc IN tasks FILTER doc.origin IN @origins", {"origins": ["user"]})

        assert _keys(result) == ["a"]

    def test_it_composes_with_the_equality_shape_rather_than_replacing_it(self):
        query = "FOR doc IN tasks FILTER doc.tenant_key == @tenant_key AND doc.origin IN @origins"

        result = apply_predicates(ROWS, query, {"tenant_key": "t1", "origins": ["pipeline"]})

        assert _keys(result) == ["c"]

    def test_a_string_bind_var_matches_nothing_rather_than_by_substring(self):
        """``in`` over a *string* is a substring test in Python and a type error
        in AQL. Left alone, ``doc.origin IN @origins`` with ``@origins='pipeline'``
        would quietly select every row whose origin is a substring of it — the
        double would be *looser* than the database it stands in for, which is the
        one direction a fake must never be."""
        result = apply_predicates(ROWS, "FOR doc IN tasks FILTER doc.origin IN @origins", {"origins": "pipelines"})

        assert result == []

    def test_a_tuple_or_set_is_a_collection_like_a_list(self):
        for wanted in (("user", "system"), {"user", "system"}):
            result = apply_predicates(ROWS, "FOR doc IN tasks FILTER doc.origin IN @origins", {"origins": wanted})

            assert _keys(result) == ["a", "b"]

    def test_an_unbound_list_variable_is_skipped_rather_than_guessed_at(self):
        result = apply_predicates(ROWS, "FOR doc IN tasks FILTER doc.origin IN @origins", {})

        assert _keys(result) == _keys(ROWS)


class TestTheInShapeUnderALimit:
    """The reason the gap matters: filtering happens *before* paging."""

    QUERY = (
        "FOR doc IN tasks FILTER doc.tenant_key == @tenant_key AND doc.origin IN @origins "
        "SORT doc.due_date ASC LIMIT @offset, @limit RETURN doc"
    )

    def test_the_page_is_cut_out_of_the_filtered_rows_not_the_raw_ones(self):
        bind = {"tenant_key": "t1", "origins": ["pipeline"], "offset": 0, "limit": 2}

        filtered = apply_predicates(ROWS, self.QUERY, bind)

        assert _keys(paginate(filtered, self.QUERY, bind)) == ["c"]

    def test_the_count_arm_counts_the_same_filtered_rows(self):
        bind = {"tenant_key": "t1", "origins": ["user", "system"], "offset": 0, "limit": 2}

        assert rows_and_count(ROWS, self.QUERY + " COLLECT WITH COUNT INTO total RETURN total", bind) == [2]
