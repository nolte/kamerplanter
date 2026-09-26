"""#1773 — privacy, auth and account log lines name no data subject.

#1700 moved the erasure log lines from ``user_key=<key>`` to ``subject=`` — the
salted subject reference (``ErasureEngine.log_subject``) — and stopped there.
The sibling lines kept the plaintext: the export pipeline's ``delivered`` /
``failed`` / ``internal_error`` lines logged ``user_key=export.user_key``, the
Art. 16 confirmation logged the old **and** the new address, registration
logged the address. A log stream has no retention rule of its own (NFR-011), so
those lines outlive the account, its erasure and the erasure record (R-06).

Every test drives the real service method and captures what structlog actually
receives. What is asserted is the absence of the plaintext key / address in
**every** captured event value — a new line reintroducing it under any name
fails here — plus the presence of the pseudonymised field, so an empty capture
cannot pass.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import structlog.testing

from app.common.decoys import email_digest
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.personal_data_repository import IPersonalDataRepository
from app.domain.models.privacy import DataExportRequest, EmailChangeRequest
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.data_subject_service import DataSubjectService
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakeDataExportRepo

#: Distinctive, so a substring hit cannot be a coincidence.
USER_KEY = "subject-5c81e2"
OLD_EMAIL = "old-address-5c81e2@example.com"
NEW_EMAIL = "new-address-5c81e2@example.com"
SALT = "log-test-salt-not-a-secret-0123456789"
LOG_SALT = "log-pseudonym-test-salt-not-a-secret-01234"


@pytest.fixture(autouse=True)
def _log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """#1812: log pseudonyms are keyed with LOG_PSEUDONYM_SALT, not with the tombstone salt the services get."""
    from app.config.settings import settings

    monkeypatch.setattr(settings, "log_pseudonym_salt", LOG_SALT)


EXPORT_KEY = "exp-1"
#: The salted, purpose-separated log reference — deliberately NOT the tombstone
#: the pseudonymised audit rows keep (#1773 review GDPR-003).
SUBJECT = ErasureEngine.log_subject(USER_KEY, LOG_SALT)


