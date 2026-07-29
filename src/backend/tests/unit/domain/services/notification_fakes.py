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

from app.domain.models.notification import Notification


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

    def list_by_group_key(self, group_key: str, tenant_key: str) -> list[Notification]:
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
