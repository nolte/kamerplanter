"""Unit tests for ``UserPreferenceService.update_preferences``.

Pins the lost-update guard: a PATCH must persist only the *partial* set of
fields it actually touched, so two concurrent PATCHes of disjoint fields
commute (ArangoDB merges partial updates in place) instead of the later
full-document writer clobbering the earlier one. Reproduced under xdist
parallel load: a worker sets ``experience_level=intermediate`` (PATCH 200) but
a millisecond-later GET returned ``beginner`` again, because a concurrent PATCH
of a different field wrote back its stale full snapshot.

The service is exercised with a fake repo that records the exact ``fields``
dict handed to ``update_fields`` — that argument *is* the invariant under test.
"""

from typing import Any

import pytest

from app.common.enums import ExperienceLevel
from app.common.exceptions import DuplicateError
from app.domain.models.user_preference import UserPreference
from app.domain.services import singleton_document
from app.domain.services.user_preference_service import UserPreferenceService

USER_KEY = "user-1"


class _RecordingRepo:
    """In-memory stand-in that records the partial ``fields`` per update.

    ``update_fields`` mirrors ArangoDB's partial merge (keep_none): only the
    supplied keys are merged into the stored document, an explicit ``None`` is
    written rather than dropped.
    """

    def __init__(self, seed: UserPreference) -> None:
        doc = seed.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc.pop("_key", None)
        doc["_key"] = "pref-1"
        self._store: dict[str, dict[str, Any]] = {"pref-1": doc}
        self.recorded_fields: list[dict[str, Any]] = []

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        return [d for d in self._store.values() if d.get(field) == value]

    def create(self, model: UserPreference) -> dict[str, Any]:  # pragma: no cover - unused here
        doc = model.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc.pop("_key", None)
        doc["_key"] = "pref-1"
        self._store["pref-1"] = doc
        return dict(doc)

    def update_fields(self, key: str, fields: dict[str, Any]) -> dict[str, Any]:
        self.recorded_fields.append(dict(fields))
        doc = dict(self._store[key])
        doc.update(fields)
        doc["_key"] = key
        self._store[key] = doc
        return dict(doc)


def _service(seed: UserPreference) -> tuple[UserPreferenceService, _RecordingRepo]:
    service = UserPreferenceService.__new__(UserPreferenceService)
    repo = _RecordingRepo(seed)
    service._repo = repo  # type: ignore[attr-defined]
    return service, repo


def test_update_persists_only_touched_fields():
    seed = UserPreference(user_key=USER_KEY, experience_level=ExperienceLevel.INTERMEDIATE, locale="en")
    service, repo = _service(seed)

    service.update_preferences(USER_KEY, {"locale": "de"})

    # The write-doc carries exactly the touched key (+ the repo's own
    # updated_at, which the fake does not add). No disjoint field is rewritten,
    # so a concurrent experience_level PATCH cannot be clobbered.
    assert repo.recorded_fields == [{"locale": "de"}]


def test_disjoint_updates_do_not_clobber_each_other():
    # Two sequential PATCHes of disjoint fields, each from its own stale read,
    # must both survive — the partial merge is what makes them commute.
    seed = UserPreference(user_key=USER_KEY, experience_level=ExperienceLevel.BEGINNER, locale="de")
    service, repo = _service(seed)

    service.update_preferences(USER_KEY, {"experience_level": "intermediate"})
    service.update_preferences(USER_KEY, {"locale": "en"})

    result = service.get_preferences(USER_KEY)
    assert result.experience_level == ExperienceLevel.INTERMEDIATE
    assert result.locale == "en"
    assert repo.recorded_fields == [{"experience_level": "intermediate"}, {"locale": "en"}]


def test_dashboard_layout_null_reset_survives_in_partial_doc():
    seed = UserPreference(user_key=USER_KEY)
    service, repo = _service(seed)

    service.update_preferences(USER_KEY, {"dashboard_layout": None})

    # The None must reach the partial write-doc (keep_none reset, REQ-045),
    # not be dropped by any exclude_none dumping on the way.
    assert repo.recorded_fields == [{"dashboard_layout": None}]
    assert service.get_preferences(USER_KEY).dashboard_layout is None


