"""Integration test for migration v0048 — backfill the missing care profiles (#1444 part 2).

The unit tests run the migration against a fake whose population predicate is
parsed out of the query text. That proves the migration keeps *using* the
repository's builders; it cannot prove four things this tier measures:

* **the family key is not the family name.** ``Species.family_key`` stores the
  ``_key`` ArangoDB assigned to a ``botanical_families`` document, and
  ``FAMILY_CARE_MAP`` is keyed by the name. The control test below inserts a
  family the way the seeder does and measures what comes back, so the resolution
  step this migration performs rests on a measurement rather than on a reading of
  ``seed_data.py``;
* **the unique ``_from`` index on ``has_care_profile``** really refuses a second
  edge for the same plant (PR #1486), and the migration really leaves no profile
  behind when it does;
* **the audit agrees afterwards.** ``scripts/audit_care_profiles.py`` is the
  positive control the issue names: exit 3 before, exit 0 with
  ``missing_total == 0`` and an unchanged ``plants_active`` after;
* **AC-4 end to end** — ``generate_due_care_reminders`` creates a care task for a
  plant that only this migration made visible to it.

Run with::

    docker run -d --rm --name kp-it-1444 -p 8529:8529 \
      -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0048_backfill_missing_care_profiles.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from tests.support.arango_integration import run_database_name

# The server probe lives in tests/integration/conftest.py (``arango_db``): one probe
# for the tier, a loud failure under CI, a skip with the address locally. A private
# ``ARANGO_AVAILABLE`` copy here would be the self-skip #1432 retired.
pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection(
        "ArangoDB's own key assignment, the unique has_care_profile index and the audit script are the SUT"
    ),
]

_DB_NAME = run_database_name("v0048_migration")
_TENANT = "mein-garten"
_FAMILY_NAME = "Cactaceae"
_SCIENTIFIC_NAME = "Opuntia ficus-indica"

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _connect():
    from app.config.settings import Settings
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(Settings(arangodb_database=_DB_NAME))
    return conn, conn.connect()


@pytest.fixture
def db():
    """A freshly bootstrapped database — every collection and index production has."""
    from arango import ArangoClient

    from app.data_access.arango.collections import ensure_collections
    from tests.support.arango_integration import (
        ARANGO_PASSWORD,
        ARANGO_URL,
        ARANGO_USERNAME,
        SYSTEM_DATABASE,
    )

    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db(SYSTEM_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)

    _conn, handle = _connect()
    ensure_collections(handle)
    yield handle

    system.delete_database(_DB_NAME)
    client.close()


def _insert_family(db, name: str = _FAMILY_NAME) -> str:
    """Insert a botanical family the way ``seed_data`` does — **without** a ``_key``."""
    from app.data_access.arango import collections as col

    meta = db.collection(col.BOTANICAL_FAMILIES).insert({"name": name, "common_name_de": "Kakteengewächse"})
    return str(meta["_key"])


def _insert_species(db, family_key: str) -> str:
    from app.data_access.arango import collections as col

    meta = db.collection(col.SPECIES).insert(
        {
            "scientific_name": _SCIENTIFIC_NAME,
            "scientific_name_normalized": _SCIENTIFIC_NAME.lower(),
            "common_names": ["Feigenkaktus"],
            "family_key": family_key,
            "tenant_key": "",
        }
    )
    return str(meta["_key"])


def _insert_plant(db, species_key: str, *, instance_id: str = "P-0001", removed_on: str | None = None) -> str:
    """Insert a plant **without** a care profile — the pre-#1440 state this repairs."""
    from app.data_access.arango import collections as col

    meta = db.collection(col.PLANT_INSTANCES).insert(
        {
            "tenant_key": _TENANT,
            "instance_id": instance_id,
            "species_key": species_key,
            "plant_name": "Feigenkaktus",
            "planted_on": str(date(2024, 5, 1)),
            "removed_on": removed_on,
            "created_at": datetime(2024, 5, 1, tzinfo=UTC).isoformat(),
            "updated_at": datetime(2024, 5, 1, tzinfo=UTC).isoformat(),
        }
    )
    return str(meta["_key"])


