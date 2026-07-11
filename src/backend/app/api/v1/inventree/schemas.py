"""REQ-016 InvenTree integration API request/response schemas.

The API token is *write-only*: it is accepted on create/update but never echoed
back. Responses expose ``api_token_set`` (a boolean) instead of the ciphertext or
plaintext (IT-002).
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

# ── Connections ─────────────────────────────────────────────────────────


class InvenTreeConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=2048)
    api_token: str = Field(min_length=1)
    is_active: bool = True
    verify_ssl: bool = True
    sync_interval_minutes: int = Field(default=60, ge=5, le=1440)
    push_interval_minutes: int = Field(default=5, ge=1, le=60)


class InvenTreeConnectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = Field(default=None, min_length=1, max_length=2048)
    api_token: str | None = None
    is_active: bool | None = None
    verify_ssl: bool | None = None
    sync_interval_minutes: int | None = Field(default=None, ge=5, le=1440)
    push_interval_minutes: int | None = Field(default=None, ge=1, le=60)


class InvenTreeConnectionResponse(BaseModel):
    key: str
    name: str
    base_url: str
    is_active: bool = True
    verify_ssl: bool = True
    api_token_set: bool = False
    sync_interval_minutes: int = 60
    push_interval_minutes: int = 5
    last_health_check_at: datetime | None = None
    last_health_check_ok: bool | None = None
    last_stock_sync_at: datetime | None = None
    last_push_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HealthCheckResponse(BaseModel):
    healthy: bool


# ── References ──────────────────────────────────────────────────────────


class ReferenceLinkRequest(BaseModel):
    entity_collection: str = Field(min_length=1)
    entity_key: str = Field(min_length=1)
    inventree_part_id: int = Field(gt=0)
    auto_deduct: bool = False
    deduct_unit: str | None = None


class InvenTreeReferenceResponse(BaseModel):
    key: str
    entity_collection: str
    entity_key: str
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


# ── Transactions ────────────────────────────────────────────────────────


class StockTransactionResponse(BaseModel):
    key: str
    reference_key: str
    inventree_part_id: int
    transaction_type: StockTransactionType
    quantity: float
    unit: str
    reason: str
    source_event_collection: str | None = None
    source_event_key: str | None = None
    status: StockTransactionStatus
    retry_count: int = 0
    last_error: str | None = None
    synced_at: datetime | None = None
    created_at: datetime | None = None


# ── Equipment ───────────────────────────────────────────────────────────


class EquipmentCreate(BaseModel):
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


class EquipmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    equipment_type: EquipmentType | None = None
    status: EquipmentStatus | None = None
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    purchase_date: date | None = None
    warranty_until: date | None = None
    location_key: str | None = None
    inventree_part_id: int | None = None
    notes: str | None = None


class EquipmentResponse(BaseModel):
    key: str
    name: str
    equipment_type: EquipmentType
    status: EquipmentStatus
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
