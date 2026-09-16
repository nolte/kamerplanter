"""Tests for v0046_reconcile_photo_refs (#1438 part 2).

The fixture carries the shape v0003 actually produced: an attachment whose ``_key``
is a short **numeric** id and whose ``storage_key`` ends in an unrelated ULID, and a
task whose ``photo_refs`` holds that ULID — a reference that resolves to no document
key anywhere (NFR-013 §2.2, "two identities").

**What makes the fake honest.** The migration reduces a storage key through the AQL
expression exported by the repository, and a fake that re-implemented that reduction
would certify its own copy — the failure class that shipped the previous guard. So
``_FakeAql`` does not know what a stem is: it reads the two separators **out of the
query text** it is handed and applies exactly those. Emptying or swapping the
expression in ``aql_storage_key_stem`` therefore turns these tests red instead of
leaving them green against a private copy.

What the fake cannot certify is what ArangoDB's ``SPLIT``/``FIRST``/``LAST`` really do
to these strings; ``tests/integration/test_v0046_reconcile_photo_refs.py`` runs the
same migration against a real server for that.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0046_reconcile_photo_refs import (
    AttachmentIdentity,
    build_identity_index,
    migration,
    plan_reference,
)

#: The ULID ``StorageKeyBuilder`` minted for the object — unrelated to ``_key``.
ULID = "01J0ABCDEFGHJKMNPQRSTVWXYZ"
OTHER_ULID = "01J0ZYXWVUTSRQPNMKJHGFEDCB"

#: The numeric document key ArangoDB assigns (measured in #1393 round 7).
ATTACHMENT_KEY = "1024799"
OTHER_ATTACHMENT_KEY = "1024800"

TENANT = "mein-garten"
OTHER_TENANT = "volkspark"

STORAGE_KEY = f"t/{TENANT}/task/2026/01/{ULID}.jpg"


# ── the pure rule ─────────────────────────────────────────────────────────────


def _index(*attachments: AttachmentIdentity):
    return build_identity_index(attachments)


class TestPlanReference:
    def test_a_document_key_is_already_the_target_form(self) -> None:
        index = _index(AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID))

        assert plan_reference(ATTACHMENT_KEY, ATTACHMENT_KEY, TENANT, index).verdict == "canonical"

    def test_a_storage_key_stem_resolves_to_the_single_owner(self) -> None:
        index = _index(AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID))
        verdict = plan_reference(ULID, ULID, TENANT, index)

        assert verdict.verdict == "repaired"
        assert verdict.matches == (ATTACHMENT_KEY,)

    def test_two_owners_are_ambiguous_and_carry_both_keys(self) -> None:
        """The branch the upload path cannot produce — pinned here, purely.

        Measured before writing it: ``AttachmentService.upload`` deduplicates by
        sha256 *within* a tenant and returns the existing row, so two same-tenant
        attachments never share one storage-key stem. Two of them can only arrive
        through a restore or an import, and the rule still has to refuse to guess,
        which is what this asserts without inventing a fixture the product cannot
        reach.
        """
        index = _index(
            AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID),
            AttachmentIdentity(OTHER_ATTACHMENT_KEY, TENANT, ULID),
        )
        verdict = plan_reference(ULID, ULID, TENANT, index)

        assert verdict.verdict == "ambiguous"
        assert verdict.matches == (ATTACHMENT_KEY, OTHER_ATTACHMENT_KEY)

    def test_a_foreign_tenants_attachment_does_not_answer(self) -> None:
        index = _index(AttachmentIdentity(ATTACHMENT_KEY, OTHER_TENANT, ULID))

        assert plan_reference(ULID, ULID, TENANT, index).verdict == "unresolved"

    def test_a_tenantless_carrier_demands_installation_wide_uniqueness(self) -> None:
        """``harvest_observations`` carries no ``tenant_key``, so both rows answer."""
        index = _index(
            AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID),
            AttachmentIdentity(OTHER_ATTACHMENT_KEY, OTHER_TENANT, ULID),
        )

        assert plan_reference(ULID, ULID, None, index).verdict == "ambiguous"

    def test_nothing_matching_is_unresolved(self) -> None:
        index = _index(AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID))

        assert plan_reference(OTHER_ULID, OTHER_ULID, TENANT, index).verdict == "unresolved"

    def test_a_key_match_outranks_a_stem_coincidence(self) -> None:
        """Idempotency depends on it: a repaired entry must stay ``canonical``.

        Numeric document keys are short, so one of them colliding with another
        attachment's stem is not an exotic worry — and if that promoted the entry to
        ``ambiguous``, the second run would report the repair it just made as a
        problem for ever.
        """
        index = _index(
            AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID),
            AttachmentIdentity(OTHER_ATTACHMENT_KEY, TENANT, ATTACHMENT_KEY),
        )

        assert plan_reference(ATTACHMENT_KEY, ATTACHMENT_KEY, TENANT, index).verdict == "canonical"



class TestAStemMayOnlyAnswerForAStorageKey:
    """The stem of a *reference* must never be looked up as a document key.

    ``aql_storage_key_stem`` reduces a string to its last path segment without the
    extension. Applied to the attachment's ``storage_key`` that is the ULID
    ``StorageKeyBuilder`` minted — the second identity, which is what rule 1 is for.
    Applied to a *reference*, the same reduction happily produces a short numeric
    string: ``/…/attachments/{id}/thumbnails/320`` — a URI the product builds itself
    (``_photo_response``) — reduces to ``"320"``, and ``"320"`` is a perfectly
    plausible ArangoDB ``_key``. Matching that against the key index rewrites the
    reference onto a **different, existing** photo, irreversibly (#1438 review, B-1).

    So: verbatim against ``_key``, stem against ``storage_stem`` only.
    """

    def test_a_thumbnail_uri_does_not_borrow_a_key_from_its_size_segment(self) -> None:
        thumbnail_uri = f"/api/v1/t/{TENANT}/attachments/{ATTACHMENT_KEY}/thumbnails/320"
        index = _index(
            AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID),
            # The trap: an unrelated attachment whose numeric key *is* the size.
            AttachmentIdentity("320", TENANT, OTHER_ULID),
        )

        verdict = plan_reference(thumbnail_uri, "320", TENANT, index)

        assert verdict.matches != ("320",)
        assert verdict.verdict == "repaired"
        assert verdict.matches == (ATTACHMENT_KEY,)

    def test_a_thumbnail_uri_that_names_no_live_key_is_unresolved(self) -> None:
        """No live ``_key`` in the URI means *report*, never fall back to the size."""
        thumbnail_uri = f"/api/v1/t/{TENANT}/attachments/{OTHER_ULID}/thumbnails/320"
        index = _index(
            AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID),
            AttachmentIdentity("320", TENANT, OTHER_ULID),
        )

        assert plan_reference(thumbnail_uri, "320", TENANT, index).verdict == "unresolved"

    def test_a_reference_stem_equal_to_another_attachments_key_does_not_repair(self) -> None:
        """The same trap without a URI: a path whose last segment is a live key."""
        reference = f"t/{TENANT}/task/2026/01/{OTHER_ATTACHMENT_KEY}.jpg"
        index = _index(
            AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID),
            AttachmentIdentity(OTHER_ATTACHMENT_KEY, TENANT, OTHER_ULID),
        )

        assert plan_reference(reference, OTHER_ATTACHMENT_KEY, TENANT, index).verdict == "unresolved"

    def test_a_plain_api_uri_is_still_rewritten_onto_the_key_it_carries(self) -> None:
        """The control — the anchored rewrite must survive the narrowing."""
        index = _index(AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID))
        verdict = plan_reference(
            f"/api/v1/t/{TENANT}/attachments/{ATTACHMENT_KEY}", ATTACHMENT_KEY, TENANT, index
        )

        assert verdict.verdict == "repaired"
        assert verdict.matches == (ATTACHMENT_KEY,)

    def test_the_two_consumers_read_one_uri_the_same_way(self) -> None:
        """v0046 and ``normalize_photo_ref`` must not disagree on what a URI denotes.

        They did: the normaliser took the **first** segment after ``/attachments/``,
        v0046 the **last** one. One string, two answers, and the one that wrote was
        the one that was wrong.
        """
        from app.migrations.migrate_photo_refs import normalize_photo_ref

        thumbnail_uri = f"/api/v1/t/{TENANT}/attachments/{ATTACHMENT_KEY}/thumbnails/320"
        index = _index(AttachmentIdentity(ATTACHMENT_KEY, TENANT, ULID))

        assert normalize_photo_ref(thumbnail_uri) == ATTACHMENT_KEY
        assert plan_reference(thumbnail_uri, "320", TENANT, index).matches == (
            normalize_photo_ref(thumbnail_uri),
        )

# ── the migration against a fake ArangoDB ─────────────────────────────────────

#: The carrier scan, as it has to be spelled: filtered and projected in the database.
_CARRIER_RE = re.compile(
    r"^FOR d IN (\w+)\s+FILTER d\.(\w+) != null\s+"
    r"RETURN \{_key: d\._key, tenant_key: d\.tenant_key, value: d\.(\w+)\}$"
)

#: Reads the reduction out of the query rather than knowing it.
_STEM_RE = re.compile(r'FIRST\(SPLIT\(LAST\(SPLIT\(\s*([^,]+?)\s*,\s*"([^"]*)"\s*\)\)\s*,\s*"([^"]*)"\s*\)\)')


def _stem_from_query(query: str, value: str | None) -> str | None:
    match = _STEM_RE.search(query)
    if match is None:
        raise AssertionError(
            "the migration no longer reduces a storage key through the repository's "
            f"stem expression; query was: {query!r}"
        )
    _field, outer, inner = match.groups()
    if not value or not outer or not inner:
        return None
    return value.split(outer)[-1].split(inner)[0] or None


class _FakeAql:
    """Interprets exactly the four queries the migration issues."""

    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.writes: list[tuple[str, dict[str, Any]]] = []
        self.queries: list[str] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        stripped = query.strip()
        self.queries.append(stripped)

        if stripped.startswith("UPDATE"):
            self.writes.append((query, dict(bind_vars)))
            collection = stripped.rsplit(" IN ", 1)[1].strip()
            field = stripped.split("@key,", 1)[1].split(":", 1)[0].strip()
            for doc in self._collections.get(collection, []):
                if doc["_key"] == bind_vars["key"]:
                    doc[field] = bind_vars["value"]
            return iter([])

        if stripped.startswith("FOR ref IN @refs"):
            return iter([{"ref": ref, "stem": _stem_from_query(query, ref)} for ref in bind_vars["refs"]])

        if stripped.startswith(f"FOR a IN {col.ATTACHMENTS}"):
            return iter(
                [
                    {
                        "key": doc["_key"],
                        "tenant_key": doc.get("tenant_key"),
                        "stem": _stem_from_query(query, doc.get("storage_key")),
                    }
                    for doc in self._collections.get(col.ATTACHMENTS, [])
                ]
            )

        match = _CARRIER_RE.match(stripped)
        if match is None:
            raise AssertionError(
                "the carrier scan must project and filter server-side — it runs under "
                "the migration lock in the startup path, where pulling whole documents "
                "of every carrier collection into memory times the other replicas out "
                f"(B-2). Query was: {stripped!r}"
            )
        collection, filtered_field, projected_field = match.groups()
        assert filtered_field == projected_field, "the filter and the projection must name one field"
        return (
            {"_key": doc["_key"], "tenant_key": doc.get("tenant_key"), "value": doc[projected_field]}
            for doc in self._collections.get(collection, [])
            if doc.get(projected_field) is not None
        )


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.collections = collections
        self.aql = _FakeAql(collections)

    def has_collection(self, name: str) -> bool:
        """Only the seeded collections exist — a partially bootstrapped database."""
        return name in self.collections


def _attachment(key: str = ATTACHMENT_KEY, *, tenant: str = TENANT, storage_key: str = STORAGE_KEY):
    return {"_key": key, "tenant_key": tenant, "storage_key": storage_key, "category": "task"}


def _seeded(*, photo_refs: list[str], attachments: list[dict[str, Any]] | None = None):
    return {
        col.ATTACHMENTS: attachments if attachments is not None else [_attachment()],
        col.TASKS: [{"_key": "task-1", "tenant_key": TENANT, "photo_refs": list(photo_refs)}],
    }


@pytest.fixture
def db_with_broken_reference() -> _FakeDb:
    """Exactly what v0003 left behind: the ULID stem instead of the document key."""
    return _FakeDb(_seeded(photo_refs=[ULID]))


class TestUp:
    def test_the_stem_v0003_wrote_is_rewritten_onto_the_document_key(self, db_with_broken_reference: _FakeDb) -> None:
        report = migration.up(db_with_broken_reference)

        assert db_with_broken_reference.collections[col.TASKS][0]["photo_refs"] == [ATTACHMENT_KEY]
        assert report.details["repaired"] == 1
        assert report.changed == 1
        assert report.details["unresolved"] == []
        assert report.details["per_collection"][col.TASKS]["repaired"] == 1

    def test_a_full_storage_key_is_rewritten_too(self) -> None:
        """The spelling v0003 was *supposed* to leave alone still names its owner."""
        db = _FakeDb(_seeded(photo_refs=[STORAGE_KEY]))

        report = migration.up(db)

        assert db.collections[col.TASKS][0]["photo_refs"] == [ATTACHMENT_KEY]
        assert report.details["repaired"] == 1

    def test_an_unresolvable_entry_is_kept_verbatim_and_reported(self) -> None:
        db = _FakeDb(_seeded(photo_refs=[OTHER_ULID]))

        report = migration.up(db)

        assert db.collections[col.TASKS][0]["photo_refs"] == [OTHER_ULID]
        assert report.changed == 0
        assert report.details["unresolved_total"] == 1
        assert report.details["unresolved"] == [
            {
                "collection": col.TASKS,
                "document": "task-1",
                "field": "photo_refs",
                "tenant_key": TENANT,
                "reference": OTHER_ULID,
            }
        ]

    def test_a_foreign_tenants_attachment_never_repairs_the_reference(self) -> None:
        db = _FakeDb(_seeded(photo_refs=[ULID], attachments=[_attachment(tenant=OTHER_TENANT)]))

        report = migration.up(db)

        assert db.collections[col.TASKS][0]["photo_refs"] == [ULID]
        assert report.details["repaired"] == 0
        assert report.details["unresolved_total"] == 1

    def test_an_ambiguous_entry_is_reported_and_left_alone(self) -> None:
        """A tenant-less carrier: uniqueness is installation-wide, two rows answer."""
        db = _FakeDb(
            {
                col.ATTACHMENTS: [
                    _attachment(),
                    _attachment(
                        OTHER_ATTACHMENT_KEY,
                        tenant=OTHER_TENANT,
                        storage_key=f"t/{OTHER_TENANT}/task/2026/01/{ULID}.jpg",
                    ),
                ],
                col.HARVEST_OBSERVATIONS: [{"_key": "obs-1", "photo_refs": [ULID]}],
            }
        )

        report = migration.up(db)

        assert db.collections[col.HARVEST_OBSERVATIONS][0]["photo_refs"] == [ULID]
        assert report.changed == 0
        assert report.details["ambiguous"] == [
            {
                "collection": col.HARVEST_OBSERVATIONS,
                "document": "obs-1",
                "field": "photo_refs",
                "tenant_key": None,
                "reference": ULID,
                "matches": [ATTACHMENT_KEY, OTHER_ATTACHMENT_KEY],
            }
        ]

    def test_a_canonical_entry_beside_a_broken_one_survives_in_place(self) -> None:
        db = _FakeDb(
            {
                col.ATTACHMENTS: [
                    _attachment(),
                    _attachment(
                        OTHER_ATTACHMENT_KEY,
                        storage_key=f"t/{TENANT}/task/2026/01/{OTHER_ULID}.jpg",
                    ),
                ],
                col.TASKS: [
                    {
                        "_key": "task-1",
                        "tenant_key": TENANT,
                        "photo_refs": [OTHER_ATTACHMENT_KEY, ULID],
                    }
                ],
            }
        )

        migration.up(db)

        assert db.collections[col.TASKS][0]["photo_refs"] == [OTHER_ATTACHMENT_KEY, ATTACHMENT_KEY]

    def test_the_scalar_cover_photo_ref_is_reconciled_too(self) -> None:
        db = _FakeDb(
            {
                col.ATTACHMENTS: [_attachment()],
                col.PLANT_INSTANCES: [{"_key": "plant-1", "tenant_key": TENANT, "cover_photo_ref": ULID}],
            }
        )

        report = migration.up(db)

        assert db.collections[col.PLANT_INSTANCES][0]["cover_photo_ref"] == ATTACHMENT_KEY
        assert report.details["per_collection"][col.PLANT_INSTANCES]["repaired"] == 1

    def test_re_running_changes_nothing(self, db_with_broken_reference: _FakeDb) -> None:
        migration.up(db_with_broken_reference)

        second = migration.up(db_with_broken_reference)

        assert second.changed == 0
        assert second.details["repaired"] == 0
        assert second.details["unresolved"] == []
        assert db_with_broken_reference.collections[col.TASKS][0]["photo_refs"] == [ATTACHMENT_KEY]

    def test_dry_run_reports_the_repair_and_writes_nothing(self, db_with_broken_reference: _FakeDb) -> None:
        report = migration.up(db_with_broken_reference, dry_run=True)

        assert report.dry_run is True
        assert report.changed == 1
        assert report.details["repaired"] == 1
        assert db_with_broken_reference.collections[col.TASKS][0]["photo_refs"] == [ULID]
        assert db_with_broken_reference.aql.writes == []

    def test_an_empty_database_is_a_no_op(self) -> None:
        report = migration.up(_FakeDb({}))

        assert report.scanned == 0
        assert report.changed == 0

    def test_a_document_without_references_never_reaches_python(self) -> None:
        """The scan runs under the migration lock in the startup path (B-2).

        Pulling whole documents of every carrier collection into the migrating
        replica's memory is what times the *other* replicas out
        (``MigrationBarrierTimeoutError``), and on the overwhelmingly common
        installation almost none of those documents carry a photo at all. So the
        filter belongs in the database: an installation without photos costs O(0)
        rows, not O(all tasks).
        """
        db = _FakeDb(
            {
                col.ATTACHMENTS: [_attachment()],
                col.TASKS: [{"_key": "task-1", "tenant_key": TENANT, "title": "no photo here"}],
            }
        )

        report = migration.up(db)

        assert report.scanned == 0
        assert col.TASKS not in report.details["per_collection"]
        carrier_queries = [q for q in db.aql.queries if q.startswith(f"FOR d IN {col.TASKS}")]
        assert carrier_queries, "the carrier was not scanned at all"
        assert all("FILTER" in q and "RETURN d\n" not in q and not q.endswith("RETURN d") for q in carrier_queries)

    def test_the_attachment_catalogue_is_projected_too(self) -> None:
        """Three fields per row, not the whole attachment document."""
        db = _FakeDb(_seeded(photo_refs=[ULID]))

        migration.up(db)

        catalogue = [q for q in db.aql.queries if q.startswith(f"FOR a IN {col.ATTACHMENTS}")]
        assert catalogue, "the catalogue was not read"
        assert all(q.endswith("}") and "RETURN {key: a._key" in q for q in catalogue)

    def test_down_refuses(self) -> None:
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb({}))
