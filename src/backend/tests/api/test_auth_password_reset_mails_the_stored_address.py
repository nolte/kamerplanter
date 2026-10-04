"""The reset link goes to the account's stored address, not to the typed spelling (#2060).

``AuthService.request_password_reset`` finds the account with
``LOWER(doc.email) == LOWER(@email)`` and mailed the link to the address the
caller typed. RFC 5321 lets a mail server treat the local part
case-sensitively, so a link for ``Owner.Name@…`` could be delivered to a
different mailbox ``owner.name@…`` that the caller controls. The resend path
(``resend_verification_email``) and the login refusal (#2046) already mail
``user.email``; the reset path does now too.

Through the real route: a differently cased request reaches the mail double
with the stored spelling, byte for byte.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.domain.models.user import User
from tests.api import test_auth_password_reset_budget as reset_flow

STORED = "Owner.Name@example.com"

_client = contextmanager(reset_flow._client)


class _RawMail(reset_flow._CountingMail):
    """Records the recipient exactly as the service hands it over."""

    def __init__(self, order: list[str]) -> None:
        super().__init__(order)
        self.recipients: list[str] = []

    def send_password_reset_email(self, to_email: str, token: str, frontend_url: str) -> None:
        self.recipients.append(to_email)
        super().send_password_reset_email(to_email, token, frontend_url)


@pytest.fixture
def world() -> reset_flow._World:
    world = reset_flow._World()
    world.mail = _RawMail(world.order)
    world.repo.users[STORED.lower()] = User(
        _key="2000099", email=STORED, display_name="Owner", password_hash=reset_flow._PASSWORD_HASH
    )
    return world


@pytest.fixture
def client(world: reset_flow._World) -> Iterator[TestClient]:
    with _client(world) as test_client:
        yield test_client


@pytest.mark.parametrize("typed", ["owner.name@example.com", "OWNER.NAME@EXAMPLE.COM", "  oWNER.nAME@example.com "])
def test_the_link_goes_to_the_stored_spelling(world: reset_flow._World, client: TestClient, typed: str) -> None:
    response = client.post(reset_flow._ROUTE, json={"email": typed})

    assert response.status_code == 200
    assert world.mail.recipients == [STORED]  # type: ignore[attr-defined]
