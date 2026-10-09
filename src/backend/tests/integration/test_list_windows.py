"""MT-035 (#2131) — the windowed list reads, on a real ArangoDB.

The route tests (``tests/api/test_list_route_windows.py``) prove the window reaches
the service. Only the server can answer whether the repository then reads *that*
window: the keyset cursor walks a tenant's rows in ``_key`` order without
repeating or skipping one and never crosses into another tenant, ``list_window``
issues no count query, and an ordered window over a non-unique sort value
(``created_at``, ``due_date``) is a total order a pager can walk.

Run with: pytest tests/integration/test_list_windows.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch

import pytest
from arango.aql import AQL

from app.data_access.arango import collections as col
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("MT-035 measures the windowed list reads on a real ArangoDB"),
]

_DB_NAME = run_database_name("list_windows")
_A = "tenant-a"
_B = "tenant-b"
_SAME_SECOND = "2026-10-05T12:00:00+00:00"


@pytest.fixture(scope="module")
def db():
    monkeypatch = pytest.MonkeyPatch()
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    try:
        yield database
    finally:
        monkeypatch.undo()
        system.delete_database(_DB_NAME)


def _walk_by_cursor(read, limit: int) -> list[str]:
    keys: list[str] = []
    after = None
    for _ in range(100):
        page = read(after=after, limit=limit)
        if not page:
            return keys
        assert len(page) <= limit
        keys.extend(row.key for row in page)
        after = page[-1].key
    raise AssertionError("the cursor never reached an empty page")


@pytest.mark.parametrize(
    ("repo_path", "collection", "row"),
    [
        (
            "app.data_access.arango.plant_instance_repository.ArangoPlantInstanceRepository",
            col.PLANT_INSTANCES,
            {"species_key": "sp", "planted_on": "2026-01-01"},
        ),
        (
            "app.data_access.arango.feeding_repository.ArangoFeedingRepository",
            col.FEEDING_EVENTS,
            {"plant_key": "p", "volume_applied_liters": 1.0},
        ),
        (
            "app.data_access.arango.watering_repository.ArangoWateringRepository",
            col.WATERING_EVENTS,
            {"plant_keys": ["p"], "volume_liters": 1.0},
        ),
        (
            "app.data_access.arango.watering_log_repository.ArangoWateringLogRepository",
            col.WATERING_LOGS,
            {"plant_keys": ["p"], "volume_liters": 1.0},
        ),
    ],
    ids=["plant_instances", "feeding_events", "watering_events", "watering_logs"],
)
def test_the_cursor_walks_one_tenant_exactly_once(db, repo_path: str, collection: str, row: dict) -> None:
    module, _, name = repo_path.rpartition(".")
    repo = getattr(__import__(module, fromlist=[name]), name)(db)
    db.collection(collection).truncate()
    # Interleaved keys: the other tenant's rows sit *between* tenant A's in _key order.
    docs = []
    for i in range(23):
        tenant = _A if i % 3 else _B
        docs.append({"_key": f"k{i:03d}", "tenant_key": tenant, "instance_id": f"I{i}", **row})
    db.collection(collection).insert_many(docs)
    own = sorted(d["_key"] for d in docs if d["tenant_key"] == _A)

    walked = _walk_by_cursor(lambda after, limit: repo.list_window(tenant_key=_A, limit=limit, after=after), 4)

    assert walked == own
    by_offset = [r.key for off in range(0, len(own), 4) for r in repo.list_window(tenant_key=_A, offset=off, limit=4)]
    assert by_offset == own
    # A cursor naming the other tenant's row still answers only tenant A's rows after it.
    assert [r.key for r in repo.list_window(tenant_key=_A, after="k009", limit=50)] == [k for k in own if k > "k009"]


def test_list_window_refuses_an_unscoped_read(db) -> None:
    from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository

    with pytest.raises(ValueError, match="tenant-scoped"):
        ArangoPlantInstanceRepository(db).list_window(limit=5)


def test_list_window_runs_one_query_where_get_all_runs_two(db) -> None:
    from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository

    repo = ArangoPlantInstanceRepository(db)
    executed: list[str] = []
    original = AQL.execute

    def spy(self, query, *args, **kwargs):
        executed.append(query)
        return original(self, query, *args, **kwargs)

    # ``db.aql`` builds a new AQL object per access, so the method is patched on the class.
    with patch.object(AQL, "execute", spy):
        repo.get_all(0, 5, tenant_key=_A)
        with_count = list(executed)
        executed.clear()
        repo.list_window(tenant_key=_A, limit=5)
    assert len(with_count) == 2 and "COLLECT WITH COUNT" in with_count[1]
    assert len(executed) == 1 and "COLLECT" not in executed[0]


def _pages(read, total: int, size: int) -> list[str]:
    return [row.key for off in range(0, total + size, size) for row in read(offset=off, limit=size)]


def test_tenants_and_users_page_through_equal_timestamps(db) -> None:
    from app.data_access.arango.tenant_repository import ArangoTenantRepository
    from app.data_access.arango.user_repository import ArangoUserRepository

    db.collection(col.TENANTS).truncate()
    db.collection(col.USERS).truncate()
    db.collection(col.TENANTS).insert_many(
        [
            {"_key": f"t{i}", "name": f"T{i}", "slug": f"t-{i}", "owner_user_key": "u", "created_at": _SAME_SECOND}
            for i in range(7)
        ]
    )
    db.collection(col.USERS).insert_many(
        [
            {"_key": f"u{i}", "email": f"u{i}@example.org", "display_name": f"U{i}", "created_at": _SAME_SECOND}
            for i in range(7)
        ]
    )

    tenants = _pages(ArangoTenantRepository(db).list_all, 7, 2)
    users = _pages(ArangoUserRepository(db).list_all, 7, 2)

    # Equal created_at everywhere: only the _key tie-break makes the windows a partition.
    assert tenants == [f"t{i}" for i in reversed(range(7))]
    assert users == [f"u{i}" for i in reversed(range(7))]
    assert len(ArangoTenantRepository(db).list_all()) == 7  # no window: every tenant, as before


def test_invitations_conversations_and_observations_are_windowed(db) -> None:
    from app.data_access.arango.ai_repository import ArangoAiConversationRepository
    from app.data_access.arango.invitation_repository import ArangoInvitationRepository
    from app.data_access.arango.post_harvest_repository import ArangoPostHarvestRepository

    expires = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    db.collection(col.INVITATIONS).insert_many(
        [
            {
                "_key": f"inv{i}",
                "tenant_key": _A if i < 5 else _B,
                "invited_by_user_key": "u",
                "token_hash": f"h{i}",
                "expires_at": expires,
                "created_at": _SAME_SECOND,
            }
            for i in range(8)
        ]
    )
    db.collection(col.AI_CONVERSATIONS).insert_many(
        [
            {"_key": f"c{i}", "tenant_key": _A, "user_key": "u" if i < 5 else "v", "updated_at": _SAME_SECOND}
            for i in range(8)
        ]
    )
    db.collection(col.STORAGE_OBSERVATIONS).insert_many(
        [{"_key": f"o{i}", "batch_key": "b1" if i < 5 else "b2", "observed_at": _SAME_SECOND} for i in range(8)]
    )

    invitations = ArangoInvitationRepository(db)
    conversations = ArangoAiConversationRepository(db)
    post_harvest = ArangoPostHarvestRepository(db)

    assert _pages(lambda **w: invitations.list_by_tenant(_A, **w), 5, 2) == [f"inv{i}" for i in reversed(range(5))]
    assert _pages(lambda **w: conversations.list_for_user(_A, "u", **w), 5, 2) == [f"c{i}" for i in reversed(range(5))]
    assert _pages(lambda **w: post_harvest.list_observations("b1", **w), 5, 2) == [f"o{i}" for i in reversed(range(5))]
    assert len(invitations.list_by_tenant(_A)) == 5


def test_a_plants_tasks_are_windowed_by_due_date(db) -> None:
    from app.data_access.arango.task_repository import ArangoTaskRepository

    db.collection(col.TASKS).truncate()
    start = date(2026, 3, 1)
    rows = [
        {
            "_key": f"task{i}",
            "name": f"Task {i}",
            "tenant_key": _A,
            "entity_type": "plant_instance",
            "entity_key": "p1",
            "status": "pending",
            # two tasks per day: the due date alone is not a total order
            "due_date": datetime.combine(start + timedelta(days=i // 2), datetime.min.time(), UTC).isoformat(),
        }
        for i in range(9)
    ]
    rows.append({**rows[0], "_key": "foreign", "tenant_key": _B})
    # Inserted in reverse key order, so the storage order of two tasks due the same
    # day is the opposite of their tie-break order: an untied sort would show it.
    db.collection(col.TASKS).insert_many(list(reversed(rows)))
    repo = ArangoTaskRepository(db)

    window = [t.key for t in repo.get_tasks_for_plant("p1", tenant_key=_A, offset=2, limit=3)]
    walked = _pages(lambda **w: repo.get_tasks_for_plant("p1", tenant_key=_A, **w), 9, 2)

    assert window == ["task2", "task3", "task4"]
    assert walked == [f"task{i}" for i in range(9)]
    # Without a window the read is unchanged: every task, ties in storage order.
    assert sorted(t.key for t in repo.get_tasks_for_plant("p1", tenant_key=_A)) == [f"task{i}" for i in range(9)]


@pytest.mark.parametrize("collection", col.KEYSET_PAGED_COLLECTIONS)
@pytest.mark.parametrize("after", [None, "k005"], ids=["first-page", "cursor"])
def test_the_window_query_reads_the_keyset_index_and_does_not_sort(db, collection: str, after: str | None) -> None:
    """The window is served by ``(tenant_key, _key)``: no sort of the tenant's rows.

    Measured before the index existed (60 000 rows, 49 880 of one tenant): on
    ``plant_instances`` the optimizer took the ``(tenant_key, instance_id)`` index,
    sorted all 49 880 rows and read them for page 1 *and* for a cursor page; on the
    other three it walked the primary index and read 24 502 entries to find a small
    tenant's first page. With the index both read ``limit`` entries.
    """
    from app.data_access.arango.feeding_repository import ArangoFeedingRepository
    from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
    from app.data_access.arango.watering_log_repository import ArangoWateringLogRepository
    from app.data_access.arango.watering_repository import ArangoWateringRepository

    repo_class = {
        col.PLANT_INSTANCES: ArangoPlantInstanceRepository,
        col.FEEDING_EVENTS: ArangoFeedingRepository,
        col.WATERING_EVENTS: ArangoWateringRepository,
        col.WATERING_LOGS: ArangoWateringLogRepository,
    }[collection]
    query, bind_vars = repo_class(db)._list_builder(0, 50, _A, all_tenants=False, after=after).build_list()

    plan = db.aql.explain(query, bind_vars=bind_vars)
    node_types = [node["type"] for node in plan["nodes"]]
    indexes = [index["fields"] for node in plan["nodes"] for index in node.get("indexes", [])]

    assert col.TENANT_KEY_ORDER_INDEX_FIELDS in indexes, (indexes, node_types)
    assert "SortNode" not in node_types, node_types
