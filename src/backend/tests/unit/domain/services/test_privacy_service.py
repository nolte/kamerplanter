"""Smoke tests for PrivacyService (REQ-025)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions import (
    DuplicateError,
    InvalidTokenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.privacy import (
    ConsentRecord,
    DataExportRequest,
    EmailChangeRequest,
    ErasureRequest,
    ProcessingRestriction,
)
from app.domain.models.user import User
from app.domain.services.privacy_service import PrivacyService
from tests.conftest import wire_get_or_raise

USER_KEY = "u1"
USER_EMAIL = "user@example.com"
USER_PASSWORD = "correct-horse-battery-staple"


@pytest.fixture
def password_engine():
    return PasswordEngine()


@pytest.fixture
def user(password_engine):
    return User(
        _key=USER_KEY,
        email=USER_EMAIL,
        display_name="Test User",
        password_hash=password_engine.hash_password(USER_PASSWORD),
        email_verified=True,
        is_active=True,
    )


@pytest.fixture
def export_repo():
    repo = MagicMock()
    repo.list_active_by_user.return_value = []
    repo.list_by_user.return_value = []

    def _create(export):
        export.key = "export-1"
        return export

    repo.create.side_effect = _create
    wire_get_or_raise(repo, "DataExportRequest")
    return repo


@pytest.fixture
def consent_repo():
    repo = MagicMock()
    repo.list_by_user.return_value = []
    repo.get_by_user_and_purpose.return_value = None

    def _create(record):
        record.key = "consent-1"
        return record

    def _update(_key, record):
        return record

    repo.create.side_effect = _create
    repo.update.side_effect = _update
    return repo


@pytest.fixture
def restriction_repo():
    repo = MagicMock()
    repo.get_by_user_and_scope.return_value = None
    repo.list_by_user.return_value = []
    repo.list_active_by_user.return_value = []

    def _create(restriction):
        restriction.key = "restriction-1"
        restriction.created_at = datetime.now(UTC)
        return restriction

    def _update(_key, restriction):
        return restriction

    repo.create.side_effect = _create
    repo.update.side_effect = _update
    return repo


@pytest.fixture
def erasure_repo():
    repo = MagicMock()
    repo.find_active_for_user.return_value = None
    repo.list_by_user.return_value = []

    def _create(erasure):
        erasure.key = "erasure-1"
        return erasure

    repo.create.side_effect = _create
    wire_get_or_raise(repo, "ErasureRequest")
    return repo


@pytest.fixture
def email_change_repo():
    repo = MagicMock()
    repo.list_pending_for_user.return_value = []
    repo.get_by_token_hash.return_value = None

    def _create(change):
        change.key = "ec-1"
        return change

    def _update(_key, change):
        return change

    repo.create.side_effect = _create
    repo.update.side_effect = _update
    return repo


@pytest.fixture
def user_repo(user):
    repo = MagicMock()
    repo.get_by_key.return_value = user
    repo.get_by_email.return_value = None
    repo.update.side_effect = lambda _k, u: u
    wire_get_or_raise(repo, "User")
    return repo


@pytest.fixture
def refresh_token_repo():
    repo = MagicMock()
    repo.revoke_all_for_user.return_value = 0
    return repo


@pytest.fixture
def email_service():
    return MagicMock()


@pytest.fixture
def service(
    export_repo,
    consent_repo,
    restriction_repo,
    erasure_repo,
    email_change_repo,
    user_repo,
    refresh_token_repo,
    password_engine,
    email_service,
):
    return PrivacyService(
        export_repo=export_repo,
        consent_repo=consent_repo,
        restriction_repo=restriction_repo,
        erasure_repo=erasure_repo,
        email_change_repo=email_change_repo,
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=password_engine,
        token_engine=TokenEngine("test-secret-key-32-chars-min!!!", "HS256"),
        email_service=email_service,
        frontend_url="http://localhost:5173",
    )


# ── Data export ────────────────────────────────────────────────────


class TestDataExport:
    def test_request_export_creates_pending_record(self, service, export_repo):
        with patch("app.tasks.retention_tasks.process_data_export.delay"):
            export = service.request_data_export(USER_KEY)

        assert export.status == "pending"
        assert export.user_key == USER_KEY
        assert export.requested_at is not None
        export_repo.create.assert_called_once()

    def test_request_data_export_dispatches_task(self, service):
        with patch("app.tasks.retention_tasks.process_data_export.delay") as delay:
            created = service.request_data_export(USER_KEY)

        delay.assert_called_once_with(created.key)

    def test_request_data_export_survives_dispatch_failure(self, service):
        # A broker outage must not fail the API request — GDPR Art. 15 acceptance
        # of the request takes precedence over immediate processing.
        with patch(
            "app.tasks.retention_tasks.process_data_export.delay",
            side_effect=ConnectionError("broker down"),
        ):
            created = service.request_data_export(USER_KEY)

        assert created.status == "pending"
        assert created.key == "export-1"

    def test_request_export_blocked_when_active_exists(
        self,
        service,
        export_repo,
    ):
        export_repo.list_active_by_user.return_value = [
            DataExportRequest(
                _key="active-1",
                user_key=USER_KEY,
                status="processing",
                requested_at=datetime.now(UTC),
            )
        ]

        with pytest.raises(ValidationError):
            service.request_data_export(USER_KEY)

    def test_get_export_status_enforces_ownership(self, service, export_repo):
        export_repo.get_by_key.return_value = DataExportRequest(
            _key="export-2",
            user_key="other-user",
            status="pending",
        )

        with pytest.raises(NotFoundError):
            service.get_export_status(USER_KEY, "export-2")

    def test_prepare_download_increments_counter(self, service, export_repo):
        completed = DataExportRequest(
            _key="export-3",
            user_key=USER_KEY,
            status="completed",
            file_path="/exports/export-3.json",
            file_size_bytes=2048,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            download_count=0,
        )
        export_repo.get_by_key.return_value = completed
        export_repo.update.side_effect = lambda _k, e: e

        result = service.prepare_export_download(USER_KEY, "export-3")

        assert result.download_count == 1
        export_repo.update.assert_called_once()

    def test_prepare_download_rejects_expired(self, service, export_repo):
        export_repo.get_by_key.return_value = DataExportRequest(
            _key="export-4",
            user_key=USER_KEY,
            status="completed",
            file_path="/exports/export-4.json",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )

        with pytest.raises(ValidationError):
            service.prepare_export_download(USER_KEY, "export-4")


# ── Consent ────────────────────────────────────────────────────────


class TestConsent:
    def test_grant_creates_record_with_granted_at(self, service, consent_repo):
        record = service.grant_consent(USER_KEY, "error_tracking")

        assert record.granted is True
        assert record.granted_at is not None
        consent_repo.create.assert_called_once()

    def test_grant_unknown_purpose_raises(self, service):
        with pytest.raises(ValidationError):
            service.grant_consent(USER_KEY, "unknown_purpose")

    def test_revoke_required_purpose_blocked(self, service):
        with pytest.raises(ValidationError):
            service.revoke_consent(USER_KEY, "core_functionality")

    def test_revoke_existing_consent_marks_revoked(self, service, consent_repo):
        consent_repo.get_by_user_and_purpose.return_value = ConsentRecord(
            _key="consent-existing",
            user_key=USER_KEY,
            purpose="error_tracking",
            granted=True,
            granted_at=datetime.now(UTC) - timedelta(days=1),
        )

        record = service.revoke_consent(USER_KEY, "error_tracking")

        assert record.granted is False
        assert record.revoked_at is not None

    def test_list_consents_includes_all_purposes(self, service):
        results = service.list_consents(USER_KEY)

        purpose_keys = {r.purpose for r in results}
        assert "core_functionality" in purpose_keys
        assert "error_tracking" in purpose_keys
        # core_functionality is required and granted by default.
        core = next(r for r in results if r.purpose == "core_functionality")
        assert core.required is True
        assert core.granted is True


# ── Erasure ────────────────────────────────────────────────────────


class TestErasure:
    def test_erasure_requires_password_for_local_account(
        self,
        service,
    ):
        with pytest.raises(UnauthorizedError):
            service.request_erasure(USER_KEY, password_confirmation="wrong-password")

    def test_erasure_soft_deletes_and_revokes_sessions(
        self,
        service,
        erasure_repo,
        user_repo,
        refresh_token_repo,
    ):
        erasure = service.request_erasure(
            USER_KEY,
            password_confirmation=USER_PASSWORD,
        )

        assert erasure.status == "scheduled"
        assert erasure.soft_deleted_at is not None
        assert erasure.hard_delete_scheduled_at is not None
        assert erasure.anonymized_collections  # not empty
        # Soft-delete: user.is_active flipped to False
        update_call = user_repo.update.call_args
        assert update_call is not None
        updated_user = update_call[0][1]
        assert updated_user.is_active is False
        assert updated_user.password_hash is None
        # Sessions revoked
        refresh_token_repo.revoke_all_for_user.assert_called_once_with(USER_KEY)
        erasure_repo.create.assert_called_once()

    def test_erasure_blocked_when_active_exists(
        self,
        service,
        erasure_repo,
    ):
        erasure_repo.find_active_for_user.return_value = ErasureRequest(
            _key="existing-erasure",
            user_key=USER_KEY,
            status="scheduled",
        )

        with pytest.raises(ValidationError):
            service.request_erasure(USER_KEY, password_confirmation=USER_PASSWORD)


# ── Restriction ────────────────────────────────────────────────────


class TestRestriction:
    def test_create_restriction(self, service, restriction_repo):
        restriction = service.restrict_processing(
            USER_KEY,
            scope="analytics",
            reason="purpose_expired",
        )

        assert restriction.scope == "analytics"
        assert restriction.reason == "purpose_expired"
        restriction_repo.create.assert_called_once()

    def test_create_restriction_duplicate_blocked(self, service, restriction_repo):
        restriction_repo.get_by_user_and_scope.return_value = ProcessingRestriction(
            _key="r-active",
            user_key=USER_KEY,
            scope="analytics",
            reason="objection_pending",
        )

        with pytest.raises(DuplicateError):
            service.restrict_processing(
                USER_KEY,
                scope="analytics",
                reason="purpose_expired",
            )

    def test_lift_restriction_sets_lifted_at(self, service, restriction_repo):
        restriction_repo.get_by_key.return_value = ProcessingRestriction(
            _key="r-1",
            user_key=USER_KEY,
            scope="analytics",
            reason="purpose_expired",
        )

        result = service.lift_restriction(USER_KEY, "r-1")

        assert result.lifted_at is not None


# ── Email change ───────────────────────────────────────────────────


class TestEmailChange:
    def test_email_change_creates_pending_request(
        self,
        service,
        email_change_repo,
        email_service,
    ):
        change = service.request_email_change(USER_KEY, "new@example.com")

        assert change.status == "pending"
        assert str(change.new_email) == "new@example.com"
        email_change_repo.create.assert_called_once()
        email_service.send_verification_email.assert_called_once()

    def test_email_change_to_a_taken_address_does_not_disclose_it(
        self,
        service,
        user_repo,
        email_change_repo,
        user,
    ):
        """This used to assert ``DuplicateError`` — i.e. it pinned the disclosure.

        The 409 it produced said ``User with email='<address>' already exists.``
        The full property is covered in
        ``test_privacy_email_change_enumeration.py``; what stays here is the
        contract this suite already described, corrected.
        """
        user_repo.get_by_email.return_value = User(
            _key="other",
            email="new@example.com",
            display_name="Other",
        )

        change = service.request_email_change(USER_KEY, "new@example.com")

        assert change.status == "pending"
        email_change_repo.create.assert_not_called()

    def test_confirm_email_change_swaps_email(
        self,
        service,
        email_change_repo,
        user_repo,
        user,
        refresh_token_repo,
    ):
        # Stage a pending request whose token-hash matches our raw token.
        raw_token = "abcdef123456"
        token_engine = service._token_engine  # noqa: SLF001
        token_hash = token_engine.hash_token(raw_token)
        pending = EmailChangeRequest(
            _key="ec-1",
            user_key=USER_KEY,
            new_email="new@example.com",
            verification_token_hash=token_hash,
            status="pending",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            requested_at=datetime.now(UTC),
        )
        email_change_repo.get_by_token_hash.return_value = pending

        result = service.confirm_email_change(raw_token)

        assert result.email == "new@example.com"
        assert result.email_verified is True
        refresh_token_repo.revoke_all_for_user.assert_called_once_with(USER_KEY)

    def test_confirm_email_change_invalid_token_raises(
        self,
        service,
        email_change_repo,
    ):
        email_change_repo.get_by_token_hash.return_value = None

        with pytest.raises(InvalidTokenError):
            service.confirm_email_change("bogus-token")


# ── Privacy policy ─────────────────────────────────────────────────


class TestPrivacyPolicy:
    def test_get_privacy_policy_includes_purposes_and_rights(self, service):
        policy = service.get_privacy_policy()

        assert policy.version
        assert policy.effective_date
        assert any(p.key == "core_functionality" for p in policy.purposes)
        assert any(r.article == "Art. 17" for r in policy.rights_summary)
        assert policy.data_controller.contact_email


# ── DataSubjectService facade ──────────────────────────────────────


class TestDataSubjectServiceFacade:
    def test_facade_delegates_access_to_export(self, service):
        from app.domain.services.data_subject_service import DataSubjectService

        facade = DataSubjectService(service)
        # Stub the dispatch like every other export test above (#978): unstubbed,
        # `.delay()` publishes to the real Celery broker — a message in the dev
        # Valkey when the stack is up, a connect timeout when it is not.
        with patch("app.tasks.retention_tasks.process_data_export.delay"):
            export = facade.access(USER_KEY)

        assert export.status == "pending"

    def test_facade_delegates_erasure(self, service):
        from app.domain.services.data_subject_service import DataSubjectService

        facade = DataSubjectService(service)
        erasure = facade.erase(USER_KEY, password_confirmation=USER_PASSWORD)

        assert erasure.status == "scheduled"

    def test_facade_delegates_objection(self, service):
        from app.domain.services.data_subject_service import DataSubjectService

        facade = DataSubjectService(service)
        result = facade.object_to(USER_KEY, "external_enrichment", "I object")

        assert result.reason == "objection_pending"


# ── RetentionService ───────────────────────────────────────────────


class TestRetentionService:
    def test_export_expires_72h_by_default(self):
        from app.domain.services.retention_service import RetentionService

        retention = RetentionService(
            export_retention_hours=72,
            hard_delete_after_days=90,
            email_change_ttl_hours=24,
        )
        completed = datetime.now(UTC)
        expires = retention.export_expires_at(completed)
        assert (expires - completed).total_seconds() == 72 * 3600

    def test_hard_delete_after_90_days_by_default(self):
        from app.domain.services.retention_service import RetentionService

        retention = RetentionService(
            export_retention_hours=72,
            hard_delete_after_days=90,
            email_change_ttl_hours=24,
        )
        soft = datetime.now(UTC)
        target = retention.hard_delete_at(soft)
        assert (target - soft).days == 90

    def test_is_export_expired_predicate(self):
        from app.domain.services.retention_service import RetentionService

        retention = RetentionService(
            export_retention_hours=72,
            hard_delete_after_days=90,
            email_change_ttl_hours=24,
        )
        old_completion = datetime.now(UTC) - timedelta(hours=80)
        assert retention.is_export_expired(old_completion) is True
        assert retention.is_export_expired(None) is False

    def test_is_due_for_hard_delete(self):
        from app.domain.services.retention_service import RetentionService

        retention = RetentionService(
            export_retention_hours=72,
            hard_delete_after_days=90,
            email_change_ttl_hours=24,
        )
        old_soft = datetime.now(UTC) - timedelta(days=91)
        assert retention.is_due_for_hard_delete(old_soft) is True
        recent = datetime.now(UTC) - timedelta(days=10)
        assert retention.is_due_for_hard_delete(recent) is False
