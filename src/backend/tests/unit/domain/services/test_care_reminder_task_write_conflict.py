"""A write-write conflict (ArangoDB 1200) is resolved by a re-read, not by a guess (#1436).

#1301 made the *loser* of a care-task creation race benign — but only for the
answer ArangoDB gives when the winner has already committed: ``1210``, unique
constraint violated, which the repository surfaces as ``DuplicateError``.

The failure measured in #1436 is the other answer:

    [HTTP 409][ERR 1200] write-write conflict - in index care_dedup_open_unique
    of type persistent over 'care_dedup_key'; document key: 800067;
    indexed values: ["tenant-alpha/plant-basil-1/watering"]

``1200`` is ``arango.errno.CONFLICT`` — a *serialization* failure, not a
uniqueness verdict. It means "a concurrent transaction holds this key", which is
not the same claim as "an equivalent task exists": the other transaction may
still roll back. So it may not simply be swallowed the way ``1210`` is. The
contract pinned here is therefore two-branched:

* the re-read finds the open task the conflict pointed at → the caller wanted to
  know whether one exists, the answer is yes, so the outcome is ``None``;
* the re-read finds nothing → the conflict was *not* a lost dedup race and must
  keep propagating, because absorbing it would drop a write silently.

Solitary tests: the repository is the owned I/O boundary and is doubled. That
ArangoDB really answers 1200 on this index under contention is measured in
``tests/integration/test_care_task_dedup_concurrency.py``; neither half certifies
anything alone. This tier is the one that runs in CI at all (#1432).
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import ReminderType
from app.common.exceptions import WriteConflictError
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.services.care_reminder_service import (
    CareReminderService,
    build_care_reminder_task,
    create_care_reminder_task,
)


def _task():
    return build_care_reminder_task(
        plant_key="plant-1",
        plant_label="Basil",
        tenant_key="tenant-a",
        reminder_type=ReminderType.WATERING,
        due_date=datetime(2026, 6, 14, tzinfo=UTC),
    )


def _service(task_repo) -> CareReminderService:
    care_repo = MagicMock()
    care_repo.get_last_confirmation.return_value = None

    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = SimpleNamespace(
        plant_name="Basil",
        instance_id="P-1",
        tenant_key="tenant-a",
    )
    return CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo=task_repo,
        plant_repo=plant_repo,
    )


# ── the public path from the issue: ensure_next_watering_task ────────────────


class TestEnsureNextWateringTaskUnderWriteConflict:
    """The signature under test is the one the issue's racers call."""

    def test_conflict_with_an_open_task_behind_it_resolves_to_none(self):
        """The losing racer gets the winner's answer, not a 409 out of a Celery beat."""
        task_repo = MagicMock()
        open_task = _task()
        task_repo.find_open_care_task.side_effect = [
            None,  # the racing read: "none open"
            open_task,  # the re-read after the conflict: the winner's task
        ]
        task_repo.create_task.side_effect = WriteConflictError("tasks")

        assert _service(task_repo).ensure_next_watering_task(CareProfile(plant_key="plant-1")) is None
        task_repo.create_task.assert_called_once()
        assert task_repo.find_open_care_task.call_count == 2

    def test_reread_mirrors_the_unique_index_and_ignores_the_recency_rule(self):
        """The index is sparse over OPEN tasks only, so the re-read must be too.

        ``find_open_care_task`` also matches a task *completed today* when
        ``include_completed_today`` is left at its default. The unique index does
        not: its computed value is null unless the task is pending/in_progress.
        A re-read carrying the recency rule would therefore report "the winner is
        there" for a task the index never counted — turning a genuine conflict
        into a silently dropped write.
        """
        task_repo = MagicMock()
        task_repo.find_open_care_task.side_effect = [None, _task()]
        task_repo.create_task.side_effect = WriteConflictError("tasks")

        _service(task_repo).ensure_next_watering_task(CareProfile(plant_key="plant-1"))

        reread = task_repo.find_open_care_task.call_args_list[1]
        assert reread.kwargs["include_completed_today"] is False
        assert reread.args[0] == "plant-1"
        assert reread.args[1] == ReminderType.WATERING
        assert reread.args[2] == "tenant-a"

    def test_conflict_without_an_open_task_keeps_propagating(self):
        """1200 is not a dedup answer on its own — with nothing there, it is a real failure.

        Swallowing it here would report "nothing to schedule" for a reminder that
        does not exist, and the plant would never be watered.
        """
        task_repo = MagicMock()
        task_repo.find_open_care_task.side_effect = [None, None]
        task_repo.create_task.side_effect = WriteConflictError("tasks")

        with pytest.raises(WriteConflictError):
            _service(task_repo).ensure_next_watering_task(CareProfile(plant_key="plant-1"))


# ── the shared creator every care-task producer routes through ───────────────


class TestCreateCareReminderTaskUnderWriteConflict:
    def test_resolves_to_none_when_the_reread_finds_the_winner(self):
        repo = MagicMock()
        repo.create_task.side_effect = WriteConflictError("tasks")
        repo.find_open_care_task.return_value = _task()

        assert create_care_reminder_task(repo, _task(), reminder_type=ReminderType.WATERING) is None

    def test_reraises_when_the_reread_finds_nothing(self):
        repo = MagicMock()
        repo.create_task.side_effect = WriteConflictError("tasks")
        repo.find_open_care_task.return_value = None

        with pytest.raises(WriteConflictError):
            create_care_reminder_task(repo, _task(), reminder_type=ReminderType.WATERING)

    def test_reread_is_scoped_to_the_task_being_written(self):
        """A tenant-blind or plant-blind re-read would absorb a foreign tenant's task."""
        repo = MagicMock()
        repo.create_task.side_effect = WriteConflictError("tasks")
        repo.find_open_care_task.return_value = _task()

        create_care_reminder_task(
            repo,
            build_care_reminder_task(
                plant_key="plant-9",
                plant_label="Mint",
                tenant_key="tenant-b",
                reminder_type=ReminderType.FERTILIZING,
                due_date=datetime(2026, 6, 14, tzinfo=UTC),
            ),
            reminder_type=ReminderType.FERTILIZING,
        )

        call = repo.find_open_care_task.call_args
        assert call.args == ("plant-9", ReminderType.FERTILIZING, "tenant-b")
        assert call.kwargs["include_completed_today"] is False


# ── the seam: repository mapping and service handling must meet ──────────────


def test_driver_level_1200_reaches_the_service_as_a_resolved_none():
    """End-to-end over the real production classes, only the driver is doubled.

    The two halves of this fix live in different layers (``_insert_doc`` maps the
    code, ``create_care_reminder_task`` interprets it). Each half is green on its
    own double; this asserts they are actually wired to each other, so a rename
    or a narrowed ``except`` cannot leave the pair inert.
    """
    from arango.exceptions import DocumentInsertError

    from app.data_access.arango.task_repository import ArangoTaskRepository

    conflict = DocumentInsertError.__new__(DocumentInsertError)
    conflict.error_code = 1200
    conflict.error_message = (
        "write-write conflict - in index care_dedup_open_unique of type persistent over 'care_dedup_key'"
    )

    db = MagicMock()
    db.collection.return_value.insert.side_effect = conflict
    winner = _task().model_dump(by_alias=True)
    winner["_key"] = "task-winner"
    db.aql.execute.return_value = iter([winner])

    repo = ArangoTaskRepository(db)

    assert create_care_reminder_task(repo, _task(), reminder_type=ReminderType.WATERING) is None
