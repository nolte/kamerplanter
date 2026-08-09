"""F-3/#808 acceptance-2: resolving the owning tenant for a global-route create.

The species catalogue create route is global (``/api/v1/species``), so
``get_current_tenant`` — bound to the ``/t/{slug}/`` path — cannot run there.
``get_creating_tenant_key`` resolves the caller's personal tenant instead, and
``TenantService.get_personal_tenant`` is the resolution behind it. Both fall back
to the shared catalogue (``""``) rather than leaking into a foreign tenant.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common import auth as auth_mod
from app.common.enums import TenantType
from app.domain.models.tenant import Tenant
from app.domain.services.tenant_service import TenantService


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="user_1")


def _tenant(key: str, tenant_type: TenantType, created_at: datetime | None = None) -> Tenant:
    return Tenant(
        _key=key,
        name=f"tenant-{key}",
        slug=f"tenant-{key}",
        tenant_type=tenant_type,
        owner_user_key="user_1",
        created_at=created_at,
    )


def _service(tenant_repo: MagicMock) -> TenantService:
    return TenantService(
        tenant_repo,
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )


# ── get_creating_tenant_key (the FastAPI dependency) ─────────────────────


def test_get_creating_tenant_key_returns_personal_tenant_key():
    tenant_service = MagicMock()
    tenant_service.get_personal_tenant.return_value = SimpleNamespace(key="tenant_personal_1")

    result = auth_mod.get_creating_tenant_key(user=_user(), tenant_service=tenant_service)

    assert result == "tenant_personal_1"
    tenant_service.get_personal_tenant.assert_called_once_with("user_1")


def test_get_creating_tenant_key_falls_back_to_global_when_none():
    tenant_service = MagicMock()
    tenant_service.get_personal_tenant.return_value = None

    result = auth_mod.get_creating_tenant_key(user=_user(), tenant_service=tenant_service)

    assert result == ""


# ── TenantService.get_personal_tenant (the resolution) ───────────────────


def test_get_personal_tenant_picks_the_owned_personal_tenant():
    tenant_repo = MagicMock()
    tenant_repo.list_by_owner.return_value = [
        _tenant("org_1", TenantType.ORGANIZATION),
        _tenant("personal_1", TenantType.PERSONAL),
    ]

    result = _service(tenant_repo).get_personal_tenant("user_1")

    assert result is not None
    assert result.key == "personal_1"


def test_get_personal_tenant_returns_none_when_only_organizations():
    tenant_repo = MagicMock()
    tenant_repo.list_by_owner.return_value = [_tenant("org_1", TenantType.ORGANIZATION)]

    assert _service(tenant_repo).get_personal_tenant("user_1") is None


def test_get_personal_tenant_prefers_the_newest_on_multiples():
    tenant_repo = MagicMock()
    tenant_repo.list_by_owner.return_value = [
        _tenant("older", TenantType.PERSONAL, created_at=datetime(2024, 1, 1, tzinfo=UTC)),
        _tenant("newer", TenantType.PERSONAL, created_at=datetime(2025, 1, 1, tzinfo=UTC)),
    ]

    result = _service(tenant_repo).get_personal_tenant("user_1")

    assert result is not None
    assert result.key == "newer"
