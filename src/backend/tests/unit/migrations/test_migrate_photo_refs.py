"""NFR-013 §2.2 / AC-09 — photo_refs normalisation migration.

Verifies the pure normaliser, the idempotent + non-destructive DB walk and the
no-op report on already-normalised data.
"""

from app.migrations.migrate_photo_refs import (
    normalize_photo_ref,
    normalize_refs,
    run,
)

ULID = "01HQ8X9V3J7P5K2N4M6T8R0S2W"


class TestNormalizePhotoRef:
    def test_plain_attachment_id_is_unchanged(self):
        assert normalize_photo_ref(ULID) == ULID

    def test_s3_url_is_reduced_to_attachment_id(self):
        assert normalize_photo_ref(f"s3://kamerplanter/diary/2026/04/{ULID}.jpg") == ULID

    def test_storage_key_is_reduced_to_attachment_id(self):
        assert normalize_photo_ref(f"t/personal_max/diary/2026/04/{ULID}.jpg") == ULID

    def test_api_uri_is_reduced_to_attachment_id(self):
        assert normalize_photo_ref(f"/api/v1/t/personal_max/attachments/{ULID}") == ULID

    def test_thumbnail_suffix_is_stripped(self):
        assert normalize_photo_ref(f"t/x/diary/2026/04/{ULID}_t512.webp") == ULID

    def test_empty_is_unchanged(self):
        assert normalize_photo_ref("") == ""
        assert normalize_photo_ref("   ") == "   "

    def test_unresolvable_value_is_kept_verbatim(self):
        # Never drop a value we can't parse — keep it for manual inspection.
        assert normalize_photo_ref("legacy-weird-name") == "legacy-weird-name"


class TestNormalizeRefs:
    def test_counts_only_changed_entries(self):
        refs = [ULID, f"s3://b/diary/{ULID}.jpg"]
        out, changed = normalize_refs(refs)
        assert out == [ULID, ULID]
        assert changed == 1

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
    from app.data_access.arango import collections as col

    collections = {
        col.PLANT_DIARY_ENTRIES: _FakeCollection(docs),
        col.HARVEST_BATCHES: _FakeCollection({}),
        col.INSPECTIONS: _FakeCollection({}),
        col.TASKS: _FakeCollection({}),
    }
    return _FakeDb(collections)


class TestRun:
    def test_migrates_and_is_idempotent(self):
        docs = {
            "d1": {"photo_refs": [f"s3://b/diary/{ULID}.jpg"]},
            "d2": {"photo_refs": [ULID]},  # already normalised
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
        docs = {"d1": {"photo_refs": [f"s3://b/diary/{ULID}.jpg"]}}
        db = _db_with_diary(docs)
        from app.data_access.arango import collections as col

        report = run(db, dry_run=True)
        assert report.changed_documents == 1
        # Nothing was written.
        assert db.collection(col.PLANT_DIARY_ENTRIES).updates == []
        assert docs["d1"]["photo_refs"] == [f"s3://b/diary/{ULID}.jpg"]

    def test_never_drops_values(self):
        docs = {"d1": {"photo_refs": [ULID, "weird-legacy", f"s3://b/x/{ULID}.png"]}}
        db = _db_with_diary(docs)
        run(db, dry_run=False)
        # Same length, the unresolvable value is preserved.
        assert len(docs["d1"]["photo_refs"]) == 3
        assert "weird-legacy" in docs["d1"]["photo_refs"]

    def test_empty_dataset_is_noop(self):
        db = _db_with_diary({})
        report = run(db, dry_run=False)
        assert report.scanned_documents == 0
        assert report.as_dict()["noop"] is True
