"""Unit tests for ArangoPlantDiaryRepository (REQ-013, REQ-050).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.

The REQ-050 half asserts the *storage contract* the analysis state machine
depends on — the compare-and-set flags of the claim write, and the shape of the
work-queue query. Both are things a service-level fake cannot prove: it would
only agree with itself.
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from arango.exceptions import DocumentRevisionError

from app.common.enums import DiaryAnalysisState
from app.common.exceptions import DiaryAnalysisConcurrentUpdateError
from app.data_access.arango import collections as col
from app.data_access.arango.plant_diary_repository import (
    ArangoPlantDiaryRepository,
    analysis_state_bind_values,
    stored_states_for_display,
)
from app.domain.interfaces.plant_diary_repository import DiaryOverviewFilter
from app.domain.models.plant_diary_entry import PlantDiaryEntry


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoPlantDiaryRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {"_key": "d1", "plant_key": "p1", "entry_type": "note", "text": "looks healthy"}
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> PlantDiaryEntry:
    defaults = {"entry_type": "note", "text": "looks healthy", "plant_key": "p1"}
    defaults.update(kwargs)
    return PlantDiaryEntry(**defaults)


class TestCreate:
    def test_creates_entry_and_plant_edge(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(_model())

        assert isinstance(result, PlantDiaryEntry)
        # entry doc insert + has_diary_entry edge
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "plant_instances/p1"
        assert edge["_to"] == "plant_diary_entries/d1"

    def test_skips_edge_without_plant_key(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(plant_key="")}

        repo.create(_model(plant_key=""))

        assert coll.insert.call_count == 1


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("d1"), PlantDiaryEntry)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("d1") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(text="updated")}

        result = repo.update("d1", _model(text="updated"))

        assert result.text == "updated"


class TestDelete:
    def test_removes_edges_then_deletes(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("d1") is True
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {
            "@edge": "has_diary_entry",
            "vertex": "plant_diary_entries/d1",
        }
        mock_db.collection.return_value.delete.assert_called_once_with("d1")


class TestGetByPlant:
    def test_returns_entries_and_total(self, repo, mock_db):
        # First execute = count, second = list of entries.
        mock_db.aql.execute.side_effect = [iter([3]), iter([_doc()])]

        entries, total = repo.get_by_plant("p1", tenant_key="tenant-a", offset=0, limit=10)

        assert total == 3
        assert len(entries) == 1
        assert isinstance(entries[0], PlantDiaryEntry)
        # Count query binds the plant_id.
        count_call = mock_db.aql.execute.call_args_list[0]
        assert count_call.kwargs["bind_vars"] == {"plant_id": "plant_instances/p1", "tenant_key": "tenant-a"}

    def test_empty_count_yields_zero(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]

        entries, total = repo.get_by_plant("p1", tenant_key="tenant-a")

        assert total == 0
        assert entries == []

    def test_both_queries_filter_on_the_tenant(self, repo, mock_db):
        """SEC-002 — the entry point is an edge, the predicate must be on the entry.

        ``has_diary_entry`` is traversed from ``plant_instances/{plant_key}``,
        and ``plant_key`` arrives from the URL. Without a ``tenant_key``
        predicate on the *target document* the read returns whatever hangs off
        the named plant — which is how a member of one tenant read another
        tenant's diary in full.

        The count is asserted alongside the page on purpose: a ``total`` taken
        with a wider filter than the page reports rows the caller may never see
        and leaks their number.
        """
        mock_db.aql.execute.side_effect = [iter([1]), iter([_doc()])]

        repo.get_by_plant("p1", tenant_key="tenant-a")

        count_query, page_query = (call.args[0] for call in mock_db.aql.execute.call_args_list)
        for query in (count_query, page_query):
            assert "entry.tenant_key == @tenant_key" in query
        for call in mock_db.aql.execute.call_args_list:
            assert call.kwargs["bind_vars"]["tenant_key"] == "tenant-a"

    def test_an_empty_tenant_key_is_refused_rather_than_read_as_every_tenant(self, repo, mock_db):
        with pytest.raises(ValueError, match="tenant"):
            repo.get_by_plant("p1", tenant_key="")

        mock_db.aql.execute.assert_not_called()


class TestGetByRun:
    def test_returns_context_dicts_with_serialized_entry(self, repo, mock_db):
        row = {
            "plant_key": "p1",
            "plant_id": "PL-001",
            "plant_name": "Tomate #1",
            "diary_entry": _doc(),
        }
        mock_db.aql.execute.side_effect = [iter([1]), iter([row])]

        results, total = repo.get_by_run("run1", tenant_key="tenant-a", offset=0, limit=10)

        assert total == 1
        assert len(results) == 1
        assert results[0]["plant_key"] == "p1"
        # The diary_entry was round-tripped through PlantDiaryEntry serialisation.
        assert results[0]["diary_entry"]["text"] == "looks healthy"
        count_call = mock_db.aql.execute.call_args_list[0]
        assert count_call.kwargs["bind_vars"]["run_id"] == "planting_runs/run1"

    def test_row_without_entry_is_passed_through(self, repo, mock_db):
        row = {"plant_key": "p1", "plant_id": "PL-001", "plant_name": "Tomate", "diary_entry": None}
        mock_db.aql.execute.side_effect = [iter([0]), iter([row])]

        results, total = repo.get_by_run("run1", tenant_key="tenant-a")

        assert total == 0
        assert results[0]["diary_entry"] is None

    def test_both_queries_filter_on_the_tenant(self, repo, mock_db):
        # SEC-002, same shape one edge further out: the aggregation enters
        # through ``run_contains`` and selected entry documents without ever
        # naming a tenant.
        mock_db.aql.execute.side_effect = [iter([1]), iter([])]

        repo.get_by_run("run1", tenant_key="tenant-a")

        for call in mock_db.aql.execute.call_args_list:
            assert "entry.tenant_key == @tenant_key" in call.args[0]
            assert call.kwargs["bind_vars"]["tenant_key"] == "tenant-a"

    def test_an_empty_tenant_key_is_refused(self, repo, mock_db):
        with pytest.raises(ValueError, match="tenant"):
            repo.get_by_run("run1", tenant_key="")

        mock_db.aql.execute.assert_not_called()


# ── REQ-050 analysis ─────────────────────────────────────────────────────────


class TestUpdateFieldsChecked:
    """The compare-and-set behind ``claim_diary_analysis`` (REQ-050 §2.2)."""

    def test_sends_the_expected_revision_and_the_three_flags(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(_rev="rev-2", analysis_claimed_by="agent-a")}

        entry, new_rev = repo.update_fields_checked(
            "d1", {"analysis_claimed_by": "agent-a", "analysis_lease_expires_at": None}, expected_rev="rev-1"
        )

        payload = coll.update.call_args.args[0]
        kwargs = coll.update.call_args.kwargs
        assert payload["_key"] == "d1"
        assert payload["_rev"] == "rev-1", "without the read revision there is no fencing at all"
        # keep_none: this is the only way a lease can be cleared — the
        # full-model path drops None (exclude_none=True) and would leave the
        # previous holder's name on the document.
        assert payload["analysis_lease_expires_at"] is None
        assert kwargs["check_rev"] is True
        assert kwargs["keep_none"] is True
        # merge=False: a re-analysis replaces the stored `analysis` object
        # wholesale instead of merging into the previous findings (AK-21).
        assert kwargs["merge"] is False
        assert isinstance(entry, PlantDiaryEntry)
        assert new_rev == "rev-2"

    def test_revision_mismatch_becomes_a_concurrent_update_error(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.side_effect = DocumentRevisionError(MagicMock(status_code=412, error_code=1200), MagicMock())

        with pytest.raises(DiaryAnalysisConcurrentUpdateError) as exc:
            repo.update_fields_checked("d1", {"analysis_state": "in_progress"}, expected_rev="stale")

        assert exc.value.error_code == "conflict.concurrent_update"

    def test_reserved_attributes_cannot_be_smuggled_in(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(_rev="rev-2")}

        repo.update_fields_checked(
            "d1", {"_key": "other", "_id": "x/other", "analysis_state": "requested"}, expected_rev="rev-1"
        )

        payload = coll.update.call_args.args[0]
        assert payload["_key"] == "d1"  # never redirected onto another document
        assert "_id" not in payload


class TestGetWithRevision:
    def test_returns_entry_and_revision(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc(_rev="rev-7")

        loaded = repo.get_with_revision("d1")

        assert loaded is not None
        entry, rev = loaded
        assert isinstance(entry, PlantDiaryEntry)
        assert rev == "rev-7"

    def test_missing_entry_returns_none(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None

        assert repo.get_with_revision("d1") is None


class TestAnalysisStateBindValues:
    def test_none_also_matches_a_missing_attribute(self):
        # In AQL a missing attribute is null and never equals the string
        # "none". Without the null in the bound list a "not marked" filter
        # silently skips every entry written before REQ-050 (AK-26).
        assert analysis_state_bind_values([DiaryAnalysisState.NONE]) == ["none", None]

    def test_other_states_are_passed_through_unchanged(self):
        assert analysis_state_bind_values([DiaryAnalysisState.COMPLETED, "failed"]) == ["completed", "failed"]


class TestListPendingAnalyses:
    def test_filters_tenant_first_and_binds_the_states(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([3]), iter([_doc(analysis_state="requested")])]

        entries, total = repo.list_pending_analyses("tenant-a", limit=20, include_stale=True)

        assert total == 3
        assert isinstance(entries[0], PlantDiaryEntry)
        query = mock_db.aql.execute.call_args_list[1].args[0]
        bind_vars = mock_db.aql.execute.call_args_list[1].kwargs["bind_vars"]
        # The index is (tenant_key, analysis_state, analysis_requested_at) — it
        # is only used when tenant_key filters first, by equality.
        assert query.index("doc.tenant_key == @tenant_key") < query.index("doc.analysis_state IN @states")
        assert "SORT doc.analysis_requested_at ASC" in query
        assert "LIMIT @limit" in query
        assert bind_vars["states"] == ["requested", "in_progress"]
        assert bind_vars["tenant_key"] == "tenant-a"
        # An OR on the indexed attribute would break the index; the staleness
        # test is a follow-up predicate on the lease instead.
        assert "OR doc.analysis_state == null" not in query

    def test_include_stale_off_asks_only_for_requested(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]

        repo.list_pending_analyses("tenant-a", include_stale=False)

        query = mock_db.aql.execute.call_args_list[1].args[0]
        bind_vars = mock_db.aql.execute.call_args_list[1].kwargs["bind_vars"]
        assert bind_vars["states"] == ["requested"]
        assert "analysis_lease_expires_at" not in query

    def test_stale_predicate_binds_the_current_moment(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]
        moment = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)

        repo.list_pending_analyses("tenant-a", now=moment)

        bind_vars = mock_db.aql.execute.call_args_list[1].kwargs["bind_vars"]
        assert bind_vars["now"] == moment.isoformat()

    def test_count_query_ignores_the_limit(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([137]), iter([])]

        _entries, total = repo.list_pending_analyses("tenant-a", limit=20)

        count_query = mock_db.aql.execute.call_args_list[0].args[0]
        assert "LIMIT" not in count_query
        assert total == 137

    def test_empty_tenant_key_is_refused(self, repo):
        with pytest.raises(ValueError, match="tenant"):
            repo.list_pending_analyses("")


class TestStoredStatesForDisplay:
    def test_requested_also_asks_for_in_progress(self):
        # An expired lease is stored ``in_progress`` and displays as
        # ``requested``. Without the widening the index pre-selection drops
        # exactly the entries a crashed agent left behind (AK-06).
        assert stored_states_for_display([DiaryAnalysisState.REQUESTED]) == [
            DiaryAnalysisState.IN_PROGRESS,
            DiaryAnalysisState.REQUESTED,
        ]

    def test_other_states_are_not_widened(self):
        assert stored_states_for_display([DiaryAnalysisState.COMPLETED]) == [DiaryAnalysisState.COMPLETED]


def _list_call(mock_db) -> tuple[str, dict]:
    """Query text and bind vars of the *page* query (the second execute)."""
    call = mock_db.aql.execute.call_args_list[1]
    return call.args[0], call.kwargs["bind_vars"]


class TestListOverview:
    def test_expands_none_into_the_bound_values(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([1]), iter([_doc()])]

        entries, total = repo.list_overview("tenant-a", DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.NONE,)))

        _query, bind_vars = _list_call(mock_db)
        assert bind_vars["states"] == ["none", None]
        assert total == 1
        assert isinstance(entries[0], PlantDiaryEntry)

    def test_tenant_filters_first_so_the_index_is_reachable(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]

        repo.list_overview(
            "tenant-a",
            DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.COMPLETED,), plant_key="p1", search="flecken"),
        )

        query, _bind_vars = _list_call(mock_db)
        # The index is (tenant_key, analysis_state, analysis_requested_at); it is
        # only usable when tenant_key is an equality on the leading attribute and
        # the state predicate follows it.
        assert query.index("doc.tenant_key == @tenant_key") < query.index("doc.analysis_state IN @states")
        # An OR on the indexed attribute would break the index; the null case of
        # a pre-REQ-050 document rides in the bound value list instead.
        assert "OR doc.analysis_state == null" not in query

    def test_requested_filter_widens_to_stored_states_and_narrows_by_lease(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]
        moment = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)

        repo.list_overview(
            "tenant-a",
            DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.REQUESTED,)),
            now=moment,
        )

        query, bind_vars = _list_call(mock_db)
        assert bind_vars["states"] == ["in_progress", "requested"]
        assert bind_vars["displayed_states"] == ["requested"]
        assert bind_vars["now"] == moment.isoformat()
        # The narrowing happens inside the query, so ``total`` counts the same
        # set the page is taken from.
        assert "FILTER displayed_analysis_state IN @displayed_states" in query
        assert "doc.analysis_lease_expires_at <= @now" in query

    def test_no_state_filter_emits_no_state_predicate(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]

        repo.list_overview("tenant-a")

        query, bind_vars = _list_call(mock_db)
        assert "analysis_state" not in query
        assert "states" not in bind_vars

    def test_a_filter_naming_every_state_excludes_nothing(self, repo, mock_db):
        # Asking for all five states is the same question as asking for none of
        # them. Emitting the IN anyway would turn one index range into six.
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]

        repo.list_overview("tenant-a", DiaryOverviewFilter(analysis_states=tuple(DiaryAnalysisState)))

        query, _bind_vars = _list_call(mock_db)
        assert "analysis_state" not in query

    def test_every_filter_of_the_parameter_table_reaches_the_query(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]

        repo.list_overview(
            "tenant-a",
            DiaryOverviewFilter(
                plant_key="p1",
                species_key="solanum_lycopersicum",
                entry_type="problem",
                tag="Blatt",
                created_from=date(2026, 7, 10),
                created_to=date(2026, 7, 31),
                search="flecken",
            ),
        )

        query, bind_vars = _list_call(mock_db)
        assert bind_vars["plant_key"] == "p1"
        assert bind_vars["entry_type"] == "problem"
        assert bind_vars["tag"] == "blatt"  # matched case-insensitively
        assert bind_vars["species_key"] == "solanum_lycopersicum"
        assert bind_vars["search"] == "%flecken%"
        # Inclusive day range in UTC, upper bound exclusive at the next midnight.
        assert bind_vars["created_from"] == int(datetime(2026, 7, 10, tzinfo=UTC).timestamp() * 1000)
        assert bind_vars["created_before"] == int(datetime(2026, 8, 1, tzinfo=UTC).timestamp() * 1000)
        assert f'DOCUMENT("{col.PLANT_INSTANCES}", doc.plant_key)' in query
        assert "overview_plant.species_key == @species_key" in query
        # The species join is tenant-scoped as well — an entry may not borrow a
        # foreign tenant's plant to pass the filter.
        assert "overview_plant.tenant_key == @tenant_key" in query

    def test_search_wildcards_are_escaped(self, repo, mock_db):
        # Without escaping, a term of "%" matches every entry and "_" matches any
        # single character: the search would answer a different question than the
        # one asked, and look like a working search while doing it.
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]

        repo.list_overview("tenant-a", DiaryOverviewFilter(search="100%_rein"))

        _query, bind_vars = _list_call(mock_db)
        assert bind_vars["search"] == "%100\\%\\_rein%"

    def test_count_query_runs_the_same_filters_without_paging(self, repo, mock_db):
        # ``total`` must describe the same set as ``items`` — a second, hand-kept
        # filter list is how the two drift apart.
        mock_db.aql.execute.side_effect = [iter([137]), iter([])]

        _entries, total = repo.list_overview(
            "tenant-a", DiaryOverviewFilter(entry_type="problem"), offset=100, limit=50
        )

        count_query = mock_db.aql.execute.call_args_list[0].args[0]
        page_query, _bind_vars = _list_call(mock_db)
        assert total == 137
        assert "LIMIT" not in count_query
        assert "COLLECT WITH COUNT INTO cnt" in count_query
        shared = page_query.split("SORT ")[0]
        assert count_query.startswith(shared)

    def test_default_sort_is_created_at_descending_with_a_tiebreaker(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]

        repo.list_overview("tenant-a")

        query, bind_vars = _list_call(mock_db)
        assert "SORT doc.created_at DESC, doc._key DESC" in query
        assert "LIMIT @offset, @limit" in query
        assert bind_vars["offset"] == 0
        assert bind_vars["limit"] == 50

    def test_sort_by_analyzed_at_reaches_into_the_nested_result(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([0]), iter([])]

        repo.list_overview("tenant-a", DiaryOverviewFilter(sort="analyzed_at"))

        query, _bind_vars = _list_call(mock_db)
        assert "SORT doc.analysis.analyzed_at DESC" in query

    def test_empty_tenant_key_is_refused(self, repo):
        with pytest.raises(ValueError, match="tenant"):
            repo.list_overview("", DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.COMPLETED,)))
