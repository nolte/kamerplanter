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

from typing import Any

#: The keyword arguments of a credential call whose step-up the double passes.
STEP_UP_PASSED: dict[str, Any] = {
    "current_password": None,
    "step_up_code": None,
    "step_up_token": None,
    "authenticated_with_api_key": False,
}


class PassedStepUpVerifier:
    """Accepts every step-up and records the acts it was asked to confirm."""

    def __init__(self) -> None:
        self.actions: list[str] = []

    def verify(self, requester: Any, *, action: str, **_: Any) -> str:
        self.actions.append(action)
        return "password"
