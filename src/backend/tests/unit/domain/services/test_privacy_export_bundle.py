"""#1645 Art. 15 — the acceptance is content reaching the user, not a status.

Every assertion below reads the bytes a data subject would receive. A test that
checked ``status == "completed"`` while the bundle was empty is precisely the
defect this repairs, so the status is only ever asserted *next to* the payload.
"""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.personal_data_repository import IPersonalDataRepository
from app.domain.models.privacy import DataExportRequest, DataSourceDefinition
from app.domain.services.privacy_service import PrivacyService
from tests.support.privacy_doubles import FakeDataExportRepo

USER = "u-42"

#: Synthetic throughout — no real personal data in a fixture. The values are
#: chosen to be recognisable in a haystack of JSON.
FIXTURE_ROWS: dict[str, list[dict[str, Any]]] = {
    "users": [{"email": "subject@example.invalid", "display_name": "Test Subject", "locale": "de"}],
    "auth_providers": [{"provider": "github", "provider_email": "subject@example.invalid"}],
    # Distinctive values on purpose: this row must be asserted *absent*, and a
    # one-letter grade like "A" is a substring of any JSON document.
    "harvest_batches": [
        {"batch_id": "HB-fixture-0001", "quality_grade": "grade-fixture", "notes": "fixture harvest note"}
    ],
    "plant_diary_entries": [{"title": "fixture diary", "text": "the plant looked fine"}],
}


class _FakePersonalDataRepo(IPersonalDataRepository):
    """Answers from :data:`FIXTURE_ROWS`; every other declared source is empty.

    It resolves by the *source the caller passes in*, so a run that stopped
    reading the manifest would ask for nothing and the assertions below would
    find no records.
    """

    def __init__(self) -> None:
        self.asked_for: list[str] = []

    def collect_for_user(self, source: DataSourceDefinition, user_key: str, tenant_keys) -> list[dict[str, Any]]:
        assert user_key == USER
        self.asked_for.append(source.collection)
        return [dict(row) for row in FIXTURE_ROWS.get(source.collection, [])]


class _InMemoryStorage:
    """The narrow slice of ``IObjectStorageAdapter`` an export bundle uses."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def put_object(self, key, stream, mime_type, metadata=None):
        chunks = [chunk async for chunk in stream]
        self.objects[key] = b"".join(chunks)
        return MagicMock(key=key)

    async def get_object(self, key: str) -> AsyncIterator[bytes]:
        payload = self.objects[key]

        async def _iter() -> AsyncIterator[bytes]:
            yield payload

        return _iter()

    async def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)


def _make_service(export: DataExportRequest, storage, personal_data_repo, **overrides) -> PrivacyService:
    # A faithful double, not a MagicMock: this repository *merges*, so `update`
    # drops a `None` and `update_fields` keeps it. A MagicMock has neither
    # behaviour and would green-light a write that cannot land (#1506).
    export_repo = FakeDataExportRepo(export)
    deps = {
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
        "storage_adapter": storage,
        "personal_data_repo": personal_data_repo,
    }
    deps.update(overrides)
    return PrivacyService(**deps)


def _pending(key: str = "exp-1") -> DataExportRequest:
    return DataExportRequest(key=key, user_key=USER, status="pending", requested_at=datetime.now(UTC))


async def _download_text(svc: PrivacyService) -> str:
    _export, stream = await svc.open_export_bundle(USER, "exp-1")
    return b"".join([chunk async for chunk in stream]).decode("utf-8")


@pytest.mark.asyncio
class TestTheBundleReachesTheUser:
    async def test_the_downloaded_bytes_carry_the_users_records(self):
        storage = _InMemoryStorage()
        svc = _make_service(_pending(), storage, _FakePersonalDataRepo())

        await svc.process_data_export("exp-1")
        text = await _download_text(svc)

        # The subject's own values, read back out of the delivered file — for
        # every source that *can* be disclosed. ``harvest_batches`` is in the
        # fixture on purpose: its rows must NOT appear, because the walk never
        # asks for a source with a declared gap (#1662 SCR-001).
        gaps = {s.collection for s in DataExportEngine.USER_DATA_MANIFEST if s.disclosure_gap}
        assert "harvest_batches" in gaps, "the fixture's negative case must be a real gap"
        for collection, rows in FIXTURE_ROWS.items():
            for value in rows[0].values():
                if collection in gaps:
                    assert value not in text, f"{collection} was disclosed although it cannot be attributed"
                else:
                    assert value in text

    async def test_every_declared_manifest_source_is_a_section_of_the_bundle(self):
        """Art. 15(1) is a right to know which categories are processed.

        Compared against the engine rather than a written-down list, so a
        manifest entry added later is covered without editing this test — and a
        run that stopped walking the manifest goes red.
        """
        storage = _InMemoryStorage()
        svc = _make_service(_pending(), storage, _FakePersonalDataRepo())

        await svc.process_data_export("exp-1")
        bundle = json.loads(await _download_text(svc))

        declared = [source.collection for source in DataExportEngine.USER_DATA_MANIFEST]
        assert declared, "guard against a vacuous comparison if the manifest ever empties"
        assert [section["collection"] for section in bundle["sections"]] == declared

    async def test_the_record_matches_the_file_that_was_stored(self):
        storage = _InMemoryStorage()
        export = _pending()
        svc = _make_service(export, storage, _FakePersonalDataRepo())

        result = await svc.process_data_export("exp-1")

        assert result.status == "completed"
        assert result.file_path in storage.objects
        assert result.file_size_bytes == len(storage.objects[result.file_path])
        assert result.expires_at is not None

    async def test_a_walk_that_reaches_nothing_fails_instead_of_delivering_an_empty_bundle(self):
        """The anti-vacuity guard lives in production, not only in this file."""

        class _EmptyRepo(IPersonalDataRepository):
            def collect_for_user(self, source, user_key, tenant_keys):
                return []

        storage = _InMemoryStorage()
        svc = _make_service(_pending(), storage, _EmptyRepo())

        result = await svc.process_data_export("exp-1")

        assert result.status == "failed"
        assert not storage.objects
        assert "no profile record" in (result.error_message or "")

    async def test_an_expired_export_no_longer_has_a_file_in_storage(self):
        """NFR-011 R-05 is 'delete the file' *and* 'set the status'."""
        storage = _InMemoryStorage()
        export = _pending()
        svc = _make_service(export, storage, _FakePersonalDataRepo())
        await svc.process_data_export("exp-1")
        assert storage.objects

        export.status = "expired"
        svc._export_repo.expire_old_result = [export]
        await svc.expire_data_exports(datetime.now(UTC) + timedelta(hours=73))

        assert storage.objects == {}
        assert export.file_path is None

    async def test_an_expired_export_cannot_be_downloaded(self):
        storage = _InMemoryStorage()
        export = _pending()
        svc = _make_service(export, storage, _FakePersonalDataRepo())
        await svc.process_data_export("exp-1")
        export.expires_at = datetime.now(UTC) - timedelta(seconds=1)

        with pytest.raises(ValidationError):
            await svc.open_export_bundle(USER, "exp-1")

    async def test_another_user_cannot_download_the_bundle(self):
        storage = _InMemoryStorage()
        svc = _make_service(_pending(), storage, _FakePersonalDataRepo())
        await svc.process_data_export("exp-1")

        from app.common.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await svc.open_export_bundle("someone-else", "exp-1")
