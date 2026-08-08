"""Unit tests for SEC-002 / SEC-003 — admin platform delete endpoints route
through the NFR-013 / REQ-025 pipelines, entirely via the service layer (#1019).

The endpoint functions are exercised directly (the ``Depends`` defaults are not
evaluated on a direct call), with the injected services mocked. After #1019 the
router holds no ``get_db``: the tenant existence / ``is_platform`` guard reads
through ``TenantService.get_tenant`` and the user cascade runs inside
``UserService.delete_account_permanently``, after the SEC-003 storage erasure.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api.v1.admin.platform import router as mod
from app.common.exceptions import ForbiddenError, NotFoundError


class TestDeleteTenantRouting:
    """SEC-002 — admin tenant delete must go through TenantService.delete_tenant."""

    def test_routes_tenant_delete_through_service(self):
        tenant_service = MagicMock()
        tenant_service.get_tenant.return_value = SimpleNamespace(is_platform=False)

        mod.delete_tenant("t-1", _user=None, tenant_service=tenant_service)

        tenant_service.get_tenant.assert_called_once_with("t-1")
        tenant_service.delete_tenant.assert_called_once_with("t-1")

    def test_rejects_platform_tenant(self):
        tenant_service = MagicMock()
        tenant_service.get_tenant.return_value = SimpleNamespace(is_platform=True)

        with pytest.raises(ForbiddenError):
            mod.delete_tenant("t-0", _user=None, tenant_service=tenant_service)

        tenant_service.delete_tenant.assert_not_called()

    def test_missing_tenant_raises_not_found(self):
        tenant_service = MagicMock()
        tenant_service.get_tenant.side_effect = NotFoundError("tenants", "ghost")

        with pytest.raises(NotFoundError):
            mod.delete_tenant("ghost", _user=None, tenant_service=tenant_service)

        tenant_service.delete_tenant.assert_not_called()


class TestDeleteUserRouting:
    """SEC-003 — admin user delete must run Phase 0/0.5 before the ArangoDB cascade."""

    def test_runs_storage_erasure_before_account_delete(self):
        call_order: list[str] = []

        async def _erasure(user_key):
            call_order.append(f"erasure:{user_key}")
            return ["user_personal", "user_diary_attachments"]

        privacy_service = MagicMock()
        privacy_service.run_user_storage_erasure.side_effect = _erasure

        user_service = MagicMock()
        user_service.get_user.return_value = SimpleNamespace(key="u-1")
        user_service.delete_account_permanently.side_effect = lambda key: call_order.append(f"cascade:{key}")

        current = SimpleNamespace(key="admin-9")
        mod.delete_user("u-1", current_user=current, privacy_service=privacy_service, user_service=user_service)

        privacy_service.run_user_storage_erasure.assert_called_once_with("u-1")
        user_service.delete_account_permanently.assert_called_once_with("u-1")
        # Phase 0/0.5 (which resolves tenants via the memberships the cascade
        # removes) must precede the ArangoDB account cascade.
        assert call_order == ["erasure:u-1", "cascade:u-1"]

    def test_cannot_delete_self(self):
        privacy_service = MagicMock()
        user_service = MagicMock()
        user_service.get_user.return_value = SimpleNamespace(key="admin-9")

        current = SimpleNamespace(key="admin-9")
        with pytest.raises(ForbiddenError):
            mod.delete_user("admin-9", current_user=current, privacy_service=privacy_service, user_service=user_service)

        privacy_service.run_user_storage_erasure.assert_not_called()
        user_service.delete_account_permanently.assert_not_called()

    def test_missing_user_raises_not_found(self):
        privacy_service = MagicMock()
        user_service = MagicMock()
        user_service.get_user.side_effect = NotFoundError("User", "ghost")

        current = SimpleNamespace(key="admin-9")
        with pytest.raises(NotFoundError):
            mod.delete_user("ghost", current_user=current, privacy_service=privacy_service, user_service=user_service)

        privacy_service.run_user_storage_erasure.assert_not_called()
        user_service.delete_account_permanently.assert_not_called()
