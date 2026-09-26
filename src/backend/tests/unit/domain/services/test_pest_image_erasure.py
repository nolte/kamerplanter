"""REQ-010 / REQ-025 — DSGVO erasure wiring for user-contributed pest images.

Covers both deletion entry points:

* ``TenantService._purge_tenant_storage`` drops the tenant's
  ``pest_image_contributions`` link documents on tenant deletion.
* ``PrivacyService._run_pre_arango_phases`` — the phases ``erase_account``
  runs before the ArangoDB plan — hard-deletes the user's contribution
  documents (the attachment bytes go via the
  ``user_pest_reference_images`` storage-cleanup rule) on user erasure.

The recognition-prototype delete (#1759) is covered with a mock inference-service
in ``test_erasure_pest_prototypes.py``.

Also asserts the ErasureEngine declares the pest-image storage rule + the
ArangoDB DELETE_ORDER entry so the wiring stays in lock-step with the plan.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import PestImageStatus
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.pest_image import PestImageContribution
from app.domain.models.privacy import AccountErasureReport
from app.domain.services.privacy_service import PrivacyService
from tests.support.tenant_erasure_doubles import RecordingTenantErasureExecutor, authorized, tenant_service_for_deletion


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A deployment that can erase has a log salt (#1812): the erasure refuses to run without one."""
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


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
        assert "pest_image_contributions" in ErasureEngine.delete_order()


class TestTenantDeletionDropsPestImages:
    """REQ-010 — the tenant's pest-image link documents go with the tenant (#1769: via the inventory)."""

    def test_the_inventory_deletes_the_link_documents(self):
        (entry,) = [e for e in TenantErasureEngine.INVENTORY if e.collection == "pest_image_contributions"]
        assert entry.action == "delete"

    def test_delete_tenant_hands_the_executor_that_entry(self):
        executor = RecordingTenantErasureExecutor()
        svc = tenant_service_for_deletion(
            executor=executor, pest_image_repo=MagicMock(), pest_prototype_store=NoopPestPrototypeStore()
        )

        assert svc.delete_tenant("t-1", **authorized("t-1")).status == "completed"
        (plan,) = executor.plans
        assert "pest_image_contributions" in [e.collection for e in plan.entries if e.action == "delete"]


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
        reference_index_store=NoopReferenceIndexStore(),
        pest_image_repo=pest_image_repo,
        pest_prototype_store=NoopPestPrototypeStore(),
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
    async def test_pre_arango_phases_delete_user_contributions(self):
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [
            _contribution("pic1", "t1", "u1"),
            _contribution("pic2", "t2", "u1"),
        ]
        pest_repo.delete.return_value = True
        svc = _privacy_service(pest_image_repo=pest_repo)
        # No storage adapter / membership repo wired → storage cleanup is a no-op,
        # but the pest-image document cleanup still runs.

        report = AccountErasureReport()
        await svc._run_pre_arango_phases("u1", report)

        pest_repo.list_for_user.assert_called_once_with("u1")
        # Each contribution deleted against its OWN tenant key.
        pest_repo.delete.assert_any_call("pic1", "t1")
        pest_repo.delete.assert_any_call("pic2", "t2")

    @pytest.mark.asyncio
    async def test_no_op_when_repo_unwired(self):
        svc = _privacy_service(pest_image_repo=None)
        # Must not raise.
        report = AccountErasureReport()
        assert await svc._run_pre_arango_phases("u1", report) == 0
        assert report.pest_prototype_binding is None