def _values(value: Any) -> list[str]:
    """Every string reachable inside one event value (dicts, lists, nested)."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _values(v)] + [s for k in value for s in _values(k)]
    if isinstance(value, list | tuple | set):
        return [s for v in value for s in _values(v)]
    return [str(value)]


def _leaks(logs: list[dict[str, Any]], *needles: str) -> list[str]:
    return [
        f"{event.get('event')}.{field}"
        for event in logs
        for field, value in event.items()
        if any(needle.lower() in text.lower() for text in _values(value) for needle in needles)
    ]


def _event(logs: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [event for event in logs if event.get("event") == name]
    assert matches, f"{name} was not logged; captured: {[event.get('event') for event in logs]}"
    return matches[0]


class _ProfileOnlyRepo(IPersonalDataRepository):
    def collect_for_user(self, source, user_key, tenant_keys) -> list[dict[str, Any]]:
        return [{"email": OLD_EMAIL}] if source.filter_field == "_key" else []


class _CompletionFailsRepo(FakeDataExportRepo):
    """The bundle is stored, then the completion write fails — the orphan-cleanup path."""

    def complete_if_processing(self, key: str, fields: dict[str, Any]) -> DataExportRequest | None:
        raise RuntimeError(f"write conflict on data_export_requests for {USER_KEY}")


class _UndeletableLocalFs(LocalFsStorageAdapter):
    """The real adapter whose delete fails with the key in the message, as a backend error would."""

    async def delete_object(self, key: str) -> None:
        raise ConnectionError(f"cannot delete {key}")


def _storage(tmp_path: Path, cls: type[LocalFsStorageAdapter] = LocalFsStorageAdapter) -> LocalFsStorageAdapter:
    return cls(
        root=str(tmp_path),
        public_base_url="http://localhost/api/v1/storage/token",
        signing_secret="test-secret-please-change",
        max_object_size_bytes=10 * 1024 * 1024,
    )


def _privacy(**overrides: Any) -> PrivacyService:
    membership_repo = MagicMock()
    membership_repo.list_by_user.return_value = []
    deps: dict[str, Any] = {
        "export_repo": FakeDataExportRepo(
            DataExportRequest(key=EXPORT_KEY, user_key=USER_KEY, status="pending", requested_at=datetime.now(UTC))
        ),
        "consent_repo": MagicMock(),
        "restriction_repo": MagicMock(),
        "erasure_repo": MagicMock(),
        "email_change_repo": MagicMock(),
        "user_repo": MagicMock(),
        "refresh_token_repo": MagicMock(),
        "data_export_engine": DataExportEngine(),
        "erasure_engine": ErasureEngine(),
        "consent_engine": ConsentEngine(),
        "password_engine": MagicMock(),
        "token_engine": MagicMock(),
        "email_service": MagicMock(),
        "frontend_url": "https://app.test",
        "personal_data_repo": _ProfileOnlyRepo(),
        "membership_repo": membership_repo,
        "tombstone_salt": SALT,
    }
    deps.update(overrides)
    return PrivacyService(**deps)


def _export_repo(cls: type[FakeDataExportRepo] = FakeDataExportRepo) -> FakeDataExportRepo:
    return cls(DataExportRequest(key=EXPORT_KEY, user_key=USER_KEY, status="pending", requested_at=datetime.now(UTC)))


@pytest.mark.asyncio
class TestExportPipelineLogsNameNobody:
    async def test_delivered_logs_the_subject_reference_not_the_key(self, tmp_path: Path) -> None:
        service = _privacy(storage_adapter=_storage(tmp_path), export_repo=_export_repo())

        with structlog.testing.capture_logs() as logs:
            result = await service.process_data_export(EXPORT_KEY)

        assert _leaks(logs, USER_KEY) == []

        assert result is not None and result.status == "completed"
        assert _event(logs, "retention.process_data_export.delivered")["subject"] == SUBJECT
        # The bundle upload goes through the adapter's own log line as well.
        _event(logs, "storage_put_object")

    async def test_failed_logs_the_subject_reference_not_the_key(self) -> None:
        # No storage adapter: ``ExportBundleUnavailableError`` → ``failed`` at once.
        service = _privacy(storage_adapter=None, export_repo=_export_repo())

        with structlog.testing.capture_logs() as logs:
            result = await service.process_data_export(EXPORT_KEY)

        assert _leaks(logs, USER_KEY) == []

        assert result is not None and result.status == "failed"
        assert _event(logs, "retention.process_data_export.failed")["subject"] == SUBJECT

    async def test_internal_error_and_the_orphan_cleanup_name_nobody(self, tmp_path: Path) -> None:
        """The stored bundle is removed again; the cleanup's own line logs the bundle key."""
        service = _privacy(storage_adapter=_storage(tmp_path), export_repo=_export_repo(_CompletionFailsRepo))

        with structlog.testing.capture_logs() as logs:
            result = await service.process_data_export(EXPORT_KEY, final_attempt=True)

        assert _leaks(logs, USER_KEY) == []

        assert result is not None and result.status == "failed"
        internal = _event(logs, "retention.process_data_export.internal_error")
        assert internal["subject"] == SUBJECT
        # The exception text named the subject; the line keeps the text, redacted.
        assert SUBJECT in internal["error"]
        _event(logs, "retention.process_data_export.failed")
        deleted = _event(logs, "storage_delete_object")
        assert deleted["key"].endswith(f"/{EXPORT_KEY}.json"), "the export key stays for correlation"

    async def test_a_failed_orphan_cleanup_names_nobody(self, tmp_path: Path) -> None:
        service = _privacy(
            storage_adapter=_storage(tmp_path, _UndeletableLocalFs),
            export_repo=_export_repo(_CompletionFailsRepo),
        )

        with structlog.testing.capture_logs() as logs:
            await service.process_data_export(EXPORT_KEY, final_attempt=True)

        assert _leaks(logs, USER_KEY) == []

        cleanup = _event(logs, "retention.process_data_export.orphan_cleanup_failed")
        assert cleanup["object_key"].endswith(f"/{EXPORT_KEY}.json")


class _PutFailsLocalFs(LocalFsStorageAdapter):
    """The real adapter whose upload fails naming the bundle key, as a backend error would."""

    async def put_object(self, key: str, stream: Any, mime_type: str, metadata: Any = None) -> Any:
        raise OSError(f"[Errno 28] No space left on device: '/data/{key}'")


BUNDLE = f"privacy/exports/{USER_KEY}/{EXPORT_KEY}.json"


