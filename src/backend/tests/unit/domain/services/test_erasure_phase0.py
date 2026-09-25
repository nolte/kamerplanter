"""REQ-025 §3.5 — erasure Phase 0 / 0.5 pipeline (W-007, SR-003).

Covers AK-OS-01 (hard-delete user_personal), AK-OS-02 (anonymise
user_diary_attachments + EXIF strip), AK-OS-04 (phase order + partial-failure
guard) and AK-OS-05 (reference-index cleanup), all exercised through
``PrivacyService.execute_scheduled_erasures``, which runs them inside
``erase_account`` ahead of the ArangoDB plan (#1645).
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import ErasureRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import RecordingErasureExecutor


def _membership(tenant_key: str):
    m = MagicMock()
    m.tenant_key = tenant_key
    return m


def _make_service(
    *, erasure, storage_adapter, attachment_repo, membership_repo, reference_index_store, erasure_executor=None
):
    erasure_repo = MagicMock()
    erasure_repo.list_due_for_hard_delete.return_value = [erasure]
    erasure_repo.update.side_effect = lambda key, e: e
    if isinstance(reference_index_store, MagicMock):
        # A bare mock would answer ``configuration_error()`` with a truthy mock
        # and hold every erasure (#1753); these doubles stand for a working store.
        reference_index_store.configuration_error.return_value = None
        reference_index_store.binding = "mock"
    return (
        PrivacyService(
            export_repo=MagicMock(),
            consent_repo=MagicMock(),
            restriction_repo=MagicMock(),
            erasure_repo=erasure_repo,
            email_change_repo=MagicMock(),
            user_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            data_export_engine=DataExportEngine(),
            erasure_engine=ErasureEngine(),
            consent_engine=ConsentEngine(),
            password_engine=MagicMock(),
            token_engine=MagicMock(),
            email_service=MagicMock(),
            frontend_url="https://app.test",
            storage_adapter=storage_adapter,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=reference_index_store,
            # #1645 — the scheduled path runs ``erase_account``, which needs the
            # ArangoDB executor and the NFR-011 salt.
            erasure_executor=erasure_executor or RecordingErasureExecutor(),
            tombstone_salt="s" * 32,
        ),
        erasure_repo,
    )


@pytest.mark.asyncio
class TestErasurePhase0:
    async def test_phase0_hard_delete_and_anonymise_are_called(self):
        """AK-OS-01 / AK-OS-02 — both storage scopes run per tenant."""
        erasure = ErasureRequest(key="er-1", user_key="u-1", status="scheduled")
        storage = MagicMock()
        storage.delete_for_user = AsyncMock(return_value=2)
        storage.strip_exif_for_user = AsyncMock(return_value=1)
        attachment_repo = MagicMock()
        attachment_repo.anonymize_user_metadata.return_value = 3
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [_membership("t-1")]
        ref_store = MagicMock()
        ref_store.delete_user_contributions = AsyncMock(return_value=0)

        svc, erasure_repo = _make_service(
            erasure=erasure,
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=ref_store,
        )

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        # #1645 - Phase 0 is followed by the ArangoDB plan, so the run finishes;
        # what this test pins is the Phase 0 *effect*, below.
        assert finalised == 1
        # Two hard-delete scopes run per tenant: personal attachments and
        # REQ-010 pest reference images (both have no retention obligation).
        hard_delete_scopes = {c.kwargs["scope"] for c in storage.delete_for_user.await_args_list}
        assert hard_delete_scopes == {"user_personal", "user_pest_reference_images"}
        for call in storage.delete_for_user.await_args_list:
            assert call.kwargs["tenant_key"] == "t-1"
            assert call.kwargs["user_key"] == "u-1"
        attachment_repo.anonymize_user_metadata.assert_called_once()
        storage.strip_exif_for_user.assert_awaited_once_with(
            tenant_key="t-1", user_key="u-1", scope="user_diary_attachments"
        )
        assert erasure.status == "completed"
        assert "user_personal" in erasure.storage_cleanup_scopes
        assert "user_diary_attachments" in erasure.storage_cleanup_scopes
        assert "user_pest_reference_images" in erasure.storage_cleanup_scopes

    async def test_phase05_reference_index_cleanup_called(self):
        """AK-OS-05 — user-contributed embeddings cleanup runs before delete."""
        erasure = ErasureRequest(key="er-2", user_key="u-2", status="scheduled")
        storage = MagicMock()
        storage.delete_for_user = AsyncMock(return_value=0)
        storage.strip_exif_for_user = AsyncMock(return_value=0)
        attachment_repo = MagicMock()
        attachment_repo.anonymize_user_metadata.return_value = 0
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [_membership("t-2")]
        ref_store = MagicMock()
        ref_store.delete_user_contributions = AsyncMock(return_value=5)

        svc, _ = _make_service(
            erasure=erasure,
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=ref_store,
        )

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        # The subject of this test is the Phase 0.5 call, not the terminal status.
        assert finalised == 1
        ref_store.delete_user_contributions.assert_awaited_once_with(tenant_key=None, user_key="u-2")

    async def test_phase05_noop_store_completes_cleanly(self):
        """AK-OS-05 — a no-op reference index (pgvector absent) still completes."""
        from app.data_access.vectordb.noop_reference_index_store import (
            NoopReferenceIndexStore,
        )

        erasure = ErasureRequest(key="er-3", user_key="u-3", status="scheduled")
        storage = MagicMock()
        storage.delete_for_user = AsyncMock(return_value=0)
        storage.strip_exif_for_user = AsyncMock(return_value=0)
        attachment_repo = MagicMock()
        attachment_repo.anonymize_user_metadata.return_value = 0
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [_membership("t-3")]

        svc, _ = _make_service(
            erasure=erasure,
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=NoopReferenceIndexStore(),
        )

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        # A no-op reference index must not *fail* the run.
        assert finalised == 1
        assert erasure.status == "completed"
        assert erasure.storage_cleanup_scopes
        assert erasure.error_message is None

    async def test_phase0_failure_marks_partially_completed_and_skips_delete(self):
        """AK-OS-04 — Phase 0 failure ⇒ partially_completed, no ArangoDB delete."""
        erasure = ErasureRequest(key="er-4", user_key="u-4", status="scheduled")
        storage = MagicMock()
        storage.delete_for_user = AsyncMock(side_effect=RuntimeError("S3 down"))
        storage.strip_exif_for_user = AsyncMock(return_value=0)
        attachment_repo = MagicMock()
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [_membership("t-4")]
        ref_store = MagicMock()
        ref_store.delete_user_contributions = AsyncMock(return_value=0)

        executor = RecordingErasureExecutor()
        svc, erasure_repo = _make_service(
            erasure=erasure,
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=ref_store,
            erasure_executor=executor,
        )

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert finalised == 0
        assert erasure.status == "partially_completed"
        assert "S3 down" in (erasure.error_message or "")
        # Phase 0.5 must NOT have run after a Phase 0 failure, nor the ArangoDB plan.
        ref_store.delete_user_contributions.assert_not_awaited()
        assert executor.runs == []

    async def test_partially_completed_is_repicked_on_next_run(self):
        """SEC-001 — a partially_completed erasure is retried on the next run.

        Run 1: Phase 0 fails ⇒ status flips to ``partially_completed``.
        Run 2: the same erasure key is selected again (the repository now
        reports retry states) and, with storage healthy, finalises.
        """
        erasure = ErasureRequest(key="er-retry", user_key="u-retry", status="scheduled")
        storage = MagicMock()
        # Run 1 aborts on the first hard-delete scope (1 call). Run 2 succeeds
        # across both hard-delete scopes (user_personal + pest reference images).
        storage.delete_for_user = AsyncMock(side_effect=[RuntimeError("S3 down"), 0, 0])
        storage.strip_exif_for_user = AsyncMock(return_value=0)
        attachment_repo = MagicMock()
        attachment_repo.anonymize_user_metadata.return_value = 0
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [_membership("t-retry")]
        ref_store = MagicMock()
        ref_store.delete_user_contributions = AsyncMock(return_value=0)

        svc, erasure_repo = _make_service(
            erasure=erasure,
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=ref_store,
        )
        # The repository keeps surfacing the same (mutated) erasure object until
        # it reaches a terminal state — mirroring the AQL retry-state filter.
        erasure_repo.list_due_for_hard_delete.side_effect = lambda *_: (
            [erasure] if erasure.status != "completed" else []
        )

        run1_at = datetime.now(UTC)
        finalised_run1 = await svc.execute_scheduled_erasures(run1_at)
        assert finalised_run1 == 0
        assert erasure.status == "partially_completed"
        assert "S3 down" in (erasure.error_message or "")

        # Run 2 is the *next daily* run: a first failure backs off one day
        # (#1666). Storage is healthy, so Phase 0 runs to the end and the
        # ArangoDB plan follows (#1645); the old reason is cleared.
        finalised_run2 = await svc.execute_scheduled_erasures(run1_at + timedelta(days=1))
        assert finalised_run2 == 1
        assert erasure.status == "completed"
        assert erasure.error_message is None
        assert erasure.storage_cleanup_scopes
        # Run 1 aborts on the first scope (1 call); run 2 completes both
        # hard-delete scopes (2 calls) ⇒ 3 total.
        assert storage.delete_for_user.await_count == 3

    async def test_phase05_failure_marks_partially_completed(self):
        """AK-OS-05 — Phase 0.5 failure ⇒ partially_completed (retryable)."""
        erasure = ErasureRequest(key="er-5", user_key="u-5", status="scheduled")
        storage = MagicMock()
        storage.delete_for_user = AsyncMock(return_value=0)
        storage.strip_exif_for_user = AsyncMock(return_value=0)
        attachment_repo = MagicMock()
        attachment_repo.anonymize_user_metadata.return_value = 0
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [_membership("t-5")]
        ref_store = MagicMock()
        ref_store.delete_user_contributions = AsyncMock(side_effect=RuntimeError("pgvector down"))

        executor = RecordingErasureExecutor()
        svc, _ = _make_service(
            erasure=erasure,
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=ref_store,
            erasure_executor=executor,
        )

        finalised = await svc.execute_scheduled_erasures(datetime.now(UTC))

        assert finalised == 0
        assert erasure.status == "partially_completed"
        assert executor.runs == []

    async def test_pre_arango_phases_run_both_phases(self):
        """SEC-003 — Phase 0 + Phase 0.5 for a user, as ``erase_account`` runs them.

        Both account-deletion paths reach these phases only through
        ``erase_account``, before the executor removes the user's memberships.
        """
        erasure = ErasureRequest(key="er-helper", user_key="u-helper", status="scheduled")
        storage = MagicMock()
        storage.delete_for_user = AsyncMock(return_value=1)
        storage.strip_exif_for_user = AsyncMock(return_value=1)
        attachment_repo = MagicMock()
        attachment_repo.anonymize_user_metadata.return_value = 1
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [_membership("t-x")]
        ref_store = MagicMock()
        ref_store.delete_user_contributions = AsyncMock(return_value=2)

        svc, _ = _make_service(
            erasure=erasure,
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=ref_store,
        )

        scopes, _, _ = await svc._run_pre_arango_phases("u-helper")

        hard_delete_scopes = {c.kwargs["scope"] for c in storage.delete_for_user.await_args_list}
        assert hard_delete_scopes == {"user_personal", "user_pest_reference_images"}
        storage.strip_exif_for_user.assert_awaited_once_with(
            tenant_key="t-x", user_key="u-helper", scope="user_diary_attachments"
        )
        ref_store.delete_user_contributions.assert_awaited_once_with(tenant_key=None, user_key="u-helper")
        assert "user_personal" in scopes
        assert "user_diary_attachments" in scopes
        assert "user_pest_reference_images" in scopes

    async def test_runs_per_tenant_for_multi_tenant_user(self):
        """A user in several tenants is cleaned up in each tenant's storage."""
        erasure = ErasureRequest(key="er-6", user_key="u-6", status="scheduled")
        storage = MagicMock()
        storage.delete_for_user = AsyncMock(return_value=0)
        storage.strip_exif_for_user = AsyncMock(return_value=0)
        attachment_repo = MagicMock()
        attachment_repo.anonymize_user_metadata.return_value = 0
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [_membership("t-a"), _membership("t-b")]
        ref_store = MagicMock()
        ref_store.delete_user_contributions = AsyncMock(return_value=0)

        svc, _ = _make_service(
            erasure=erasure,
            storage_adapter=storage,
            attachment_repo=attachment_repo,
            membership_repo=membership_repo,
            reference_index_store=ref_store,
        )

        await svc.execute_scheduled_erasures(datetime.now(UTC))

        tenants_deleted = {c.kwargs["tenant_key"] for c in storage.delete_for_user.await_args_list}
        assert tenants_deleted == {"t-a", "t-b"}
