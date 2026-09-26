"""#1769 — tenant deletion runs the declared inventory, persists its proof and retries.

Driven through ``TenantService.delete_tenant`` — the one method both HTTP entry
points call (``DELETE /t/{slug}``, ``DELETE /admin/platform/tenants/{key}``;
pinned by ``test_admin_platform_erasure_routing.py``) — and
``resume_tenant_erasures``, the daily beat. What the ArangoDB run removes is
measured against a real server in ``tests/integration/test_tenant_erasure_reach.py``;
this file pins the order of effects, the record and the refusals around it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import (
    ExternalSourceError,
    FeatureNotConfiguredError,
    ForbiddenError,
    NotFoundError,
    TenantErasureIncompleteError,
    ValidationError,
    WriteConflictError,
)
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from tests.support.tenant_erasure_doubles import (
    SALT,
    FakeTenantErasureRepository,
    RecordingTenantErasureExecutor,
    authorized,
    tenant,
    tenant_service_for_deletion,
)

NOW = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)
KEY = "t-1"
RECORD = TenantErasureEngine.record_key(KEY)


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A deployment that can erase has a log salt (#1812): the erasure refuses to run without one."""
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


def _record(repo: FakeTenantErasureRepository) -> dict:
    return repo.records[RECORD]


class TestTheDeletionRunsTheInventory:
    def test_the_executor_receives_the_declared_plan_and_the_record_completes(self) -> None:
        executor = RecordingTenantErasureExecutor()
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)

        result = service.delete_tenant(KEY, **authorized(KEY, origin="platform_admin"), now=NOW)

        (plan,) = executor.plans
        assert plan.tenant_key == KEY
        assert plan.entries == TenantErasureEngine.INVENTORY
        assert result.status == "completed"
        assert _record(repo)["status"] == "completed"
        assert _record(repo)["origin"] == "platform_admin"
        assert _record(repo)["unreached"] == []

    def test_retained_account_keys_become_the_accounts_tombstones(self) -> None:
        executor = RecordingTenantErasureExecutor(account_keys=["member-1"])
        service = tenant_service_for_deletion(executor=executor)

        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert executor.pseudonyms == {"member-1": ErasureEngine.compute_tombstone_hash("member-1", SALT)}

    def test_memberships_are_frozen_before_anything_is_erased(self) -> None:
        order: list[str] = []
        storage = MagicMock()
        storage.delete_prefix = AsyncMock(side_effect=lambda prefix: order.append("storage") or 0)
        executor = RecordingTenantErasureExecutor(on_run=lambda: order.append("arango"))
        readings = MagicMock()
        readings.delete_by_tenant.side_effect = lambda key: order.append("readings") or 0
        service = tenant_service_for_deletion(executor=executor, storage_adapter=storage, observation_repo=readings)
        service._membership_repo.deactivate_all_for_tenant.side_effect = lambda key: order.append("freeze") or 1

        service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        # Readings last: ingestion is not stopped by the freeze, only by the
        # sensors being gone (#1769 code review).
        assert order == ["freeze", "storage", "arango", "readings"]
        storage.delete_prefix.assert_awaited_once_with(f"t/{KEY}/")

    def test_the_tenants_sensor_readings_are_deleted_and_counted(self) -> None:
        """#1769 review GDPR-001 — TimescaleDB sits outside the ArangoDB transaction."""
        repo = FakeTenantErasureRepository()
        readings = MagicMock()
        readings.delete_by_tenant.return_value = 12
        tenant_service_for_deletion(record_repo=repo, observation_repo=readings).delete_tenant(
            KEY, **authorized(KEY), now=NOW
        )

        readings.delete_by_tenant.assert_called_once_with(KEY)
        assert _record(repo)["timeseries_rows_removed"] == 12

    def test_the_record_names_no_tenant_name_slug_or_owner(self) -> None:
        repo = FakeTenantErasureRepository()
        tenant_service_for_deletion(record_repo=repo).delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert {"name", "slug", "owner_user_key"}.isdisjoint(_record(repo))


