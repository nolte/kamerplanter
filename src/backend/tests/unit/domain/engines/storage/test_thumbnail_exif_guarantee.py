"""NFR-013 §8.2 / REQ-050 §4.4 — thumbnail renditions are EXIF-free, provably.

REQ-050 §4.4 delivers thumbnail renditions to an *external* language model over
MCP and justifies that with exactly one property: renditions carry no EXIF —
also not when the tenant enabled ``STORAGE_KEEP_EXIF_<CATEGORY>``, which governs
the stored original only (NFR-013 §6.4). NFR-013 §8.2 v1.3 requires that
property to be actively ensured and tested rather than assumed as a side effect
of re-encoding, which is what these tests do:

* :class:`TestSourceFixturesReallyCarryMetadata` guards against the failure mode
  where the whole file passes because the source never had EXIF to begin with.
* :class:`TestRenditionsAreMetadataFree` asserts the property per source format
  and per rendition size, both semantically (Pillow finds no metadata) and
  literally (the marker strings do not occur in the encoded bytes).
* :class:`TestKeepExifTenantStillGetsCleanRenditions` runs the *real* pipeline
  with ``storage_strip_exif=False`` — the keep-EXIF tenant — from upload through
  the thumbnail task, and asserts the split: original keeps its GPS, renditions
  do not.
* :class:`TestMetadataLeakFailsClosed` pins the behaviour when the guarantee is
  violated: raise, emit nothing.
"""

from __future__ import annotations

import io
from typing import Any
from unittest.mock import patch

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase

from app.common.enums import AttachmentCategory
from app.common.exceptions import NotFoundError
from app.config.settings import Settings
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.engines.storage.thumbnail_generator import (
    THUMBNAIL_SIZES,
    ThumbnailGenerator,
    ThumbnailMetadataError,
    metadata_keys,
    thumbnail_key,
)
from app.domain.models.attachment import Attachment
from app.domain.services.attachment_service import AttachmentService
from tests.unit.domain.engines.storage.conftest import (
    CAMERA_MAKE,
    CAMERA_MODEL,
    CAPTURE_TIME,
    XMP_MARKER,
    gps_exif,
)

MAX_SIZE = 25 * 1024 * 1024

#: Byte sequences that must not appear anywhere in a rendition. Covers the RIFF
#: container chunks as well as the payload markers themselves, so a leak is
#: caught even if it lands in a container Pillow does not decode back.
FORBIDDEN_MARKERS: tuple[bytes, ...] = (
    b"EXIF",  # RIFF EXIF chunk id
    b"Exif\x00\x00",  # TIFF/JPEG EXIF header
    b"XMP ",  # RIFF XMP chunk id
    XMP_MARKER,
    CAMERA_MAKE.encode(),
    CAMERA_MODEL.encode(),
    CAPTURE_TIME.encode(),
)


def _exif_of(data: bytes) -> dict[int, Any]:
    with Image.open(io.BytesIO(data)) as img:
        return dict(img.getexif())


def _gps_of(data: bytes) -> dict[int, Any]:
    with Image.open(io.BytesIO(data)) as img:
        return dict(img.getexif().get_ifd(ExifBase.GPSInfo.value))


def _assert_metadata_free(data: bytes, *, context: str) -> None:
    """Assert an encoded image carries no EXIF/GPS/XMP/ICC, three ways."""
    assert metadata_keys(data) == [], f"{context}: metadata blocks present"
    assert _exif_of(data) == {}, f"{context}: EXIF tags readable"
    assert _gps_of(data) == {}, f"{context}: GPS IFD readable"
    for marker in FORBIDDEN_MARKERS:
        assert marker not in data, f"{context}: raw marker {marker!r} found in encoded bytes"


class TestSourceFixturesReallyCarryMetadata:
    """Without this, every assertion below could pass on an empty source."""

    def test_jpeg_source_has_gps_and_device_tags(self, jpeg_with_gps: bytes) -> None:
        exif = _exif_of(jpeg_with_gps)
        assert exif[ExifBase.Make.value] == CAMERA_MAKE
        assert exif[ExifBase.Model.value] == CAMERA_MODEL
        assert exif[ExifBase.DateTime.value] == CAPTURE_TIME
        gps = _gps_of(jpeg_with_gps)
        assert gps[2] == (52.0, 31.0, 12.0)  # GPSLatitude
        assert gps[4] == (13.0, 24.0, 36.0)  # GPSLongitude
        assert b"Exif\x00\x00" in jpeg_with_gps

    def test_png_source_has_gps(self, png_with_gps: bytes) -> None:
        assert _gps_of(png_with_gps)[2] == (52.0, 31.0, 12.0)

    def test_webp_source_has_gps_and_xmp(self, webp_with_gps: bytes) -> None:
        assert _gps_of(webp_with_gps)[2] == (52.0, 31.0, 12.0)
        with Image.open(io.BytesIO(webp_with_gps)) as img:
            assert img.info["xmp"] == XMP_MARKER


