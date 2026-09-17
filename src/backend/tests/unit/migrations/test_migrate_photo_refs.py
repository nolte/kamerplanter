"""NFR-013 §2.2 / AC-09 — photo_refs normalisation migration.

Verifies the pure normaliser, the idempotent + non-destructive DB walk and the
no-op report on already-normalised data.

**Three assertions in this file used to demand the opposite of what they demand
now** (#1438). They pinned the reduction of a storage key / an ``s3://`` URL to
the ULID stem of its last path segment as the required behaviour — the very
rewrite the module header had already been measured and recorded as false: that
ULID is minted by ``StorageKeyBuilder.build`` and is unrelated to the attachment's
``_key``, which ArangoDB assigns numerically. So the "normalised" value resolves
to no attachment, while the unrewritten storage key resolves correctly through
``ArangoAttachmentRepository``'s ``storage_key`` comparison. Anyone keeping this
suite green kept the defect alive; the assertions now demand the storage-key
spellings stay **verbatim**.
"""

from app.migrations.migrate_photo_refs import (
    normalize_photo_ref,
    normalize_refs,
    run,
)

ULID = "01HQ8X9V3J7P5K2N4M6T8R0S2W"
#: The one spelling the migration still rewrites: an API URI carries the
#: attachment's ``_key`` in its ``/attachments/{id}`` segment, so reducing it to
#: that segment yields a reference that resolves.
API_URI = f"/api/v1/t/personal_max/attachments/{ULID}"


class TestNormalizePhotoRef:
    def test_plain_attachment_id_is_unchanged(self):
        assert normalize_photo_ref(ULID) == ULID

    def test_s3_url_is_kept_verbatim(self):
        """An ``s3://`` URL is a storage key with a scheme, and stays one.

        Its last segment is the ULID ``StorageKeyBuilder`` minted for the object,
        not the attachment's ``_key``; reducing the reference to it would point at
        no document, while the full key resolves against ``Attachment.storage_key``.
        """
        reference = f"s3://kamerplanter/diary/2026/04/{ULID}.jpg"
        assert normalize_photo_ref(reference) == reference

    def test_storage_key_is_kept_verbatim(self):
        """The shape ``StorageKeyBuilder.build`` emits resolves as-is; do not touch it.

        Same reason as the ``s3://`` row: the resolver compares a reference against
        the attachment's own ``storage_key``, so the *whole* key is the working
        reference and its ULID stem is a foreign id.
        """
        reference = f"t/personal_max/diary/2026/04/{ULID}.jpg"
        assert normalize_photo_ref(reference) == reference

    def test_api_uri_is_reduced_to_attachment_id(self):
        assert normalize_photo_ref(f"/api/v1/t/personal_max/attachments/{ULID}") == ULID

    def test_thumbnail_storage_key_is_kept_verbatim(self):
        """A thumbnail rendition is a storage key too — the same false premise.

        Stripping ``_t512`` yielded the object ULID, which is not an attachment
        ``_key`` either, so the "repaired" value resolved to nothing while the
        original at least named a real object.
        """
        reference = f"t/x/diary/2026/04/{ULID}_t512.webp"
        assert normalize_photo_ref(reference) == reference

    def test_a_storage_key_whose_category_segment_is_attachments_is_kept_verbatim(self):
        """The rewrite rule must recognise the *API URI*, not the word "attachments".

        ``StorageKeyBuilder.build`` puts the attachment category into the third
        segment (``t/{tenant}/{category}/{yyyy}/{mm}/{ulid}.{ext}``). A layout whose
        category reads ``attachments`` therefore contains ``/attachments/`` without
        being an API URI at all, and the unanchored pattern read the *year* out of it
        as the attachment id — replacing a reference the resolver resolves through
        ``Attachment.storage_key`` with the string ``"2026"``, which is a plausible
        numeric document key (#1438 review, O-5).
        """
        reference = f"t/personal_max/attachments/2026/04/{ULID}.jpg"
        assert normalize_photo_ref(reference) == reference

    def test_an_s3_url_containing_attachments_is_kept_verbatim(self):
        """Same hazard behind a scheme: a bucket prefix is not an API route."""
        reference = f"s3://kamerplanter/attachments/2026/04/{ULID}.jpg"
        assert normalize_photo_ref(reference) == reference

    def test_the_api_uri_is_recognised_with_an_absolute_host(self):
        """The anchor must not cost the spellings that really are API URIs."""
        assert normalize_photo_ref(f"https://garten.example/api/v1/t/max/attachments/{ULID}") == ULID

    def test_empty_is_unchanged(self):
        assert normalize_photo_ref("") == ""
        assert normalize_photo_ref("   ") == "   "

    def test_unresolvable_value_is_kept_verbatim(self):
        # Never drop a value we can't parse — keep it for manual inspection.
        assert normalize_photo_ref("legacy-weird-name") == "legacy-weird-name"


