"""REQ-038 -- PlantCV phenotype measurement (measurement only, never diagnosis).

Segments the plant from the background and derives objective colour/shape
metrics (leaf area, green index, discoloured / necrotic area ratios, solidity,
mean hue). These are *measurements*, not a verdict: the classifier proposes a
disease, the phenotype panel quantifies the visible symptom for the human to
judge.

PlantCV is licensed MPL-2.0 (file-level copyleft). It is used strictly as an
unmodified library -- no PlantCV source file is patched -- and imported lazily so
the base image stays lean and the service still boots when the optional ``cv``
extra is not installed. When PlantCV (or OpenCV) is unavailable ``is_available()``
returns False and ``measure`` raises ``PhenotypeUnavailableError``; the endpoint
then simply omits the phenotype block and the disease classification still works.
"""

from __future__ import annotations

import io

import numpy as np
import structlog
from PIL import Image, ImageOps

logger = structlog.get_logger(__name__)


class PhenotypeUnavailableError(RuntimeError):
    """Raised when phenotype measurement is requested but PlantCV is unavailable."""


class PhenotypeMetrics:
    """Objective phenotype measurements for one image."""

    __slots__ = (
        "leaf_area_px",
        "green_index",
        "discolored_area_ratio",
        "necrotic_area_ratio",
        "solidity",
        "hue_circular_mean_deg",
        "plantcv_version",
    )

    def __init__(
        self,
        *,
        leaf_area_px: int,
        green_index: float,
        discolored_area_ratio: float,
        necrotic_area_ratio: float,
        solidity: float,
        hue_circular_mean_deg: float,
        plantcv_version: str,
    ) -> None:
        self.leaf_area_px = leaf_area_px
        self.green_index = green_index
        self.discolored_area_ratio = discolored_area_ratio
        self.necrotic_area_ratio = necrotic_area_ratio
        self.solidity = solidity
        self.hue_circular_mean_deg = hue_circular_mean_deg
        self.plantcv_version = plantcv_version

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "leaf_area_px": self.leaf_area_px,
            "green_index": self.green_index,
            "discolored_area_ratio": self.discolored_area_ratio,
            "necrotic_area_ratio": self.necrotic_area_ratio,
            "solidity": self.solidity,
            "hue_circular_mean_deg": self.hue_circular_mean_deg,
            "plantcv_version": self.plantcv_version,
        }


