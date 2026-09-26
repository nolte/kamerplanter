"""#1841 — the e-mail change is an account-takeover step and passes the one step-up.

``POST /privacy/email-change`` depended on ``get_current_user`` alone: a hijacked
session — or an API key, which ``get_current_user`` resolves to its human owner —
moved the account onto an address the attacker reads, and from there a password
reset took the account for good. The owner was told nothing (REQ-025 AK-06 asks
for an info mail to the old address; neither the request nor the confirmation sent one).

The rule now (REQ-023 §3.9, the verifier every irreversible account action passes):

* a signed-in session of a person — an API key or a service account is 403;
* the current password when the account has one (401 missing or wrong), the mailed
  one-time code when it has none (401 ``STEP_UP_CODE_REQUIRED`` without it, #1815);
* throttled in the same budget as every other step-up (429 ``STEP_UP_LOCKED``);
* checked **before** anything else — before the address is validated, before the
  "already taken" branch, before any mail — so the route is no oracle without it;
* after a passed step-up, the account's current address is told a change to the new
  address was requested — in the genuine and the suppressed-taken branch alike, so
  the two stay indistinguishable — and after the confirmation the old address is
  told the address changed and every session was revoked.

The requests run the real privacy and users routers and the real services over
in-memory doubles. Every test uses a fresh account key, so the process-wide
in-memory throttle and code tiers never carry state from one test into another.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.auth.router import limiter
from app.api.v1.auth.router import router as auth_router
from app.api.v1.privacy.router import router as privacy_router
from app.api.v1.users.router import router as users_router
from app.common.auth import get_current_user
from app.common.dependencies import get_auth_service, get_privacy_service
from app.common.exceptions import DuplicateError, KamerplanterError, NotFoundError
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.privacy import EmailChangeRequest
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.privacy_service import PrivacyService

# Probe credentials are assembled at runtime: a literal shaped like one trips the
# secret scanner (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)
WRONG_PASSWORD = PASSWORD[::-1]
API_KEY = "kp_" + "x" * 24
TAKEN = "somebody-else@example.org"
ROUTE = "/api/v1/privacy/email-change"


@pytest.fixture(autouse=True)
def _limiter_off(monkeypatch: pytest.MonkeyPatch):
    """The per-address hourly e-mail-change budget is asserted elsewhere; here the step-up is under test."""
    limiter.reset()
    monkeypatch.setattr(limiter, "enabled", False)
    yield
    limiter.reset()


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


class _Users:
    def __init__(self, *users: User) -> None:
        self.rows = {u.key: u for u in users}
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def get_or_raise(self, key: str) -> User:
        if key not in self.rows:
            raise NotFoundError("User", key)
        return self.rows[key]

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    def get_by_password_reset_token(self, token: str) -> User | None:
        return next((u for u in self.rows.values() if u.password_reset_token == token), None)

    def create(self, user: User) -> User:
        if self.get_by_email(user.email) is not None:
            raise DuplicateError("User", "email", user.email)
        user.key = user.key or f"new-{len(self.rows) + 1}"
        self.rows[user.key] = user
        return user

    def move_email(self, key: str, expected_email: str, fields: dict[str, Any]) -> User | None:
        """Compare-and-set on the address, with the unique index on ``users.email``."""
        if key not in self.rows or self.rows[key].email.lower() != str(expected_email).lower():
            return None
        new_email = fields.get("email")
        holder = self.get_by_email(new_email) if new_email else None
        if holder is not None and holder.key != key:
            raise DuplicateError("User", "email", new_email)
        return self.update_fields(key, fields)

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        # Validated like the Arango repository's re-read, so an ISO timestamp the
        # service writes (``password_reset_expires``) comes back as a datetime.
        self.writes.append((key, dict(fields)))
        self.rows[key] = User.model_validate({**self.rows[key].model_dump(by_alias=True), **fields})
        return self.rows[key]


class _EmailChanges:
    """``IEmailChangeRepository`` over a dict."""

    def __init__(self) -> None:
        self.rows: dict[str, EmailChangeRequest] = {}

    def create(self, change: EmailChangeRequest) -> EmailChangeRequest:
        change.key = f"ec-{len(self.rows) + 1}"
        self.rows[change.key] = change
        return change

    def get_by_token_hash(self, token_hash: str) -> EmailChangeRequest | None:
        return next((c for c in self.rows.values() if c.verification_token_hash == token_hash), None)

    def update(self, key: str, change: EmailChangeRequest) -> EmailChangeRequest:
        # Stored and read back through validation, as the Arango repository does:
        # a status the model does not know must fail here, not only in production.
        # And in merge mode, as that repository writes (``_update_is_full_replace``
        # is False): a ``None`` is dropped and the stored value survives (#1848).
        incoming = {k: v for k, v in change.model_dump(by_alias=True).items() if v is not None}
        stored = self.rows[key].model_dump(by_alias=True) if key in self.rows else {}
        self.rows[key] = EmailChangeRequest.model_validate({**stored, **incoming})
        return self.rows[key]

    def clear_fields(self, key: str, fields: dict) -> None:
        """What an AQL ``UPDATE ... OPTIONS { keepNull: true }`` does: the named fields become null."""
        self.rows[key] = EmailChangeRequest.model_validate({**self.rows[key].model_dump(by_alias=True), **fields})

    def get_by_revert_token_hash(self, token_hash: str) -> EmailChangeRequest | None:
        return next((c for c in self.rows.values() if c.revert_token_hash == token_hash), None)

    def expire_old(self, now_iso: str) -> int:
        from datetime import datetime

        now = datetime.fromisoformat(now_iso)
        expired = [k for k, c in self.rows.items() if c.status == "pending" and c.expires_at < now]
        for key in expired:
            self.update(key, self.rows[key].model_copy(update={"status": "expired"}))
        return len(expired)

    def close_revert_windows(self, now_iso: str) -> int:
        from datetime import datetime

        now = datetime.fromisoformat(now_iso)
        closed = 0
        for key, change in list(self.rows.items()):
            if change.revert_token_hash and (change.revert_expires_at is None or change.revert_expires_at < now):
                self.clear_fields(key, {"previous_email": None, "revert_token_hash": None, "revert_expires_at": None})
                closed += 1
        return closed

    #: NFR-011 R-07 (#1800) — mirrors ``ArangoEmailChangeRepository.delete_expired_unconfirmed``.
    _UNCONFIRMED_STATUSES = ("pending", "expired", "cancelled")

    def delete_expired_unconfirmed(self, now_iso: str) -> int:
        from datetime import datetime

        now = datetime.fromisoformat(now_iso)
        due = [
            key
            for key, change in self.rows.items()
            if change.status in self._UNCONFIRMED_STATUSES and (change.expires_at is None or change.expires_at < now)
        ]
        for key in due:
            del self.rows[key]
        return len(due)

    #: NFR-011 R-07b (#1800) — mirrors ``ArangoEmailChangeRepository.delete_confirmed_past_revert_window``.
    _CONFIRMED_STATUSES = ("confirmed", "reverted", "superseded")

    def delete_confirmed_past_revert_window(self, now_iso: str) -> int:
        from datetime import datetime

        now = datetime.fromisoformat(now_iso)
        due = [
            key
            for key, change in self.rows.items()
            if change.status in self._CONFIRMED_STATUSES
            and (
                change.revert_token_hash is None
                or (change.revert_expires_at is not None and change.revert_expires_at < now)
            )
        ]
        for key in due:
            del self.rows[key]
        return len(due)

    def claim_status(self, key: str, from_status: str, to_status: str, now_iso: str) -> bool:
        """Compare-and-set on the status, as the Arango ``UPDATE ... FILTER status == @from`` does.

        Claiming ``confirmed`` stamps ``confirmed_at`` in the same write, as the AQL does.
        """
        row = self.rows.get(key)
        if row is None or row.status != from_status:
            return False
        update: dict[str, Any] = {"status": to_status}
        if to_status == "confirmed":
            update["confirmed_at"] = now_iso
        self.rows[key] = EmailChangeRequest.model_validate({**row.model_dump(by_alias=True), **update})
        return True

    def record_confirmation(
        self,
        key: str,
        *,
        previous_email: str,
        revert_token_hash: str,
        revert_expires_at_iso: str,
        now_iso: str,
    ) -> bool:
        row = self.rows.get(key)
        if row is None or row.status != "confirmed":
            return False
        self.rows[key] = EmailChangeRequest.model_validate(
            {
                **row.model_dump(by_alias=True),
                "previous_email": previous_email,
                "revert_token_hash": revert_token_hash,
                "revert_expires_at": revert_expires_at_iso,
            }
        )
        return True

    def find_revert_reservation(self, email: str, now_iso: str) -> EmailChangeRequest | None:
        from datetime import datetime

        now = datetime.fromisoformat(now_iso)
        return next(
            (
                c
                for c in self.rows.values()
                if c.status == "confirmed"
                and c.previous_email is not None
                and str(c.previous_email).lower() == email.lower()
                and c.revert_expires_at is not None
                and c.revert_expires_at > now
            ),
            None,
        )

    def supersede_confirmed_after(self, user_key: str, confirmed_after_iso: str, now_iso: str) -> int:
        from datetime import datetime

        after = datetime.fromisoformat(confirmed_after_iso)
        later = [
            k
            for k, c in self.rows.items()
            if c.user_key == user_key and c.status == "confirmed" and c.confirmed_at and c.confirmed_at > after
        ]
        for key in later:
            self.rows[key] = EmailChangeRequest.model_validate(
                {**self.rows[key].model_dump(by_alias=True), "status": "superseded"}
            )
        return len(later)

    def list_pending_for_user(self, user_key: str) -> list[EmailChangeRequest]:
        # A copy, as the Arango repository returns fresh documents: a caller that
        # mutates the result without writing it back must not change the store.
        return [c.model_copy() for c in self.rows.values() if c.user_key == user_key and c.status == "pending"]


class _Providers:
    """``IAuthProviderRepository`` over a list — the links the revert may drop (#1848)."""

    def __init__(self) -> None:
        self.rows: list[Any] = []
        self.deleted: list[str] = []

    def list_by_user(self, user_key: str) -> list[Any]:
        return [p for p in self.rows if p.user_key == user_key and p.key not in self.deleted]

    def delete(self, key: str) -> bool:
        self.deleted.append(key)
        return True


class _ApiKeys:
    """``IApiKeyRepository`` over a list — the keys the revert may revoke (#1848)."""

    def __init__(self) -> None:
        self.rows: list[Any] = []
        self.revoked: list[str] = []

    def list_by_user(self, user_key: str) -> list[Any]:
        return [k for k in self.rows if k.user_key == user_key]

    def revoke(self, key: str) -> bool:
        self.revoked.append(key)
        return True


class _World:
    def __init__(self, *, password_hash: str | None = PASSWORD_HASH, account_type: str = "human") -> None:
        self.key = f"owner-{uuid.uuid4().hex[:12]}"
        self.email = f"{self.key}@example.org"
        self.new_email = f"new-{self.key}@example.org"
        owner = User.model_validate(
            {
                "_key": self.key,
                "email": self.email,
                "display_name": "Owner",
                "password_hash": password_hash,
                "account_type": account_type,
            }
        )
        other = User.model_validate({"_key": f"other-{self.key}", "email": TAKEN, "display_name": "Other"})
        self.users = _Users(owner, other)
        self.changes = _EmailChanges()
        self.providers = _Providers()
        self.api_keys = _ApiKeys()
        self.privacy_mail = MagicMock()
        self.auth_mail = MagicMock()
        self.refresh_tokens = MagicMock()
        self.privacy = PrivacyService(
            export_repo=MagicMock(),
            consent_repo=MagicMock(),
            restriction_repo=MagicMock(),
            erasure_repo=MagicMock(),
            email_change_repo=self.changes,
            user_repo=self.users,
            refresh_token_repo=self.refresh_tokens,
            data_export_engine=DataExportEngine(),
            erasure_engine=ErasureEngine(),
            consent_engine=ConsentEngine(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            email_service=self.privacy_mail,
            frontend_url="https://app.test",
            reference_index_store=NoopReferenceIndexStore(),
            auth_provider_repo=self.providers,
            api_key_repo=self.api_keys,
        )
        self.auth = AuthService(
            user_repo=self.users,
            auth_provider_repo=MagicMock(),
            refresh_token_repo=self.refresh_tokens,
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=self.auth_mail,
            frontend_url="https://app.test",
            email_change_repo=self.changes,
        )

    def client(self) -> TestClient:
        app = FastAPI()
        app.include_router(privacy_router, prefix="/api/v1")
        app.include_router(users_router, prefix="/api/v1")
        app.include_router(auth_router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.users.rows[self.key]
        app.dependency_overrides[get_privacy_service] = lambda: self.privacy
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        return TestClient(app, raise_server_exceptions=False)

    def post(self, path: str, body: dict[str, Any] | None, *, bearer: str | None = None, ip: str = "198.51.100.7"):  # noqa: ANN201
        headers = {"X-Forwarded-For": ip}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        client = self.client()
        if body is None:
            return client.post(path, headers=headers)
        return client.post(path, json=body, headers=headers)

    def change(self, new_email: str | None = None, **step_up: Any):  # noqa: ANN201
        return self.post(ROUTE, {"new_email": new_email or self.new_email, **step_up})

    def issue_code(self) -> str:
        resp = self.post("/api/v1/users/me/step-up-code", {"action": "email_change"})
        assert resp.status_code == 202, resp.text
        return self.auth_mail.send_step_up_code_email.call_args.kwargs["code"]

    # ── what happened ────────────────────────────────────────────────────

    def nothing_happened(self) -> bool:
        return (
            not self.changes.rows
            and not self.privacy_mail.method_calls
            and not self.users.writes
            and self.users.rows[self.key].email == self.email
        )

    def notices_to(self, address: str) -> list[dict[str, Any]]:
        return [
            c.kwargs
            for c in self.privacy_mail.send_notification_email.call_args_list
            if c.kwargs.get("to_email") == address
        ]


# ── who, and with what ──────────────────────────────────────────────────────


def test_an_api_key_cannot_change_the_e_mail_even_with_the_password() -> None:
    world = _World()

    resp = world.post(ROUTE, {"new_email": world.new_email, "password": PASSWORD}, bearer=API_KEY)

    assert resp.status_code == 403, resp.text
    assert world.nothing_happened()


def test_a_service_account_cannot_change_its_e_mail() -> None:
    world = _World(password_hash=None, account_type="service")

    resp = world.change()

    assert resp.status_code == 403, resp.text
    assert world.nothing_happened()


def test_a_missing_password_is_refused() -> None:
    world = _World()

    resp = world.change()

    assert resp.status_code == 401, resp.text
    assert world.nothing_happened()


def test_a_wrong_password_is_refused() -> None:
    world = _World()

    resp = world.change(password=WRONG_PASSWORD)

    assert resp.status_code == 401, resp.text
    assert world.nothing_happened()


def test_the_step_up_runs_before_the_address_is_looked_up() -> None:
    """Without the step-up the route answers the same for a taken and a free address.

    Only the *lookup* sits behind the step-up — it is what could tell a taken
    address from a free one. The stateless checks (the own address, the reserved
    tombstone domain) run first (/code-review of #1862): they reveal nothing the
    requester did not type, and refusing them early spends no code or attempt.
    """
    world = _World()

    answers = {
        address: world.change(address, password=WRONG_PASSWORD).status_code for address in (TAKEN, world.new_email)
    }

    assert set(answers.values()) == {401}, answers
    assert world.nothing_happened()


@pytest.mark.parametrize("address_of", [lambda w: w.email, lambda w: "x@deleted.example.com"])
def test_a_stateless_refusal_comes_before_the_step_up_and_spends_no_code(address_of) -> None:
    world = _World(password_hash=None)
    code = world.issue_code()

    refused = world.change(address_of(world), step_up_code=code)
    assert refused.status_code == 422, refused.text

    accepted = world.change(step_up_code=code)
    assert accepted.status_code == 201, accepted.text


def test_five_wrong_passwords_lock_the_e_mail_change() -> None:
    world = _World()
    for _ in range(5):
        assert world.change(password=WRONG_PASSWORD).status_code == 401

    resp = world.change(password=PASSWORD)

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    assert world.nothing_happened()


def test_failures_elsewhere_lock_the_e_mail_change_too() -> None:
    """One budget per account: failed erasure step-ups hold the e-mail change as well."""
    world = _World()
    for _ in range(5):
        resp = world.post("/api/v1/privacy/erasure", {"confirm_email": world.email, "password": WRONG_PASSWORD})
        assert resp.status_code == 401, resp.text

    resp = world.change(password=PASSWORD)

    assert resp.status_code == 429, resp.text
    assert not world.changes.rows


def test_a_federated_account_needs_the_mailed_code() -> None:
    world = _World(password_hash=None)

    resp = world.change()

    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "STEP_UP_CODE_REQUIRED"
    assert world.nothing_happened()


def test_a_federated_account_changes_with_the_mailed_code() -> None:
    world = _World(password_hash=None)
    code = world.issue_code()

    resp = world.change(step_up_code=code)

    assert resp.status_code == 201, resp.text
    (change,) = world.changes.rows.values()
    assert change.new_email == world.new_email


# ── with the step-up: what is sent ───────────────────────────────────────────


def test_a_passed_step_up_opens_the_request_and_mails_the_new_address() -> None:
    world = _World()

    resp = world.change(password=PASSWORD)

    assert resp.status_code == 201, resp.text
    assert len(world.changes.rows) == 1
    assert world.privacy_mail.send_email_change_email.call_args.kwargs["to_email"] == world.new_email


def test_the_current_address_is_told_at_the_request() -> None:
    """REQ-025 AK-06 — the owner learns of the change while it can still be stopped."""
    world = _World()

    world.change(password=PASSWORD)

    (notice,) = world.notices_to(world.email)
    assert world.new_email in notice["html_body"]
    assert "revert" not in notice["html_body"].lower()


def test_the_current_address_is_told_in_the_taken_branch_too() -> None:
    """The two branches stay indistinguishable to the requester — and the owner hears of both."""
    world = _World()

    resp = world.change(TAKEN, password=PASSWORD)

    assert resp.status_code == 201, resp.text
    assert not world.changes.rows
    (notice,) = world.notices_to(world.email)
    assert TAKEN in notice["html_body"]
    world.privacy_mail.send_email_change_email.assert_not_called()


def test_a_refused_step_up_sends_nothing_to_either_address() -> None:
    world = _World()

    world.change(password=WRONG_PASSWORD)

    assert not world.privacy_mail.method_calls


def test_the_old_address_is_told_at_the_confirmation() -> None:
    world = _World()
    world.change(password=PASSWORD)
    token = world.privacy_mail.send_email_change_email.call_args.kwargs["token"]
    world.privacy_mail.reset_mock()

    resp = world.post("/api/v1/privacy/email-change/confirm", {"token": token})

    assert resp.status_code == 200, resp.text
    assert world.users.rows[world.key].email == world.new_email
    (notice,) = world.notices_to(world.email)
    body = notice["html_body"]
    assert world.new_email in body
    assert "session" in body.lower()
    # Since #1848 the notice carries the way back (tests/unit/api/test_email_change_revert.py).
    assert "https://app.test/email-change/revert/" in body
    world.refresh_tokens.revoke_all_for_user.assert_called_with(world.key)


# ── a pending change is withdrawn when the owner takes the account back ─────────


NEW_PASSWORD = "-".join(["a", "fresh", "owner", "passphrase"])


def _pending_change_token(world: _World) -> str:
    resp = world.change(password=PASSWORD)
    assert resp.status_code == 201, resp.text
    return world.privacy_mail.send_email_change_email.call_args.kwargs["token"]


def _confirm(world: _World, token: str):  # noqa: ANN202 - httpx Response
    return world.post("/api/v1/privacy/email-change/confirm", {"token": token})


def test_a_password_reset_cancels_the_pending_change() -> None:
    """The notice tells the owner to reset the password; the reset must actually stop the change."""
    world = _World()
    token = _pending_change_token(world)

    assert world.post("/api/v1/auth/password-reset/request", {"email": world.email}).status_code == 200
    reset_token = world.auth_mail.send_password_reset_email.call_args.kwargs["token"]
    resp = world.post("/api/v1/auth/password-reset/confirm", {"token": reset_token, "new_password": NEW_PASSWORD})
    assert resp.status_code == 200, resp.text

    confirmed = _confirm(world, token)

    assert confirmed.status_code == 401, confirmed.text
    assert confirmed.json()["error_code"] == "INVALID_TOKEN"
    assert world.users.rows[world.key].email == world.email
    assert [c.status for c in world.changes.rows.values()] == ["cancelled"]


def test_a_password_change_cancels_the_pending_change() -> None:
    world = _World()
    token = _pending_change_token(world)

    resp = world.post("/api/v1/users/me/password", {"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    assert resp.status_code == 200, resp.text

    confirmed = _confirm(world, token)

    assert confirmed.status_code == 401, confirmed.text
    assert world.users.rows[world.key].email == world.email


def test_signing_out_everywhere_cancels_the_pending_change() -> None:
    world = _World()
    token = _pending_change_token(world)
    csrf = "".join(["c", "s", "r", "f"]) * 8

    client = world.client()
    client.cookies.set("csrf_token", csrf)
    resp = client.post("/api/v1/auth/logout-all", headers={"x-csrf-token": csrf})
    assert resp.status_code == 200, resp.text

    confirmed = _confirm(world, token)

    assert confirmed.status_code == 401, confirmed.text
    assert world.users.rows[world.key].email == world.email


def test_a_wrong_password_change_cancels_nothing() -> None:
    """Only the owner's proof withdraws the change — a thief's failed attempt must not."""
    world = _World()
    token = _pending_change_token(world)

    resp = world.post("/api/v1/users/me/password", {"current_password": WRONG_PASSWORD, "new_password": NEW_PASSWORD})
    assert resp.status_code == 401, resp.text

    assert _confirm(world, token).status_code == 200


def test_the_owner_notice_says_the_reset_cancels_the_change() -> None:
    world = _World()

    world.change(password=PASSWORD)

    (notice,) = world.notices_to(world.email)
    assert "cancels the pending change" in notice["html_body"]


def test_a_cancelled_request_is_a_status_the_api_can_report() -> None:
    from app.api.v1.privacy.schemas import EmailChangeResponse

    stored = EmailChangeRequest.model_validate(
        {
            "user_key": "u",
            "new_email": "x@example.org",
            "verification_token_hash": "h",
            "status": "cancelled",
            "expires_at": "2026-09-26T12:00:00Z",
        }
    )

    assert (
        EmailChangeResponse(
            key="ec-1",
            new_email=stored.new_email,
            status=stored.status,
            requested_at=None,
            expires_at=stored.expires_at,
        ).status
        == "cancelled"
    )


def test_the_sixth_code_within_an_hour_is_refused_and_not_mailed() -> None:
    """Review SEC-002: a session holder cannot use the account as a mail cannon.

    Each code is spent before the next is asked for, so the one-minute replacement
    wait does not apply — only the hourly issuance budget does.
    """
    world = _World(password_hash=None)
    for n in range(5):
        code = world.issue_code()
        resp = world.change(f"new-{n}-{world.new_email}", step_up_code=code)
        assert resp.status_code == 201, resp.text
    world.auth_mail.reset_mock()

    resp = world.post("/api/v1/users/me/step-up-code", {"action": "email_change"})

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    world.auth_mail.send_step_up_code_email.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        pytest.param(lambda: __import__("smtplib").SMTPServerDisconnected("gone"), id="smtp"),
        pytest.param(lambda: RuntimeError("adapter bug"), id="any error"),
    ],
)
def test_a_failing_old_address_notice_does_not_undo_the_confirmation(failure) -> None:
    """/code-review of #1862: the notice is sent after the change is committed; a failure must not answer 500."""
    world = _World()
    world.change(password=PASSWORD)
    token = world.privacy_mail.send_email_change_email.call_args.kwargs["token"]
    world.privacy_mail.send_notification_email.side_effect = failure()

    resp = world.post("/api/v1/privacy/email-change/confirm", {"token": token})

    assert resp.status_code == 200, resp.text
    assert world.users.rows[world.key].email == world.new_email


# ── #1888 review: a Resend failure is an undeliverable code, not a 500 ─────────


@pytest.mark.parametrize("failure", ["status-500", "status-422", "connect-error"])
def test_a_failed_resend_delivery_withdraws_the_code_so_a_retry_is_not_held(failure: str) -> None:
    """``request_step_up_code`` catches the undeliverable family; Resend's errors must be in it.

    Otherwise the code stays issued, the request answers 500, and the one-minute
    wait and the hourly budget hold the retry after the operator fixed the mail
    setup — what the /code-review of #1862 closed for SMTP.
    """
    import httpx

    from app.data_access.external.resend_email_adapter import ResendEmailAdapter

    sent: list[httpx.Request] = []
    broken = {"on": True}

    def resend(request: httpx.Request) -> httpx.Response:
        if broken["on"]:
            if failure == "connect-error":
                raise httpx.ConnectError("unreachable", request=request)
            return httpx.Response(int(failure.removeprefix("status-")), json={"message": "refused"})
        sent.append(request)
        return httpx.Response(200, json={"id": "ok"})

    world = _World(password_hash=None)
    key = "_".join(("re", "test", "1888"))
    world.auth._email_service = ResendEmailAdapter(  # noqa: SLF001
        api_key=key, from_email="noreply@example.org", transport=httpx.MockTransport(resend)
    )

    failed = world.post("/api/v1/users/me/step-up-code", {"action": "email_change"})
    broken["on"] = False
    retried = world.post("/api/v1/users/me/step-up-code", {"action": "email_change"})

    assert failed.status_code == 503, failed.text
    assert retried.status_code == 202, retried.text
    assert len(sent) == 1
