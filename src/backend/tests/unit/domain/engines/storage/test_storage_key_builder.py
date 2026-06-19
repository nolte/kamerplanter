"""NFR-013 §4.3 — StorageKeyBuilder + ULID unit tests."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest

from app.common.enums import AttachmentCategory
from app.domain.engines.storage.storage_key_builder import (
    StorageKeyBuilder,
    generate_ulid,
)

_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


class TestUlid:
    def test_ulid_is_26_crockford_chars(self) -> None:
        ulid = generate_ulid()
        assert len(ulid) == 26
        assert _ULID_RE.match(ulid), ulid

    def test_ulids_are_unique(self) -> None:
        ulids = {generate_ulid() for _ in range(1000)}
        assert len(ulids) == 1000

    def test_ulid_is_time_sortable(self) -> None:
        early = generate_ulid(1_000)
        late = generate_ulid(2_000_000_000_000)
        assert early < late


class TestStorageKeyBuilder:
    def setup_method(self) -> None:
        self.builder = StorageKeyBuilder()

    def test_key_follows_scheme(self) -> None:
        created = datetime(2026, 6, 9, 10, 30, tzinfo=UTC)
        key = self.builder.build(
            tenant_key="tenant_a",
            category=AttachmentCategory.DIARY,
            mime_type="image/jpeg",
            created_at=created,
        )
        assert re.match(r"^t/tenant_a/diary/2026/06/[0-9A-HJKMNP-TV-Z]{26}\.jpg$", key), key

    def test_extension_always_from_mime_not_filename(self) -> None:
        key = self.builder.build(
            tenant_key="tenant_a",
            category=AttachmentCategory.PLANT,
            mime_type="image/png",
        )
        assert key.endswith(".png")

    @pytest.mark.parametrize(
        ("mime", "ext"),
        [
            ("image/jpeg", "jpg"),
            ("image/png", "png"),
            ("image/webp", "webp"),
            ("image/heic", "heic"),
            ("application/pdf", "pdf"),
            ("text/csv", "csv"),
            ("application/zip", "zip"),
        ],
    )
    def test_mime_to_extension_mapping(self, mime: str, ext: str) -> None:
        assert self.builder.extension_for_mime(mime) == ext

    def test_unknown_mime_raises(self) -> None:
        with pytest.raises(ValueError, match="No extension mapping"):
            self.builder.extension_for_mime("application/x-tar")

    def test_naive_datetime_treated_as_utc(self) -> None:
        naive = datetime(2026, 1, 5, 12, 0)
        key = self.builder.build(
            tenant_key="t1",
            category=AttachmentCategory.EXPORT,
            mime_type="application/pdf",
            created_at=naive,
        )
        assert "/2026/01/" in key

    def test_reuses_supplied_ulid(self) -> None:
        key = self.builder.build(
            tenant_key="t1",
            category=AttachmentCategory.DIARY,
            mime_type="image/jpeg",
            ulid="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        )
        assert key.endswith("/01ARZ3NDEKTSV4RRFFQ69G5FAV.jpg")

    def test_ulid_from_key_roundtrip(self) -> None:
        key = self.builder.build(
            tenant_key="t1",
            category=AttachmentCategory.DIARY,
            mime_type="image/jpeg",
            ulid="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        )
        assert StorageKeyBuilder.ulid_from_key(key) == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
