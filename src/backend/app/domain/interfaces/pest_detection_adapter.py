"""REQ-044 §4.2 — Vertrag der bildbasierten Schädlingserkennung.

Gemeinsames Interface für Cloud- und Self-Hosted-Adapter (Modus 1 Direkt-
Detektion und Modus 2 Schadbild/Symptom). Das Ergebnis ist immer ein
vereinheitlichtes ``PestDetectionResult`` — nie eine automatische Behandlung
(§0). Jeder Adapter erhält bereits gekachelte Bilddaten (Tiling-Pflicht, §4.3).
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.common.enums import PestFindingCategory, PestFindingMode

# §4.2 — durchgängiger Disclaimer; ein automatisierter Test prüft, dass dieses
# Feld in keiner API-Antwort leer ist (§8 / Szenario 6).
DEFAULT_PEST_DISCLAIMER = (
    "Nur eine Einschätzung der Bilderkennung — keine gesicherte Schädlings-Bestimmung. "
    "Bitte den Befund prüfen, bevor du behandelst; Nützlinge nicht verwechseln."
)


class BoundingBox(BaseModel):
    """Normalisierte Box (0–1) im Vollbild-Koordinatensystem."""

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(ge=0.0, le=1.0)
    height: float = Field(ge=0.0, le=1.0)


class PestFinding(BaseModel):
    """Ein erkannter Schädlings-, Nützlings- oder Schadbild-Befund."""

    label: str
    category: PestFindingCategory
    common_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    mode: PestFindingMode
    bounding_box: BoundingBox | None = None
    # Mapping gegen REQ-010-Stammdaten (vom Engine gesetzt, nicht vom Adapter).
    matched_pest_key: str | None = None
    matched_beneficial_key: str | None = None  # WP-8


class PestDetectionResult(BaseModel):
    """Vereinheitlichtes Ergebnis (Cloud ODER self-hosted, Modus 1 ODER 2)."""

    is_plant: bool = True
    findings: list[PestFinding] = Field(default_factory=list)
    is_confident: bool = True  # False → Abstention (§4.3)
    tiles_processed: int = 0
    adapter_key: str = ""
    source: str = ""  # PestDetectionSource value
    inference_time_ms: int = 0
    disclaimer: str = DEFAULT_PEST_DISCLAIMER


class PestDetectionAdapter(ABC):
    """Gemeinsamer Vertrag für Cloud- und Self-Hosted-Schädlingserkennung.

    Phase 1: ``LocalPestSymptomAdapter`` (Modus 2, Default) + optional
    ``KindwisePestAdapter`` (Cloud, opt-in).
    Phase 2: ``LocalPestDetectorAdapter`` (Modus 1, quantisiertes ONNX + Tiling).
    """

    adapter_key: str = ""
    # Consent-Zweck, der vor Nutzung erfüllt sein muss (z. B.
    # ``pest_detection_cloud`` für Cloud), oder ``None`` für rein lokale Adapter.
    requires_consent: str | None = None
    # True, wenn der Adapter Bilddaten an einen Dritten sendet (Daten-Egress).
    is_external: bool = False
    # Welche Modi der Adapter liefert: ['direct'] | ['symptom'] | beide.
    supports_modes: list[str] = []

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the adapter has everything it needs to run (model/key/flag)."""

    @abstractmethod
    def detect(self, tiles: list[bytes], *, language: str = "de") -> PestDetectionResult:
        """Detect pests/symptoms across the supplied (already tiled) images."""

    def health_check(self) -> bool:
        return self.is_configured()
