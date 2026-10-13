"""One mailbox, three mail paths, one hour: the measured maximum (#2062, #2046 review).

Three budgets exist for one inbox, each deliberately independent (a budget shared
across them would let whoever exhausts one lock the owner out of the others,
#2059): the anonymous verification resend (3 per address), the password-proven
resend of the unverified login refusal (3 per account) and the password reset
(3 per address and source, 10 per address over all sources). REQ-023 §3.2b used to
say "up to 9"; the reset budget grew to 10 in #2059 without that sum being redone.

Measured here through the service with the production stores, from a squatter's
position — an account for the victim's address whose password the caller knows,
and as many source addresses as it takes: **16 mails in one window**, and no
further mail however often each path is asked again inside it.
"""

from __future__ import annotations

import pytest

from app.common.exceptions import EmailNotVerifiedError
from app.domain.engines.password_engine import PasswordEngine
from app.domain.services.auth_service import (
    MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW,
    MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW,
    MAX_VERIFICATION_RESENDS_PER_WINDOW,
)
from tests.unit.domain.services.test_auth_service_mail_token_order import ADDRESS, _Mailbox, _Repo, _service

PASSWORD = "A-Long-Enough-Password-2024!"


@pytest.fixture
def world() -> tuple[object, _Mailbox]:
    repo, mailbox = _Repo(), _Mailbox()
    repo.user = repo.user.model_copy(update={"password_hash": PasswordEngine().hash_password(PASSWORD)})
    return _service(repo, mailbox), mailbox


def test_the_three_paths_add_up_to_the_measured_maximum_and_not_one_mail_more(world: tuple[object, _Mailbox]) -> None:
    service, mailbox = world
    per_window_each = 5  # well past every budget

    for _ in range(per_window_each * 2):
        service.resend_verification_email(ADDRESS)  # type: ignore[attr-defined]
    for _ in range(per_window_each * 2):
        with pytest.raises(EmailNotVerifiedError):
            service.login_local(ADDRESS, PASSWORD, "agent", "198.51.100.9")  # type: ignore[attr-defined]
    # Reset: one source is held to 3, so reaching 10 takes four sources.
    for source in range(1, 9):
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 2):
            service.request_password_reset(ADDRESS, client_ip=f"203.0.113.{source}")  # type: ignore[attr-defined]

    resets = len(mailbox.reset_tokens)
    verifications = len(mailbox.verification_tokens)
    total = verifications + resets
    print(f"\nmails to one mailbox in one window: {verifications} verification + {resets} reset = {total}")
    # 3 anonymous + 3 proven land in the verification kind, 10 in the reset kind.
    assert verifications == 2 * MAX_VERIFICATION_RESENDS_PER_WINDOW
    assert resets == MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW
    assert total == 16
