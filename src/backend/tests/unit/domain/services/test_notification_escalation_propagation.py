"""ADR-008 F-8 — the overdue escalation's stamp goes through the propagation owner.

Phase 0 of ADR-008 measured exactly one notification write outside
:class:`NotificationPropagationService` that was neither an event nor a user
action: :meth:`NotificationEngine.escalate_overdue` stamping ``escalation_level``
back onto the *existing* care row (site b1 of
``.audits/adr-008-phase-0-inventory/2026-09-01-inventory.md``). F-8 routes that
stamp through :meth:`NotificationPropagationService.on_notification_escalated`,
which makes it ONE conditional repository write
(:meth:`INotificationRepository.claim_escalation_level`) and the **claim** of the
escalation: the engine sends the escalation notification only when the claim
returned a row.

The two invariants of the owner are pinned on this edge (F-8 acceptance-2/-3):

* **Idempotent** — a second escalation run produces no second escalation
  notification and no second stamp. Redis dedup is switched off in these tests
  (``redis.get`` → ``None``), so the only thing that can keep the second run quiet
  is the claim itself.
* **Fail-closed per tenant** — no resolvable tenant writes nothing; a row of
  another tenant is neither stamped nor escalated in this tenant's run.

The repository is the stateful
:class:`~tests.unit.domain.services.notification_fakes.EscalationNotificationRepo`
(the #769 lesson: a stateless mock lets every hook look right while the stored row
ends up wrong). That the real conditional statement lets exactly one of two
*concurrent* claimers win is measured against ArangoDB in
``tests/integration/test_notification_escalation_claim.py`` — a sequential fake
cannot show it and does not pretend to.

Traces to issue #1061, feature F-8 (no TC-ID: unit tests of a service edge).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.notification import Notification, NotificationPreferences
from app.domain.services.notification_propagation_service import NotificationPropagationService
from tests.unit.domain.services.notification_fakes import EscalationNotificationRepo

TENANT = "tenant-A"
OTHER_TENANT = "tenant-B"
USER = "user-a"


def _member(user_key: str, tenant_key: str) -> bool:
    """Every recipient is an active member here; the membership rule has its own tests."""
    return bool(user_key and tenant_key)


def _seed(repo: EscalationNotificationRepo, *, tenant_key: str = TENANT, days_old: int = 3) -> str:
    return repo.seed_overdue_care_row(tenant_key=tenant_key, user_key=USER, days_old=days_old)


def _engine(repo: EscalationNotificationRepo) -> NotificationEngine:
    preference_repo = MagicMock()
    preference_repo.get_by_user.return_value = NotificationPreferences(user_key=USER)
    redis = MagicMock()
    redis.get.return_value = None  # Redis dedup never answers: only the claim may keep a rerun quiet
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
        repo = EscalationNotificationRepo()
        original_key = _seed(repo)
        engine = _engine(repo)

        first = asyncio.run(engine.escalate_overdue(TENANT, is_active_member=_member))
        second = asyncio.run(engine.escalate_overdue(TENANT, is_active_member=_member))

        assert first == {"escalated": 1}
        assert second == {"escalated": 0}
        assert len(repo.escalations()) == 1
        assert repo.get(original_key).escalation_level == 1
        # One claim, on the original row — and no full-model write at all.
        assert repo.claims == [(original_key, 1)]
        assert repo.updates == []

    def test_a_run_handed_a_stale_read_sends_no_second_escalation(self) -> None:
        """An overlapping run read the row at level 0 before the first claim landed."""
        repo = EscalationNotificationRepo()
        original_key = _seed(repo)
        snapshot = {
            level: repo.find_overdue_watering(datetime.now(UTC), level, tenant_key=TENANT) for level in range(3)
        }
        engine = _engine(repo)
        asyncio.run(engine.escalate_overdue(TENANT, is_active_member=_member))

        repo.find_overdue_watering = lambda overdue_since, escalation_level, *, tenant_key: [  # type: ignore[method-assign]
            row.model_copy(deep=True) for row in snapshot.get(escalation_level, [])
        ]
        second = asyncio.run(engine.escalate_overdue(TENANT, is_active_member=_member))

        assert second == {"escalated": 0}
        assert len(repo.escalations()) == 1
        assert repo.claims == [(original_key, 1)]

    def test_the_claim_keeps_the_rows_read_state(self) -> None:
        """A partial write: the stamp never resets what the user did to the row."""
        repo = EscalationNotificationRepo()
        original_key = _seed(repo)
        read_at = datetime.now(UTC) - timedelta(hours=1)
        repo.mark_read(original_key, read_at)

        asyncio.run(_engine(repo).escalate_overdue(TENANT, is_active_member=_member))

        stored = repo.get(original_key)
        assert stored.escalation_level == 1
        assert stored.read_at == read_at


class TestEscalationRunFailsClosedPerTenant:
    """F-8 acceptance-3 on the escalation edge: no resolvable tenant → nothing written."""

    def test_a_run_without_a_tenant_writes_nothing(self) -> None:
        repo = EscalationNotificationRepo()
        _seed(repo)
        rows_before = len(repo.all_rows())

        result = asyncio.run(_engine(repo).escalate_overdue("", is_active_member=_member))

        assert result == {"escalated": 0}
        assert repo.claims == []
        assert len(repo.all_rows()) == rows_before

    def test_a_row_without_a_tenant_is_never_escalated(self) -> None:
        repo = EscalationNotificationRepo()
        _seed(repo, tenant_key="")

        result = asyncio.run(_engine(repo).escalate_overdue(TENANT, is_active_member=_member))

        assert result == {"escalated": 0}
        assert repo.claims == []
        assert repo.escalations() == []

    def test_another_tenants_row_is_left_to_its_own_run(self) -> None:
        repo = EscalationNotificationRepo()
        foreign_key = _seed(repo, tenant_key=OTHER_TENANT)
        engine = _engine(repo)

        assert asyncio.run(engine.escalate_overdue(TENANT, is_active_member=_member)) == {"escalated": 0}
        assert repo.claims == []
        assert repo.escalations() == []
        # Never read either: the preferences of the foreign row's user are not loaded.
        engine._preference_repo.get_by_user.assert_not_called()

        assert asyncio.run(engine.escalate_overdue(OTHER_TENANT, is_active_member=_member)) == {"escalated": 1}
        assert repo.claims == [(foreign_key, 1)]
        assert [row.tenant_key for row in repo.escalations()] == [OTHER_TENANT]


class TestOneFailingRowDoesNotAbortTheRun:
    """S4: a throwing ``notify`` for one row is logged; the tenant's other rows still escalate."""

    def test_the_next_row_is_still_escalated(self) -> None:
        repo = EscalationNotificationRepo()
        first_key = _seed(repo)
        second_key = repo.seed_overdue_care_row(tenant_key=TENANT, user_key=USER, group_key="care.watering:plant-2")
        engine = _engine(repo)
        real_notify = engine.notify
        calls: list[str] = []

        async def notify(*, user_key: str, tenant_key: str, notification: Notification) -> dict:
            calls.append(notification.parent_notification_key or "")
            if len(calls) == 1:
                raise RuntimeError("channel exploded")
            return await real_notify(user_key=user_key, tenant_key=tenant_key, notification=notification)

        engine.notify = AsyncMock(side_effect=notify)  # type: ignore[method-assign]

        result = asyncio.run(engine.escalate_overdue(TENANT, is_active_member=_member))

        assert sorted(calls) == sorted([first_key, second_key])
        assert result == {"escalated": 1}
        assert len(repo.escalations()) == 1


