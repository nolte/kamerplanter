"""Tests for v0010_backfill_scientific_name_normalized (REQ-048 Stufe 1).

Covers the pure survivor-selection / field-merge helpers and end-to-end runs of
the migration against a dict-backed fake database:

* the observed ``Fragaria`` pair — the ×-row carrying the live plant survives,
  adopts the ASCII row's richer metadata (family, cultivar) and keeps the plant;
* SEC-001 — a loser referenced from many collections (grow-run entries,
  succession plans, starter-kit species lists, tasks, a lifecycle edge …) is
  fully repointed with NO dangling reference left behind;
* SEC-002 — a ``has_lifecycle`` collision deletes the loser's child document
  instead of orphaning it.
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.migrations.versions.v0010_backfill_scientific_name_normalized import (
    _merge_fields,
    _richness,
    _select_survivor,
    migration,
)

# ── Fake database (AQL for scans/backfill, collection API for reconcile) ──────


class _FakeCollection:
    def __init__(self, store: dict[str, dict]) -> None:
        self._store = store

    def all(self):
        return [dict(d) for d in self._store.values()]

    def get(self, key: str):
        doc = self._store.get(key)
        return dict(doc) if doc else None

    def update(self, doc: dict) -> None:
        self._store[doc["_key"]].update(doc)

    def insert(self, doc: dict) -> None:
        key = doc.get("_key") or f"gen_{len(self._store) + 1}_{id(doc)}"
        stored = dict(doc)
        stored["_key"] = key
        self._store[key] = stored

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        cols = self._db.cols

        if "COLLECT sk = p.species_key" in query:
            counts: dict[str, int] = {}
            for p in cols.get(col.PLANT_INSTANCES, {}).values():
                if p.get("removed_on") is None and p.get("species_key"):
                    counts[p["species_key"]] = counts.get(p["species_key"], 0) + 1
            return iter([{"species_key": k, "count": v} for k, v in counts.items()])

        if query.strip() == f"FOR d IN {col.SPECIES} RETURN d":
            return iter([dict(d) for d in cols[col.SPECIES].values()])

        if "FOR pair IN @pairs" in query:
            for pair in bind_vars["pairs"]:
                cols[col.SPECIES][pair["key"]]["scientific_name_normalized"] = pair["norm"]
            return iter([])

        raise AssertionError(f"unhandled query: {query!r}")


class _FakeDb:
    def __init__(self, cols: dict[str, dict[str, dict]]) -> None:
        self.cols = cols
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.cols

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(self.cols.setdefault(name, {}))


def _species_id(key: str) -> str:
    return f"{col.SPECIES}/{key}"


# ── Scenarios ────────────────────────────────────────────────────────────────


def _fragaria_db() -> _FakeDb:
    """The observed pair plus one unrelated species (plain backfill)."""
    return _FakeDb(
        {
            col.SPECIES: {
                "sp_sign": {
                    "_key": "sp_sign",
                    "scientific_name": "Fragaria × ananassa",
                    "scientific_name_normalized": "",
                    "family_key": None,
                    "genus": "",
                },
                "sp_ascii": {
                    "_key": "sp_ascii",
                    "scientific_name": "Fragaria x ananassa",
                    "scientific_name_normalized": "",
                    "family_key": "fam_rosaceae",
                    "genus": "Fragaria",
                },
                "sp_tomato": {
                    "_key": "sp_tomato",
                    "scientific_name": "Solanum lycopersicum",
                    "scientific_name_normalized": "",
                },
            },
            col.PLANT_INSTANCES: {
                "pi_1": {"_key": "pi_1", "species_key": "sp_sign", "removed_on": None},
            },
            col.CULTIVARS: {
                "cv_1": {"_key": "cv_1", "species_key": "sp_ascii", "name": "Elsanta"},
            },
            col.HAS_CULTIVAR: {
                "hc_1": {"_key": "hc_1", "_from": _species_id("sp_ascii"), "_to": f"{col.CULTIVARS}/cv_1"},
            },
            col.BELONGS_TO_FAMILY: {
                "bf_1": {
                    "_key": "bf_1",
                    "_from": _species_id("sp_ascii"),
                    "_to": f"{col.BOTANICAL_FAMILIES}/fam_rosaceae",
                },
            },
        }
    )


def _rich_loser_db() -> _FakeDb:
    """Survivor holds the live plant; loser is referenced from many collections."""
    return _FakeDb(
        {
            col.SPECIES: {
                "sp_keep": {
                    "_key": "sp_keep",
                    "scientific_name": "Fragaria × ananassa",
                    "scientific_name_normalized": "",
                    "family_key": "fam_rosaceae",
                },
                "sp_drop": {
                    "_key": "sp_drop",
                    "scientific_name": "Fragaria x ananassa",
                    "scientific_name_normalized": "",
                    "family_key": "fam_rosaceae",
                },
            },
            col.PLANT_INSTANCES: {
                "pi_live": {"_key": "pi_live", "species_key": "sp_keep", "removed_on": None},
            },
            col.PLANTING_RUN_ENTRIES: {
                "pre_1": {"_key": "pre_1", "species_key": "sp_drop"},
            },
            col.SUCCESSION_PLANS: {
                "sc_1": {"_key": "sc_1", "species_key": "sp_drop"},
            },
            col.TASKS: {
                "tk_1": {"_key": "tk_1", "species_key": "sp_drop"},
            },
            col.OVERWINTERING_PROFILE_TEMPLATES: {
                "ow_1": {"_key": "ow_1", "species_key": "sp_drop"},
            },
            col.HARVEST_INDICATORS: {
                "hi_1": {"_key": "hi_1", "species_key": "sp_drop"},
            },
            col.REFERENCE_IMAGE_JOBS: {
                "refjob_sp_drop": {"_key": "refjob_sp_drop", "species_key": "sp_drop"},
            },
            col.STARTER_KITS: {
                "kit_1": {"_key": "kit_1", "species_keys": ["sp_drop", "sp_other"]},
            },
            col.LIFECYCLE_CONFIGS: {
                "lc_drop": {"_key": "lc_drop", "species_key": "sp_drop"},
            },
            col.HAS_LIFECYCLE: {
                "hl_drop": {
                    "_key": "hl_drop",
                    "_from": _species_id("sp_drop"),
                    "_to": f"{col.LIFECYCLE_CONFIGS}/lc_drop",
                },
            },
            col.USER_FAVORITES: {
                "uf_1": {"_key": "uf_1", "_from": f"{col.USERS}/u1", "_to": _species_id("sp_drop")},
            },
            col.ENTRY_FOR_SPECIES: {
                "efs_1": {
                    "_key": "efs_1",
                    "_from": f"{col.PLANTING_RUN_ENTRIES}/pre_1",
                    "_to": _species_id("sp_drop"),
                },
            },
        }
    )


def _identification_ref_db() -> _FakeDb:
    """Loser is referenced only from a nested ``results[].matched_species_key`` (SEC-101)."""
    return _FakeDb(
        {
            col.SPECIES: {
                "sp_keep": {
                    "_key": "sp_keep",
                    "scientific_name": "Fragaria × ananassa",
                    "scientific_name_normalized": "",
                },
                "sp_drop": {
                    "_key": "sp_drop",
                    "scientific_name": "Fragaria x ananassa",
                    "scientific_name_normalized": "",
                },
            },
            col.PLANT_INSTANCES: {
                "pi_live": {"_key": "pi_live", "species_key": "sp_keep", "removed_on": None},
            },
            col.IDENTIFICATION_REQUESTS: {
                "ir_1": {
                    "_key": "ir_1",
                    "tenant_key": "t1",
                    "results": [
                        {"rank": 1, "scientific_name": "Fragaria x ananassa", "matched_species_key": "sp_drop"},
                        {"rank": 2, "scientific_name": "Solanum lycopersicum", "matched_species_key": None},
                    ],
                },
            },
        }
    )


def _lifecycle_collision_db() -> _FakeDb:
    """Both survivor and loser own a lifecycle → the loser's child is deleted."""
    return _FakeDb(
        {
            col.SPECIES: {
                "sp_keep": {
                    "_key": "sp_keep",
                    "scientific_name": "Fragaria × ananassa",
                    "scientific_name_normalized": "",
                },
                "sp_drop": {
                    "_key": "sp_drop",
                    "scientific_name": "Fragaria x ananassa",
                    "scientific_name_normalized": "",
                },
            },
            col.PLANT_INSTANCES: {
                "pi_keep": {"_key": "pi_keep", "species_key": "sp_keep", "removed_on": None},
                "pi_keep2": {"_key": "pi_keep2", "species_key": "sp_keep", "removed_on": None},
            },
            col.LIFECYCLE_CONFIGS: {
                "lc_keep": {"_key": "lc_keep", "species_key": "sp_keep"},
                "lc_drop": {"_key": "lc_drop", "species_key": "sp_drop"},
            },
            col.HAS_LIFECYCLE: {
                "hl_keep": {
                    "_key": "hl_keep",
                    "_from": _species_id("sp_keep"),
                    "_to": f"{col.LIFECYCLE_CONFIGS}/lc_keep",
                },
                "hl_drop": {
                    "_key": "hl_drop",
                    "_from": _species_id("sp_drop"),
                    "_to": f"{col.LIFECYCLE_CONFIGS}/lc_drop",
                },
            },
        }
    )


