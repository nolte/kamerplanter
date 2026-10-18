"""Persistence of the care log (REQ-053 §13, §20.10; WP 4.1, #2400).

Every read takes the tenant keyword-only without a default: ``care_events`` carry ``tenant_key`` (E-01, §20.13)
and a foreign event answers exactly like an absent one (``None`` / empty), never a different error.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.models.care_event import CareEvent


@dataclass(frozen=True)
class CareEventRow:
    """A stored event with the display names its account references resolve to (never the keys themselves)."""

    event: CareEvent
    #: Display name of ``performed_by_user_key``; ``None`` when the account is gone or erased.
    performed_by_name: str | None = None
    performed_for_name: str | None = None


@dataclass(frozen=True)
class CareEventFilter:
    """The filters of ``GET /care-events`` (GP-API-034)."""

    location_key: str | None = None
    plant_key: str | None = None
    category: str | None = None
    performed_from: datetime | None = None
    performed_to: datetime | None = None
    #: An account key the caller took from the member list; matches ``performed_by_user_key``.
    performed_by: str | None = None
    include_superseded: bool = False


@dataclass
class AnonymizedBatch:
    """What one retention batch changed (NFR-011 R-25)."""

    anonymized: int = 0
    #: ``(tenant_key, attachment_id)`` of every photo the batch detached; the caller deletes the unreferenced ones.
    detached_photos: list[tuple[str, str]] = field(default_factory=list)


class ICareEventRepository(ABC):
    @abstractmethod
    def get(self, key: str, *, tenant_key: str) -> CareEvent | None:
        """The event of ``tenant_key`` behind ``key``; absent and foreign both give ``None``."""

    @abstractmethod
    def get_row(self, key: str, *, tenant_key: str) -> CareEventRow | None:
        """:meth:`get` with the display names of its account references."""

    @abstractmethod
    def chain(self, key: str, *, tenant_key: str) -> list[CareEvent]:
        """Every event of ``key``'s supersede chain, oldest first (empty when ``key`` is not the tenant's)."""

    @abstractmethod
    def list_events(self, criteria: CareEventFilter, *, tenant_key: str, offset: int, limit: int) -> list[CareEventRow]:
        """One page of the tenant's care log, newest ``performed_at`` first."""

    @abstractmethod
    def plants_in_locations(self, plant_keys: list[str], location_keys: list[str], *, tenant_key: str) -> set[str]:
        """The keys among ``plant_keys`` that are the tenant's plants standing in one of ``location_keys``."""

    @abstractmethod
    def insert(self, event: CareEvent, *, tenant_key: str) -> CareEvent:
        """Store the event and its edges (``care_event_at``, ``care_event_for`` per plant, ``task_logged_as``).

        ``tenant_key`` must be the event's own: a repository that writes a tenant's row takes the tenant it
        writes under, so the write cannot name one tenant and store another's.
        """

    @abstractmethod
    def supersede(self, predecessor_key: str, event: CareEvent, *, tenant_key: str) -> CareEvent:
        """In one transaction: store ``event`` and set ``superseded_by_key`` on its predecessor (V-13).

        Raises:
            NotFoundError: the predecessor is gone or not the tenant's.
            PlanError: ``care_event.sequence`` — the predecessor is superseded or voided already.
        """

    @abstractmethod
    def void(self, key: str, *, tenant_key: str, voided_by: str, reason: str, at: datetime) -> CareEvent:
        """Mark the event voided (``voided_at``, ``voided_by``, ``void_reason``); nothing else changes.

        Raises:
            NotFoundError: the event is gone or not the tenant's.
            PlanError: ``care_event.sequence`` — it is voided or superseded already.
        """

    @abstractmethod
    def redact(
        self, key: str, *, tenant_key: str, redacted_by: str, reason: str, at: datetime
    ) -> tuple[list[CareEvent], list[str]]:
        """Redact the whole supersede chain of ``key`` and write the ``garden_plan_audit`` row, in one transaction.

        Returns the redacted events and the attachment ids the chain referenced before.
        """

    # ── Retention (NFR-011 R-25) — installation-wide sweeps, not tenant reads ──

    @abstractmethod
    def anonymize_expired(
        self, *, cutoff: datetime, pflschg_cutoff: datetime, now: datetime, batch: int
    ) -> AnonymizedBatch:
        """Anonymise up to ``batch`` events past their period: person fields, free texts and photos go."""
