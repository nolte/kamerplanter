"""Tests for v0008_backfill_enrichment_origin.

The migration promotes a species' ``origin`` from ``system`` to ``enrichment`` when
the species carries a genuine enrichment marker — an ``external_mappings`` document
(``internal_collection == "species"``) with at least one ``accepted`` field. It
mirrors the live flip in ``EnrichmentEngine._apply_enrichment``:

* only ``system`` records are promoted (``tenant``/``import`` are left untouched —
  the anti-lockout guarantee);
* a mapping that recorded *no* accepted field (external data rejected because the
  local value was already populated) is not a promotion signal.
"""

from __future__ import annotations

from app.common.enums import DataOrigin
from app.migrations.versions.v0008_backfill_enrichment_origin import (
    _has_accepted_field,
    migration,
)

_ACCEPTED = {"genus": {"external_value": "Solanum", "accepted": True}}
_REJECTED = {"genus": {"external_value": "Solanum", "accepted": False}}


class _FakeAql:
    def __init__(self, data: dict) -> None:
        self._data = data

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        if "UPDATE" in query:
            origin = bind_vars["origin"]
            for key in bind_vars["keys"]:
                self._data["species"][key]["origin"] = origin
            return iter([])
        if "external_mappings" in query:
            return iter(
                {"internal_key": m["internal_key"], "field_mappings": m.get("field_mappings", {})}
                for m in self._data["external_mappings"]
                if m.get("internal_collection") == "species"
            )
        if "FOR d IN species" in query:
            keys = set(bind_vars.get("keys", []))
            system = bind_vars.get("system")
            return iter(
                key for key, doc in self._data["species"].items() if key in keys and doc.get("origin") == system
            )
        return iter([])


class _FakeDb:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.aql = _FakeAql(data)


def _sample_data() -> dict:
    return {
        "species": {
            # system + accepted enrichment marker → promoted to enrichment.
            "sp_sys_enriched": {"origin": DataOrigin.SYSTEM.value},
            # tenant + accepted marker → stays tenant (anti-lockout).
            "sp_tenant_enriched": {"origin": DataOrigin.TENANT.value},
            # system but mapping recorded no accepted field → stays system.
            "sp_sys_matchonly": {"origin": DataOrigin.SYSTEM.value},
            # system, no mapping at all → stays system.
            "sp_sys_nomap": {"origin": DataOrigin.SYSTEM.value},
            # already enrichment → untouched (idempotency).
            "sp_already": {"origin": DataOrigin.ENRICHMENT.value},
        },
        "external_mappings": [
            {"internal_collection": "species", "internal_key": "sp_sys_enriched", "field_mappings": _ACCEPTED},
            {"internal_collection": "species", "internal_key": "sp_tenant_enriched", "field_mappings": _ACCEPTED},
            {"internal_collection": "species", "internal_key": "sp_sys_matchonly", "field_mappings": _REJECTED},
            {"internal_collection": "species", "internal_key": "sp_already", "field_mappings": _ACCEPTED},
            # A cultivar mapping for the same key must be ignored (wrong collection).
            {"internal_collection": "cultivars", "internal_key": "sp_sys_enriched", "field_mappings": _ACCEPTED},
        ],
    }


class TestHasAcceptedField:
    def test_none_is_not_accepted(self):
        assert _has_accepted_field(None) is False

    def test_empty_dict_is_not_accepted(self):
        assert _has_accepted_field({}) is False

    def test_all_rejected_is_not_accepted(self):
        assert _has_accepted_field(_REJECTED) is False

    def test_one_accepted_is_accepted(self):
        assert _has_accepted_field(_ACCEPTED) is True

    def test_mixed_is_accepted(self):
        assert _has_accepted_field({**_REJECTED, "family": {"accepted": True}}) is True


class TestBackfill:
    def test_system_enriched_promoted_to_enrichment(self):
        data = _sample_data()
        report = migration.up(_FakeDb(data))
        assert data["species"]["sp_sys_enriched"]["origin"] == DataOrigin.ENRICHMENT.value
        assert report.changed == 1
        # Three species carry an accepted marker (cultivar mapping excluded).
        assert report.scanned == 3

    def test_tenant_enriched_stays_tenant_anti_lockout(self):
        data = _sample_data()
        migration.up(_FakeDb(data))
        assert data["species"]["sp_tenant_enriched"]["origin"] == DataOrigin.TENANT.value

    def test_match_only_mapping_not_promoted(self):
        data = _sample_data()
        migration.up(_FakeDb(data))
        assert data["species"]["sp_sys_matchonly"]["origin"] == DataOrigin.SYSTEM.value

    def test_species_without_mapping_untouched(self):
        data = _sample_data()
        migration.up(_FakeDb(data))
        assert data["species"]["sp_sys_nomap"]["origin"] == DataOrigin.SYSTEM.value

    def test_already_enrichment_untouched(self):
        data = _sample_data()
        migration.up(_FakeDb(data))
        assert data["species"]["sp_already"]["origin"] == DataOrigin.ENRICHMENT.value

    def test_rerun_is_a_noop(self):
        data = _sample_data()
        migration.up(_FakeDb(data))
        report = migration.up(_FakeDb(data))
        assert report.changed == 0
        assert report.noop is True

    def test_dry_run_writes_nothing(self):
        data = _sample_data()
        report = migration.up(_FakeDb(data), dry_run=True)
        assert report.dry_run is True
        assert report.changed == 0
        assert data["species"]["sp_sys_enriched"]["origin"] == DataOrigin.SYSTEM.value

    def test_report_details_breakdown(self):
        data = _sample_data()
        report = migration.up(_FakeDb(data))
        assert report.details == {"enriched_species": 3, "flipped": 1}

    def test_migration_metadata(self):
        assert migration.version == "0008"
        assert migration.name == "backfill_enrichment_origin"
        assert migration.reversible is False
