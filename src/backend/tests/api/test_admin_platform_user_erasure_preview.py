"""API tests for #1961 — ``GET /admin/platform/users/{key}/erasure-preview``.

The platform-admin counterpart of ``GET /privacy/erasure-preview`` (REQ-025
AK-FK-06): what deleting another account takes with it. Driven through the real
router, the real platform-admin guard, the real :class:`PrivacyService` and the
real :class:`TenantService` over the in-memory repositories of
``test_erasure_invitations_and_late_join`` — not a ``MagicMock`` that would answer
whatever the route asks.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.platform import router as mod
from app.common.auth import get_current_user, get_is_platform_admin
from app.common.dependencies import get_privacy_service, get_user_service
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.user import User
from tests.support.privacy_doubles import FakeErasureRepo
from tests.unit.domain.services.test_erasure_invitations_and_late_join import (  # noqa: F401 - the autouse salt fixture
    FRIEND,
    OWNER,
    PERSONAL,
    Tenants,
    _log_pseudonym_salt,
    _member,
    _personal_tenant,
    _privacy,
)
from tests.unit.domain.services.test_erasure_together_notice_and_preview import (
    FRIEND_EMAIL,
    OTHER,
    OTHER_EMAIL,
    _users,
)

ADMIN = "u-admin"
URL = "/api/v1/admin/platform/users/{key}/erasure-preview"


def _client(*, admin: bool) -> TestClient:
    # The target's personal tenant has two other members; a foreign personal tenant has one more.
    tenants = Tenants(
        _personal_tenant(PERSONAL, owner=OWNER),
        _personal_tenant("t-foreign", owner="u-foreign"),
        members=[
            _member(OWNER),
            _member(FRIEND),
            _member(OTHER),
            _member("u-foreign", "t-foreign"),
            _member("u-spy", "t-foreign"),
        ],
    )
    privacy, _ = _privacy(tenants, FakeErasureRepo(), user_repo=_users((FRIEND, FRIEND_EMAIL), (OTHER, OTHER_EMAIL)))
    users = MagicMock()

    def _get_user(key: str) -> User:
        if key not in (OWNER, "u-foreign", ADMIN):
            raise NotFoundError("User", key)
        return User(_key=key, email=f"{key}@example.org", display_name=key)

    users.get_user.side_effect = _get_user
    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    # The real ``require_platform_admin`` stays in place; only what it reads is decided here.
    app.dependency_overrides[get_current_user] = lambda: User(_key=ADMIN, email="a@example.org", display_name="Admin")
    app.dependency_overrides[get_is_platform_admin] = lambda: admin
    app.dependency_overrides[get_user_service] = lambda: users
    app.dependency_overrides[get_privacy_service] = lambda: privacy
    return TestClient(app)


@pytest.fixture
def admin_client() -> TestClient:
    return _client(admin=True)


class TestTheAdminSeesWhatTheDeletionTakesAlong:
    def test_it_returns_the_targets_tenant_with_a_count_of_the_others(self, admin_client: TestClient):
        response = admin_client.get(URL.format(key=OWNER))

        assert response.status_code == 200
        assert response.json() == {
            "personal_tenants": [{"name": "Garden", "other_member_count": 2}],
            "organizations": [],  # #2134
        }

    def test_it_has_the_shape_of_the_self_service_preview(self, admin_client: TestClient):
        from app.api.v1.privacy.schemas import ErasurePreviewResponse

        body = admin_client.get(URL.format(key=OWNER)).json()

        assert ErasurePreviewResponse.model_validate(body).personal_tenants[0].other_member_count == 2

    def test_it_carries_nothing_about_who_the_other_members_are(self, admin_client: TestClient):
        shown = admin_client.get(URL.format(key=OWNER)).text

        assert not any(leak in shown for leak in (FRIEND, OTHER, FRIEND_EMAIL, OTHER_EMAIL, "role", "email", "u-"))

    def test_it_is_scoped_to_the_target_and_shows_no_other_tenant(self, admin_client: TestClient):
        shown = admin_client.get(URL.format(key=OWNER)).text

        assert "t-foreign" not in shown and "u-foreign" not in shown and "u-spy" not in shown

    def test_the_foreign_target_gets_its_own_answer_not_the_first_ones(self, admin_client: TestClient):
        body = admin_client.get(URL.format(key="u-foreign")).json()

        assert body == {"personal_tenants": [{"name": "Garden", "other_member_count": 1}], "organizations": []}

    def test_an_account_without_a_personal_tenant_answers_an_empty_list(self, admin_client: TestClient):
        assert admin_client.get(URL.format(key=ADMIN)).json() == {"personal_tenants": [], "organizations": []}

    def test_an_unknown_account_is_404(self, admin_client: TestClient):
        assert admin_client.get(URL.format(key="ghost")).status_code == 404


class TestOnlyAPlatformAdminMayAsk:
    def test_a_non_admin_is_refused_and_learns_nothing(self):
        response = _client(admin=False).get(URL.format(key=OWNER))

        assert response.status_code == 403
        assert "Garden" not in response.text and "other_member_count" not in response.text
