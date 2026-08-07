"""API smoke tests for the REQ-025 privacy router.

These tests mount only the privacy router on a minimal FastAPI app to keep
DB-dependent middleware out of the picture.
"""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth.router import limiter
from app.api.v1.privacy.router import public_router as privacy_public_router
from app.api.v1.privacy.router import router as privacy_router
from app.common.auth import get_current_user
from app.common.dependencies import get_privacy_service
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.models.privacy import (
    ConsentRecord,
    ConsentWithPurpose,
    DataControllerInfo,
    DataExportRequest,
    EmailChangeRequest,
    ErasureRequest,
    PrivacyPolicyInfo,
    ProcessingRestriction,
    RetentionCategoryInfo,
    RightInfo,
)
from app.domain.models.user import User

USER_KEY = "u-test-1"


def _build_app(service):
    app = FastAPI()
    app.include_router(privacy_router, prefix="/api/v1")
    app.include_router(privacy_public_router, prefix="/api/v1")
    app.dependency_overrides[get_privacy_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: User(
        _key=USER_KEY,
        email="user@example.com",
        display_name="Test User",
        is_active=True,
    )
    return app


def _build_service():
    service = MagicMock()
    service._consent_engine = ConsentEngine()  # noqa: SLF001 — used by router
    return service


class TestPrivacyPolicy:
    def test_get_policy_is_public(self):
        service = _build_service()
        service.get_privacy_policy.return_value = PrivacyPolicyInfo(
            version="1.0",
            effective_date=date(2026, 4, 27),
            purposes=ConsentEngine().get_all_purposes(),
            retention_summary=[
                RetentionCategoryInfo(
                    category="account_data",
                    description="Profile",
                    retention_period="Until deletion",
                ),
            ],
            data_controller=DataControllerInfo(name="Op", contact_email="privacy@example.com"),
            rights_summary=[RightInfo(article="Art. 15", title="Access", description="...")],
        )

        app = _build_app(service)
        client = TestClient(app)
        response = client.get("/api/v1/privacy/policy")

        assert response.status_code == 200
        body = response.json()
        assert body["version"] == "1.0"
        assert any(p["key"] == "core_functionality" for p in body["purposes"])


class TestConsentEndpoints:
    def test_list_consents_returns_purposes(self):
        service = _build_service()
        service.list_consents.return_value = [
            ConsentWithPurpose(
                purpose="core_functionality",
                label="Core functionality",
                description="Required",
                legal_basis="Art. 6(1)(b) GDPR",
                required=True,
                granted=True,
            ),
            ConsentWithPurpose(
                purpose="error_tracking",
                label="Error tracking",
                description="Optional",
                legal_basis="Art. 6(1)(a) GDPR",
                required=False,
                granted=False,
            ),
        ]

        app = _build_app(service)
        client = TestClient(app)
        response = client.get("/api/v1/privacy/consents")

        assert response.status_code == 200
        purposes = {item["purpose"] for item in response.json()}
        assert {"core_functionality", "error_tracking"} <= purposes

    def test_grant_consent_creates_record(self):
        service = _build_service()
        service.grant_consent.return_value = ConsentRecord(
            _key="c1",
            user_key=USER_KEY,
            purpose="error_tracking",
            granted=True,
            granted_at=datetime.now(UTC),
        )

        app = _build_app(service)
        client = TestClient(app)
        response = client.post(
            "/api/v1/privacy/consents",
            json={"purpose": "error_tracking"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["purpose"] == "error_tracking"
        assert body["granted"] is True

    def test_revoke_consent(self):
        service = _build_service()
        service.revoke_consent.return_value = ConsentRecord(
            _key="c1",
            user_key=USER_KEY,
            purpose="error_tracking",
            granted=False,
            revoked_at=datetime.now(UTC),
        )

        app = _build_app(service)
        client = TestClient(app)
        response = client.delete("/api/v1/privacy/consents/error_tracking")

        assert response.status_code == 200
        assert response.json()["granted"] is False


class TestExportEndpoints:
    def test_request_export(self):
        service = _build_service()
        service.request_data_export.return_value = DataExportRequest(
            _key="e1",
            user_key=USER_KEY,
            status="pending",
            requested_at=datetime.now(UTC),
        )

        app = _build_app(service)
        client = TestClient(app)
        response = client.post("/api/v1/privacy/export")

        assert response.status_code == 201
        assert response.json()["status"] == "pending"


class TestErasureEndpoints:
    def test_request_erasure(self):
        service = _build_service()
        service.request_erasure.return_value = ErasureRequest(
            _key="er1",
            user_key=USER_KEY,
            status="scheduled",
            requested_at=datetime.now(UTC),
            soft_deleted_at=datetime.now(UTC),
            hard_delete_scheduled_at=datetime.now(UTC) + timedelta(days=90),
            anonymized_collections=["harvest_batches"],
        )

        app = _build_app(service)
        client = TestClient(app)
        response = client.post(
            "/api/v1/privacy/erasure",
            json={"password": "very-strong-pass"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "scheduled"
        assert "harvest_batches" in body["anonymized_collections"]


class TestRestrictionEndpoints:
    def test_create_restriction(self):
        service = _build_service()
        service.restrict_processing.return_value = ProcessingRestriction(
            _key="r1",
            user_key=USER_KEY,
            scope="analytics",
            reason="purpose_expired",
            created_at=datetime.now(UTC),
        )

        app = _build_app(service)
        client = TestClient(app)
        response = client.post(
            "/api/v1/privacy/restrict",
            json={"scope": "analytics", "reason": "purpose_expired"},
        )

        assert response.status_code == 201
        assert response.json()["scope"] == "analytics"


class TestEmailChangeEndpoints:
    def test_request_email_change(self):
        # ``/privacy/email-change`` is rate-limited per IP with an hourly window
        # (#958), shared under ``testclient`` with every other module that posts
        # here. Without the reset this test depends on how many of them ran
        # first — and the minimal app built below registers no 429 handler, so
        # it would fail as a 500 naming nothing.
        limiter.reset()
        service = _build_service()
        service.request_email_change.return_value = EmailChangeRequest(
            _key="ec1",
            user_key=USER_KEY,
            new_email="new@example.com",
            verification_token_hash="hash",
            status="pending",
            requested_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )

        app = _build_app(service)
        client = TestClient(app)
        response = client.post(
            "/api/v1/privacy/email-change",
            json={"new_email": "new@example.com"},
        )

        assert response.status_code == 201
        assert response.json()["new_email"] == "new@example.com"

    def test_confirm_email_change_no_auth_required(self):
        service = _build_service()
        service.confirm_email_change.return_value = User(
            _key=USER_KEY,
            email="new@example.com",
            display_name="Test User",
        )

        app = _build_app(service)
        # Remove the auth override so we verify the endpoint works without it.
        app.dependency_overrides.pop(get_current_user, None)
        client = TestClient(app)
        response = client.post(
            "/api/v1/privacy/email-change/confirm",
            json={"token": "raw-token-123"},
        )

        assert response.status_code == 200
        assert "updated" in response.json()["message"].lower()
