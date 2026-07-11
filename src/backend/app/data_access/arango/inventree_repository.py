"""REQ-016 InvenTree integration ArangoDB repository.

Persists the four tenant-scoped collections — connections, references,
immutable stock transactions and equipment — plus the graph edges linking
entities to references, references to transactions and equipment to locations.

All AQL is parameterised via ``bind_vars`` (never f-string interpolation of
values) and every list query filters on ``tenant_key`` with an up-front
non-empty guard (SEC-B4 cross-tenant isolation).
"""

from __future__ import annotations

from typing import Any

from arango.database import StandardDatabase

from app.common.enums import LinkableEntityCollection
from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.inventree import (
    Equipment,
    InvenTreeConnection,
    InvenTreeReference,
    StockTransaction,
)

#: Allowlisted collections that may receive a ``has_inventree_ref`` edge. Mirrors
#: :class:`~app.common.enums.LinkableEntityCollection` and is re-checked here as a
#: defense-in-depth guard before dialing ``self._db.collection(<name>)``.
_LINKABLE_COLLECTIONS = frozenset(c.value for c in LinkableEntityCollection)


class ArangoInvenTreeRepository(BaseArangoRepository[InvenTreeConnection]):
    """Repository for the InvenTree integration domain (all tenant-scoped)."""

    is_tenant_scoped = True
    _model_cls = InvenTreeConnection
    _entity_name = "InvenTreeConnection"

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.INVENTREE_CONNECTIONS)
        self._references = BaseArangoRepository[InvenTreeReference](db, col.INVENTREE_REFERENCES, InvenTreeReference)
        self._references.is_tenant_scoped = True
        self._transactions = BaseArangoRepository[StockTransaction](db, col.STOCK_TRANSACTIONS, StockTransaction)
        self._transactions.is_tenant_scoped = True
        self._equipment = BaseArangoRepository[Equipment](db, col.EQUIPMENT, Equipment)
        self._equipment.is_tenant_scoped = True

    # ── Connections ─────────────────────────────────────────────────────

    def list_connections(self, tenant_key: str) -> list[InvenTreeConnection]:
        self._require_tenant_key(tenant_key, "list_connections")
        return self.find_by_field("tenant_key", tenant_key, sort="name")

    def create_connection(self, connection: InvenTreeConnection) -> InvenTreeConnection:
        return self.create(connection)

    def get_connection(self, key: str) -> InvenTreeConnection | None:
        return self.get_by_key(key)

    def get_connection_or_raise(self, key: str) -> InvenTreeConnection:
        return self.get_or_raise(key)

    def update_connection(self, key: str, connection: InvenTreeConnection) -> InvenTreeConnection:
        return self.update(key, connection)

    def delete_connection(self, key: str) -> bool:
        return self.delete(key)

    def get_active_connection(self, tenant_key: str) -> InvenTreeConnection | None:
        """The tenant's first active connection (``None`` when none exists)."""
        self._require_tenant_key(tenant_key, "get_active_connection")
        found = self.find_by_field(
            "tenant_key",
            tenant_key,
            extra_filters=[("is_active", "==", True)],
            sort="name",
            offset=0,
            limit=1,
        )
        return found[0] if found else None

    # ── References ──────────────────────────────────────────────────────

    def list_references(self, tenant_key: str, entity_collection: str | None = None) -> list[InvenTreeReference]:
        self._require_tenant_key(tenant_key, "list_references")
        extra: list[tuple[str, str, Any]] = []
        if entity_collection:
            extra.append(("entity_collection", "==", entity_collection))
        return self._references.find_by_field("tenant_key", tenant_key, extra_filters=extra, sort="entity_collection")

    def get_reference(self, key: str) -> InvenTreeReference | None:
        return self._references.get_by_key(key)

    def get_reference_or_raise(self, key: str) -> InvenTreeReference:
        return self._references.get_or_raise(key)

    def find_reference_by_entity(
        self, tenant_key: str, entity_collection: str, entity_key: str
    ) -> InvenTreeReference | None:
        self._require_tenant_key(tenant_key, "find_reference_by_entity")
        return self._references.find_one_by_field(
            "tenant_key",
            tenant_key,
            extra_filters=[
                ("entity_collection", "==", entity_collection),
                ("entity_key", "==", entity_key),
            ],
        )

    def verify_linkable_entity(self, entity_collection: str, entity_key: str, tenant_key: str) -> None:
        """Ensure the to-be-linked entity exists and is visible to ``tenant_key``.

        The reference-link request already allowlists ``entity_collection`` to
        ``fertilizers | tanks | equipment``
        (:class:`~app.common.enums.LinkableEntityCollection`); this guards the
        *value* side. An entity that does not exist, or that belongs to another
        tenant, must never receive a ``has_inventree_ref`` edge — otherwise a
        GROWER could point an edge at a foreign or dangling key (graph pollution
        / latent cross-tenant leak, SEC-B4 / IT-003).

        Globally-seeded catalog rows (empty ``tenant_key``, e.g. the shared
        fertilizer catalog) stay linkable, mirroring the hybrid-catalog read
        visibility. On any violation we fail closed with
        :class:`NotFoundError` (→ HTTP 404) rather than a 403, so the existence
        of a foreign key is never disclosed.
        """
        self._require_tenant_key(tenant_key, "verify_linkable_entity")
        if entity_collection not in _LINKABLE_COLLECTIONS:
            # Defense-in-depth: never dial an off-allowlist collection handle.
            raise NotFoundError(entity_collection, entity_key)
        doc = self._db.collection(entity_collection).get(entity_key)
        if doc is None:
            raise NotFoundError(entity_collection, entity_key)
        doc_tenant = doc.get("tenant_key", "") or ""
        if doc_tenant not in ("", tenant_key):
            raise NotFoundError(entity_collection, entity_key)

    def upsert_reference(self, reference: InvenTreeReference) -> InvenTreeReference:
        existing = self.find_reference_by_entity(
            reference.tenant_key, reference.entity_collection, reference.entity_key
        )
        if existing is not None and existing.key:
            merged = reference.model_copy(update={"key": existing.key})
            return self._references.update(existing.key, merged)
        created = self._references.create(reference)
        if created.key:
            self.create_edge(
                col.HAS_INVENTREE_REF,
                f"{reference.entity_collection}/{reference.entity_key}",
                f"{col.INVENTREE_REFERENCES}/{created.key}",
                {"linked_at": self._now()},
            )
        return created

    def update_reference(self, key: str, reference: InvenTreeReference) -> InvenTreeReference:
        return self._references.update(key, reference)

    def update_cached_stock(self, key: str, *, stock: float, unit: str | None, updated_at: str) -> InvenTreeReference:
        existing = self._references.get_or_raise(key)
        merged = existing.model_copy(
            update={
                "cached_stock": stock,
                "cached_stock_unit": unit,
                "cached_stock_updated_at": updated_at,
            }
        )
        return self._references.update(key, merged)

    def delete_reference(self, key: str) -> bool:
        ref_id = f"{col.INVENTREE_REFERENCES}/{key}"
        self.delete_edges(col.HAS_INVENTREE_REF, ref_id, direction="inbound")
        self.delete_edges(col.HAS_STOCK_TRANSACTION, ref_id)
        return self._references.delete(key)

    # ── Stock transactions (immutable) ──────────────────────────────────

    def create_transaction(self, transaction: StockTransaction) -> StockTransaction:
        created = self._transactions.create(transaction)
        if transaction.reference_key and created.key:
            self.create_edge(
                col.HAS_STOCK_TRANSACTION,
                f"{col.INVENTREE_REFERENCES}/{transaction.reference_key}",
                f"{col.STOCK_TRANSACTIONS}/{created.key}",
            )
        return created

    def find_transactions(
        self,
        tenant_key: str,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[StockTransaction]:
        self._require_tenant_key(tenant_key, "find_transactions")
        extra: list[tuple[str, str, Any]] = []
        if status:
            extra.append(("status", "==", status))
        return self._transactions.find_by_field(
            "tenant_key",
            tenant_key,
            extra_filters=extra,
            sort="created_at",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
        )

    def find_pending_transactions(self, tenant_key: str, max_retries: int = 3) -> list[StockTransaction]:
        self._require_tenant_key(tenant_key, "find_pending_transactions")
        return self._transactions.find_by_field(
            "tenant_key",
            tenant_key,
            extra_filters=[
                ("status", "==", "pending"),
                ("retry_count", "<", max_retries),
            ],
            sort="created_at",
        )

    def update_transaction(self, key: str, transaction: StockTransaction) -> StockTransaction:
        return self._transactions.update(key, transaction)

    # ── Equipment ───────────────────────────────────────────────────────

    def list_equipment(
        self,
        tenant_key: str,
        *,
        equipment_type: str | None = None,
        status: str | None = None,
    ) -> list[Equipment]:
        self._require_tenant_key(tenant_key, "list_equipment")
        extra: list[tuple[str, str, Any]] = []
        if equipment_type:
            extra.append(("equipment_type", "==", equipment_type))
        if status:
            extra.append(("status", "==", status))
        return self._equipment.find_by_field("tenant_key", tenant_key, extra_filters=extra, sort="name")

    def create_equipment(self, equipment: Equipment) -> Equipment:
        created = self._equipment.create(equipment)
        if equipment.location_key and created.key:
            self.create_edge(
                col.EQUIPMENT_AT,
                f"{col.EQUIPMENT}/{created.key}",
                f"{col.LOCATIONS}/{equipment.location_key}",
                {"assigned_at": self._now()},
            )
        return created

    def get_equipment(self, key: str) -> Equipment | None:
        return self._equipment.get_by_key(key)

    def get_equipment_or_raise(self, key: str) -> Equipment:
        return self._equipment.get_or_raise(key)

    def update_equipment(self, key: str, equipment: Equipment, *, location_changed: bool = False) -> Equipment:
        updated = self._equipment.update(key, equipment)
        if location_changed:
            eq_id = f"{col.EQUIPMENT}/{key}"
            self.delete_edges(col.EQUIPMENT_AT, eq_id)
            if equipment.location_key:
                self.create_edge(
                    col.EQUIPMENT_AT,
                    eq_id,
                    f"{col.LOCATIONS}/{equipment.location_key}",
                    {"assigned_at": self._now()},
                )
        return updated

    def delete_equipment(self, key: str) -> bool:
        eq_id = f"{col.EQUIPMENT}/{key}"
        self.delete_edges(col.EQUIPMENT_AT, eq_id)
        return self._equipment.delete(key)

    def find_equipment_by_location(self, tenant_key: str, location_key: str) -> list[Equipment]:
        """Equipment assigned to a location via the ``equipment_at`` edge.

        Tenant-filtered in AQL so a caller can never read another tenant's
        equipment through a foreign location key (SEC-B4).
        """
        self._require_tenant_key(tenant_key, "find_equipment_by_location")
        query = """
        FOR e IN @@edge
          FILTER e._to == @location_id
          FOR eq IN @@equipment
            FILTER eq._id == e._from AND eq.tenant_key == @tenant_key
            SORT eq.name
            RETURN eq
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@edge": col.EQUIPMENT_AT,
                "@equipment": col.EQUIPMENT,
                "location_id": f"{col.LOCATIONS}/{location_key}",
                "tenant_key": tenant_key,
            },
        )
        return [Equipment(**self._equipment._from_doc(doc)) for doc in cursor]  # noqa: SLF001
