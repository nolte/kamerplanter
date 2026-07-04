"""#306 — retired ``harvest`` phase reclassification migration.

Verifies feeding-vs-flush routing, idempotency, dry-run and non-destructiveness.
"""

from app.migrations.migrate_nutrient_phase_harvest import migrate_nutrient_phase_harvest


class _FakeAql:
    """Minimal AQL stub: filtered scan lists harvest docs, UPDATE mutates them."""

    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        if query.strip().startswith("UPDATE"):
            key = bind_vars["key"]
            new_phase = bind_vars["new_phase"]
            for doc in self._docs:
                if doc["_key"] == key:
                    doc["phase_name"] = new_phase
            return []
        # FILTER doc.phase_name == @harvest scan
        harvest = bind_vars["harvest"]
        return [
            {"_key": d["_key"], "npk_ratio": d.get("npk_ratio")} for d in self._docs if d.get("phase_name") == harvest
        ]


class _FakeDb:
    def __init__(self, docs: list[dict]) -> None:
        self.aql = _FakeAql(docs)


def _docs() -> list[dict]:
    return [
        # Feeding harvest → ripening
        {"_key": "p1", "phase_name": "harvest", "npk_ratio": [5.0, 3.0, 8.0]},
        # 0-0-0 flush → flushing
        {"_key": "p2", "phase_name": "harvest", "npk_ratio": [0.0, 0.0, 0.0]},
        # Missing npk_ratio → treated as flush
        {"_key": "p3", "phase_name": "harvest"},
        # Non-harvest documents must never be touched
        {"_key": "p4", "phase_name": "flowering", "npk_ratio": [10.0, 5.0, 7.0]},
        {"_key": "p5", "phase_name": "ripening", "npk_ratio": [0.0, 0.0, 0.0]},
    ]


class TestHarvestPhaseMigration:
    def test_routes_feeding_and_flush(self):
        docs = _docs()
        report = migrate_nutrient_phase_harvest(_FakeDb(docs))

        assert report.scanned == 3
        assert report.reclassified == 3
        assert report.to_ripening == 1
        assert report.to_flushing == 2
        assert set(report.changed_keys) == {"p1", "p2", "p3"}

        by_key = {d["_key"]: d for d in docs}
        assert by_key["p1"]["phase_name"] == "ripening"
        assert by_key["p2"]["phase_name"] == "flushing"
        assert by_key["p3"]["phase_name"] == "flushing"
        # Non-harvest documents stay exactly as they were.
        assert by_key["p4"]["phase_name"] == "flowering"
        assert by_key["p5"]["phase_name"] == "ripening"

    def test_dry_run_changes_nothing(self):
        docs = _docs()
        report = migrate_nutrient_phase_harvest(_FakeDb(docs), dry_run=True)

        assert report.reclassified == 3
        # Dry-run must not mutate any document.
        assert docs[0]["phase_name"] == "harvest"
        assert docs[1]["phase_name"] == "harvest"

    def test_idempotent_second_run_is_noop(self):
        docs = _docs()
        migrate_nutrient_phase_harvest(_FakeDb(docs))
        report2 = migrate_nutrient_phase_harvest(_FakeDb(docs))
        assert report2.scanned == 0
        assert report2.reclassified == 0
