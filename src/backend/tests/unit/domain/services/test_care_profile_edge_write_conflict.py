"""A lost care-profile creation race answers with the winner, not with a 500 (#1292).

Measured, not inferred. The 2026-09-14 ``e2e-nightly`` (run 34814941664, profile
``mobile``) failed self-provisioning with ``could not create a care profile for
'522789' (status=500)``; the backend log collected by that same run carries the
traceback behind it::

    File "/app/app/domain/services/care_reminder_service.py", line 267,
        in get_or_create_profile
      self._repo.create_profile_edge(plant_key, created.key)
    ...
    arango.exceptions.DocumentInsertError: [HTTP 409][ERR 1200] write-write
    conflict - in index idx_1876288907249713152 of type persistent over '_from';
    document key: 526429; indexed values: ["plant_instances/522789"]

So this is #1436's failure class on a **different write**: that issue fixed the
care *task* insert, whose 1200 arrives through ``_insert_doc``. Edges never went
through ``_insert_doc`` — ``create_edge`` calls the driver directly — so the same
condition on the ``has_care_profile`` unique ``_from`` index still reached the
router as a bare driver exception.

**Round two, measured 2026-09-16 on PR #1498.** The first resolution kept the two
writes separate and cleaned up after a lost race. The required ``Integration tests
(ArangoDB)`` lane then reported ``racers answered with different profiles:
['11770', '11772', '11772', '11772']`` with a single surviving edge and a single
surviving document, both ``11772``: storage was right, one ANSWER was not. The
loser's document had been committed and readable through the non-unique
``plant_key`` field before its edge was refused, so a fourth caller read the
orphan and answered with it. The write is now one transaction
(``create_linked_profile``), which is why the branch below that used to assert the
orphan is deleted now asserts there is no orphan to delete.

The contract pinned here is the two-branched one :class:`WriteConflictError`
requires, because 1200 is a statement about timing and not about data:

* the edge resolves to a profile → the winner committed, and its profile is this
  caller's answer too;
* the edge resolves to nothing → the other transaction rolled back, nothing was
  won, and the conflict keeps propagating.

Solitary: the repository is the owned I/O boundary and is doubled here — against
``spec=ICareReminderRepository``, so a double cannot answer a call the real
repository no longer offers. That ArangoDB really answers 1200/1210 on this index
under contention, and that the transactional write really hides the intermediate
state, is measured in ``tests/integration/test_care_profile_edge_concurrency.py``;
neither tier certifies anything alone, and this one is the one that runs in a CI
gate (#1432).
"""

from __future__ import annotations

from unittest import mock
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import DuplicateError, WriteConflictError
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
from app.domain.models.care_reminder import CareProfile
from app.domain.services.care_reminder_service import (
    _RACE_REREAD_ATTEMPTS,
    _RACE_REREAD_INTERVAL_SECONDS,
    CareReminderService,
)

PLANT = "522789"


def _service(care_repo) -> CareReminderService:
    return CareReminderService(care_repo, CareReminderEngine())


