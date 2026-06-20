"""Unit tests for NFR-013 §6.1 / SEC-004 — tenant-storage purge on delete.

Covers that ``TenantService.delete_tenant`` routes through ``_purge_tenant_storage``
(object-storage prefix + reference-index cleanup) and that the purge refuses an
empty / malformed tenant key before building an over-broad delete prefix.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.domain.services.tenant_service import TenantService


def _make_service(*, storage_adapter=None, attachment_repo=None, reference_index_store=None):
    return TenantService(
        tenant_repo=MagicMock(),
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


class TestDeleteTenantPurge:
    def test_delete_tenant_purges_storage_prefix_and_ref_index(self):
        """SEC-002 (shared path) — delete_prefix runs for the tenant prefix."""
        storage = MagicMock()
        storage.delete_prefix = AsyncMock(return_value=4)
        ref_store = MagicMock()
        ref_store.delete_tenant_contributions = AsyncMock(return_value=2)
        attachment_repo = MagicMock()
        attachment_repo.delete_all_for_tenant.return_value = 3

        svc = _make_service(
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            reference_index_store=ref_store,
        )
        svc._tenant_repo.delete.return_value = True

        assert svc.delete_tenant("t-abc") is True

        storage.delete_prefix.assert_awaited_once_with("t/t-abc/")
        ref_store.delete_tenant_contributions.assert_awaited_once_with("t-abc")
        attachment_repo.delete_all_for_tenant.assert_called_once_with("t-abc")
        svc._membership_repo.delete_all_for_tenant.assert_called_once_with("t-abc")
        svc._tenant_repo.delete.assert_called_once_with("t-abc")

    def test_purge_runs_before_record_delete(self):
        """Storage purge precedes the tenant-record delete (retry-safe)."""
        order: list[str] = []
        storage = MagicMock()

        async def _del_prefix(prefix):
            order.append("storage")
            return 0

        storage.delete_prefix = AsyncMock(side_effect=_del_prefix)
        svc = _make_service(storage_adapter=storage)
        svc._tenant_repo.delete.side_effect = lambda key: order.append("record") or True

        svc.delete_tenant("t-xyz")

        assert order == ["storage", "record"]


class TestPurgeKeyHardening:
    """SEC-004 — refuse to purge with an empty / malformed tenant key."""

    @pytest.mark.parametrize("bad_key", ["", "   ", "t/x", "../etc", "a b", "a/b"])
    def test_invalid_tenant_key_rejected(self, bad_key):
        storage = MagicMock()
        storage.delete_prefix = AsyncMock(return_value=0)
        svc = _make_service(storage_adapter=storage)

        with pytest.raises(ValidationError):
            svc._purge_tenant_storage(bad_key)

        storage.delete_prefix.assert_not_awaited()

    def test_valid_tenant_key_accepted(self):
        storage = MagicMock()
        storage.delete_prefix = AsyncMock(return_value=0)
        svc = _make_service(storage_adapter=storage)

        svc._purge_tenant_storage("12345")

        storage.delete_prefix.assert_awaited_once_with("t/12345/")
