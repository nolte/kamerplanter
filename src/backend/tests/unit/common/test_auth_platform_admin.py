"""Platform-admin gating across light/full mode (REQ-027 / REQ-029-A §4.5)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api.v1.users import router as users_mod
from app.common import auth as auth_mod
from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="system-user")


def _membership(role: TenantRole, active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(role=role, is_active=active)


# -- require_platform_admin -------------------------------------------------


def test_require_platform_admin_light_mode_allows_system_user(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "light")
    tenant_service = MagicMock()

    result = auth_mod.require_platform_admin(user=_user(), tenant_service=tenant_service)

    assert result.key == "system-user"
    # Light mode must not even consult tenant memberships.
    tenant_service.get_membership.assert_not_called()


def test_require_platform_admin_full_mode_rejects_non_admin(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = _membership(TenantRole.GROWER)

    with pytest.raises(ForbiddenError):
        auth_mod.require_platform_admin(user=_user(), tenant_service=tenant_service)


def test_require_platform_admin_full_mode_allows_platform_admin(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = _membership(TenantRole.ADMIN)

    result = auth_mod.require_platform_admin(user=_user(), tenant_service=tenant_service)

    assert result.key == "system-user"
    tenant_service.get_membership.assert_called_once_with("system-user", "platform")


# -- _is_platform_admin (/users/me flag) ------------------------------------


def test_is_platform_admin_true_in_light_mode(monkeypatch):
    # ``_is_platform_admin`` is the shared ``auth.is_platform_admin`` (re-exported
    # by the users router), so the mode flag lives on ``auth.settings``.
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "light")
    tenant_service = MagicMock()

    assert users_mod._is_platform_admin(tenant_service, "system-user") is True
    tenant_service.get_membership.assert_not_called()


def test_is_platform_admin_full_mode_follows_membership(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = _membership(TenantRole.ADMIN)
    assert users_mod._is_platform_admin(tenant_service, "u1") is True

    tenant_service.get_membership.return_value = _membership(TenantRole.VIEWER)
    assert users_mod._is_platform_admin(tenant_service, "u1") is False

    tenant_service.get_membership.return_value = None
    assert users_mod._is_platform_admin(tenant_service, "u1") is False
