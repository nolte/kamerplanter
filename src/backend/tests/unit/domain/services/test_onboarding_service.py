"""Unit tests for the ``onboarding_states`` per-user singleton.

``onboarding_states`` holds one document per ``user_key``. It used to be
auto-created on the first cold **read**, which made a plain ``GET`` persist
(#1461) and raced under concurrent cold reads, minting duplicate singletons and
making the read flap.

Since #1461 the read creates nothing and the first **write** materialises the
row; the race moved with it and is resolved the same way — re-read the winner on
either refusal code (#1458) — and the read still picks deterministically
(smallest ``_key``) while legacy duplicates exist.
"""

from typing import Any
from unittest.mock import MagicMock

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

    def update(self, key: str, model: OnboardingState) -> dict[str, Any]:
        self._winner.update(model.model_dump(mode="json", exclude={"key"}))
        return dict(self._winner)


class _MultiDocRepo:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        return [dict(doc) for doc in self._docs]

    def create(self, model: OnboardingState) -> dict[str, Any]:  # pragma: no cover - never reached
        raise AssertionError("create must not run when documents already exist")


def _service_with(repo: Any) -> OnboardingService:
    """The real service with only its repository doubled (review SCR-011)."""
    from app.domain.services.starter_kit_service import StarterKitService

    db = MagicMock()
    service = OnboardingService(db, StarterKitService(db))
    service._repo = repo  # type: ignore[assignment]
    return service


def test_the_first_write_rereads_on_duplicate_race():
    """The auto-create race, on the path it lives on since #1461: the first WRITE.

    It used to live on ``get_state``, which made a plain ``GET`` persist. The
    resolution is unchanged — the refusal is swallowed and the winner's document
    is returned instead of a 409 reaching the losing request — only the caller
    that triggers it moved.
    """
    winner = {"_key": "onb-win", "user_key": USER_KEY, "wizard_step": 3}
    repo = _RaceRepo(winner)
    service = _service_with(repo)

    result = service.save_progress(USER_KEY, 4)

    assert result.key == "onb-win"
    assert result.wizard_step == 4
    assert repo.create_calls == 1


def test_reading_the_state_creates_nothing():
    """#1461 — the read answers with the initial state and writes no row.

    ``_RaceRepo`` raises on ``create``, so an auto-create would surface here as a
    ``DuplicateError`` rather than as a quiet extra row: the assertion on
    ``create_calls`` is the statement, and the absence of an exception is the
    control that it is not passing for the wrong reason.
    """
    repo = _RaceRepo({"_key": "onb-win", "user_key": USER_KEY, "wizard_step": 3})
    service = _service_with(repo)

    result = service.get_state(USER_KEY)

    assert repo.create_calls == 0
    assert result.key is None
    assert result.user_key == USER_KEY
    assert result.wizard_step == OnboardingState(user_key=USER_KEY).wizard_step
    assert result.completed is False


def test_the_first_write_creates_the_row_when_there_is_none():
    """The other half: nothing reads the row into existence, so a write must."""

    class _ColdRepo:
        def __init__(self) -> None:
            self.created: list[OnboardingState] = []
            self._doc: dict[str, Any] | None = None

        def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
            return [dict(self._doc)] if self._doc else []

        def create(self, model: OnboardingState) -> dict[str, Any]:
            self.created.append(model)
            self._doc = {"_key": "onb-new", **model.model_dump(mode="json", exclude={"key"})}
            return dict(self._doc)

        def update(self, key: str, model: OnboardingState) -> dict[str, Any]:
            assert self._doc is not None
            self._doc.update(model.model_dump(mode="json", exclude={"key"}))
            return dict(self._doc)

    repo = _ColdRepo()
    service = _service_with(repo)

    result = service.save_progress(USER_KEY, 2)

    assert len(repo.created) == 1
    assert result.key == "onb-new"
    assert result.wizard_step == 2


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
