"""Unit tests for ``OnboardingService.get_state`` auto-create race guard.

``onboarding_states`` holds one document per ``user_key`` and is auto-created on
the first cold read. Under concurrent cold reads that insert raced, minting
duplicate singletons and making the read flap. The service now upserts (re-read
on ``DuplicateError``) and reads deterministically (smallest ``_key``).
"""

from typing import Any

from app.common.exceptions import DuplicateError
from app.domain.models.onboarding import OnboardingState
from app.domain.services.onboarding_service import OnboardingService

USER_KEY = "user-1"


class _RaceRepo:
    """The loser's insert collides on the unique index; the re-read wins."""

    def __init__(self, winner: dict[str, Any]) -> None:
        self._winner = winner
        self._exists = False
        self.create_calls = 0

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        return [dict(self._winner)] if self._exists else []

    def create(self, model: OnboardingState) -> dict[str, Any]:
        self.create_calls += 1
        self._exists = True
        raise DuplicateError("onboarding_states", "user_key", USER_KEY)


class _MultiDocRepo:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        return [dict(doc) for doc in self._docs]

    def create(self, model: OnboardingState) -> dict[str, Any]:  # pragma: no cover - never reached
        raise AssertionError("create must not run when documents already exist")


def _service_with(repo: Any) -> OnboardingService:
    service = OnboardingService.__new__(OnboardingService)
    service._repo = repo  # type: ignore[attr-defined]
    return service


def test_get_state_rereads_on_duplicate_race():
    winner = {"_key": "onb-win", "user_key": USER_KEY, "wizard_step": 3}
    repo = _RaceRepo(winner)
    service = _service_with(repo)

    result = service.get_state(USER_KEY)

    assert result.key == "onb-win"
    assert result.wizard_step == 3
    assert repo.create_calls == 1


def test_get_state_picks_smallest_key_on_duplicates():
    repo = _MultiDocRepo(
        [
            {"_key": "z", "user_key": USER_KEY, "wizard_step": 2},
            {"_key": "a", "user_key": USER_KEY, "wizard_step": 5},
        ]
    )
    service = _service_with(repo)

    result = service.get_state(USER_KEY)

    assert result.key == "a"
    assert result.wizard_step == 5
