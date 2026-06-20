"""Unit tests for SEC-002 / SEC-003 — admin platform delete endpoints route
through the NFR-013 / REQ-025 purge pipelines.

The endpoint functions are exercised directly (the ``Depends`` defaults are not
evaluated on a direct call), with ``get_db`` and the injected services mocked.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api.v1.admin.platform import router as mod
from app.common.exceptions import ForbiddenError, NotFoundError


class TestDeleteTenantRouting:
    """SEC-002 — admin tenant delete must go through TenantService.delete_tenant."""

    def test_routes_tenant_delete_through_service(self, monkeypatch):
        db = MagicMock()
        db.collection.return_value.get.return_value = {"_key": "t-1", "is_platform": False}
        monkeypatch.setattr(mod, "get_db", lambda: db)

        tenant_service = MagicMock()

        mod.delete_tenant("t-1", _user=None, tenant_service=tenant_service)

        tenant_service.delete_tenant.assert_called_once_with("t-1")

    def test_rejects_platform_tenant(self, monkeypatch):
        db = MagicMock()
        db.collection.return_value.get.return_value = {"_key": "t-0", "is_platform": True}
        monkeypatch.setattr(mod, "get_db", lambda: db)
        tenant_service = MagicMock()

        with pytest.raises(ForbiddenError):
            mod.delete_tenant("t-0", _user=None, tenant_service=tenant_service)

        tenant_service.delete_tenant.assert_not_called()

    def test_missing_tenant_raises_not_found(self, monkeypatch):
        db = MagicMock()
        db.collection.return_value.get.return_value = None
        monkeypatch.setattr(mod, "get_db", lambda: db)
        tenant_service = MagicMock()

        with pytest.raises(NotFoundError):
            mod.delete_tenant("ghost", _user=None, tenant_service=tenant_service)

        tenant_service.delete_tenant.assert_not_called()


class TestDeleteUserRouting:
    """SEC-003 — admin user delete must run Phase 0/0.5 before membership removal."""

    def test_runs_storage_erasure_before_membership_delete(self, monkeypatch):
        db = MagicMock()
        db.collection.return_value.get.return_value = {"_key": "u-1"}
        monkeypatch.setattr(mod, "get_db", lambda: db)

        call_order: list[str] = []

        async def _erasure(user_key):
            call_order.append(f"erasure:{user_key}")
            return ["user_personal", "user_diary_attachments"]

        privacy_service = MagicMock()
        privacy_service.run_user_storage_erasure.side_effect = _erasure

        # Record when the first AQL (membership removal) runs.
        def _aql(*args, **kwargs):
            call_order.append("aql")
            return iter([])

        db.aql.execute.side_effect = _aql

        current = SimpleNamespace(key="admin-9")
        mod.delete_user("u-1", current_user=current, privacy_service=privacy_service)

        privacy_service.run_user_storage_erasure.assert_called_once_with("u-1")
        # Phase 0/0.5 must precede the first membership-removal AQL.
        assert call_order[0] == "erasure:u-1"
        assert "aql" in call_order
        assert call_order.index("erasure:u-1") < call_order.index("aql")
        db.collection.return_value.delete.assert_called_once_with("u-1")

    def test_cannot_delete_self(self, monkeypatch):
        db = MagicMock()
        db.collection.return_value.get.return_value = {"_key": "admin-9"}
        monkeypatch.setattr(mod, "get_db", lambda: db)
        privacy_service = MagicMock()

        current = SimpleNamespace(key="admin-9")
        with pytest.raises(ForbiddenError):
            mod.delete_user("admin-9", current_user=current, privacy_service=privacy_service)

        privacy_service.run_user_storage_erasure.assert_not_called()

    def test_missing_user_raises_not_found(self, monkeypatch):
        db = MagicMock()
        db.collection.return_value.get.return_value = None
        monkeypatch.setattr(mod, "get_db", lambda: db)
        privacy_service = MagicMock()

        current = SimpleNamespace(key="admin-9")
        with pytest.raises(NotFoundError):
            mod.delete_user("ghost", current_user=current, privacy_service=privacy_service)

        privacy_service.run_user_storage_erasure.assert_not_called()
