"""Persistence of the atomic task completion (REQ-053 §12.3, GP-FR-083, GP-FR-149; WP 4.3).

One method per transition, each **one transaction** over the task, the care event, the specialist document and the
edges. The service computes everything it needs (validation, the documents) before it calls; the repository only
re-checks what a concurrent request could have changed — the task's status — inside the transaction.

Every method takes the tenant keyword-only without a default and filters on it in the statement: a task of
another tenant answers exactly like an absent one.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.models.care_event import CareEvent
from app.domain.models.task_completion import CompletedTask, CompletionWrite, UndoWrite


class ITaskCompletionRepository(ABC):
    @abstractmethod
    def plant_location(self, plant_key: str, *, tenant_key: str) -> str | None:
        """The location key the tenant's plant stands in; ``None`` for a foreign, absent or unplaced plant."""

    @abstractmethod
    def plants_in_locations(self, location_keys: list[str], *, tenant_key: str) -> list[str]:
        """The keys of the tenant's plants standing in one of ``location_keys`` and not removed, oldest key first."""

    @abstractmethod
    def task_event(self, task_key: str, *, tenant_key: str) -> CareEvent | None:
        """The open head of the care-event chain the task was logged as: not voided, not superseded.

        ``None`` when the task logged nothing (or the tenant's task is absent).
        """

    @abstractmethod
    def complete(self, writes: Sequence[CompletionWrite], *, tenant_key: str) -> list[CompletedTask]:
        """Complete every task of ``writes`` in ONE transaction — all of them or none.

        Per task, in this order: the stored status is re-read (``ValidationError`` when it is no longer
        ``pending`` / ``in_progress``, ``NotFoundError`` when the tenant has no such task), the specialist document
        and its edges are inserted, the care event is stored with ``source_ref`` pointing at the document (and its
        ``care_event_at`` / ``care_event_for`` / ``task_logged_as`` edges), and the task patch is applied.
        """

    @abstractmethod
    def reopen(self, write: UndoWrite, *, tenant_key: str) -> None:
        """Reopen the task and — when ``write.event_key`` is set — void its care event, in ONE transaction.

        Raises:
            NotFoundError: the task is absent or another tenant's.
            ValidationError: the task is no longer ``completed`` / ``skipped``.
            PlanError: ``care_event.sequence`` — the event is voided or superseded since the service read it.
        """
