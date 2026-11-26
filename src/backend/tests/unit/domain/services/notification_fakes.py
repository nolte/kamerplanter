"""Stateful in-memory notification repository for propagation tests (#742/#769).

The source→notification feedback loop is a *sequence* of repository writes on one
``group_key``: a care confirmation marks the row read, the follow-up reschedule
updates the same row. A stateless mock hides that composition — each hook looks
correct in isolation while the persisted row ends up in a state no query returns
(#769: read, therefore invisible to the badge). :class:`FakeNotificationRepo`
therefore models the repository's *state*, so a write is visible to the very next
lookup exactly as in ArangoDB.

It mirrors the parts of ``ArangoNotificationRepository`` the propagation service
touches:

* ``list_by_group_key`` is tenant-scoped and returns newest first (the ordering
  :meth:`NotificationPropagationService._update_single` relies on to pick the row
  it keeps),
* ``mark_read`` / ``mark_acted`` stamp the fields the unread list and the badge
  count filter on (``FILTER doc.read_at == null``).

:meth:`unread_for` reproduces exactly that badge predicate, so a test can assert
what the user actually sees instead of re-deriving it from field values.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.models.notification import (
    WATERING_ESCALATION_TYPE,
    WATERING_REMINDER_TYPE,
    Notification,
    NotificationStatus,
    announced_due_date,
)


class FakeNotificationRepo:
    """In-memory ``INotificationRepository`` slice used by the propagation tests."""

    def __init__(self) -> None:
        self._store: dict[str, Notification] = {}
        self._seq = 0

    # ── writes ──
    def create(self, notification: Notification) -> Notification:
        self._seq += 1
        key = f"n{self._seq}"
        notification.key = key
        notification.created_at = datetime.now(UTC) + timedelta(seconds=self._seq)
        self._store[key] = notification
        return notification

    def update(self, key: str, notification: Notification) -> Notification:
        notification.key = key
        self._store[key] = notification
        return notification

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def mark_read(self, key: str, read_at: datetime) -> Notification | None:
        notif = self._store.get(key)
        if notif is None:
            return None
        notif.read_at = read_at
        return notif

    def mark_acted(self, key: str, acted_at: datetime) -> Notification | None:
        notif = self._store.get(key)
        if notif is None:
            return None
        notif.acted_at = acted_at
        return notif

    # ── reads ──
    def get(self, key: str) -> Notification | None:
        return self._store.get(key)

    def list_by_group_key(self, group_key: str, *, tenant_key: str) -> list[Notification]:
        rows = [n for n in self._store.values() if n.group_key == group_key and n.tenant_key == tenant_key]
        rows.sort(key=lambda n: n.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return rows

    # ── test helpers ──
    def all_rows(self) -> list[Notification]:
        return list(self._store.values())

    def unread_for(self, user_key: str, tenant_key: str) -> list[Notification]:
        """Return what the unread list / badge count would show for the user.

        Mirrors the ``FILTER doc.read_at == null`` predicate shared by
        ``ArangoNotificationRepository.list_by_user(status=...)`` and
        ``count_unread`` — the single reason a row that keeps its ``read_at``
        never reaches the user (#769).
        """
        return [
            n
            for n in self._store.values()
            if n.user_key == user_key and n.tenant_key == tenant_key and n.read_at is None
        ]


def is_overdue_watering_candidate(
    row: Notification, overdue_since: datetime, escalation_level: int, *, tenant_key: str
) -> bool:
    """The filter of ``ArangoNotificationRepository.find_overdue_watering``, clause by clause (#3135).

    ``tenant_key`` (empty: nothing) · ``notification_type == care.watering`` exactly ·
    ``acted_at == null`` · ``data.due_date`` a readable ISO string before the cutoff,
    as instants (:func:`announced_due_date` reads it like ``DATE_TIMESTAMP``) ·
    ``escalation_level == level``. Held to the same case table as the AQL.
    """
    due = announced_due_date(row)
    return (
        bool(tenant_key)
        and row.tenant_key == tenant_key
        and row.notification_type == WATERING_REMINDER_TYPE
        and row.acted_at is None
        and due is not None
        and due < overdue_since
        and row.escalation_level == escalation_level
    )


class EscalationNotificationRepo(FakeNotificationRepo):
    """The fake plus the escalation surface, modelled on the real AQL (ADR-008 F-8).

    * Every read returns a fresh copy, as ArangoDB materialises a new model per
      document — so a caller holding a stale row is representable.
    * :meth:`find_overdue_watering` applies :func:`is_overdue_watering_candidate`,
      the Python reading of the AQL filter. Both are held to one case table
      (``tests/support/overdue_watering_cases.py``): the unit test
      ``test_overdue_watering_fake_matches_the_case_table`` runs it against this
      fake, the integration test ``test_overdue_watering_candidates`` against
      ArangoDB — so the fake cannot select a row the real statement would not.
    * :meth:`claim_escalation_level` is the single conditional write: key, tenant
      and "level still below" are checked and the level is raised in one step,
      touching no other field. A sequential fake cannot interleave inside it, and
      neither can the real statement — that is the property being modelled, not
      assumed away. Full-model ``update`` calls are recorded so a test can assert
      the escalation path makes none.
    """

    def __init__(self) -> None:
        super().__init__()
        self.updates: list[str] = []
        self.claims: list[tuple[str, int]] = []

    def get(self, key: str) -> Notification | None:
        row = super().get(key)
        return row.model_copy(deep=True) if row is not None else None

    def update(self, key: str, notification: Notification) -> Notification:
        self.updates.append(key)
        return super().update(key, notification.model_copy(deep=True))

    def claim_escalation_level(self, key: str, *, tenant_key: str, escalation_level: int) -> Notification | None:
        row = self._store.get(key)
        if not tenant_key or row is None or row.tenant_key != tenant_key or row.escalation_level >= escalation_level:
            return None
        row.escalation_level = escalation_level
        self.claims.append((key, escalation_level))
        return row.model_copy(deep=True)

    def find_overdue_watering(
        self, overdue_since: datetime, escalation_level: int, *, tenant_key: str
    ) -> list[Notification]:
        return [
            row.model_copy(deep=True)
            for row in self._store.values()
            if is_overdue_watering_candidate(row, overdue_since, escalation_level, tenant_key=tenant_key)
        ]

    def escalations(self) -> list[Notification]:
        return [row for row in self._store.values() if row.notification_type == WATERING_ESCALATION_TYPE]

    def seed_overdue_care_row(
        self,
        *,
        tenant_key: str,
        user_key: str,
        days_old: int = 3,
        group_key: str = "care.watering:plant-1",
    ) -> str:
        """A care note announcing a watering due *days_old* days ago, not acted on (level-0 overdue only).

        The age is the announced due date (``data.due_date``), the field the overdue
        query reads (#3135); ``created_at`` is set to the same instant only so a
        test that sorts by it still sees this row as the older one.
        """
        due = datetime.now(UTC) - timedelta(days=days_old)
        row = self.create(
            Notification(
                tenant_key=tenant_key,
                user_key=user_key,
                notification_type="care.watering",
                title="Monstera",
                body="watering due: Monstera",
                data={"due_date": due.isoformat()},
                group_key=group_key,
                status=NotificationStatus.DELIVERED,
            )
        )
        row.created_at = due
        return row.key or ""
