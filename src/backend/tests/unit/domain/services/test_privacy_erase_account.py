"""#1664 — ``PrivacyService.erase_account``: the one entry both deletion paths share.

What is pinned here is the *sequence* and the refusals. The rows themselves are
read back in ``tests/integration/test_account_erasure_reach.py``.

* Nothing runs when the tombstone salt is missing — a half-run erasure is worse
  than none, and a short salt would make the ``anon_…`` hash brute-forceable.
* Stored Art. 15 bundles are deleted before the executor removes the
  ``data_export_requests`` rows that point at them.
* The storage phases (which resolve tenants through memberships) run before the
  executor (which removes the memberships).
* The pest-image cleanup's count is attributed to the step declared for it.
* Pest images in a tenant the user has left are still reached (#1664 gap).
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import FeatureNotConfiguredError
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.membership import Membership
from app.domain.models.pest_image import PestImageContribution
from app.domain.models.privacy import (
    AccountErasureReport,
    DataExportRequest,
    ErasureExecutionReport,
    ErasureStepOutcome,
)
from app.domain.services.privacy_service import PrivacyService

USER_KEY = "u-1"
SALT = "x" * 32


def _service(**overrides) -> PrivacyService:
    deps = {
        # #1753 — every erasure path needs a wired reference-index store.
        "reference_index_store": NoopReferenceIndexStore(),
        # #1759 — and a pest-prototype store wherever pest images are wired.
        "pest_prototype_store": NoopPestPrototypeStore(),
        "export_repo": MagicMock(),
        "consent_repo": MagicMock(),
        "restriction_repo": MagicMock(),
        "erasure_repo": MagicMock(),
        "email_change_repo": MagicMock(),
        "user_repo": MagicMock(),
        "refresh_token_repo": MagicMock(),
        "data_export_engine": DataExportEngine(),
        "erasure_engine": ErasureEngine(),
        "consent_engine": ConsentEngine(),
        "password_engine": MagicMock(),
        "token_engine": MagicMock(),
        "email_service": MagicMock(),
        "frontend_url": "https://app.test",
        "erasure_executor": MagicMock(),
        "tombstone_salt": SALT,
    }
    deps.update(overrides)
    return PrivacyService(**deps)


def _executor(calls: list[str]) -> MagicMock:
    executor = MagicMock()

    def _execute(plan, *, tombstone):
        calls.append("executor")
        return ErasureExecutionReport(
            steps=[ErasureStepOutcome(collection="users", kind="user", executor="account_cascade", affected=1)]
        )

    executor.run_erasure_plan.side_effect = _execute
    return executor


def _storage(calls: list[str]) -> MagicMock:
    storage = MagicMock()

    async def _delete_object(key):
        calls.append(f"delete_object:{key}")

    async def _delete_for_user(tenant_key, user_key, scope):
        calls.append(f"delete_for_user:{tenant_key}:{scope}")
        return 0

    async def _strip(tenant_key, user_key, scope):
        return 0

    storage.delete_object.side_effect = _delete_object
    storage.delete_for_user.side_effect = _delete_for_user
    storage.strip_exif_for_user.side_effect = _strip
    return storage


def _contribution(tenant_key: str) -> PestImageContribution:
    return PestImageContribution(
        _key=f"c-{tenant_key}",
        tenant_key=tenant_key,
        pest_key="p-1",
        attachment_id="att-1",
        contributed_by=USER_KEY,
    )


@pytest.mark.asyncio
class TestRefusals:
    @pytest.mark.parametrize("salt", ["", "too-short"])
    async def test_a_missing_or_short_salt_refuses_before_anything_runs(self, salt):
        calls: list[str] = []
        storage = _storage(calls)
        executor = _executor(calls)
        export_repo = MagicMock()
        service = _service(
            tombstone_salt=salt,
            erasure_executor=executor,
            storage_adapter=storage,
            export_repo=export_repo,
            membership_repo=MagicMock(),
        )

        with pytest.raises(FeatureNotConfiguredError) as info:
            await service.erase_account(USER_KEY)

        assert info.value.status_code == 503
        assert calls == []
        executor.run_erasure_plan.assert_not_called()
        export_repo.list_by_user.assert_not_called()

    @pytest.mark.parametrize("user_key", ["", "   "])
    async def test_an_empty_user_key_refuses_before_anything_runs(self, user_key):
        """#1664 — ``""`` would match every unattributed row in the executor's filters."""
        calls: list[str] = []
        storage = _storage(calls)
        executor = _executor(calls)
        export_repo = MagicMock()
        membership_repo = MagicMock()
        service = _service(
            erasure_executor=executor,
            storage_adapter=storage,
            export_repo=export_repo,
            membership_repo=membership_repo,
        )

        with pytest.raises(ValueError, match="user key"):
            await service.erase_account(user_key)

        assert calls == []
        executor.run_erasure_plan.assert_not_called()
        export_repo.list_by_user.assert_not_called()
        membership_repo.list_by_user.assert_not_called()