class TestNormalizeRefs:
    def test_counts_only_changed_entries(self):
        refs = [ULID, API_URI]
        out, changed = normalize_refs(refs)
        assert out == [ULID, ULID]
        assert changed == 1

    def test_a_storage_key_entry_is_not_counted_as_changed(self):
        """A list of working storage keys is a no-op, not a rewrite (#1438)."""
        refs = [f"t/personal_max/diary/2026/04/{ULID}.jpg"]
        out, changed = normalize_refs(refs)
        assert out == refs
        assert changed == 0

    def test_already_normalised_is_noop(self):
        out, changed = normalize_refs([ULID, ULID])
        assert out == [ULID, ULID]
        assert changed == 0


class _FakeCursor(list):
    pass


class _FakeCollection:
    def __init__(self, docs: dict[str, dict]) -> None:
        self._docs = docs
        self.updates: list[dict] = []

    def update(self, doc: dict) -> None:
        self.updates.append(doc)
        self._docs[doc["_key"]]["photo_refs"] = doc["photo_refs"]


class _FakeAql:
    def __init__(self, collections: dict[str, _FakeCollection]) -> None:
        self._collections = collections

    def execute(self, query, bind_vars):  # noqa: ARG002 — query text is fixed
        name = bind_vars["@collection"]
        coll = self._collections.get(name)
        if coll is None:
            return _FakeCursor()
        rows = [
            {"_key": key, "refs": doc["photo_refs"]}
            for key, doc in coll._docs.items()
            if isinstance(doc.get("photo_refs"), list) and doc["photo_refs"]
        ]
        return _FakeCursor(rows)


class _FakeDb:
    def __init__(self, collections: dict[str, _FakeCollection]) -> None:
        self._collections = collections
        self.aql = _FakeAql(collections)

    def collection(self, name: str) -> _FakeCollection:
        return self._collections[name]


def _db_with_diary(docs: dict[str, dict]) -> _FakeDb:
    """A fake holding every carrier the migration walks, with the docs in the diary.

    Built from ``migrate_photo_refs``' own list rather than a hand-kept copy. The copy
    this replaces named the four collections the migration used to walk — including
    ``HARVEST_BATCHES``, which has no ``photo_refs`` at all — so it could not have
    noticed that the migration was skipping ``plant_instances``,
    ``harvest_observations`` and ``storage_observations``. A fake that mirrors a wrong
    list certifies the wrong list.

    Deriving it here is safe in a way it would not be for the carrier list itself:
    what this file tests is *normalisation*, and the membership of that list is pinned
    against the models in ``tests/unit/data_access/arango/test_photo_ref_carriers.py``.
    """
    from app.data_access.arango import collections as col
    from app.migrations.migrate_photo_refs import _PHOTO_REF_COLLECTIONS

    collections = {name: _FakeCollection({}) for name in _PHOTO_REF_COLLECTIONS}
    collections[col.PLANT_DIARY_ENTRIES] = _FakeCollection(docs)
    return _FakeDb(collections)


class TestCliDryRunDefault:
    """The CLI writes only on ``--write`` (#1438).

    It used to write unless ``--dry-run`` was passed, which made the destructive
    direction the default one for an irreversible rewrite.
    """

    def test_no_argument_means_dry_run(self):
        from app.migrations.migrate_photo_refs import dry_run_from_argv

        assert dry_run_from_argv([]) is True

    def test_write_flag_turns_writing_on(self):
        from app.migrations.migrate_photo_refs import dry_run_from_argv

        assert dry_run_from_argv(["--write"]) is False

    def test_explicit_dry_run_wins_over_write(self):
        from app.migrations.migrate_photo_refs import dry_run_from_argv

        assert dry_run_from_argv(["--write", "--dry-run"]) is True


