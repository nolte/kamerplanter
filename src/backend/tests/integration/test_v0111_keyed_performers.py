"""spec/privacy/09 §5 / §9 / §11 / §12 (TA-700, TA-702, TA-716) — v0111 against a real ArangoDB.

The AQL is what this module measures: the dynamic field names, the tenant predicate on the row and on
the tank of a row that carries none (#706), the ``active`` gate, the 80-character label, the
service-account check of ``mcp:`` inspections, ``down`` and the persisted report — and that a
repository read and write keeps the new fields. The phases (partial run, residual, runner) are pinned in
``tests/unit/migrations/versions/test_v0111_keyed_performers.py``.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0111_keyed_performers.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.tank_repository import ArangoTankRepository
from app.migrations.framework.report_store import persist_report
from app.migrations.versions.v0111_keyed_performers import (
    BUCKET_INSPECTOR_CLEARED,
    BUCKET_MAINTENANCE_LOGS,
    BUCKET_SERVICE_ACCOUNT_KEYED,
    BUCKET_TANK_FILL_EVENTS,
    BUCKET_WATERING_EVENTS,
    STEP_BUCKETS,
    migration,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the backfill is AQL over seven collections on a real server"),
]

_DB_NAME = run_database_name("v0111_keyed_performers")


def _insert(database, collection: str, documents: list[dict]) -> None:  # type: ignore[no-untyped-def]
    results = database.collection(collection).insert_many(documents)
    assert [r for r in results if isinstance(r, Exception)] == []


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    _insert(
        database,
        col.TENANTS,
        [
            {"_key": "t_a", "name": "a", "slug": "a", "owner_user_key": "human", "status": "active"},
            {"_key": "t_s", "name": "s", "slug": "s", "owner_user_key": "human", "status": "suspended"},
            {"_key": "t_n", "name": "n", "slug": "n", "owner_user_key": "human"},  # no status: the model's active
        ],
    )
    _insert(
        database,
        col.USERS,
        [
            {"_key": "svc", "email": "svc@example.com", "display_name": "HA", "account_type": "service"},
            {"_key": "human", "email": "h@example.com", "display_name": "Lisa", "account_type": "human"},
            {"_key": "svc_b", "email": "b@example.com", "display_name": "B", "account_type": "service"},
            {
                "_key": "svc_off",
                "email": "off@example.com",
                "display_name": "Off",
                "account_type": "service",
                "is_active": False,
            },
        ],
    )
    _insert(
        database,
        col.MEMBERSHIPS,
        [
            {"user_key": "svc", "tenant_key": "t_a", "role": "grower", "is_active": True},
            {"user_key": "human", "tenant_key": "t_a", "role": "lead", "is_active": True},
            {"user_key": "svc_b", "tenant_key": "t_s", "role": "grower", "is_active": True},
            {"user_key": "svc_off", "tenant_key": "t_a", "role": "grower", "is_active": True},
        ],
    )
    _insert(
        database,
        col.TANKS,
        [
            {"_key": "tank_a", "tenant_key": "t_a", "name": "A", "tank_type": "reservoir", "volume_liters": 50},
            {"_key": "tank_s", "tenant_key": "t_s", "name": "S", "tank_type": "reservoir", "volume_liters": 50},
        ],
    )
    long_name = "Ä" * 100
    _insert(
        database,
        col.WATERING_EVENTS,
        [
            {"_key": "we_a", "tenant_key": "t_a", "volume_liters": 1, "performed_by": "Lisa"},
            {"_key": "we_a_name_is_key", "tenant_key": "t_a", "volume_liters": 1, "performed_by": "human"},
            {"_key": "we_a_empty", "tenant_key": "t_a", "volume_liters": 1, "performed_by": ""},
            {"_key": "we_s", "tenant_key": "t_s", "volume_liters": 1, "performed_by": "Lisa"},
            {"_key": "we_n", "tenant_key": "t_n", "volume_liters": 1, "performed_by": "Ida"},
        ],
    )
    _insert(
        database,
        col.WATERING_LOGS,
        [{"_key": "wl_a", "tenant_key": "t_a", "volume_liters": 1, "plant_keys": ["p"], "performed_by": long_name}],
    )
    # No tenant_key on either: the tank is the anchor.
    _insert(
        database,
        col.MAINTENANCE_LOGS,
        [
            {"_key": "ml_a", "tank_key": "tank_a", "maintenance_type": "cleaning", "performed_by": "Maren"},
            {"_key": "ml_s", "tank_key": "tank_s", "maintenance_type": "cleaning", "performed_by": "Maren"},
        ],
    )
    _insert(
        database,
        col.TANK_FILL_EVENTS,
        [{"_key": "tf_a", "tank_key": "tank_a", "fill_type": "top_up", "volume_liters": 5, "performed_by": "Maren"}],
    )
    _insert(
        database,
        col.NUTRIENT_PLANS,
        [
            {"_key": "np_a", "tenant_key": "t_a", "name": "A", "author": "Lisa"},
            {"_key": "np_global", "tenant_key": "", "name": "G", "author": "Plagron", "is_template": True},
        ],
    )
    _insert(
        database,
        col.WORKFLOW_TEMPLATES,
        [{"_key": "wt_a", "tenant_key": "t_a", "name": "W", "created_by": "Lisa"}],
    )
    _insert(
        database,
        col.INSPECTIONS,
        [
            {"_key": "in_svc", "tenant_key": "t_a", "inspector": "mcp:svc", "inspected_by_key": None},
            {"_key": "in_off", "tenant_key": "t_a", "inspector": "mcp:svc_off", "inspected_by_key": None},
            {"_key": "in_human", "tenant_key": "t_a", "inspector": "mcp:human", "inspected_by_key": None},
            {"_key": "in_foreign", "tenant_key": "t_a", "inspector": "mcp:svc_b", "inspected_by_key": None},
            {"_key": "in_gone", "tenant_key": "t_a", "inspector": "mcp:gone", "inspected_by_key": None},
            {"_key": "in_keyed", "tenant_key": "t_a", "inspector": "mcp:svc", "inspected_by_key": "svc"},
            {"_key": "in_name", "tenant_key": "t_a", "inspector": "Maren", "inspected_by_key": None},
            {"_key": "in_s", "tenant_key": "t_s", "inspector": "mcp:svc_b", "inspected_by_key": None},
        ],
    )
    yield database
    system.delete_database(_DB_NAME)


def _doc(db, collection: str, key: str) -> dict:  # type: ignore[no-untyped-def]
    return {k: v for k, v in db.collection(collection).get(key).items() if not k.startswith("_")}


def test_the_dry_run_counts_and_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    assert report.details["status"] == "dry_run"
    assert report.details["buckets"][BUCKET_WATERING_EVENTS] == {"t_a": 3, "t_n": 1}
    assert report.details["buckets"][BUCKET_MAINTENANCE_LOGS] == {"t_a": 1}
    assert report.details["buckets"][BUCKET_INSPECTOR_CLEARED] == {"t_a": 6}
    assert report.details["buckets"][BUCKET_SERVICE_ACCOUNT_KEYED] == {"t_a": 1}
    assert "performed_by_user_key" not in _doc(db, col.WATERING_EVENTS, "we_a")


def test_the_real_run_lays_down_the_fields_in_active_tenants_only(db) -> None:  # type: ignore[no-untyped-def]
    """TA-716: the suspended tenant and the global catalogue row are not touched."""
    report = migration.up(db)

    assert report.details["status"] == "applied"
    we_a = _doc(db, col.WATERING_EVENTS, "we_a")
    assert we_a["performed_by_user_key"] is None
    assert we_a["performed_by_label"] == "Lisa"
    assert we_a["performed_by"] == "Lisa"
    assert _doc(db, col.WATERING_EVENTS, "we_a_empty") == {
        "tenant_key": "t_a",
        "volume_liters": 1,
        "performed_by": "",
        "performed_by_user_key": None,
    }
    assert _doc(db, col.WATERING_EVENTS, "we_n")["performed_by_label"] == "Ida"
    assert _doc(db, col.WATERING_LOGS, "wl_a")["performed_by_label"] == "Ä" * 80
    assert _doc(db, col.MAINTENANCE_LOGS, "ml_a")["performed_by_label"] == "Maren"
    assert _doc(db, col.TANK_FILL_EVENTS, "tf_a")["performed_by_label"] == "Maren"
    assert _doc(db, col.NUTRIENT_PLANS, "np_a")["author_label"] == "Lisa"
    assert _doc(db, col.WORKFLOW_TEMPLATES, "wt_a")["created_by_user_key"] is None
    assert "performed_by_user_key" not in _doc(db, col.WATERING_EVENTS, "we_s")
    assert "performed_by_user_key" not in _doc(db, col.MAINTENANCE_LOGS, "ml_s")
    assert "author_user_key" not in _doc(db, col.NUTRIENT_PLANS, "np_global")
    assert _doc(db, col.INSPECTIONS, "in_s")["inspector"] == "mcp:svc_b"
    assert report.details["phases"]["verify"]["residual"] == dict.fromkeys(STEP_BUCKETS, 0)
    assert report.details["phases"]["apply"]["changed"][BUCKET_TANK_FILL_EVENTS] == 1


def test_no_key_comes_from_a_name_and_mcp_only_from_a_live_service_member(db) -> None:  # type: ignore[no-untyped-def]
    """TA-702."""
    migration.up(db)

    assert _doc(db, col.WATERING_EVENTS, "we_a_name_is_key")["performed_by_user_key"] is None
    assert _doc(db, col.INSPECTIONS, "in_svc") == {"tenant_key": "t_a", "inspector": "", "inspected_by_key": "svc"}
    for key in ("in_human", "in_foreign", "in_gone", "in_off"):
        assert _doc(db, col.INSPECTIONS, key)["inspected_by_key"] is None, key
        assert _doc(db, col.INSPECTIONS, key)["inspector"] == "", key
    assert _doc(db, col.INSPECTIONS, "in_keyed") == {"tenant_key": "t_a", "inspector": "", "inspected_by_key": "svc"}
    assert _doc(db, col.INSPECTIONS, "in_name")["inspector"] == "Maren"


def test_a_second_run_changes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)

    again = migration.up(db)

    assert again.changed == 0
    assert again.details["status"] == "applied"


def test_the_repository_keeps_the_fields_across_a_write(db) -> None:  # type: ignore[no-untyped-def]
    """A read-modify-write through the model does not drop what v0111 laid down."""
    migration.up(db)
    repo = ArangoTankRepository(db)
    log = repo.get_maintenance_logs("tank_a")[0]

    assert log.performed_by_label == "Maren"
    assert log.performed_by_user_key is None


def test_down_removes_null_keys_and_copied_labels_only(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)
    db.collection(col.NUTRIENT_PLANS).update({"_key": "np_a", "author_label": "Edited"})
    db.collection(col.TANK_FILL_EVENTS).update({"_key": "tf_a", "performed_by_user_key": "human"})

    report = migration.down(db)

    assert report.details["status"] == "applied"
    assert _doc(db, col.WATERING_EVENTS, "we_a") == {"tenant_key": "t_a", "volume_liters": 1, "performed_by": "Lisa"}
    assert "performed_by_label" not in _doc(db, col.WATERING_LOGS, "wl_a")
    assert _doc(db, col.NUTRIENT_PLANS, "np_a")["author_label"] == "Edited"
    assert "author_user_key" not in _doc(db, col.NUTRIENT_PLANS, "np_a")
    assert _doc(db, col.TANK_FILL_EVENTS, "tf_a")["performed_by_user_key"] == "human"
    assert "performed_by_label" not in _doc(db, col.TANK_FILL_EVENTS, "tf_a")
    assert "created_by_user_key" not in _doc(db, col.WORKFLOW_TEMPLATES, "wt_a")
    assert _doc(db, col.INSPECTIONS, "in_svc")["inspected_by_key"] == "svc"


def test_the_report_is_persisted_without_redaction(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    persist_report(db, migration, report)

    (stored,) = list(db.collection(col.MIGRATION_REPORTS).all())
    assert stored["kind"] == "data_backfill"
    assert stored["redacted_entries"] == 0
