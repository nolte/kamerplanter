"""#1848 — the e-mail change has its own link, and the previous address can take the account back.

Before: the mail to the new address linked the account-verification page (whose
``POST /auth/verify-email`` rejects an e-mail-change token), and after a
confirmed change the owner had no way back — the password reset goes to the new
address and no admin route can change an e-mail. Now:

* the new address gets ``/email-change/{token}`` (the page calls
  ``POST /privacy/email-change/confirm``) and no display name (#1856);
* the notice to the previous address carries a single-use revert link, valid for
  ``RETENTION_EMAIL_CHANGE_REVERT_DAYS``;
* ``POST /privacy/email-change/revert`` restores that address as verified, signs
  out every session, voids a password-reset token (it went to the new address)
  and withdraws pending changes — once, within the window, and only while the
  previous address is still free;
* the R-07 task drops the previous address and the token's hash when the window
  closes.

The requests run the real privacy router and services over the in-memory doubles
of ``test_email_change_step_up``.
"""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime, timedelta

from app.domain.models.auth import ApiKey, AuthProvider, AuthProviderType
from app.domain.models.user import User
from tests.unit.api.test_email_change_step_up import PASSWORD, _limiter_off, _World  # noqa: F401 - autouse fixture

REVERT = "/api/v1/privacy/email-change/revert"
CHANGE = "/api/v1/privacy/email-change"
CONFIRM = "/api/v1/privacy/email-change/confirm"


def _changed(world: _World) -> str:
    """Request and confirm a change; return the revert token from the notice to the old address."""
    assert world.change(password=PASSWORD).status_code == 201
    token = world.privacy_mail.send_email_change_email.call_args.kwargs["token"]
    assert world.post(CONFIRM, {"token": token}).status_code == 200
    # The owner's address hears twice: at the request, then at the confirmation.
    notice = world.notices_to(world.email)[-1]
    match = re.search(r"/email-change/revert/([A-Za-z0-9_-]+)", notice["html_body"])
    assert match, notice["html_body"]
    return match.group(1)


def test_the_new_address_gets_the_email_change_link_without_a_display_name() -> None:
    world = _World()

    world.change(password=PASSWORD)

    call = world.privacy_mail.send_email_change_email.call_args
    assert call.kwargs["to_email"] == world.new_email
    assert call.kwargs["frontend_url"] == "https://app.test"
    assert "display_name" not in call.kwargs
    world.privacy_mail.send_verification_email.assert_not_called()


def test_the_previous_address_takes_the_account_back() -> None:
    world = _World()
    revert = _changed(world)
    world.users.update_fields(world.key, {"password_reset_token": "reset-sent-to-the-new-address"})
    world.refresh_tokens.reset_mock()

    resp = world.post(REVERT, {"token": revert})

    assert resp.status_code == 200, resp.text
    owner = world.users.rows[world.key]
    assert owner.email == world.email
    assert owner.email_verified is True
    assert owner.password_reset_token is None
    world.refresh_tokens.revoke_all_for_user.assert_called_with(world.key)
    (change,) = world.changes.rows.values()
    assert change.status == "reverted"


def test_a_revert_token_works_once() -> None:
    world = _World()
    revert = _changed(world)
    world.post(REVERT, {"token": revert})
    world.users.update_fields(world.key, {"email": world.new_email})

    resp = world.post(REVERT, {"token": revert})

    assert resp.status_code == 401, resp.text
    assert world.users.rows[world.key].email == world.new_email


def test_an_unknown_revert_token_is_refused() -> None:
    world = _World()
    _changed(world)

    resp = world.post(REVERT, {"token": "not-a-token"})

    assert resp.status_code == 401, resp.text
    assert world.users.rows[world.key].email == world.new_email


def test_a_revert_after_the_window_is_refused() -> None:
    world = _World()
    revert = _changed(world)
    (change,) = world.changes.rows.values()
    world.changes.update(
        change.key, change.model_copy(update={"revert_expires_at": datetime.now(UTC) - timedelta(seconds=1)})
    )

    resp = world.post(REVERT, {"token": revert})

    assert resp.status_code == 401, resp.text
    assert world.users.rows[world.key].email == world.new_email


def test_a_previous_address_taken_meanwhile_is_not_restored() -> None:
    world = _World()
    revert = _changed(world)
    squatter = User.model_validate({"_key": f"squat-{world.key}", "email": world.email, "display_name": "S"})
    world.users.rows[squatter.key] = squatter

    resp = world.post(REVERT, {"token": revert})

    assert resp.status_code == 422, resp.text
    assert world.users.rows[world.key].email == world.new_email


