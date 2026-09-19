"""#1525 SCR-009 — a lost notification refresh must not be swallowed as "some error".

``NotificationPropagationService._update_single`` wrote the refreshed row inside a
bare ``except Exception: logger.warning(...)``. #1515 then mapped ArangoDB's 1200
write-write conflict onto :class:`WriteConflictError` in that very write path, so the
broad clause quietly started absorbing a **retryable** failure.

What is lost when it is absorbed is not cosmetic: the row keeps the previous
occurrence's title and body, and under ``reset_read`` its read state — so a care
occurrence the user has not seen stays out of the unread list and the badge (#769),
which filter strictly on ``read_at == null``. That is the single-entry guarantee this
service exists to provide.

The rule measured here:

* a write-write conflict is retried **once**, and the second attempt's success is the
  normal outcome;
* sustained contention is a warning carrying the attempt count, not a spin;
* a row that vanished between lookup and write is not an error at all;
* anything else propagates — an unforeseen failure has to surface rather than be
  filed as a warning line nobody reads.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.common.exceptions import NotFoundError, WriteConflictError
from app.domain.models.notification import Notification
from app.domain.services.notification_propagation_service import NotificationPropagationService

_GROUP = "care.watering:plant-basil"
_TENANT = "tenant-alpha"
_USER = "user-erika"


def _stored() -> Notification:
    return Notification(
        key="n-1",
        tenant_key=_TENANT,
        user_key=_USER,
        notification_type="care.watering",
        title="Basil",
        body="Giessen faellig",
        group_key=_GROUP,
        read_at=datetime(2026, 3, 1, 9, tzinfo=UTC),
        acted_at=datetime(2026, 3, 1, 9, 0, 1, tzinfo=UTC),
    )


#: How each failure the double raises is constructed — with the **production**
#: signature, so the double cannot certify a shape the real raiser never produces.
#: ``NotFoundError`` takes ``(entity, key)``; ``WriteConflictError`` takes
#: ``(entity)``; ``RuntimeError`` stands for "something nobody anticipated".
_FAILURES = {
    WriteConflictError: lambda: WriteConflictError("notifications"),
    NotFoundError: lambda: NotFoundError("Notification", "n-1"),
    RuntimeError: lambda: RuntimeError("the driver fell over"),
}


class _Repo:
    """Repository double that fails the first ``n`` writes with ``failure``."""

    def __init__(self, failures: int = 0, failure: type[Exception] = WriteConflictError) -> None:
        self._remaining = failures
        self._failure = _FAILURES[failure]
        self.written: list[Notification] = []
        self.attempts = 0

    def update(self, key: str, model: Notification) -> Notification:
        self.attempts += 1
        if self._remaining > 0:
            self._remaining -= 1
            raise self._failure()
        self.written.append(model)
        return model


def _refresh(repo: _Repo, keep: Notification) -> None:
    """Drive the private write the way ``_update_single`` does, with ``reset_read``."""
    service = NotificationPropagationService(repo)
    service._update_single(
        [keep],
        user_key=_USER,
        title="Basil",
        body="Giessen faellig (neue Runde)",
        data={"plant_key": "plant-basil"},
        reset_read=True,
    )


class TestTheRefreshSurvivesOneConflict:
    def test_a_single_conflict_is_retried_and_the_row_is_written(self):
        repo = _Repo(failures=1)

        _refresh(repo, _stored())

        assert repo.attempts == 2, "the conflict was not retried"
        assert len(repo.written) == 1
        assert repo.written[0].body == "Giessen faellig (neue Runde)"

    def test_the_retry_still_carries_the_read_reset(self):
        """The retry must write the *refreshed* model, not a re-read of the old one.

        Without this the retry could be satisfied by any successful second write, and
        the read state — the reason ``reset_read`` exists — would be free to survive.
        """
        repo = _Repo(failures=1)

        _refresh(repo, _stored())

        assert repo.written[0].read_at is None
        assert repo.written[0].acted_at is None

    def test_sustained_contention_gives_up_after_the_second_attempt(self):
        repo = _Repo(failures=5)

        _refresh(repo, _stored())

        assert repo.attempts == 2, "the write must not spin on a contended row"
        assert repo.written == []

    def test_a_vanished_row_is_not_retried(self):
        """A concurrent delete leaves nothing to refresh; that is not a conflict."""
        repo = _Repo(failures=5, failure=NotFoundError)

        _refresh(repo, _stored())

        assert repo.attempts == 1

    def test_an_unexpected_failure_propagates(self):
        """The half the bare ``except Exception`` removed.

        A failure nobody anticipated has to reach the caller. Swallowing it is how a
        broken propagation path stays green for months.
        """
        repo = _Repo(failures=1, failure=RuntimeError)

        with pytest.raises(RuntimeError):
            _refresh(repo, _stored())