class PhenotypeEngine:
    """Lazy PlantCV wrapper. Measurement only; safe to instantiate always."""

    def __init__(self, *, enabled: bool = True) -> None:
        self._enabled = enabled
        self._checked = False
        self._available = False
        self._plantcv_version = ""

    def is_available(self) -> bool:
        """Whether PlantCV can be imported (probes lazily, caches the result)."""
        if not self._enabled:
            return False
        if not self._checked:
            self._checked = True
            try:
                import plantcv  # noqa: F401 -- availability probe only

                self._plantcv_version = getattr(plantcv, "__version__", "unknown")
                self._available = True
            except Exception as exc:  # noqa: BLE001 -- optional dependency
                logger.info("plantcv_unavailable", reason=str(exc))
                self._available = False
        return self._available

    def measure(self, image_bytes: bytes) -> PhenotypeMetrics:
        """Compute phenotype metrics for one image.

        Uses PlantCV's colour spaces (LAB/HSV) to threshold the plant mask, then
        derives the metrics. All heavy work is delegated to the unmodified
        library; this method only orchestrates and shapes the output.
        """
        if not self.is_available():
            raise PhenotypeUnavailableError("PlantCV is not installed -- phenotype measurement unavailable")

        from plantcv import plantcv as pcv

        rgb = self._decode_rgb(image_bytes)
        # LAB 'a' channel isolates green-vs-magenta; dark objects on a light
        # background threshold cleanly into a plant mask.
        a_channel = pcv.rgb2gray_lab(rgb_img=rgb, channel="a")
        mask = pcv.threshold.binary(gray_img=a_channel, threshold=120, object_type="dark")
        mask = pcv.fill(bin_img=mask, size=50)

        plant_pixels = int(np.count_nonzero(mask))
        if plant_pixels == 0:
            return self._empty_metrics()

        green_index = self._green_index(rgb, mask)
        discolored, necrotic = self._discoloration_ratios(rgb, mask)
        solidity = self._solidity(mask, plant_pixels)
        hue_mean = self._hue_circular_mean(rgb, mask)

        return PhenotypeMetrics(
            leaf_area_px=plant_pixels,
            green_index=round(green_index, 4),
            discolored_area_ratio=round(discolored, 4),
            necrotic_area_ratio=round(necrotic, 4),
            solidity=round(solidity, 4),
            hue_circular_mean_deg=round(hue_mean, 2),
            plantcv_version=self._plantcv_version,
        )

    # -- internal helpers --------------------------------------------------

    @staticmethod
    def _decode_rgb(image_bytes: bytes) -> np.ndarray:
        """Decode bytes into an EXIF-corrected RGB uint8 array."""
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("RGB")
        return np.asarray(image, dtype=np.uint8)

    def _empty_metrics(self) -> PhenotypeMetrics:
        return PhenotypeMetrics(
            leaf_area_px=0,
            green_index=0.0,
            discolored_area_ratio=0.0,
            necrotic_area_ratio=0.0,
            solidity=0.0,
            hue_circular_mean_deg=0.0,
            plantcv_version=self._plantcv_version,
        )

    @staticmethod
    def _masked_rgb(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
        sel = mask.astype(bool)
        return rgb[sel].astype(np.float32)

    def _green_index(self, rgb: np.ndarray, mask: np.ndarray) -> float:
        """Normalised excess-green (2G - R - B) averaged over the plant, in [0, 1]."""
        pixels = self._masked_rgb(rgb, mask)
        if pixels.size == 0:
            return 0.0
        r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
        exg = (2.0 * g - r - b) / 255.0
        return float(np.clip(np.mean(exg), 0.0, 1.0))

    def _discoloration_ratios(self, rgb: np.ndarray, mask: np.ndarray) -> tuple[float, float]:
        """Fraction of the plant that is discoloured (yellow/brown) vs necrotic (dark brown)."""
        pixels = self._masked_rgb(rgb, mask)
        if pixels.size == 0:
            return 0.0, 0.0
        r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
        # Discoloured: red/green dominate blue and green is not clearly leading (chlorosis/browning).
        discolored = (r > b + 20) & (g > b) & (g <= r + 10)
        # Necrotic: dark and low-saturation brown.
        brightness = (r + g + b) / 3.0
        necrotic = (brightness < 90) & (r >= g) & (g >= b)
        n = pixels.shape[0]
        return float(np.count_nonzero(discolored) / n), float(np.count_nonzero(necrotic) / n)

    @staticmethod
    def _solidity(mask: np.ndarray, plant_pixels: int) -> float:
        """Plant-area / bounding-box-area -- a compactness proxy in [0, 1]."""
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not rows.any() or not cols.any():
            return 0.0
        height = int(np.where(rows)[0][-1] - np.where(rows)[0][0] + 1)
        width = int(np.where(cols)[0][-1] - np.where(cols)[0][0] + 1)
        bbox_area = height * width
        if bbox_area == 0:
            return 0.0
        return float(min(1.0, plant_pixels / bbox_area))

    def _hue_circular_mean(self, rgb: np.ndarray, mask: np.ndarray) -> float:
        """Circular mean of the plant's hue (degrees, 0-360)."""
        pixels = self._masked_rgb(rgb, mask) / 255.0
        if pixels.size == 0:
            return 0.0
        maxc = np.max(pixels, axis=1)
        minc = np.min(pixels, axis=1)
        delta = maxc - minc
        r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
        hue = np.zeros_like(maxc)
        nonzero = delta > 1e-6
        # Standard RGB->hue; guarded against zero delta (greys).
        rc = np.where(maxc == r, ((g - b) / np.where(nonzero, delta, 1)) % 6, 0)
        gc = np.where(maxc == g, ((b - r) / np.where(nonzero, delta, 1)) + 2, 0)
        bc = np.where(maxc == b, ((r - g) / np.where(nonzero, delta, 1)) + 4, 0)
        hue = np.where(nonzero, (rc + gc + bc) * 60.0, 0.0)
        radians = np.deg2rad(hue)
        mean_angle = np.arctan2(np.mean(np.sin(radians)), np.mean(np.cos(radians)))
        degrees = float(np.rad2deg(mean_angle))
        return degrees + 360.0 if degrees < 0 else degrees
