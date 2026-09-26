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
#
# Since #1501 (review SCR-006) ``require_platform_admin`` takes the ANSWER, not the
# tenant service: it depends on ``get_is_platform_admin``, so a route carrying the
# gate *and* threading the flag into its service resolves one sub-graph instead of
# two and hits the tenant store once instead of twice.
#
# The three claims these tests made did not disappear with the parameter, they
# moved to the function that now owns each of them, and they are asserted there
# rather than dropped:
#
# * "light mode must not consult memberships" and "full mode looks up
#   (user, 'platform')" are properties of the LOOKUP → asserted below on
#   ``get_is_platform_admin``, which performs it;
# * "a non-admin is refused / an admin is returned" is the property of the GATE →
#   asserted on ``require_platform_admin`` with the boolean it now receives.
#
# Splitting them this way is the point: a gate driven by a stub boolean can no
# longer pass because the lookup happened to be permissive, and vice versa.


def test_require_platform_admin_returns_the_user_when_the_flag_is_true():
    result = auth_mod.require_platform_admin(user=_user(), platform_admin=True)

    assert result.key == "system-user"


def test_require_platform_admin_refuses_when_the_flag_is_false():
    with pytest.raises(ForbiddenError):
        auth_mod.require_platform_admin(user=_user(), platform_admin=False)


def test_get_is_platform_admin_light_mode_allows_system_user(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "light")
    tenant_service = MagicMock()

    assert auth_mod.get_is_platform_admin(user=_user(), tenant_service=tenant_service) is True
    # Light mode must not even consult tenant memberships.
    tenant_service.get_membership.assert_not_called()


def test_get_is_platform_admin_full_mode_rejects_non_admin(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = _membership(TenantRole.GROWER)

    assert auth_mod.get_is_platform_admin(user=_user(), tenant_service=tenant_service) is False


def test_get_is_platform_admin_full_mode_allows_platform_admin(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = _membership(TenantRole.LEAD)

    assert auth_mod.get_is_platform_admin(user=_user(), tenant_service=tenant_service) is True
    tenant_service.get_membership.assert_called_once_with("system-user", "platform")


def test_the_gate_really_depends_on_the_shared_lookup(monkeypatch):
    """The composition, so the split above cannot become two unrelated halves.

    Asserted on the dependency FastAPI resolves rather than on a call: the two
    functions are wired by a default argument, and a refactor that reintroduced a
    second lookup would leave both halves above green while restoring the very
    double roundtrip SCR-006 removed.
    """
    import inspect

    from fastapi.params import Depends as DependsParam

    parameter = inspect.signature(auth_mod.require_platform_admin).parameters["platform_admin"]

    assert isinstance(parameter.default, DependsParam)
    assert parameter.default.dependency is auth_mod.get_is_platform_admin


# -- is_platform_admin (the lookup behind the /users/me flag) ---------------
#
# Since #1851 ``GET /users/me`` takes the flag from ``get_is_platform_admin`` (so a
# tenant-scoped API key never advertises a platform role); the lookup underneath
# is still ``auth.is_platform_admin``, asserted here.


def test_is_platform_admin_true_in_light_mode(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "light")
    tenant_service = MagicMock()

    assert auth_mod.is_platform_admin(tenant_service, "system-user") is True
    tenant_service.get_membership.assert_not_called()


def test_is_platform_admin_full_mode_follows_membership(monkeypatch):
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = _membership(TenantRole.LEAD)
    assert auth_mod.is_platform_admin(tenant_service, "u1") is True

    tenant_service.get_membership.return_value = _membership(TenantRole.VIEWER)
    assert auth_mod.is_platform_admin(tenant_service, "u1") is False

    tenant_service.get_membership.return_value = None
    assert auth_mod.is_platform_admin(tenant_service, "u1") is False


def test_the_users_me_flag_resolves_through_the_scope_aware_dependency():
    import inspect

    from fastapi.params import Depends as DependsParam

    parameter = inspect.signature(users_mod.get_profile).parameters["platform_admin"]

    assert isinstance(parameter.default, DependsParam)
    assert parameter.default.dependency is auth_mod.get_is_platform_admin