@pytest.mark.asyncio
class TestSequence:
    async def test_export_bundles_and_storage_run_before_the_executor(self):
        calls: list[str] = []
        export_repo = MagicMock()
        export_repo.list_by_user.return_value = [
            DataExportRequest(
                key="e-1",
                user_key=USER_KEY,
                status="completed",
                requested_at=datetime.now(UTC),
                file_path="exports/e-1.zip",
            ),
            DataExportRequest(key="e-2", user_key=USER_KEY, status="expired", requested_at=datetime.now(UTC)),
        ]
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [Membership(user_key=USER_KEY, tenant_key="t-1", role="grower")]
        service = _service(
            export_repo=export_repo,
            storage_adapter=_storage(calls),
            membership_repo=membership_repo,
            erasure_executor=_executor(calls),
        )

        report = await service.erase_account(USER_KEY)

        assert calls[0] == "delete_object:exports/e-1.zip"
        assert calls[-1] == "executor"
        assert any(c.startswith("delete_for_user:t-1:") for c in calls[:-1])
        assert report.export_files_removed == 1
        assert report.affected("users") == 1

    async def test_the_executor_receives_the_declared_plan_and_the_subjects_hash(self):
        executor = _executor([])
        service = _service(erasure_executor=executor)

        await service.erase_account(USER_KEY)

        (plan,), kwargs = executor.run_erasure_plan.call_args
        assert plan.user_key == USER_KEY
        assert plan.steps == ErasureEngine.DELETE_STEPS
        assert kwargs == {"tombstone": ErasureEngine.compute_tombstone_hash(USER_KEY, SALT)}

    async def test_a_failed_bundle_delete_stops_before_the_pointer_is_lost(self):
        calls: list[str] = []
        storage = _storage(calls)
        storage.delete_object.side_effect = OSError("storage down")
        export_repo = MagicMock()
        export_repo.list_by_user.return_value = [
            DataExportRequest(
                key="e-1",
                user_key=USER_KEY,
                status="completed",
                requested_at=datetime.now(UTC),
                file_path="exports/e-1.zip",
            )
        ]
        executor = _executor(calls)
        service = _service(export_repo=export_repo, storage_adapter=storage, erasure_executor=executor)

        with pytest.raises(OSError):
            await service.erase_account(USER_KEY)

        executor.run_erasure_plan.assert_not_called()


