"""REQ-044 §4.3 — Tiling + box-merge (NMS) unit tests."""

import io

import pytest
from PIL import Image

from app.common.enums import PestFindingCategory, PestFindingMode
from app.domain.calculators.image_tiler import ImageTiler
from app.domain.interfaces.pest_detection_adapter import BoundingBox, PestFinding


def _jpeg(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color=(0, 120, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _boxed(label: str, confidence: float, x: float) -> PestFinding:
    return PestFinding(
        label=label,
        category=PestFindingCategory.PEST,
        common_name=label,
        confidence=confidence,
        mode=PestFindingMode.DIRECT,
        bounding_box=BoundingBox(x=x, y=0.1, width=0.1, height=0.1),
    )


def _symptom(confidence: float) -> PestFinding:
    return PestFinding(
        label="spider_mite",
        category=PestFindingCategory.SYMPTOM,
        common_name="x",
        confidence=confidence,
        mode=PestFindingMode.SYMPTOM,
    )


class TestTile:
    def test_large_image_yields_multiple_overlapping_tiles(self) -> None:
        tiles = ImageTiler().tile(_jpeg(1500, 1000), tile=512, overlap=0.2)
        assert len(tiles) > 1
        assert all(isinstance(t, bytes) and t for t in tiles)

    def test_image_smaller_than_tile_yields_single_tile(self) -> None:
        assert len(ImageTiler().tile(_jpeg(300, 200), tile=512, overlap=0.2)) == 1

    def test_invalid_overlap_rejected(self) -> None:
        with pytest.raises(ValueError):
            ImageTiler().tile(_jpeg(100, 100), overlap=1.0)

    def test_undecodable_bytes_raise(self) -> None:
        with pytest.raises(ValueError):
            ImageTiler().tile(b"not-an-image")


class TestMergeBoxes:
    def test_overlapping_same_label_boxes_collapse_to_highest_confidence(self) -> None:
        # Two boxes for the same pest at a tile boundary must not double-count.
        merged = ImageTiler().merge_boxes([[_boxed("spider_mite", 0.9, 0.10)], [_boxed("spider_mite", 0.5, 0.105)]])
        assert len(merged) == 1
        assert merged[0].confidence == 0.9

    def test_distinct_labels_are_kept(self) -> None:
        merged = ImageTiler().merge_boxes([[_boxed("spider_mite", 0.9, 0.1)], [_boxed("aphid", 0.8, 0.1)]])
        assert {m.label for m in merged} == {"spider_mite", "aphid"}

    def test_non_overlapping_same_label_boxes_kept(self) -> None:
        merged = ImageTiler().merge_boxes([[_boxed("aphid", 0.9, 0.1)], [_boxed("aphid", 0.8, 0.8)]])
        assert len(merged) == 2

    def test_boxless_symptom_findings_deduped_by_label(self) -> None:
        merged = ImageTiler().merge_boxes([[_symptom(0.4)], [_symptom(0.6)]])
        assert len(merged) == 1
        assert merged[0].confidence == 0.6

    def test_results_sorted_by_confidence_desc(self) -> None:
        merged = ImageTiler().merge_boxes([[_boxed("aphid", 0.5, 0.1), _boxed("spider_mite", 0.9, 0.5)]])
        assert [m.confidence for m in merged] == [0.9, 0.5]
