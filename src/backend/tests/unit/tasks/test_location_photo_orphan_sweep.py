"""REQ-053 GP-FR-051 (#2661 SEC-001 / GDPR-001) — never-linked bed photos are collected, on by default.

A bed photo is uploaded (``POST /attachments``, category ``location``) and linked in a second request
(``POST /locations/{key}/photos``). A link that never happens, or a discard that fails after a bed write
committed, leaves the upload unreferenced. ``cleanup_orphaned_location_photos`` is what collects it.

Pinned here: the default is ON (48 h) and 0 disables without a query; the task is on the beat and routed; the
body selects ``location`` (never ``task``) and deletes through the tenant-scoped ``AttachmentService`` with the
row's own tenant; the audit dict keeps the task sweep's shape including ``held_undated``. The query itself runs
against ArangoDB in ``tests/integration/test_orphaned_location_photo_query.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from celery.schedules import crontab

from app.common.enums import AttachmentCategory
from app.config.settings import Settings
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.domain.models.attachment import Attachment
from app.tasks import celery_app, storage_tasks
from app.tasks.routing import DEFAULT_TASKS, task_routes

TASK = "app.tasks.storage_tasks.cleanup_orphaned_location_photos"


def _photo(key: str, tenant: str, size: int = 100) -> Attachment:
    return Attachment(
        _key=key,
        tenant_key=tenant,
        mime_type="image/jpeg",
        byte_size=size,
        sha256="0" * 64,
        original_filename="beet.jpg",
        created_by="u_sabine",
        category=AttachmentCategory.LOCATION,
        storage_key=f"t/{tenant}/location/2026/11/{key}.jpg",
    )


class TestTheDefault:
    def test_the_sweep_ships_on_with_a_48_hour_floor(self) -> None:
        assert Settings().storage_location_photo_orphan_hours == 48

    def test_zero_disables_and_a_negative_value_is_refused(self) -> None:
        assert Settings(storage_location_photo_orphan_hours=0).storage_location_photo_orphan_hours == 0
        try:
            Settings(storage_location_photo_orphan_hours=-1)
        except Exception as exc:  # noqa: BLE001 — pydantic's ValidationError, named by field
            assert "storage_location_photo_orphan_hours" in str(exc)
        else:
            raise AssertionError("a negative floor was accepted")

    def test_the_task_photo_sweep_default_is_untouched(self) -> None:
        assert Settings().storage_task_photo_orphan_hours == 0


class TestTheWiring:
    def test_the_task_is_registered_on_the_beat_nightly(self) -> None:
        entries = [entry for entry in celery_app.conf.beat_schedule.values() if entry["task"] == TASK]
        assert len(entries) == 1
        assert entries[0]["schedule"] == crontab(hour=3, minute=50)
        assert TASK in celery_app.tasks

    def test_the_task_is_routed_to_the_default_queue(self) -> None:
        assert TASK in DEFAULT_TASKS and TASK in task_routes()


class TestTheTask:
    def test_a_disabled_sweep_returns_without_querying(self) -> None:
        with (
            patch.object(storage_tasks.settings, "storage_location_photo_orphan_hours", 0),
            patch("app.common.dependencies.get_attachment_repo") as repo,
        ):
            result = storage_tasks.cleanup_orphaned_location_photos.run()

        assert result["disabled"] is True and result["deleted"] == 0
        repo.assert_not_called()

    def test_an_enabled_sweep_runs_with_the_configured_floor_and_logs_the_audit(self) -> None:
        body = AsyncMock(return_value={"found": 0, "deleted": 0})
        with (
            patch.object(storage_tasks.settings, "storage_location_photo_orphan_hours", 48),
            patch.object(storage_tasks, "_cleanup_orphaned_location_photos", body),
            patch.object(storage_tasks, "logger") as logger,
        ):
            storage_tasks.cleanup_orphaned_location_photos.run(limit=7)

        body.assert_awaited_once_with(48, 7)
        assert logger.info.call_args.args[0] == "cleanup_orphaned_location_photos_audit"


class TestTheBody:
    async def test_it_selects_location_photos_and_deletes_each_under_its_own_tenant(self) -> None:
        repo = MagicMock(spec=ArangoAttachmentRepository)
        repo.find_orphaned_photos.return_value = [_photo("a1", "t_a", 100), _photo("b1", "t_b", 50)]
        repo.count_undated_orphaned_photos.return_value = 2
        service = MagicMock()
        service.delete_if_unreferenced = AsyncMock(side_effect=[True, RuntimeError("storage down")])
        before = datetime.now(UTC)

        with (
            patch("app.common.dependencies.get_attachment_repo", return_value=repo),
            patch("app.common.dependencies.get_attachment_service", return_value=service),
        ):
            result = await storage_tasks._cleanup_orphaned_location_photos(48, 500)

        args, kwargs = repo.find_orphaned_photos.call_args
        assert args == (AttachmentCategory.LOCATION,) and kwargs["limit"] == 500
        assert (before - kwargs["older_than"]).total_seconds() >= 48 * 3600 - 5
        repo.find_orphaned_task_photos.assert_not_called()
        repo.count_undated_orphaned_photos.assert_called_once_with(AttachmentCategory.LOCATION)
        assert [call.args for call in service.delete_if_unreferenced.await_args_list] == [("a1", "t_a"), ("b1", "t_b")]
        assert {key: result[key] for key in ("found", "deleted", "failed", "skipped", "freed_bytes")} == {
            "found": 2,
            "deleted": 1,
            "failed": 1,
            "skipped": 0,
            "freed_bytes": 100,
        }
        assert result["held_undated"] == 2 and "cutoff" in result