def _seed_unprofiled_plant(db) -> str:
    family_key = _insert_family(db)
    species_key = _insert_species(db, family_key)
    return _insert_plant(db, species_key)


def _run_audit() -> tuple[int, dict]:
    """Run the read-only audit exactly as an operator would, against this database."""
    from tests.support.arango_integration import (
        ARANGO_HOST,
        ARANGO_PASSWORD,
        ARANGO_PORT,
        ARANGO_USERNAME,
    )

    result = subprocess.run(  # noqa: S603 — fixed argv, no shell
        [sys.executable, "scripts/audit_care_profiles.py", "--json"],
        cwd=_BACKEND_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        env={
            **os.environ,
            "ARANGODB_DATABASE": _DB_NAME,
            "ARANGODB_HOST": ARANGO_HOST,
            "ARANGODB_PORT": ARANGO_PORT,
            "ARANGODB_USERNAME": ARANGO_USERNAME,
            "ARANGODB_PASSWORD": ARANGO_PASSWORD,
        },
    )
    assert result.stdout, f"audit printed nothing; stderr was: {result.stderr}"
    return result.returncode, json.loads(result.stdout)


# ── the premise, measured ─────────────────────────────────────────────────────


def test_a_species_family_key_is_a_document_key_not_the_family_name(db) -> None:
    """Without this control every family assertion below could be a tautology.

    ``BaseArangoRepository._to_doc`` pops ``_key`` before every insert, so a
    family's key is whatever ArangoDB assigns — while ``FAMILY_CARE_MAP`` is keyed
    by ``"Cactaceae"``. Handing the stored key to ``auto_generate_profile`` as the
    botanical family therefore matches nothing and yields the TROPICAL preset,
    which is what ``_bootstrap_care_profile`` does today.
    """
    from app.domain.engines.care_reminder_engine import FAMILY_CARE_MAP

    family_key = _insert_family(db)

    assert family_key != _FAMILY_NAME
    assert family_key.isdigit(), f"expected ArangoDB's numeric key, got {family_key!r}"
    assert family_key not in FAMILY_CARE_MAP
    assert _FAMILY_NAME in FAMILY_CARE_MAP


# ── the backfill against a real server ────────────────────────────────────────


def test_the_plant_gets_one_profile_and_one_edge_with_its_family_preset(db) -> None:
    from app.common.enums import CareStyleType
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0048_backfill_missing_care_profiles import migration

    plant_key = _seed_unprofiled_plant(db)

    report = migration.up(db)

    profiles = list(db.collection(col.CARE_PROFILES).all())
    edges = list(db.collection(col.HAS_CARE_PROFILE).all())
    assert len(profiles) == 1
    assert profiles[0]["plant_key"] == plant_key
    assert profiles[0]["care_style"] == CareStyleType.CACTUS.value
    assert profiles[0]["auto_generated"] is True
    assert "tenant_key" not in profiles[0]
    assert len(edges) == 1
    assert edges[0]["_from"] == f"{col.PLANT_INSTANCES}/{plant_key}"
    assert edges[0]["_to"] == f"{col.CARE_PROFILES}/{profiles[0]['_key']}"
    assert report.scanned == 1
    assert report.changed == 1
    assert report.details["created"][0]["botanical_family"] == _FAMILY_NAME


def test_a_removed_plant_stays_out_of_the_population(db) -> None:
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0048_backfill_missing_care_profiles import migration

    family_key = _insert_family(db)
    species_key = _insert_species(db, family_key)
    _insert_plant(db, species_key, instance_id="P-GONE", removed_on=str(date(2025, 3, 1)))

    report = migration.up(db)

    assert report.scanned == 0
    assert list(db.collection(col.CARE_PROFILES).all()) == []


