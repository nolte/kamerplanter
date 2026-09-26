"""#1767 GDPR-004 / SEC-003 — the immediate erasure entries keep proof and retry.

The platform-admin ``DELETE /admin/platform/users/{key}`` and the
unverified-account cleanup erase at once instead of after the self-service
grace. Until #1767 both called :meth:`PrivacyService.erase_account` and
discarded its report: a run that skipped a declared step answered 204 (or
counted ``removed``), nothing was persisted, and a failure left nothing that
would retry it. They also did not deactivate the account first, so a live
session could write between the storage phases and the ArangoDB plan, and two
runs for one account could overlap (SEC-003).

Pinned here through the production entry :meth:`PrivacyService.erase_account_now`
with the faithful :class:`FakeErasureRepo` (the real claim and selection
filters), never on a ``MagicMock`` that would accept any write:

* a run that accounts for every step leaves a ``completed`` record with its origin;
* a run that leaves a step unreached raises, and leaves a ``partially_completed``
  record the daily beat selects after the backoff;
* the account is deactivated and its sessions revoked **before** the run;
* a misconfigured deployment changes nothing;
* a request another run holds is refused, and its erasure does not run twice.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import (
    ErasureIncompleteError,
    FeatureNotConfiguredError,
    WriteConflictError,
)
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import ErasureRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakeErasureRepo, FakePersonalTenants, RecordingErasureExecutor

SALT = "s" * 32
USER = "u-1"
NOW = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A deployment that can erase has a log salt (#1812): the erasure refuses to run without one."""
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


class _Recorder:
    """Records the order of the account writes and the executor run."""

    def __init__(self, executor: RecordingErasureExecutor) -> None:
        self.events: list[str] = []
        self.user_repo = MagicMock()
        self.user_repo.get_by_key.return_value = SimpleNamespace(key=USER, email_verified=False)
        self.user_repo.update_fields.side_effect = lambda key, fields: self.events.append(
            f"user:{sorted(fields.items())}"
        )
        self.refresh_token_repo = MagicMock()
        self.refresh_token_repo.revoke_all_for_user.side_effect = lambda key: self.events.append("revoke")
        self.consent_repo = MagicMock()

        def _revoke_all_unrevoked(_key: str, _now: str) -> int:
            self.events.append("consent_revoke")
            return 0

        self.consent_repo.revoke_all_unrevoked.side_effect = _revoke_all_unrevoked
        inner = executor.run_erasure_plan

        def _run(plan, *, tombstone, executors=None):
            self.events.append("executor")
            return inner(plan, tombstone=tombstone, executors=executors)

        executor.run_erasure_plan = _run  # type: ignore[method-assign]
        self.executor = executor


def _service(
    repo: FakeErasureRepo,
    executor: RecordingErasureExecutor,
    *,
    salt: str = SALT,
) -> tuple[PrivacyService, _Recorder]:
    recorder = _Recorder(executor)
    export_repo = MagicMock()
    export_repo.list_by_user.return_value = []
    service = PrivacyService(
        export_repo=export_repo,
        consent_repo=recorder.consent_repo,
        restriction_repo=MagicMock(),
        erasure_repo=repo,
        email_change_repo=MagicMock(),
        user_repo=recorder.user_repo,
        refresh_token_repo=recorder.refresh_token_repo,
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="https://app.test",
        reference_index_store=NoopReferenceIndexStore(),
        erasure_executor=executor,
        tenant_service=FakePersonalTenants(),
        tombstone_salt=salt,
    )
    return service, recorder


def _admin_request(service: PrivacyService, recorder: _Recorder) -> dict:
    """Route arguments of a platform admin erasing ``USER`` with a valid step-up (#1814).

    The admin signs in only federated (no hash), so the step-up is the echo of the
    target's e-mail plus the code mailed to the admin (#1815), issued through the
    service's own verifier; the stored platform membership proves the admin.
    """
    from app.api.v1.privacy.schemas import ErasureCreateRequest
    from app.common.enums import TenantRole
    from app.domain.models.membership import Membership
    from app.domain.models.user import User

    recorder.user_repo.get_or_raise.return_value = User.model_validate(
        {"_key": USER, "email": f"{USER}@example.org", "display_name": "Subject"}
    )
    service._membership_repo = MagicMock(  # type: ignore[attr-defined]
        **{
            "get_by_user_and_tenant.return_value": Membership(
                user_key="admin-1", tenant_key="platform", role=TenantRole.LEAD
            )
        }
    )
    admin = User.model_validate({"_key": "admin-1", "email": "admin@example.org", "display_name": "A"})
    from tests.support.step_up import admitting_every_target

    with admitting_every_target(service._step_up_verifier) as verifier:
        code, _expires_at = verifier.issue_code(
            admin,
            action="admin_account_erasure",
            target=USER,
            authenticated_with_api_key=False,
            client_ip="203.0.113.1",
        )
    return {
        "body": ErasureCreateRequest(confirm_email=f"{USER}@example.org", step_up_code=code),
        "current_user": admin,
        "via_api_key": False,
        "client_ip": "203.0.113.1",
        "privacy_service": service,
    }


