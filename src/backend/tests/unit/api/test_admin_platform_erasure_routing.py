"""Unit tests for SEC-002 / SEC-003 — admin platform delete endpoints route
through the NFR-013 / REQ-025 pipelines, entirely via the service layer (#1019).

The endpoint functions are exercised directly (the ``Depends`` defaults are not
evaluated on a direct call), with the injected services mocked. After #1019 the
router holds no ``get_db``; since #1769 the tenant existence / ``is_platform``
guard lives in ``TenantService.delete_tenant`` itself. Since #1664 the user delete makes exactly
one erasure call — since #1767 ``PrivacyService.erase_account_now``, which
persists the request and runs ``erase_account``, the shared entry that runs
the SEC-003 storage phases *and* the declared ArangoDB plan in the right order
(pinned in ``tests/unit/domain/services/test_privacy_erase_account.py``).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from app.api.v1.admin.platform import router as mod
from app.api.v1.privacy.schemas import ErasureCreateRequest
from app.api.v1.tenants.schemas import TenantDeleteRequest
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.models.privacy import ErasureRequest
from app.domain.models.tenant_erasure import TenantErasureRecord

_BODY = TenantDeleteRequest(confirm_slug="garden", password="pw")


_ACCEPTED = TenantErasureRecord(tenant_key="t-2", tenant_type="organization", origin="tenant_management")


class TestDeleteTenantRouting:
    """SEC-002 / #1769 — both tenant-delete routes run the one service entry, nothing beside it.

    The platform-tenant refusal and the 404 live in ``TenantService.delete_tenant``
    (``test_tenant_erasure_service.py``), so the tenant-scoped route is guarded the
    same way — it had no platform check of its own before #1769.
    """

    def test_admin_route_runs_the_service_deletion_as_platform_admin(self):
        tenant_service = MagicMock()
        tenant_service.delete_tenant.return_value = _ACCEPTED
        admin = SimpleNamespace(key="admin-1")

        response = mod.delete_tenant(
            "t-1", body=_BODY, user=admin, via_api_key=False, client_ip="203.0.113.1", tenant_service=tenant_service
        )

        assert response.status == "in_progress"  # 202 body, #1792
        # The requester and the step-up reach the service, which decides (#1791).
        assert tenant_service.mock_calls == [
            call.delete_tenant(
                "t-1",
                requester=admin,
                authenticated_with_api_key=False,
                confirmation=_BODY.to_confirmation(),
                origin="platform_admin",
                client_ip="203.0.113.1",
            )
        ]

    def test_tenant_route_runs_the_service_deletion_as_tenant_management(self):
        from app.api.v1.tenants import router as tenant_router

        service = MagicMock()
        service.delete_tenant.return_value = _ACCEPTED
        member = SimpleNamespace(key="member-1")

        response = tenant_router.delete_tenant(
            body=_BODY,
            ctx=SimpleNamespace(tenant_key="t-2"),
            user=member,
            via_api_key=False,
            client_ip="203.0.113.2",
            service=service,
        )

        assert response.tenant_key == "t-2"
        assert service.mock_calls == [
            call.delete_tenant(
                "t-2",
                requester=member,
                authenticated_with_api_key=False,
                confirmation=_BODY.to_confirmation(),
                origin="tenant_management",
                client_ip="203.0.113.2",
            )
        ]

    def test_a_service_refusal_reaches_the_caller(self):
        tenant_service = MagicMock()
        tenant_service.delete_tenant.side_effect = ForbiddenError("The platform tenant cannot be deleted.")

        with pytest.raises(ForbiddenError):
            mod.delete_tenant(
                "t-0",
                body=_BODY,
                user=SimpleNamespace(key="admin-1"),
                via_api_key=False,
                client_ip=None,
                tenant_service=tenant_service,
            )


class TestDeleteUserRouting:
    """#1664 / #1814 / #1949 — admin user delete runs the one step-up-guarded request entry, nothing beside it.

    Asynchronous since #1949: the route accepts (``202``) and the service dispatches
    the erasure to a worker. The step-up, the self-deletion refusal and the
    membership re-check live in ``PrivacyService.request_account_erasure_by_admin``
    and are driven through the real route in ``test_step_up_irreversible_account_actions.py``.
    """

    _STEP_UP = ErasureCreateRequest(confirm_email="u-1@example.org", password="pw")

    def test_routes_user_delete_through_the_step_up_guarded_entry(self):
        privacy_service = MagicMock()
        privacy_service.request_account_erasure_by_admin.return_value = ErasureRequest(
            key="er-1", user_key="u-1", status="scheduled"
        )
        current = SimpleNamespace(key="admin-9")

        response = mod.delete_user(
            "u-1",
            body=self._STEP_UP,
            current_user=current,
            via_api_key=False,
            client_ip="203.0.113.1",
            privacy_service=privacy_service,
        )

        # The 202 body names the request, never the account (#1949).
        assert (response.erasure_key, response.status) == ("er-1", "scheduled")
        assert "u-1" not in response.model_dump_json()
        assert privacy_service.method_calls == [
            call.request_account_erasure_by_admin(
                "u-1",
                requester=current,
                confirmation=self._STEP_UP.to_confirmation(),
                authenticated_with_api_key=False,
                client_ip="203.0.113.1",
            )
        ]

    def test_the_route_no_longer_reaches_a_separate_cascade(self):
        """The service methods the routes used to call beside the Art. 17 pipeline are gone."""
        from app.domain.services.user_service import UserService

        assert not hasattr(UserService, "delete_account_permanently")
        # #1813 — the tombstone-only soft delete of DELETE /users/me.
        assert not hasattr(UserService, "delete_account")

    def test_a_service_refusal_reaches_the_caller(self):
        privacy_service = MagicMock()
        privacy_service.request_account_erasure_by_admin.side_effect = ForbiddenError(
            "You cannot delete your own account from the admin panel."
        )

        with pytest.raises(ForbiddenError):
            mod.delete_user(
                "admin-9",
                body=self._STEP_UP,
                current_user=SimpleNamespace(key="admin-9"),
                via_api_key=False,
                client_ip=None,
                privacy_service=privacy_service,
            )

    def test_missing_user_raises_not_found(self):
        privacy_service = MagicMock()
        privacy_service.request_account_erasure_by_admin.side_effect = NotFoundError("User", "ghost")

        with pytest.raises(NotFoundError):
            mod.delete_user(
                "ghost",
                body=self._STEP_UP,
                current_user=SimpleNamespace(key="admin-9"),
                via_api_key=False,
                client_ip=None,
                privacy_service=privacy_service,
            )
