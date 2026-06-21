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

import pytest

from app.common.enums import AttachmentCategory, PestImageStatus
from app.common.exceptions import NotFoundError
from app.domain.models.attachment import Attachment
from app.domain.models.ipm import Pest
from app.domain.models.pest_image import PestImageContribution
from app.domain.services.pest_image_service import PestImageService


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

    def delete(self, key: str, tenant_key: str) -> bool:
        c = self.store.get(key)
        if c is None or c.tenant_key != tenant_key:
            return False
        del self.store[key]
        return True


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

    def get_attachment(self, attachment_id: str, tenant_key: str) -> Attachment:
        from app.common.exceptions import AttachmentNotFoundError

        att = self.store.get(attachment_id)
        if att is None or att.tenant_key != tenant_key:
            raise AttachmentNotFoundError(attachment_id)
        return att

    async def delete(self, attachment_id: str, tenant_key: str) -> bool:
        self.deleted.append(attachment_id)
        att = self.store.get(attachment_id)
        if att is None or att.tenant_key != tenant_key:
            return False
        del self.store[attachment_id]
        return True


class _FakeIpmService:
    def __init__(self, known_pests: set[str]) -> None:
        self._known = known_pests
        self.get_pest_calls: list[str] = []

    def get_pest(self, key: str) -> Pest:
        self.get_pest_calls.append(key)
        if key not in self._known:
            raise NotFoundError("Pest", key)
        return Pest(_key=key, scientific_name="Tetranychus urticae", common_name="Spider Mites")


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
        assert attachment_id in attachments.deleted
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