class TestRenditionsAreMetadataFree:
    """NFR-013 §8.2 — no rendition, of any size, from any source, carries EXIF."""

    def setup_method(self) -> None:
        self.generator = ThumbnailGenerator()

    @pytest.mark.parametrize(
        ("fixture_name", "mime_type"),
        [
            ("jpeg_with_gps", "image/jpeg"),
            ("png_with_gps", "image/png"),
            ("webp_with_gps", "image/webp"),
        ],
    )
    def test_all_renditions_are_metadata_free(self, request, fixture_name: str, mime_type: str) -> None:
        source: bytes = request.getfixturevalue(fixture_name)
        thumbs = self.generator.generate(source, mime_type)

        assert [t.size for t in thumbs] == list(THUMBNAIL_SIZES)
        for thumb in thumbs:
            _assert_metadata_free(thumb.data, context=f"{mime_type} → t{thumb.size}")

    def test_renditions_are_still_valid_images(self, jpeg_with_gps: bytes) -> None:
        """Stripping metadata must not cost us the picture itself."""
        for thumb in self.generator.generate(jpeg_with_gps, "image/jpeg"):
            with Image.open(io.BytesIO(thumb.data)) as img:
                img.load()
                assert img.format == "WEBP"
                assert max(img.size) <= thumb.size
                assert img.size[0] > 0

    def test_gif_comment_does_not_survive(self) -> None:
        """GIF is the fourth renderable type; its metadata is free text, not EXIF."""
        buffer = io.BytesIO()
        Image.new("P", (800, 600)).save(buffer, format="GIF", comment=b"secret-comment")

        thumbs = self.generator.generate(buffer.getvalue(), "image/gif")
        assert len(thumbs) == len(THUMBNAIL_SIZES)
        for thumb in thumbs:
            assert b"secret-comment" not in thumb.data
            assert metadata_keys(thumb.data) == []

    def test_source_bytes_are_not_mutated(self, jpeg_with_gps: bytes) -> None:
        """The generator clears metadata on its renditions, never on the input.

        The original is a separate promise (``STORAGE_KEEP_EXIF_<CATEGORY>``);
        the generator must not silently decide it for the caller.
        """
        before = bytes(jpeg_with_gps)
        self.generator.generate(jpeg_with_gps, "image/jpeg")
        assert jpeg_with_gps == before
        assert _gps_of(jpeg_with_gps)[2] == (52.0, 31.0, 12.0)


class TestKeepExifTenantStillGetsCleanRenditions:
    """The decisive case: ``STORAGE_KEEP_EXIF_<CATEGORY>=true``.

    Modelled with ``storage_strip_exif=False`` — the setting the upload pipeline
    actually branches on (``AttachmentService.upload`` step 7) — so the stored
    original keeps its EXIF and the thumbnail task is fed EXIF-bearing bytes.
    That is precisely the state in which the REQ-050 §4.4 promise could be
    false, so it is asserted end to end rather than on the engine alone.
    """

    async def test_original_keeps_exif_but_renditions_do_not(self, tmp_path, jpeg_with_gps: bytes) -> None:
        from app.tasks import storage_tasks

        adapter = LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://localhost:8000/api/v1/attachments/token",
            signing_secret="test-secret-please-change",
            max_object_size_bytes=MAX_SIZE,
        )
        repo = _InMemoryAttachmentRepo()
        settings = Settings(storage_strip_exif=False)  # ← keep-EXIF tenant
        service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)

        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            attachment = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg_with_gps,
                mime_type="image/jpeg",
                original_filename="garden.jpg",
                category=AttachmentCategory.DIARY,
            )

        # The original was intentionally kept intact — otherwise the test would
        # be asserting the guarantee on an already-stripped source.
        stored_original = await _collect(await adapter.get_object(attachment.storage_key))
        assert _gps_of(stored_original)[2] == (52.0, 31.0, 12.0)
        assert _exif_of(stored_original)[ExifBase.Model.value] == CAMERA_MODEL

        with (
            patch.object(storage_tasks, "get_object_storage", return_value=adapter),
            patch.object(storage_tasks, "get_attachment_repo", return_value=repo),
        ):
            result = await storage_tasks._generate(attachment.key, "t-1")

        assert result["generated"] == len(THUMBNAIL_SIZES)
        for size in THUMBNAIL_SIZES:
            rendition = await _collect(await adapter.get_object(thumbnail_key(attachment.storage_key, size)))
            _assert_metadata_free(rendition, context=f"keep-exif tenant → stored t{size}")


