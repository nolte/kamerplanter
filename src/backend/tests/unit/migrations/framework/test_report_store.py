"""spec/privacy/09 §2 (PRIV-701, PRIV-702; TA-701a) — redaction filter, persisted report, ``--report-out``."""

from __future__ import annotations

import json
from pathlib import Path

from app.migrations.framework.base import Migration
from app.migrations.framework.cli import write_report_file
from app.migrations.framework.report import MigrationReport
from app.migrations.framework.report_store import (
    DETAILS_SHAPE,
    MAX_SAMPLES_PER_BUCKET,
    REPORT_PHASES,
    persist_report,
    redact_details,
    report_document,
)
from tests.unit.migrations.framework.conftest import FakeDatabase

TOMBSTONE = "anon_0123456789abcdef"


class _Privacy(Migration):
    version = "0001"
    name = "privacy_probe"
    kind = "privacy_correction"


class _Plain(Migration):
    version = "0002"
    name = "plain_probe"


def _clean() -> dict:
    return {
        "status": "applied",
        "phases": {
            "precheck": {"ok": True, "unmet": [], "candidates": {"t1": 3}},
            "dry_run": {"would_change": {"care_events.tombstone_to_marker": 3}},
            "apply": {"tenants_done": ["t1"], "tenants_failed": [], "changed": {"care_events.tombstone_to_marker": 3}},
            "verify": {"residual": {"care_events.tombstone_to_marker": 0}},
            "monitor": {"handed_to": "privacy.consistency"},
        },
        "buckets": {"care_events.tombstone_to_marker": {"t1": 3}, "undeclared_tombstones": {"tasks.created_by": 1}},
        "samples": {"care_events.tombstone_to_marker": ["e1", "e2", "e3"]},
    }


class TestTheAllowedKeySet:
    def test_the_shape_is_the_one_the_spec_names(self) -> None:
        assert set(DETAILS_SHAPE) == {"status", "phases", "buckets", "samples"}
        assert tuple(DETAILS_SHAPE["phases"]) == REPORT_PHASES
        assert DETAILS_SHAPE["phases"]["apply"].keys() == {"tenants_done", "tenants_failed", "changed"}

    def test_a_report_of_the_allowed_shape_passes_unchanged(self) -> None:
        assert redact_details(_clean()) == (_clean(), 0)


class TestTheFilterRefuses:
    """TA-701a: user keys, names, text and tombstones never reach ``migration_reports``."""

    def test_an_unknown_key_at_any_level(self) -> None:
        details = _clean()
        details["user_key"] = "u-123"
        details["phases"]["apply"]["performed_by"] = "u-123"
        details["phases"]["precheck"]["display_name"] = "Anna Beispiel"

        redacted, dropped = redact_details(details)

        assert redacted == _clean()
        assert dropped == 3

    def test_a_name_or_text_where_an_identifier_belongs(self) -> None:
        details = _clean()
        details["phases"]["apply"]["tenants_done"].append("Anna Beispiel")
        details["buckets"]["care_events.tombstone_to_marker"]["anna@example.org"] = 1
        details["samples"]["care_events.tombstone_to_marker"].append("Omas Hochbeet")
        details["phases"]["monitor"]["handed_to"] = "drop table"

        redacted, dropped = redact_details(details)

        assert redacted["phases"]["apply"]["tenants_done"] == ["t1"]
        assert "anna@example.org" not in redacted["buckets"]["care_events.tombstone_to_marker"]
        assert redacted["samples"]["care_events.tombstone_to_marker"] == ["e1", "e2", "e3"]
        assert "handed_to" not in redacted["phases"]["monitor"]
        assert dropped == 4

    def test_a_tombstone_or_the_marker_anywhere(self) -> None:
        details = _clean()
        details["samples"]["care_events.tombstone_to_marker"].append(TOMBSTONE)
        details["buckets"]["undeclared_tombstones"][TOMBSTONE] = 1
        details["phases"]["apply"]["tenants_failed"].append("anon2_0123456789abcdef")
        details["phases"]["apply"]["tenants_failed"].append("_anonymized")

        redacted, dropped = redact_details(details)

        assert TOMBSTONE not in json.dumps(redacted)
        assert "anon2_" not in json.dumps(redacted)
        assert "_anonymized" not in json.dumps(redacted)
        assert dropped == 4

    def test_a_value_of_the_wrong_type(self) -> None:
        details = _clean()
        details["status"] = "done by Anna"
        details["phases"]["precheck"]["ok"] = "yes"
        details["phases"]["precheck"]["candidates"]["t1"] = "three"
        details["buckets"]["care_events.tombstone_to_marker"]["t1"] = True

        redacted, dropped = redact_details(details)

        assert "status" not in redacted
        assert "ok" not in redacted["phases"]["precheck"]
        assert redacted["phases"]["precheck"]["candidates"] == {}
        assert redacted["buckets"]["care_events.tombstone_to_marker"] == {}
        assert dropped == 4

    def test_more_than_twenty_five_samples_per_bucket(self) -> None:
        details = _clean()
        details["samples"]["care_events.tombstone_to_marker"] = [f"e{i}" for i in range(40)]

        redacted, dropped = redact_details(details)

        assert len(redacted["samples"]["care_events.tombstone_to_marker"]) == MAX_SAMPLES_PER_BUCKET
        assert dropped == 40 - MAX_SAMPLES_PER_BUCKET


class TestPersistence:
    def test_the_stored_document_is_the_redacted_report(self) -> None:
        db = FakeDatabase()
        details = _clean() | {"user_key": "u-123"}
        report = MigrationReport(version="0001", name="privacy_probe", scanned=3, changed=3, details=details)

        stored = persist_report(db, _Privacy(), report)

        (document,) = db.collection("migration_reports").all()
        assert document["_key"] == stored["_key"]
        assert document["details"] == _clean()
        assert document["redacted_entries"] == 1
        assert document["status"] == "applied"
        assert document["kind"] == "privacy_correction"
        assert "u-123" not in json.dumps(document)

    def test_two_runs_of_one_version_are_two_documents(self) -> None:
        db = FakeDatabase()
        report = MigrationReport(version="0001", name="privacy_probe", dry_run=True, details=_clean())

        persist_report(db, _Privacy(), report)
        persist_report(db, _Privacy(), report)

        assert len(db.collection("migration_reports").all()) == 2


class TestReportOut:
    def test_only_the_privacy_migrations_are_written_and_redacted(self, tmp_path: Path) -> None:
        out = tmp_path / "audits" / "v0109-dry-run.json"
        reports = [
            MigrationReport(version="0001", name="privacy_probe", dry_run=True, details=_clean() | {"name": "Anna"}),
            MigrationReport(version="0002", name="plain_probe", dry_run=True, details={"keys": ["u-123"]}),
        ]

        written = write_report_file(out, [_Privacy(), _Plain()], reports, dry_run=True)

        payload = json.loads(out.read_text(encoding="utf-8"))
        assert written == 1
        assert payload["dry_run"] is True
        assert [r["version"] for r in payload["reports"]] == ["0001"]
        assert payload["reports"][0]["details"] == _clean()
        assert "u-123" not in out.read_text(encoding="utf-8")

    def test_the_document_names_the_counters(self) -> None:
        report = MigrationReport(version="0001", name="privacy_probe", scanned=5, changed=4, incomplete=True)

        document = report_document(_Privacy(), report)

        assert (document["scanned"], document["changed"], document["incomplete"]) == (5, 4, True)
