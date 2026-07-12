"""REQ-016 InvenTree integration — persisted domain models.

Couples Kamerplanter entities (fertilizers, tanks, equipment) to an external
InvenTree inventory instance. Every persisted document is tenant-scoped
(REQ-024): a connection, reference, transaction or equipment item belongs to
exactly one tenant, so InvenTree data never leaks across tenants.

The API token is stored **encrypted** (``api_token_encrypted``, Fernet/AES-256)
and never serialized into an API response (IT-001/IT-002). ``StockTransaction``
is an immutable audit-log entry for consumption bookings.

Source code is English (NFR-003); the specification lives in
``spec/req/REQ-016_InvenTree-Integration.md`` (German).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import (
    EquipmentStatus,
    EquipmentType,
    StockTransactionStatus,
    StockTransactionType,
)


class InvenTreeConnection(BaseModel):
    """Server configuration for a tenant's InvenTree instance.

    ``api_token_encrypted`` holds the Fernet ciphertext of the API token; the
    plaintext token is only ever handled transiently in the service layer and is
    never persisted or returned (IT-001/IT-002).
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=2048)
    api_token_encrypted: str = ""
    is_active: bool = True
    verify_ssl: bool = True
    sync_interval_minutes: int = Field(default=60, ge=5, le=1440)
    push_interval_minutes: int = Field(default=5, ge=1, le=60)
    last_health_check_at: datetime | None = None
    last_health_check_ok: bool | None = None
    last_stock_sync_at: datetime | None = None
    last_push_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class Equipment(BaseModel):
    """An operating resource (pump, sensor, tool, cleaning agent, …)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    equipment_type: EquipmentType
    status: EquipmentStatus = EquipmentStatus.ACTIVE
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    purchase_date: date | None = None
    warranty_until: date | None = None
    location_key: str | None = None
    inventree_part_id: int | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class InvenTreeReference(BaseModel):
    """Link between a Kamerplanter entity and an InvenTree part."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    entity_collection: str = Field(min_length=1)
    entity_key: str = Field(min_length=1)
    inventree_part_id: int
    inventree_part_name: str | None = None
    inventree_ipn: str | None = None
    cached_stock: float | None = None
    cached_stock_unit: str | None = None
    cached_stock_updated_at: datetime | None = None
    auto_deduct: bool = False
    deduct_unit: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class StockTransaction(BaseModel):
    """Immutable transaction-log entry for a consumption booking."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    reference_key: str = Field(min_length=1)
    inventree_part_id: int
    transaction_type: StockTransactionType
    quantity: float = Field(gt=0)
    unit: str
    reason: str
    source_event_collection: str | None = None
    source_event_key: str | None = None
    status: StockTransactionStatus = StockTransactionStatus.PENDING
    retry_count: int = Field(default=0, ge=0)
    last_error: str | None = None
    inventree_response: dict | None = None
    synced_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
