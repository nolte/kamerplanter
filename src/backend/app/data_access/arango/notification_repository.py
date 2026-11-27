"""ArangoDB repository for notifications."""

from datetime import UTC, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.notification_repository import INotificationRepository
from app.domain.models.notification import (
    DUE_DATE_SHAPE,
    WATERING_REMINDER_GROUP_PREFIX,
    WATERING_REMINDER_TYPE,
    Notification,
    NotificationStatus,
)

# Collection constants
NOTIFICATIONS = "notifications"


class ArangoNotificationRepository(BaseArangoRepository[Notification], INotificationRepository):
    """ArangoDB-backed notification repository."""

    _model_cls = Notification
    #: Every row belongs to exactly one tenant; a base list read without a
    #: ``tenant_key`` (or an explicit ``all_tenants=True``) raises (MT-023, #2119).
    is_tenant_scoped = True

    #: Full-replace null semantics for ``notifications`` (#1516).
    #:
    #: ``NotificationPropagationService._update_single`` nulls ``read_at`` and
    #: ``acted_at`` under ``reset_read`` so a notification whose subject materially
    #: changed re-surfaces in the badge (#769). In the inherited merge mode both
    #: were dropped and the row stayed read — the re-surfacing never happened.
    #:
    #: **The one full-model writer starts from the stored notification**, so it
    #: cannot lose a field it never mentioned (re-measured 2026-11-26 over every
    #: ``update`` on this repository; a second writer, the overdue escalation's
    #: stamp in ``NotificationEngine.escalate_overdue``, became the partial
    #: ``claim_escalation_level`` in ADR-008 F-8):
    #:
    #: * ``NotificationPropagationService._update_single`` — ``_safe_lookup`` then
    #:   attribute assignment on the loaded row.
    #:
    #: ``mark_read``/``mark_acted``/``claim_escalation_level`` are hand-written AQL
    #: ``UPDATE ... WITH`` statements and set their field explicitly; every other
    #: engine path only ``create``s.
    _update_is_full_replace = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, NOTIFICATIONS)

    def _to_notification(self, doc: dict) -> Notification:
        """Convert ArangoDB document to Notification model."""
        return Notification(**self._from_doc(doc))

    # ── CRUD ──────────────────────────────────────────────────────────

    def create(self, model: Notification, *, default_now_fields: tuple[str, ...] = ()) -> Notification:
        """Insert a notification — never one without a recipient (MT-045.8, #2144).

        Every reader is per user (``doc.user_key == @user_key``): a row with an empty
        ``user_key`` lands in no inbox, and was readable and actionable by key for every
        member of the tenant until the readers failed closed. There is no tenant
        broadcast; the one choke point all five writers pass refuses the shape.
        """
        if not model.user_key:
            raise ValueError("A notification needs a recipient (user_key); there is no tenant broadcast.")
        return super().create(model, default_now_fields=default_now_fields)

    def get(self, key: str) -> Notification | None:
        return super().get_by_key(key)

    def update(self, key: str, model: Notification) -> Notification:
        """Rewrite a notification from a full model — except its ``escalation_level`` (#3135).

        The level is owned by two conditional statements, :meth:`claim_escalation_level`
        and :meth:`reset_escalation_level`. The one full-model writer
        (``NotificationPropagationService._update_single``) read the row before it
        writes and compares no ``_rev``; writing the level it read would undo a claim
        that landed in between, and the level would be sent a second time. Left out
        of the write, the stored level stays as it is at write time.
        """
        if self._verify_references_on_update:
            self._verify_changed_owned_references(key, model)
        return cast(Notification, self._wrap(self._update_doc(key, model, untouched=("escalation_level",))))

    # ── Queries ───────────────────────────────────────────────────────

    def list_for_user(
        self,
        user_key: str,
        tenant_key: str | None = None,
        status: NotificationStatus | None = None,
        notification_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """List notifications for a user, sorted by created_at DESC.

        Supports optional filtering by tenant, status (for unread_only),
        and notification type.
        """
        filters = ["doc.user_key == @user_key"]
        bind_vars: dict = {
            "user_key": user_key,
            "limit": limit,
            "offset": offset,
        }

        if tenant_key is not None:
            filters.append("doc.tenant_key == @tenant_key")
            bind_vars["tenant_key"] = tenant_key

        if status is not None:
            # For unread_only: status=DELIVERED means read_at IS NULL
            filters.append("doc.read_at == null")

        if notification_type is not None:
            filters.append("doc.notification_type == @notification_type")
            bind_vars["notification_type"] = notification_type

        filter_clause = " AND ".join(filters)

        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER {filter_clause} "
            f"SORT DATE_TIMESTAMP(doc.created_at) DESC "
            f"LIMIT @offset, @limit "
            f"RETURN doc"
        )

        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._to_notification(doc) for doc in cursor]

    def list_for_user_since(
        self,
        user_key: str,
        since: datetime,
        limit: int = 100,
    ) -> list[Notification]:
        """List a user's notifications created at/after ``since``, newest first.

        Used by the daily email digest (REQ-030) to collect the notifications
        of the trailing window.
        """
        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER doc.user_key == @user_key "
            f"AND DATE_TIMESTAMP(doc.created_at) != null "
            f"AND DATE_TIMESTAMP(doc.created_at) >= DATE_TIMESTAMP(@since) "
            f"SORT DATE_TIMESTAMP(doc.created_at) DESC "
            f"LIMIT @limit "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "user_key": user_key,
                "since": since.isoformat(),
                "limit": limit,
            },
        )
        return [self._to_notification(doc) for doc in cursor]

    def mark_read(self, key: str, read_at: datetime) -> Notification | None:
        """Mark a notification as read."""
        query = f"UPDATE @key WITH {{ read_at: @read_at, updated_at: @read_at }} IN {NOTIFICATIONS} RETURN NEW"
        cursor = self._db.aql.execute(
            query,
            bind_vars={"key": key, "read_at": read_at.isoformat()},
        )
        doc = next(cursor, None)
        if doc is None:
            return None
        return self._to_notification(doc)

    def mark_acted(self, key: str, acted_at: datetime) -> Notification | None:
        """Mark a notification action as performed."""
        query = f"UPDATE @key WITH {{ acted_at: @acted_at, updated_at: @acted_at }} IN {NOTIFICATIONS} RETURN NEW"
        cursor = self._db.aql.execute(
            query,
            bind_vars={"key": key, "acted_at": acted_at.isoformat()},
        )
        doc = next(cursor, None)
        if doc is None:
            return None
        return self._to_notification(doc)

    def claim_escalation_level(
        self, key: str, *, tenant_key: str, escalation_level: int, due_date: str
    ) -> Notification | None:
        """Raise ``escalation_level`` by exactly one step, atomically, only for the tenant's row (ADR-008 F-8).

        One AQL statement — filter and update are evaluated in the same write, so
        two overlapping escalation runs cannot both claim the same level (a
        read-then-update could, because :meth:`update` compares no ``_rev``). The
        stored level must be exactly ``escalation_level - 1`` (#3135): a run that
        read the row at an older level cannot jump it over a level another run has
        claimed meanwhile. A row stored without a level counts as level 0, the
        model's default, as in :meth:`find_overdue_watering`.

        The row must also still be the overdue occurrence the candidate was selected
        as (#3135): not acted on, and announcing the same ``data.due_date`` the
        caller read. Between :meth:`find_overdue_watering` and this claim the user
        can water the plant, or a sync can announce the next occurrence on the same
        row; the claim then writes nothing, and no "overdue" goes out for a watering
        that is done or for an occurrence that is not due. The ``UPDATE … WITH``
        is partial: ``read_at``/``acted_at`` and every other field stay as stored.
        An empty ``tenant_key`` claims nothing.
        """
        if not tenant_key or not key or not due_date:
            return None
        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER doc._key == @key AND doc.tenant_key == @tenant_key "
            f"AND NOT_NULL(doc.escalation_level, 0) == @previous_level "
            f"AND doc.acted_at == null "
            f"AND doc.data.due_date == @due_date "
            f"UPDATE doc WITH {{ escalation_level: @level, updated_at: @now }} IN {NOTIFICATIONS} "
            f"RETURN NEW"
        )
        bind_vars: dict[str, Any] = {
            "key": key,
            "tenant_key": tenant_key,
            "level": escalation_level,
            "previous_level": escalation_level - 1,
            "due_date": due_date,
            "now": datetime.now(UTC).isoformat(),
        }
        cursor = cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars))
        doc = next(cursor, None)
        if doc is None:
            return None
        return self._to_notification(doc)

    def find_overdue_watering(
        self,
        overdue_since: datetime,
        escalation_level: int,
        *,
        tenant_key: str,
    ) -> list[Notification]:
        """Find the tenant's watering reminders due before ``overdue_since`` at ``escalation_level``.

        Matches (#3135 — the reading :func:`~app.domain.models.notification.announced_due_date`
        describes, held for this statement and the unit fake by one case table,
        ``tests/support/overdue_watering_cases.py``):

        - ``tenant_key`` == the given tenant (an empty tenant matches nothing)
        - ``notification_type`` == ``care.watering`` exactly — the escalation rows
          (``care.watering.escalation``) it sends are never candidates themselves
        - ``group_key`` starts with ``care.watering:`` — the plant's one reminder row,
          the one the propagation owner keeps in step with the task and a watering
          closes; the due-care dispatch's per-day rows are delivery, not a reminder
        - ``acted_at`` IS NULL
        - the **announced due date** ``data.due_date`` is a string of
          :data:`~app.domain.models.notification.DUE_DATE_SHAPE` naming a real
          calendar date, and lies before the cutoff, compared as instants. Not
          ``created_at``: the row is reused across occurrences and keeps its
          creation time. Anything else is not proven overdue and not selected; the
          shape test runs first, so ``DATE_TIMESTAMP`` never sees an unreadable
          string (no warning, whatever ``failOnWarning`` the server runs with).
        - ``escalation_level`` == the given level, a row without one counting as 0
        """
        if not tenant_key:
            return []
        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER doc.tenant_key == @tenant_key "
            f"AND doc.notification_type == @notification_type "
            f"AND STARTS_WITH(doc.group_key, @group_prefix) "
            f"AND doc.acted_at == null "
            f"AND NOT_NULL(doc.escalation_level, 0) == @level "
            f"AND IS_STRING(doc.data.due_date) "
            f"AND REGEX_TEST(doc.data.due_date, @due_shape) "
            f"AND LEFT(DATE_ISO8601(LEFT(doc.data.due_date, 10)), 10) == LEFT(doc.data.due_date, 10) "
            f"AND DATE_TIMESTAMP(doc.data.due_date) < DATE_TIMESTAMP(@cutoff) "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "cutoff": overdue_since.isoformat(),
                "due_shape": DUE_DATE_SHAPE,
                "group_prefix": WATERING_REMINDER_GROUP_PREFIX,
                "level": escalation_level,
                "notification_type": WATERING_REMINDER_TYPE,
                "tenant_key": tenant_key,
            },
        )
        return [self._to_notification(doc) for doc in cursor]

    def reset_escalation_level(self, key: str, *, tenant_key: str) -> bool:
        """Start a new escalation cycle on the tenant's row: ``escalation_level`` back to 0 (#3135).

        Its own conditional statement, not part of :meth:`update`: the full write
        of a reminder refresh leaves the level alone (it may hold a level a
        concurrent claim raised after the refresh read the row). Only a new
        occurrence resets it, and only here. Returns whether a row was reset.
        """
        if not tenant_key or not key:
            return False
        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER doc._key == @key AND doc.tenant_key == @tenant_key "
            f"AND NOT_NULL(doc.escalation_level, 0) != 0 "
            f"UPDATE doc WITH {{ escalation_level: 0, updated_at: @now }} IN {NOTIFICATIONS} "
            f"RETURN 1"
        )
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query,
                bind_vars={"key": key, "tenant_key": tenant_key, "now": datetime.now(UTC).isoformat()},
            ),
        )
        return next(cursor, None) is not None

    def exists_by_group_key(self, group_key: str, *, tenant_key: str) -> bool:
        """Return whether the tenant has any notification carrying ``group_key``.

        Existence-only primitive: ``LIMIT 1 RETURN 1`` stops at the first match and
        maps no documents. Backs cross-run idempotency for producers that must emit
        a group at most once (e.g. one frost forecast warning per
        ``(site_key, forecast_date)``). Index-backed (Issue #409, F2) by the
        ``(group_key, tenant_key)`` persistent index.
        """
        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER doc.group_key == @group_key AND doc.tenant_key == @tenant_key "
            f"LIMIT 1 "
            f"RETURN 1"
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={"group_key": group_key, "tenant_key": tenant_key},
        )
        return next(cursor, None) is not None

    def list_by_group_key(self, group_key: str, *, tenant_key: str) -> list[Notification]:
        """Return every notification carrying ``(group_key, tenant_key)`` (newest first).

        Strictly tenant-scoped (SEC-B4): the ``tenant_key`` is bound into the filter
        so a source→notification mutation (Issue #742) can never reach another
        tenant's rows. Index-backed by the ``(group_key, tenant_key)`` persistent
        index (Issue #409, F2).
        """
        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER doc.group_key == @group_key AND doc.tenant_key == @tenant_key "
            f"SORT DATE_TIMESTAMP(doc.created_at) DESC "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={"group_key": group_key, "tenant_key": tenant_key},
        )
        return [self._to_notification(doc) for doc in cursor]

    def find_notified_user_keys(self, group_key: str, *, tenant_key: str) -> set[str]:
        """Return the ``user_key`` set already notified for ``(group_key, tenant_key)``.

        Projected, index-backed read (``RETURN DISTINCT doc.user_key``) — full
        documents are never materialised. Backs the per-recipient top-up (Issue
        #409, F3): a later run sends only to members NOT already in this set. Rows
        without a ``user_key`` are ignored so they never poison the set.
        """
        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER doc.group_key == @group_key AND doc.tenant_key == @tenant_key "
            f"AND doc.user_key != null "
            f"RETURN DISTINCT doc.user_key"
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={"group_key": group_key, "tenant_key": tenant_key},
        )
        return {user_key for user_key in cursor if user_key}

    def count_unread(self, user_key: str, tenant_key: str | None = None) -> int:
        """Count unread notifications for a user."""
        filters = ["doc.user_key == @user_key", "doc.read_at == null"]
        bind_vars: dict = {"user_key": user_key}

        if tenant_key is not None:
            filters.append("doc.tenant_key == @tenant_key")
            bind_vars["tenant_key"] = tenant_key

        filter_clause = " AND ".join(filters)

        query = f"RETURN LENGTH(FOR doc IN {NOTIFICATIONS} FILTER {filter_clause} RETURN 1)"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)

    def create_edges(
        self,
        notification_key: str,
        task_keys: list[str],
        plant_keys: list[str],
    ) -> None:
        """Create edges from notification to related tasks and plants."""
        notif_id = f"{NOTIFICATIONS}/{notification_key}"

        for task_key in task_keys:
            task_id = f"{col.TASKS}/{task_key}"
            self.create_edge("notified_about_task", notif_id, task_id)

        for plant_key in plant_keys:
            plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
            self.create_edge("notified_about_plant", notif_id, plant_id)
