"""The tenant-erasure seed of the reach audit (#1769) over the real inventory, without a database (#3090).

``scripts/reach/seed_tenant_for_erasure.py`` writes one row per ``TenantErasureEngine.INVENTORY``
entry into the reach stack. Its proof is the T2 run, which the weekly ``Capability Reach Audit``
makes — and once the probes on it were re-derived the run stopped in the seed: ``calendar_feeds``
was seeded with ``token``, a field the model dropped for ``token_hash`` in #2229. This test runs
the whole seed (organisation and personal tenant) over the REAL inventory and the REAL collection
-> model bindings into an in-memory stand-in, so the next renamed field fails here first.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from tests.support.repo_scripts import find_repo_root, load_repo_script

sys.modules.setdefault("check_privacy_inventory", load_repo_script("check_privacy_inventory"))
subject_seed = load_repo_script("reach/seed_privacy_subject")
sys.modules.setdefault("seed_privacy_subject", subject_seed)
tenant_seed = load_repo_script("reach/seed_tenant_for_erasure")


class _Collection:
    def __init__(self, name: str, store: dict[str, list[dict[str, Any]]]) -> None:
        self.name = name
        self.store = store

    def insert(self, doc: dict[str, Any]) -> dict[str, str]:
        key = doc.get("_key") or f"auto{len(self.store[self.name])}"
        self.store[self.name].append({**doc, "_key": key})
        return {"_id": f"{self.name}/{key}", "_key": key, "_rev": "1"}


class _Database:
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
    root = find_repo_root(Path(__file__).resolve())
    assert root is not None
    original = subject_seed.APP_ROOT
    subject_seed.APP_ROOT = root / "src/backend/app"
    try:
        return subject_seed.collection_models()
    finally:
        subject_seed.APP_ROOT = original


@pytest.mark.parametrize("personal", [False, True], ids=["organisation", "personal"])
def test_the_seed_writes_a_row_for_every_inventory_entry(
    models: dict[str, list[Any]], monkeypatch: pytest.MonkeyPatch, personal: bool
) -> None:
    monkeypatch.setattr(subject_seed, "collection_models", lambda: models)
    seeder = tenant_seed.Seeder(_Database(), "reach-member-test")
    tenant_seed._seed_one(seeder, "reach-tenant-test", "reach-member-test", "tenant", personal=personal)
    seeded = {row["collection"] for row in seeder.rows if row["role"].startswith("tenant:")}
    expected = {
        entry.collection
        for entry in TenantErasureEngine().build_plan("reach-tenant-test").entries
        if entry.collection != TenantErasureEngine.RECORD_COLLECTION
    }
    assert expected <= seeded


def test_a_calendar_feed_is_seeded_with_its_token_hash(
    models: dict[str, list[Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(subject_seed, "collection_models", lambda: models)
    seeder = tenant_seed.Seeder(_Database(), "reach-member-test")
    tenant_seed._seed_one(seeder, "reach-tenant-test", "reach-member-test", "tenant")
    (feed,) = seeder.db.store["calendar_feeds"]
    assert "token" not in feed and len(feed["token_hash"]) == 64
