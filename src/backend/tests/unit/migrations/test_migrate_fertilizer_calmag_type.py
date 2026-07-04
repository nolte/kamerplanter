"""DOM-6 — CalMag type backfill migration.

Verifies name-matched reclassification, idempotency and non-destructiveness.
"""

from app.migrations.migrate_fertilizer_calmag_type import migrate_fertilizer_calmag_type


class _FakeAql:
    """Minimal AQL stub: first call lists docs, UPDATE calls mutate them."""

    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def execute(self, query: str, bind_vars: dict | None = None):
        if query.strip().startswith("UPDATE"):
            key = bind_vars["key"]
            new_type = bind_vars["new_type"]
            for doc in self._docs:
                if doc["_key"] == key:
                    doc["fertilizer_type"] = new_type
            return []
        # SELECT-style scan
        return [
            {"_key": d["_key"], "product_name": d["product_name"], "fertilizer_type": d["fertilizer_type"]}
            for d in self._docs
        ]


class _FakeDb:
    def __init__(self, docs: list[dict]) -> None:
        self.aql = _FakeAql(docs)


def _docs() -> list[dict]:
    return [
        {"_key": "f1", "product_name": "CaliMagic", "fertilizer_type": "supplement"},
        {"_key": "f2", "product_name": "Cal-Mag Plus", "fertilizer_type": "supplement"},
        {"_key": "f3", "product_name": "Calcium Nitrate", "fertilizer_type": "base"},
        {"_key": "f4", "product_name": "Already CalMag", "fertilizer_type": "calmag"},
    ]


class TestCalmagMigration:
    def test_reclassifies_name_matches(self):
        docs = _docs()
        report = migrate_fertilizer_calmag_type(_FakeDb(docs))

        assert report.scanned == 4
        assert report.reclassified == 2
        assert set(report.changed_keys) == {"f1", "f2"}

        by_key = {d["_key"]: d for d in docs}
        assert by_key["f1"]["fertilizer_type"] == "calmag"
        assert by_key["f2"]["fertilizer_type"] == "calmag"
        # Non-CalMag base fertilizer untouched (no false positive).
        assert by_key["f3"]["fertilizer_type"] == "base"
        # Already-typed document untouched.
        assert by_key["f4"]["fertilizer_type"] == "calmag"

    def test_dry_run_changes_nothing(self):
        docs = _docs()
        report = migrate_fertilizer_calmag_type(_FakeDb(docs), dry_run=True)

        assert report.reclassified == 2
        # Dry-run must not mutate documents.
        assert docs[0]["fertilizer_type"] == "supplement"
        assert docs[1]["fertilizer_type"] == "supplement"

    def test_idempotent_second_run_is_noop(self):
        docs = _docs()
        migrate_fertilizer_calmag_type(_FakeDb(docs))
        report2 = migrate_fertilizer_calmag_type(_FakeDb(docs))
        assert report2.reclassified == 0
