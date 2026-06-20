"""REQ-034 §2.1 — unit tests for :class:`PlantPhotoService`.

Covers the gallery link/cover/list/delete logic and the consistency guards
(category + tenant) against in-memory fakes — no I/O, no storage backend.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.common.enums import AttachmentCategory
from app.common.exceptions import (
    NotFoundError,
    PhotoQuotaExceededError,
    ValidationError,
)
from app.config.settings import Settings
from app.domain.interfaces.attachment_repository import UNSET, _Unset
from app.domain.models.attachment import CAPTION_MAX_LENGTH, Attachment
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_photo_service import PlantPhotoService

TENANT = "tenant_anna"
OTHER_TENANT = "tenant_bob"


class _FakePlantRepo:
    def __init__(self, plant: PlantInstance) -> None:
        self._plant = plant

    def get_by_key(self, key):
        return self._plant if self._plant.key == key else None

    def update(self, key, plant):
        self._plant = plant
        return plant


class _FakeAttachmentRepo:
    def __init__(self) -> None:
        self._store: dict[str, Attachment] = {}

    def add(self, attachment: Attachment) -> Attachment:
        self._store[attachment.key or ""] = attachment
        return attachment

    def get(self, key, tenant_key):
        att = self._store.get(key)
        return att if att and att.tenant_key == tenant_key else None

    def update_metadata(self, key, tenant_key, *, caption=UNSET, taken_on=UNSET):
        att = self.get(key, tenant_key)
        if att is None:
            return None
        update: dict = {}
        if not isinstance(caption, _Unset):
            update["caption"] = caption
        if not isinstance(taken_on, _Unset):
            update["taken_on"] = taken_on
        updated = att.model_copy(update=update)
        self._store[key] = updated
        return updated


class _FakeAttachmentService:
    def __init__(self, repo: _FakeAttachmentRepo) -> None:
        self._repo = repo
        self.deleted: list[str] = []

    async def delete(self, attachment_id, tenant_key):
        existing = self._repo.get(attachment_id, tenant_key)
        if existing is None:
            return False
        del self._repo._store[attachment_id]
        self.deleted.append(attachment_id)
        return True


def _attachment(
    key: str,
    *,
    tenant_key: str = TENANT,
    category=AttachmentCategory.PLANT,
    seconds: int = 0,
) -> Attachment:
    return Attachment(
        _key=key,
        tenant_key=tenant_key,
        mime_type="image/jpeg",
        byte_size=100,
        sha256=f"sha-{key}",
        original_filename=f"{key}.jpg",
        created_by="user_anna",
        category=category,
        storage_key=f"t/{tenant_key}/plant/2026/06/{key}.jpg",
        created_at=datetime(2026, 6, 19, 12, 0, seconds, tzinfo=UTC),
    )


def _build(plant: PlantInstance | None = None, *, max_photos: int = 50):
    plant = plant or PlantInstance(
        _key="plant1",
        tenant_key=TENANT,
        instance_id="P-1",
        species_key="species1",
        planted_on=datetime(2026, 6, 1).date(),
    )
    plant_repo = _FakePlantRepo(plant)
    att_repo = _FakeAttachmentRepo()
    att_service = _FakeAttachmentService(att_repo)
    settings = Settings(storage_max_photos_per_instance=max_photos)
    service = PlantPhotoService(plant_repo, att_repo, att_service, settings)
    return service, plant_repo, att_repo, att_service


class TestLink:
    def test_link_appends_and_sets_first_cover(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("att1"))
        updated = service.link_photo("plant1", "att1", TENANT)
        assert updated.photo_refs == ["att1"]
        assert updated.cover_photo_ref == "att1"

    def test_link_prepends_newest_first(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("att1"))
        att_repo.add(_attachment("att2"))
        service.link_photo("plant1", "att1", TENANT)
        updated = service.link_photo("plant1", "att2", TENANT)
        assert updated.photo_refs == ["att2", "att1"]
        # Cover stays the first one set.
        assert updated.cover_photo_ref == "att1"

    def test_link_is_idempotent(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("att1"))
        service.link_photo("plant1", "att1", TENANT)
        updated = service.link_photo("plant1", "att1", TENANT)
        assert updated.photo_refs == ["att1"]

    def test_link_rejects_cross_category(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("att1", category=AttachmentCategory.DIARY))
        with pytest.raises(ValidationError):
            service.link_photo("plant1", "att1", TENANT)

    def test_link_rejects_cross_tenant(self):
        service, _pr, att_repo, _as = _build()
        # Attachment belongs to a different tenant — repo.get returns None for ours.
        att_repo.add(_attachment("att1", tenant_key=OTHER_TENANT))
        with pytest.raises(NotFoundError):
            service.link_photo("plant1", "att1", TENANT)

    def test_link_rejects_unknown_attachment(self):
        service, _pr, _ar, _as = _build()
        with pytest.raises(NotFoundError):
            service.link_photo("plant1", "ghost", TENANT)

    def test_link_enforces_quota(self):
        plant = PlantInstance(
            _key="plant1",
            tenant_key=TENANT,
            instance_id="P-1",
            species_key="species1",
            planted_on=datetime(2026, 6, 1).date(),
            photo_refs=["existing"],
        )
        service, _pr, att_repo, _as = _build(plant, max_photos=1)
        att_repo.add(_attachment("att1"))
        with pytest.raises(PhotoQuotaExceededError):
            service.link_photo("plant1", "att1", TENANT)

    def test_assert_can_add_photo_raises_at_quota(self):
        plant = PlantInstance(
            _key="plant1",
            tenant_key=TENANT,
            instance_id="P-1",
            species_key="species1",
            planted_on=datetime(2026, 6, 1).date(),
            photo_refs=["a", "b"],
        )
        service, *_ = _build(plant, max_photos=2)
        with pytest.raises(PhotoQuotaExceededError):
            service.assert_can_add_photo("plant1", TENANT)


class TestCover:
    def test_set_cover_requires_membership(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("att1"))
        service.link_photo("plant1", "att1", TENANT)
        with pytest.raises(ValidationError):
            service.set_cover("plant1", "not-linked", TENANT)

    def test_set_cover_updates_ref(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("att1"))
        att_repo.add(_attachment("att2"))
        service.link_photo("plant1", "att1", TENANT)
        service.link_photo("plant1", "att2", TENANT)
        updated = service.set_cover("plant1", "att2", TENANT)
        assert updated.cover_photo_ref == "att2"


class TestMetadata:
    def _linked(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("att1"))
        service.link_photo("plant1", "att1", TENANT)
        return service, att_repo

    def test_set_caption_and_taken_on(self):
        service, att_repo = self._linked()
        updated = service.update_photo_metadata("plant1", "att1", TENANT, caption="My basil", taken_on=date(2026, 6, 1))
        assert updated.caption == "My basil"
        assert updated.taken_on == date(2026, 6, 1)
        # Persisted on the attachment record.
        assert att_repo.get("att1", TENANT).caption == "My basil"

    def test_patch_only_touches_provided_fields(self):
        service, _ar = self._linked()
        service.update_photo_metadata("plant1", "att1", TENANT, caption="first", taken_on=date(2026, 6, 1))
        # Patch only the caption — taken_on must survive untouched (UNSET).
        updated = service.update_photo_metadata("plant1", "att1", TENANT, caption="second")
        assert updated.caption == "second"
        assert updated.taken_on == date(2026, 6, 1)

    def test_explicit_null_clears_caption(self):
        service, _ar = self._linked()
        service.update_photo_metadata("plant1", "att1", TENANT, caption="to be cleared")
        updated = service.update_photo_metadata("plant1", "att1", TENANT, caption=None)
        assert updated.caption is None

    def test_taken_on_none_keeps_created_at_for_fe_fallback(self):
        # The service never substitutes created_at for taken_on — the FE owns the
        # `taken_on ?? created_at` display fallback. A null taken_on stays null.
        service, _ar = self._linked()
        updated = service.update_photo_metadata("plant1", "att1", TENANT, taken_on=None)
        assert updated.taken_on is None
        assert updated.created_at is not None

    def test_caption_too_long_422(self):
        service, _ar = self._linked()
        with pytest.raises(ValidationError):
            service.update_photo_metadata("plant1", "att1", TENANT, caption="x" * (CAPTION_MAX_LENGTH + 1))

    def test_caption_at_limit_ok(self):
        service, _ar = self._linked()
        updated = service.update_photo_metadata("plant1", "att1", TENANT, caption="x" * CAPTION_MAX_LENGTH)
        assert updated.caption == "x" * CAPTION_MAX_LENGTH

    def test_taken_on_future_422(self):
        service, _ar = self._linked()
        future = datetime.now(UTC).date() + timedelta(days=1)
        with pytest.raises(ValidationError):
            service.update_photo_metadata("plant1", "att1", TENANT, taken_on=future)

    def test_taken_on_today_ok(self):
        service, _ar = self._linked()
        today = datetime.now(UTC).date()
        updated = service.update_photo_metadata("plant1", "att1", TENANT, taken_on=today)
        assert updated.taken_on == today

    def test_unknown_photo_404(self):
        service, _ar = self._linked()
        with pytest.raises(NotFoundError):
            service.update_photo_metadata("plant1", "ghost", TENANT, caption="x")

    def test_cross_tenant_instance_404(self):
        service, _ar = self._linked()
        with pytest.raises(NotFoundError):
            service.update_photo_metadata("plant1", "att1", OTHER_TENANT, caption="x")


class TestList:
    def test_list_orders_newest_first(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("old", seconds=1))
        att_repo.add(_attachment("new", seconds=5))
        service.link_photo("plant1", "old", TENANT)
        service.link_photo("plant1", "new", TENANT)
        _plant, photos = service.list_photos("plant1", TENANT)
        assert [p.key for p in photos] == ["new", "old"]

    def test_list_skips_stale_refs(self):
        plant = PlantInstance(
            _key="plant1",
            tenant_key=TENANT,
            instance_id="P-1",
            species_key="species1",
            planted_on=datetime(2026, 6, 1).date(),
            photo_refs=["ghost"],
        )
        service, _pr, _ar, _as = _build(plant)
        _plant, photos = service.list_photos("plant1", TENANT)
        assert photos == []


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_removes_and_unlinks(self):
        service, plant_repo, att_repo, att_service = _build()
        att_repo.add(_attachment("att1"))
        service.link_photo("plant1", "att1", TENANT)
        updated = await service.delete_photo("plant1", "att1", TENANT)
        assert updated.photo_refs == []
        assert updated.cover_photo_ref is None
        assert "att1" in att_service.deleted

    @pytest.mark.asyncio
    async def test_delete_reassigns_cover(self):
        service, _pr, att_repo, _as = _build()
        att_repo.add(_attachment("att1"))
        att_repo.add(_attachment("att2"))
        service.link_photo("plant1", "att1", TENANT)
        service.link_photo("plant1", "att2", TENANT)
        # att1 is cover (first linked); delete it → cover falls back to remaining.
        updated = await service.delete_photo("plant1", "att1", TENANT)
        assert updated.cover_photo_ref == "att2"
        assert updated.photo_refs == ["att2"]

    @pytest.mark.asyncio
    async def test_delete_unknown_photo_404(self):
        service, *_ = _build()
        with pytest.raises(NotFoundError):
            await service.delete_photo("plant1", "ghost", TENANT)

    @pytest.mark.asyncio
    async def test_delete_all_photos_cascade(self):
        plant = PlantInstance(
            _key="plant1",
            tenant_key=TENANT,
            instance_id="P-1",
            species_key="species1",
            planted_on=datetime(2026, 6, 1).date(),
            photo_refs=["att1", "att2"],
        )
        service, _pr, att_repo, att_service = _build(plant)
        att_repo.add(_attachment("att1"))
        att_repo.add(_attachment("att2"))
        removed = await service.delete_all_photos(plant, TENANT)
        assert removed == 2
        assert set(att_service.deleted) == {"att1", "att2"}
