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

Datastore-freedom (R-8, #1091): every tenant-bearing dependency the create route
declares must be overridden here, not just the stamping one. This file used to
override ``get_creating_tenant_key`` alone and stayed datastore-free by accident —
the read route's ``get_active_tenant_key`` is the *same function object* (the F-3
alias), so one override covered both. SEC-005 (#1113) added
``get_active_tenant_context`` and ``get_is_platform_admin``, which are separate
objects: without their overrides the route resolves the real tenant service and
the tier's ``block_datastore_access`` guard fires. Measured, not assumed — the
guard was seen firing on this file before the overrides below were added.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.cultivars.router import router as cultivars_router
from app.api.v1.cultivars.schemas import CultivarCreate, CultivarResponse
from app.common.auth import (
    get_active_tenant_context,
    get_creating_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_species_service
from app.common.enums import DataOrigin, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.models.species import Cultivar
from app.domain.models.tenant_context import TenantContext

_BODY = {"name": "Genovese", "species_key": "sp_basil"}

#: The tenant the *role context* reports, deliberately different from every
#: ``creating_tenant_key`` used below. In production the two cannot differ (one
#: ``_resolve_active_tenant`` feeds both), so setting them apart here is free — and
#: it turns every stamping assertion in this file into a live proof that the stamp
#: still reads the F-3 alias rather than ``ctx.tenant_key``. If the route ever
#: switched sources, the alias would become inert and this file would certify
#: nothing; instead it fails.
_ROLE_CONTEXT_TENANT = "tenant_role_context_only"


def _app(
    service: MagicMock,
    *,
    creating_tenant_key: str,
    role: TenantRole = TenantRole.GROWER,
    is_platform_admin: bool = False,
) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(cultivars_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_creating_tenant_key] = lambda: creating_tenant_key
    # SEC-005 (#1113): the create route now also resolves a role-bearing context and
    # the platform-admin flag. Overridden here for two reasons — to keep the tier
    # datastore-free (see the module docstring) and to model a caller who is allowed
    # to create, so these stamping tests keep testing the stamp and not the gate.
    app.dependency_overrides[get_active_tenant_context] = lambda: TenantContext(
        tenant_key=_ROLE_CONTEXT_TENANT, tenant_slug="t", user_key="user_1", role=role
    )
    app.dependency_overrides[get_is_platform_admin] = lambda: is_platform_admin
    return app


def _service() -> MagicMock:
    service = MagicMock()
    # ``tenant_key`` is the C-4 co-scoping argument for the *parent species* lookup
    # (a foreign species must 404 rather than gain a has_cultivar edge); this file
    # is about the *stamping* on the new row, so the stub just accepts it. That the
    # route actually threads it is asserted below and proven against the real
    # service in ``test_cultivar_authorization_api.py``. ``caller_role`` /
    # ``is_platform_admin`` (SEC-005, #1113) are accepted for the same reason: the
    # gate itself is proven against the real service in that same file.
    service.create_cultivar.side_effect = lambda c, **_kwargs: c.model_copy(update={"key": "cv_1"})
    return service


# ── Create stamps the caller's tenant ────────────────────────────────────────


def test_create_stamps_the_callers_tenant_key(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    service = _service()
    client = TestClient(_app(service, creating_tenant_key="tenant_personal_1"))

    resp = client.post("/api/v1/species/sp_basil/cultivars", json=_BODY)

    assert resp.status_code == 201
    created = service.create_cultivar.call_args.args[0]
    # Not ``_ROLE_CONTEXT_TENANT``: the stamp comes from ``get_creating_tenant_key``,
    # while the SEC-005 (#1113) context contributes only the role.
    assert created.tenant_key == "tenant_personal_1"
    assert created.origin is DataOrigin.TENANT
    # C-4: the very same resolved tenant scopes the parent-species lookup, so the
    # ownership stamp and the species scope can never drift apart at this route.
    assert service.create_cultivar.call_args.kwargs["tenant_key"] == "tenant_personal_1"
    # SEC-005 (#1113): the role really is threaded to the service — a route that
    # dropped it would fall into the service's system-context escape and gate nothing.
    assert service.create_cultivar.call_args.kwargs["caller_role"] is TenantRole.GROWER


def test_only_the_creating_tenant_dependency_moves_the_stamp(monkeypatch):
    # AC 4 / F-3 back-compat, stated as a difference: the role context is identical
    # in both requests and only ``get_creating_tenant_key`` varies — and the stamp
    # follows it. That is the property the four test files overriding this alias rely
    # on. Were the route to read ``ctx.tenant_key`` instead, both stamps would come
    # out as ``_ROLE_CONTEXT_TENANT`` and those files would pass while proving
    # nothing about ownership.
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    stamps = []
    for tenant in ("tenant_a", "tenant_b"):
        service = _service()
        client = TestClient(_app(service, creating_tenant_key=tenant))

        assert client.post("/api/v1/species/sp_basil/cultivars", json=_BODY).status_code == 201
        stamps.append(service.create_cultivar.call_args.args[0].tenant_key)

    assert stamps == ["tenant_a", "tenant_b"]


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


def test_the_light_mode_operator_can_still_curate_the_catalogue(monkeypatch):
    # Light mode (REQ-027) modelled as it actually is: no resolvable tenant, no
    # membership (hence the fail-safe VIEWER role) and the anonymous operator counted
    # as platform admin. The SEC-005 (#1113) gate must let that caller through on the
    # platform-admin arm, or light mode loses the ability to add cultivars at all.
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    service = _service()
    client = TestClient(_app(service, creating_tenant_key="", role=TenantRole.VIEWER, is_platform_admin=True))

    resp = client.post("/api/v1/species/sp_basil/cultivars", json=_BODY)

    assert resp.status_code == 201
    assert service.create_cultivar.call_args.kwargs["is_platform_admin"] is True


def test_the_missing_tenant_guard_answers_before_the_role_gate(monkeypatch):
    # SEC-004 pendant vs SEC-005 (#1113) ordering, pinned on this route too: a
    # full-mode caller with neither an active tenant nor a writing role gets the 422.
    # The gate lives in the service, so "the route body refused first" is exactly
    # what an uncalled service proves.
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    service = _service()
    client = TestClient(_app(service, creating_tenant_key="", role=TenantRole.VIEWER))

    resp = client.post("/api/v1/species/sp_basil/cultivars", json=_BODY)

    assert resp.status_code == 422
    service.create_cultivar.assert_not_called()


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
