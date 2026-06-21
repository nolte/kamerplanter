"""REQ-044 §4.3 — Tiling-Baustein (Pflicht) gegen das Small-Object-Problem.

Zerlegt ein hochauflösendes Bild in überlappende Kacheln, sodass winzige
Schädlinge/Symptome (AgriPest Ø 0,16 % Bildfläche, §2.1) nicht systematisch
übersehen werden. Nach der Detektion pro Kachel werden überlappende Boxen via
greedy NMS (SAHI ``GREEDYNMM``/``IOS``, WP-3.3) zurück ins Vollbild gemerged.

Pure-logic + In-Memory-PIL; geteilte Infrastruktur mit REQ-038 (§0).
"""

import io

from PIL import Image

from app.domain.interfaces.pest_detection_adapter import PestFinding

# §4.3 / Prep §6 — Tag-1-Default. Die finale, klassenweise Schwelle kommt aus
# WP-5 (Temperature Scaling + Energy-Gate + Risk-Coverage auf Feld-Daten).
ABSTAIN_CONFIDENCE = 0.40

# WP-3.3 — SAHI match metric IOS / match_threshold; greedy NMS suppression.
_NMS_IOU_THRESHOLD = 0.5


class ImageTiler:
    """Slice an image into overlapping tiles and merge per-tile detections."""

    def tile(self, image: bytes, *, tile: int = 512, overlap: float = 0.2) -> list[bytes]:
        """Split ``image`` into overlapping square tiles (JPEG bytes each).

        An image smaller than one tile yields a single tile (the whole image),
        so the caller always receives at least one tile to run inference on.

        Raises:
            ValueError: when the bytes cannot be decoded as an image.
        """
        if not 0.0 <= overlap < 1.0:
            raise ValueError("overlap must be in [0, 1).")
        if tile <= 0:
            raise ValueError("tile size must be positive.")

        try:
            with Image.open(io.BytesIO(image)) as img:
                rgb = img.convert("RGB")
                width, height = rgb.size
                step = max(1, int(tile * (1.0 - overlap)))

                x_offsets = _tile_offsets(width, tile, step)
                y_offsets = _tile_offsets(height, tile, step)

                tiles: list[bytes] = []
                for top in y_offsets:
                    for left in x_offsets:
                        box = (left, top, min(left + tile, width), min(top + tile, height))
                        crop = rgb.crop(box)
                        buffer = io.BytesIO()
                        crop.save(buffer, format="JPEG", quality=90)
                        tiles.append(buffer.getvalue())
                return tiles
        except (OSError, ValueError) as exc:
            raise ValueError("Image could not be decoded for tiling.") from exc

    def merge_boxes(self, per_tile: list[list[PestFinding]]) -> list[PestFinding]:
        """Merge per-tile findings into full-image findings via greedy NMS.

        Findings are expected to carry boxes already normalized to the full
        image. Boxes of the same label overlapping above the IoU threshold are
        merged (highest confidence wins) so a pest straddling a tile boundary is
        not double-counted (§Szenario 5). Box-less findings (symptom mode) are
        de-duplicated per label, keeping the highest confidence.
        """
        flat: list[PestFinding] = [f for tile_findings in per_tile for f in tile_findings]

        boxed = [f for f in flat if f.bounding_box is not None]
        boxless = [f for f in flat if f.bounding_box is None]

        merged: list[PestFinding] = _greedy_nms(boxed)
        merged.extend(_dedupe_boxless(boxless))
        merged.sort(key=lambda f: f.confidence, reverse=True)
        return merged


def _tile_offsets(extent: int, tile: int, step: int) -> list[int]:
    """Start offsets covering ``extent`` with tiles of ``tile`` width and stride ``step``."""
    if extent <= tile:
        return [0]
    offsets = list(range(0, extent - tile + 1, step))
    last = extent - tile
    if offsets[-1] != last:
        offsets.append(last)
    return offsets


def _iou(a: PestFinding, b: PestFinding) -> float:
    box_a, box_b = a.bounding_box, b.bounding_box
    if box_a is None or box_b is None:
        return 0.0
    ax2, ay2 = box_a.x + box_a.width, box_a.y + box_a.height
    bx2, by2 = box_b.x + box_b.width, box_b.y + box_b.height
    inter_w = max(0.0, min(ax2, bx2) - max(box_a.x, box_b.x))
    inter_h = max(0.0, min(ay2, by2) - max(box_a.y, box_b.y))
    inter = inter_w * inter_h
    if inter <= 0.0:
        return 0.0
    union = box_a.width * box_a.height + box_b.width * box_b.height - inter
    return inter / union if union > 0 else 0.0


def _greedy_nms(findings: list[PestFinding]) -> list[PestFinding]:
    kept: list[PestFinding] = []
    for candidate in sorted(findings, key=lambda f: f.confidence, reverse=True):
        if any(k.label == candidate.label and _iou(k, candidate) >= _NMS_IOU_THRESHOLD for k in kept):
            continue
        kept.append(candidate)
    return kept


def _dedupe_boxless(findings: list[PestFinding]) -> list[PestFinding]:
    best: dict[str, PestFinding] = {}
    for f in findings:
        current = best.get(f.label)
        if current is None or f.confidence > current.confidence:
            best[f.label] = f
    return list(best.values())
