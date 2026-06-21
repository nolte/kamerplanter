"""REQ-010 — PestImageService unit tests.

The service composes the attachment pipeline with a thin link document. We
exercise it against in-memory doubles for the repository, the attachment
service, and the IPM service so the tests need neither object storage nor
ArangoDB. Coverage:

* ``contribute`` validates the pest first, uploads via the attachment service
  (category PEST_REFERENCE), and persists a contribution.
* ``contribute`` against an unknown pest raises ``NotFoundError`` and never
  uploads (no orphan).
* ``list_for_pest`` returns only the tenant's contributions, with thumbnail
  flags derived from the attachment MIME type.
* ``delete`` removes a tenant-owned contribution AND its attachment; a foreign
  contribution is invisible and yields ``False`` (and never deletes anything).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import AttachmentCategory, PestImageStatus
from app.common.exceptions import NotFoundError
from app.domain.models.attachment import Attachment
from app.domain.models.ipm import Pest
from app.domain.models.pest_image import PestImageContribution
from app.domain.services.pest_image_service import PestImageContent, PestImageService


class _FakePestImageRepo:
    def __init__(self) -> None:
        self.store: dict[str, PestImageContribution] = {}
        self._seq = 0

    def create(self, contribution: PestImageContribution) -> PestImageContribution:
        self._seq += 1
        key = f"pic{self._seq}"
        stored = contribution.model_copy(update={"key": key, "created_at": datetime.now(UTC)})
        self.store[key] = stored
        return stored

    def get(self, key: str, tenant_key: str) -> PestImageContribution | None:
        c = self.store.get(key)
        if c is None or c.tenant_key != tenant_key:
            return None
        return c

    def list_for_pest(self, tenant_key: str, pest_key: str) -> list[PestImageContribution]:
        return [c for c in self.store.values() if c.tenant_key == tenant_key and c.pest_key == pest_key]

    def list_for_tenant(self, tenant_key: str) -> list[PestImageContribution]:
        return [c for c in self.store.values() if c.tenant_key == tenant_key]

    def list_for_user(self, user_key: str) -> list[PestImageContribution]:
        return [c for c in self.store.values() if c.contributed_by == user_key]

    def get_by_key(self, key: str) -> PestImageContribution | None:
        return self.store.get(key)

    def list_all_for_pest(self, pest_key: str) -> list[PestImageContribution]:
        return [c for c in self.store.values() if c.pest_key == pest_key]

    def list_promoted_for_pest(self, pest_key: str) -> list[PestImageContribution]:
        return [c for c in self.store.values() if c.pest_key == pest_key and c.status == PestImageStatus.PROMOTED]

    def set_status(self, key, status, promoted_by):
        c = self.store.get(key)
        if c is None:
            return None
        if status == PestImageStatus.PROMOTED:
            promoted_at = datetime.now(UTC)
        else:
            promoted_at = None
            promoted_by = None
        updated = c.model_copy(update={"status": status, "promoted_at": promoted_at, "promoted_by": promoted_by})
        self.store[key] = updated
        return updated

    def delete(self, key: str, tenant_key: str) -> bool:
        c = self.store.get(key)
        if c is None or c.tenant_key != tenant_key:
            return False
        del self.store[key]
        return True

    def delete_for_tenant(self, tenant_key: str) -> int:
        keys = [k for k, c in self.store.items() if c.tenant_key == tenant_key]
        for k in keys:
            del self.store[k]
        return len(keys)


class _FakeAttachmentService:
    """Mimics the slice of AttachmentService the PestImageService uses."""

    def __init__(self) -> None:
        self.store: dict[str, Attachment] = {}
        self._seq = 0
        self.upload_calls: list[dict] = []
        self.deleted: list[str] = []

    def max_upload_bytes(self) -> int:
        return 25 * 1024 * 1024

    async def upload(
        self,
        *,
        tenant_key: str,
        user_key: str,
        data: bytes,
        mime_type: str,
        original_filename: str,
        category: AttachmentCategory,
    ) -> Attachment:
        self.upload_calls.append(
            {
                "tenant_key": tenant_key,
                "user_key": user_key,
                "category": category,
                "mime_type": mime_type,
                "filename": original_filename,
            }
        )
        self._seq += 1
        key = f"att{self._seq}"
        att = Attachment(
            _key=key,
            tenant_key=tenant_key,
            mime_type=mime_type,
            byte_size=len(data),
            sha256="x" * 64,
            original_filename=original_filename,
            created_by=user_key,
            category=category,
            storage_key=f"{tenant_key}/{key}",
            created_at=datetime.now(UTC),
        )
        self.store[key] = att
        return att

    def seed_attachment(self, attachment_id: str, tenant_key: str, mime_type: str = "image/jpeg") -> None:
        """Inject a pre-existing attachment (e.g. an inspection photo) directly."""
        self.store[attachment_id] = Attachment(
            _key=attachment_id,
            tenant_key=tenant_key,
            mime_type=mime_type,
            byte_size=123,
            sha256="y" * 64,
            original_filename=f"{attachment_id}.jpg",
            created_by="u1",
            category=AttachmentCategory.PLANT,
            storage_key=f"{tenant_key}/{attachment_id}",
            created_at=datetime.now(UTC),
        )

    def get_attachment(self, attachment_id: str, tenant_key: str) -> Attachment:
        from app.common.exceptions import AttachmentNotFoundError

        att = self.store.get(attachment_id)
        if att is None or att.tenant_key != tenant_key:
            raise AttachmentNotFoundError(attachment_id)
        return att

    async def delete(self, attachment_id: str, tenant_key: str) -> bool:
        self.deleted.append((attachment_id, tenant_key))
        att = self.store.get(attachment_id)
        if att is None or att.tenant_key != tenant_key:
            return False
        del self.store[attachment_id]
        return True

    async def open_stream(self, attachment):
        async def _gen():
            yield b"bytes-for-" + (attachment.key or "x").encode()

        return _gen()

    async def open_thumbnail_stream(self, attachment, size):
        async def _gen():
            yield b"thumb"

        return _gen()


class _FakeIpmService:
    def __init__(self, known_pests: set[str]) -> None:
        self._known = known_pests
        self.get_pest_calls: list[str] = []
        # Maps (tenant_key, pest_key) → ordered, deduplicated attachment ids,
        # mirroring ArangoIpmRepository.get_inspection_photo_refs_for_pest.
        self.inspection_photo_refs: dict[tuple[str, str], list[str]] = {}
        self.inspection_calls: list[tuple[str, str]] = []

    def get_pest(self, key: str) -> Pest:
        self.get_pest_calls.append(key)
        if key not in self._known:
            raise NotFoundError("Pest", key)
        return Pest(_key=key, scientific_name="Tetranychus urticae", common_name="Spider Mites")

    def get_inspection_photo_refs_for_pest(self, tenant_key: str, pest_key: str) -> list[str]:
        self.inspection_calls.append((tenant_key, pest_key))
        return list(self.inspection_photo_refs.get((tenant_key, pest_key), []))


def _service(*, known_pests: set[str] | None = None):
    repo = _FakePestImageRepo()
    attachments = _FakeAttachmentService()
    ipm = _FakeIpmService(known_pests if known_pests is not None else {"p1"})
    service = PestImageService(repo, attachments, ipm)  # type: ignore[arg-type]
    return service, repo, attachments, ipm


class TestContribute:
    @pytest.mark.asyncio
    async def test_uploads_and_persists_contribution(self):
        service, repo, attachments, ipm = _service()

        view = await service.contribute(
            tenant_key="t1",
            user_key="u1",
            pest_key="p1",
            data=b"jpeg-bytes",
            mime_type="image/jpeg",
            filename="mite.jpg",
            caption="  on the underside  ",
        )

        # Pest validated before upload.
        assert ipm.get_pest_calls == ["p1"]
        # Upload ran through the attachment service with the right category.
        assert len(attachments.upload_calls) == 1
        assert attachments.upload_calls[0]["category"] == AttachmentCategory.PEST_REFERENCE
        assert attachments.upload_calls[0]["tenant_key"] == "t1"
        # Contribution persisted and linked to the attachment.
        assert len(repo.store) == 1
        contribution = view.contribution
        assert contribution.tenant_key == "t1"
        assert contribution.pest_key == "p1"
        assert contribution.contributed_by == "u1"
        assert contribution.attachment_id in attachments.store
        assert contribution.status == PestImageStatus.PRIVATE
        # Caption trimmed.
        assert contribution.caption == "on the underside"
        # JPEG is renderable → thumbnail available.
        assert view.has_thumbnail is True

    @pytest.mark.asyncio
    async def test_blank_caption_becomes_none(self):
        service, _repo, _attachments, _ipm = _service()
        view = await service.contribute(
            tenant_key="t1",
            user_key="u1",
            pest_key="p1",
            data=b"x",
            mime_type="image/jpeg",
            filename="f.jpg",
            caption="   ",
        )
        assert view.contribution.caption is None

    @pytest.mark.asyncio
    async def test_unknown_pest_raises_and_does_not_upload(self):
        service, repo, attachments, _ipm = _service(known_pests=set())

        with pytest.raises(NotFoundError):
            await service.contribute(
                tenant_key="t1",
                user_key="u1",
                pest_key="ghost",
                data=b"x",
                mime_type="image/jpeg",
                filename="f.jpg",
                caption=None,
            )

        # No orphan upload, no contribution.
        assert attachments.upload_calls == []
        assert repo.store == {}


class TestListForPest:
    @pytest.mark.asyncio
    async def test_returns_only_own_tenant_contributions(self):
        service, _repo, _attachments, _ipm = _service()
        await service.contribute(
            tenant_key="t1",
            user_key="u1",
            pest_key="p1",
            data=b"a",
            mime_type="image/jpeg",
            filename="a.jpg",
            caption=None,
        )
        # Foreign tenant contributes to the same global pest.
        await service.contribute(
            tenant_key="t2",
            user_key="u2",
            pest_key="p1",
            data=b"b",
            mime_type="image/jpeg",
            filename="b.jpg",
            caption=None,
        )

        views_t1 = service.list_for_pest("t1", "p1")
        views_t2 = service.list_for_pest("t2", "p1")

        assert len(views_t1) == 1
        assert views_t1[0].contribution.tenant_key == "t1"
        assert len(views_t2) == 1
        assert views_t2[0].contribution.tenant_key == "t2"

    @pytest.mark.asyncio
    async def test_thumbnail_flag_reflects_mime(self):
        service, _repo, _attachments, _ipm = _service()
        await service.contribute(
            tenant_key="t1",
            user_key="u1",
            pest_key="p1",
            data=b"a",
            mime_type="image/jpeg",
            filename="a.jpg",
            caption=None,
        )
        views = service.list_for_pest("t1", "p1")
        assert views[0].has_thumbnail is True

    def test_empty_when_no_contributions(self):
        service, _repo, _attachments, _ipm = _service()
        assert service.list_for_pest("t1", "p1") == []


class TestDelete:
    @pytest.mark.asyncio
    async def test_deletes_contribution_and_attachment(self):
        service, repo, attachments, _ipm = _service()
        view = await service.contribute(
            tenant_key="t1",
            user_key="u1",
            pest_key="p1",
            data=b"a",
            mime_type="image/jpeg",
            filename="a.jpg",
            caption=None,
        )
        contribution_key = view.contribution.key
        attachment_id = view.contribution.attachment_id

        result = await service.delete("t1", "u1", contribution_key)

        assert result is True
        assert contribution_key not in repo.store
        assert (attachment_id, "t1") in attachments.deleted
        assert attachment_id not in attachments.store

    @pytest.mark.asyncio
    async def test_foreign_tenant_cannot_delete(self):
        service, repo, attachments, _ipm = _service()
        view = await service.contribute(
            tenant_key="t1",
            user_key="u1",
            pest_key="p1",
            data=b"a",
            mime_type="image/jpeg",
            filename="a.jpg",
            caption=None,
        )
        contribution_key = view.contribution.key

        # A different tenant must not be able to delete it.
        result = await service.delete("t2", "u2", contribution_key)

        assert result is False
        assert contribution_key in repo.store  # untouched
        assert attachments.deleted == []  # attachment never touched

    @pytest.mark.asyncio
    async def test_unknown_contribution_returns_false(self):
        service, _repo, attachments, _ipm = _service()
        result = await service.delete("t1", "u1", "missing")
        assert result is False
        assert attachments.deleted == []


async def _contribute(service, *, tenant_key, user_key="u1", pest_key="p1", data=b"a"):
    return await service.contribute(
        tenant_key=tenant_key,
        user_key=user_key,
        pest_key=pest_key,
        data=data,
        mime_type="image/jpeg",
        filename="a.jpg",
        caption=None,
    )


class TestSetPromotion:
    @pytest.mark.asyncio
    async def test_promote_sets_status_and_audit(self):
        service, repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key

        promoted = service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")

        assert promoted is not None
        assert promoted.contribution.status == PestImageStatus.PROMOTED
        assert promoted.contribution.promoted_by == "admin1"
        assert promoted.contribution.promoted_at is not None
        # is_own is False on the moderation view (cross-tenant perspective).
        assert promoted.is_own is False
        assert repo.store[key].status == PestImageStatus.PROMOTED

    @pytest.mark.asyncio
    async def test_demote_clears_audit(self):
        service, repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key
        service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")

        demoted = service.set_promotion(contribution_key=key, promote=False, admin_user_key="admin1")

        assert demoted.contribution.status == PestImageStatus.PRIVATE
        assert demoted.contribution.promoted_at is None
        assert demoted.contribution.promoted_by is None
        assert repo.store[key].status == PestImageStatus.PRIVATE

    @pytest.mark.asyncio
    async def test_promote_is_idempotent(self):
        service, _repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key

        first = service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")
        second = service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin2")

        assert first.contribution.status == PestImageStatus.PROMOTED
        assert second.contribution.status == PestImageStatus.PROMOTED

    def test_promote_unknown_returns_none(self):
        service, _repo, _attachments, _ipm = _service()
        assert service.set_promotion(contribution_key="missing", promote=True, admin_user_key="a") is None


class TestPromotionRecognitionHook:
    """REQ-010 P2 — the promotion transition dispatches the index/retract task.

    The hook is feature-flagged (``pest_detection_enabled``) and only fires on a
    real status transition. We patch ``settings`` + the task module's ``.delay``
    so no broker / inference service is touched.
    """

    @pytest.mark.asyncio
    async def test_promote_dispatches_index_task(self, monkeypatch):
        import app.tasks.pest_image_tasks as task_mod
        from app.config.settings import settings

        monkeypatch.setattr(settings, "pest_detection_enabled", True)
        index_delay = MagicMock()
        retract_delay = MagicMock()
        monkeypatch.setattr(task_mod.index_promoted_pest_image_task, "delay", index_delay)
        monkeypatch.setattr(task_mod.retract_promoted_pest_image_task, "delay", retract_delay)

        service, _repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key

        service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")

        index_delay.assert_called_once_with(key)
        retract_delay.assert_not_called()

    @pytest.mark.asyncio
    async def test_demote_dispatches_retract_task(self, monkeypatch):
        import app.tasks.pest_image_tasks as task_mod
        from app.config.settings import settings

        monkeypatch.setattr(settings, "pest_detection_enabled", True)
        index_delay = MagicMock()
        retract_delay = MagicMock()
        monkeypatch.setattr(task_mod.index_promoted_pest_image_task, "delay", index_delay)
        monkeypatch.setattr(task_mod.retract_promoted_pest_image_task, "delay", retract_delay)

        service, _repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key
        service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")
        index_delay.reset_mock()

        service.set_promotion(contribution_key=key, promote=False, admin_user_key="admin1")

        retract_delay.assert_called_once_with(key)
        index_delay.assert_not_called()

    @pytest.mark.asyncio
    async def test_feature_flag_off_does_not_dispatch(self, monkeypatch):
        import app.tasks.pest_image_tasks as task_mod
        from app.config.settings import settings

        monkeypatch.setattr(settings, "pest_detection_enabled", False)
        index_delay = MagicMock()
        monkeypatch.setattr(task_mod.index_promoted_pest_image_task, "delay", index_delay)

        service, _repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key

        service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")

        index_delay.assert_not_called()

    @pytest.mark.asyncio
    async def test_idempotent_promote_does_not_redispatch(self, monkeypatch):
        import app.tasks.pest_image_tasks as task_mod
        from app.config.settings import settings

        monkeypatch.setattr(settings, "pest_detection_enabled", True)
        index_delay = MagicMock()
        monkeypatch.setattr(task_mod.index_promoted_pest_image_task, "delay", index_delay)

        service, _repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key

        service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")
        # A second promote is a no-op transition → no re-dispatch.
        service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin2")

        index_delay.assert_called_once_with(key)


class TestResolvePromotedContent:
    @pytest.mark.asyncio
    async def test_promoted_image_resolves(self):
        service, _repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key
        service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")

        content = service.resolve_promoted_content(key)

        assert isinstance(content, PestImageContent)
        assert content.contribution.key == key

    @pytest.mark.asyncio
    async def test_private_image_resolves_to_none(self):
        """SECURITY: a private contribution must never resolve for global serving."""
        service, _repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")

        assert service.resolve_promoted_content(view.contribution.key) is None

    def test_unknown_resolves_to_none(self):
        service, _repo, _attachments, _ipm = _service()
        assert service.resolve_promoted_content("missing") is None

    @pytest.mark.asyncio
    async def test_promoted_then_demoted_no_longer_resolves(self):
        service, _repo, _attachments, _ipm = _service()
        view = await _contribute(service, tenant_key="t1")
        key = view.contribution.key
        service.set_promotion(contribution_key=key, promote=True, admin_user_key="admin1")
        service.set_promotion(contribution_key=key, promote=False, admin_user_key="admin1")

        assert service.resolve_promoted_content(key) is None


class TestCombinedListForPest:
    @pytest.mark.asyncio
    async def test_returns_own_plus_foreign_promoted(self):
        service, _repo, _attachments, _ipm = _service()
        own = await _contribute(service, tenant_key="t1", user_key="u1")
        foreign = await _contribute(service, tenant_key="t2", user_key="u2")
        # Promote the foreign one.
        service.set_promotion(contribution_key=foreign.contribution.key, promote=True, admin_user_key="admin1")
        # A second foreign one stays private → must NOT appear for t1.
        foreign_private = await _contribute(service, tenant_key="t3", user_key="u3")

        views = service.list_for_pest("t1", "p1")
        keys = {v.contribution.key: v.is_own for v in views}

        assert own.contribution.key in keys
        assert keys[own.contribution.key] is True
        assert foreign.contribution.key in keys
        assert keys[foreign.contribution.key] is False
        assert foreign_private.contribution.key not in keys

    @pytest.mark.asyncio
    async def test_own_promoted_not_duplicated_and_stays_own(self):
        service, _repo, _attachments, _ipm = _service()
        own = await _contribute(service, tenant_key="t1", user_key="u1")
        service.set_promotion(contribution_key=own.contribution.key, promote=True, admin_user_key="admin1")

        views = service.list_for_pest("t1", "p1")

        matching = [v for v in views if v.contribution.key == own.contribution.key]
        assert len(matching) == 1
        assert matching[0].is_own is True


class TestErasure:
    @pytest.mark.asyncio
    async def test_delete_all_for_tenant_removes_docs_and_attachments(self):
        service, repo, attachments, _ipm = _service()
        a = await _contribute(service, tenant_key="t1", user_key="u1")
        b = await _contribute(service, tenant_key="t1", user_key="u2")
        other = await _contribute(service, tenant_key="t2", user_key="u3")

        removed = await service.delete_all_for_tenant("t1")

        assert removed == 2
        assert a.contribution.key not in repo.store
        assert b.contribution.key not in repo.store
        assert other.contribution.key in repo.store  # foreign tenant untouched
        assert (a.contribution.attachment_id, "t1") in attachments.deleted

    @pytest.mark.asyncio
    async def test_delete_all_for_user_removes_across_tenants(self):
        service, repo, attachments, _ipm = _service()
        # Same user contributes in two tenants.
        a = await _contribute(service, tenant_key="t1", user_key="u1")
        b = await _contribute(service, tenant_key="t2", user_key="u1")
        other = await _contribute(service, tenant_key="t1", user_key="u2")

        removed = await service.delete_all_for_user("u1")

        assert removed == 2
        assert a.contribution.key not in repo.store
        assert b.contribution.key not in repo.store
        assert other.contribution.key in repo.store
        # Each attachment deleted against its own tenant.
        assert (a.contribution.attachment_id, "t1") in attachments.deleted
        assert (b.contribution.attachment_id, "t2") in attachments.deleted


class TestListInspectionImagesForPest:
    """REQ-010 — read-only inspection photos surfaced in the pest detail gallery."""

    def test_returns_resolvable_inspection_photos(self):
        service, _repo, attachments, ipm = _service()
        attachments.seed_attachment("att-i1", "t1")
        attachments.seed_attachment("att-i2", "t1")
        ipm.inspection_photo_refs[("t1", "p1")] = ["att-i1", "att-i2"]

        views = service.list_inspection_images_for_pest("t1", "p1")

        # Pest validated first (consistent 404 with the contribution path).
        assert ipm.get_pest_calls == ["p1"]
        assert [v.attachment_id for v in views] == ["att-i1", "att-i2"]
        assert all(v.has_thumbnail for v in views)
        assert ipm.inspection_calls == [("t1", "p1")]

    def test_unknown_pest_raises(self):
        service, _repo, _attachments, _ipm = _service(known_pests=set())
        with pytest.raises(NotFoundError):
            service.list_inspection_images_for_pest("t1", "ghost")

    def test_strict_tenant_isolation(self):
        """Only the calling tenant's inspection refs are ever resolved."""
        service, _repo, attachments, ipm = _service()
        attachments.seed_attachment("att-t1", "t1")
        attachments.seed_attachment("att-t2", "t2")
        ipm.inspection_photo_refs[("t1", "p1")] = ["att-t1"]
        ipm.inspection_photo_refs[("t2", "p1")] = ["att-t2"]

        views_t1 = service.list_inspection_images_for_pest("t1", "p1")

        assert [v.attachment_id for v in views_t1] == ["att-t1"]
        # The repo lookup was scoped to t1 only.
        assert ipm.inspection_calls == [("t1", "p1")]

    def test_stale_ref_is_skipped(self):
        """A photo_ref whose attachment vanished is dropped, not surfaced broken."""
        service, _repo, attachments, ipm = _service()
        attachments.seed_attachment("att-live", "t1")
        # "att-gone" is referenced but has no attachment metadata.
        ipm.inspection_photo_refs[("t1", "p1")] = ["att-gone", "att-live"]

        views = service.list_inspection_images_for_pest("t1", "p1")

        assert [v.attachment_id for v in views] == ["att-live"]

    def test_empty_when_no_inspection_photos(self):
        service, _repo, _attachments, _ipm = _service()
        assert service.list_inspection_images_for_pest("t1", "p1") == []
