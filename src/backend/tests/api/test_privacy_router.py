"""API smoke tests for the REQ-025 privacy router.

Driven through the **real** application, as the other privacy modules are, with
only ``app.main``'s datastore setup patched out. The module used to mount the
router on a bare ``FastAPI()`` "to keep DB-dependent middleware out of the
picture" — but that app registered neither ``app_error_handler`` nor slowapi's
``RateLimitExceeded`` handler, so every error this router can raise came out as a
bare 500 naming nothing (#989). ``/privacy/email-change`` carries an hourly limit
whose counters are process-global, so a 429 here is reachable in principle, and
"500, no message" is the worst possible thing for whoever trips it to read.

Keeping the datastore out and keeping the app's error contract are not in
conflict: patching the connection setup does the first without giving up the
second.
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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


@pytest.fixture
def service() -> MagicMock:
    service = MagicMock()
    service._consent_engine = ConsentEngine()  # noqa: SLF001 — used by router
    return service


@pytest.fixture
def privacy_app(service: MagicMock) -> Iterator[FastAPI]:
    """The real app, with the privacy service and the caller faked out."""
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_privacy_service] = lambda: service
        app.dependency_overrides[get_current_user] = lambda: User(
            _key=USER_KEY,
            email="user@example.com",
            display_name="Test User",
            is_active=True,
        )
        try:
            yield app
        finally:
            app.dependency_overrides.pop(get_privacy_service, None)
            app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client(privacy_app: FastAPI) -> TestClient:
    return TestClient(privacy_app, raise_server_exceptions=False)


@pytest.fixture
def anonymous_client(privacy_app: FastAPI) -> TestClient:
    """Same app without the ``get_current_user`` override — nobody is logged in."""
    privacy_app.dependency_overrides.pop(get_current_user, None)
    return TestClient(privacy_app, raise_server_exceptions=False)


class TestPrivacyPolicy:
    def test_get_policy_is_public(self, client: TestClient, service: MagicMock) -> None:
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

        response = client.get("/api/v1/privacy/policy")

        assert response.status_code == 200
        body = response.json()
        assert body["version"] == "1.0"
        assert any(p["key"] == "core_functionality" for p in body["purposes"])


class TestConsentEndpoints:
    def test_list_consents_returns_purposes(self, client: TestClient, service: MagicMock) -> None:
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

        response = client.get("/api/v1/privacy/consents")

        assert response.status_code == 200
        purposes = {item["purpose"] for item in response.json()}
        assert {"core_functionality", "error_tracking"} <= purposes

    def test_grant_consent_creates_record(self, client: TestClient, service: MagicMock) -> None:
        service.grant_consent.return_value = ConsentRecord(
            _key="c1",
            user_key=USER_KEY,
            purpose="error_tracking",
            granted=True,
            granted_at=datetime.now(UTC),
        )

        response = client.post(
            "/api/v1/privacy/consents",
            json={"purpose": "error_tracking"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["purpose"] == "error_tracking"
        assert body["granted"] is True

    def test_revoke_consent(self, client: TestClient, service: MagicMock) -> None:
        service.revoke_consent.return_value = ConsentRecord(
            _key="c1",
            user_key=USER_KEY,
            purpose="error_tracking",
            granted=False,
            revoked_at=datetime.now(UTC),
        )

        response = client.delete("/api/v1/privacy/consents/error_tracking")

        assert response.status_code == 200
        assert response.json()["granted"] is False


class TestExportEndpoints:
    def test_request_export(self, client: TestClient, service: MagicMock) -> None:
        service.request_data_export.return_value = DataExportRequest(
            _key="e1",
            user_key=USER_KEY,
            status="pending",
            requested_at=datetime.now(UTC),
        )

        response = client.post("/api/v1/privacy/export")

        assert response.status_code == 201
        assert response.json()["status"] == "pending"


class TestErasureEndpoints:
    def test_request_erasure(self, client: TestClient, service: MagicMock) -> None:
        service.request_erasure.return_value = ErasureRequest(
            _key="er1",
            user_key=USER_KEY,
            status="scheduled",
            requested_at=datetime.now(UTC),
            soft_deleted_at=datetime.now(UTC),
            hard_delete_scheduled_at=datetime.now(UTC) + timedelta(days=90),
            anonymized_collections=["harvest_batches"],
        )

        response = client.post(
            "/api/v1/privacy/erasure",
            json={"password": "very-strong-pass"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "scheduled"
        assert "harvest_batches" in body["anonymized_collections"]


class TestRestrictionEndpoints:
    def test_create_restriction(self, client: TestClient, service: MagicMock) -> None:
        service.restrict_processing.return_value = ProcessingRestriction(
            _key="r1",
            user_key=USER_KEY,
            scope="analytics",
            reason="purpose_expired",
            created_at=datetime.now(UTC),
        )

        response = client.post(
            "/api/v1/privacy/restrict",
            json={"scope": "analytics", "reason": "purpose_expired"},
        )

        assert response.status_code == 201
        assert response.json()["scope"] == "analytics"


class TestEmailChangeEndpoints:
    def test_request_email_change(self, client: TestClient, service: MagicMock) -> None:
        service.request_email_change.return_value = EmailChangeRequest(
            _key="ec1",
            user_key=USER_KEY,
            new_email="new@example.com",
            verification_token_hash="hash",
            status="pending",
            requested_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )

        response = client.post(
            "/api/v1/privacy/email-change",
            json={"new_email": "new@example.com"},
        )

        assert response.status_code == 201
        assert response.json()["new_email"] == "new@example.com"

    def test_exhausted_budget_answers_429_not_a_bare_500(self, client: TestClient, service: MagicMock) -> None:
        """What the old minimal app could not say (#989).

        The limit itself is asserted in ``test_privacy_email_change_rate_limit``;
        what this pins is that *this* app renders the refusal — before, the same
        ``RateLimitExceeded`` reached no handler and became a 500 with no
        ``error_code`` and no message, from which nothing could be diagnosed.
        """
        from app.config.settings import settings

        service.request_email_change.return_value = EmailChangeRequest(
            _key="ec1",
            user_key=USER_KEY,
            new_email="new@example.com",
            verification_token_hash="hash",
            status="pending",
            requested_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        budget = int(settings.rate_limit_email_change.split("/")[0])

        statuses = [
            client.post("/api/v1/privacy/email-change", json={"new_email": f"new-{i}@example.com"}).status_code
            for i in range(budget + 1)
        ]

        assert statuses[-1] == 429
        assert 500 not in statuses

    def test_confirm_email_change_no_auth_required(self, anonymous_client: TestClient, service: MagicMock) -> None:
        service.confirm_email_change.return_value = User(
            _key=USER_KEY,
            email="new@example.com",
            display_name="Test User",
        )

        response = anonymous_client.post(
            "/api/v1/privacy/email-change/confirm",
            json={"token": "raw-token-123"},
        )

        assert response.status_code == 200
        assert "updated" in response.json()["message"].lower()
