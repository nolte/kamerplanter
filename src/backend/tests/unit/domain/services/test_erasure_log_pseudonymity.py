"""#1700 — the erasure logs no longer carry the erased user's plaintext key.

``erasure.account_erased``, ``retention.erasure.failed`` and the per-phase
storage / reference-index events logged ``user_key=<key>``. The account is gone
afterwards, but the log lines outlive it under no retention rule, and a key is
enough to re-link them to everything else a log shipper holds. The events now
carry ``subject`` — a salted reference (``ErasureEngine.log_subject``) — so the
lines of one erasure stay correlatable to each other and name nobody. Since the
#1773 review (GDPR-003) that reference is purpose-separated from the tombstone
the audit rows get (NFR-011 R-06): a log line cannot be joined to the
pseudonymised ``erasure_requests`` row without the salt.

What is asserted is the absence of the plaintext key in **every** captured event
value, not the presence of one field: a new log line that reintroduces the key
under any name fails here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import structlog.testing

from app.common.exceptions import NotFoundError
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.attachment import Attachment
from app.domain.models.membership import Membership
from app.domain.models.pest_image import PestImageContribution
from app.domain.models.privacy import ErasureExecutionReport, ErasureRequest, ErasureStepOutcome
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakePersonalTenants

#: Distinctive, so a substring hit cannot be a coincidence.
USER_KEY = "subject-7f3a91"
SALT = "log-test-salt-not-a-secret-0123456789"
LOG_SALT = "log-pseudonym-test-salt-not-a-secret-01234"


@pytest.fixture(autouse=True)
def _log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """#1812: log pseudonyms are keyed with LOG_PSEUDONYM_SALT, not with the tombstone salt the services get."""
    from app.config.settings import settings

    monkeypatch.setattr(settings, "log_pseudonym_salt", LOG_SALT)


TENANT = "t-1"