class TestPureHelpers:
    def test_richness_counts_non_empty_fields(self):
        assert _richness({"_key": "x", "a": 1, "b": "", "c": None, "d": "v"}) == 2

    def test_survivor_prefers_active_plants(self):
        group = [{"_key": "rich", "family_key": "f", "genus": "G"}, {"_key": "live"}]
        assert _select_survivor(group, {"live": 1})["_key"] == "live"

    def test_survivor_tie_breaks_on_richness_then_key(self):
        group = [{"_key": "b"}, {"_key": "a", "family_key": "f"}]
        assert _select_survivor(group, {})["_key"] == "a"

    def test_merge_fields_fills_empty_only_and_protects_display(self):
        survivor = {"_key": "s", "scientific_name": "Fragaria × ananassa", "family_key": None, "genus": "Fragaria"}
        loser = {"_key": "l", "scientific_name": "Fragaria x ananassa", "family_key": "fam", "genus": "Other"}
        assert _merge_fields(survivor, loser) == {"family_key": "fam"}


class TestFragariaReconcile:
    def test_survivor_keeps_plant_and_adopts_metadata(self):
        db = _fragaria_db()
        migration.up(db)

        species = db.cols[col.SPECIES]
        assert "sp_ascii" not in species
        survivor = species["sp_sign"]
        assert survivor["family_key"] == "fam_rosaceae"
        assert survivor["genus"] == "Fragaria"
        assert survivor["scientific_name"] == "Fragaria × ananassa"
        assert survivor["scientific_name_normalized"] == "fragaria x ananassa"

    def test_active_plant_not_orphaned(self):
        db = _fragaria_db()
        migration.up(db)
        assert db.cols[col.PLANT_INSTANCES]["pi_1"]["species_key"] == "sp_sign"

    def test_cultivar_repointed_to_survivor(self):
        db = _fragaria_db()
        migration.up(db)
        assert db.cols[col.CULTIVARS]["cv_1"]["species_key"] == "sp_sign"
        edges = list(db.cols[col.HAS_CULTIVAR].values())
        assert len(edges) == 1
        assert edges[0]["_from"] == _species_id("sp_sign")

    def test_family_edge_reestablished_for_survivor(self):
        db = _fragaria_db()
        migration.up(db)
        edges = list(db.cols[col.BELONGS_TO_FAMILY].values())
        assert len(edges) == 1
        assert edges[0]["_from"] == _species_id("sp_sign")
        assert edges[0]["_to"] == f"{col.BOTANICAL_FAMILIES}/fam_rosaceae"

    def test_unrelated_species_backfilled(self):
        db = _fragaria_db()
        migration.up(db)
        assert db.cols[col.SPECIES]["sp_tomato"]["scientific_name_normalized"] == "solanum lycopersicum"

    def test_report_counts(self):
        db = _fragaria_db()
        report = migration.up(db)
        assert report.changed == 3  # 2 survivors backfilled + 1 loser merged away
        assert report.scanned == 3
        group_report = report.details["reconciled_groups"][0]
        assert group_report["survivor"] == "sp_sign"
        assert group_report["losers"] == ["sp_ascii"]
        assert group_report["plants_repointed"] == 0
        assert group_report["cultivars_repointed"] == 1

    def test_rerun_is_a_noop(self):
        db = _fragaria_db()
        migration.up(db)
        report = migration.up(db)
        assert report.changed == 0
        assert report.noop is True

    def test_dry_run_writes_nothing_and_reports_planned_moves(self):
        db = _fragaria_db()
        report = migration.up(db, dry_run=True)
        assert report.dry_run is True
        assert report.changed == 0
        assert "sp_ascii" in db.cols[col.SPECIES]  # nothing merged
        assert db.cols[col.SPECIES]["sp_tomato"]["scientific_name_normalized"] == ""
        moves = report.details["planned_reference_moves"]
        assert moves[col.CULTIVARS] == 1
        assert moves[col.HAS_CULTIVAR] == 1
        assert moves[col.BELONGS_TO_FAMILY] == 1

    def test_migration_metadata(self):
        assert migration.version == "0010"
        assert migration.reversible is False


