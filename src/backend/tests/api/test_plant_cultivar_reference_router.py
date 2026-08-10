"""A plant instance may not bind another tenant's cultivar (#1090 C-9).

#1090 gave ``Cultivar`` an owner (C-1), left the legacy population global (C-2),
scoped every read to it (C-3/C-5) and gated the mutations on ownership and role
(C-4). What survived all four is the *reference*: ``cultivar_key`` arrives in the
``POST``/``PUT /t/{slug}/plant-instances`` body and used to be persisted
unverified, so a member of tenant A could anchor their own plant on a cultivar
owned by tenant B. That is the last path by which a foreign tenant's cultivar key
enters a tenant's data, and it is not cosmetic: the key is dereferenced in system
context all over the codebase (print labels, care reminders, watering, the
calendar aggregation's ``DOCUMENT()`` join), so the foreign cultivar's *name* and
*traits* come back out through the referencing tenant's own screens — the C-3/C-5
read gates never see that request.

The fix is the declarative #948 mechanism, not a hand-written line in
``create_plant``: the repository names ``cultivar_key`` in
``_owned_reference_fields`` and ``BaseArangoRepository`` verifies it before the
write. Two properties are pinned here because they are the ones a re-implementation
would get wrong:

* **Global cultivars stay bindable.** ``v0038`` deliberately left the entire
  legacy population global (``tenant_key == ""``, and — for rows written before
  C-1 that the migration has not yet touched — with no ``tenant_key`` attribute at
  all). Both shapes must keep working, or the guard breaks every existing plant
  form instead of closing a leak.
* **A foreign key and an unknown key answer identically** (404, ``ENTITY_NOT_FOUND``),
  so the endpoint is not turned into a cross-tenant existence oracle.

The update path gets its own class: ``create`` is where the #948 mechanism hangs,
so a ``PUT`` that re-points an existing plant at a foreign cultivar would
otherwise walk straight past a guard that looks closed.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.tenant_router import router as plant_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_plant_instance_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.tenant_ownership import OWNERSHIP_VERIFIABLE_COLLECTIONS
from app.domain.models.tenant_context import TenantContext
from app.domain.services.plant_instance_service import PlantInstanceService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_CULTIVAR = "cv-own"
GLOBAL_CULTIVAR = "cv-global"
LEGACY_CULTIVAR = "cv-legacy"
FOREIGN_CULTIVAR = "cv-foreign"
UNKNOWN_CULTIVAR = "cv-does-not-exist"

OWN_PLANT = "plant-a1"

CULTIVARS: dict[str, dict[str, Any]] = {
    OWN_CULTIVAR: {"_key": OWN_CULTIVAR, "name": "Anna's Cross", "tenant_key": TENANT_KEY},
    GLOBAL_CULTIVAR: {"_key": GLOBAL_CULTIVAR, "name": "Genovese", "tenant_key": ""},
    # The pre-C-1 shape ``v0038`` stamps: no ``tenant_key`` attribute at all.
    # ``verify_entity_ownership`` reads that as global, and it must stay bindable.
    LEGACY_CULTIVAR: {"_key": LEGACY_CULTIVAR, "name": "Marmande"},
    FOREIGN_CULTIVAR: {"_key": FOREIGN_CULTIVAR, "name": "Secret Cross", "tenant_key": FOREIGN_TENANT_KEY},
}


# ── Harness ──────────────────────────────────────────────────────────────────


class _RecordingCollection:
    """Insert/update-recording collection double, so "wrote nothing" is assertable."""

    def __init__(self, name: str, docs: dict[str, dict[str, Any]] | None = None) -> None:
        self._name = name
        self._docs = docs or {}
        self.inserted: list[dict[str, Any]] = []
        #: Every key this collection was asked for — lets a test assert that a
        #: reference was *not* dialled at all, not merely that it passed.
        self.reads: list[str] = []

    def get(self, key: str) -> dict[str, Any] | None:
        self.reads.append(key)
        return self._docs.get(key)

    def insert(self, data: dict[str, Any], return_new: bool = False) -> dict[str, Any]:
        key = f"{self._name}-{len(self.inserted) + 1}"
        doc = {"_key": key, "_id": f"{self._name}/{key}", **data}
        self.inserted.append(doc)
        self._docs[key] = doc
        return {"new": doc}

    def update(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        key = data["_key"]
        stored = {**self._docs.get(key, {}), **data}
        self._docs[key] = stored
        return {"new": stored}

    def stored(self, key: str) -> dict[str, Any] | None:
        return self._docs.get(key)


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _plant_doc(cultivar_key: str | None) -> dict[str, Any]:
    return {
        "_key": OWN_PLANT,
        "_id": f"{col.PLANT_INSTANCES}/{OWN_PLANT}",
        "tenant_key": TENANT_KEY,
        "instance_id": "TOM-001",
        "species_key": "sp-tomato",
        "cultivar_key": cultivar_key,
        "planted_on": "2026-03-01",
    }


def _client(
    *, existing_cultivar_key: str | None = None
) -> tuple[TestClient, _RecordingCollection, _RecordingCollection]:
    """Wire the real router → service → repository over a replaying fake DB.

    Only the collaborators the create/update paths actually touch are real; the
    site/rotation/companion collaborators are doubled because no test here plants
    into a slot. ``species_repo`` stays unwired, so the response mapper resolves
    no labels — the assertions are on what was *written*, not on what came back.
    """
    plants = _RecordingCollection(col.PLANT_INSTANCES, {OWN_PLANT: _plant_doc(existing_cultivar_key)})
    cultivars = _RecordingCollection(col.CULTIVARS, dict(CULTIVARS))
    collections = {
        col.PLANT_INSTANCES: plants,
        col.CULTIVARS: cultivars,
        col.PLACED_IN: _RecordingCollection(col.PLACED_IN),
    }
    repo = ArangoPlantInstanceRepository(ReplayingDatabase(ReplayingAql(), collections))
    service = PlantInstanceService(repo, MagicMock(), MagicMock(), MagicMock())

    app = FastAPI()
    app.include_router(plant_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user-1",
        role=TenantRole.GROWER,
    )
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    return TestClient(app), plants, cultivars


def _url(path: str = "") -> str:
    return f"/api/v1/t/{TENANT_SLUG}/plant-instances{path}"


def _body(cultivar_key: str | None, instance_id: str = "TOM-002") -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "species_key": "sp-tomato",
        "cultivar_key": cultivar_key,
        "planted_on": "2026-03-01",
    }


# ── 1: create ────────────────────────────────────────────────────────────────


class TestPlantCreateCultivarReference:
    """``POST /t/{slug}/plant-instances`` — ``cultivar_key`` from the body."""

    def test_a_foreign_cultivar_is_not_found_and_writes_nothing(self):
        client, plants, _ = _client()

        resp = client.post(_url(), json=_body(FOREIGN_CULTIVAR))

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert plants.inserted == []

    def test_an_unknown_cultivar_looks_exactly_the_same(self):
        """No oracle: 'owned by another tenant' and 'does not exist' are one answer."""
        client, _, _ = _client()

        foreign = client.post(_url(), json=_body(FOREIGN_CULTIVAR))
        unknown = client.post(_url(), json=_body(UNKNOWN_CULTIVAR))

        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["error_code"] == unknown.json()["error_code"]

    @pytest.mark.parametrize(
        ("cultivar_key", "why"),
        [
            (OWN_CULTIVAR, "the tenant's own cultivar"),
            (GLOBAL_CULTIVAR, "a globally seeded cultivar (tenant_key == '')"),
            (LEGACY_CULTIVAR, "a legacy row with no tenant_key attribute (v0038 shape)"),
        ],
    )
    def test_a_bindable_cultivar_still_creates_the_plant(self, cultivar_key, why):
        client, plants, _ = _client()

        resp = client.post(_url(), json=_body(cultivar_key))

        assert resp.status_code == 201, f"{why} must stay bindable: {resp.text}"
        assert [p["cultivar_key"] for p in plants.inserted] == [cultivar_key]

    def test_a_plant_without_a_cultivar_dials_no_reference_at_all(self):
        client, plants, cultivars = _client()

        resp = client.post(_url(), json=_body(None))

        assert resp.status_code == 201, resp.text
        # ``exclude_none=True`` on the insert drops the attribute entirely.
        assert plants.inserted[0].get("cultivar_key") is None
        assert cultivars.reads == []


# ── 2: update — the path ``create``'s guard does not cover ───────────────────


class TestPlantUpdateCultivarReference:
    """``PUT /t/{slug}/plant-instances/{key}`` — re-pointing an existing plant.

    Without this the create guard is trivially bypassable in two requests: create
    with a global cultivar, then ``PUT`` the foreign key onto the same plant.
    """

    def test_repointing_at_a_foreign_cultivar_is_not_found_and_changes_nothing(self):
        client, plants, _ = _client(existing_cultivar_key=GLOBAL_CULTIVAR)

        resp = client.put(_url(f"/{OWN_PLANT}"), json=_body(FOREIGN_CULTIVAR, instance_id="TOM-001"))

        assert resp.status_code == 404, resp.text
        assert plants.stored(OWN_PLANT)["cultivar_key"] == GLOBAL_CULTIVAR

    def test_repointing_at_an_unknown_cultivar_looks_exactly_the_same(self):
        client, _, _ = _client(existing_cultivar_key=GLOBAL_CULTIVAR)

        foreign = client.put(_url(f"/{OWN_PLANT}"), json=_body(FOREIGN_CULTIVAR, instance_id="TOM-001"))
        unknown = client.put(_url(f"/{OWN_PLANT}"), json=_body(UNKNOWN_CULTIVAR, instance_id="TOM-001"))

        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["error_code"] == unknown.json()["error_code"]

    @pytest.mark.parametrize("cultivar_key", [OWN_CULTIVAR, GLOBAL_CULTIVAR, LEGACY_CULTIVAR, None])
    def test_a_bindable_cultivar_still_updates_the_plant(self, cultivar_key):
        client, plants, _ = _client(existing_cultivar_key=GLOBAL_CULTIVAR)

        resp = client.put(_url(f"/{OWN_PLANT}"), json=_body(cultivar_key, instance_id="TOM-001"))

        assert resp.status_code == 200, resp.text
        assert plants.stored(OWN_PLANT)["cultivar_key"] == cultivar_key

    def test_an_unchanged_reference_is_not_re_verified(self):
        """Only a *changed* reference is verified — see the repository's ``update``.

        This is what keeps a plant editable after the cultivar it points at was
        deleted (a dangling reference is an integrity defect, not a leak), and it
        is why the internal update paths — phase transitions, planting-run
        materialisation, removal — pay no extra read per plant.
        """
        client, _, cultivars = _client(existing_cultivar_key=GLOBAL_CULTIVAR)

        resp = client.put(_url(f"/{OWN_PLANT}"), json=_body(GLOBAL_CULTIVAR, instance_id="TOM-001"))

        assert resp.status_code == 200, resp.text
        assert cultivars.reads == []


# ── 3: the declaration, not the call site ────────────────────────────────────


class TestTheCultivarReferenceIsDeclaredNotRemembered:
    """The mechanism (#948), mirroring ``test_cross_tenant_writes_router.py`` §5."""

    def test_the_plant_repository_declares_its_cultivar_reference(self):
        assert ArangoPlantInstanceRepository._owned_reference_fields.get("cultivar_key") == col.CULTIVARS

    def test_cultivars_are_ownership_verifiable(self):
        """Off-allowlist collections fail closed *before* the lookup — the guard
        would reject every cultivar, global ones included, if this were missing."""
        assert col.CULTIVARS in OWNERSHIP_VERIFIABLE_COLLECTIONS
