"""ADR-008 F-8 — the overdue escalation's stamp goes through the propagation owner.

Phase 0 of ADR-008 measured exactly one notification write outside
:class:`NotificationPropagationService` that was neither an event nor a user
action: :meth:`NotificationEngine.escalate_overdue` stamping ``escalation_level``
back onto the *existing* care row (site b1 of
``.audits/adr-008-phase-0-inventory/2026-09-01-inventory.md``). F-8 routes that
stamp through :meth:`NotificationPropagationService.on_notification_escalated`
and makes it the **claim** of the escalation: the engine sends the escalation
notification only when the stamp was written.

The two invariants of the owner are pinned on this edge (F-8 acceptance-2/-3):

* **Idempotent** — a second escalation run produces no second escalation
  notification and no second stamp. Redis dedup is switched off in these tests
  (``redis.get`` → ``None``), so the only thing that can keep the second run quiet
  is the stamp itself.
* **Fail-closed per tenant** — no resolvable tenant writes nothing; a row of
  another tenant is neither stamped nor escalated in this tenant's run.

The engine runs against a **stateful** fake repository (the #769 lesson: a
stateless mock lets every hook look right while the stored row ends up wrong),
which re-materialises rows on every read the way ArangoDB does, so a stale read
is representable.

Traces to issue #1061, feature F-8 (no TC-ID: unit tests of a service edge).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.common.exceptions import WriteConflictError
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.notification import (
    Notification,
    NotificationPreferences,
    NotificationStatus,
)
from app.domain.services.notification_propagation_service import NotificationPropagationService
from tests.unit.domain.services.notification_fakes import FakeNotificationRepo

TENANT = "tenant-A"
OTHER_TENANT = "tenant-B"
USER = "user-a"
CARE_GROUP = "care.watering:plant-1"
ESCALATION_TYPE = "care.watering.escalation"


class _StoredNotificationRepo(FakeNotificationRepo):
    """The fake plus the escalation query, re-materialising rows per read like ArangoDB.

    ``find_overdue_watering`` mirrors the real AQL: **not** tenant-scoped (a
    system read, see ``test_tenant_scoped_reads_are_derived.py``), type prefix
    ``care.watering``, not acted upon, older than the cutoff, at exactly the
    queried level.
    """

    def __init__(self) -> None:
        super().__init__()
        self.updates: list[tuple[str, int]] = []

    def get(self, key: str) -> Notification | None:
        row = super().get(key)
        return row.model_copy(deep=True) if row is not None else None

    def update(self, key: str, notification: Notification) -> Notification:
        self.updates.append((key, notification.escalation_level))
        return super().update(key, notification.model_copy(deep=True))

    def find_overdue_watering(self, overdue_since: datetime, escalation_level: int) -> list[Notification]:
        return [
            row.model_copy(deep=True)
            for row in self.all_rows()
            if row.notification_type.startswith("care.watering")
            and row.acted_at is None
            and row.created_at is not None
            and row.created_at < overdue_since
            and row.escalation_level == escalation_level
        ]

    def escalations(self) -> list[Notification]:
        return [row for row in self.all_rows() if row.notification_type == ESCALATION_TYPE]


def _seed_overdue_care_row(repo: _StoredNotificationRepo, *, tenant_key: str = TENANT, days_old: int = 3) -> str:
    """A care note the user has not acted on for *days_old* days (level-0 overdue only)."""
    row = repo.create(
        Notification(
            tenant_key=tenant_key,
            user_key=USER,
            notification_type="care.watering",
            title="Monstera",
            body="watering due: Monstera",
            group_key=CARE_GROUP,
            status=NotificationStatus.DELIVERED,
        )
    )
    row.created_at = datetime.now(UTC) - timedelta(days=days_old)
    return row.key or ""


def _engine(repo: _StoredNotificationRepo) -> NotificationEngine:
    preference_repo = MagicMock()
    preference_repo.get_by_user.return_value = NotificationPreferences(user_key=USER)
    redis = MagicMock()
    redis.get.return_value = None  # Redis dedup never answers: only the stamp may keep a rerun quiet
    engine = NotificationEngine(
        notification_repo=repo,
        preference_repo=preference_repo,
        channel_registry=MagicMock(),
        redis_client=redis,
        user_repo=MagicMock(),
        propagation=NotificationPropagationService(repo),
    )
    engine._is_quiet_hours = MagicMock(return_value=False)  # type: ignore[method-assign]
    engine._resolve_channels = MagicMock(return_value=[])  # type: ignore[method-assign]
    return engine


# ── the engine edge ──────────────────────────────────────────────────────────


class TestEscalationRunIsIdempotent:
    """F-8 acceptance-2 on the escalation edge: a double run → one escalation."""

    def test_a_second_run_sends_no_second_escalation(self) -> None:
        repo = _StoredNotificationRepo()
        original_key = _seed_overdue_care_row(repo)
        engine = _engine(repo)

        first = asyncio.run(engine.escalate_overdue(TENANT))
        second = asyncio.run(engine.escalate_overdue(TENANT))

        assert first == {"escalated": 1}
        assert second == {"escalated": 0}
        assert len(repo.escalations()) == 1
        assert repo.get(original_key).escalation_level == 1
        # One stamp, on the original row — not one per run.
        assert repo.updates == [(original_key, 1)]

    def test_a_concurrent_run_on_a_stale_read_sends_no_second_escalation(self) -> None:
        """Two overlapping runs (the noon beat plus a retry) both read the row at level 0.

        Sequentially the old stamp-after-send order was idempotent as well; it was
        the overlap that sent twice. The second run here is handed the snapshot
        taken before the first run's stamp landed — exactly what an overlapping
        run reads — and must still send nothing.
        """
        repo = _StoredNotificationRepo()
        original_key = _seed_overdue_care_row(repo)
        snapshot = {level: repo.find_overdue_watering(datetime.now(UTC), level) for level in range(3)}
        engine = _engine(repo)
        asyncio.run(engine.escalate_overdue(TENANT))

        repo.find_overdue_watering = lambda overdue_since, escalation_level: [  # type: ignore[method-assign]
            row.model_copy(deep=True) for row in snapshot.get(escalation_level, [])
        ]
        second = asyncio.run(engine.escalate_overdue(TENANT))

        assert second == {"escalated": 0}
        assert len(repo.escalations()) == 1
        assert repo.updates == [(original_key, 1)]

    def test_the_hook_refuses_a_stale_row_that_is_already_claimed(self) -> None:
        repo = _StoredNotificationRepo()
        original_key = _seed_overdue_care_row(repo)
        stale = repo.find_overdue_watering(datetime.now(UTC) - timedelta(days=2), 0)
        engine = _engine(repo)
        asyncio.run(engine.escalate_overdue(TENANT))

        claimed = engine._propagation.on_notification_escalated(stale[0], tenant_key=TENANT, escalation_level=1)

        assert claimed is False
        assert len(repo.escalations()) == 1
        assert repo.updates == [(original_key, 1)]


class TestEscalationRunFailsClosedPerTenant:
    """F-8 acceptance-3 on the escalation edge: no resolvable tenant → nothing written."""

    def test_a_run_without_a_tenant_writes_nothing(self) -> None:
        repo = _StoredNotificationRepo()
        _seed_overdue_care_row(repo)
        rows_before = len(repo.all_rows())

        result = asyncio.run(_engine(repo).escalate_overdue(""))

        assert result == {"escalated": 0}
        assert repo.updates == []
        assert len(repo.all_rows()) == rows_before

    def test_a_row_without_a_tenant_is_never_escalated(self) -> None:
        repo = _StoredNotificationRepo()
        _seed_overdue_care_row(repo, tenant_key="")

        result = asyncio.run(_engine(repo).escalate_overdue(TENANT))

        assert result == {"escalated": 0}
        assert repo.updates == []
        assert repo.escalations() == []

    def test_another_tenants_row_is_left_to_its_own_run(self) -> None:
        """The overdue query is cross-tenant; the stamp is not."""
        repo = _StoredNotificationRepo()
        foreign_key = _seed_overdue_care_row(repo, tenant_key=OTHER_TENANT)
        engine = _engine(repo)

        assert asyncio.run(engine.escalate_overdue(TENANT)) == {"escalated": 0}
        assert repo.updates == []
        assert repo.escalations() == []

        # …and its own tenant's run escalates it exactly once, under its own tenant.
        assert asyncio.run(engine.escalate_overdue(OTHER_TENANT)) == {"escalated": 1}
        assert repo.updates == [(foreign_key, 1)]
        assert [row.tenant_key for row in repo.escalations()] == [OTHER_TENANT]


# ── the owner's hook in isolation ────────────────────────────────────────────


class TestOnNotificationEscalated:
    def _row(self, repo: _StoredNotificationRepo, *, tenant_key: str = TENANT, level: int = 0) -> Notification:
        key = _seed_overdue_care_row(repo, tenant_key=tenant_key)
        if level:
            next(row for row in repo.all_rows() if row.key == key).escalation_level = level
        stored = repo.get(key)
        assert stored is not None
        return stored

    def test_stamps_the_stored_row_once(self) -> None:
        repo = _StoredNotificationRepo()
        row = self._row(repo)
        service = NotificationPropagationService(repo)

        assert service.on_notification_escalated(row, tenant_key=TENANT, escalation_level=1) is True
        assert service.on_notification_escalated(row, tenant_key=TENANT, escalation_level=1) is False
        assert repo.updates == [(row.key, 1)]

    def test_never_lowers_a_level(self) -> None:
        repo = _StoredNotificationRepo()
        row = self._row(repo, level=2)

        claimed = NotificationPropagationService(repo).on_notification_escalated(
            row, tenant_key=TENANT, escalation_level=1
        )

        assert claimed is False
        assert repo.updates == []
        assert repo.get(row.key or "").escalation_level == 2

    def test_an_empty_tenant_writes_nothing(self) -> None:
        repo = _StoredNotificationRepo()
        row = self._row(repo)

        assert (
            NotificationPropagationService(repo).on_notification_escalated(row, tenant_key="", escalation_level=1)
            is False
        )
        assert repo.updates == []

    def test_a_row_whose_stored_tenant_differs_writes_nothing(self) -> None:
        """The row as passed in is not trusted: the stored row's tenant decides."""
        repo = _StoredNotificationRepo()
        row = self._row(repo, tenant_key=OTHER_TENANT)
        forged = row.model_copy(update={"tenant_key": TENANT})

        claimed = NotificationPropagationService(repo).on_notification_escalated(
            forged, tenant_key=TENANT, escalation_level=1
        )

        assert claimed is False
        assert repo.updates == []

    def test_a_vanished_row_writes_nothing(self) -> None:
        repo = _StoredNotificationRepo()
        row = self._row(repo)
        repo.delete(row.key or "")

        assert (
            NotificationPropagationService(repo).on_notification_escalated(row, tenant_key=TENANT, escalation_level=1)
            is False
        )
        assert repo.updates == []

    def test_a_write_conflict_is_retried_once(self) -> None:
        repo = _StoredNotificationRepo()
        row = self._row(repo)
        real_update = repo.update
        calls = {"n": 0}

        def flaky(key: str, notification: Notification) -> Notification:
            calls["n"] += 1
            if calls["n"] == 1:
                raise WriteConflictError("notification", key)
            return real_update(key, notification)

        repo.update = flaky  # type: ignore[method-assign]

        assert (
            NotificationPropagationService(repo).on_notification_escalated(row, tenant_key=TENANT, escalation_level=1)
            is True
        )
        assert calls["n"] == 2
