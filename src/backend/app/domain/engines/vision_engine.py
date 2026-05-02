"""REQ-029 Vision engine scaffold."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisionPrediction:
    species_key: str
    confidence: float


class VisionEngine:
    """Scaffold pure-logic engine — pins API for REQ-029."""

    def normalise_predictions(self, raw: list[dict]) -> list[VisionPrediction]:
        raise NotImplementedError("REQ-029 VisionEngine.normalise_predictions — pending follow-up.")