def test_a_pending_change_is_withdrawn_by_the_revert() -> None:
    world = _World()
    revert = _changed(world)
    world.users.update_fields(world.key, {"email": world.new_email})
    world.change(new_email=f"third-{world.key}@example.org", password=PASSWORD)

    world.post(REVERT, {"token": revert})

    assert all(c.status != "pending" for c in world.changes.rows.values())


def test_the_retention_task_closes_the_revert_window_and_removes_the_document() -> None:
    """NFR-011 R-07a closes the revert window; R-07b hard-deletes the whole document at the same instant (#1800).

    Both fire at the identical threshold (``confirmed_at`` + the revert-days
    setting), so once the window has closed the document is gone outright, not
    left behind with its revert fields merely nulled.
    """
    world = _World()
    revert = _changed(world)
    (change,) = world.changes.rows.values()
    world.changes.update(
        change.key, change.model_copy(update={"revert_expires_at": datetime.now(UTC) - timedelta(seconds=1)})
    )

    asyncio.run(world.privacy.expire_email_change_requests(now=datetime.now(UTC)))

    assert world.changes.rows == {}
    assert world.post(REVERT, {"token": revert}).status_code == 401


# ── security review of the #1848 branch ──────────────────────────────────────


def _take_over_twice(world: _World) -> tuple[str, str]:
    """A→B confirmed (owner's token to A), then B→C confirmed (attacker's token to B)."""
    owners = _changed(world)
    world.privacy_mail.reset_mock()
    third = f"third-{world.key}@example.org"
    assert world.change(new_email=third, password=PASSWORD).status_code == 201
    token = world.privacy_mail.send_email_change_email.call_args.kwargs["token"]
    assert world.post(CONFIRM, {"token": token}).status_code == 200
    notice = world.notices_to(world.new_email)[-1]
    attackers = re.search(r"/email-change/revert/([A-Za-z0-9_-]+)", notice["html_body"])
    assert attackers
    return owners, attackers.group(1)


def test_a_later_change_cannot_undo_the_owners_revert() -> None:
    # SEC-001: the attacker's own second change carried a revert token to B; after
    # the owner took the account back to A, it moved the account onto B again.
    world = _World()
    owners, attackers = _take_over_twice(world)

    assert world.post(REVERT, {"token": owners}).status_code == 200
    resp = world.post(REVERT, {"token": attackers})

    assert resp.status_code == 401, resp.text
    assert world.users.rows[world.key].email == world.email


def test_the_owners_earlier_token_survives_a_revert_of_a_later_change() -> None:
    world = _World()
    owners, attackers = _take_over_twice(world)

    world.post(REVERT, {"token": attackers})
    resp = world.post(REVERT, {"token": owners})

    assert resp.status_code == 200, resp.text
    assert world.users.rows[world.key].email == world.email


def test_a_confirmation_that_lost_the_race_writes_nothing() -> None:
    # SEC-001 (TOCTOU): the status is claimed atomically before the address moves.
    world = _World()
    world.change(password=PASSWORD)
    token = world.privacy_mail.send_email_change_email.call_args.kwargs["token"]
    (change,) = world.changes.rows.values()
    world.changes.claim_status(change.key, "pending", "cancelled", datetime.now(UTC).isoformat())
    world.changes.rows[change.key] = world.changes.rows[change.key].model_copy(update={"status": "pending"})
    world.changes.claim_status = lambda *a, **k: False  # another request claimed it first

    resp = world.post(CONFIRM, {"token": token})

    assert resp.status_code == 401, resp.text
    assert world.users.rows[world.key].email == world.email


def test_the_revert_drops_sign_in_links_made_since_the_request() -> None:
    # SEC-002: a Google/OIDC identity auto-linked to the hijacked address kept
    # signing the attacker in after the revert.
    world = _World()
    before = datetime.now(UTC) - timedelta(days=30)
    world.providers.rows.append(
        AuthProvider(
            _key="google-old",
            user_key=world.key,
            provider=AuthProviderType.GOOGLE,
            provider_user_id="g-old",
            linked_at=before,
        )
    )
    revert = _changed(world)
    later = datetime.now(UTC) + timedelta(seconds=1)
    world.providers.rows += [
        AuthProvider(
            _key="google-new",
            user_key=world.key,
            provider=AuthProviderType.GOOGLE,
            provider_user_id="g-new",
            linked_at=later,
        ),
        AuthProvider(
            _key="local-new",
            user_key=world.key,
            provider=AuthProviderType.LOCAL,
            provider_user_id=world.key,
            linked_at=later,
        ),
    ]

    world.post(REVERT, {"token": revert})

    assert world.providers.deleted == ["google-new"]