class TestCompletionDependsOnWhatWasRemoved:
    def test_residue_keeps_the_deletion_open_and_answers_500(self) -> None:
        repo = FakeTenantErasureRepository()
        executor = RecordingTenantErasureExecutor(unreached=["undeclared:legacy_orphans"])
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)

        with pytest.raises(TenantErasureIncompleteError) as raised:
            service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert raised.value.status_code == 500
        assert KEY not in raised.value.message
        record = _record(repo)
        assert record["status"] == "partially_completed"
        assert record["unreached"] == ["undeclared:legacy_orphans"]
        assert record["attempt_count"] == 1
        assert record["next_attempt_at"] == (NOW + timedelta(days=1)).isoformat()

    def test_a_failed_external_store_is_recorded_and_the_inventory_does_not_run(self) -> None:
        repo = FakeTenantErasureRepository()
        executor = RecordingTenantErasureExecutor()
        store = MagicMock()
        store.configuration_error.return_value = None
        store.binding = "inference_service"
        store.delete_tenant_contributions = AsyncMock(side_effect=ExternalSourceError("inference", "down"))
        service = tenant_service_for_deletion(executor=executor, record_repo=repo, reference_index_store=store)

        with pytest.raises(ExternalSourceError):
            service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert executor.plans == []
        assert _record(repo)["status"] == "partially_completed"
        assert _record(repo)["error_message"].startswith("Attempt 1 failed (ExternalSourceError)")


class TestRefusalsBeforeAnythingChanges:
    def test_the_platform_tenant_is_refused_on_every_entry_point(self) -> None:
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(existing=tenant(KEY, is_platform=True), record_repo=repo)

        with pytest.raises(ForbiddenError):
            service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert repo.records == {}
        service._membership_repo.deactivate_all_for_tenant.assert_not_called()

    def test_an_unknown_tenant_is_404(self) -> None:
        service = tenant_service_for_deletion()
        service._tenant_repo.get_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.delete_tenant("ghost", **authorized("ghost"), now=NOW)

    def test_a_deployment_without_a_log_salt_answers_503_and_changes_nothing(self, monkeypatch) -> None:
        """#1812 review SEC-001: the record's ``requested_by_subject`` would be the constant ``anon_unavailable``."""
        from app.config.settings import settings

        monkeypatch.setattr(settings, "log_pseudonym_salt", "")
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(record_repo=repo)

        with pytest.raises(FeatureNotConfiguredError, match="LOG_PSEUDONYM_SALT"):
            service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert repo.records == {}
        service._membership_repo.deactivate_all_for_tenant.assert_not_called()

    @pytest.mark.parametrize(
        ("overrides", "reason"),
        [
            ({"salt": "short"}, "ERASURE_TOMBSTONE_SALT"),
            ({"executor": None, "tenant_erasure_executor": None}, "executor"),
            # #1759 — the pest feature is wired but no prototype store: refused
            # before the reference vectors are removed, not after.
            ({"pest_image_repo": MagicMock(), "pest_prototype_store": None}, "pest-prototype store"),
            ({"observation_repo": None}, "sensor-reading store"),
        ],
    )
    def test_a_deployment_that_cannot_erase_answers_503_and_changes_nothing(self, overrides, reason) -> None:
        repo = FakeTenantErasureRepository()
        store = MagicMock()
        store.configuration_error.return_value = None
        store.delete_tenant_contributions = AsyncMock(return_value=0)
        overrides = dict(overrides)
        if "tenant_erasure_executor" in overrides:
            overrides.pop("executor")
        service = tenant_service_for_deletion(record_repo=repo, reference_index_store=store, **overrides)

        with pytest.raises(FeatureNotConfiguredError, match=reason):
            service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        store.delete_tenant_contributions.assert_not_awaited()
        assert repo.records == {}
        service._membership_repo.deactivate_all_for_tenant.assert_not_called()

    def test_a_second_concurrent_deletion_is_a_conflict(self) -> None:
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(record_repo=repo)
        repo.records[RECORD] = {
            "tenant_key": KEY,
            "tenant_type": "organization",
            "origin": "tenant_management",
            "status": "in_progress",
            "last_attempt_at": NOW.isoformat(),
            "updated_at": NOW.isoformat(),
        }

        with pytest.raises(WriteConflictError):
            service.delete_tenant(KEY, **authorized(KEY), now=NOW)

    @pytest.mark.parametrize("bad_key", ["", "t/x", "../etc", "a b"])
    def test_a_malformed_key_never_builds_a_storage_prefix(self, bad_key) -> None:
        storage = MagicMock()
        storage.delete_prefix = AsyncMock(return_value=0)
        service = tenant_service_for_deletion(storage_adapter=storage)

        with pytest.raises(ValidationError):
            service._purge_tenant_storage(bad_key)

        storage.delete_prefix.assert_not_awaited()