def _values(value: Any) -> list[str]:
    """Every string reachable inside one event value (dicts, lists, nested)."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _values(v)] + [s for k in value for s in _values(k)]
    if isinstance(value, list | tuple | set):
        return [s for v in value for s in _values(v)]
    return []


def _leaks(logs: list[dict[str, Any]]) -> list[str]:
    return [
        f"{event.get('event')}.{field}"
        for event in logs
        for field, value in event.items()
        if any(USER_KEY in text for text in _values(value))
    ]


def _attachment(category: str, mime_type: str = "image/heic") -> Attachment:
    return Attachment(
        _key=f"att-{category}",
        tenant_key=TENANT,
        mime_type=mime_type,
        byte_size=1,
        sha256="0" * 64,
        original_filename="x.heic",
        created_by=USER_KEY,
        category=category,
        storage_key=f"t/{TENANT}/{category}/x",
    )


def _service(tmp_path: Path, **overrides: Any) -> PrivacyService:
    attachment_repo = MagicMock()
    attachment_repo.find_by_user.side_effect = lambda _tenant, _user, categories: [
        _attachment(category) for category in (categories or [])
    ]
    attachment_repo.anonymize_user_metadata.return_value = 1
    storage = LocalFsStorageAdapter(
        str(tmp_path),
        "http://localhost",
        "signing-secret",
        max_object_size_bytes=1024,
        attachment_repo=attachment_repo,
    )
    membership_repo = MagicMock()
    membership_repo.get_by_user.return_value = [Membership(user_key=USER_KEY, tenant_key=TENANT)]
    membership_repo.list_by_user.return_value = [Membership(user_key=USER_KEY, tenant_key=TENANT)]
    pest_image_repo = MagicMock()
    pest_image_repo.list_for_user.return_value = [
        PestImageContribution(
            _key="c-1", tenant_key=TENANT, pest_key="p-1", attachment_id="att-1", contributed_by=USER_KEY
        )
    ]
    pest_image_repo.delete.return_value = True
    executor = MagicMock()
    executor.run_erasure_plan.return_value = ErasureExecutionReport(
        steps=[ErasureStepOutcome(collection="users", kind="user", executor="account_cascade", affected=1)]
    )
    export_repo = MagicMock()
    export_repo.list_by_user.return_value = []
    deps: dict[str, Any] = {
        "export_repo": export_repo,
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
        "tenant_service": FakePersonalTenants(),
        "storage_adapter": storage,
        "attachment_repo": attachment_repo,
        "membership_repo": membership_repo,
        "pest_image_repo": pest_image_repo,
        "pest_prototype_store": NoopPestPrototypeStore(),
        "reference_index_store": NoopReferenceIndexStore(),
        "erasure_executor": executor,
        "tombstone_salt": SALT,
    }
    deps.update(overrides)
    return PrivacyService(**deps)


@pytest.mark.asyncio
class TestErasureLogsNameNobody:
    async def test_a_full_erasure_logs_no_plaintext_key(self, tmp_path: Path) -> None:
        service = _service(tmp_path)

        with structlog.testing.capture_logs() as logs:
            await service.erase_account(USER_KEY)

        events = {event.get("event") for event in logs}
        # The phases this test means to cover actually logged — otherwise an
        # empty capture would pass the absence check below.
        assert {
            "erasure.account_erased",
            "retention.erasure.storage_hard_delete",
            "retention.erasure.storage_anonymize",
            "storage_delete_for_user",
            "storage_strip_exif_for_user",
            "exif_strip_unsupported_format",
            "retention.erasure.pest_image_documents_cleanup",
            "reference_index_cleanup_noop",
            "retention.erasure.reference_index_cleanup",
        } <= events
        assert _leaks(logs) == []

    async def test_the_erasure_events_carry_the_log_subject_not_the_tombstone(self, tmp_path: Path) -> None:
        """The reference is purpose-separated from the tombstone (#1773 review GDPR-003).

        A log line equal to the tombstone could be joined to the pseudonymised
        audit rows by anyone holding the log stream — no salt needed.
        """
        service = _service(tmp_path)
        tombstone = ErasureEngine.compute_tombstone_hash(USER_KEY, SALT)

        with structlog.testing.capture_logs() as logs:
            await service.erase_account(USER_KEY)

        erased = next(event for event in logs if event.get("event") == "erasure.account_erased")
        assert erased["subject"] == ErasureEngine.log_subject(USER_KEY, LOG_SALT)
        assert tombstone not in repr(logs)

    async def test_a_failed_erasure_logs_no_plaintext_key(self, tmp_path: Path) -> None:
        executor = MagicMock()
        executor.run_erasure_plan.side_effect = RuntimeError("store unavailable")
        service = _service(tmp_path, erasure_executor=executor)
        request = ErasureRequest(_key="e-1", user_key=USER_KEY, status="scheduled")

        with structlog.testing.capture_logs() as logs:
            assert await service._finalize_erasure(request, datetime(2026, 9, 24, tzinfo=UTC)) is False

        assert "retention.erasure.failed" in {event.get("event") for event in logs}
        assert _leaks(logs) == []

    @pytest.mark.parametrize(
        "failure",
        [
            NotFoundError("User", USER_KEY),
            FileNotFoundError(f"[Errno 2] No such file or directory: '/data/privacy/exports/{USER_KEY}/exp-1.json'"),
            OSError(f"cannot remove privacy/exports/{USER_KEY}/"),
        ],
        ids=["not-found-names-the-key", "storage-error-names-the-bundle", "storage-error-names-the-prefix"],
    )
    async def test_a_failure_whose_text_names_the_subject_logs_no_plaintext_key(
        self, tmp_path: Path, failure: Exception
    ) -> None:
        """GDPR-001 (#1773 review): ``error=`` carried the exception text unredacted.

        Only ``reason`` (the record's ``error_message``) was redacted; the log
        line beside it kept ``str(exc)``, and a storage error names the export
        bundle ``privacy/exports/<user_key>/…``.
        """
        executor = MagicMock()
        executor.run_erasure_plan.side_effect = failure
        erasure_repo = MagicMock()
        service = _service(tmp_path, erasure_executor=executor, erasure_repo=erasure_repo)
        request = ErasureRequest(_key="e-1", user_key=USER_KEY, status="scheduled")

        with structlog.testing.capture_logs() as logs:
            assert await service._finalize_erasure(request, datetime(2026, 9, 24, tzinfo=UTC)) is False

        failed = next(event for event in logs if event.get("event") == "retention.erasure.failed")
        assert _leaks(logs) == []
        assert failed["error"], "the line keeps the (redacted) text for the operator"
        assert failed["error_type"] == type(failure).__name__
        # The record outlives the account as well (R-06).
        assert USER_KEY not in str(erasure_repo.update_fields.call_args_list)

    async def test_skipped_phases_log_no_plaintext_key(self, tmp_path: Path) -> None:
        service = _service(tmp_path, storage_adapter=None)

        with structlog.testing.capture_logs() as logs:
            await service.erase_account(USER_KEY)

        # An unwired reference-index store is refused, not skipped (#1753
        # SEC-002); the no-op binding logs its own line instead.
        assert {
            "retention.erasure.export_file_cleanup_skipped",
            "retention.erasure.storage_cleanup_skipped",
            "reference_index_cleanup_noop",
        } <= {event.get("event") for event in logs}
        assert _leaks(logs) == []
