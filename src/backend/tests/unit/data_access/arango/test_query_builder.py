"""Unit tests for the AQLBuilder LIMIT binding (SEC-B5).

The builder previously interpolated ``LIMIT {offset}, {limit}`` into the query
text. These tests pin the injection-safe replacement: offset/limit are bound as
reserved ``@__offset``/``@__limit`` parameters and never appear in the count
query's bind_vars.
"""

from app.data_access.arango.query_builder import AQLBuilder


def test_build_list_binds_offset_and_limit():
    query, bind_vars = AQLBuilder("things").paginate(10, 5).build_list()

    assert "LIMIT @__offset, @__limit" in query
    assert "LIMIT {" not in query
    assert bind_vars["__offset"] == 10
    assert bind_vars["__limit"] == 5


def test_build_list_without_pagination_has_no_limit():
    query, bind_vars = AQLBuilder("things").build_list()

    assert "LIMIT" not in query
    assert "__offset" not in bind_vars
    assert "__limit" not in bind_vars


def test_filter_and_pagination_binds_coexist():
    builder = AQLBuilder("things").filter("name", "==", "tomato").paginate(0, 50)
    query, bind_vars = builder.build_list()

    assert "doc.name == @v0" in query
    assert bind_vars["v0"] == "tomato"
    assert bind_vars["__offset"] == 0
    assert bind_vars["__limit"] == 50


def test_build_count_excludes_pagination_binds():
    builder = AQLBuilder("things").filter("name", "==", "tomato").paginate(10, 5)
    # build_list must not mutate the builder's shared bind_vars.
    builder.build_list()
    count_query, count_bind = builder.build_count()

    assert "COLLECT WITH COUNT INTO total" in count_query
    assert "LIMIT" not in count_query
    assert "__offset" not in count_bind
    assert "__limit" not in count_bind
    assert count_bind["v0"] == "tomato"
