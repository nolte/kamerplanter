from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.common.enums import AdminScope, TenantRole, TenantStatus, TenantType


class Tenant(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    tenant_type: TenantType = TenantType.PERSONAL
    description: str | None = None
    owner_user_key: str
    #: Lifecycle state (REQ-024 AK-65, MT-027 #2123). Replaced the ``is_active``
    #: bool (migration v0085): ``is_active`` is now *derived* — only ``active``
    #: resolves into an authorization context (#2105).
    status: TenantStatus = TenantStatus.ACTIVE
    #: When the erasure of a ``pending_deletion`` / ``orphaned`` tenant runs — the
    #: end of the cancellable grace (``RETENTION_TENANT_ERASURE_GRACE_DAYS``).
    #: ``None`` in every other state.
    deletion_scheduled_at: datetime | None = None
    is_platform: bool = False
    max_members: int = Field(default=1, ge=1)
    #: Free-form settings sub-object (REQ-024). REQ-031 §3.1 stores the KI toggle
    #: block here (``ai_features_enabled``, ``ai_default_provider_key``,
    #: ``ai_allow_cloud_providers``, ``ai_daily_tip_enabled``).
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def _legacy_is_active(cls, data: Any) -> Any:
        """Read a document (or a constructor call) that still carries the retired bool (#2123).

        v0085 moves every stored tenant to ``status`` and drops ``is_active``. A
        document read before it ran — or code that still passes ``is_active=False`` —
        must not come out *active* just because the bool is no field any more: without
        a ``status``, ``is_active == false`` reads as ``suspended``. A ``status`` that
        is present always wins.
        """
        if isinstance(data, dict) and "is_active" in data:
            data = dict(data)
            legacy = data.pop("is_active")
            if data.get("status") is None and legacy is False:
                data["status"] = TenantStatus.SUSPENDED
        return data

    @property
    def is_active(self) -> bool:
        """Whether the tenant resolves for its members: ``status == active`` and nothing else (#2105, #2123).

        Read-only on purpose: the state is written as ``status``. Every resolver that
        reads ``is_active`` (``test_tenant_lookups_read_is_active``) therefore refuses a
        suspended, pending-deletion, orphaned or deleted tenant alike.
        """
        return self.status == TenantStatus.ACTIVE


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    tenant_type: TenantType = TenantType.ORGANIZATION
    description: str | None = None
    max_members: int = Field(default=50, ge=1)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    max_members: int | None = Field(default=None, ge=1)


class TenantWithRole(BaseModel):
    key: str
    name: str
    slug: str
    tenant_type: TenantType
    description: str | None
    role: TenantRole
    # REQ-049 axis 2 — carried alongside the rank because neither implies the
    # other; the tenant switcher and every gated action need both.
    admin_scopes: list[AdminScope] = Field(default_factory=list)
    is_active: bool