# ── the owner's hook in isolation ────────────────────────────────────────────


class TestOnNotificationEscalated:
    def _row(self, repo: EscalationNotificationRepo, *, tenant_key: str = TENANT, level: int = 0) -> Notification:
        key = _seed(repo, tenant_key=tenant_key)
        if level:
            next(row for row in repo.all_rows() if row.key == key).escalation_level = level
        stored = repo.get(key)
        assert stored is not None
        return stored

    def test_claims_the_row_once(self) -> None:
        repo = EscalationNotificationRepo()
        row = self._row(repo)
        service = NotificationPropagationService(repo)

        assert service.on_notification_escalated(row, tenant_key=TENANT, escalation_level=1) is True
        assert service.on_notification_escalated(row, tenant_key=TENANT, escalation_level=1) is False
        assert repo.claims == [(row.key, 1)]
        assert repo.updates == []

    def test_never_lowers_a_level(self) -> None:
        repo = EscalationNotificationRepo()
        row = self._row(repo, level=2)

        claimed = NotificationPropagationService(repo).on_notification_escalated(
            row, tenant_key=TENANT, escalation_level=1
        )

        assert claimed is False
        assert repo.claims == []
        assert repo.get(row.key or "").escalation_level == 2

    def test_an_empty_tenant_writes_nothing(self) -> None:
        repo = EscalationNotificationRepo()
        row = self._row(repo)

        claimed = NotificationPropagationService(repo).on_notification_escalated(row, tenant_key="", escalation_level=1)

        assert claimed is False
        assert repo.claims == []

    def test_a_row_whose_stored_tenant_differs_writes_nothing(self) -> None:
        """The row as passed in is not trusted: the stored row's tenant decides (in the write's filter)."""
        repo = EscalationNotificationRepo()
        row = self._row(repo, tenant_key=OTHER_TENANT)
        forged = row.model_copy(update={"tenant_key": TENANT})

        claimed = NotificationPropagationService(repo).on_notification_escalated(
            forged, tenant_key=TENANT, escalation_level=1
        )

        assert claimed is False
        assert repo.claims == []

    def test_a_vanished_row_writes_nothing(self) -> None:
        repo = EscalationNotificationRepo()
        row = self._row(repo)
        repo.delete(row.key or "")

        claimed = NotificationPropagationService(repo).on_notification_escalated(
            row, tenant_key=TENANT, escalation_level=1
        )

        assert claimed is False
        assert repo.claims == []

    def test_a_failing_claim_is_no_claim(self) -> None:
        """No retry: an unclaimed level is retried by the next run, never sent unrecorded."""
        repo = EscalationNotificationRepo()
        row = self._row(repo)
        repo.claim_escalation_level = MagicMock(side_effect=RuntimeError("conflict"))  # type: ignore[method-assign]

        claimed = NotificationPropagationService(repo).on_notification_escalated(
            row, tenant_key=TENANT, escalation_level=1
        )

        assert claimed is False
        assert repo.claim_escalation_level.call_count == 1
