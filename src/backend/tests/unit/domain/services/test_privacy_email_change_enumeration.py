"""``request_email_change`` must not confirm that an address is registered.

The branch for a taken address carried the comment "Generic error to prevent
account enumeration" and then raised ``DuplicateError("User", "email", new_email)``,
which the global handler renders as

    409 {"message": "User with email='<address>' already exists.",
         "details": [{"field": "email",
                      "reason": "Value '<address>' is already taken.", ...}]}

— an explicit existence statement that also mirrors the submitted address back.
The same defect class as #901, on a second surface, hidden behind the same kind
of comment.

These tests assert the property rather than the implementation: the answer for a
taken address must be indistinguishable from the answer for a free one, and the
synthesised request must never become a confirmable record.
"""

from unittest.mock import MagicMock

import pytest
import structlog

from app.common.exceptions import InvalidTokenError
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


def _stored_user() -> User:
    return User(_key=USER_KEY, email=OWN_EMAIL, display_name="Requesting User")


def _foreign_user() -> User:
    return User(_key="9999", email=TAKEN_EMAIL, display_name="Third Party")


def _make_service() -> tuple[PrivacyService, MagicMock, MagicMock]:
    user_repo = MagicMock()
    user_repo.get_or_raise.return_value = _stored_user()
    user_repo.get_by_email.side_effect = lambda email: _foreign_user() if email == TAKEN_EMAIL else None

    email_change_repo = MagicMock()

    def _create(change):  # noqa: ANN001, ANN202 - repo stub
        change.key = "ec-1"
        return change

    email_change_repo.create.side_effect = _create
    email_change_repo.get_by_token_hash.return_value = None

    email_service = MagicMock()
    service = PrivacyService(
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
        email_service=email_service,
        frontend_url="http://localhost:5173",
    )
    return service, email_change_repo, email_service


class TestTakenAddressAnswersLikeAFreeOne:
    def test_no_error_is_raised(self) -> None:
        service, _, _ = _make_service()

        change = service.request_email_change(USER_KEY, TAKEN_EMAIL)

        assert change.status == "pending"
        assert str(change.new_email) == TAKEN_EMAIL

    def test_response_matches_a_free_address_field_for_field(self) -> None:
        service, _, _ = _make_service()

        taken = service.request_email_change(USER_KEY, TAKEN_EMAIL).model_dump()
        free = service.request_email_change(USER_KEY, FREE_EMAIL).model_dump()

        # ``key`` and the timestamps differ between any two requests, and
        # ``new_email`` echoes what was submitted. Everything the API returns
        # beyond that must be identical — ``EmailChangeResponse`` exposes
        # key/new_email/status/requested_at/expires_at/confirmed_at.
        volatile = {"key", "new_email", "requested_at", "expires_at", "verification_token_hash"}
        assert {k: v for k, v in taken.items() if k not in volatile} == {
            k: v for k, v in free.items() if k not in volatile
        }
        assert taken["key"] != free["key"]

    def test_decoy_key_is_not_stable_across_requests(self) -> None:
        """A fixed decoy key would itself fingerprint the address."""
        service, _, _ = _make_service()

        first = service.request_email_change(USER_KEY, TAKEN_EMAIL)
        second = service.request_email_change(USER_KEY, TAKEN_EMAIL)

        assert first.key != second.key


class TestNothingIsPersistedForATakenAddress:
    def test_no_request_is_written(self) -> None:
        service, email_change_repo, _ = _make_service()

        service.request_email_change(USER_KEY, TAKEN_EMAIL)

        email_change_repo.create.assert_not_called()

    def test_free_address_still_writes_one(self) -> None:
        """Guards against 'fixed' by never persisting anything at all."""
        service, email_change_repo, _ = _make_service()

        service.request_email_change(USER_KEY, FREE_EMAIL)

        email_change_repo.create.assert_called_once()

    def test_synthesised_request_cannot_be_confirmed(self) -> None:
        """Confirming it would move the account onto an address someone else owns."""
        service, _, _ = _make_service()
        service.request_email_change(USER_KEY, TAKEN_EMAIL)

        with pytest.raises(InvalidTokenError):
            service.confirm_email_change("any-token-the-caller-might-try")


class TestNotificationGoesToTheTargetNotTheRequester:
    def test_no_verification_token_is_mailed_to_the_taken_address(self) -> None:
        service, _, email_service = _make_service()

        service.request_email_change(USER_KEY, TAKEN_EMAIL)

        email_service.send_verification_email.assert_not_called()

    def test_target_address_is_told_what_was_attempted(self) -> None:
        service, _, email_service = _make_service()

        service.request_email_change(USER_KEY, TAKEN_EMAIL)

        email_service.send_notification_email.assert_called_once()
        kwargs = email_service.send_notification_email.call_args.kwargs
        assert kwargs["to_email"] == TAKEN_EMAIL
        # The requester is a stranger to the recipient; echoing their chosen
        # display name would turn this notice into a message channel.
        assert "Requesting User" not in kwargs["html_body"]
        assert OWN_EMAIL not in kwargs["html_body"]

    def test_free_address_gets_the_verification_mail_instead(self) -> None:
        service, _, email_service = _make_service()

        service.request_email_change(USER_KEY, FREE_EMAIL)

        email_service.send_verification_email.assert_called_once()
        email_service.send_notification_email.assert_not_called()

    def test_unimplemented_notification_channel_does_not_change_the_answer(self) -> None:
        service, _, email_service = _make_service()
        email_service.send_notification_email.side_effect = NotImplementedError

        change = service.request_email_change(USER_KEY, TAKEN_EMAIL)

        assert change.status == "pending"


class TestLoggingAndSideChannels:
    def test_log_line_carries_a_digest_not_the_address(self) -> None:
        service, _, _ = _make_service()

        with structlog.testing.capture_logs() as logs:
            service.request_email_change(USER_KEY, TAKEN_EMAIL)

        events = [entry for entry in logs if entry["event"] == "privacy_email_change_suppressed"]
        assert len(events) == 1
        assert TAKEN_EMAIL not in str(events[0])
        assert events[0]["new_email_sha256"]

    def test_token_is_still_generated_so_the_branch_is_not_faster(self) -> None:
        service, _, _ = _make_service()
        token_engine = MagicMock(wraps=service._token_engine)  # noqa: SLF001
        service._token_engine = token_engine  # noqa: SLF001

        service.request_email_change(USER_KEY, TAKEN_EMAIL)

        assert token_engine.hash_token.call_count == 1
