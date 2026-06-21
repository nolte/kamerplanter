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

from app.common.enums import PestImageStatus
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.ipm import Pest
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


def _tenant_service(pest_image_repo=None, ipm_repo=None, pest_inference_client=None):
    return TenantService(
        tenant_repo=MagicMock(),
        membership_repo=MagicMock(),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=MagicMock(),
        membership_engine=MagicMock(),
        invitation_engine=MagicMock(),
        pest_image_repo=pest_image_repo,
        ipm_repo=ipm_repo,
        pest_inference_client=pest_inference_client,
    )


def _ipm_repo_with_pest(detection_slug: str | None) -> MagicMock:
    """An IPM repo whose pest resolves to ``detection_slug`` (recognition label)."""
    repo = MagicMock()
    repo.get_pest_by_key.return_value = Pest(
        _key="p1",
        scientific_name="Tetranychus urticae",
        common_name="Two-spotted spider mite",
        detection_slug=detection_slug,
    )
    return repo


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


def _privacy_service(pest_image_repo=None, ipm_repo=None, pest_inference_client=None):
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
        ipm_repo=ipm_repo,
        pest_inference_client=pest_inference_client,
    )


def _contribution(
    key: str,
    tenant_key: str,
    user_key: str,
    *,
    status: PestImageStatus = PestImageStatus.PRIVATE,
) -> PestImageContribution:
    return PestImageContribution(
        _key=key,
        tenant_key=tenant_key,
        pest_key="p1",
        attachment_id=f"att-{key}",
        contributed_by=user_key,
        status=status,
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


# ── SEC-001: promoted-embedding retract on erasure ─────────────────────────


class TestUserErasureRetractsPromotedEmbeddings:
    @pytest.mark.asyncio
    async def test_promoted_contribution_is_retracted_from_index(self):
        promoted = _contribution("pic1", "t1", "u1", status=PestImageStatus.PROMOTED)
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [promoted]
        pest_repo.delete.return_value = True
        inference = MagicMock()
        inference.retract_prototype.return_value = 1

        svc = _privacy_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest("spider_mite"),
            pest_inference_client=inference,
        )

        await svc.run_user_storage_erasure("u1")

        inference.retract_prototype.assert_called_once_with(
            label="spider_mite",
            source="user_contributed",
            source_record_id="pic1",
        )

    @pytest.mark.asyncio
    async def test_retract_runs_before_document_delete(self):
        """The label must be resolvable, so retract precedes the doc delete."""
        promoted = _contribution("pic1", "t1", "u1", status=PestImageStatus.PROMOTED)
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [promoted]
        pest_repo.delete.return_value = True
        inference = MagicMock()
        order: list[str] = []
        inference.retract_prototype.side_effect = lambda **_: order.append("retract") or 1
        pest_repo.delete.side_effect = lambda *_: order.append("delete") or True

        svc = _privacy_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest("spider_mite"),
            pest_inference_client=inference,
        )

        await svc.run_user_storage_erasure("u1")

        assert order == ["retract", "delete"]

    @pytest.mark.asyncio
    async def test_private_contribution_is_not_retracted(self):
        private = _contribution("pic1", "t1", "u1", status=PestImageStatus.PRIVATE)
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [private]
        pest_repo.delete.return_value = True
        inference = MagicMock()

        svc = _privacy_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest("spider_mite"),
            pest_inference_client=inference,
        )

        await svc.run_user_storage_erasure("u1")

        inference.retract_prototype.assert_not_called()
        # …but the document is still dropped.
        pest_repo.delete.assert_called_once_with("pic1", "t1")

    @pytest.mark.asyncio
    async def test_promoted_without_detection_slug_is_not_retracted(self):
        promoted = _contribution("pic1", "t1", "u1", status=PestImageStatus.PROMOTED)
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [promoted]
        pest_repo.delete.return_value = True
        inference = MagicMock()

        svc = _privacy_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest(None),  # pest has no detection_slug
            pest_inference_client=inference,
        )

        await svc.run_user_storage_erasure("u1")

        inference.retract_prototype.assert_not_called()
        pest_repo.delete.assert_called_once_with("pic1", "t1")

    @pytest.mark.asyncio
    async def test_inference_error_does_not_abort_erasure(self):
        promoted = _contribution("pic1", "t1", "u1", status=PestImageStatus.PROMOTED)
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [promoted]
        pest_repo.delete.return_value = True
        inference = MagicMock()
        inference.retract_prototype.side_effect = RuntimeError("service down")

        svc = _privacy_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest("spider_mite"),
            pest_inference_client=inference,
        )

        # Must still complete the document delete despite the retract failure.
        await svc.run_user_storage_erasure("u1")
        pest_repo.delete.assert_called_once_with("pic1", "t1")

    @pytest.mark.asyncio
    async def test_no_retract_when_inference_client_unwired(self):
        promoted = _contribution("pic1", "t1", "u1", status=PestImageStatus.PROMOTED)
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [promoted]
        pest_repo.delete.return_value = True

        svc = _privacy_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest("spider_mite"),
            pest_inference_client=None,
        )

        # Must not raise; documents still dropped.
        await svc.run_user_storage_erasure("u1")
        pest_repo.delete.assert_called_once_with("pic1", "t1")


class TestTenantPurgeRetractsPromotedEmbeddings:
    def test_promoted_contribution_is_retracted_from_index(self):
        pest_repo = MagicMock()
        pest_repo.list_for_tenant.return_value = [
            _contribution("pic1", "t-abc", "u1", status=PestImageStatus.PROMOTED),
            _contribution("pic2", "t-abc", "u2", status=PestImageStatus.PRIVATE),
        ]
        pest_repo.delete_for_tenant.return_value = 2
        inference = MagicMock()
        inference.retract_prototype.return_value = 1

        svc = _tenant_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest("spider_mite"),
            pest_inference_client=inference,
        )

        svc._purge_tenant_storage("t-abc")

        # Only the promoted contribution is retracted; the private one is skipped.
        inference.retract_prototype.assert_called_once_with(
            label="spider_mite",
            source="user_contributed",
            source_record_id="pic1",
        )
        pest_repo.delete_for_tenant.assert_called_once_with("t-abc")

    def test_retract_runs_before_delete_for_tenant(self):
        pest_repo = MagicMock()
        pest_repo.list_for_tenant.return_value = [
            _contribution("pic1", "t-abc", "u1", status=PestImageStatus.PROMOTED),
        ]
        order: list[str] = []
        inference = MagicMock()
        inference.retract_prototype.side_effect = lambda **_: order.append("retract") or 1
        pest_repo.delete_for_tenant.side_effect = lambda *_: order.append("delete") or 1

        svc = _tenant_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest("spider_mite"),
            pest_inference_client=inference,
        )

        svc._purge_tenant_storage("t-abc")

        assert order == ["retract", "delete"]

    def test_inference_error_does_not_abort_tenant_purge(self):
        pest_repo = MagicMock()
        pest_repo.list_for_tenant.return_value = [
            _contribution("pic1", "t-abc", "u1", status=PestImageStatus.PROMOTED),
        ]
        pest_repo.delete_for_tenant.return_value = 1
        inference = MagicMock()
        inference.retract_prototype.side_effect = RuntimeError("service down")

        svc = _tenant_service(
            pest_image_repo=pest_repo,
            ipm_repo=_ipm_repo_with_pest("spider_mite"),
            pest_inference_client=inference,
        )

        # Must still drop the documents despite the retract failure.
        svc._purge_tenant_storage("t-abc")
        pest_repo.delete_for_tenant.assert_called_once_with("t-abc")
