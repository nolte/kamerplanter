"""REQ-016 InvenTree integration service.

Owns the tenant-scoped business logic: connection CRUD with **encrypted** token
handling, entity↔part references, InvenTree browsing, the immutable transaction
log and equipment CRUD. Every read/write is tenant-scoped — a connection,
reference, transaction or equipment item is loaded and ownership-verified against
``tenant_key`` before use, so nothing leaks across tenants (SEC-B4).

Security (REQ-016 §4.1):

* The API token is Fernet-encrypted (IT-001) before persistence and never
  returned (IT-002) — responses only report ``api_token_set``.
* The adapter is built via :meth:`_build_adapter`, which decrypts the token in
  memory and re-validates the ``base_url`` against SSRF (IT-003) — private/LAN
  addresses require the operator opt-in (``inventree_allow_private_endpoint``).
* When the feature is disabled (kill-switch off / no active connection) an
  operation that needs a live connection raises :class:`FeatureDisabledError`
  (409) rather than crashing — the integration is optional (graceful
  degradation).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from app.common.exceptions import FeatureDisabledError, NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.common.url_safety import validate_inventree_url
from app.config.settings import settings
from app.data_access.arango.inventree_repository import ArangoInvenTreeRepository
from app.data_access.external.inventree_adapter import InvenTreeRestAdapter
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.inventree_sync_engine import InvenTreeSyncEngine
from app.domain.interfaces.inventree_adapter import InvenTreeAdapter
from app.domain.models.inventree import (
    Equipment,
    InvenTreeConnection,
    InvenTreeReference,
    StockTransaction,
)

logger = structlog.get_logger(__name__)

#: Placeholder the frontend echoes for an already-stored token; treated (like an
#: empty string) as "token unchanged" on update.
_MASKED_SECRET = "••••"


class InvenTreeService:
    """Business logic for the optional REQ-016 InvenTree integration."""

    def __init__(
        self,
        repo: ArangoInvenTreeRepository,
        encryption_engine: EncryptionEngine,
        adapter_factory: Any | None = None,
        redis_client: Any | None = None,
    ) -> None:
        self._repo = repo
        self._encryption = encryption_engine
        # Shared Valkey/Redis client for the adapter's persistent per-connection
        # outbound rate-limit window (IT-005). Optional: without it the adapter
        # degrades to a best-effort per-instance window.
        self._redis = redis_client
        # Injectable for tests: (connection) -> InvenTreeAdapter. Defaults to the
        # real SSRF-guarded, token-decrypting REST adapter.
        self._adapter_factory = adapter_factory or self._build_adapter

    # ── Feature gate ────────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return settings.inventree_enabled

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise FeatureDisabledError("InvenTree integration", "the integration is disabled (kill-switch off)")

    # ── Adapter construction (SSRF + credential decryption) ─────────────

    def _build_adapter(self, connection: InvenTreeConnection) -> InvenTreeAdapter:
        # Re-validate the stored URL before dialing — defense against a URL that
        # became unsafe after storage or a DNS rebind (IT-003).
        validate_inventree_url(
            connection.base_url,
            allow_private=settings.inventree_allow_private_endpoint,
            field="base_url",
        )
        token = self._encryption.decrypt(connection.api_token_encrypted) if connection.api_token_encrypted else ""
        return InvenTreeRestAdapter(
            connection.base_url,
            token,
            verify_ssl=connection.verify_ssl,
            allow_private=settings.inventree_allow_private_endpoint,
            # Stable identifier + shared store keep the outbound rate-limit window
            # persistent across the per-request adapter rebuild (IT-005).
            connection_key=connection.key,
            redis_client=self._redis,
        )

    def _load_owned_connection(self, key: str, tenant_key: str) -> InvenTreeConnection:
        connection = self._repo.get_connection_or_raise(key)
        verify_tenant_ownership(connection, tenant_key, "InvenTreeConnection")
        return connection

    def _sync_engine_for(self, connection: InvenTreeConnection, tenant_key: str) -> InvenTreeSyncEngine:
        adapter = self._adapter_factory(connection)
        return InvenTreeSyncEngine(adapter, self._repo, tenant_key)

    def _active_engine(self, tenant_key: str) -> InvenTreeSyncEngine:
        self._require_enabled()
        connection = self._repo.get_active_connection(tenant_key)
        if connection is None:
            raise FeatureDisabledError("InvenTree integration", "no active connection configured for this tenant")
        return self._sync_engine_for(connection, tenant_key)

    # ── Connections ─────────────────────────────────────────────────────

    def list_connections(self, tenant_key: str) -> list[InvenTreeConnection]:
        return self._repo.list_connections(tenant_key)

    def get_connection(self, key: str, tenant_key: str) -> InvenTreeConnection:
        return self._load_owned_connection(key, tenant_key)

    def create_connection(
        self, tenant_key: str, name: str, base_url: str, api_token: str, *, verify_ssl: bool = True, **extra: Any
    ) -> InvenTreeConnection:
        self._require_enabled()
        # SSRF gate at write time — never persist a URL that dials an internal
        # address (IT-003).
        validate_inventree_url(base_url, allow_private=settings.inventree_allow_private_endpoint, field="base_url")
        if not api_token:
            raise ValidationError("An API token is required to create an InvenTree connection.")
        connection = InvenTreeConnection(
            tenant_key=tenant_key,
            name=name,
            base_url=base_url,
            api_token_encrypted=self._encryption.encrypt(api_token),
            verify_ssl=verify_ssl,
            **extra,
        )
        return self._repo.create_connection(connection)

    def update_connection(self, key: str, tenant_key: str, data: dict[str, Any]) -> InvenTreeConnection:
        self._require_enabled()
        connection = self._load_owned_connection(key, tenant_key)
        payload = dict(data)
        # Token rotation (IT-004): a new plaintext token is re-encrypted; an empty
        # or masked value preserves the stored ciphertext.
        new_token = payload.pop("api_token", None)
        if new_token and new_token != _MASKED_SECRET:
            payload["api_token_encrypted"] = self._encryption.encrypt(new_token)
        if "base_url" in payload:
            validate_inventree_url(
                payload["base_url"], allow_private=settings.inventree_allow_private_endpoint, field="base_url"
            )
        updated = connection.model_copy(update=payload)
        return self._repo.update_connection(key, updated)

    def delete_connection(self, key: str, tenant_key: str) -> None:
        self._load_owned_connection(key, tenant_key)
        self._repo.delete_connection(key)

    async def health_check(self, key: str, tenant_key: str) -> dict[str, Any]:
        """Probe the connection. Never a 500 — a generic ``{"healthy": bool}``.

        IT-006: does not disclose whether the URL is a valid InvenTree instance
        when auth fails — a failed probe simply reports ``healthy: false``.
        """
        self._require_enabled()
        connection = self._load_owned_connection(key, tenant_key)
        try:
            adapter = self._adapter_factory(connection)
            ok = await adapter.health_check()
        except Exception as exc:  # noqa: BLE001 — the probe must never surface a 500
            logger.warning("inventree_health_check_failed", connection_key=key, error=type(exc).__name__)
            ok = False
        updated = connection.model_copy(
            update={"last_health_check_at": datetime.now(tz=UTC), "last_health_check_ok": ok}
        )
        if connection.key:
            self._repo.update_connection(connection.key, updated)
        return {"healthy": ok}

    # ── References ──────────────────────────────────────────────────────

    def list_references(self, tenant_key: str, entity_collection: str | None = None) -> list[InvenTreeReference]:
        return self._repo.list_references(tenant_key, entity_collection)

    async def link_entity(
        self,
        tenant_key: str,
        entity_collection: str,
        entity_key: str,
        inventree_part_id: int,
        *,
        auto_deduct: bool = False,
        deduct_unit: str | None = None,
    ) -> InvenTreeReference:
        engine = self._active_engine(tenant_key)
        return await engine.link_entity(
            entity_collection,
            entity_key,
            inventree_part_id,
            auto_deduct=auto_deduct,
            deduct_unit=deduct_unit,
        )

    def _load_owned_reference(self, key: str, tenant_key: str) -> InvenTreeReference:
        reference = self._repo.get_reference_or_raise(key)
        verify_tenant_ownership(reference, tenant_key, "InvenTreeReference")
        return reference

    def unlink_entity(self, key: str, tenant_key: str) -> None:
        self._load_owned_reference(key, tenant_key)
        self._repo.delete_reference(key)

    async def sync_reference(self, key: str, tenant_key: str) -> dict[str, Any]:
        engine = self._active_engine(tenant_key)
        reference = self._load_owned_reference(key, tenant_key)
        part = await engine._adapter.get_part(reference.inventree_part_id)  # noqa: SLF001
        if part is None:
            raise NotFoundError("InvenTreePart", str(reference.inventree_part_id))
        if reference.key:
            self._repo.update_cached_stock(
                reference.key,
                stock=part.total_in_stock,
                unit=part.stock_unit,
                updated_at=datetime.now(tz=UTC).isoformat(),
            )
        return {"stock": part.total_in_stock, "unit": part.stock_unit}

    # ── Browse ──────────────────────────────────────────────────────────

    async def browse_parts(
        self, tenant_key: str, query: str, *, category_id: int | None = None, limit: int = 25
    ) -> list[dict[str, Any]]:
        engine = self._active_engine(tenant_key)
        parts = await engine._adapter.search_parts(query, category_id=category_id, limit=limit)  # noqa: SLF001
        return [p.model_dump() for p in parts]

    async def browse_categories(self, tenant_key: str, *, parent_id: int | None = None) -> list[dict[str, Any]]:
        engine = self._active_engine(tenant_key)
        categories = await engine._adapter.get_categories(parent_id=parent_id)  # noqa: SLF001
        return [c.model_dump() for c in categories]

    # ── Sync + transactions ─────────────────────────────────────────────

    async def sync_stock_levels(self, tenant_key: str) -> dict[str, Any]:
        return await self._active_engine(tenant_key).sync_stock_levels()

    async def push_pending_transactions(self, tenant_key: str) -> dict[str, Any]:
        return await self._active_engine(tenant_key).push_pending_transactions()

    def list_transactions(
        self, tenant_key: str, *, status: str | None = None, offset: int = 0, limit: int = 50
    ) -> list[StockTransaction]:
        return self._repo.find_transactions(tenant_key, status=status, offset=offset, limit=limit)

    # ── Equipment ───────────────────────────────────────────────────────

    def list_equipment(
        self, tenant_key: str, *, equipment_type: str | None = None, status: str | None = None
    ) -> list[Equipment]:
        return self._repo.list_equipment(tenant_key, equipment_type=equipment_type, status=status)

    def create_equipment(self, tenant_key: str, equipment: Equipment) -> Equipment:
        equipment.tenant_key = tenant_key
        return self._repo.create_equipment(equipment)

    def get_equipment(self, key: str, tenant_key: str) -> Equipment:
        equipment = self._repo.get_equipment_or_raise(key)
        verify_tenant_ownership(equipment, tenant_key, "Equipment")
        return equipment

    def update_equipment(self, key: str, tenant_key: str, data: dict[str, Any]) -> Equipment:
        equipment = self.get_equipment(key, tenant_key)
        location_changed = "location_key" in data and data["location_key"] != equipment.location_key
        updated = equipment.model_copy(update=data)
        return self._repo.update_equipment(key, updated, location_changed=location_changed)

    def delete_equipment(self, key: str, tenant_key: str) -> None:
        self.get_equipment(key, tenant_key)
        self._repo.delete_equipment(key)

    def find_equipment_by_location(self, tenant_key: str, location_key: str) -> list[Equipment]:
        return self._repo.find_equipment_by_location(tenant_key, location_key)
