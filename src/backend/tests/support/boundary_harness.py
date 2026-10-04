"""One in-process API over a real ArangoDB, with a caller the test can switch (#2099..#2119).

The tenant-boundary members all need the same thing: the **real** routers, DI
factories, services and repositories against a **real** database, with only the
caller's identity decided by the test. A stub would agree with the code whether
or not a predicate is there; this harness cannot.

``Caller`` is mutable on purpose: one module-scoped database holds the rows of two
tenants and the global catalogue, and each test switches who is asking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

TENANT_A = "tenant-alice"
TENANT_B = "tenant-bob"
SLUG_A = "alice"
SLUG_B = "bob"


@dataclass
class Caller:
    """Who is asking right now."""

    tenant_key: str = TENANT_A
    slug: str = SLUG_A
    user_key: str = "user-a"
    role: str = "lead"
    platform_admin: bool = False

    def as_a(self, role: str = "lead", *, platform_admin: bool = False) -> Caller:
        self.tenant_key, self.slug, self.user_key = TENANT_A, SLUG_A, "user-a"
        self.role, self.platform_admin = role, platform_admin
        return self

    def as_b(self, role: str = "lead") -> Caller:
        self.tenant_key, self.slug, self.user_key = TENANT_B, SLUG_B, "user-b"
        self.role, self.platform_admin = role, False
        return self


class BoundaryEnv:
    """The database, the app, and the caller; built by :func:`open_env`."""

    def __init__(self, db: Any, client: Any, caller: Caller, close: Any) -> None:
        self.db = db
        self.client = client
        self.caller = caller
        self._close = close

    def close(self) -> None:
        self._close()


def open_env(database_name: str, *router_modules: tuple[str, str]) -> BoundaryEnv:
    """Create ``database_name``, mount ``router_modules`` (``(module, attribute)``) and return the env.

    The routers resolve every repository through ``dependencies.get_db()``; the
    connection is swapped for the throwaway database and restored by ``close``.
    """
    import importlib

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient

    from app.common import dependencies as deps
    from app.common.auth import (
        get_active_tenant_context,
        get_active_tenant_key,
        get_current_tenant,
        get_current_user,
        get_is_platform_admin,
    )
    from app.common.enums import TenantRole
    from app.common.exceptions import KamerplanterError
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.connection import ArangoConnection
    from app.domain.models.tenant_context import TenantContext
    from app.domain.models.user import User

    settings = Settings(arangodb_database=database_name)
    conn = ArangoConnection(settings)
    db = conn.connect()
    col.ensure_collections(db)
    previous_connection = deps._connection
    deps._connection = conn

    app = FastAPI()
    for module_name, attribute in router_modules:
        app.include_router(getattr(importlib.import_module(module_name), attribute), prefix="/api/v1")

    @app.exception_handler(KamerplanterError)
    def _handler(_request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": str(exc)})

    caller = Caller()

    def _ctx() -> TenantContext:
        return TenantContext(
            tenant_key=caller.tenant_key,
            tenant_slug=caller.slug,
            user_key=caller.user_key,
            role=TenantRole(caller.role),
        )

    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_active_tenant_context] = _ctx
    app.dependency_overrides[get_active_tenant_key] = lambda: caller.tenant_key
    app.dependency_overrides[get_current_user] = lambda: User(
        _key=caller.user_key, email=f"{caller.user_key}@example.com", display_name=caller.user_key
    )
    app.dependency_overrides[get_is_platform_admin] = lambda: caller.platform_admin

    def _close() -> None:
        deps._connection = previous_connection
        sysdb = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        if sysdb.has_database(database_name):
            sysdb.delete_database(database_name)
        conn.close()

    return BoundaryEnv(db, TestClient(app, raise_server_exceptions=False), caller, _close)


def put(db: Any, collection: str, model: Any) -> None:
    """Insert a pydantic model the way the repositories do."""
    doc = {k: v for k, v in model.model_dump(by_alias=True, mode="json").items() if v is not None}
    db.collection(collection).insert(doc, overwrite=True)