@pytest.mark.asyncio
class TestExceptionTextsOnTheExportPathNameNobody:
    """GDPR-002 (#1773 review): the ``error=`` of three sinks was ``str(exc)``, unredacted.

    A storage error names the object it failed on, and the export bundle's key
    embeds the account key. Each test drives the real service method with such
    an error and asserts the key is absent from every captured value while the
    line still carries a text and the exception type for the operator.
    """

    async def test_a_retried_build_names_nobody(self, tmp_path: Path) -> None:
        service = _privacy(storage_adapter=_storage(tmp_path, _PutFailsLocalFs), export_repo=_export_repo())

        with structlog.testing.capture_logs() as logs, pytest.raises(OSError):
            await service.process_data_export(EXPORT_KEY, final_attempt=False)

        retrying = _event(logs, "retention.process_data_export.retrying")
        assert _leaks(logs, USER_KEY) == []
        assert retrying["error_type"] == "OSError"
        assert f"privacy/exports/<subject>/{EXPORT_KEY}.json" in retrying["error"]

    async def test_a_failed_bundle_delete_at_expiry_names_nobody(self, tmp_path: Path) -> None:
        now = datetime.now(UTC)
        expired = DataExportRequest(
            key=EXPORT_KEY,
            user_key=USER_KEY,
            status="completed",
            requested_at=now - timedelta(days=4),
            completed_at=now - timedelta(days=4),
            expires_at=now - timedelta(days=1),
            file_path=BUNDLE,
        )
        service = _privacy(
            storage_adapter=_storage(tmp_path, _UndeletableLocalFs), export_repo=FakeDataExportRepo(expired)
        )

        with structlog.testing.capture_logs() as logs:
            assert await service.expire_data_exports(now) == 0

        failed = _event(logs, "retention.expire_data_exports.object_delete_failed")
        assert _leaks(logs, USER_KEY) == []
        assert failed["error_type"] == "ConnectionError"
        assert f"privacy/exports/<subject>/{EXPORT_KEY}.json" in failed["error"]

    async def test_a_failed_dispatch_names_nobody(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.tasks import retention_tasks

        def _broker_down(export_key: str) -> None:
            raise ConnectionError(f"broker refused task for {BUNDLE}")

        monkeypatch.setattr(retention_tasks.process_data_export, "delay", _broker_down)
        service = _privacy(export_repo=FakeDataExportRepo())

        with structlog.testing.capture_logs() as logs:
            service.request_data_export(USER_KEY)

        failed = _event(logs, "privacy_export_dispatch_failed")
        assert _leaks(logs, USER_KEY) == []
        assert failed["error_type"] == "ConnectionError"


class TestEmailChangeConfirmationNamesNobody:
    def test_confirmed_logs_digests_not_the_addresses(self) -> None:
        user_repo = MagicMock()
        user_repo.get_or_raise.return_value = User(_key=USER_KEY, email=OLD_EMAIL, display_name="x")
        user_repo.update_fields.return_value = User(_key=USER_KEY, email=NEW_EMAIL, display_name="x")
        # The address moves by compare-and-set since #1848.
        user_repo.move_email.return_value = User(_key=USER_KEY, email=NEW_EMAIL, display_name="x")
        change_repo = MagicMock()
        change_repo.get_by_token_hash.return_value = EmailChangeRequest(
            _key="ecr-1",
            user_key=USER_KEY,
            new_email=NEW_EMAIL,
            verification_token_hash="h",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        token_engine = MagicMock()
        token_engine.hash_token.return_value = "h"
        service = _privacy(user_repo=user_repo, email_change_repo=change_repo, token_engine=token_engine)

        with structlog.testing.capture_logs() as logs:
            service.confirm_email_change("raw-token")

        assert _leaks(logs, USER_KEY, OLD_EMAIL, NEW_EMAIL) == []

        confirmed = _event(logs, "privacy_email_change_confirmed")
        assert confirmed["subject"] == SUBJECT
        assert confirmed["old_email_sha256"] == email_digest(OLD_EMAIL)
        assert confirmed["new_email_sha256"] == email_digest(NEW_EMAIL)


class TestFacadeAndAccountLinesNameNobody:
    def test_the_data_subject_facade_logs_the_privacy_services_reference(self) -> None:
        privacy = _privacy()
        privacy.request_data_export = MagicMock()  # type: ignore[method-assign]

        with structlog.testing.capture_logs() as logs:
            DataSubjectService(privacy).access(USER_KEY)

        assert _leaks(logs, USER_KEY) == []

        assert _event(logs, "data_subject_right_invoked")["subject"] == SUBJECT


def _auth_service(user_repo: MagicMock) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        tenant_service=MagicMock(),
        tombstone_salt=SALT,
    )


class TestAuthLinesNameNobody:
    def test_user_registered_logs_a_digest_not_the_address(self) -> None:
        user_repo = MagicMock()
        user_repo.get_by_email.return_value = None

        def _create(user: User) -> User:
            created = user.model_copy(deep=True)
            created.key = USER_KEY
            return created

        user_repo.create.side_effect = _create
        service = _auth_service(user_repo)

        with structlog.testing.capture_logs() as logs:
            service.register_local(NEW_EMAIL, "a-sufficiently-long-password-2024", "Someone")

        assert _leaks(logs, NEW_EMAIL, USER_KEY) == []

        assert _event(logs, "user_registered")["email_sha256"] == email_digest(NEW_EMAIL)

    def test_a_refused_service_account_credential_logs_the_subject_reference(self) -> None:
        from app.common.exceptions import ForbiddenError

        user_repo = MagicMock()
        user_repo.get_or_raise.return_value = User(
            _key=USER_KEY, email=OLD_EMAIL, display_name="svc", account_type="service"
        )
        service = _auth_service(user_repo)

        with structlog.testing.capture_logs() as logs, pytest.raises(ForbiddenError):
            service.change_password(
                USER_KEY,
                None,
                "a-sufficiently-long-password-2024",
                step_up_code=None,
                step_up_token=None,
                authenticated_with_api_key=False,
                client_ip=None,
            )

        assert _leaks(logs, USER_KEY, OLD_EMAIL) == []

        assert _event(logs, "service_account_interactive_credential_refused")["subject"] == SUBJECT