class TestRun:
    def test_migrates_and_is_idempotent(self):
        docs = {
            "d1": {"photo_refs": [API_URI]},
            "d2": {"photo_refs": [ULID]},  # already an attachment id
        }
        db = _db_with_diary(docs)

        report = run(db, dry_run=False)
        assert report.changed_documents == 1
        assert report.changed_refs == 1
        assert docs["d1"]["photo_refs"] == [ULID]

        # Second run is a clean no-op (idempotent).
        report2 = run(db, dry_run=False)
        assert report2.changed_documents == 0
        assert report2.as_dict()["noop"] is True

    def test_dry_run_does_not_write(self):
        docs = {"d1": {"photo_refs": [API_URI]}}
        db = _db_with_diary(docs)
        from app.data_access.arango import collections as col

        report = run(db, dry_run=True)
        assert report.changed_documents == 1
        # Nothing was written.
        assert db.collection(col.PLANT_DIARY_ENTRIES).updates == []
        assert docs["d1"]["photo_refs"] == [API_URI]

    def test_run_writes_nothing_unless_asked_to(self):
        """Writing is an explicit decision: ``run`` defaults to ``dry_run=True``.

        This migration rewrites references irreversibly (``reversible = False``),
        and its premise was wrong once already. A caller that forgets the keyword
        must get the report, not a write.
        """
        docs = {"d1": {"photo_refs": [API_URI]}}
        db = _db_with_diary(docs)
        from app.data_access.arango import collections as col

        report = run(db)

        assert report.dry_run is True
        assert db.collection(col.PLANT_DIARY_ENTRIES).updates == []
        assert docs["d1"]["photo_refs"] == [API_URI]

    def test_never_drops_values(self):
        docs = {"d1": {"photo_refs": [ULID, "weird-legacy", API_URI]}}
        db = _db_with_diary(docs)
        run(db, dry_run=False)
        # Same length, the unresolvable value is preserved.
        assert len(docs["d1"]["photo_refs"]) == 3
        assert "weird-legacy" in docs["d1"]["photo_refs"]

    def test_a_storage_key_document_is_left_alone(self):
        """The regression #1438 names: a working reference must survive the run."""
        reference = f"t/personal_max/diary/2026/04/{ULID}.jpg"
        docs = {"d1": {"photo_refs": [reference]}}
        db = _db_with_diary(docs)
        from app.data_access.arango import collections as col

        report = run(db, dry_run=False)

        assert report.changed_documents == 0
        assert db.collection(col.PLANT_DIARY_ENTRIES).updates == []
        assert docs["d1"]["photo_refs"] == [reference]

    def test_empty_dataset_is_noop(self):
        db = _db_with_diary({})
        report = run(db, dry_run=False)
        assert report.scanned_documents == 0
        assert report.as_dict()["noop"] is True


def test_the_migration_walks_every_pinned_carrier():
    """The migration and the sweep must agree on where photo references live.

    They did not. The migration kept its own four-entry list, which named
    ``harvest_batches`` — a collection with no ``photo_refs`` — and omitted
    ``plant_instances``, ``harvest_observations`` and ``storage_observations``, all
    three of which carry it. So it reported success while leaving every legacy
    reference in the plant gallery unnormalised, and #1393's safety story names this
    migration as part of the reference history the orphan sweep has to survive.

    Asserted as *identity* with the pinned list rather than as a superset: a migration
    that walked more collections than the sweep protects would be writing to rows
    nothing checks, which is the same divergence in the other direction.
    """
    from app.data_access.arango.attachment_repository import PHOTO_REF_COLLECTIONS
    from app.migrations.migrate_photo_refs import _PHOTO_REF_COLLECTIONS

    assert tuple(_PHOTO_REF_COLLECTIONS) == tuple(PHOTO_REF_COLLECTIONS), (
        "the migration's carrier list drifted from the one the orphan sweep scans; "
        "the two must name the same collections or one of them is silently skipping "
        "rows the other protects (#1393)"
    )
