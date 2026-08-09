"""Cultivar create-path tenant ownership through the HTTP boundary (#1090).

Proves the *route wiring* of the write-side stamping, the Cultivar pendant of
``test_species_authorization_api.py``'s SEC-004 block:

* the interactive create binds the new cultivar to the tenant resolved from the
  **authenticated caller** (``get_creating_tenant_key``), never to anything in the
  request body (#1000) — ``CultivarCreate`` has no tenant field, so a body-supplied
  key is dropped at the schema boundary rather than stamped;
* in ``full`` mode a create with no resolvable active tenant is refused with 422
  instead of being stamped global, which would inject an ``origin=tenant`` row into
  the shared seed catalogue every tenant reads;
* ``light`` mode (REQ-027) is single-tenant, so the empty key there is the
  legitimate global operator context and stays accepted;
* ownership is *not* served to the client (operator decision Q4), mirroring
  ``SpeciesResponse``.

The HTTP route is unchanged by #1090: it is still
``/api/v1/species/{species_key}/cultivars``; only the router module moved.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.cultivars.router import router as cultivars_router
from app.api.v1.cultivars.schemas import CultivarCreate, CultivarResponse
from app.common.auth import get_creating_tenant_key, get_current_user
from app.common.dependencies import get_species_service
from app.common.enums import DataOrigin
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.models.species import Cultivar

_BODY = {"name": "Genovese", "species_key": "sp_basil"}


def _app(service: MagicMock, *, creating_tenant_key: str) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(cultivars_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_creating_tenant_key] = lambda: creating_tenant_key
    return app


def _service() -> MagicMock:
    service = MagicMock()
    service.create_cultivar.side_effect = lambda c: c.model_copy(update={"key": "cv_1"})
    return service


# ── Create stamps the caller's tenant ────────────────────────────────────────


def test_create_stamps_the_callers_tenant_key(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    service = _service()
    client = TestClient(_app(service, creating_tenant_key="tenant_personal_1"))

    resp = client.post("/api/v1/species/sp_basil/cultivars", json=_BODY)

    assert resp.status_code == 201
    created = service.create_cultivar.call_args.args[0]
    assert created.tenant_key == "tenant_personal_1"
    assert created.origin is DataOrigin.TENANT


def test_a_body_supplied_tenant_key_is_never_stamped(monkeypatch):
    # #1000: the owning tenant comes from the authenticated context, never from the
    # payload. The schema has no such field, so the attacker value is dropped.
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    service = _service()
    client = TestClient(_app(service, creating_tenant_key="tenant_personal_1"))

    resp = client.post(
        "/api/v1/species/sp_basil/cultivars",
        json={**_BODY, "tenant_key": "attacker_tenant"},
    )

    assert resp.status_code == 201
    assert service.create_cultivar.call_args.args[0].tenant_key == "tenant_personal_1"


def test_the_request_schema_carries_no_tenant_field():
    # Pins the structural half of the guard above: the field cannot reappear on the
    # schema without this test (and the repo's tenant-body-field gate) failing.
    assert "tenant_key" not in CultivarCreate.model_fields


# ── SEC-004 pendant: create requires an active tenant in full mode ───────────


def test_full_mode_create_without_active_tenant_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    service = _service()
    client = TestClient(_app(service, creating_tenant_key=""))

    resp = client.post("/api/v1/species/sp_basil/cultivars", json=_BODY)

    assert resp.status_code == 422
    # Refused before the service — nothing was written to the shared catalogue.
    service.create_cultivar.assert_not_called()


def test_light_mode_create_without_active_tenant_still_works(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    service = _service()
    client = TestClient(_app(service, creating_tenant_key=""))

    resp = client.post("/api/v1/species/sp_basil/cultivars", json=_BODY)

    assert resp.status_code == 201
    assert service.create_cultivar.call_args.args[0].tenant_key == ""


# ── Q4: ownership is not exposed to the client ───────────────────────────────


def test_cultivar_response_does_not_expose_tenant_key():
    assert "tenant_key" not in CultivarResponse.model_fields


def test_a_served_cultivar_carries_no_tenant_key(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    service = _service()
    service.get_cultivar.return_value = Cultivar(
        _key="cv_1", name="Genovese", species_key="sp_basil", tenant_key="tenant_42"
    )
    client = TestClient(_app(service, creating_tenant_key="tenant_42"))

    resp = client.get("/api/v1/species/sp_basil/cultivars/cv_1")

    assert resp.status_code == 200
    assert "tenant_key" not in resp.json()
