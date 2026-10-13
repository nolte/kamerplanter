"""#1948 — v0080 stamps verified accounts without a proof and leaves every other account alone.

Runs on a database built by today's ``ensure_collections`` with the accounts a volume can
carry: verified without the field (grandfathered), verified with a proof (untouched),
unverified (untouched, they confirm through the link).
"""

from __future__ import annotations

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0080_backfill_email_confirmed_at import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration rewrites rows on a real server"),
]

_DB_NAME = run_database_name("v0080_backfill_email_confirmed_at")
PROVEN = "2026-01-01T00:00:00+00:00"


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    database.collection(col.USERS).insert_many(
        [
            {"_key": "legacy", "email": "legacy@example.org", "email_verified": True},
            {"_key": "legacy-null", "email": "null@example.org", "email_verified": True, "email_confirmed_at": None},
            {"_key": "proven", "email": "proven@example.org", "email_verified": True, "email_confirmed_at": PROVEN},
            {"_key": "pending", "email": "pending@example.org", "email_verified": False},
        ]
    )
    yield database
    system.delete_database(_DB_NAME)


def _proofs(db) -> dict[str, str | None]:
    return {doc["_key"]: doc.get("email_confirmed_at") for doc in db.collection(col.USERS).all()}


def test_only_verified_accounts_without_a_proof_are_stamped_and_a_rerun_is_a_noop(db):
    dry = migration.up(db, dry_run=True)
    assert (dry.scanned, dry.changed) == (2, 0)
    assert _proofs(db)["legacy"] is None

    report = migration.up(db)

    assert report.changed == 2
    proofs = _proofs(db)
    assert proofs["legacy"] is not None
    assert proofs["legacy-null"] is not None
    assert proofs["proven"] == PROVEN
    assert proofs["pending"] is None
    assert migration.up(db).changed == 0
