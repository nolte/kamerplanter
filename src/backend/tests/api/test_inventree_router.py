"""REQ-016 — API tests for the tenant-scoped InvenTree + equipment routers.

A real :class:`InvenTreeService` (plaintext-passthrough encryption + an injected
fake adapter) runs over an in-memory fake repository, exercising the full request
stack: connection CRUD, health-check, reference linking, browse, sync, the
transaction log and equipment CRUD — plus the security-critical paths: SSRF
rejection (422), cross-tenant isolation (404), RBAC (viewer 403) and graceful
degradation when the feature is disabled (409).
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.equipment.tenant_router import router as equipment_router
from app.api.v1.inventree.tenant_router import router as inventree_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_inventree_service
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import KamerplanterError, NotFoundError
from app.config.settings import settings
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.interfaces.inventree_adapter import (
    InvenTreeCategoryData,
    InvenTreePartData,
    InvenTreeStockItemData,
    StockAdjustmentResult,
)
from app.domain.models.inventree import (
    Equipment,
    InvenTreeConnection,
    InvenTreeReference,
    StockTransaction,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.inventree_service import InvenTreeService

TENANT_SLUG = "mein-garten"
TENANT_KEY = "tenant_garten"
OTHER_TENANT = "tenant_other"
PUBLIC_URL = "http://8.8.8.8/api"


class FakeAdapter:
    """Canned InvenTree adapter (no HTTP)."""

    def __init__(self, healthy: bool = True) -> None:
        self._healthy = healthy

    async def health_check(self) -> bool:
        return self._healthy

    async def get_part(self, part_id: int):
        if part_id == 404:
            return None
        return InvenTreePartData(pk=part_id, name="BioBloom", ipn="BB-1", total_in_stock=12.5, stock_unit="litre")

    async def search_parts(self, query, *, category_id=None, limit=25):
        return [InvenTreePartData(pk=1, name=f"match-{query}", total_in_stock=3.0)]

    async def get_stock_items(self, part_id):
        return [InvenTreeStockItemData(pk=900, part_id=part_id, quantity=100)]

    async def get_categories(self, *, parent_id=None):
        return [InvenTreeCategoryData(pk=1, name="Fertilizers")]

    async def remove_stock(self, items, *, notes=""):
        return StockAdjustmentResult(success=True, items_affected=len(items))

    async def add_stock(self, items, *, notes=""):
        return StockAdjustmentResult(success=True)

    async def count_stock(self, items, *, notes=""):
        return StockAdjustmentResult(success=True)


class FakeRepo:
    is_tenant_scoped = True

    def __init__(self) -> None:
        self.connections: dict[str, InvenTreeConnection] = {}
        self.references: dict[str, InvenTreeReference] = {}
        self.transactions: dict[str, StockTransaction] = {}
        self.equipment: dict[str, Equipment] = {}
        #: ``"collection/key" -> tenant_key`` for the linkable-entity guard. Empty
        #: → permissive (test shortcut); once populated it enforces existence +
        #: tenant visibility like the real repository.
        self.entities: dict[str, str] = {}
        self._seq = 0

    def _next(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}{self._seq}"

    def register_entity(self, entity_collection, entity_key, tenant_key):
        self.entities[f"{entity_collection}/{entity_key}"] = tenant_key

    def verify_linkable_entity(self, entity_collection, entity_key, tenant_key):
        if not self.entities:
            return
        doc_tenant = self.entities.get(f"{entity_collection}/{entity_key}")
        if doc_tenant is None or doc_tenant not in ("", tenant_key):
            raise NotFoundError(entity_collection, entity_key)

    # connections
    def list_connections(self, tenant_key):
        return [c for c in self.connections.values() if c.tenant_key == tenant_key]

    def create_connection(self, connection):
        key = self._next("conn")
        stored = connection.model_copy(update={"key": key})
        self.connections[key] = stored
        return stored

    def get_connection(self, key):
        return self.connections.get(key)

    def get_connection_or_raise(self, key):
        c = self.connections.get(key)
        if c is None:
            raise NotFoundError("InvenTreeConnection", key)
        return c

    def update_connection(self, key, connection):
        stored = connection.model_copy(update={"key": key})
        self.connections[key] = stored
        return stored

    def delete_connection(self, key):
        self.connections.pop(key, None)
        return True

    def get_active_connection(self, tenant_key):
        for c in self.connections.values():
            if c.tenant_key == tenant_key and c.is_active:
                return c
        return None

    # references
    def list_references(self, tenant_key, entity_collection=None):
        items = [r for r in self.references.values() if r.tenant_key == tenant_key]
        if entity_collection:
            items = [r for r in items if r.entity_collection == entity_collection]
        return items

    def get_reference_or_raise(self, key):
        r = self.references.get(key)
        if r is None:
            raise NotFoundError("InvenTreeReference", key)
        return r

    def find_reference_by_entity(self, tenant_key, entity_collection, entity_key):
        for r in self.references.values():
            if r.tenant_key == tenant_key and r.entity_collection == entity_collection and r.entity_key == entity_key:
                return r
        return None

    def upsert_reference(self, reference):
        key = reference.key or self._next("ref")
        stored = reference.model_copy(update={"key": key})
        self.references[key] = stored
        return stored

    def update_cached_stock(self, key, *, stock, unit, updated_at):
        ref = self.references[key]
        merged = ref.model_copy(update={"cached_stock": stock, "cached_stock_unit": unit})
        self.references[key] = merged
        return merged

    def delete_reference(self, key):
        self.references.pop(key, None)
        return True

    # transactions
    def find_transactions(self, tenant_key, *, status=None, offset=0, limit=50):
        items = [t for t in self.transactions.values() if t.tenant_key == tenant_key]
        if status:
            items = [t for t in items if t.status.value == status]
        return items[offset : offset + limit]

    def find_pending_transactions(self, tenant_key, max_retries=3):
        return []

    def update_transaction(self, key, transaction):
        self.transactions[key] = transaction
        return transaction

    # equipment
    def list_equipment(self, tenant_key, *, equipment_type=None, status=None):
        items = [e for e in self.equipment.values() if e.tenant_key == tenant_key]
        if equipment_type:
            items = [e for e in items if e.equipment_type.value == equipment_type]
        if status:
            items = [e for e in items if e.status.value == status]
        return items

    def create_equipment(self, equipment):
        key = self._next("eq")
        stored = equipment.model_copy(update={"key": key})
        self.equipment[key] = stored
        return stored

    def get_equipment_or_raise(self, key):
        e = self.equipment.get(key)
        if e is None:
            raise NotFoundError("Equipment", key)
        return e

    def update_equipment(self, key, equipment, *, location_changed=False):
        stored = equipment.model_copy(update={"key": key})
        self.equipment[key] = stored
        return stored

    def delete_equipment(self, key):
        self.equipment.pop(key, None)
        return True

    def find_equipment_by_location(self, tenant_key, location_key):
        return [e for e in self.equipment.values() if e.tenant_key == tenant_key and e.location_key == location_key]


def _ctx(
    role: TenantRole = TenantRole.LEAD,
    tenant_key: str = TENANT_KEY,
    admin_scopes: list[AdminScope] | None = None,
) -> TenantContext:
    """Build a caller. Defaults to lead + technical, the InvenTree operator.

    REQ-049 moved connection management to the ``technical`` scope, so the
    domain role alone no longer opens these endpoints — which is why the scopes
    are an explicit parameter rather than derived from the role.
    """
    return TenantContext(
        tenant_key=tenant_key,
        tenant_slug=TENANT_SLUG,
        user_key="user_1",
        role=role,
        admin_scopes=[AdminScope.TECHNICAL] if admin_scopes is None else admin_scopes,
    )


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code})


def _build(
    role: TenantRole = TenantRole.LEAD,
    tenant_key: str = TENANT_KEY,
    admin_scopes: list[AdminScope] | None = None,
) -> tuple[TestClient, FakeRepo, InvenTreeService]:
    repo = FakeRepo()
    service = InvenTreeService(repo, EncryptionEngine(""), adapter_factory=lambda conn: FakeAdapter())  # type: ignore[arg-type]

    app = FastAPI()
    app.include_router(inventree_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(equipment_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: _ctx(role, tenant_key, admin_scopes)
    app.dependency_overrides[get_inventree_service] = lambda: service
    return TestClient(app), repo, service


def _inv(path: str = "") -> str:
    return f"/api/v1/t/{TENANT_SLUG}/inventree{path}"


def _eq(path: str = "") -> str:
    return f"/api/v1/t/{TENANT_SLUG}/equipment{path}"


_CONN_BODY = {"name": "Main", "base_url": PUBLIC_URL, "api_token": "tok-123"}


@pytest.fixture(autouse=True)
def _enable_inventree():
    prev_enabled = settings.inventree_enabled
    prev_private = settings.inventree_allow_private_endpoint
    settings.inventree_enabled = True
    settings.inventree_allow_private_endpoint = True
    yield
    settings.inventree_enabled = prev_enabled
    settings.inventree_allow_private_endpoint = prev_private


# ── Connections ─────────────────────────────────────────────────────────


class TestConnections:
    def test_create_encrypts_token_and_hides_it(self):
        client, repo, _ = _build()
        resp = client.post(_inv("/connections"), json=_CONN_BODY)
        assert resp.status_code == 201
        body = resp.json()
        assert body["api_token_set"] is True
        assert "api_token" not in body
        assert "api_token_encrypted" not in body
        # Stored connection carries ciphertext (plaintext-passthrough here), never
        # the raw token field in the response.
        stored = next(iter(repo.connections.values()))
        assert stored.api_token_encrypted == "tok-123"

    def test_create_rejects_ssrf_metadata_url(self):
        client, _, _ = _build()
        resp = client.post(
            _inv("/connections"),
            json={"name": "Evil", "base_url": "http://169.254.169.254/api", "api_token": "x"},
        )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "VALIDATION_ERROR"

    def test_list_and_get_roundtrip(self):
        client, _, _ = _build()
        created = client.post(_inv("/connections"), json=_CONN_BODY).json()
        key = created["key"]
        listed = client.get(_inv("/connections")).json()
        assert len(listed) == 1
        fetched = client.get(_inv(f"/connections/{key}")).json()
        assert fetched["name"] == "Main"

    def test_health_check_reports_healthy(self):
        client, _, _ = _build()
        key = client.post(_inv("/connections"), json=_CONN_BODY).json()["key"]
        resp = client.post(_inv(f"/connections/{key}/health-check"))
        assert resp.status_code == 200
        assert resp.json() == {"healthy": True}

    def test_update_rotates_token(self):
        client, repo, _ = _build()
        key = client.post(_inv("/connections"), json=_CONN_BODY).json()["key"]
        resp = client.put(_inv(f"/connections/{key}"), json={"api_token": "new-token"})
        assert resp.status_code == 200
        assert repo.connections[key].api_token_encrypted == "new-token"

    def test_delete_connection(self):
        client, repo, _ = _build()
        key = client.post(_inv("/connections"), json=_CONN_BODY).json()["key"]
        assert client.delete(_inv(f"/connections/{key}")).status_code == 204
        assert key not in repo.connections

    def test_a_lead_without_the_technical_scope_is_rejected(self):
        # REQ-049 AK-05: the connection is technical configuration, so the top
        # domain rank grants nothing here. Before the split this endpoint was
        # open to every admin, which is how a club had to hand its member list
        # to whoever wired up InvenTree.
        client, _, _ = _build(role=TenantRole.LEAD, admin_scopes=[])
        resp = client.post(_inv("/connections"), json=_CONN_BODY)
        assert resp.status_code == 403

    def test_the_management_scope_does_not_substitute(self):
        client, _, _ = _build(role=TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT])
        resp = client.post(_inv("/connections"), json=_CONN_BODY)
        assert resp.status_code == 403

    def test_a_viewer_holding_the_technical_scope_may_configure_it(self):
        # The other half of AK-05: the technician documents nothing in the
        # garden and still wires the integration.
        client, _, _ = _build(role=TenantRole.VIEWER, admin_scopes=[AdminScope.TECHNICAL])
        resp = client.post(_inv("/connections"), json=_CONN_BODY)
        assert resp.status_code == 201

    def test_cross_tenant_connection_returns_404(self):
        client, repo, _ = _build()
        repo.connections["foreign"] = InvenTreeConnection(
            _key="foreign", tenant_key=OTHER_TENANT, name="Other", base_url=PUBLIC_URL
        )
        resp = client.get(_inv("/connections/foreign"))
        assert resp.status_code == 404


class TestFeatureDisabled:
    def test_create_connection_disabled_returns_409(self):
        client, _, _ = _build()
        settings.inventree_enabled = False
        resp = client.post(_inv("/connections"), json=_CONN_BODY)
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "FEATURE_DISABLED"

    def test_link_without_active_connection_returns_409(self):
        client, _, _ = _build()
        resp = client.post(
            _inv("/references/link"),
            json={"entity_collection": "fertilizers", "entity_key": "fert_1", "inventree_part_id": 42},
        )
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "FEATURE_DISABLED"


class TestReferences:
    def _with_connection(self):
        client, repo, _ = _build()
        client.post(_inv("/connections"), json=_CONN_BODY)
        return client, repo

    def test_link_entity_persists_reference(self):
        client, repo = self._with_connection()
        resp = client.post(
            _inv("/references/link"),
            json={
                "entity_collection": "fertilizers",
                "entity_key": "fert_1",
                "inventree_part_id": 42,
                "auto_deduct": True,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["inventree_part_name"] == "BioBloom"
        assert body["cached_stock"] == 12.5
        assert body["auto_deduct"] is True

    def test_link_rejects_unknown_entity_collection(self):
        client, _ = self._with_connection()
        # IT-003/SEC: a collection outside the allowlist (fertilizers/tanks/
        # equipment) is rejected by request validation before touching InvenTree.
        resp = client.post(
            _inv("/references/link"),
            json={"entity_collection": "secrets", "entity_key": "x", "inventree_part_id": 42},
        )
        assert resp.status_code == 422

    def test_link_accepts_allowlisted_entity_collections(self):
        client, _ = self._with_connection()
        for collection in ("fertilizers", "tanks", "equipment"):
            resp = client.post(
                _inv("/references/link"),
                json={"entity_collection": collection, "entity_key": "e1", "inventree_part_id": 42},
            )
            assert resp.status_code == 201, collection
            assert resp.json()["entity_collection"] == collection

    def test_link_own_entity_succeeds(self):
        # SEC-B4 / IT-003: a valid, tenant-owned entity_key links (201).
        client, repo = self._with_connection()
        repo.register_entity("fertilizers", "fert_1", TENANT_KEY)
        resp = client.post(
            _inv("/references/link"),
            json={"entity_collection": "fertilizers", "entity_key": "fert_1", "inventree_part_id": 42},
        )
        assert resp.status_code == 201
        assert resp.json()["entity_key"] == "fert_1"

    def test_link_foreign_tenant_entity_returns_404(self):
        # SEC-B4 / IT-003: a foreign tenant's entity_key must not be linkable and
        # its existence must not leak (404, not 403).
        client, repo = self._with_connection()
        repo.register_entity("fertilizers", "fert_foreign", OTHER_TENANT)
        resp = client.post(
            _inv("/references/link"),
            json={"entity_collection": "fertilizers", "entity_key": "fert_foreign", "inventree_part_id": 42},
        )
        assert resp.status_code == 404
        assert repo.references == {}

    def test_link_nonexistent_entity_returns_404(self):
        client, repo = self._with_connection()
        repo.register_entity("fertilizers", "exists", TENANT_KEY)  # flip guard to enforce
        resp = client.post(
            _inv("/references/link"),
            json={"entity_collection": "fertilizers", "entity_key": "ghost", "inventree_part_id": 42},
        )
        assert resp.status_code == 404
        assert repo.references == {}

    def test_sync_reference_updates_cache(self):
        client, repo = self._with_connection()
        ref_key = client.post(
            _inv("/references/link"),
            json={"entity_collection": "fertilizers", "entity_key": "fert_1", "inventree_part_id": 42},
        ).json()["key"]
        resp = client.post(_inv(f"/references/{ref_key}/sync"))
        assert resp.status_code == 200
        assert resp.json()["stock"] == 12.5

    def test_browse_parts(self):
        client, _ = self._with_connection()
        resp = client.get(_inv("/browse/parts"), params={"query": "bloom"})
        assert resp.status_code == 200
        assert resp.json()[0]["name"] == "match-bloom"

    def test_trigger_sync_returns_stats(self):
        client, _ = self._with_connection()
        resp = client.post(_inv("/sync/trigger"))
        assert resp.status_code == 200
        assert "stock_sync" in resp.json()


class TestEquipment:
    _BODY = {"name": "Bluelab pH Pen", "equipment_type": "sensor", "location_key": "loc_1"}

    def test_create_and_get(self):
        client, _, _ = _build()
        created = client.post(_eq(""), json=self._BODY)
        assert created.status_code == 201
        key = created.json()["key"]
        fetched = client.get(_eq(f"/{key}"))
        assert fetched.status_code == 200
        assert fetched.json()["equipment_type"] == "sensor"

    def test_list_and_filter_by_location(self):
        client, _, _ = _build()
        client.post(_eq(""), json=self._BODY)
        listed = client.get(_eq("/by-location/loc_1")).json()
        assert len(listed) == 1

    def test_update_equipment(self):
        client, _, _ = _build()
        key = client.post(_eq(""), json=self._BODY).json()["key"]
        resp = client.put(_eq(f"/{key}"), json={"status": "maintenance"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "maintenance"

    def test_viewer_cannot_create_equipment(self):
        client, _, _ = _build(role=TenantRole.VIEWER)
        assert client.post(_eq(""), json=self._BODY).status_code == 403

    def test_grower_cannot_delete_equipment(self):
        client, repo, _ = _build(role=TenantRole.GROWER)
        repo.equipment["eq1"] = Equipment(_key="eq1", tenant_key=TENANT_KEY, name="Pump", equipment_type="pump")
        assert client.delete(_eq("/eq1")).status_code == 403

    def test_cross_tenant_equipment_returns_404(self):
        client, repo, _ = _build()
        repo.equipment["foreign"] = Equipment(
            _key="foreign", tenant_key=OTHER_TENANT, name="Other", equipment_type="tool"
        )
        assert client.get(_eq("/foreign")).status_code == 404
