"""#1782 — the privacy flows apply the NFR-011 periods their settings name.

``PrivacyService`` carried three class literals — ``HARD_DELETE_DAYS = 90``
(R-01), ``EXPORT_TTL_HOURS = 72`` (R-05), ``EMAIL_CHANGE_TTL_HOURS = 24``
(R-07) — while the documented settings were read only by a
:class:`RetentionService` nothing consulted for those three. Setting the env
var changed nothing. Each period is now computed once, in the retention
service, from its setting.

Every test drives the production entry point and reads the deadline off the
record it persists; the configured value is deliberately not the default, so a
literal cannot pass.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.config.settings import settings
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.personal_data_repository import IPersonalDataRepository
from app.domain.models.privacy import DataExportRequest, DataSourceDefinition
from app.domain.models.user import User
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.retention_service import RetentionService
from tests.support.privacy_doubles import FakeDataExportRepo, step_up

USER_KEY = "u-1782"
PASSWORD = "correct-horse-battery-staple"

#: Slack for the wall clock between the service's ``now`` and the test's.
_CLOCK_SLACK = timedelta(seconds=30)


class _OneRowRepo(IPersonalDataRepository):
    """Answers one synthetic row for ``users`` so the export walk is not empty."""

    def collect_for_user(self, source: DataSourceDefinition, user_key: str, tenant_keys) -> list[dict[str, Any]]:
        if source.collection == "users":
            return [{"display_name": "Synthetic Subject"}]
        return []


class _InMemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def put_object(self, key, stream: AsyncIterator[bytes], mime_type, metadata=None):
        self.objects[key] = b"".join([chunk async for chunk in stream])
        return MagicMock(key=key)


def _user() -> User:
    return User(
        _key=USER_KEY,
        email="subject@example.com",
        display_name="Synthetic Subject",
        password_hash=PasswordEngine().hash_password(PASSWORD),
        email_verified=True,
        is_active=True,
    )


def _service(retention: RetentionService | None, **overrides: Any) -> PrivacyService:
    user = _user()
    user_repo = MagicMock()
    user_repo.get_or_raise.return_value = user
    user_repo.get_by_key.return_value = user
    user_repo.get_by_email.return_value = None
    user_repo.update_fields.side_effect = lambda _key, _fields: user

    erasure_repo = MagicMock()
    erasure_repo.find_active_for_user.return_value = None
    erasure_repo.create.side_effect = lambda erasure: erasure

    email_change_repo = MagicMock()
    email_change_repo.create.side_effect = lambda change: change

    deps: dict[str, Any] = {
        "export_repo": MagicMock(),
        "consent_repo": MagicMock(),
        "restriction_repo": MagicMock(),
        "erasure_repo": erasure_repo,
        "email_change_repo": email_change_repo,
        "user_repo": user_repo,
        "refresh_token_repo": MagicMock(),
        "data_export_engine": DataExportEngine(),
        "erasure_engine": ErasureEngine(),
        "consent_engine": ConsentEngine(),
        "password_engine": PasswordEngine(),
        "token_engine": TokenEngine("test-secret-key-32-chars-min!!!", "HS256"),
        "email_service": MagicMock(),
        "frontend_url": "https://app.test",
        "retention": retention,
    }
    deps.update(overrides)
    return PrivacyService(**deps)


class TestR01TheHardDeleteIsScheduledAfterTheConfiguredPeriod:
    def test_the_injected_period_schedules_the_hard_delete(self):
        before = datetime.now(UTC)
        erasure = _service(RetentionService(hard_delete_after_days=45)).request_erasure(
            USER_KEY, **step_up("subject@example.com", PASSWORD)
        )

        assert erasure.hard_delete_scheduled_at is not None
        assert abs(erasure.hard_delete_scheduled_at - (before + timedelta(days=45))) < _CLOCK_SLACK
        assert erasure.hard_delete_scheduled_at - erasure.soft_deleted_at == timedelta(days=45)

    def test_the_setting_schedules_the_hard_delete(self, monkeypatch):
        monkeypatch.setattr(settings, "retention_soft_delete_retention_days", 30)

        erasure = _service(None).request_erasure(USER_KEY, **step_up("subject@example.com", PASSWORD))

        assert erasure.hard_delete_scheduled_at - erasure.soft_deleted_at == timedelta(days=30)


class TestR05TheExportExpiresAfterTheConfiguredPeriod:
    @staticmethod
    async def _completed(retention: RetentionService | None) -> DataExportRequest:
        export = DataExportRequest(key="exp-1", user_key=USER_KEY, status="pending", requested_at=datetime.now(UTC))
        svc = _service(
            retention,
            export_repo=FakeDataExportRepo(export),
            storage_adapter=_InMemoryStorage(),
            personal_data_repo=_OneRowRepo(),
        )
        result = await svc.process_data_export("exp-1")
        assert result is not None
        assert result.status == "completed"
        return result

    @pytest.mark.asyncio
    async def test_the_injected_period_sets_expires_at(self):
        result = await self._completed(RetentionService(export_retention_hours=12))

        assert result.expires_at - result.completed_at == timedelta(hours=12)

    @pytest.mark.asyncio
    async def test_the_setting_sets_expires_at(self, monkeypatch):
        monkeypatch.setattr(settings, "retention_export_file_retention_hours", 6)

        result = await self._completed(None)

        assert result.expires_at - result.completed_at == timedelta(hours=6)


class TestR07TheEmailChangeLinkExpiresAfterTheConfiguredPeriod:
    def test_the_injected_period_sets_expires_at(self):
        change = _service(RetentionService(email_change_ttl_hours=2)).request_email_change(USER_KEY, "new@example.com")

        assert change.expires_at - change.requested_at == timedelta(hours=2)

    def test_the_setting_sets_expires_at(self, monkeypatch):
        monkeypatch.setattr(settings, "retention_email_change_retention_hours", 3)

        change = _service(None).request_email_change(USER_KEY, "new@example.com")

        assert change.expires_at - change.requested_at == timedelta(hours=3)

    def test_the_suppressed_branch_answers_with_the_same_period(self):
        """An address that is taken must not be told apart by a different ``expires_at``."""
        user_repo = MagicMock()
        user_repo.get_or_raise.return_value = _user()
        user_repo.get_by_email.return_value = MagicMock()  # the new address is taken

        change = _service(RetentionService(email_change_ttl_hours=2), user_repo=user_repo).request_email_change(
            USER_KEY, "taken@example.com"
        )

        assert change.expires_at - change.requested_at == timedelta(hours=2)


class TestNoLiteralSurvives:
    @pytest.mark.parametrize("literal", ["HARD_DELETE_DAYS", "EXPORT_TTL_HOURS", "EMAIL_CHANGE_TTL_HOURS"])
    def test_the_class_carries_no_second_copy_of_a_period(self, literal):
        assert not hasattr(PrivacyService, literal)


class TestTheServiceHoldsTheSettingFloors:
    """A caller constructing the service directly is held to the settings' ``ge=1``."""

    @pytest.mark.parametrize(
        "argument",
        [
            "hard_delete_after_days",
            "ip_anonymisation_after_days",
            "export_retention_hours",
            "email_change_ttl_hours",
        ],
    )
    def test_zero_is_refused(self, argument):
        assert getattr(RetentionService(**{argument: 1}), argument) == 1
        with pytest.raises(ValueError, match="NFR-011"):
            RetentionService(**{argument: 0})
