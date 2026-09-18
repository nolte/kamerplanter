"""v0051 deletes staged import jobs that belong to no tenant (#1501, review SCR-001).

The rows this removes are the ones `ImportJob.tenant_key` was never written for:
before #1501 the field existed and nothing set it, so every job in the collection
was stamped `""`. After #1501 that key is a caller with **no** resolvable tenant
rather than a wildcard, so those documents are addressable by nobody — and
`POST /import/upload` now needs `require_active_tenant_role(GROWER)`, so nothing
can create another one.

What the tests here are mostly about is what the migration must **not** touch: a
job that does have an owner, on a re-run, and on a dry run. A migration that
deleted an owned job would be a data-loss bug wearing a security fix's clothes.

The AQL double answers this migration's own two queries and **refuses** one it
does not recognise. A double returning `[]` for an unknown query would make every
assertion below pass vacuously — including the idempotence one, whose whole job is
to observe an empty delete list.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0051_drop_unowned_import_jobs import DropUnownedImportJobsMigration

_IMPORT_JOBS = "import_jobs"


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.deleted: list[str] = []

    def delete(self, spec: dict[str, Any], ignore_missing: bool = False) -> None:
        key = spec["_key"]
        if key not in self.docs:
            if ignore_missing:
                return
            raise KeyError(key)
        self.deleted.append(key)
        del self.docs[key]


class _Aql:
    def __init__(self, collection: _Collection) -> None:
        self._col = collection

    def execute(self, query: str, bind_vars: dict | None = None) -> list[Any]:  # noqa: ARG002
        normalised = re.sub(r"\s+", " ", query).strip()
        if normalised == f"RETURN LENGTH({_IMPORT_JOBS})":
            return [len(self._col.docs)]
        if _IMPORT_JOBS not in normalised:
            raise AssertionError(f"unexpected query, this double cannot answer it: {normalised!r}")
        if '(j.tenant_key || "") == ""' not in normalised:
            raise AssertionError(
                "the migration no longer restricts itself to jobs with no owner. A job that belongs "
                "to a tenant is that tenant's staged work and must never be deleted by a migration."
            )
        # The `|| ""` half matters: a document written before the field existed has
        # no attribute at all, not an empty one, and both mean "belongs to nobody".
        return [key for key, doc in self._col.docs.items() if not (doc.get("tenant_key") or "")]


class _Db:
    def __init__(self, docs: dict[str, dict[str, Any]] | None, *, has_collection: bool = True) -> None:
        self._col = _Collection(docs if docs is not None else {})
        self.aql = _Aql(self._col)
        self._has = has_collection

    def has_collection(self, name: str) -> bool:
        return self._has and name == _IMPORT_JOBS

    def collection(self, name: str) -> _Collection:
        assert name == _IMPORT_JOBS, name
        return self._col

    @property
    def deleted(self) -> list[str]:
        return self._col.deleted

    @property
    def remaining(self) -> set[str]:
        return set(self._col.docs)


def _docs() -> dict[str, dict[str, Any]]:
    return {
        # Stamped empty — the shape every job in a pre-#1501 installation has.
        "legacy_empty": {"entity_type": "species", "tenant_key": "", "preview_rows": [{"row_number": 1}]},
        # Written before the field existed at all: no attribute, same meaning.
        "legacy_absent": {"entity_type": "cultivar", "preview_rows": []},
        # Owned. Must survive.
        "owned": {"entity_type": "species", "tenant_key": "tenant_acme"},
    }


@pytest.fixture
def migration() -> DropUnownedImportJobsMigration:
    return DropUnownedImportJobsMigration()


class TestItDeletesExactlyTheUnownedJobs:
    def test_both_unowned_shapes_go_and_the_owned_job_stays(self, migration) -> None:
        db = _Db(_docs())

        report = migration.up(db)  # type: ignore[arg-type]

        assert sorted(db.deleted) == ["legacy_absent", "legacy_empty"]
        assert db.remaining == {"owned"}
        assert report.scanned == 3
        assert report.changed == 2
        assert report.details["unowned"] == 2

    def test_an_installation_with_only_owned_jobs_is_untouched(self, migration) -> None:
        """The #706 direction: the common case must be a no-op, not a clear-out."""
        db = _Db({"owned": {"entity_type": "species", "tenant_key": "tenant_acme"}})

        report = migration.up(db)  # type: ignore[arg-type]

        assert db.deleted == []
        assert db.remaining == {"owned"}
        assert report.changed == 0
        assert report.noop


class TestTheReportIsHonest:
    def test_a_dry_run_reports_the_plan_and_writes_nothing(self, migration) -> None:
        """M-5. A dry run that took its own path would describe a plan nobody executes."""
        db = _Db(_docs())

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert db.deleted == []
        assert db.remaining == {"legacy_empty", "legacy_absent", "owned"}
        assert report.dry_run is True
        assert report.scanned == 3
        assert report.changed == 0
        # The plan is still reported in full, which is the only reason to run one.
        assert report.details["unowned"] == 2
        assert sorted(report.details["keys"]) == ["legacy_absent", "legacy_empty"]

    def test_a_second_run_changes_nothing(self, migration) -> None:
        """M-3 idempotence, observed rather than asserted about."""
        db = _Db(_docs())
        migration.up(db)  # type: ignore[arg-type]

        second = migration.up(db)  # type: ignore[arg-type]

        assert second.changed == 0
        assert second.noop
        assert db.remaining == {"owned"}

    def test_a_missing_collection_is_a_clean_no_op(self, migration) -> None:
        """A fresh installation has never staged an import."""
        db = _Db(None, has_collection=False)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 0
        assert report.changed == 0


class TestItDeclaresItselfHonestly:
    def test_it_is_not_reversible(self, migration) -> None:
        """M-6. There is no owner to restore the rows to, so there is no inverse.

        Asserted rather than described: a `down` that re-created ownerless jobs
        would recreate the very defect #1501 closed.
        """
        from app.migrations.framework.report import IrreversibleMigrationError

        assert migration.reversible is False
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_Db(_docs()))  # type: ignore[arg-type]

    def test_its_metadata_matches_its_module(self, migration) -> None:
        assert migration.version == "0051"
        assert migration.name == "drop_unowned_import_jobs"
        assert len(migration.description) > 20