class TestTheBeatRetries:
    def _open(self, repo: FakeTenantErasureRepository, *, next_attempt_at: datetime | None) -> None:
        repo.records[RECORD] = {
            "tenant_key": KEY,
            "tenant_type": "organization",
            "origin": "tenant_management",
            "status": "partially_completed",
            "attempt_count": 1,
            "next_attempt_at": next_attempt_at.isoformat() if next_attempt_at else None,
            "updated_at": (NOW - timedelta(days=1)).isoformat(),
        }

    def test_a_due_record_is_retried_to_completion_even_without_the_tenant_document(self) -> None:
        repo = FakeTenantErasureRepository()
        self._open(repo, next_attempt_at=NOW - timedelta(minutes=1))
        executor = RecordingTenantErasureExecutor()
        service = tenant_service_for_deletion(executor=executor, record_repo=repo)
        service._tenant_repo.get_by_key.return_value = None

        result = service.resume_tenant_erasures(NOW)

        assert result["completed"] == 1
        assert [plan.tenant_key for plan in executor.plans] == [KEY]
        assert _record(repo)["status"] == "completed"

    def test_a_record_inside_its_backoff_is_left_alone(self) -> None:
        repo = FakeTenantErasureRepository()
        self._open(repo, next_attempt_at=NOW + timedelta(days=2))
        executor = RecordingTenantErasureExecutor()

        result = tenant_service_for_deletion(executor=executor, record_repo=repo).resume_tenant_erasures(NOW)

        assert result["deferred"] == 1
        assert executor.plans == []

    def test_a_misconfigured_deployment_holds_every_record_without_spending_an_attempt(self) -> None:
        repo = FakeTenantErasureRepository()
        self._open(repo, next_attempt_at=None)

        result = tenant_service_for_deletion(record_repo=repo, salt="").resume_tenant_erasures(NOW)

        assert result["held"] == 1
        assert _record(repo)["attempt_count"] == 1

    def test_a_retry_that_fails_again_backs_off_further(self) -> None:
        repo = FakeTenantErasureRepository()
        self._open(repo, next_attempt_at=None)
        executor = RecordingTenantErasureExecutor(unreached=["sites"])

        result = tenant_service_for_deletion(executor=executor, record_repo=repo).resume_tenant_erasures(NOW)

        assert result["open"] == 1
        assert _record(repo)["attempt_count"] == 2
        assert _record(repo)["next_attempt_at"] == (NOW + timedelta(days=2)).isoformat()


class TestNoDeletionThatBreaksTheInstallationOrLeaksAccess:
    def test_light_mode_refuses_to_delete_its_system_tenant(self) -> None:
        """#1769 review SEC-002 — the light-mode tenant is the installation; its seed does not re-create it."""
        repo = FakeTenantErasureRepository()
        service = tenant_service_for_deletion(record_repo=repo, light_mode=True)

        with pytest.raises(ForbiddenError):
            service.delete_tenant(KEY, **authorized(KEY), now=NOW)

        assert repo.records == {}

    def test_no_new_membership_while_the_deletion_is_open(self) -> None:
        """#1769 review SEC-006 — an invitation accepted mid-deletion would grant access to a tenant being erased."""
        repo = FakeTenantErasureRepository()
        repo.records[RECORD] = {
            "tenant_key": KEY,
            "tenant_type": "organization",
            "origin": "tenant_management",
            "status": "partially_completed",
        }
        service = tenant_service_for_deletion(record_repo=repo)

        with pytest.raises(ForbiddenError):
            service.admin_add_membership(KEY, "user-9", TenantRole.GROWER)
        service._membership_repo.create.assert_not_called()

    def test_the_retry_feeds_the_persisted_parent_keys_back(self) -> None:
        """#1769 review SEC-001 — a child written after its parent's deletion is reached on the retry."""
        repo = FakeTenantErasureRepository()
        repo.records[RECORD] = {
            "tenant_key": KEY,
            "tenant_type": "organization",
            "origin": "tenant_management",
            "status": "partially_completed",
            "parent_keys": {"sites": ["site-1"]},
        }
        executor = RecordingTenantErasureExecutor()

        tenant_service_for_deletion(executor=executor, record_repo=repo).resume_tenant_erasures(NOW)

        (plan,) = executor.plans
        assert plan.known_parent_keys == {"sites": ["site-1"]}
