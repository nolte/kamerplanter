"""A step-up that has already passed — for tests of what happens *after* it (#1847).

Minting an API key or a pairing code passes :class:`StepUpVerifier` since #1847.
The pairing and API-key mechanics tests (code shape, expiry, redemption, scope
resolution) are about the credential, not the confirmation, and issue codes by
the thousand — a real bcrypt check per issuance would dominate their run time.
They take this double instead. What it stands in for is tested against the real
verifier in ``tests/unit/api/test_credential_issuance_step_up.py``; nothing that
uses this double may assert a step-up refusal.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from app.domain.services.step_up_service import StepUpVerifier, assert_target_bound

#: The keyword arguments of a credential call whose step-up the double passes.
STEP_UP_PASSED: dict[str, Any] = {
    "current_password": None,
    "step_up_code": None,
    "step_up_token": None,
    "authenticated_with_api_key": False,
}


class PassedStepUpVerifier:
    """Accepts every step-up and records the acts (and targets) it was asked to confirm.

    It still refuses what the real verifier refuses *before* any check (#1884): a
    call that omits ``target``, names none for a targeted act or one for another —
    so a caller that forgets the target fails here too, not only in production.
    """

    def __init__(self) -> None:
        self.actions: list[str] = []
        self.targets: list[str | None] = []

    def verify(self, requester: Any, *, action: str, target: str | None, **_: Any) -> str:
        assert_target_bound(action, target)
        self.actions.append(action)
        self.targets.append(target)
        return "password"


class AdmitEveryTarget:
    """A step-up target policy that admits every target (#1884).

    For tests about what happens *after* a factor was issued. Who may obtain a
    factor for which target is pinned against the real ``StepUpTargetAuthorizer``
    in ``tests/unit/domain/services/test_step_up_target_binding.py``.
    """

    def authorize(self, requester: Any, *, action: str, target: str) -> None:
        return None


@contextmanager
def admitting_every_target(verifier: StepUpVerifier) -> Iterator[StepUpVerifier]:
    """*verifier* with :class:`AdmitEveryTarget` for the duration — to issue a factor in a test harness."""
    previous = verifier._target_policy
    verifier._target_policy = AdmitEveryTarget()
    try:
        yield verifier
    finally:
        verifier._target_policy = previous