class TestSec001NoDanglingReferences:
    def test_all_references_repointed_to_survivor(self):
        db = _rich_loser_db()
        migration.up(db)

        assert "sp_drop" not in db.cols[col.SPECIES]
        # Scalar references moved onto the survivor.
        assert db.cols[col.PLANTING_RUN_ENTRIES]["pre_1"]["species_key"] == "sp_keep"
        assert db.cols[col.SUCCESSION_PLANS]["sc_1"]["species_key"] == "sp_keep"
        assert db.cols[col.TASKS]["tk_1"]["species_key"] == "sp_keep"
        assert db.cols[col.OVERWINTERING_PROFILE_TEMPLATES]["ow_1"]["species_key"] == "sp_keep"
        assert db.cols[col.HARVEST_INDICATORS]["hi_1"]["species_key"] == "sp_keep"
        # List reference: loser key replaced by survivor key, de-duplicated.
        assert db.cols[col.STARTER_KITS]["kit_1"]["species_keys"] == ["sp_keep", "sp_other"]
        # Derived singleton doc (unique index) is deleted, not repointed.
        assert db.cols[col.REFERENCE_IMAGE_JOBS] == {}
        # Edges repointed onto the survivor.
        assert list(db.cols[col.USER_FAVORITES].values())[0]["_to"] == _species_id("sp_keep")
        assert list(db.cols[col.ENTRY_FOR_SPECIES].values())[0]["_to"] == _species_id("sp_keep")
        # Lifecycle edge + child repointed onto the survivor (no collision).
        assert list(db.cols[col.HAS_LIFECYCLE].values())[0]["_from"] == _species_id("sp_keep")
        assert db.cols[col.LIFECYCLE_CONFIGS]["lc_drop"]["species_key"] == "sp_keep"

    def test_no_reference_left_pointing_at_deleted_loser(self):
        db = _rich_loser_db()
        migration.up(db)
        loser_id = _species_id("sp_drop")
        for store in db.cols.values():
            for doc in store.values():
                assert doc.get("species_key") != "sp_drop"
                assert "sp_drop" not in (doc.get("species_keys") or [])
                assert doc.get("_from") != loser_id
                assert doc.get("_to") != loser_id


