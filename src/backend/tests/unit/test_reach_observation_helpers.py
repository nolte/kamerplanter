"""The parsing halves of the capability-reach observation helpers (#1680).

``scripts/reach/observe_*.py`` are the observation steps of the approved reach
probes under ``project/reach-probes/``. Their proof is the real run against the
reach stack (``.audits/capability-reach/``); what is pinned here is the part a
fake can honestly stand in for — turning an opened archive, measured row counts
or a query log into member lines — and above all the property every helper must
keep: **what it prints is an observation, never a verdict**, and an empty or
absent observation is printed as such instead of as silence (the runner reads
silence as *not probed*, which would hide a defect).

The ArangoDB query each helper sends (``_MATCHING`` in the residue helper) is not
evaluated by any double here: a fake cannot execute AQL, and one that pretended
to would certify a query the database has never seen. The real run is its test.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.support.repo_scripts import load_repo_script

export = load_repo_script("reach/observe_export_archive")
residue = load_repo_script("reach/observe_erasure_residue")
inventory = load_repo_script("reach/observe_executing_inventory")


# ── observe_export_archive ─────────────────────────────────────────────────


def _subject() -> dict[str, Any]:
    return {
        "subject": "reach-subject",
        "rows": [
            {"id": "users/reach-subject", "key": "reach-subject", "collection": "users", "kind": "document"},
            {"id": "consent_records/rsa", "key": "rsa", "collection": "consent_records", "kind": "document"},
            {"id": "tasks/rsb", "key": "rsb", "collection": "tasks", "kind": "document"},
            {"id": "has_consent/rse", "key": "rse", "collection": "has_consent", "kind": "edge"},
        ],
        "subject_edges": {"has_consent": "consent_records/rsa"},
    }


def _bundle(*sections: tuple[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {"sections": [{"collection": name, "records": records} for name, records in sections]}


def test_a_record_counts_only_when_it_carries_a_seeded_row_marker_of_its_own_collection():
    bundle = _bundle(
        ("users", [{"avatar_url": "reach-seed:reach-subject:avatar_url"}]),
        ("consent_records", [{"purpose": "reach-seed:rsa:purpose"}]),
        # A tasks section that holds another collection's row is not the subject's task.
        ("tasks", [{"name": "reach-seed:rsa:purpose"}]),
    )
    assert export.observe([bundle], _subject()) == [
        "collection/consent_records",
        "collection/users",
        "edge/has_consent",
    ]


def test_empty_sections_and_foreign_records_list_nothing():
    """An archive of empty sections is presence, not reach: it must print no member."""
    bundle = _bundle(("users", []), ("consent_records", [{"purpose": "someone else"}]), ("tasks", [{}]))
    assert export.observe([bundle], _subject()) == []


def test_markers_nested_in_lists_and_objects_are_found():
    bundle = _bundle(("tasks", [{"notes": {"history": ["x", "reach-seed:rsb:notes"]}}]))
    assert export.observe([bundle], _subject()) == ["collection/tasks"]


def test_an_edge_is_listed_only_when_its_target_row_arrived():
    bundle = _bundle(("users", [{"avatar_url": "reach-seed:reach-subject:avatar_url"}]))
    assert "edge/has_consent" not in export.observe([bundle], _subject())


def test_detail_mode_adds_per_section_counts_after_the_members():
    bundle = _bundle(("tasks", [{"name": "reach-seed:rsb:name"}, {"name": "other"}]))
    assert export.observe([bundle], _subject(), detail=True) == [
        "collection/tasks",
        "records/tasks=2",
        "recognised/tasks=1",
    ]


def test_a_missing_archive_is_printed_as_an_observation(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(export, "read_stack", lambda: {"storage_root": str(tmp_path)})
    monkeypatch.setattr(export, "read_subject", lambda _name: _subject())
    assert export.main(["--subject", "reach-subject"]) == 0
    assert capsys.readouterr().out == "archive/none\n"


def test_the_opened_archive_is_named_beside_its_members(monkeypatch, tmp_path, capsys):
    folder = tmp_path / "privacy" / "exports" / "reach-subject"
    folder.mkdir(parents=True)
    (folder / "exp1.json").write_text(
        '{"sections": [{"collection": "tasks", "records": [{"name": "reach-seed:rsb:name"}]}]}', encoding="utf-8"
    )
    monkeypatch.setattr(export, "read_stack", lambda: {"storage_root": str(tmp_path)})
    monkeypatch.setattr(export, "read_subject", lambda _name: _subject())
    assert export.main(["--subject", "reach-subject"]) == 0
    assert capsys.readouterr().out.splitlines() == ["collection/tasks", "archive/exp1.json"]


# ── observe_erasure_residue ────────────────────────────────────────────────


def test_residue_members_name_the_measured_condition_per_collection():
    measured = [
        residue.Residue("users", seeded=1, gone=1, changed=0, matching=0),
        residue.Residue("harvest_batches", seeded=1, gone=0, changed=1, matching=0),
        residue.Residue("invitations", seeded=2, gone=1, changed=1, matching=0),
        residue.Residue("consent_records", seeded=1, gone=0, changed=0, matching=1),
        # Untouched and unreferenced: nothing happened to it, so nothing is claimed.
        residue.Residue("tasks", seeded=1, gone=0, changed=0, matching=0),
    ]
    assert residue.members(measured, seeded_total=6) == [
        "residue/consent_records=1",
        "redacted/harvest_batches",
        "erased/invitations",
        "redacted/invitations",
        "erased/users",
        "seeded/6",
    ]


def test_a_collection_still_pointing_at_the_subject_is_never_erased_or_redacted():
    """Rows gone but a copy still names the subject: residue wins over the rows that went."""
    measured = [residue.Residue("notifications", seeded=1, gone=1, changed=0, matching=2)]
    assert residue.members(measured, seeded_total=1) == ["residue/notifications=2", "seeded/1"]


def test_the_output_is_never_empty():
    assert residue.members([], seeded_total=0) == ["seeded/0"]


class _RowStore:
    """Answers document reads from a dict and records the matching query's bind variables.

    It does not evaluate the AQL — it returns the count it was told to — so this
    test pins only what ``measure`` computes and sends, not what the query finds.
    """

    def __init__(self, documents: dict[str, dict[str, Any] | None], matching: dict[str, int]) -> None:
        self._documents = documents
        self._matching = matching
        self.sent: list[dict[str, Any]] = []

    def document(self, document_id: str) -> dict[str, Any] | None:
        return self._documents.get(document_id)

    def aql(self, _query: str, bind_vars: dict[str, Any]) -> list[int]:
        self.sent.append(bind_vars)
        return [self._matching.get(bind_vars["@collection"], 0)]


def test_measure_counts_gone_and_changed_rows_and_passes_every_gone_reference():
    subject = {
        "subject": "reach-subject",
        "rows": [
            {"id": "memberships/rsm", "key": "rsm", "rev": "r1", "collection": "memberships"},
            {"id": "tasks/rst", "key": "rst", "rev": "r1", "collection": "tasks"},
            {"id": "tasks/rsu", "key": "rsu", "rev": "r1", "collection": "tasks"},
        ],
    }
    store = _RowStore(
        {"memberships/rsm": None, "tasks/rst": {"_rev": "r2"}, "tasks/rsu": {"_rev": "r1"}},
        {"tasks": 0, "memberships": 0},
    )
    measured = {item.collection: item for item in residue.measure(store, subject)}
    assert measured["memberships"] == residue.Residue("memberships", 1, 1, 0, 0)
    assert measured["tasks"] == residue.Residue("tasks", 2, 0, 1, 0)
    # A row that references a removed row of the subject (by id or key) still
    # points at the subject; both spellings must reach the query.
    assert all(sent["gone"] == ["memberships/rsm", "rsm"] for sent in store.sent)
    assert all(sent["subject"] == "reach-subject" for sent in store.sent)


# ── observe_executing_inventory ────────────────────────────────────────────


def _marker(label: str, started: str) -> dict[str, Any]:
    return {"query": "RETURN @reach_marker", "bindVars": {"reach_marker": label}, "started": started}


def _log() -> list[dict[str, Any]]:
    return [
        {
            "query": "FOR d IN @@collection RETURN KEEP(d, @fields)",
            "bindVars": {"@collection": "users"},
            "started": "00",
        },
        _marker("reach-marker:export:begin", "01"),
        {
            "query": "FOR d IN @@collection FILTER d._key == @k RETURN KEEP(d, @fields)",
            "bindVars": {"@collection": "users", "k": "reach-subject"},
            "started": "02",
        },
        {
            "query": "FOR v IN 1..1 ANY @user_id @@edge FILTER PARSE_IDENTIFIER(v._id).collection == @collection "
            "RETURN KEEP(v, @fields)",
            "bindVars": {"@edge": "has_consent", "collection": "consent_records", "user_id": "users/x"},
            "started": "03",
        },
        # Bookkeeping in the window, no disclosure projection: not part of the walk.
        {
            "query": "FOR d IN data_export_requests UPDATE d WITH {} IN data_export_requests",
            "bindVars": {},
            "started": "04",
        },
        _marker("reach-marker:export:end", "05"),
        _marker("reach-marker:erasure:begin", "06"),
        {
            "query": "FOR d IN @@collection FILTER d[@field] == @value REMOVE d IN @@collection",
            "bindVars": {"@collection": "consent_records"},
            "started": "07",
        },
        {
            "query": "FOR d IN @@collection FILTER d._key == @value REMOVE d IN @@collection",
            "bindVars": {"@collection": "users"},
            "started": "08",
        },
        # A read inside the erasure window names a collection but writes nothing.
        {"query": "FOR d IN @@collection RETURN d", "bindVars": {"@collection": "has_consent"}, "started": "09"},
        _marker("reach-marker:erasure:end", "10"),
    ]


KNOWN = {"users", "consent_records", "has_consent", "data_export_requests"}


def test_an_inventory_is_listed_when_the_phase_named_every_declared_collection():
    declared = {
        "export-manifest": ["users", "consent_records", "has_consent"],
        "erasure-plan": ["users", "consent_records"],
    }
    assert inventory.observe(_log(), declared, KNOWN) == [
        "export-manifest",
        "erasure-plan",
        "executed/export=3",
        "executed/erasure=2",
    ]


def test_a_declared_collection_the_phase_did_not_touch_keeps_the_inventory_off_the_list():
    declared = {"export-manifest": ["users", "data_export_requests"], "erasure-plan": ["users", "has_consent"]}
    assert inventory.observe(_log(), declared, KNOWN, detail=True) == [
        "executed/export=3",
        "executed/erasure=2",
        "declared/export-manifest=2",
        "missing/export-manifest/data_export_requests",
        "declared/erasure-plan=2",
        "missing/erasure-plan/has_consent",
    ]


def test_queries_outside_the_markers_do_not_count():
    declared = {"export-manifest": ["users"], "erasure-plan": ["users"]}
    without_markers = [entry for entry in _log() if "reach_marker" not in entry["bindVars"]]
    assert inventory.observe(without_markers, declared, KNOWN) == ["executed/export=0", "executed/erasure=0"]


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ({"query": "FOR d IN tasks RETURN d", "bindVars": {}}, {"tasks"}),
        ({"query": "INSERT {} INTO notes", "bindVars": {}}, set()),  # not a collection of this database
        ({"query": "RETURN 1", "bindVars": {"@collection": "tasks", "value": "not-a-collection"}}, {"tasks"}),
    ],
)
def test_query_collections_reads_bind_parameters_bound_names_and_literal_names(entry, expected):
    assert inventory.query_collections(entry, {"tasks", "users"}) == expected


# ── observe_ranking_order ──────────────────────────────────────────────────

ranking = load_repo_script("reach/observe_ranking_order")


@pytest.fixture
def ranking_url(monkeypatch, tmp_path):
    (tmp_path / "ranking.url").write_text("http://ranking.invalid\n", encoding="utf-8")
    monkeypatch.setattr(ranking, "reach_dir", lambda: tmp_path)


def _answers(monkeypatch, orders: dict[str, list[int] | None]) -> None:
    monkeypatch.setattr(ranking, "ordering", lambda _url, query: orders[query])


def test_an_endpoint_that_ranks_each_query_correctly_counts_one(monkeypatch, ranking_url, capsys):
    _answers(monkeypatch, {query: order for query, order in ranking.CASES})
    assert ranking.main([]) == 0
    assert capsys.readouterr().out == "1\n"


def test_a_constant_answer_counts_zero(monkeypatch, ranking_url, capsys):
    """A stub that returns the same order for every query must not pass for a ranker."""
    _answers(monkeypatch, {query: [0, 1] for query, _order in ranking.CASES})
    assert ranking.main([]) == 0
    assert capsys.readouterr().out == "0\n"


def test_an_endpoint_that_never_answers_counts_zero_rather_than_staying_silent(monkeypatch, ranking_url, capsys):
    _answers(monkeypatch, {query: None for query, _order in ranking.CASES})
    assert ranking.main(["--deadline", "0"]) == 0
    assert capsys.readouterr().out == "0\n"


def test_the_two_cases_demand_opposite_orders():
    """If both cases wanted the same order, a constant answer would pass the probe."""
    (_first_query, first), (_second_query, second) = ranking.CASES
    assert first != second
