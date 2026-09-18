"""#1525 SCR-014 — nobody may occupy the address a soft-delete needs.

``UserService.delete_account`` parks a soft-deleted account at
``deleted_<user_key>@deleted.example.com`` (REQ-025 Szenario 3), and ``users.email``
carries a **unique** index (`collections.py`: ``add_persistent_index(fields=["email"],
unique=True)``).

Put together, those two facts are a denial of service on someone else's Art. 17
erasure: register ``deleted_<their key>@deleted.example.com`` and their eventual
account deletion collides on the index. Before #1525 the deletion write raised for a
different reason anyway, so this was unreachable; making the write work made it real,
which is why the guard ships with it rather than after it.

Both address-setting paths are covered — registration and the email-change flow —
because a rule enforced on one of two entrances is the #948 shape.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.domain.models.user import DELETED_EMAIL_DOMAIN, is_tombstone_email, tombstone_email


class TestThePredicate:
    def test_it_matches_the_address_delete_account_writes(self):
        """The predicate and the writer must agree, and not by two literals.

        If they ever disagree the guard is inert while reading correctly — so this
        composes the two production functions rather than restating the domain.
        """
        assert is_tombstone_email(tombstone_email("abc123"))

    @pytest.mark.parametrize(
        "address",
        [
            f"anything@{DELETED_EMAIL_DOMAIN}",
            f"ANYTHING@{DELETED_EMAIL_DOMAIN.upper()}",
            f"  spaced@{DELETED_EMAIL_DOMAIN}  ",
        ],
    )
    def test_it_is_not_escapable_by_case_or_whitespace(self, address: str):
        assert is_tombstone_email(address)

    @pytest.mark.parametrize(
        "address",
        [
            "erika@example.org",
            # A *subdomain* of the reserved domain is a different domain, and a
            # look-alike prefix is not the reserved one either. Pinned so the
            # predicate cannot be widened into refusing ordinary addresses.
            f"erika@nope.{DELETED_EMAIL_DOMAIN}",
            "erika@deleted.example.com.evil.test",
            "erika@notdeleted.example.com",
        ],
    )
    def test_it_leaves_ordinary_addresses_alone(self, address: str):
        assert not is_tombstone_email(address)


def _auth_service():
    from app.domain.engines.login_throttle_engine import LoginThrottleEngine
    from app.domain.engines.password_engine import PasswordEngine
    from app.domain.services.auth_service import AuthService

    user_repo = MagicMock()
    user_repo.get_by_email.return_value = None
    return (
        AuthService(
            user_repo,
            MagicMock(),
            MagicMock(),
            PasswordEngine(),
            MagicMock(),
            LoginThrottleEngine(),
            MagicMock(),
            "http://localhost:5173",
        ),
        user_repo,
    )


class TestRegistrationRefusesTheDomain:
    def test_it_is_rejected(self):
        service, _ = _auth_service()

        with pytest.raises(ValidationError):
            service.register_local(
                tombstone_email("victim-key"),
                "Strong-Enough-2026!",
                "Impersonator",
            )

    def test_it_is_rejected_before_anything_is_looked_up(self):
        """No stored state is read, so the refusal is not an enumeration oracle.

        SEC-H-009 made the duplicate-address branch indistinguishable from a genuine
        registration on purpose. A reserved-domain refusal that ran *after* the lookup
        would answer differently depending on whether the account exists.
        """
        service, user_repo = _auth_service()

        with pytest.raises(ValidationError):
            service.register_local(tombstone_email("victim-key"), "Strong-Enough-2026!", "X")

        user_repo.get_by_email.assert_not_called()

    def test_an_ordinary_address_still_registers(self):
        """The other half: the guard must not refuse everything."""
        service, user_repo = _auth_service()
        user_repo.create.side_effect = lambda user: user

        profile = service.register_local("erika@example.org", "Strong-Enough-2026!", "Erika")

        assert profile.email == "erika@example.org"


class TestTheEmailChangeFlowRefusesTheDomain:
    def _privacy_service(self):
        from app.domain.engines.consent_engine import ConsentEngine
        from app.domain.engines.data_export_engine import DataExportEngine
        from app.domain.engines.erasure_engine import ErasureEngine
        from app.domain.engines.password_engine import PasswordEngine
        from app.domain.engines.token_engine import TokenEngine
        from app.domain.models.user import User
        from app.domain.services.privacy_service import PrivacyService

        user_repo = MagicMock()
        user_repo.get_or_raise.return_value = User(_key="u-1", email="erika@example.org", display_name="Erika")
        user_repo.get_by_email.return_value = None
        return (
            PrivacyService(
                export_repo=MagicMock(),
                consent_repo=MagicMock(),
                restriction_repo=MagicMock(),
                erasure_repo=MagicMock(),
                email_change_repo=MagicMock(),
                user_repo=user_repo,
                refresh_token_repo=MagicMock(),
                data_export_engine=DataExportEngine(),
                erasure_engine=ErasureEngine(),
                consent_engine=ConsentEngine(),
                password_engine=PasswordEngine(),
                # Real, not a mock: `request_email_change` feeds `hash_token`'s result
                # straight into a `str` field of `EmailChangeRequest`, so a mock makes the
                # positive case fail on validation rather than on the rule under test.
                token_engine=TokenEngine(secret_key="unit-test-secret-not-a-credential"),
                email_service=MagicMock(),
                frontend_url="http://localhost:5173",
            ),
            user_repo,
        )

    def test_it_is_rejected(self):
        service, _ = self._privacy_service()

        with pytest.raises(ValidationError):
            service.request_email_change("u-1", tombstone_email("victim-key"))

    def test_an_ordinary_address_is_still_accepted(self):
        service, _ = self._privacy_service()

        service.request_email_change("u-1", "erika.neu@example.org")
