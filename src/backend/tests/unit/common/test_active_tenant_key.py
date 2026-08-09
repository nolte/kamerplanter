"""get_active_tenant_key — tenant resolution for global-but-tenant-aware routes (F-5, #808).

The species and botanical-family catalogues are mounted globally
(``/api/v1/species``), so :func:`get_current_tenant` — bound to the ``/t/{slug}/``
path — cannot run there. :func:`get_active_tenant_key` is the F-5 mechanism that
answers "which tenant is this caller acting in?" on such a route. It resolves the
caller's personal tenant and falls back to the global catalogue (``""``) rather
than erroring, so an anonymous / light-mode / tenant-less caller sees only the
global seeds — never a foreign tenant, never a 4xx.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common import auth as auth_mod


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="user_1")


def test_resolves_the_callers_personal_tenant():
    tenant_service = MagicMock()
    tenant_service.get_personal_tenant.return_value = SimpleNamespace(key="tenant_personal_1")

    result = auth_mod.get_active_tenant_key(user=_user(), tenant_service=tenant_service)

    assert result == "tenant_personal_1"
    tenant_service.get_personal_tenant.assert_called_once_with("user_1")


def test_falls_back_to_global_when_no_personal_tenant():
    # No resolvable tenant → "" (global-only via the hybrid union), never an error.
    tenant_service = MagicMock()
    tenant_service.get_personal_tenant.return_value = None

    assert auth_mod.get_active_tenant_key(user=_user(), tenant_service=tenant_service) == ""


def test_falls_back_to_global_for_a_keyless_user():
    tenant_service = MagicMock()
    tenant_service.get_personal_tenant.return_value = None

    result = auth_mod.get_active_tenant_key(user=SimpleNamespace(key=None), tenant_service=tenant_service)

    assert result == ""
    # A keyless (anonymous) caller is resolved against "", never crashing on None.
    tenant_service.get_personal_tenant.assert_called_once_with("")


def test_creating_tenant_key_is_the_same_resolver():
    # F-3 write stamping and F-5 read scoping deliberately share ONE resolver, so
    # they can never drift onto different notions of "the caller's tenant" and a
    # test overriding either dependency reaches the same function (test_origin_
    # provenance overrides get_creating_tenant_key and thereby the read path too).
    assert auth_mod.get_creating_tenant_key is auth_mod.get_active_tenant_key
