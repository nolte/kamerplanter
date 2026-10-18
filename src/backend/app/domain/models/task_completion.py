"""The atomic completion transition of a task (REQ-053 §12.3, §13; ADR-008 phase 3 for tasks, E-02; WP 4.3).

``POST /tasks/{key}/complete`` and ``POST /tasks/batch/status`` (action ``complete``) carry the care fields of
GP-API-031 / GP-API-032; ``POST /tasks/{key}/reopen`` carries ``undo``. This module holds the three kinds of value
that cross the layers:

* :class:`TaskCompletionDetails` — what the *client* may send besides the task fields. Like
  :class:`~app.domain.models.care_event.CareEventInput` it carries no ``trigger``, ``task_key``, ``source_ref``,
  performer or ``tenant_key`` (SR-009, GP-NFR-054): the transition sets them.
* :class:`CompletionActor` — the verified caller (token user and tenant role); the transition never takes it from
  a body.
* :class:`CompletionWrite` / :class:`UndoWrite` — everything one transaction writes, computed **before** the
  transaction opens (the pattern of :class:`~app.domain.models.garden_plan.PlanBatchWrite`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.enums import TenantRole
from app.domain.models.care_event import (
    CARE_EVENT_UNITS,
    MAX_PLANTS_PER_EVENT,
    OUTCOME_RATINGS,
    UNDO_REASON,
    CareEvent,
    Measurement,
    ProductRef,
)

#: GP-FR-088: tasks one batch completion may carry (``batch_too_large`` beyond).
MAX_BATCH_COMPLETION = 200


class TaskCompletionDetails(BaseModel):
    """The optional care fields of a completion (GP-API-031). Every field is optional (GP-FR-084).

    ``extra="forbid"``: a client that sends ``trigger``, ``source_ref``, ``performed_by_user_key`` and the like
    gets a 422 instead of a silently ignored field.
    """

    model_config = ConfigDict(extra="forbid")

    #: When the care was done; default now. V-11: at most five minutes ahead, at most a year back.
    performed_at: datetime | None = None
    #: Subset of the plants standing in the task's bed; empty means the whole bed (GP-FR-100).
    plant_keys: list[str] = Field(default_factory=list, max_length=MAX_PLANTS_PER_EVENT)
    reason: str | None = Field(default=None, max_length=1000)
    product_ref: ProductRef | None = None
    product_label: str | None = Field(default=None, max_length=200)
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = None
    material: str | None = Field(default=None, max_length=200)
    measurements: list[Measurement] | None = Field(default=None, max_length=50)
    observed_outcome: str | None = Field(default=None, max_length=2000)
    outcome_rating: str = "unknown"

    @field_validator("unit")
    @classmethod
    def _known_unit(cls, value: str | None) -> str | None:
        if value is not None and value not in CARE_EVENT_UNITS:
            raise ValueError(f"Unknown unit '{value}'.")
        return value

    @field_validator("outcome_rating")
    @classmethod
    def _known_rating(cls, value: str) -> str:
        if value not in OUTCOME_RATINGS:
            raise ValueError(f"Unknown outcome rating '{value}'.")
        return value

    @field_validator("performed_at")
    @classmethod
    def _aware(cls, value: datetime | None) -> datetime | None:
        """A naive instant is read as UTC (§20.13: ``performed_at`` is UTC)."""
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.quantity is not None and self.unit is None:
            raise ValueError("A quantity needs a unit.")
        if len(set(self.plant_keys)) != len(self.plant_keys):
            raise ValueError("plant_keys must not repeat a key.")
        return self

    def details(self) -> TaskCompletionDetails:
        """The care fields alone: a request body that extends this model hands the service this plain value."""
        return TaskCompletionDetails.model_validate(self.model_dump(include=set(TaskCompletionDetails.model_fields)))

    @property
    def carries_care_fields(self) -> bool:
        """Whether the client said anything beyond the instant (such a body needs a bed to log into)."""
        return bool(
            self.plant_keys
            or self.reason
            or self.product_ref
            or self.product_label
            or self.quantity is not None
            or self.material
            or self.measurements
            or self.observed_outcome
            or self.outcome_rating != "unknown"
        )


@dataclass(frozen=True)
class CompletionActor:
    """The verified caller of a completion: the token's user and the tenant role (GP-NFR-054)."""

    user_key: str
    role: TenantRole


@dataclass(frozen=True)
class DomainDocument:
    """One specialist document the completion writes beside the care event (§12.1).

    ``edges_out`` run from the new document to ``other_id``, ``edges_in`` from ``other_id`` to it; each entry is
    ``(edge collection, other vertex id, attributes)``.
    """

    collection: str
    document: dict[str, Any]
    edges_out: tuple[tuple[str, str, dict[str, Any]], ...] = ()
    edges_in: tuple[tuple[str, str, dict[str, Any]], ...] = ()


@dataclass(frozen=True)
class CompletionWrite:
    """What one task's completion writes: the task patch, the care event and the specialist document."""

    task_key: str
    #: JSON-shaped fields of the task to set (``status``, ``completed_at`` …); ``None`` is stored as ``null``.
    task_patch: dict[str, Any]
    #: ``None`` for a task without a bed context — the task is then updated alone.
    event: CareEvent | None = None
    domain: DomainDocument | None = None
    #: The open care line of an earlier completion of this task (the task was reopened without an undo) that this
    #: completion replaces: voided with ``void_reason = reopened`` and its specialist document removed in the same
    #: transaction. Set by the service only for a caller who could void that line themselves (its author, or a lead).
    replaces_event_key: str | None = None


@dataclass(frozen=True)
class CompletedTask:
    """What the transaction answers per task: the stored care event key and the specialist document."""

    task_key: str
    event_key: str | None = None
    domain_ref: dict[str, str] | None = None


@dataclass(frozen=True)
class UndoWrite:
    """``reopen`` with ``undo``: the task is reopened and its care event voided in one transaction (GP-FR-149)."""

    task_key: str
    task_patch: dict[str, Any]
    #: The head of the task's care-event chain; ``None`` when the task logged nothing.
    event_key: str | None
    voided_by: str
    voided_at: datetime
    void_reason: str = UNDO_REASON
    #: Statuses the stored task may have when the transaction runs; anything else aborts it.
    expected_statuses: tuple[str, ...] = field(default=("completed", "skipped"))
