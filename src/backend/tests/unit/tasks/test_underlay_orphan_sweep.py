"""#2715 item 1 — never-named garden-plan underlays are collected, on by default.

An underlay is uploaded (``POST /attachments``, category ``garden_plan_underlay``) and named by the site in a second
request (``PUT /sites/{key}/plan/underlay``). A PUT that never happens, or a discard that fails after a replaced or
removed underlay committed, leaves the upload unreferenced. ``cleanup_orphaned_underlays`` is what collects it.

Pinned here: the default is ON (48 h) and 0 disables without a query; the task is on the beat, routed and decided
by the tenant gate; the body selects ``garden_plan_underlay`` (never another category) and deletes through the
tenant-scoped ``AttachmentService`` with the row's own tenant. The query runs against ArangoDB in
``tests/integration/test_orphaned_underlay_query.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from celery.schedules import crontab
from pydantic import ValidationError

from app.common.enums import AttachmentCategory
from app.config.settings import Settings
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.domain.models.attachment import Attachment
from app.tasks import celery_app, storage_tasks
from app.tasks.routing import DEFAULT_TASKS, task_routes
from app.tasks.tenant_gate import TENANT_AGNOSTIC_BEATS

TASK = "app.tasks.storage_tasks.cleanup_orphaned_underlays"


def _underlay(key: str, tenant: str, size: int = 100) -> Attachment:
    return Attachment(
        _key=key,
        tenant_key=tenant,
        mime_type="image/jpeg",
        byte_size=size,
        sha256="0" * 64,
        original_filename="luftbild.jpg",
        created_by="u_sabine",
        category=AttachmentCategory.GARDEN_PLAN_UNDERLAY,
        storage_key=f"t/{tenant}/garden_plan_underlay/2026/11/{key}.jpg",
    )


class TestTheDefault:
    def test_the_sweep_ships_on_with_a_48_hour_floor(self) -> None:
        assert Settings().storage_garden_plan_underlay_orphan_hours == 48

    def test_zero_disables_and_a_negative_value_is_refused(self) -> None:
        assert Settings(storage_garden_plan_underlay_orphan_hours=0).storage_garden_plan_underlay_orphan_hours == 0
        with pytest.raises(ValidationError, match="storage_garden_plan_underlay_orphan_hours"):
            Settings(storage_garden_plan_underlay_orphan_hours=-1)


class TestTheWiring:
    def test_the_task_is_registered_on_the_beat_nightly_before_the_reconciliation(self) -> None:
        entries = [entry for entry in celery_app.conf.beat_schedule.values() if entry["task"] == TASK]
        assert len(entries) == 1
        assert entries[0]["schedule"] == crontab(hour=4, minute=0)
        assert TASK in celery_app.tasks

    def test_the_task_is_routed_to_the_default_queue(self) -> None:
        assert TASK in DEFAULT_TASKS and TASK in task_routes()

    def test_the_tenant_gate_decision_is_recorded(self) -> None:
        assert TASK in TENANT_AGNOSTIC_BEATS


class TestTheTask:
    def test_a_disabled_sweep_returns_without_querying(self) -> None:
        with (
            patch.object(storage_tasks.settings, "storage_garden_plan_underlay_orphan_hours", 0),
            patch("app.common.dependencies.get_attachment_repo") as repo,
        ):
            result = storage_tasks.cleanup_orphaned_underlays.run()

        assert result["disabled"] is True and result["deleted"] == 0
        repo.assert_not_called()

    def test_an_enabled_sweep_runs_with_the_configured_floor_and_logs_the_audit(self) -> None:
        body = AsyncMock(return_value={"found": 0, "deleted": 0})
        with (
            patch.object(storage_tasks.settings, "storage_garden_plan_underlay_orphan_hours", 48),
            patch.object(storage_tasks, "_cleanup_orphaned_underlays", body),
            patch.object(storage_tasks, "logger") as logger,
        ):
            storage_tasks.cleanup_orphaned_underlays.run(limit=7)

        body.assert_awaited_once_with(48, 7)
        assert logger.info.call_args.args[0] == "cleanup_orphaned_underlays_audit"


class TestTheBody:
    async def test_it_selects_underlays_and_deletes_each_under_its_own_tenant(self) -> None:
        repo = MagicMock(spec=ArangoAttachmentRepository)
        repo.find_orphaned_photos.return_value = [_underlay("a1", "t_a", 100), _underlay("b1", "t_b", 50)]
        repo.count_undated_orphaned_photos.return_value = 0
        service = MagicMock()
        service.delete = AsyncMock(side_effect=[True, True])
        before = datetime.now(UTC)

        with (
            patch("app.common.dependencies.get_attachment_repo", return_value=repo),
            patch("app.common.dependencies.get_attachment_service", return_value=service),
        ):
            result = await storage_tasks._cleanup_orphaned_underlays(48, 500)

        args, kwargs = repo.find_orphaned_photos.call_args
        assert args == (AttachmentCategory.GARDEN_PLAN_UNDERLAY,) and kwargs["limit"] == 500
        assert (before - kwargs["older_than"]).total_seconds() >= 48 * 3600 - 5
        repo.count_undated_orphaned_photos.assert_called_once_with(AttachmentCategory.GARDEN_PLAN_UNDERLAY)
        assert [call.args for call in service.delete.await_args_list] == [("a1", "t_a"), ("b1", "t_b")]
        assert result["found"] == 2 and result["deleted"] == 2 and result["freed_bytes"] == 150