def test_module_visibility_update_is_isolated():
    seed = UserPreference(user_key=USER_KEY, experience_level=ExperienceLevel.INTERMEDIATE)
    service, repo = _service(seed)

    service.update_preferences(USER_KEY, {"module_visibility": {"tanks": "disabled"}})

    assert list(repo.recorded_fields[0].keys()) == ["module_visibility"]
    # experience_level is untouched by a module_visibility-only PATCH.
    assert service.get_preferences(USER_KEY).experience_level == ExperienceLevel.INTERMEDIATE


@pytest.mark.parametrize("value", ["intermediate", "expert", "beginner"])
def test_experience_level_only_touches_experience_level(value: str):
    seed = UserPreference(user_key=USER_KEY, locale="de", theme="dark")
    service, repo = _service(seed)

    service.update_preferences(USER_KEY, {"experience_level": value})

    assert list(repo.recorded_fields[0].keys()) == ["experience_level"]


# ── Auto-create race guard (duplicate-singleton bug) ─────────────────────────


class _RaceRepo:
    """Simulates the auto-create race: the loser's insert collides.

    The first ``find_by_field`` sees an empty collection, so the service tries to
    ``create`` — but a concurrent request already inserted the winner, so this
    insert raises ``DuplicateError``. The subsequent re-read then returns the
    winner's document.
    """

    def __init__(self, winner: dict[str, Any]) -> None:
        self._winner = winner
        self._exists = False
        self.create_calls = 0

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        return [dict(self._winner)] if self._exists else []

    def create(self, model: UserPreference) -> dict[str, Any]:
        self.create_calls += 1
        # The winning writer landed first; this insert loses on the unique index.
        self._exists = True
        raise DuplicateError("user_preferences", "user_key", USER_KEY)


class _MultiDocRepo:
    """A legacy volume that still holds duplicate singletons for one user_key."""

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        return [dict(doc) for doc in self._docs]

    def create(self, model: UserPreference) -> dict[str, Any]:  # pragma: no cover - never reached
        raise AssertionError("create must not run when documents already exist")


def _service_with(repo: Any) -> UserPreferenceService:
    service = UserPreferenceService.__new__(UserPreferenceService)
    service._repo = repo  # type: ignore[attr-defined]
    return service


def test_get_preferences_rereads_on_duplicate_race():
    winner = {"_key": "pref-win", "user_key": USER_KEY, "locale": "en"}
    repo = _RaceRepo(winner)
    service = _service_with(repo)

    result = service.get_preferences(USER_KEY)

    # The DuplicateError is swallowed and the winner's document returned (upsert),
    # instead of surfacing a 409 to the losing request.
    assert result.key == "pref-win"
    assert result.locale == "en"
    assert repo.create_calls == 1


def test_get_preferences_picks_smallest_key_on_duplicates():
    repo = _MultiDocRepo(
        [
            {"_key": "z", "user_key": USER_KEY, "locale": "de"},
            {"_key": "a", "user_key": USER_KEY, "locale": "en"},
        ]
    )
    service = _service_with(repo)

    result = service.get_preferences(USER_KEY)

    # Deterministic: smallest _key wins, so the read no longer flaps between
    # requests on a legacy duplicate volume.
    assert result.key == "a"
    assert result.locale == "en"


def test_pick_singleton_warns_and_picks_smallest_key(monkeypatch):
    calls: list[tuple[str, dict[str, Any]]] = []

    class _RecordingLogger:
        def warning(self, event: str, **kwargs: Any) -> None:
            calls.append((event, kwargs))

    monkeypatch.setattr(singleton_document, "logger", _RecordingLogger())

    docs = [{"_key": "z", "user_key": "u1"}, {"_key": "a", "user_key": "u1"}]
    picked = singleton_document.pick_singleton(docs, collection="user_preferences", user_key="u1")

    assert picked["_key"] == "a"
    assert calls[0][0] == "duplicate_singleton_docs"
    assert calls[0][1]["keys"] == ["a", "z"]
    assert calls[0][1]["count"] == 2


def test_pick_singleton_single_doc_does_not_warn(monkeypatch):
    calls: list[str] = []

    class _RecordingLogger:
        def warning(self, event: str, **kwargs: Any) -> None:  # pragma: no cover - must not run
            calls.append(event)

    monkeypatch.setattr(singleton_document, "logger", _RecordingLogger())

    doc = {"_key": "only", "user_key": "u1"}
    picked = singleton_document.pick_singleton([doc], collection="user_preferences", user_key="u1")

    assert picked is doc
    assert calls == []
