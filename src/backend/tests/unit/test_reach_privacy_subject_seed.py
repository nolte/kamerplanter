"""The privacy-subject seed of the reach audit (#1680) against the declared inventories, without a database.

``scripts/reach/seed_privacy_subject.py`` runs inside the backend container of the
reach stack and writes one row of a data subject per declared *(collection, user
field)*. Its proof is the run against that stack, which only the weekly
``Capability Reach Audit`` makes — and from 2026-10-11 on that run never got past
the seed: every T2 probe built on it was *not probed* (0 of 27 probed). Two
defects stopped it, one masking the other:

* **A field one object down.** The sites rule of REQ-053 GP-NFR-055 anonymises
  ``plan.plan_updated_by``. The seed held that path against the flat field names of
  ``Site`` and refused it; accepted as a flat key it would have written a literal
  ``"plan.plan_updated_by"`` attribute the executor (``doc.plan.plan_updated_by``)
  never reads.
* **A source without an account field.** A personal-tenant export source
  (#2135) carries no ``filter_field`` by validator; the seed made that the field
  ``''`` and refused it. Such a source is the subject's personal garden, which this
  seed does not build (``seed_tenant_for_erasure.py --personal-of`` does).
* **Rows the domain validators refuse,** reached only once the two above were
  gone: a ``care_events`` category held against the known categories, and a
  ``garden_objects`` row whose class, geometry kind and props must agree (a
  tagged union validates only with its tag written out).

What a test can honestly stand in for: the seed runs over the REAL erasure plan
and export manifest and the REAL collection -> model bindings, into an in-memory
stand-in that records what an ArangoDB insert would have stored.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.models.privacy import DataSourceDefinition, PersonalTenantScope
from tests.support.repo_scripts import find_repo_root, load_repo_script

# The seed imports the inventory guard as a sibling module (``stack.py`` ships both into the
# container side by side); in the checkout it sits one directory up.
sys.modules.setdefault("check_privacy_inventory", load_repo_script("check_privacy_inventory"))
seed = load_repo_script("reach/seed_privacy_subject")

SUBJECT = "reach-subject-test"


class _Collection:
    def __init__(self, name: str, store: dict[str, list[dict[str, Any]]]) -> None:
        self.name = name
        self.store = store

    def insert(self, doc: dict[str, Any]) -> dict[str, str]:
        key = doc.get("_key") or f"auto{len(self.store[self.name])}"
        self.store[self.name].append({**doc, "_key": key})
        return {"_id": f"{self.name}/{key}", "_key": key, "_rev": "1"}


class _Database:
    """What the seed uses of a python-arango database: collections and inserts."""

    def __init__(self) -> None:
        self.store: dict[str, list[dict[str, Any]]] = {}

    def has_collection(self, name: str) -> bool:
        return name in self.store

    def create_collection(self, name: str, *, edge: bool = False) -> None:
        self.store.setdefault(name, [])

    def collection(self, name: str) -> _Collection:
        self.store.setdefault(name, [])
        return _Collection(name, self.store)


@pytest.fixture(scope="module")
def models() -> dict[str, list[Any]]:
    """The real collection -> model bindings, read from this checkout's ``app/`` (the container's ``/app/app``)."""
    root = find_repo_root(Path(__file__).resolve())
    assert root is not None
    original = seed.APP_ROOT
    seed.APP_ROOT = root / "src/backend/app"
    try:
        return seed.collection_models()
    finally:
        seed.APP_ROOT = original


@pytest.fixture
def seeder(models: dict[str, list[Any]], monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setattr(seed, "collection_models", lambda: models)
    instance = seed.Seeder(_Database(), SUBJECT)
    instance.tenant_key = "rs-tenant"
    return instance


def _stored(seeder: Any, row: dict[str, Any]) -> dict[str, Any]:
    return next(doc for doc in seeder.db.store[row["collection"]] if doc["_key"] == row["key"])


# ── A field one object down ─────────────────────────────────────────────────


def test_a_dotted_rule_field_is_written_inside_the_embedded_object_the_executor_reads(seeder: Any) -> None:
    row = seeder.document("sites", {"plan.plan_updated_by": SUBJECT, "tenant_key": "rs-tenant"}, role="rule")
    stored = _stored(seeder, row)
    assert stored["plan"]["plan_updated_by"] == SUBJECT
    assert "plan.plan_updated_by" not in stored
    # The embedded plan is a whole, valid SitePlan, not a dict holding one key.
    assert stored["plan"]["plan_revision"] == 0


@pytest.mark.parametrize(
    "path",
    [
        "plan.plan_updated_bye",  # misspelt tail
        "plans.plan_updated_by",  # misspelt head
        "name.plan_updated_by",  # head is a plain value, not an embedded model
        "plan.underlay.file_key",  # deeper than the executor's two segments
    ],
)
def test_a_dotted_field_the_model_does_not_hold_stops_the_seed(seeder: Any, path: str) -> None:
    with pytest.raises(seed.SeedError, match="are not fields of its model"):
        seeder.document("sites", {path: SUBJECT, "tenant_key": "rs-tenant"}, role="rule")
    assert not seeder.db.store.get("sites")


def test_a_flat_field_the_model_does_not_hold_still_stops_the_seed(seeder: Any) -> None:
    with pytest.raises(seed.SeedError, match="are not fields of its model"):
        seeder.document("sites", {"plan_updated_bye": SUBJECT}, role="rule")


# ── A source without an account field ──────────────────────────────────────


def test_a_personal_tenant_source_is_skipped_not_seeded_with_an_empty_field(
    seeder: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    personal = DataSourceDefinition(
        collection="sites", label="Sites", fields=["name"], personal_tenant_scope=PersonalTenantScope()
    )
    monkeypatch.setattr(DataExportEngine, "build_export_manifest", lambda self, subject: [personal])
    record = seeder.seed()
    assert not any(row["role"].startswith("export:sites") for row in record["rows"])


def test_the_seed_of_the_declared_inventories_completes_and_reaches_the_site_plan(seeder: Any) -> None:
    """The whole seed over the real plan and manifest — the step every T2 probe of the audit stands on."""
    record = seeder.seed()
    json.dumps(record)  # ``main`` prints it as JSON for the act and observation helpers
    site_rows = [row for row in record["rows"] if row["role"] == "rule:sites.plan.plan_updated_by"]
    assert len(site_rows) == 1
    assert _stored(seeder, site_rows[0])["plan"]["plan_updated_by"] == SUBJECT