@pytest.mark.asyncio
class TestPestImages:
    async def test_the_pest_cleanup_count_is_attributed_to_its_declared_step(self):
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [_contribution("t-1"), _contribution("t-2")]
        pest_repo.delete.return_value = True
        service = _service(pest_image_repo=pest_repo, erasure_executor=_executor([]))

        report = await service.erase_account(USER_KEY)

        declared = [s.collection for s in ErasureEngine.DELETE_STEPS if s.executor == "pest_image_cleanup"]
        assert len(declared) == 1
        assert report.delegated_removed == {declared[0]: 2}
        assert report.affected(declared[0]) == 2

    async def test_pest_images_in_a_tenant_the_user_left_are_still_hard_deleted(self):
        """The storage rule used to walk member tenants only; a former tenant's images survived."""
        calls: list[str] = []
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [
            Membership(user_key=USER_KEY, tenant_key="t-member", role="grower")
        ]
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [_contribution("t-left")]
        pest_repo.delete.return_value = True
        service = _service(
            storage_adapter=_storage(calls),
            membership_repo=membership_repo,
            pest_image_repo=pest_repo,
            attachment_repo=MagicMock(),
            erasure_executor=_executor(calls),
        )

        await service.erase_account(USER_KEY)

        assert "delete_for_user:t-left:user_pest_reference_images" in calls
        assert "delete_for_user:t-member:user_pest_reference_images" in calls

    async def test_the_art15_export_stays_restricted_to_member_tenants(self):
        """The widened tenant walk is erasure-only (#1662 SCR-001 must not regress)."""
        membership_repo = MagicMock()
        membership_repo.list_by_user.return_value = [
            Membership(user_key=USER_KEY, tenant_key="t-member", role="grower")
        ]
        pest_repo = MagicMock()
        pest_repo.list_for_user.return_value = [_contribution("t-left")]
        service = _service(membership_repo=membership_repo, pest_image_repo=pest_repo)

        assert service._user_tenant_keys(USER_KEY) == ["t-member"]


@pytest.mark.asyncio
async def test_the_pre_arango_phases_report_the_applied_scopes():
    """The Phase 0/0.5 part of ``erase_account`` returns the scopes it applied."""
    calls: list[str] = []
    membership_repo = MagicMock()
    membership_repo.list_by_user.return_value = [Membership(user_key=USER_KEY, tenant_key="t-1", role="grower")]
    service = _service(storage_adapter=_storage(calls), membership_repo=membership_repo, attachment_repo=MagicMock())

    report = AccountErasureReport()
    await service._run_pre_arango_phases(USER_KEY, report)

    assert report.storage_cleanup_scopes == [rule.scope for rule in ErasureEngine.STORAGE_CLEANUP_RULES]


def test_no_storage_only_erasure_entry_remains():
    """#1645 — the scheduled path was the last caller of the storage-only entry.

    With both account-deletion paths on ``erase_account``, a public method that
    runs Phase 0/0.5 and stops is an invitation to a second, partial erasure.
    """
    assert not hasattr(PrivacyService, "run_user_storage_erasure")


@pytest.mark.asyncio
async def test_stored_bundles_without_an_object_store_stop_the_erasure():
    """#1767 review — without an object store the bundles cannot go; the run must not report them gone."""
    from tests.support.privacy_doubles import FakeDataExportRepo

    export_repo = FakeDataExportRepo(
        DataExportRequest(_key="exp-1", user_key=USER_KEY, status="completed", file_path="privacy/exports/x.json")
    )
    calls: list[str] = []
    service = _service(export_repo=export_repo, storage_adapter=None, erasure_executor=_executor(calls))

    with pytest.raises(FeatureNotConfiguredError):
        await service.erase_account(USER_KEY)

    assert calls == []


@pytest.mark.asyncio
async def test_in_flight_exports_are_closed_before_the_bundles_are_deleted():
    from tests.support.privacy_doubles import FakeDataExportRepo

    export_repo = FakeDataExportRepo(DataExportRequest(_key="exp-1", user_key=USER_KEY, status="processing"))
    calls: list[str] = []
    service = _service(export_repo=export_repo, storage_adapter=_storage(calls), erasure_executor=_executor(calls))

    await service.erase_account(USER_KEY)

    assert export_repo.stored["exp-1"].status == "failed"
