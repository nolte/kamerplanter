"""REQ-050 §2.5.2 — the overview query against a real ArangoDB.

**Why this file exists next to the router tests.** Every other test of the
overview runs against an in-memory double. A double can prove that the *router*
asks the right question, but not one thing about the answer it would get from
ArangoDB: not that the AQL parses, not that ``LIKE`` escapes what the SSOT
escaper escaped, not that ``DATE_TIMESTAMP`` reads the stored spelling of a
timestamp, and above all not that the persistent index
``(tenant_key, analysis_state, analysis_requested_at)`` is still reached once
seven more predicates hang off the same ``FOR`` loop. An index the query misses
costs write throughput and buys nothing — and nothing in a unit test would say so.

Skipped when no ArangoDB answers on ``localhost:8529``. Run it with::

    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_diary_overview_query.py -v
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.common.enums import DiaryAnalysisState
from app.data_access.arango import collections as col
from app.data_access.arango.plant_diary_repository import ArangoPlantDiaryRepository
from app.domain.interfaces.plant_diary_repository import DiaryOverviewFilter

ARANGO_URL = "http://localhost:8529"
ARANGO_PASSWORD = "rootpassword"
TEST_DATABASE = "kamerplanter_diary_overview_test"

TENANT = "tenant-a"
FOREIGN_TENANT = "tenant-b"

#: The index this query must keep reaching (migration ``v0033``).
INDEX_FIELDS = ["tenant_key", "analysis_state", "analysis_requested_at"]

ARANGO_AVAILABLE = False
try:  # pragma: no cover - probe, not behaviour
    from arango import ArangoClient

    _probe = ArangoClient(hosts=ARANGO_URL)
    _probe.db("_system", username="root", password=ARANGO_PASSWORD).version()
    ARANGO_AVAILABLE = True
    _probe.close()
except Exception:  # noqa: BLE001 - any failure means "not available"
    pass

pytestmark = pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB not available on localhost:8529")

NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)

ANALYSIS = {
    "summary": "Vermutlich Staunässe.",
    "findings": [],
    "recommended_actions": [],
    "analyzed_photo_ids": [],
    "model": "claude-opus-5",
    "recipe_version": "1.0.0",
    "analyzed_at": "2026-08-04T07:14:52+00:00",
    "disclaimer": "Hypothese.",
}


def _entry(key: str, **fields) -> dict:
    doc = {
        "_key": key,
        "tenant_key": TENANT,
        "plant_key": "plant-1",
        "entry_type": "note",
        "title": "Notiz",
        "text": "Alles ruhig.",
        "tags": [],
        "photo_refs": [],
        "created_by": "user-author",
        "created_at": "2026-07-15T08:00:00+00:00",
        "updated_at": "2026-07-15T08:00:00+00:00",
        "analysis_state": DiaryAnalysisState.NONE.value,
    }
    doc.update(fields)
    return doc


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username="root", password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username="root", password=ARANGO_PASSWORD)

    entries = database.create_collection(col.PLANT_DIARY_ENTRIES)
    # The index under test — the same definition ``collections.py`` bootstraps
    # and migration v0033 backfills.
    entries.add_index({"type": "persistent", "fields": INDEX_FIELDS, "unique": False})
    plants = database.create_collection(col.PLANT_INSTANCES)

    plants.insert({"_key": "plant-1", "tenant_key": TENANT, "species_key": "solanum_lycopersicum"})
    plants.insert({"_key": "plant-2", "tenant_key": TENANT, "species_key": "ocimum_basilicum"})

    entries.insert(
        _entry(
            "old",
            title="Umtopfen",
            text="Substrat gewechselt.",
            entry_type="observation",
            tags=["Substrat"],
            created_at="2026-07-01T08:00:00+00:00",
        )
    )
    entries.insert(
        _entry(
            "mid",
            plant_key="plant-2",
            title="Blattflecken",
            text="Braune Flecken unten.",
            entry_type="problem",
            tags=["blatt"],
            created_at="2026-07-15T08:00:00+00:00",
            analysis_state=DiaryAnalysisState.COMPLETED.value,
            analysis=ANALYSIS,
        )
    )
    entries.insert(
        _entry(
            "new",
            title="Erste Blüte",
            text="Sieht gut aus.",
            entry_type="milestone",
            created_at="2026-08-01T08:00:00+00:00",
        )
    )
    # Stored in_progress, lease long gone → displays (and filters) as requested.
    entries.insert(
        _entry(
            "stale",
            title="Beansprucht",
            text="Von einem abgestürzten Agenten gehalten.",
            created_at="2026-08-02T08:00:00+00:00",
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_by="goose-laptop",
            analysis_lease_expires_at="2026-08-02T09:00:00+00:00",
        )
    )
    # Stored in_progress with a live lease → stays in_progress.
    entries.insert(
        _entry(
            "held",
            title="In Arbeit",
            text="Läuft gerade.",
            created_at="2026-08-03T08:00:00+00:00",
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_by="goose-laptop",
            analysis_lease_expires_at="2026-08-06T09:00:00+00:00",
        )
    )
    # AK-26: written before REQ-050, carries no analysis_state attribute at all.
    legacy = _entry("legacy", title="Alt", text="Vor REQ-050 geschrieben.", created_at="2026-06-01T08:00:00+00:00")
    legacy.pop("analysis_state")
    entries.insert(legacy)
    # Wildcard bait for the free-text search.
    entries.insert(_entry("percent", title="Rabatt", text="100% Bio.", created_at="2026-06-02T08:00:00+00:00"))
    entries.insert(_entry("underscore", title="Codename", text="Beet_A.", created_at="2026-06-03T08:00:00+00:00"))
    # Another tenant's entry — must never appear.
    entries.insert(_entry("foreign", tenant_key=FOREIGN_TENANT, text="Fremde Notiz."))

    yield database

    system.delete_database(TEST_DATABASE)
    client.close()


@pytest.fixture
def repo(db):
    return ArangoPlantDiaryRepository(db)


def _keys(result: tuple[list, int]) -> list[str]:
    entries, _total = result
    return [entry.key for entry in entries]


class TestOverviewFiltersAgainstArangoDB:
    """One test per parameter of the §2.5.2 table, then combinations."""

    def test_unfiltered_lists_only_the_tenant_newest_first(self, repo):
        entries, total = repo.list_overview(TENANT, now=NOW)

        assert total == 8
        assert "foreign" not in [entry.key for entry in entries]
        # created_at descending: 2026-08-03, 2026-08-02, 2026-08-01.
        assert [entry.key for entry in entries][:3] == ["held", "stale", "new"]

    def test_filter_by_plant(self, repo):
        assert _keys(repo.list_overview(TENANT, DiaryOverviewFilter(plant_key="plant-2"), now=NOW)) == ["mid"]

    def test_filter_by_species_joins_the_plant(self, repo):
        result = repo.list_overview(TENANT, DiaryOverviewFilter(species_key="ocimum_basilicum"), now=NOW)

        assert _keys(result) == ["mid"]
        assert result[1] == 1

    def test_filter_by_entry_type(self, repo):
        assert _keys(repo.list_overview(TENANT, DiaryOverviewFilter(entry_type="problem"), now=NOW)) == ["mid"]

    def test_filter_by_tag_is_case_insensitive(self, repo):
        # Stored "Substrat", asked for "substrat".
        assert _keys(repo.list_overview(TENANT, DiaryOverviewFilter(tag="substrat"), now=NOW)) == ["old"]

    def test_filter_by_date_range_is_inclusive_on_both_days(self, repo):
        result = repo.list_overview(
            TENANT,
            DiaryOverviewFilter(created_from=date(2026, 7, 1), created_to=date(2026, 7, 15)),
            now=NOW,
        )

        assert _keys(result) == ["mid", "old"]

    def test_free_text_search_covers_title_and_text(self, repo):
        assert _keys(repo.list_overview(TENANT, DiaryOverviewFilter(search="blattflecken"), now=NOW)) == ["mid"]
        assert _keys(repo.list_overview(TENANT, DiaryOverviewFilter(search="sieht gut"), now=NOW)) == ["new"]

    def test_search_wildcards_match_literally(self, repo):
        # Unescaped these two terms would match all eight entries.
        assert _keys(repo.list_overview(TENANT, DiaryOverviewFilter(search="%"), now=NOW)) == ["percent"]
        assert _keys(repo.list_overview(TENANT, DiaryOverviewFilter(search="_"), now=NOW)) == ["underscore"]

    def test_sort_by_analyzed_at_puts_the_analysed_entry_first(self, repo):
        entries, total = repo.list_overview(TENANT, DiaryOverviewFilter(sort="analyzed_at"), now=NOW)

        assert entries[0].key == "mid"
        assert total == 8

    def test_two_filters_combine_conjunctively(self, repo):
        alone_type = repo.list_overview(TENANT, DiaryOverviewFilter(entry_type="note"), now=NOW)[1]
        alone_range = repo.list_overview(TENANT, DiaryOverviewFilter(created_from=date(2026, 8, 1)), now=NOW)[1]
        both = repo.list_overview(
            TENANT,
            DiaryOverviewFilter(entry_type="note", created_from=date(2026, 8, 1)),
            now=NOW,
        )

        assert alone_type == 5
        assert alone_range == 3
        assert _keys(both) == ["held", "stale"]
        assert both[1] == 2

    def test_the_free_text_or_does_not_swallow_the_other_filters(self, repo):
        # The search is the one clause with an ``OR`` in it (title or text). If
        # AQL bound it looser than the neighbouring filters, ``(title OR text)
        # AND plant`` would collapse into ``title OR (text AND plant)`` and the
        # search would silently ignore every other filter.
        assert _keys(repo.list_overview(TENANT, DiaryOverviewFilter(search="e"), now=NOW)) != ["mid"]
        result = repo.list_overview(
            TENANT,
            DiaryOverviewFilter(search="e", plant_key="plant-2"),
            now=NOW,
        )

        assert _keys(result) == ["mid"]
        assert result[1] == 1

    def test_state_and_species_combine(self, repo):
        result = repo.list_overview(
            TENANT,
            DiaryOverviewFilter(
                analysis_states=(DiaryAnalysisState.COMPLETED,),
                species_key="ocimum_basilicum",
            ),
            now=NOW,
        )

        assert _keys(result) == ["mid"]


class TestDisplayedStateAgainstArangoDB:
    def test_requested_finds_the_entry_whose_lease_ran_out(self, repo):
        # Stored ``in_progress``, lease expired 2026-08-02 09:00 → back in the
        # queue and displayed as ``requested`` (AK-06). A filter that asked the
        # database for the stored value alone would hide it.
        result = repo.list_overview(
            TENANT, DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.REQUESTED,)), now=NOW
        )

        assert _keys(result) == ["stale"]
        assert result[1] == 1

    def test_in_progress_finds_only_the_live_lease(self, repo):
        result = repo.list_overview(
            TENANT, DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.IN_PROGRESS,)), now=NOW
        )

        assert _keys(result) == ["held"]

    def test_the_same_entry_flips_when_the_lease_expires(self, repo):
        before = repo.list_overview(
            TENANT,
            DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.IN_PROGRESS,)),
            now=NOW,
        )
        after = repo.list_overview(
            TENANT,
            DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.REQUESTED,)),
            now=NOW + timedelta(days=7),
        )

        assert _keys(before) == ["held"]
        assert sorted(_keys(after)) == ["held", "stale"]

    def test_none_finds_the_pre_req050_entry_without_the_attribute(self, repo):
        # AK-26 — a missing attribute is null in AQL, never the string "none".
        result = repo.list_overview(TENANT, DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.NONE,)), now=NOW)

        assert "legacy" in _keys(result)
        assert result[1] == 5

    def test_completed_excludes_everything_else(self, repo):
        spec = DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.COMPLETED,))

        assert _keys(repo.list_overview(TENANT, spec, now=NOW)) == ["mid"]


class TestTotalAndPagingAgainstArangoDB:
    def test_total_is_the_whole_match_count_not_the_page_length(self, repo):
        entries, total = repo.list_overview(TENANT, limit=2, now=NOW)

        assert len(entries) == 2
        assert total == 8

    def test_paging_walks_the_whole_set_exactly_once(self, repo):
        seen: list[str] = []
        for offset in range(0, 10, 3):
            entries, total = repo.list_overview(TENANT, offset=offset, limit=3, now=NOW)
            assert total == 8
            seen.extend(entry.key or "" for entry in entries)

        assert sorted(seen) == sorted(["old", "mid", "new", "stale", "held", "legacy", "percent", "underscore"])

    def test_total_of_a_filtered_query_counts_only_the_matches(self, repo):
        _entries, total = repo.list_overview(TENANT, DiaryOverviewFilter(entry_type="note"), limit=1, now=NOW)

        assert total == 5


class TestIndexUsage:
    """The proof that the extra predicates did not cost the index.

    ``explain`` is asserted rather than inspected by hand because the failure is
    invisible otherwise: a query that stopped using the index returns exactly the
    same rows, just by reading every document of the collection.
    """

    @staticmethod
    def _plan(repo, filters, **kwargs):
        body, bind_vars = repo._overview_body(TENANT, filters, now=NOW)
        query = f"{body} SORT doc.created_at DESC, doc._key DESC LIMIT @offset, @limit RETURN doc"
        return repo._db.aql.explain(query, bind_vars={**bind_vars, "offset": 0, "limit": 50, **kwargs})

    @staticmethod
    def _index_nodes(plan) -> list[dict]:
        nodes = plan["nodes"] if isinstance(plan, dict) and "nodes" in plan else plan["plan"]["nodes"]
        return [node for node in nodes if node["type"] == "IndexNode"]

    @staticmethod
    def _node_types(plan) -> list[str]:
        nodes = plan["nodes"] if isinstance(plan, dict) and "nodes" in plan else plan["plan"]["nodes"]
        return [node["type"] for node in nodes]

    def test_tenant_only_query_uses_the_persistent_index(self, repo):
        plan = self._plan(repo, DiaryOverviewFilter())

        index_nodes = self._index_nodes(plan)
        assert index_nodes, f"no IndexNode in plan: {self._node_types(plan)}"
        assert index_nodes[0]["indexes"][0]["fields"] == INDEX_FIELDS
        assert "EnumerateCollectionNode" not in self._node_types(plan)

    def test_state_filtered_query_uses_the_persistent_index(self, repo):
        plan = self._plan(repo, DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.COMPLETED,)))

        index_nodes = self._index_nodes(plan)
        assert index_nodes, f"no IndexNode in plan: {self._node_types(plan)}"
        assert index_nodes[0]["indexes"][0]["fields"] == INDEX_FIELDS
        assert "EnumerateCollectionNode" not in self._node_types(plan)

    def test_all_filters_together_still_use_the_persistent_index(self, repo):
        # The question this work package had to answer: do seven additional
        # predicates plus a join push the read off the index? They do not — they
        # are applied to the rows the index already produced.
        plan = self._plan(
            repo,
            DiaryOverviewFilter(
                analysis_states=(DiaryAnalysisState.REQUESTED, DiaryAnalysisState.COMPLETED),
                plant_key="plant-1",
                species_key="solanum_lycopersicum",
                entry_type="note",
                tag="substrat",
                created_from=date(2026, 7, 1),
                created_to=date(2026, 8, 31),
                search="flecken",
            ),
        )

        index_nodes = self._index_nodes(plan)
        assert index_nodes, f"no IndexNode in plan: {self._node_types(plan)}"
        assert index_nodes[0]["indexes"][0]["fields"] == INDEX_FIELDS
        assert "EnumerateCollectionNode" not in self._node_types(plan)

    def test_the_count_query_uses_the_index_too(self, repo):
        # ``total`` runs its own statement; an index that only the page query
        # reaches would still make every request a full scan.
        body, bind_vars = repo._overview_body(TENANT, DiaryOverviewFilter(entry_type="note"), now=NOW)
        plan = repo._db.aql.explain(f"{body} COLLECT WITH COUNT INTO cnt RETURN cnt", bind_vars=bind_vars)

        index_nodes = self._index_nodes(plan)
        assert index_nodes, f"no IndexNode in plan: {self._node_types(plan)}"
        assert index_nodes[0]["indexes"][0]["fields"] == INDEX_FIELDS
