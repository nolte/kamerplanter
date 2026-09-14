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

from app.data_access.arango.attachment_repository import aql_photo_ref_candidates
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
    # The three shapes review found missing, each of which the previous
    # single-answer normaliser got wrong — the trailing slash destructively, by
    # resolving to the empty string.
    (f"/api/v1/t/mein-garten/attachments/{ULID}_t320.webp", "an API URI carrying a thumbnail suffix"),
    (f"t/mein-garten/task/2026/01/{ULID}.jpg?v=2", "a key with a query string"),
    (f"t/mein-garten/task/2026/01/{ULID}.jpg/", "a key with a trailing slash"),
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


def _candidates_in_aql(db, reference: str) -> list[str]:
    """Run the sweep's own expression over one reference."""
    query = f"RETURN {aql_photo_ref_candidates('@ref')}"
    cursor = db.aql.execute(query, bind_vars={"ref": reference})
    return list(next(cursor))


@pytest.mark.parametrize(("reference", "shape"), REFERENCES, ids=[row[1] for row in REFERENCES])
def test_the_production_answer_is_among_the_candidates(db, reference: str, shape: str):
    """The property that matters: the sweep protects what the normaliser resolves to.

    Not equality. The sweep's output is **deleted**, so the two directions cost
    different things: an extra candidate leaves one photo uncollected, a missing one
    destroys a photo a task still shows. Demanding equality is what the two previous
    versions did, and both were wrong in the destroying direction.
    """
    candidates = _candidates_in_aql(db, reference)

    assert normalize_photo_ref(reference) in candidates, (
        f"the sweep does not protect what migrate_photo_refs resolves {shape} to "
        f"({reference!r} -> {normalize_photo_ref(reference)!r}, candidates {candidates}); "
        "a reference it cannot resolve is a photo it deletes (#1393)"
    )


@pytest.mark.parametrize(("reference", "shape"), REFERENCES, ids=[row[1] for row in REFERENCES])
def test_the_attachment_id_is_among_the_candidates(db, reference: str, shape: str):
    """The control.

    Without it, a candidate list that simply returned its input would contain the
    normaliser's answer for the already-an-id row and nothing useful for any other,
    and the test above would still pass on most rows.
    """
    assert ULID in _candidates_in_aql(db, reference), f"{shape} does not resolve to the attachment id"


@pytest.mark.parametrize(("reference", "shape"), REFERENCES, ids=[row[1] for row in REFERENCES])
def test_no_candidate_is_empty(db, reference: str, shape: str):
    """An empty candidate protects nothing and matches no document key.

    The previous version produced exactly that for a trailing slash — ``LAST(SPLIT())``
    of ``"a/b/"`` is ``""`` — so the photo went unprotected while the expression
    looked like it had an answer.
    """
    assert "" not in _candidates_in_aql(db, reference), f"{shape} produced an empty candidate"


def test_the_candidate_set_stays_proportional_to_the_reference(db):
    """A superset is the point; a set that grows without bound is not.

    The bound used to be a flat four, because only the *last* path segment was
    resolved. Round 7 resolves **every** segment — the identifier sits in the middle
    of ``/attachments/{id}/thumbnails/{size}``, which is the shape ``_photo_response``
    hands to every client, and the previous design reached it only through a substring
    test that turned out to be unusable against numeric document keys.

    So the invariant is no longer a constant but a proportion: at most three
    candidates per path segment (the segment, its extension-stripped stem, that stem
    without a ``_t{size}`` suffix), plus the whole reference. Asserted as a
    relationship rather than a number, so it cannot be "fixed" by raising a literal
    when someone widens the expression.
    """
    for reference, shape in REFERENCES:
        candidates = set(_candidates_in_aql(db, reference))
        segments = [part for part in reference.split("?")[0].split("/") if part]
        ceiling = 3 * len(segments) + 1
        assert len(candidates) <= ceiling, (
            f"{shape} produced {len(candidates)} distinct candidates for "
            f"{len(segments)} segments (ceiling {ceiling}); the expression widened "
            f"beyond per-segment resolution, and a wide candidate set protects photos "
            f"nothing references — the sweep then collects nothing"
        )
