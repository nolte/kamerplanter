"""A lost care-profile creation race answers with the winner, not with a 500 (#1292).

Measured, not inferred. The 2026-09-14 ``e2e-nightly`` (run 34814941664, profile
``mobile``) failed self-provisioning with ``could not create a care profile for
'522789' (status=500)``; the backend log collected by that same run carries the
traceback behind it::

    File "/app/app/domain/services/care_reminder_service.py", line 267,
        in get_or_create_profile
      self._repo.create_profile_edge(plant_key, created.key)
    File "/app/app/data_access/arango/care_reminder_repository.py", line 125,
        in create_profile_edge
      self.create_edge(col.HAS_CARE_PROFILE, plant_id, profile_id)
    File "/app/app/data_access/arango/base_repository.py", line 891, in create_edge
      result = col.insert(edge_data, return_new=True)
    arango.exceptions.DocumentInsertError: [HTTP 409][ERR 1200] write-write
    conflict - in index idx_1876288907249713152 of type persistent over '_from';
    document key: 526429; indexed values: ["plant_instances/522789"]

So this is #1436's failure class on a **different write**: that issue fixed the
care *task* insert, whose 1200 arrives through ``_insert_doc``. Edges never went
through ``_insert_doc`` — ``create_edge`` calls the driver directly — so the same
condition on the ``has_care_profile`` unique ``_from`` index still reached the
router as a bare driver exception.

The contract pinned here is the two-branched one :class:`WriteConflictError`
requires, because 1200 is a statement about timing and not about data:

* the edge resolves to a profile → the winner committed, and its profile is this
  caller's answer too (plus: the orphan document this call inserted a moment
  earlier is removed, since ``get_profile_by_plant_key`` reads an un-indexed
  *field* and would otherwise start answering with an unlinked duplicate);
* the edge resolves to nothing → the other transaction rolled back, nothing was
  won, and the conflict keeps propagating.

Solitary: the repository is the owned I/O boundary and is doubled here. That
ArangoDB really answers 1200 on this index under contention is measured in
``tests/integration/test_care_profile_edge_concurrency.py``; neither tier
certifies anything alone, and this one is the one that runs in a CI gate (#1432).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import DuplicateError, WriteConflictError
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.services.care_reminder_service import CareReminderService

PLANT = "522789"


def _service(care_repo) -> CareReminderService:
    return CareReminderService(care_repo, CareReminderEngine())


def _losing_repo(*, winner: CareProfile | None, rejection: Exception | None = None) -> MagicMock:
    """A repository whose profile insert succeeds and whose edge insert loses.

    That ordering is the measured one: ``create_profile`` committed (the orphan
    exists) and only ``create_profile_edge`` hit the unique ``_from`` index.
    """
    repo = MagicMock()
    repo.get_profile_by_plant_key.return_value = None
    repo.create_profile.side_effect = lambda profile: profile.model_copy(update={"key": "mine"})
    repo.create_profile_edge.side_effect = rejection or WriteConflictError("has_care_profile")
    repo.get_linked_profile.return_value = winner
    return repo


class TestLostProfileCreationRace:
    def test_the_loser_answers_with_the_winners_profile(self):
        """The 500 measured in #1292 becomes the answer the caller asked for."""
        winner = CareProfile(key="theirs", plant_key=PLANT)
        repo = _losing_repo(winner=winner)

        result = _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert result is winner
        repo.get_linked_profile.assert_called_once_with(PLANT)

    def test_the_losers_orphan_document_is_removed(self):
        """``get_profile_by_plant_key`` reads an un-indexed field, so the orphan matters.

        The loser's ``CareProfile`` carries the same ``plant_key`` as the winner's
        and no edge points at it. ``care_profiles`` has no index over ``plant_key``
        at all, so a later ``find_one_by_field`` lookup may answer with either
        document — a plant would then read care intervals from a profile nothing
        links to. Leaving the orphan is what makes that state reachable.
        """
        repo = _losing_repo(winner=CareProfile(key="theirs", plant_key=PLANT))

        _service(repo).get_or_create_profile(PLANT, may_create=True)

        repo.delete_profile.assert_called_once_with("mine")

    def test_the_winners_own_document_is_never_deleted(self):
        """Guard against the resolution eating the very profile it returns.

        If the edge re-read resolves back to *this* call's document — the two keys
        are equal — then nothing was lost and the delete would destroy the answer.
        """
        mine = CareProfile(key="mine", plant_key=PLANT)
        repo = _losing_repo(winner=mine)

        result = _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert result.key == "mine"
        repo.delete_profile.assert_not_called()

    def test_a_conflict_with_no_edge_behind_it_keeps_propagating(self):
        """1200 is not "it already exists" — with nothing linked, it is a real failure.

        Absorbing it would hand back a profile whose ``has_care_profile`` edge does
        not exist, so every later graph read of that plant would find none.
        """
        repo = _losing_repo(winner=None)

        with pytest.raises(WriteConflictError):
            _service(repo).get_or_create_profile(PLANT, may_create=True)

        repo.delete_profile.assert_not_called()

    def test_the_other_rejection_code_resolves_the_same_way(self):
        """ArangoDB answers this index with ``1210`` as well as with ``1200``.

        Not a hypothetical: the four-way race in
        ``tests/integration/test_care_profile_edge_concurrency.py`` produced both
        codes from the *same* burst against a real server — 1200 in the nightly's
        traceback, 1210 locally. Handling only the one that happened to be
        measured first would have left the 500 in place half the time.
        """
        winner = CareProfile(key="theirs", plant_key=PLANT)
        repo = _losing_repo(winner=winner, rejection=DuplicateError("has_care_profile", "_from", PLANT))

        result = _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert result is winner
        repo.delete_profile.assert_called_once_with("mine")

    def test_the_other_rejection_code_also_keeps_propagating_when_nothing_is_linked(self):
        """The two-branch contract is not weakened for ``1210`` either."""
        repo = _losing_repo(winner=None, rejection=DuplicateError("has_care_profile", "_from", PLANT))

        with pytest.raises(DuplicateError):
            _service(repo).get_or_create_profile(PLANT, may_create=True)

    def test_a_read_never_reaches_the_conflicting_write_at_all(self):
        """``may_create=False`` still writes nothing — the #1422 boundary stays put."""
        repo = _losing_repo(winner=CareProfile(key="theirs", plant_key=PLANT))

        _service(repo).get_or_create_profile(PLANT, may_create=False)

        repo.create_profile.assert_not_called()
        repo.create_profile_edge.assert_not_called()
