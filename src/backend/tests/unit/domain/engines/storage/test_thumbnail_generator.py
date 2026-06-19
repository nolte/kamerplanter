"""NFR-013 §8.2 — ThumbnailGenerator unit tests."""

from __future__ import annotations

import io

from PIL import Image

from app.domain.engines.storage.thumbnail_generator import (
    THUMBNAIL_SIZES,
    ThumbnailGenerator,
    thumbnail_key,
)


class TestThumbnailGenerator:
    def setup_method(self) -> None:
        self.generator = ThumbnailGenerator()

    def test_generates_three_webp_variants(self, plain_jpeg: bytes) -> None:
        thumbs = self.generator.generate(plain_jpeg, "image/jpeg")
        assert len(thumbs) == 3
        assert [t.size for t in thumbs] == list(THUMBNAIL_SIZES)
        for thumb in thumbs:
            assert thumb.mime_type == "image/webp"
            with Image.open(io.BytesIO(thumb.data)) as img:
                assert img.format == "WEBP"

    def test_longest_edge_clamped_to_size(self, plain_jpeg: bytes) -> None:
        # source is 640x480 → longest edge must not exceed the target.
        for thumb in self.generator.generate(plain_jpeg, "image/jpeg"):
            with Image.open(io.BytesIO(thumb.data)) as img:
                assert max(img.size) <= thumb.size

    def test_never_upscales(self) -> None:
        # 64x64 source is smaller than every target → renditions stay <= source.
        small = Image.new("RGB", (64, 64), (10, 20, 30))
        buffer = io.BytesIO()
        small.save(buffer, format="PNG")
        thumbs = self.generator.generate(buffer.getvalue(), "image/png")
        for thumb in thumbs:
            with Image.open(io.BytesIO(thumb.data)) as img:
                assert max(img.size) <= 64

    def test_non_renderable_returns_empty(self) -> None:
        assert self.generator.generate(b"%PDF-1.7", "application/pdf") == []

    def test_thumbnail_key_scheme(self) -> None:
        original = "t/tenant_a/diary/2026/06/01ABCDEF.jpg"
        assert thumbnail_key(original, 128) == "t/tenant_a/diary/2026/06/01ABCDEF_t128.webp"
        assert thumbnail_key(original, 512) == "t/tenant_a/diary/2026/06/01ABCDEF_t512.webp"
