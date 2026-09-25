"""#1772 — erasure records are hard-deleted once NFR-011 R-06 has run out.

NFR-011 R-06 keeps an ``erasure_requests`` record (pseudonymised at erasure)
as Art. 5(2) proof for **one year after completion**, then hard-deletes it
(AK-13). Nothing deleted one: every record lived forever. The daily beat task
``retention.purge_expired_erasure_records`` now runs
:meth:`PrivacyService.purge_expired_erasure_records`, which removes completed
records older than ``settings.retention_erasure_audit_retention_years``.

The task runs end-to-end here — Celery bridge, real ``PrivacyService``, and
:class:`FakeErasureRepo`, whose ``delete_completed_before`` mirrors the AQL
filter (``status == 'completed'`` and ``completed_at < cutoff``). What the AQL
itself does on a server is measured in
``tests/integration/test_erasure_record_purge.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.config.settings import Settings
from app.domain.models.privacy import ErasureRequest
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.retention_service import RetentionService
from tests.support.privacy_doubles import FakeErasureRepo

NOW = datetime(2026, 9, 25, 4, 30, tzinfo=UTC)


def _service(erasure_repo: object, *, years: int = 1) -> PrivacyService:
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=erasure_repo,  # type: ignore[arg-type]
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=MagicMock(),
        consent_engine=MagicMock(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="http://frontend.invalid",
        retention=RetentionService(erasure_record_retention_years=years),
    )


def _record(key: str, status: str, completed_days_ago: int | None) -> ErasureRequest:
    completed_at = None if completed_days_ago is None else NOW - timedelta(days=completed_days_ago)
    return ErasureRequest(_key=key, user_key=f"tomb-{key}", status=status, completed_at=completed_at)


class TestThePurgeTaskRunsThroughTheService:
    def test_only_completed_records_past_the_period_are_purged(self):
        repo = FakeErasureRepo(
            _record("completed-old", "completed", 400),
            _record("completed-young", "completed", 100),
            _record("partial-old", "partially_completed", 400),
            _record("scheduled-old", "scheduled", None),
            _record("in-progress-old", "in_progress", None),
        )
        service = _service(repo)

        from app.tasks.retention_tasks import purge_expired_erasure_records

        with patch("app.common.dependencies.get_privacy_service", return_value=service):
            result = purge_expired_erasure_records()

        assert result == {"purged": 1}
        assert set(repo.stored) == {"completed-young", "partial-old", "scheduled-old", "in-progress-old"}

    def test_the_task_is_registered_on_the_daily_beat(self):
        from app.tasks import celery_app

        entries = [
            e for e in celery_app.conf.beat_schedule.values() if e["task"] == "retention.purge_expired_erasure_records"
        ]
        assert len(entries) == 1

    def test_the_task_retries_on_transient_transport_errors(self):
        from app.tasks.retention_tasks import purge_expired_erasure_records

        assert ConnectionError in purge_expired_erasure_records.autoretry_for
        assert TimeoutError in purge_expired_erasure_records.autoretry_for


class TestTheServicePassesTheR06Cutoff:
    @pytest.mark.parametrize(
        ("years", "expected"),
        [(1, datetime(2025, 9, 25, 4, 30, tzinfo=UTC)), (3, datetime(2023, 9, 25, 4, 30, tzinfo=UTC))],
    )
    async def test_the_cutoff_is_now_minus_the_configured_calendar_years(self, years, expected):
        repo = MagicMock()
        repo.delete_completed_before.return_value = 0
        service = _service(repo, years=years)

        await service.purge_expired_erasure_records(now=NOW)

        cutoff = datetime.fromisoformat(repo.delete_completed_before.call_args.args[0])
        assert cutoff == expected

    async def test_a_leap_day_counts_back_to_the_28th(self):
        repo = MagicMock()
        repo.delete_completed_before.return_value = 0
        service = _service(repo)

        await service.purge_expired_erasure_records(now=datetime(2028, 2, 29, 4, 30, tzinfo=UTC))

        cutoff = datetime.fromisoformat(repo.delete_completed_before.call_args.args[0])
        assert cutoff == datetime(2027, 2, 28, 4, 30, tzinfo=UTC)

    async def test_the_default_period_is_the_setting(self, monkeypatch):
        from app.config.settings import settings

        monkeypatch.setattr(settings, "retention_erasure_audit_retention_years", 2)
        repo = MagicMock()
        repo.delete_completed_before.return_value = 0
        service = _service(repo, years=RetentionService().erasure_record_retention_years)

        await service.purge_expired_erasure_records(now=NOW)

        cutoff = datetime.fromisoformat(repo.delete_completed_before.call_args.args[0])
        assert cutoff == datetime(2024, 9, 25, 4, 30, tzinfo=UTC)


class TestTheR06Setting:
    def test_the_default_is_the_spec_period(self):
        """NFR-011 R-06 / §4 ``ERASURE_AUDIT_RETENTION_YEARS = 1``."""
        assert Settings.model_fields["retention_erasure_audit_retention_years"].default == 1

    def test_zero_years_is_refused(self):
        # ``0`` would drop the Art. 5(2) proof the moment the erasure completed.
        # The positive case first, or an unknown field would pass this test too.
        assert Settings(retention_erasure_audit_retention_years=1).retention_erasure_audit_retention_years == 1
        with pytest.raises(ValidationError):
            Settings(retention_erasure_audit_retention_years=0)

    def test_the_service_refuses_a_period_under_one_year(self):
        with pytest.raises(ValueError, match="R-06"):
            RetentionService(erasure_record_retention_years=0)