def test_a_second_run_writes_nothing(db) -> None:
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0048_backfill_missing_care_profiles import migration

    _seed_unprofiled_plant(db)
    migration.up(db)
    stored = list(db.collection(col.CARE_PROFILES).all())

    second = migration.up(db)

    assert second.scanned == 0
    assert second.changed == 0
    assert list(db.collection(col.CARE_PROFILES).all()) == stored
    assert len(list(db.collection(col.HAS_CARE_PROFILE).all())) == 1


def test_a_taken_edge_slot_leaves_no_profile_behind(db) -> None:
    """The unique ``_from`` index is real, and the loser is rolled back (PR #1486).

    The plant owns an edge to a profile whose ``plant_key`` names somebody else, so
    it sits inside the population while its ``_from`` slot is taken — reachable
    without any concurrency.
    """
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0048_backfill_missing_care_profiles import migration

    plant_key = _seed_unprofiled_plant(db)
    stranger = db.collection(col.CARE_PROFILES).insert({"plant_key": "someone-else", "care_style": "tropical"})
    db.collection(col.HAS_CARE_PROFILE).insert(
        {
            "_from": f"{col.PLANT_INSTANCES}/{plant_key}",
            "_to": f"{col.CARE_PROFILES}/{stranger['_key']}",
        }
    )

    report = migration.up(db)

    assert report.scanned == 1
    assert report.changed == 0
    assert report.details["already_profiled"] == [
        {"plant_key": plant_key, "tenant_key": _TENANT, "reason": "profile_edge_already_present"}
    ]
    assert [doc["_key"] for doc in db.collection(col.CARE_PROFILES).all()] == [stranger["_key"]]


# ── the positive control the issue names ──────────────────────────────────────


def test_the_audit_goes_from_findings_to_clean_over_the_migration(db) -> None:
    from app.migrations.versions.v0048_backfill_missing_care_profiles import migration

    _seed_unprofiled_plant(db)

    before_code, before = _run_audit()
    assert before_code == 3
    assert before["expected_profiles_to_create"] == 1

    migration.up(db)

    after_code, after = _run_audit()
    assert after_code == 0
    assert after["missing_total"] == 0
    assert after["expected_profiles_to_create"] == 0
    assert after["plants_active"] == before["plants_active"]
    assert after["orphan_profiles"] == 0


# ── AC-4, end to end ──────────────────────────────────────────────────────────


def test_the_backfilled_plant_receives_a_care_task_from_the_nightly_run(db, monkeypatch) -> None:
    """AC-4: the plant the generator could not see before now produces a task.

    The generator iterates *stored* profiles, so before the migration this plant is
    not "skipped" — it is absent from the iteration, which the first half asserts.
    """
    from app.common import dependencies
    from app.common.enums import TaskCategory
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0048_backfill_missing_care_profiles import migration
    from app.tasks.care_tasks import generate_due_care_reminders

    monkeypatch.setattr(dependencies, "get_db", lambda: db)
    plant_key = _seed_unprofiled_plant(db)

    before = generate_due_care_reminders()
    assert before == {"created": 0, "skipped": 0}
    assert list(db.collection(col.TASKS).all()) == []

    migration.up(db)
    after = generate_due_care_reminders()

    tasks = [task for task in db.collection(col.TASKS).all() if task["entity_key"] == plant_key]
    assert after["created"] >= 1
    assert tasks, "the backfilled plant produced no care task"
    assert all(task["category"] == TaskCategory.CARE_REMINDER.value for task in tasks)
    assert all(task["tenant_key"] == _TENANT for task in tasks)
    due_dates = {str(task["due_date"])[:10] for task in tasks}
    assert due_dates, "a care task must carry a due date"
    assert min(due_dates) <= str(date.today() + timedelta(days=90))