def _only(repo: FakeErasureRepo) -> ErasureRequest:
    (request,) = repo.stored.values()
    return request


@pytest.mark.asyncio
class TestTheAdminDeletePersistsItsProof:
    async def test_a_complete_run_leaves_a_completed_record_with_its_origin(self):
        repo = FakeErasureRepo()
        service, _ = _service(repo, RecordingErasureExecutor())

        result = await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        request = _only(repo)
        assert result is request
        assert (request.status, request.origin) == ("completed", "platform_admin")
        assert request.completed_at == NOW
        assert request.hard_delete_scheduled_at == NOW

    async def test_an_unreached_step_raises_and_leaves_the_duty_open_for_the_beat(self):
        repo = FakeErasureRepo()
        # ``processing_restrictions`` (any document step still on DELETE_STEPS
        # works — not ``consent_records``, which #1800 moved into
        # PSEUDONYMIZE_AUDIT_COLLECTIONS and out of the plan's declared steps).
        service, _ = _service(repo, RecordingErasureExecutor(drop=("processing_restrictions",)))

        with pytest.raises(ErasureIncompleteError) as excinfo:
            await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        request = _only(repo)
        assert "processing_restrictions" in excinfo.value.message
        assert request.key not in str(excinfo.value.details), "the request key stays out of the answer"
        assert request.status == "partially_completed"
        assert request.attempt_count == 1
        after_backoff = request.next_attempt_at + timedelta(minutes=1)
        assert repo.list_due_for_hard_delete(after_backoff.isoformat(), after_backoff.isoformat()) == [request]

    async def test_a_failing_run_re_raises_after_recording_the_attempt(self):
        repo = FakeErasureRepo()
        service, _ = _service(repo, RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted")))

        with pytest.raises(RuntimeError, match="transaction aborted"):
            await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        request = _only(repo)
        assert request.status == "partially_completed"
        assert "transaction aborted" in (request.error_message or "")

    async def test_the_beat_completes_what_the_admin_run_left_open(self):
        repo = FakeErasureRepo()
        executor = RecordingErasureExecutor(fail_with=RuntimeError("transaction aborted"))
        service, _ = _service(repo, executor)
        with pytest.raises(RuntimeError):
            await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        executor._fail_with = None
        finalised = await service.execute_scheduled_erasures(NOW + timedelta(days=2))

        assert finalised == 1
        assert _only(repo).status == "completed"


@pytest.mark.asyncio
class TestTheAccountIsClosedBeforeAnythingIsRemoved:
    async def test_deactivation_and_session_revocation_precede_the_executor(self):
        repo = FakeErasureRepo()
        service, recorder = _service(repo, RecordingErasureExecutor())
        # Review SEC-D: the request exists before the account is closed, so a
        # failure after the close still leaves a duty the beat retries.
        recorder.user_repo.update_fields.side_effect = lambda key, fields: recorder.events.append(
            f"user:{sorted(fields.items())}:requests={len(repo.stored)}"
        )

        await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        # #1800 security review (SEC-001): revoke_all_unrevoked must run before
        # the executor pseudonymises consent_records, or an unrevoked consent
        # would be pseudonymised with revoked_at still null and the R-04 purge
        # (which excludes null on purpose) would never reach it.
        assert recorder.events[:4] == [
            "user:[('is_active', False), ('password_hash', None)]:requests=1",
            "revoke",
            "consent_revoke",
            "executor",
        ]

    async def test_a_misconfigured_deployment_changes_nothing(self):
        repo = FakeErasureRepo()
        service, recorder = _service(repo, RecordingErasureExecutor(), salt="short")

        with pytest.raises(FeatureNotConfiguredError):
            await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        assert repo.stored == {}
        assert recorder.events == []

    @pytest.mark.parametrize("log_salt", ["", "short"])
    async def test_a_deployment_without_a_log_salt_changes_nothing(self, monkeypatch, log_salt):
        """#1812 review SEC-001: the proof's ``requested_by_subject`` would be the constant ``anon_unavailable``."""
        from app.config.settings import settings

        monkeypatch.setattr(settings, "log_pseudonym_salt", log_salt)
        repo = FakeErasureRepo()
        service, recorder = _service(repo, RecordingErasureExecutor())

        with pytest.raises(FeatureNotConfiguredError, match="LOG_PSEUDONYM_SALT"):
            await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        assert repo.stored == {}
        assert recorder.events == []

    async def test_an_empty_key_is_refused_before_anything_runs(self):
        repo = FakeErasureRepo()
        service, recorder = _service(repo, RecordingErasureExecutor())

        with pytest.raises(ValueError):
            await service.erase_account_now(" ", origin="platform_admin", now=NOW)

        assert repo.stored == {}
        assert recorder.events == []


@pytest.mark.asyncio
class TestOneAccountIsErasedByOneRunAtATime:
    async def test_a_request_a_fresh_run_holds_is_refused_and_not_run_again(self):
        held = ErasureRequest(
            key="er-held",
            user_key=USER,
            status="in_progress",
            hard_delete_scheduled_at=NOW,
            updated_at=NOW - timedelta(minutes=5),
        )
        repo = FakeErasureRepo(held)
        executor = RecordingErasureExecutor()
        service, _ = _service(repo, executor)

        with pytest.raises(WriteConflictError):
            await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        assert executor.runs == []
        assert list(repo.stored) == ["er-held"]

    async def test_two_callers_that_both_found_no_request_cannot_both_create_one(self):
        """The second caller's lookup ran before the first one's insert landed."""
        repo = FakeErasureRepo()
        executor = RecordingErasureExecutor()
        service, _ = _service(repo, executor)
        first = service._create_immediate_request(USER, now=NOW, origin="platform_admin")
        repo.find_active_for_user = lambda user_key: None  # type: ignore[method-assign]

        with pytest.raises(WriteConflictError):
            await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        assert list(repo.stored) == [first.key]
        assert executor.runs == []

    async def test_the_request_key_names_neither_the_account_nor_its_tombstone(self):
        """Deterministic for the collision, but not linkable to the audit pseudonym (review SEC-C)."""
        repo = FakeErasureRepo()
        service, _ = _service(repo, RecordingErasureExecutor())

        await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        (key,) = repo.stored
        assert key == ErasureEngine.compute_request_key(USER, SALT)
        assert USER not in key
        assert ErasureEngine.compute_tombstone_hash(USER, SALT).removeprefix("anon_") not in key
        assert not ErasureEngine.is_tombstone(key)

    async def test_the_beat_does_not_run_a_request_an_immediate_run_claimed_meanwhile(self):
        """The beat listed the request, then an admin run claimed it: the beat must skip it."""
        request = ErasureRequest(key="er-1", user_key=USER, status="scheduled", hard_delete_scheduled_at=NOW)
        repo = FakeErasureRepo(request)
        executor = RecordingErasureExecutor()
        service, _ = _service(repo, executor)
        repo.claim_for_run("er-1", now_iso=NOW.isoformat(), stale_before_iso=(NOW - timedelta(hours=1)).isoformat())

        finalised = await service._finalize_erasure(request, NOW)

        assert finalised is False
        assert executor.runs == []


@pytest.mark.asyncio
class TestAnOpenRequestIsReusedNotDuplicated:
    async def test_a_self_service_request_in_its_grace_is_run_now_and_stays_one_record(self):
        grace = ErasureRequest(
            key="er-self",
            user_key=USER,
            status="scheduled",
            origin="self_service",
            hard_delete_scheduled_at=NOW + timedelta(days=60),
        )
        repo = FakeErasureRepo(grace)
        service, _ = _service(repo, RecordingErasureExecutor())

        await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        assert list(repo.stored) == ["er-self"]
        assert grace.status == "completed"
        assert grace.hard_delete_scheduled_at == NOW

    async def test_the_cleanup_leaves_a_request_in_its_backoff_to_the_beat(self):
        waiting = ErasureRequest(
            key="er-wait",
            user_key=USER,
            status="partially_completed",
            origin="unverified_cleanup",
            attempt_count=1,
            hard_delete_scheduled_at=NOW - timedelta(hours=1),
            next_attempt_at=NOW + timedelta(days=1),
        )
        repo = FakeErasureRepo(waiting)
        executor = RecordingErasureExecutor()
        service, recorder = _service(repo, executor)

        result = await service.erase_account_now(USER, origin="unverified_cleanup", now=NOW)

        assert result is waiting
        assert result.status == "partially_completed"
        assert executor.runs == []
        assert recorder.events == []

    async def test_an_admin_retries_a_request_in_its_backoff_at_once(self):
        waiting = ErasureRequest(
            key="er-wait",
            user_key=USER,
            status="partially_completed",
            attempt_count=1,
            hard_delete_scheduled_at=NOW - timedelta(hours=1),
            next_attempt_at=NOW + timedelta(days=1),
        )
        repo = FakeErasureRepo(waiting)
        service, _ = _service(repo, RecordingErasureExecutor())

        await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        assert waiting.status == "completed"


class TestTheEntryPointsGoThroughIt:
    """Red before #1767: both entry points discarded the report of an unreached step."""

    def test_the_admin_route_does_not_answer_success_over_an_unreached_step(self):

        from app.api.v1.admin.platform import router as admin_router

        repo = FakeErasureRepo()
        service, recorder = _service(repo, RecordingErasureExecutor(drop=("processing_restrictions",)))

        with pytest.raises(ErasureIncompleteError):
            admin_router.delete_user(USER, **_admin_request(service, recorder))

        request = _only(repo)
        assert (request.origin, request.status) == ("platform_admin", "partially_completed")

    def test_the_admin_route_persists_a_completed_record(self):

        from app.api.v1.admin.platform import router as admin_router

        repo = FakeErasureRepo()
        service, recorder = _service(repo, RecordingErasureExecutor())

        admin_router.delete_user(USER, **_admin_request(service, recorder))

        assert (_only(repo).origin, _only(repo).status) == ("platform_admin", "completed")

    def test_the_cleanup_does_not_count_an_unreached_step_as_removed(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from app.tasks.auth_tasks import cleanup_unverified_accounts

        repo = FakeErasureRepo()
        service, _ = _service(repo, RecordingErasureExecutor(drop=("processing_restrictions",)))
        user_repo = MagicMock()
        user_repo.get_unverified_before.return_value = [SimpleNamespace(key=USER)]
        with (
            patch("app.common.dependencies.get_user_repo", return_value=user_repo),
            patch("app.common.dependencies.get_privacy_service", return_value=service),
        ):
            result = cleanup_unverified_accounts.run()

        assert result["removed"] == 0
        assert result["failed"] == 1
        request = _only(repo)
        assert (request.origin, request.status) == ("unverified_cleanup", "partially_completed")


@pytest.mark.asyncio
class TestReviewFindings:
    async def test_the_cleanup_leaves_an_account_verified_since_the_snapshot_alone(self):
        repo = FakeErasureRepo()
        executor = RecordingErasureExecutor()
        service, recorder = _service(repo, executor)
        recorder.user_repo.get_by_key.return_value = SimpleNamespace(key=USER, email_verified=True)

        result = await service.erase_account_now(USER, origin="unverified_cleanup", now=NOW)

        assert result is None
        assert repo.stored == {}
        assert executor.runs == []
        assert recorder.events == []

    async def test_a_recorded_failure_does_not_carry_the_account_key(self):
        repo = FakeErasureRepo()
        service, _ = _service(repo, RecordingErasureExecutor(fail_with=RuntimeError(f"write to users/{USER} failed")))

        with pytest.raises(RuntimeError):
            await service.erase_account_now(USER, origin="platform_admin", now=NOW)

        assert USER not in (_only(repo).error_message or "")

    async def test_the_beat_closes_a_committed_request_without_waiting_out_its_backoff(self):
        committed = ErasureRequest(
            key="er-done",
            user_key=ErasureEngine.compute_tombstone_hash(USER, SALT),
            status="partially_completed",
            attempt_count=1,
            hard_delete_scheduled_at=NOW - timedelta(hours=1),
            next_attempt_at=NOW + timedelta(days=1),
            error_message="Erasure did not finish.",
        )
        repo = FakeErasureRepo(committed)
        service, _ = _service(repo, RecordingErasureExecutor())

        assert await service.execute_scheduled_erasures(NOW) == 1
        assert (committed.status, committed.error_message) == ("completed", None)

    def test_stored_bundles_without_an_object_store_fail_one_account_not_the_run(self):
        """#1767 code review — this is per account; the cleanup must not report every candidate blocked."""
        from unittest.mock import patch

        from app.domain.models.privacy import DataExportRequest
        from app.tasks.auth_tasks import cleanup_unverified_accounts
        from tests.support.privacy_doubles import FakeDataExportRepo

        repo = FakeErasureRepo()
        service, _ = _service(repo, RecordingErasureExecutor())
        service._export_repo = FakeDataExportRepo(
            DataExportRequest(_key="exp-1", user_key=USER, status="completed", file_path="privacy/exports/x.json")
        )
        user_repo = MagicMock()
        user_repo.get_unverified_before.return_value = [SimpleNamespace(key=USER), SimpleNamespace(key="u-2")]
        with (
            patch("app.common.dependencies.get_user_repo", return_value=user_repo),
            patch("app.common.dependencies.get_privacy_service", return_value=service),
        ):
            result = cleanup_unverified_accounts.run()

        assert result["blocked"] == 0
        assert result["failed"] == 1
        assert result["removed"] == 1