class TestSec101NestedIdentificationRef:
    def test_nested_matched_species_key_repointed_to_survivor(self):
        db = _identification_ref_db()
        migration.up(db)

        assert "sp_drop" not in db.cols[col.SPECIES]
        results = db.cols[col.IDENTIFICATION_REQUESTS]["ir_1"]["results"]
        # The loser key in the stored candidate now resolves the survivor …
        assert results[0]["matched_species_key"] == "sp_keep"
        # … while an unmatched candidate stays untouched.
        assert results[1]["matched_species_key"] is None

    def test_no_nested_reference_left_pointing_at_deleted_loser(self):
        db = _identification_ref_db()
        migration.up(db)
        for req in db.cols[col.IDENTIFICATION_REQUESTS].values():
            for candidate in req.get("results", []):
                assert candidate.get("matched_species_key") != "sp_drop"

    def test_dry_run_counts_nested_reference_as_planned_move(self):
        db = _identification_ref_db()
        report = migration.up(db, dry_run=True)
        assert report.details["planned_reference_moves"][col.IDENTIFICATION_REQUESTS] == 1
        # Nothing written in dry-run: the loser and its nested reference survive.
        assert "sp_drop" in db.cols[col.SPECIES]
        assert db.cols[col.IDENTIFICATION_REQUESTS]["ir_1"]["results"][0]["matched_species_key"] == "sp_drop"


class TestSec002SingletonChildCollision:
    def test_loser_child_deleted_not_orphaned(self):
        db = _lifecycle_collision_db()
        migration.up(db)

        assert "sp_drop" not in db.cols[col.SPECIES]
        # Survivor keeps its own lifecycle config; the loser's is deleted.
        assert "lc_keep" in db.cols[col.LIFECYCLE_CONFIGS]
        assert "lc_drop" not in db.cols[col.LIFECYCLE_CONFIGS]
        # Exactly one lifecycle edge remains, anchored on the survivor.
        edges = list(db.cols[col.HAS_LIFECYCLE].values())
        assert len(edges) == 1
        assert edges[0]["_from"] == _species_id("sp_keep")