def _patch_encoder_to_reinstate_exif(monkeypatch) -> None:
    """Make the WEBP writer emit EXIF no matter what the generator asks for.

    This is the scenario the post-condition exists for: a Pillow release (or a
    system Pillow outside the pinned 12.3.0 — ``pyproject.toml`` allows
    ``>=11.0,<13.0.0``) whose encoder sources metadata from somewhere the
    generator does not control. The rendition bytes then really do carry GPS,
    so this exercises the check on a genuine leak rather than on a stub.
    """
    original_save = Image.Image.save
    exif_blob = gps_exif().tobytes()

    def _leaking_save(self, fp, format=None, **params):  # noqa: ANN001, ANN202, A002
        params["exif"] = exif_blob
        original_save(self, fp, format=format, **params)

    monkeypatch.setattr(Image.Image, "save", _leaking_save)


class TestMetadataLeakFailsClosed:
    """If the guarantee is ever violated, nothing is emitted (NFR-013 §8.2)."""

    def test_leaking_encoder_raises_and_emits_nothing(self, jpeg_with_gps: bytes, monkeypatch) -> None:
        _patch_encoder_to_reinstate_exif(monkeypatch)

        with pytest.raises(ThumbnailMetadataError) as excinfo:
            ThumbnailGenerator().generate(jpeg_with_gps, "image/jpeg")

        assert excinfo.value.error_code == "THUMBNAIL_METADATA_LEAK"
        # The message names the leaked block but never its content (NFR-013 §9.2).
        assert "exif" in excinfo.value.message
        assert CAMERA_MODEL not in excinfo.value.message
        # The smallest size is rejected first — no partial batch escapes.
        assert f"{THUMBNAIL_SIZES[0]} px" in excinfo.value.message

    async def test_leak_aborts_the_celery_task_without_storing_renditions(
        self, tmp_path, jpeg_with_gps: bytes, monkeypatch
    ) -> None:
        """A leaking rendition must never reach the object storage."""
        from app.tasks import storage_tasks

        adapter = LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://localhost:8000/api/v1/attachments/token",
            signing_secret="test-secret-please-change",
            max_object_size_bytes=MAX_SIZE,
        )
        repo = _InMemoryAttachmentRepo()
        settings = Settings(storage_strip_exif=False)
        service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)
        with patch("app.tasks.storage_tasks.generate_thumbnails.delay"):
            attachment = await service.upload(
                tenant_key="t-1",
                user_key="u-1",
                data=jpeg_with_gps,
                mime_type="image/jpeg",
                original_filename="garden.jpg",
                category=AttachmentCategory.DIARY,
            )

        _patch_encoder_to_reinstate_exif(monkeypatch)
        with (
            patch.object(storage_tasks, "get_object_storage", return_value=adapter),
            patch.object(storage_tasks, "get_attachment_repo", return_value=repo),
            pytest.raises(ThumbnailMetadataError),
        ):
            await storage_tasks._generate(attachment.key, "t-1")

        for size in THUMBNAIL_SIZES:
            with pytest.raises(NotFoundError):
                await adapter.head_object(thumbnail_key(attachment.storage_key, size))


class TestMetadataKeysHelper:
    def test_reports_blocks_of_a_metadata_bearing_image(self, webp_with_gps: bytes) -> None:
        assert metadata_keys(webp_with_gps) == ["exif", "xmp"]

    def test_empty_for_clean_image(self, plain_jpeg: bytes) -> None:
        assert metadata_keys(plain_jpeg) == []

    def test_undecodable_bytes_report_nothing(self) -> None:
        assert metadata_keys(b"not-an-image") == []


class _InMemoryAttachmentRepo:
    """Minimal IAttachmentRepository double for the upload + thumbnail path."""

    def __init__(self) -> None:
        self._store: dict[str, Attachment] = {}
        self._seq = 0

    def create(self, attachment: Attachment) -> Attachment:
        self._seq += 1
        key = f"att{self._seq}"
        stored = attachment.model_copy(update={"key": key})
        self._store[key] = stored
        return stored

    def get(self, key: str, tenant_key: str) -> Attachment | None:
        att = self._store.get(key)
        if att is None or att.tenant_key != tenant_key:
            return None
        return att

    def find_by_sha256(self, tenant_key: str, sha256: str) -> Attachment | None:
        for att in self._store.values():
            if att.tenant_key == tenant_key and att.sha256 == sha256:
                return att
        return None

    def count_by_tenant(self, tenant_key: str) -> int:
        return sum(1 for a in self._store.values() if a.tenant_key == tenant_key)

    def sum_bytes_by_tenant(self, tenant_key: str) -> int:
        return sum(a.byte_size for a in self._store.values() if a.tenant_key == tenant_key)


async def _collect(stream) -> bytes:
    out = bytearray()
    async for chunk in stream:
        out.extend(chunk)
    return bytes(out)
