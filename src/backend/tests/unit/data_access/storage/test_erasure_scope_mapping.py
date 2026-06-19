"""REQ-025 §3.1 — erasure-scope → attachment-category mapping (Phase 0).

Guards the security-critical contract: ``user_personal`` MUST NOT resolve to
"every category" (which would hard-delete the user's documentation photos), and
``user_diary_attachments`` must cover exactly the tenant-record documentation
categories (incl. the REQ-034 ``plant`` gallery).
"""

import pytest

from app.common.enums import AttachmentCategory
from app.data_access.storage.local_fs_adapter import (
    LocalFsStorageAdapter,
    _scope_to_categories,
)

SECRET = "x" * 40
MAX_SIZE = 25 * 1024 * 1024


async def _stream(data: bytes):
    yield data


class TestScopeToCategories:
    def test_all_means_every_category(self):
        assert _scope_to_categories("all") is None
        assert _scope_to_categories("") is None

    def test_user_personal_matches_no_existing_category(self):
        # Hard-delete scope: no personal categories exist yet → empty list,
        # which the adapters treat as "touch nothing" (never "touch everything").
        result = _scope_to_categories("user_personal")
        assert result == []

    def test_user_diary_attachments_covers_documentation_categories(self):
        result = _scope_to_categories("user_diary_attachments")
        assert set(result) == {
            AttachmentCategory.DIARY,
            AttachmentCategory.IPM,
            AttachmentCategory.HARVEST,
            AttachmentCategory.POST_HARVEST,
            AttachmentCategory.TASK,
            AttachmentCategory.PLANT,
        }

    def test_plant_gallery_is_anonymise_scope_not_hard_delete(self):
        # REQ-034 §5: gallery photos belong to the plant record → anonymise.
        assert AttachmentCategory.PLANT in _scope_to_categories("user_diary_attachments")
        assert AttachmentCategory.PLANT not in (_scope_to_categories("user_personal") or [])

    def test_legacy_csv_category_list_still_supported(self):
        result = _scope_to_categories("diary,harvest")
        assert set(result) == {AttachmentCategory.DIARY, AttachmentCategory.HARVEST}


class _FakeAttachment:
    def __init__(self, storage_key: str, mime_type: str) -> None:
        self.storage_key = storage_key
        self.mime_type = mime_type


class _RecordingRepo:
    def __init__(self, attachments) -> None:
        self._attachments = attachments
        self.calls: list = []

    def find_by_user(self, tenant_key, user_key, categories=None):
        self.calls.append(categories)
        return self._attachments


@pytest.mark.asyncio
class TestUserPersonalIsSafe:
    async def test_user_personal_hard_delete_touches_nothing(self, tmp_path):
        # An empty category set must short-circuit BEFORE the repo lookup so a
        # mapping regression can never hard-delete every object.
        attachments = [_FakeAttachment("t-1/diary/u1.jpg", "image/jpeg")]
        repo = _RecordingRepo(attachments)
        adapter = LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://x",
            signing_secret=SECRET,
            max_object_size_bytes=MAX_SIZE,
            attachment_repo=repo,
        )
        await adapter.put_object("t-1/diary/u1.jpg", _stream(b"img"), "image/jpeg")

        deleted = await adapter.delete_for_user("t-1", "u-1", "user_personal")

        assert deleted == 0
        assert repo.calls == []  # repo never queried for an empty scope
        # The documentation photo is untouched.
        result = await adapter.list_objects("t-1")
        assert result["keys"] == ["t-1/diary/u1.jpg"]