def test_the_revert_revokes_api_keys_created_since_the_request() -> None:
    # SEC-003: a key minted during the takeover kept reading and writing.
    world = _World()
    world.api_keys.rows.append(
        ApiKey(
            _key="ak-old",
            user_key=world.key,
            label="ha",
            key_hash="h1",
            key_prefix="kp_old",
            created_at=datetime.now(UTC) - timedelta(days=30),
        )
    )
    revert = _changed(world)
    world.api_keys.rows.append(
        ApiKey(
            _key="ak-new",
            user_key=world.key,
            label="x",
            key_hash="h2",
            key_prefix="kp_new",
            created_at=datetime.now(UTC) + timedelta(seconds=1),
        )
    )

    world.post(REVERT, {"token": revert})

    assert world.api_keys.revoked == ["ak-new"]


def test_the_address_the_account_left_again_is_told() -> None:
    # SEC-004: the new address learned nothing of the revert.
    world = _World()
    revert = _changed(world)
    world.privacy_mail.reset_mock()

    world.post(REVERT, {"token": revert})

    (notice,) = world.notices_to(world.new_email)
    assert "Owner" not in notice["html_body"]
    assert world.email not in notice["html_body"]


def test_a_revert_on_an_account_being_erased_is_refused() -> None:
    # SEC-007: the revert wrote an address onto an account queued for hard deletion.
    world = _World()
    revert = _changed(world)
    world.users.update_fields(world.key, {"is_active": False})

    resp = world.post(REVERT, {"token": revert})

    assert resp.status_code == 409, resp.text
    assert world.users.rows[world.key].email == world.new_email


# ── /code-review of #1893 ────────────────────────────────────────────────────


def test_an_address_held_for_the_revert_cannot_be_registered() -> None:
    # Finding 1: registering an account on the freed previous address — no
    # mailbox access needed, registration is unverified — made every revert 422.
    world = _World()
    revert = _changed(world)

    world.auth.register_local(world.email, PASSWORD, "Squatter")

    assert [u.key for u in world.users.rows.values() if u.email == world.email] == []
    assert world.post(REVERT, {"token": revert}).status_code == 200
    assert world.users.rows[world.key].email == world.email


def test_another_account_cannot_move_onto_an_address_held_for_the_revert() -> None:
    world = _World()
    revert = _changed(world)
    other = world.users.rows[f"other-{world.key}"]
    world.users.rows[other.key] = other.model_copy(update={"password_hash": world.users.rows[world.key].password_hash})
    world.key, owner = other.key, world.key  # act as the other account

    world.post(CHANGE, {"new_email": world.email, "password": PASSWORD})
    world.key = owner

    assert all(c.user_key != other.key for c in world.changes.rows.values())
    assert world.post(REVERT, {"token": revert}).status_code == 200


def test_a_confirmation_onto_a_taken_address_leaves_the_request_pending() -> None:
    # Finding 2: the status was claimed before the account write; a unique-index
    # failure left the request "confirmed" without ever moving the account.
    world = _World()
    world.change(password=PASSWORD)
    token = world.privacy_mail.send_email_change_email.call_args.kwargs["token"]
    squatter = User.model_validate({"_key": f"squat-{world.key}", "email": world.new_email, "display_name": "S"})
    world.users.rows[squatter.key] = squatter

    resp = world.post(CONFIRM, {"token": token})

    assert resp.status_code == 409, resp.text
    assert world.users.rows[world.key].email == world.email
    (change,) = world.changes.rows.values()
    assert change.status == "pending"


def test_a_revert_that_loses_the_race_keeps_its_token() -> None:
    # Finding 2/3: a revert whose account write loses to a concurrent move must
    # not burn the single-use token.
    world = _World()
    revert = _changed(world)
    world.users.move_email = lambda *a, **k: None  # the address moved in between

    resp = world.post(REVERT, {"token": revert})

    assert resp.status_code == 409, resp.text
    (change,) = [c for c in world.changes.rows.values() if c.previous_email]
    assert change.status == "confirmed"


def test_a_confirmation_in_flight_is_superseded_by_the_revert() -> None:
    # Finding 3: a confirmation that had claimed its request but not yet stamped
    # confirmed_at escaped the supersede, then moved the account back.
    world = _World()
    owners = _changed(world)
    third = f"third-{world.key}@example.org"
    world.change(new_email=third, password=PASSWORD)
    second_token = world.privacy_mail.send_email_change_email.call_args.kwargs["token"]
    (second,) = [c for c in world.changes.rows.values() if c.status == "pending"]
    world.changes.claim_status(second.key, "pending", "confirmed", datetime.now(UTC).isoformat())

    assert world.post(REVERT, {"token": owners}).status_code == 200

    assert world.changes.rows[second.key].status == "superseded"
    assert world.post(CONFIRM, {"token": second_token}).status_code == 401
    assert world.users.rows[world.key].email == world.email
