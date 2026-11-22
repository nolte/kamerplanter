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
            # REQ-053 GP-FR-033: the plan underlay is a tenant-record photo (an aerial view can reveal a home).
            AttachmentCategory.GARDEN_PLAN_UNDERLAY,
            # REQ-053 GP-FR-051: the photos of a bed are tenant-record photos (a garden photo can show a home).
            AttachmentCategory.LOCATION,
        }

    def test_bed_photos_are_anonymised_not_hard_deleted(self):
        # WP 8.18: an erased member's bed photo stays with the garden for the other members, uploader replaced.
        assert AttachmentCategory.LOCATION in _scope_to_categories("user_diary_attachments")
        assert AttachmentCategory.LOCATION not in (_scope_to_categories("user_personal") or [])
        assert AttachmentCategory.LOCATION not in _scope_to_categories("user_pest_reference_images")

    def test_plant_gallery_is_anonymise_scope_not_hard_delete(self):
        # REQ-034 §5: gallery photos belong to the plant record → anonymise.
        assert AttachmentCategory.PLANT in _scope_to_categories("user_diary_attachments")
        assert AttachmentCategory.PLANT not in (_scope_to_categories("user_personal") or [])

    def test_every_category_has_an_erasure_rule_or_a_named_reason(self):
        """The class, not the instance: a new category is decided here before an erasure can skip it.

        ``location`` (WP 8.18) and ``garden_plan_underlay`` (WP 7.14) were each added by hand to the mapping;
        this makes the next one fail until it is mapped or named with the reason it needs no storage scope.
        """
        mapped = {
            category
            for scope in ("user_personal", "user_diary_attachments", "user_pest_reference_images")
            for category in (_scope_to_categories(scope) or [])
        }
        no_storage_scope = {
            # files the system writes for the tenant, not documentation of a person (NFR-013 §6.2); their record's
            # uploader is anonymised by the ``attachments`` rule of the ArangoDB pass like every other attachment
            AttachmentCategory.IMPORT,
            AttachmentCategory.EXPORT,
            AttachmentCategory.TENANT_EXPORT,
            # a transient recognition input (REQ-034 §4), anonymised by the same ArangoDB rule
            AttachmentCategory.ID_RECOGNITION,
        }

        assert set(AttachmentCategory) - mapped - no_storage_scope == set()
        assert mapped & no_storage_scope == set()

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

        assert deleted.removed == 0 and deleted.retained_shared == 0
        assert repo.calls == []  # repo never queried for an empty scope
        # The documentation photo is untouched.
        result = await adapter.list_objects("t-1")
        assert result["keys"] == ["t-1/diary/u1.jpg"]
