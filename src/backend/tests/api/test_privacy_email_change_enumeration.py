"""``POST /api/v1/privacy/email-change`` may not disclose that an address is taken.

The service-level guarantee is covered in
``tests/unit/domain/services/test_privacy_email_change_enumeration.py``. This
module asserts it on the wire, through the real global error handler — which is
where the disclosure was actually readable:

    409 {"error_code": "DUPLICATE_ENTRY",
         "message": "User with email='<address>' already exists.",
         "details": [{"field": "email",
                      "reason": "Value '<address>' is already taken."}]}

A minimal app that mounts the router without ``app_error_handler`` would have
rendered that as a 500 and hidden exactly the part that leaked.
"""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_privacy_service
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.user import User
from app.domain.services.privacy_service import PrivacyService

USER_KEY = "u1"
OWN_EMAIL = "owner@example.com"
FREE_EMAIL = "free@example.com"
TAKEN_EMAIL = "somebody-else@example.com"

#: Differ between any two requests and therefore carry nothing about the account.
_VOLATILE_FIELDS = frozenset({"key", "new_email", "requested_at", "expires_at"})


def _privacy_service() -> PrivacyService:
    user_repo = MagicMock()
    user_repo.get_or_raise.return_value = User(_key=USER_KEY, email=OWN_EMAIL, display_name="Requesting User")
    user_repo.get_by_email.side_effect = lambda email: (
        User(_key="9999", email=TAKEN_EMAIL, display_name="Third Party") if email == TAKEN_EMAIL else None
    )

    email_change_repo = MagicMock()

    def _create(change):  # noqa: ANN001, ANN202 - repo stub
        change.key = "ec-1"
        return change

    email_change_repo.create.side_effect = _create

    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=email_change_repo,
        user_repo=user_repo,
        refresh_token_repo=MagicMock(),
        data_export_engine=DataExportEngine(),
        erasure_engine=ErasureEngine(),
        consent_engine=ConsentEngine(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_privacy_service] = _privacy_service
        app.dependency_overrides[get_current_user] = lambda: User(
            _key=USER_KEY,
            email=OWN_EMAIL,
            display_name="Requesting User",
            is_active=True,
        )
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_privacy_service, None)
            app.dependency_overrides.pop(get_current_user, None)


def _request_change(client: TestClient, new_email: str):  # noqa: ANN202 - httpx Response
    return client.post("/api/v1/privacy/email-change", json={"new_email": new_email})


class TestEmailChangeIsNotAnEnumerationOracle:
    def test_taken_address_answers_201_like_a_free_one(self, client: TestClient) -> None:
        taken = _request_change(client, TAKEN_EMAIL)
        free = _request_change(client, FREE_EMAIL)

        assert taken.status_code == free.status_code == 201
        assert taken.json().keys() == free.json().keys()
        assert {k: v for k, v in taken.json().items() if k not in _VOLATILE_FIELDS} == {
            k: v for k, v in free.json().items() if k not in _VOLATILE_FIELDS
        }
        assert taken.json()["new_email"] == TAKEN_EMAIL

    def test_response_never_states_that_the_address_exists(self, client: TestClient) -> None:
        body = _request_change(client, TAKEN_EMAIL).text

        assert "already exists" not in body
        assert "already taken" not in body
        assert "DUPLICATE_ENTRY" not in body

    def test_own_current_address_is_still_rejected(self, client: TestClient) -> None:
        """Not an oracle — the caller is telling us an address they already own."""
        response = _request_change(client, OWN_EMAIL)

        assert response.status_code == 422
        assert "must differ" in response.json()["message"]