def _losing_repo(*, winner: CareProfile | None, rejection: Exception | None = None) -> MagicMock:
    """A repository whose single transactional profile write loses the race.

    ``spec`` is the real interface on purpose (the #1155 lesson): the double must
    not be able to answer ``create_profile``/``create_profile_edge``, because the
    repository no longer offers them and a test that kept exercising them would
    certify a path production cannot take.
    """
    repo = MagicMock(spec=ICareReminderRepository)
    repo.get_profile_by_plant_key.return_value = None
    repo.create_linked_profile.side_effect = rejection or WriteConflictError("has_care_profile")
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

    def test_the_loser_has_no_orphan_to_delete(self):
        """The cleanup is gone because the state it cleaned up cannot occur.

        The inverse of what this test asserted before #1292 round two. While the
        profile and the edge were two writes, the loser had committed a document no
        edge referenced and had to remove it — and between committing and removing
        it, a third caller could read it through the un-indexed ``plant_key`` field
        and answer with it, which is the defect the round-two fix removes. One
        transaction means the rejected attempt leaves nothing behind, so a delete
        here would be reaching for a document that does not exist.
        """
        repo = _losing_repo(winner=CareProfile(key="theirs", plant_key=PLANT))

        _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert not hasattr(repo, "delete_profile"), (
            "the repository offers a profile delete again; deleting the document while the edge "
            "survives locks the plant out of ever getting a profile (every later create hits the "
            "unique _from index and the edge resolves to nothing)"
        )

    def test_the_profile_and_its_edge_are_written_by_one_call(self):
        """The invariant, stated as a call shape: there is no second write to lose.

        ``get_or_create_profile`` reaches persistence exactly once. A future edit
        that goes back to "insert the document, then link it" reopens the window
        measured on PR #1498, and it cannot do so without failing here — the spec'd
        double has no other write method to call.
        """
        repo = MagicMock(spec=ICareReminderRepository)
        repo.get_profile_by_plant_key.return_value = None
        stored = CareProfile(key="mine", plant_key=PLANT)
        repo.create_linked_profile.return_value = stored

        result = _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert result is stored
        written, linked_to = repo.create_linked_profile.call_args.args
        assert linked_to == PLANT
        assert isinstance(written, CareProfile) and written.plant_key == PLANT
        repo.get_linked_profile.assert_not_called()
        assert not hasattr(ICareReminderRepository, "create_profile_edge"), (
            "the two-step write is spellable again; the transactional guarantee is only as "
            "strong as the absence of a way to write the document on its own"
        )
        assert not hasattr(ICareReminderRepository, "create_profile"), (
            "a care profile can be stored without its edge again — the #1292 window is back"
        )

    def test_a_conflict_with_no_edge_behind_it_keeps_propagating(self):
        """1200 is not "it already exists" — with nothing linked, it is a real failure.

        Absorbing it would hand back a profile whose ``has_care_profile`` edge does
        not exist, so every later graph read of that plant would find none.
        """
        repo = _losing_repo(winner=None)

        with pytest.raises(WriteConflictError):
            _service(repo).get_or_create_profile(PLANT, may_create=True)

    def test_the_other_rejection_code_resolves_the_same_way(self):
        """ArangoDB answers this index with ``1210`` as well as with ``1200``.

        Not a hypothetical: the race in
        ``tests/integration/test_care_profile_edge_concurrency.py`` produced both
        codes from the same burst against a real server — 1200 in the nightly's
        traceback, 1210 locally, and the probe behind the transactional write
        reproduced the split exactly (1210 against a committed winner, 1200 —
        ``timeout waiting to lock key`` — against one still open). Handling only the
        one that happened to be measured first would have left the 500 in place half
        the time.
        """
        winner = CareProfile(key="theirs", plant_key=PLANT)
        repo = _losing_repo(winner=winner, rejection=DuplicateError("has_care_profile", "_from", PLANT))

        result = _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert result is winner

    def test_the_other_rejection_code_also_keeps_propagating_when_nothing_is_linked(self):
        """The two-branch contract is not weakened for ``1210`` either."""
        repo = _losing_repo(winner=None, rejection=DuplicateError("has_care_profile", "_from", PLANT))

        with pytest.raises(DuplicateError):
            _service(repo).get_or_create_profile(PLANT, may_create=True)

    def test_a_1200_loser_re_reads_until_the_winner_commits(self):
        """SCR-001: one read is not enough for ``1200``, and the transaction made it worse.

        ``1200`` says a concurrent transaction HELD the unique ``_from`` entry — not
        that it committed. Since #1292 that entry is held from the edge insert until
        ``commit_transaction`` instead of for the microseconds a bare insert took, so
        a loser can be refused while the winner's commit is still in flight. A single
        re-read then answers ``None`` and the caller re-raises a 409 for a profile
        that exists a moment later.

        The double answers ``None`` twice and then the winner. Against a resolver
        that reads once this raises, which is the red this test was written for.
        """
        winner = CareProfile(key="theirs", plant_key=PLANT)
        repo = _losing_repo(winner=None)
        repo.get_linked_profile.side_effect = [None, None, winner]

        result = _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert result is winner
        assert repo.get_linked_profile.call_count == 3, (
            "the loop stopped re-reading; a winner committing after the first read is missed again"
        )

    def test_the_wait_is_bounded_and_then_the_conflict_stands(self):
        """A winner that never appears stays a failure — the loop may not hide one.

        Bounded at ``_RACE_REREAD_ATTEMPTS`` reads; after that the ``1200``
        propagates, because reporting success would hand back a profile whose link
        does not exist.
        """
        repo = _losing_repo(winner=None)

        with pytest.raises(WriteConflictError):
            _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert repo.get_linked_profile.call_count == _RACE_REREAD_ATTEMPTS

    def test_the_loop_really_waits_rather_than_spinning(self):
        """A retry loop that re-creates the bad moment is inert and looks robust.

        This one does not re-attempt anything — it repeats a *read* against state
        another transaction is committing — but "it sleeps between reads" is the
        part that makes each iteration a genuinely later observation, so it is
        measured rather than asserted in prose.
        """
        repo = _losing_repo(winner=None)
        slept: list[float] = []

        with (
            mock.patch("app.domain.services.care_reminder_service.time.sleep", slept.append),
            pytest.raises(WriteConflictError),
        ):
            _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert slept == [_RACE_REREAD_INTERVAL_SECONDS] * (_RACE_REREAD_ATTEMPTS - 1), (
            "a sleep per gap between reads, and none after the last one"
        )

    def test_a_1210_loser_reads_exactly_once(self):
        """``1210`` is a statement about committed data; re-reading would only add latency.

        Kept apart from the ``1200`` branch deliberately: giving both the loop would
        make a genuine duplicate-key failure take the full wait before answering.
        """
        repo = _losing_repo(winner=None, rejection=DuplicateError("has_care_profile", "_from", PLANT))

        with pytest.raises(DuplicateError):
            _service(repo).get_or_create_profile(PLANT, may_create=True)

        assert repo.get_linked_profile.call_count == 1

    def test_a_read_never_reaches_the_conflicting_write_at_all(self):
        """``may_create=False`` still writes nothing — the #1422 boundary stays put."""
        repo = _losing_repo(winner=CareProfile(key="theirs", plant_key=PLANT))

        _service(repo).get_or_create_profile(PLANT, may_create=False)

        repo.create_linked_profile.assert_not_called()
