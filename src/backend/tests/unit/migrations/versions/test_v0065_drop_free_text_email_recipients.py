"""v0065 (#1885): a dry run writes nothing, a clean store runs no write, the keys bound are the model's."""

from __future__ import annotations

from typing import Any

from app.domain.models.notification import EMAIL_RECIPIENT_KEYS
from app.migrations.versions.v0065_drop_free_text_email_recipients import DropFreeTextEmailRecipientsMigration


class _Db:
    def __init__(self, affected: list[str]) -> None:
        self.affected = affected
        self.queries: list[tuple[str, dict[str, Any]]] = []
        self.aql = self

    def has_collection(self, name: str) -> bool:
        return name == "notification_preferences"

    def execute(self, query: str, bind_vars: dict | None = None, **kwargs: Any) -> list[str]:  # noqa: ARG002
        self.queries.append((query, bind_vars or {}))
        return list(self.affected) if query.lstrip().startswith("FOR p IN") and "RETURN" in query else []


def test_a_dry_run_only_scans() -> None:
    db = _Db(["a", "b"])

    report = DropFreeTextEmailRecipientsMigration().up(db, dry_run=True)  # type: ignore[arg-type]

    assert (report.scanned, report.changed) == (2, 0)
    assert len(db.queries) == 1


def test_a_clean_store_runs_no_write() -> None:
    db = _Db([])

    report = DropFreeTextEmailRecipientsMigration().up(db)  # type: ignore[arg-type]

    assert (report.scanned, report.changed) == (0, 0)
    assert len(db.queries) == 1


def test_the_write_strips_exactly_the_keys_the_model_drops() -> None:
    db = _Db(["a"])

    report = DropFreeTextEmailRecipientsMigration().up(db)  # type: ignore[arg-type]

    assert report.changed == 1
    scan, strip = db.queries
    assert scan[1] == strip[1] == {"keys": list(EMAIL_RECIPIENT_KEYS)}
    assert strip[0].lstrip().startswith("FOR p IN") and "REPLACE p WITH" in strip[0]
