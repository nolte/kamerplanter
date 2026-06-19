"""NFR-013 §6.1 / REQ-025 — tenant deletion purges object storage + ref index.

Covers AC-03: tenant deletion runs ``delete_prefix("t/{tenant_key}/")`` and the
reference-index tenant cleanup, and deletes the attachment metadata first.
"""

from unittest.mock import AsyncMock, MagicMock

from app.domain.services.tenant_service import TenantService


def _make_service(*, storage_adapter, attachment_repo, reference_index_store, tenant_repo=None):
    tenant_repo = tenant_repo or MagicMock()
    tenant_repo.delete.return_value = True
    return TenantService(
        tenant_repo=tenant_repo,
        membership_repo=MagicMock(),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=MagicMock(),
        membership_engine=MagicMock(),
        invitation_engine=MagicMock(),
        storage_adapter=storage_adapter,
        attachment_repo=attachment_repo,
        reference_index_store=reference_index_store,
    )


class TestTenantDeleteStorage:
    def test_delete_tenant_purges_storage_prefix(self):
        storage = MagicMock()
        storage.delete_prefix = AsyncMock(return_value=7)
        attachment_repo = MagicMock()
        attachment_repo.delete_all_for_tenant.return_value = 7
        ref_store = MagicMock()
        ref_store.delete_tenant_contributions = AsyncMock(return_value=2)

        svc = _make_service(
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            reference_index_store=ref_store,
        )

        assert svc.delete_tenant("tenant-123") is True

        # Metadata deleted, then the binary prefix, then the reference index.
        attachment_repo.delete_all_for_tenant.assert_called_once_with("tenant-123")
        storage.delete_prefix.assert_awaited_once_with("t/tenant-123/")
        ref_store.delete_tenant_contributions.assert_awaited_once_with("tenant-123")

    def test_delete_tenant_works_without_storage_wired(self):
        # Backwards compatibility: a TenantService built without the storage
        # dependencies must still delete the tenant (no crash).
        svc = _make_service(
            storage_adapter=None,
            attachment_repo=None,
            reference_index_store=None,
        )
        assert svc.delete_tenant("tenant-xyz") is True

    def test_noop_reference_index_store_completes(self):
        from app.data_access.vectordb.noop_reference_index_store import (
            NoopReferenceIndexStore,
        )

        storage = MagicMock()
        storage.delete_prefix = AsyncMock(return_value=0)
        attachment_repo = MagicMock()
        attachment_repo.delete_all_for_tenant.return_value = 0

        svc = _make_service(
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            reference_index_store=NoopReferenceIndexStore(),
        )
        assert svc.delete_tenant("tenant-noop") is True
        storage.delete_prefix.assert_awaited_once_with("t/tenant-noop/")
