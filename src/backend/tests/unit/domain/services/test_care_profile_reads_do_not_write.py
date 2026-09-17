"""#1422 round 2 — a read of a care profile stores nothing, and neither does the dashboard.

`get_or_create_profile` did what its name says: it persisted a `CareProfile` and a
profile edge whenever the plant had none. Two callers reach it on a plain read —
`GET /care-reminders/plants/{key}/profile` and the tenant care dashboard — and the
dashboard does it for **every** plant of the tenant at once. Any member could
therefore write documents by looking at a page, which is the axis #1422 closes.

Round 1 of the review gated the narrow route instead, and that was worse than the
defect in one respect: reading an *existing* profile writes nothing, so the gate took
the read away from viewers and left the frontend's care tab spinning on a 403 it does
not handle. The gate belonged on the write; the write is now simply not performed.

`may_create` is keyword-only with **no default**, so every call site says which it is.
A default would be an opt-in, and an opt-in on a persisting call is the #948 shape:
the paths that must not write would inherit the permissive answer by saying nothing.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.domain.models.care_reminder import CareProfile
from app.domain.services.care_reminder_service import CareReminderService


def _service(existing: CareProfile | None):
    service = CareReminderService.__new__(CareReminderService)
    repo = MagicMock()
    repo.get_profile_by_plant_key.return_value = existing
    # Returns a row WITH a key, as the real repository does — the edge is only
    # created `if created.key`, so a keyless double would have made the write
    # control pass for the wrong reason.
    repo.create_profile.side_effect = lambda profile: profile.model_copy(update={"key": "cp-new"})
    engine = MagicMock()
    engine.auto_generate_profile.return_value = CareProfile(plant_key="p1", watering_interval_days=7)
    service._repo = repo
    service._engine = engine
    # The collaborators `get_or_create_profile` resolves its presets through since
    # #1489. `None` is the shape the constructor allows for each of them (every one
    # is optional), and it is the shape that makes the resolution answer "no species,
    # no family" — which is what these cases are about: the *write*, not the presets.
    service._plant_repo = None
    service._species_repo = None
    service._family_name_resolver = None
    service._family_name_cache = {}
    return service, repo


def test_a_read_of_an_absent_profile_stores_nothing():
    """The fix. The presets are returned; the database is untouched."""
    service, repo = _service(existing=None)

    profile = service.get_or_create_profile("p1", may_create=False)

    assert profile is not None, "the caller still gets presets to render"
    repo.create_profile.assert_not_called()
    repo.create_profile_edge.assert_not_called()


def test_a_write_path_still_stores_it():
    """The control. Without it, `may_create` could be ignored entirely and pass above."""
    service, repo = _service(existing=None)

    service.get_or_create_profile("p1", may_create=True)

    repo.create_profile.assert_called_once()
    repo.create_profile_edge.assert_called_once()


def test_an_existing_profile_is_returned_untouched_either_way():
    """Why round 1's route-level gate was the wrong instrument.

    Reading an existing profile never wrote anything, so gating the operation took
    the read from viewers to prevent a write that was not happening on that path.
    """
    existing = CareProfile(key="cp1", plant_key="p1", watering_interval_days=3)

    for may_create in (True, False):
        service, repo = _service(existing=existing)

        assert service.get_or_create_profile("p1", may_create=may_create) is existing
        repo.create_profile.assert_not_called()


def test_may_create_has_no_default():
    """Omitting it must be an error, not a permissive guess.

    This is the whole reason the parameter is keyword-only without a default: a call
    site that says nothing would otherwise inherit the answer that writes, which is
    the #948 opt-in drift that put the defect on two read paths in the first place.
    """
    service, _repo = _service(existing=None)

    with pytest.raises(TypeError):
        service.get_or_create_profile("p1")  # type: ignore[call-arg]
