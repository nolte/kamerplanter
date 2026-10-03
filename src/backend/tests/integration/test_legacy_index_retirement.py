"""SEC-001 (#2034 review) — the legacy index is never counted as its own replacement.

On a real ArangoDB 3.12: one hash-typed unique index, a legacy shape spelled with a
list and a replacement shape spelled with a tuple of the same fields. Both shapes
match that one index; the retirement must refuse and the constraint must survive.
"""

from __future__ import annotations

import pytest
from arango.exceptions import DocumentInsertError

from app.migrations.support.legacy_indexes import IndexShape, retire_legacy_index
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the helper drops indexes on a real server"),
]

_DB_NAME = run_database_name("legacy_index_retirement")
_COLLECTION = "legacy_index_probe"


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def test_mixed_field_spellings_refuse_and_keep_the_only_unique_index(db) -> None:
    probe = db.create_collection(_COLLECTION)
    probe.add_index({"type": "hash", "fields": ["label"], "unique": True})
    probe.insert({"label": "LOT-1"})

    outcome = retire_legacy_index(
        probe,
        legacy=IndexShape(fields=["label"], unique=True),  # type: ignore[arg-type]
        replacement=IndexShape(fields=("label",), unique=True),
        dry_run=False,
    )

    assert outcome.refused
    assert outcome.dropped == 0
    assert [idx["type"] for idx in probe.indexes() if idx["fields"] == ["label"]] == ["hash"]
    with pytest.raises(DocumentInsertError):
        probe.insert({"label": "LOT-1"})
