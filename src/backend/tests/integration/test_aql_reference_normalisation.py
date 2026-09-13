"""#1393 — the sweep's AQL normalisation answers what `normalize_photo_ref` answers.

`find_orphaned_task_photos` deletes what nothing references. It decides "nothing
references this" by normalising each `photo_refs` entry to an attachment id, and
`app/migrations/migrate_photo_refs.normalize_photo_ref` is the production definition
of that mapping. **The two disagreeing by one character deletes photos a task still
references**, which is what shipped: the AQL took the last path segment and stopped,
while the writer emits `t/{tenant}/{cat}/{yyyy}/{mm}/{ulid}.{ext}`, so it compared
`{ulid}.{ext}` against a key of `{ulid}` and found nothing.

Two things make this file the guard rather than another way to be wrong:

* it runs the **same expression the query runs** — `aql_normalise_photo_ref` is
  called here and there, never transcribed. A test that re-implements the logic
  certifies its own copy, which is how the previous guard shipped with a hole.
* it runs the AQL **against a real ArangoDB**, because the question is what
  `REGEX_REPLACE` and `SPLIT` actually do to these strings, not what they look like
  they do.

Skipped when no ArangoDB answers on ``localhost:8529``. Run it with::

    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_aql_reference_normalisation.py -v
"""

from __future__ import annotations

import pytest

from app.data_access.arango.attachment_repository import aql_normalise_photo_ref
from app.migrations.migrate_photo_refs import normalize_photo_ref

ARANGO_URL = "http://localhost:8529"
ARANGO_PASSWORD = "rootpassword"
TEST_DATABASE = "kamerplanter_ref_normalisation_test"

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

#: A ULID-shaped id, because `normalize_photo_ref` returns an already-normalised
#: value unchanged only when it matches that shape.
ULID = "01J0ABCDEFGHJKMNPQRSTVWXYZ"

#: Every spelling a `photo_refs` entry is known to take.
#:
#: The storage-key and URI rows carry an extension on purpose: the fixture that
#: was supposed to protect them omitted it, so it asserted protection for a shape
#: the writer cannot produce and stayed green while the real one was deleted.
REFERENCES: list[tuple[str, str]] = [
    (ULID, "already an attachment id"),
    (f"/api/v1/t/mein-garten/attachments/{ULID}", "an API URI without an extension"),
    (f"/api/v1/t/mein-garten/attachments/{ULID}.jpg", "an API URI with an extension"),
    (f"t/mein-garten/task/2026/01/{ULID}.jpg", "the storage key StorageKeyBuilder emits"),
    (f"t/mein-garten/task/2026/01/{ULID}.webp", "the same with another extension"),
    (f"t/mein-garten/task/2026/01/{ULID}_t320.webp", "a thumbnail rendition of it"),
    (f"s3://bucket/t/mein-garten/task/2026/01/{ULID}.jpg", "an s3 URL"),
]


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username="root", password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    yield client.db(TEST_DATABASE, username="root", password=ARANGO_PASSWORD)
    system.delete_database(TEST_DATABASE)
    client.close()


def _normalise_in_aql(db, reference: str) -> str:
    """Run the sweep's own expression over one reference."""
    query = f"RETURN {aql_normalise_photo_ref('@ref')}"
    cursor = db.aql.execute(query, bind_vars={"ref": reference})
    return next(cursor)


@pytest.mark.parametrize(("reference", "shape"), REFERENCES, ids=[row[1] for row in REFERENCES])
def test_the_aql_agrees_with_the_production_normaliser(db, reference: str, shape: str):
    """Same input, same answer, or the sweep deletes what a task references."""
    assert _normalise_in_aql(db, reference) == normalize_photo_ref(reference), (
        f"the sweep and migrate_photo_refs disagree about {shape} ({reference!r}); "
        "a reference the sweep cannot resolve is a photo it deletes (#1393)"
    )


@pytest.mark.parametrize(("reference", "shape"), REFERENCES, ids=[row[1] for row in REFERENCES])
def test_every_spelling_resolves_to_the_id(db, reference: str, shape: str):
    """The control.

    Without it, a normaliser that returned its input unchanged — and an AQL
    expression that did the same — would agree perfectly and resolve nothing. The
    two tests fail for different reasons: this one catches "both are wrong the same
    way", the one above catches "they drifted apart".
    """
    assert _normalise_in_aql(db, reference) == ULID, f"{shape} did not resolve to the attachment id"
