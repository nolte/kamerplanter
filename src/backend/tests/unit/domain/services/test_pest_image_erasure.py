"""REQ-010 / REQ-025 — DSGVO erasure wiring for user-contributed pest images.

Covers both deletion entry points:

* ``TenantService._purge_tenant_storage`` drops the tenant's
  ``pest_image_contributions`` link documents on tenant deletion.
* ``PrivacyService.run_user_storage_erasure`` hard-deletes the user's
  contribution documents (the attachment bytes go via the
  ``user_pest_reference_images`` storage-cleanup rule) on user erasure.

Also asserts the ErasureEngine declares the pest-image storage rule + the
ArangoDB DELETE_ORDER entry so the wiring stays in lock-step with the plan.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.pest_image import PestImageContribution
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.tenant_service import TenantService


class TestErasureEnginePlan:
    def test_pest_reference_storage_rule_is_hard_delete(self):
        engine = ErasureEngine()
        rule = next(
            (r for r in engine.STORAGE_CLEANUP_RULES if r.scope == "user_pest_reference_images"),
            None,
        )
        assert rule is not None
        assert rule.action == "hard_delete"

    def test_pest_image_collection_in_delete_order(self):
        assert "pest_image_contributions" in ErasureEngine().DELETE_ORDER


def _tenant_service(pest_image_repo=None):
    return TenantService(
        tenant_repo=MagicMock(),
        membership_repo=MagicMock(),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=MagicMock(),
        membership_engine=MagicMock(),
        invitation_engine=MagicMock(),
        pest_image_repo=pest_image_repo,
    )


class TestTenantPurgeDropsPestImages:
    def test_purge_calls_delete_for_tenant(self):
        pest_repo = MagicMock()
        pest_repo.delete_for_tenant.return_value = 3
        svc = _tenant_service(pest_image_repo=pest_repo)

        svc._purge_tenant_storage("t-abc")

        pest_repo.delete_for_tenant.assert_called_once_with("t-abc")

    def test_delete_tenant_routes_through_purge(self):
        pest_repo = MagicMock()
        pest_repo.delete_for_tenant.return_value = 1
        svc = _tenant_service(pest_image_repo=pest_repo)
        svc._tenant_repo.delete.return_value = True

        assert svc.delete_tenant("t-abc") is True
        pest_repo.delete_for_tenant.assert_called_once_with("t-abc")


def _privacy_service(pest_image_repo=None):
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=ErasureEngine(),
        consent_engine=MagicMock(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        pest_image_repo=pest_image_repo,
    )


def _contribution(key: str, tenant_key: str, user_key: str) -> PestImageContribution:
    return PestImageContribution(
        _key=key,
        tenant_key=tenant_key,
        pest_key="p1",
        attachment_id=f"att-{key}",
        contributed_by=user_key,
    )


class TestUserErasureDropsPestImageDocuments:
    @pytest.mark.asyncio
    async def test_run_user_storage_erasure_deletes_user_contributions(self):
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [
            _contribution("pic1", "t1", "u1"),
            _contribution("pic2", "t2", "u1"),
        ]
        pest_repo.delete.return_value = True
        svc = _privacy_service(pest_image_repo=pest_repo)
        # No storage adapter / membership repo wired → storage cleanup is a no-op,
        # but the pest-image document cleanup still runs.

        await svc.run_user_storage_erasure("u1")

        pest_repo.list_for_user.assert_called_once_with("u1")
        # Each contribution deleted against its OWN tenant key.
        pest_repo.delete.assert_any_call("pic1", "t1")
        pest_repo.delete.assert_any_call("pic2", "t2")

    @pytest.mark.asyncio
    async def test_no_op_when_repo_unwired(self):
        svc = _privacy_service(pest_image_repo=None)
        # Must not raise.
        assert await svc.run_user_storage_erasure("u1") == []
