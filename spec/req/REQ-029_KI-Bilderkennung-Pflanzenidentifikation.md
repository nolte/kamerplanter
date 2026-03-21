# Spezifikation: REQ-029 - KI-basierte Pflanzenidentifikation

```yaml
ID: REQ-029
Titel: KI-basierte Pflanzenidentifikation via Plant.id (Optional)
Kategorie: Integration
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery, React, TypeScript, MUI, Flutter
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-001 v5.0 (Stammdaten), REQ-011 v1.0 (Adapter-Pattern), REQ-020 v1.6 (Onboarding-Wizard), REQ-021 v1.0 (Erfahrungsstufen), REQ-022 v2.4 (Pflegeerinnerungen), REQ-024 v1.3 (Mandantenverwaltung)
```

## 1. Business Case

**User Story (Casual User):** "Als Zimmerpflanzen-Besitzer, der den Namen seiner Pflanze nicht kennt, möchte ich ein Foto meiner Pflanze machen und sofort erfahren, um welche Art es sich handelt — damit das System mir passende Pflegehinweise geben kann, ohne dass ich botanische Begriffe nachschlagen muss."

**User Story (Onboarding):** "Als Erstnutzer möchte ich im Onboarding-Wizard meine erste Pflanze per Foto identifizieren und direkt anlegen können — damit ich in unter 30 Sekunden vom Foto zur vollständigen Pflege-Einrichtung komme."

**User Story (Krankheitserkennung):** "Als Gärtner möchte ich ein Foto eines kranken Blatts machen und eine Diagnose mit Behandlungsvorschlägen erhalten — damit ich schnell reagieren kann, bevor der Befall sich ausbreitet."

**User Story (Bestandspflanze):** "Als Nutzer mit 20 Pflanzen im System möchte ich jederzeit eine bestehende Pflanze per Foto neu identifizieren oder eine neue Pflanze per Kamera hinzufügen können — nicht nur beim Onboarding."

**User Story (Offline/Self-Hosted):** "Als Self-Hosted-Nutzer ohne Plant.id-API-Key möchte ich die App trotzdem vollständig nutzen können — die Bilderkennung soll optional sein und mich nie blockieren."

**User Story (Datenschutz):** "Als datenschutzbewusster Nutzer möchte ich wissen, dass meine Pflanzenfotos nur zur Identifikation an den Dienst gesendet und danach nicht gespeichert werden — und ich möchte die Wahl haben, ob ich dieses Feature überhaupt nutze."

**Beschreibung:**

Das Feature integriert einen externen Bilderkennungsdienst (primär: Plant.id by Kindwise) als **optionale Komponente** in das bestehende Adapter-Pattern (REQ-011). Die Bilderkennung dient als niedrigschwelliger Einstiegspunkt für Casual User, die den Namen ihrer Pflanzen nicht kennen, und als Krankheitsdiagnose-Tool für alle Nutzer.

**Grundprinzipien:**

- **Vollständig optional:** Das Feature erfordert einen externen API-Key. Ohne Key ist die Funktion deaktiviert — die App bleibt voll funktionsfähig.
- **Adapter-Pattern:** Neue Bilderkennungsdienste können als Adapter hinzugefügt werden, ohne bestehenden Code zu ändern.
- **Datensparsamkeit:** Bilder werden nur zur Identifikation an den Dienst gesendet, nicht lokal dauerhaft gespeichert (es sei denn, der Nutzer wählt explizit die Foto-Galerie).
- **Graceful Degradation:** Bei API-Ausfall wird die manuelle Artsuche als Fallback angeboten.
- **Consent-basiert:** Die Nutzung erfordert explizite Einwilligung (DSGVO-konform, REQ-025).

### 1.1 Externe Dienste

| Prio | Dienst | Basis-URL | Datentyp | Auth | Free Tier | Kosten (Paid) |
|------|--------|-----------|----------|------|-----------|---------------|
| 1 | **Plant.id** (Kindwise) | `https://plant.id/api/v3/` | Artbestimmung + Krankheitsdiagnose | API-Key (Header) | 100 IDs/Tag | ~29 €/Mo (5.000 IDs), ~99 €/Mo (20.000 IDs) |
| 2 | **PlantNet** (Fallback) | `https://my-api.plantnet.org/v2/` | Artbestimmung (keine Krankheiten) | API-Key (Query) | 500 IDs/Tag | Individuell (akademisch) |

**Abgrenzung zu REQ-011:**
- REQ-011 reichert **bestehende** Stammdaten mit Textdaten an (Taxonomie, Pflegeparameter).
- REQ-029 **identifiziert unbekannte** Pflanzen anhand von Bildern und verknüpft sie mit bestehenden Stammdaten.
- Beide nutzen dasselbe Adapter-Pattern, aber unterschiedliche Interfaces (Text-Suche vs. Bild-Upload).

### 1.2 Identifikations-Workflow

```
Nutzer fotografiert Pflanze
        │
        ▼
┌─────────────────────┐
│  Bild-Upload        │──▶ Validierung (Format, Größe, EXIF-Strip)
│  (Frontend)         │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Backend Proxy      │──▶ Consent-Check (DSGVO)
│  /identify          │──▶ Rate-Limit-Check (pro User + global)
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  PlantIdAdapter     │──▶ Plant.id API v3
│  (oder Fallback)    │    POST /identification
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  IdentificationEngine│──▶ Top-N Vorschläge (Konfidenz ≥ Schwelle)
│  Mapping             │──▶ Match gegen lokale Species-Stammdaten
└─────────────────────┘
        │
        ├── Match gefunden ──▶ Species vorschlagen, CareProfile anlegen
        │
        ├── Kein Match ──▶ Species-Anlage vorschlagen (mit externen Daten)
        │
        └── Konfidenz zu niedrig ──▶ Manuelle Suche anbieten
```

### 1.3 Krankheitsdiagnose-Workflow

```
Nutzer fotografiert krankes Blatt
        │
        ▼
┌─────────────────────┐
│  Backend Proxy      │──▶ POST /diagnose
│  /diagnose          │──▶ Plant.id Health Assessment API
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  DiagnosisEngine    │──▶ Krankheiten/Schädlinge mit Konfidenz
│  Mapping            │──▶ Match gegen lokale IPM-Stammdaten (REQ-010)
└─────────────────────┘
        │
        ├── Match gefunden ──▶ Behandlungsvorschläge aus IPM anzeigen
        │
        └── Kein Match ──▶ Externe Behandlungshinweise anzeigen
```

## 2. Datenmodell-Erweiterung (ArangoDB)

### Neue Collections:

**`identification_requests` (Document Collection):**
```json
{
  "_key": "ident_20260321_abc123",
  "tenant_key": "tenant_personal_anna",
  "user_key": "user_anna",
  "adapter_key": "plant_id",
  "request_type": "identification",
  "image_hash": "sha256:a1b2c3...",
  "image_organ": "leaf",
  "status": "completed",
  "results": [
    {
      "rank": 1,
      "scientific_name": "Monstera deliciosa",
      "common_names": ["Fensterblatt", "Swiss Cheese Plant"],
      "confidence": 0.9432,
      "matched_species_key": "species_monstera_deliciosa",
      "external_id": "plantid_12345"
    },
    {
      "rank": 2,
      "scientific_name": "Monstera adansonii",
      "common_names": ["Monkey Mask"],
      "confidence": 0.0312,
      "matched_species_key": "species_monstera_adansonii",
      "external_id": "plantid_12346"
    }
  ],
  "selected_result_rank": 1,
  "health_assessment": null,
  "api_response_time_ms": 1240,
  "created_at": "2026-03-21T14:30:00Z",
  "image_deleted_at": "2026-03-21T14:30:02Z"
}
```

**`diagnosis_requests` (Document Collection):**
```json
{
  "_key": "diag_20260321_def456",
  "tenant_key": "tenant_personal_anna",
  "user_key": "user_anna",
  "adapter_key": "plant_id",
  "plant_instance_key": "plant_anna_monstera_01",
  "image_hash": "sha256:d4e5f6...",
  "status": "completed",
  "health_assessment": {
    "is_healthy": false,
    "diseases": [
      {
        "name": "Leaf spot",
        "scientific_name": "Septoria lycopersici",
        "confidence": 0.872,
        "matched_disease_key": "disease_septoria",
        "severity": "medium",
        "treatment_suggestions": [
          "Befallene Blätter entfernen",
          "Fungizid auf Kupferbasis anwenden",
          "Luftzirkulation verbessern"
        ]
      }
    ],
    "pests": []
  },
  "api_response_time_ms": 1850,
  "created_at": "2026-03-21T15:00:00Z",
  "image_deleted_at": "2026-03-21T15:00:02Z"
}
```

### Neue Edges:

```aql
// Edge Collection: identified_as (identification_requests → species)
//   Verbindet eine Identifikationsanfrage mit der ausgewählten Species
//   Felder: confidence, selected_at, auto_accepted

// Edge Collection: diagnosed_for (diagnosis_requests → plant_instances)
//   Verbindet eine Diagnose mit der betroffenen Pflanze

// Edge Collection: diagnosis_found (diagnosis_requests → pests / diseases)
//   Verbindet eine Diagnose mit den erkannten Schädlingen/Krankheiten aus REQ-010
//   Felder: confidence, severity
```

### AQL-Beispielabfragen:

**Identifikations-Historie eines Nutzers:**
```aql
FOR req IN identification_requests
  FILTER req.tenant_key == @tenant_key
     AND req.user_key == @user_key
  SORT req.created_at DESC
  LIMIT @limit
  LET selected = req.results[req.selected_result_rank - 1]
  LET species = DOCUMENT(CONCAT("species/", selected.matched_species_key))
  RETURN {
    _key: req._key,
    created_at: req.created_at,
    species_name: species.scientific_name,
    common_name: species.common_name,
    confidence: selected.confidence,
    request_type: req.request_type
  }
```

**Häufig identifizierte Arten (für Starter-Kit-Optimierung):**
```aql
FOR req IN identification_requests
  FILTER req.status == "completed"
     AND req.selected_result_rank != null
  LET selected = req.results[req.selected_result_rank - 1]
  COLLECT species_key = selected.matched_species_key WITH COUNT INTO count
  SORT count DESC
  LIMIT 20
  LET species = DOCUMENT(CONCAT("species/", species_key))
  RETURN { species_key, scientific_name: species.scientific_name, identification_count: count }
```

## 3. Technische Umsetzung (Python)

### 3.1 Plant Identification Adapter Interface

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from enum import StrEnum


class PlantOrgan(StrEnum):
    """Pflanzenteil für die Identifikation (verbessert Genauigkeit)."""
    LEAF = "leaf"
    FLOWER = "flower"
    FRUIT = "fruit"
    BARK = "bark"
    HABIT = "habit"
    AUTO = "auto"


class IdentificationSuggestion(BaseModel):
    """Ein Identifikationsvorschlag."""
    rank: int
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family: str | None = None
    genus: str | None = None
    confidence: float  # 0.0 – 1.0
    external_id: str
    image_url: str | None = None  # Referenzbild vom Dienst
    gbif_id: int | None = None
    raw_data: dict = Field(default_factory=dict)


class HealthIssue(BaseModel):
    """Eine erkannte Krankheit oder ein Schädling."""
    name: str
    scientific_name: str | None = None
    category: str  # "disease", "pest", "abiotic"
    confidence: float
    severity: str | None = None  # "low", "medium", "high"
    treatment_suggestions: list[str] = Field(default_factory=list)
    external_id: str | None = None
    raw_data: dict = Field(default_factory=dict)


class HealthAssessment(BaseModel):
    """Gesundheitsbewertung einer Pflanze."""
    is_healthy: bool
    healthy_confidence: float
    diseases: list[HealthIssue] = Field(default_factory=list)
    pests: list[HealthIssue] = Field(default_factory=list)
    abiotic: list[HealthIssue] = Field(default_factory=list)


class IdentificationResult(BaseModel):
    """Gesamtergebnis einer Identifikation."""
    suggestions: list[IdentificationSuggestion] = Field(default_factory=list)
    health_assessment: HealthAssessment | None = None
    is_plant: bool = True  # False wenn kein Pflanzenmaterial erkannt
    api_response_time_ms: int = 0


class PlantIdentificationAdapter(ABC):
    """Basis-Adapter für KI-basierte Pflanzenidentifikation.

    Separates Interface von ExternalSourceAdapter (REQ-011),
    da der Anwendungsfall grundlegend anders ist:
    - REQ-011: Text-basierte Suche und Sync bestehender Stammdaten
    - REQ-029: Bild-basierte Identifikation unbekannter Pflanzen
    """

    @property
    @abstractmethod
    def adapter_key(self) -> str:
        """Eindeutiger Schluessel des Dienstes (z.B. 'plant_id')."""

    @property
    @abstractmethod
    def supports_health_assessment(self) -> bool:
        """True wenn der Dienst Krankheitsdiagnose unterstuetzt."""

    @property
    @abstractmethod
    def rate_limit_per_day(self) -> int | None:
        """Maximale Anfragen pro Tag, None = unbegrenzt."""

    @abstractmethod
    async def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        """Identifiziert eine Pflanze anhand eines Bildes.

        Args:
            image_data: JPEG/PNG-Bilddaten (max 5 MB)
            organ: Pflanzenteil im Bild (verbessert Genauigkeit)
            max_results: Maximale Anzahl Vorschlaege
            include_health: Gesundheitsbewertung mit anfordern
            language: Sprache fuer Common Names und Behandlungsvorschlaege

        Returns:
            IdentificationResult mit sortierten Vorschlaegen
        """

    @abstractmethod
    async def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        """Diagnostiziert Krankheiten/Schaedlinge anhand eines Bildes.

        Args:
            image_data: JPEG/PNG-Bilddaten (max 5 MB)
            language: Sprache fuer Diagnose-Texte

        Returns:
            HealthAssessment mit erkannten Problemen
        """

    async def health_check(self) -> bool:
        """Prueft Erreichbarkeit der API."""
        return True
```

### 3.2 Plant.id Adapter (Prio 1)

```python
import base64
import time

import httpx
import structlog

from app.config import settings
from app.domain.interfaces.plant_identification_adapter import (
    HealthAssessment,
    HealthIssue,
    IdentificationResult,
    IdentificationSuggestion,
    PlantIdentificationAdapter,
    PlantOrgan,
)

logger = structlog.get_logger()


class PlantIdAdapter(PlantIdentificationAdapter):
    """Adapter fuer Plant.id v3 API (Kindwise).

    Dokumentation: https://plant.id/docs
    Account: https://web.plant.id
    """

    adapter_key = "plant_id"
    supports_health_assessment = True
    rate_limit_per_day = 100  # Free Tier

    def __init__(self) -> None:
        self._base_url = "https://plant.id/api/v3"
        self._api_key = settings.plant_id_api_key  # Optional, None = deaktiviert

    async def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        start = time.monotonic()

        payload: dict = {
            "images": [base64.b64encode(image_data).decode()],
            "similar_images": True,
            "language": language,
        }

        # Health Assessment optional mit anfordern
        if include_health:
            payload["health"] = "all"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/identification",
                headers={
                    "Api-Key": self._api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        elapsed_ms = int((time.monotonic() - start) * 1000)

        suggestions = []
        for i, suggestion in enumerate(
            data.get("result", {}).get("classification", {}).get("suggestions", [])[:max_results],
            start=1,
        ):
            suggestions.append(
                IdentificationSuggestion(
                    rank=i,
                    scientific_name=suggestion.get("name", ""),
                    common_names=suggestion.get("details", {}).get("common_names") or [],
                    family=suggestion.get("details", {}).get("taxonomy", {}).get("family"),
                    genus=suggestion.get("details", {}).get("taxonomy", {}).get("genus"),
                    confidence=suggestion.get("probability", 0.0),
                    external_id=str(suggestion.get("id", "")),
                    image_url=(suggestion.get("similar_images") or [{}])[0].get("url"),
                    gbif_id=suggestion.get("details", {}).get("gbif_id"),
                    raw_data=suggestion,
                )
            )

        health = None
        if include_health and "health_assessment" in data.get("result", {}):
            health = self._parse_health(data["result"]["health_assessment"])

        return IdentificationResult(
            suggestions=suggestions,
            health_assessment=health,
            is_plant=data.get("result", {}).get("is_plant", {}).get("binary", True),
            api_response_time_ms=elapsed_ms,
        )

    async def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        payload = {
            "images": [base64.b64encode(image_data).decode()],
            "language": language,
            "health": "all",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/identification",
                headers={
                    "Api-Key": self._api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        health_data = data.get("result", {}).get("health_assessment", {})
        return self._parse_health(health_data)

    def _parse_health(self, health_data: dict) -> HealthAssessment:
        diseases = []
        pests = []
        abiotic = []

        for disease in health_data.get("diseases", []):
            issue = HealthIssue(
                name=disease.get("name", ""),
                scientific_name=disease.get("details", {}).get("local_name"),
                category=disease.get("disease_details", {}).get("type", "disease"),
                confidence=disease.get("probability", 0.0),
                treatment_suggestions=disease.get("details", {}).get("treatment", {}).get("biological", [])
                    + disease.get("details", {}).get("treatment", {}).get("chemical", []),
                external_id=str(disease.get("id", "")),
                raw_data=disease,
            )
            if issue.category == "pest":
                pests.append(issue)
            elif issue.category == "abiotic":
                abiotic.append(issue)
            else:
                diseases.append(issue)

        return HealthAssessment(
            is_healthy=health_data.get("is_healthy", {}).get("binary", True),
            healthy_confidence=health_data.get("is_healthy", {}).get("probability", 1.0),
            diseases=diseases,
            pests=pests,
            abiotic=abiotic,
        )

    async def health_check(self) -> bool:
        if not self._api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self._base_url}/usage_info",
                    headers={"Api-Key": self._api_key},
                )
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
```

### 3.3 PlantNet Adapter (Fallback)

```python
class PlantNetAdapter(PlantIdentificationAdapter):
    """Adapter fuer PlantNet API v2 (Fallback).

    Dokumentation: https://my.plantnet.org/doc/openapi
    Account: https://my.plantnet.org
    Einschraenkungen: Keine Krankheitsdiagnose, nur Artbestimmung.
    Free Tier: 500 Requests/Tag (nicht-kommerziell).
    """

    adapter_key = "plantnet"
    supports_health_assessment = False
    rate_limit_per_day = 500

    def __init__(self) -> None:
        self._base_url = "https://my-api.plantnet.org/v2"
        self._api_key = settings.plantnet_api_key  # Optional

    async def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        start = time.monotonic()

        organ_param = organ.value if organ != PlantOrgan.AUTO else "auto"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/identify/all",
                params={
                    "api-key": self._api_key,
                    "include-related-images": "true",
                    "nb-results": max_results,
                    "lang": language,
                },
                files={
                    "images": ("plant.jpg", image_data, "image/jpeg"),
                },
                data={"organs": organ_param},
            )
            resp.raise_for_status()
            data = resp.json()

        elapsed_ms = int((time.monotonic() - start) * 1000)

        suggestions = []
        for i, result in enumerate(data.get("results", [])[:max_results], start=1):
            species = result.get("species", {})
            suggestions.append(
                IdentificationSuggestion(
                    rank=i,
                    scientific_name=species.get("scientificNameWithoutAuthor", ""),
                    common_names=species.get("commonNames", []),
                    family=species.get("family", {}).get("scientificNameWithoutAuthor"),
                    genus=species.get("genus", {}).get("scientificNameWithoutAuthor"),
                    confidence=result.get("score", 0.0),
                    external_id=str(species.get("gbif", {}).get("id", "")),
                    image_url=(result.get("images") or [{}])[0].get("url", {}).get("m"),
                    gbif_id=species.get("gbif", {}).get("id"),
                    raw_data=result,
                )
            )

        return IdentificationResult(
            suggestions=suggestions,
            health_assessment=None,  # PlantNet hat keine Krankheitsdiagnose
            is_plant=len(suggestions) > 0,
            api_response_time_ms=elapsed_ms,
        )

    async def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        raise NotImplementedError(
            "PlantNet unterstuetzt keine Krankheitsdiagnose. "
            "Verwende Plant.id fuer Health Assessment."
        )

    async def health_check(self) -> bool:
        return self._api_key is not None
```

### 3.4 Identification Adapter Registry

```python
from typing import ClassVar


class IdentificationAdapterRegistry:
    """Registry fuer Pflanzenidentifikations-Adapter.

    Analog zu AdapterRegistry (REQ-011), aber fuer Bild-basierte Dienste.
    """

    _adapters: ClassVar[dict[str, type[PlantIdentificationAdapter]]] = {}

    @classmethod
    def register(cls, adapter_cls: type[PlantIdentificationAdapter]) -> type[PlantIdentificationAdapter]:
        key = adapter_cls.adapter_key
        if isinstance(key, property):
            raise ValueError("adapter_key must be a class attribute, not a property")
        cls._adapters[key] = adapter_cls
        return adapter_cls

    @classmethod
    def get(cls, adapter_key: str) -> PlantIdentificationAdapter:
        adapter_cls = cls._adapters.get(adapter_key)
        if not adapter_cls:
            raise KeyError(
                f"Unknown identification adapter '{adapter_key}'. "
                f"Available: {list(cls._adapters.keys())}"
            )
        return adapter_cls()

    @classmethod
    def get_available(cls) -> list[PlantIdentificationAdapter]:
        """Gibt alle Adapter zurueck, deren API-Key konfiguriert ist."""
        available = []
        for adapter_cls in cls._adapters.values():
            instance = adapter_cls()
            if hasattr(instance, '_api_key') and instance._api_key:
                available.append(instance)
        return available

    @classmethod
    def get_preferred(cls) -> PlantIdentificationAdapter | None:
        """Gibt den ersten verfuegbaren Adapter zurueck (nach Prio)."""
        available = cls.get_available()
        return available[0] if available else None

    @classmethod
    def all_keys(cls) -> list[str]:
        return list(cls._adapters.keys())
```

### 3.5 Identification Engine

```python
import hashlib
from datetime import datetime, timezone

import structlog

from app.domain.interfaces.plant_identification_adapter import (
    HealthAssessment,
    IdentificationResult,
    PlantOrgan,
)
from app.domain.interfaces.species_repository import SpeciesRepository

logger = structlog.get_logger()

# Schwellenwerte
CONFIDENCE_AUTO_ACCEPT = 0.85   # Automatisch vorschlagen
CONFIDENCE_SHOW_RESULTS = 0.10  # Mindest-Konfidenz fuer Anzeige
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class IdentificationEngine:
    """Orchestriert die Pflanzenidentifikation und das Mapping auf lokale Stammdaten."""

    def __init__(
        self,
        species_repo: SpeciesRepository,
        identification_repo,  # IdentificationRequestRepository
    ) -> None:
        self._species_repo = species_repo
        self._identification_repo = identification_repo

    def validate_image(self, image_data: bytes) -> None:
        """Validiert Bilddaten vor dem Upload.

        Raises:
            ValueError: Bild zu gross oder ungueltig
        """
        if len(image_data) > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(
                f"Image too large: {len(image_data)} bytes "
                f"(max {MAX_IMAGE_SIZE_BYTES} bytes)"
            )

        # JPEG/PNG Magic Bytes pruefen
        if not (
            image_data[:2] == b'\xff\xd8'          # JPEG
            or image_data[:8] == b'\x89PNG\r\n\x1a\n'  # PNG
        ):
            raise ValueError("Unsupported image format. Only JPEG and PNG are accepted.")

    def compute_image_hash(self, image_data: bytes) -> str:
        """SHA-256 Hash des Bildes (fuer Deduplizierung, nicht Speicherung)."""
        return f"sha256:{hashlib.sha256(image_data).hexdigest()[:32]}"

    async def identify(
        self,
        adapter,  # PlantIdentificationAdapter
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        include_health: bool = False,
        language: str = "de",
        tenant_key: str,
        user_key: str,
    ) -> dict:
        """Identifiziert eine Pflanze und matched gegen lokale Stammdaten.

        Returns:
            Dict mit suggestions (angereichert um matched_species_key)
            und optionalem health_assessment
        """
        self.validate_image(image_data)
        image_hash = self.compute_image_hash(image_data)

        # Identifikation via externem Dienst
        result: IdentificationResult = await adapter.identify(
            image_data,
            organ=organ,
            include_health=include_health,
            language=language,
        )

        if not result.is_plant:
            return {
                "is_plant": False,
                "suggestions": [],
                "health_assessment": None,
                "message": "No plant material detected in image.",
            }

        # Match gegen lokale Species-Stammdaten
        enriched_suggestions = []
        for suggestion in result.suggestions:
            if suggestion.confidence < CONFIDENCE_SHOW_RESULTS:
                continue

            matched_species = await self._species_repo.find_by_scientific_name(
                suggestion.scientific_name
            )

            enriched_suggestions.append({
                "rank": suggestion.rank,
                "scientific_name": suggestion.scientific_name,
                "common_names": suggestion.common_names,
                "family": suggestion.family,
                "genus": suggestion.genus,
                "confidence": suggestion.confidence,
                "external_id": suggestion.external_id,
                "image_url": suggestion.image_url,
                "gbif_id": suggestion.gbif_id,
                "matched_species_key": matched_species["_key"] if matched_species else None,
                "species_in_database": matched_species is not None,
                "auto_accept": suggestion.confidence >= CONFIDENCE_AUTO_ACCEPT,
            })

        # Identifikationsanfrage protokollieren (ohne Bilddaten)
        request_doc = {
            "tenant_key": tenant_key,
            "user_key": user_key,
            "adapter_key": adapter.adapter_key,
            "request_type": "identification",
            "image_hash": image_hash,
            "image_organ": organ.value,
            "status": "completed",
            "results": enriched_suggestions,
            "selected_result_rank": None,
            "health_assessment": (
                result.health_assessment.model_dump()
                if result.health_assessment
                else None
            ),
            "api_response_time_ms": result.api_response_time_ms,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "image_deleted_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        saved = await self._identification_repo.create(request_doc)

        return {
            "request_key": saved["_key"],
            "is_plant": True,
            "suggestions": enriched_suggestions,
            "health_assessment": (
                result.health_assessment.model_dump()
                if result.health_assessment
                else None
            ),
        }

    async def diagnose(
        self,
        adapter,  # PlantIdentificationAdapter
        image_data: bytes,
        *,
        plant_instance_key: str | None = None,
        language: str = "de",
        tenant_key: str,
        user_key: str,
    ) -> dict:
        """Diagnostiziert Krankheiten/Schaedlinge und matched gegen IPM-Stammdaten.

        Returns:
            Dict mit health_assessment und optionalen IPM-Matches
        """
        self.validate_image(image_data)
        image_hash = self.compute_image_hash(image_data)

        if not adapter.supports_health_assessment:
            raise ValueError(
                f"Adapter '{adapter.adapter_key}' does not support health assessment."
            )

        health: HealthAssessment = await adapter.diagnose(
            image_data,
            language=language,
        )

        # Diagnose protokollieren
        request_doc = {
            "tenant_key": tenant_key,
            "user_key": user_key,
            "adapter_key": adapter.adapter_key,
            "plant_instance_key": plant_instance_key,
            "image_hash": image_hash,
            "status": "completed",
            "health_assessment": health.model_dump(),
            "api_response_time_ms": 0,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "image_deleted_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        saved = await self._identification_repo.create_diagnosis(request_doc)

        return {
            "request_key": saved["_key"],
            "health_assessment": health.model_dump(),
            "plant_instance_key": plant_instance_key,
        }

    async def confirm_identification(
        self,
        request_key: str,
        selected_rank: int,
        *,
        tenant_key: str,
    ) -> dict:
        """Bestaetigt eine Identifikation und verknuepft sie mit der Species.

        Wird aufgerufen, wenn der Nutzer einen Vorschlag akzeptiert.
        Gibt die matched_species_key zurueck, damit der Aufrufer
        eine PlantInstance anlegen kann.
        """
        request = await self._identification_repo.get(request_key, tenant_key)
        if not request:
            raise ValueError(f"Identification request '{request_key}' not found")

        if selected_rank < 1 or selected_rank > len(request["results"]):
            raise ValueError(f"Invalid rank {selected_rank}")

        selected = request["results"][selected_rank - 1]

        await self._identification_repo.update(
            request_key,
            {"selected_result_rank": selected_rank},
        )

        return {
            "matched_species_key": selected.get("matched_species_key"),
            "scientific_name": selected["scientific_name"],
            "common_names": selected["common_names"],
            "confidence": selected["confidence"],
            "species_in_database": selected["species_in_database"],
        }
```

### 3.6 Identification Service

```python
import structlog

from app.domain.engines.identification_engine import IdentificationEngine
from app.domain.interfaces.plant_identification_adapter import PlantOrgan

logger = structlog.get_logger()


class IdentificationService:
    """Service-Schicht fuer Pflanzenidentifikation.

    Verwaltet Adapter-Auswahl, Rate-Limiting, Consent-Check
    und orchestriert Engine-Aufrufe.
    """

    def __init__(
        self,
        engine: IdentificationEngine,
        adapter_registry,  # IdentificationAdapterRegistry
        rate_limiter,      # Redis-basiert
    ) -> None:
        self._engine = engine
        self._registry = adapter_registry
        self._rate_limiter = rate_limiter

    async def is_available(self) -> bool:
        """Prueft ob mindestens ein Identifikations-Adapter konfiguriert ist."""
        return self._registry.get_preferred() is not None

    async def identify_plant(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        include_health: bool = False,
        language: str = "de",
        tenant_key: str,
        user_key: str,
        adapter_key: str | None = None,
    ) -> dict:
        """Identifiziert eine Pflanze anhand eines Bildes.

        Args:
            image_data: JPEG/PNG (max 5 MB)
            organ: Pflanzenteil (leaf, flower, fruit, bark, habit, auto)
            include_health: Gesundheitscheck mit anfordern
            language: Sprache (de/en)
            tenant_key: Tenant des Nutzers
            user_key: Nutzer-Key
            adapter_key: Optionaler spezifischer Adapter (sonst bevorzugter)

        Returns:
            Identifikations-Ergebnis mit Vorschlaegen

        Raises:
            ValueError: Bild ungueltig oder Feature nicht verfuegbar
            RateLimitError: Tages-Limit erreicht
        """
        adapter = (
            self._registry.get(adapter_key)
            if adapter_key
            else self._registry.get_preferred()
        )

        if adapter is None:
            raise ValueError(
                "Plant identification is not configured. "
                "Set PLANT_ID_API_KEY or PLANTNET_API_KEY in environment."
            )

        # Rate-Limit pruefen (pro User pro Tag)
        await self._rate_limiter.check_and_increment(
            key=f"identify:{adapter.adapter_key}:{user_key}",
            limit=adapter.rate_limit_per_day or 1000,
            window_seconds=86400,
        )

        return await self._engine.identify(
            adapter,
            image_data,
            organ=organ,
            include_health=include_health,
            language=language,
            tenant_key=tenant_key,
            user_key=user_key,
        )

    async def diagnose_plant(
        self,
        image_data: bytes,
        *,
        plant_instance_key: str | None = None,
        language: str = "de",
        tenant_key: str,
        user_key: str,
    ) -> dict:
        """Diagnostiziert Krankheiten/Schaedlinge anhand eines Bildes."""
        adapter = self._registry.get_preferred()

        if adapter is None or not adapter.supports_health_assessment:
            raise ValueError(
                "Health assessment requires Plant.id API key. "
                "Set PLANT_ID_API_KEY in environment."
            )

        await self._rate_limiter.check_and_increment(
            key=f"diagnose:{adapter.adapter_key}:{user_key}",
            limit=adapter.rate_limit_per_day or 1000,
            window_seconds=86400,
        )

        return await self._engine.diagnose(
            adapter,
            image_data,
            plant_instance_key=plant_instance_key,
            language=language,
            tenant_key=tenant_key,
            user_key=user_key,
        )

    async def confirm_identification(
        self,
        request_key: str,
        selected_rank: int,
        *,
        tenant_key: str,
    ) -> dict:
        """Bestaetigt einen Identifikationsvorschlag."""
        return await self._engine.confirm_identification(
            request_key,
            selected_rank,
            tenant_key=tenant_key,
        )

    async def get_status(self) -> dict:
        """Status aller konfigurierten Adapter."""
        status = {}
        for key in self._registry.all_keys():
            try:
                adapter = self._registry.get(key)
                is_healthy = await adapter.health_check()
                status[key] = {
                    "configured": True,
                    "healthy": is_healthy,
                    "supports_health": adapter.supports_health_assessment,
                    "rate_limit_per_day": adapter.rate_limit_per_day,
                }
            except Exception:
                status[key] = {"configured": False, "healthy": False}
        return status
```

### 3.7 REST-API Endpunkte

```python
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from app.common.auth import get_current_user, require_consent

router = APIRouter(
    prefix="/api/v1/t/{tenant_slug}/identification",
    tags=["identification"],
)


@router.get("/status")
async def identification_status(
    service=Depends(get_identification_service),
) -> dict:
    """Status der Bilderkennungs-Dienste (verfuegbar? gesund? Rate-Limits?).

    Wird vom Frontend genutzt um die Kamera-Buttons ein/auszublenden.
    Kein Auth erforderlich — damit Onboarding pruefen kann ob Feature aktiv ist.
    """
    return await service.get_status()


@router.post("/identify")
async def identify_plant(
    tenant_slug: str,
    image: UploadFile = File(..., description="JPEG/PNG, max 5 MB"),
    organ: str = Form("auto", description="leaf, flower, fruit, bark, habit, auto"),
    include_health: bool = Form(False),
    language: str = Form("de"),
    user=Depends(get_current_user),
    consent=Depends(require_consent("plant_identification")),
    service=Depends(get_identification_service),
) -> dict:
    """Identifiziert eine Pflanze anhand eines Bildes.

    **Consent erforderlich:** `plant_identification`
    (Bild wird an externen Dienst gesendet)

    Returns:
        - suggestions: Liste der Vorschlaege (mit Konfidenz und Species-Match)
        - health_assessment: Optionale Gesundheitsbewertung
    """
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(400, "Only JPEG and PNG images are accepted")

    image_data = await image.read()

    try:
        return await service.identify_plant(
            image_data,
            organ=PlantOrgan(organ),
            include_health=include_health,
            language=language,
            tenant_key=user.tenant_key,
            user_key=user.user_key,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except RateLimitError as exc:
        raise HTTPException(429, str(exc))


@router.post("/diagnose")
async def diagnose_plant(
    tenant_slug: str,
    image: UploadFile = File(..., description="JPEG/PNG, max 5 MB"),
    plant_instance_key: str | None = Form(None),
    language: str = Form("de"),
    user=Depends(get_current_user),
    consent=Depends(require_consent("plant_identification")),
    service=Depends(get_identification_service),
) -> dict:
    """Diagnostiziert Krankheiten/Schaedlinge anhand eines Bildes.

    **Nur mit Plant.id verfuegbar** (PlantNet hat keine Health Assessment API).

    Returns:
        - health_assessment: Erkannte Krankheiten, Schaedlinge, abiotische Probleme
    """
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(400, "Only JPEG and PNG images are accepted")

    image_data = await image.read()

    try:
        return await service.diagnose_plant(
            image_data,
            plant_instance_key=plant_instance_key,
            language=language,
            tenant_key=user.tenant_key,
            user_key=user.user_key,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except RateLimitError as exc:
        raise HTTPException(429, str(exc))


@router.post("/identify/{request_key}/confirm")
async def confirm_identification(
    tenant_slug: str,
    request_key: str,
    selected_rank: int = Query(..., ge=1, le=10),
    user=Depends(get_current_user),
    service=Depends(get_identification_service),
) -> dict:
    """Bestaetigt einen Identifikationsvorschlag.

    Nach Bestaetigung kann der Frontend-Client die zurueckgegebene
    matched_species_key nutzen um eine PlantInstance anzulegen.
    """
    try:
        return await service.confirm_identification(
            request_key,
            selected_rank,
            tenant_key=user.tenant_key,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@router.get("/history")
async def identification_history(
    tenant_slug: str,
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    service=Depends(get_identification_service),
) -> list[dict]:
    """Identifikations-Historie des Nutzers (letzte N Anfragen)."""
    return await service.get_history(
        tenant_key=user.tenant_key,
        user_key=user.user_key,
        limit=limit,
    )
```

### 3.8 Konfiguration (Settings)

```python
# In app/config.py (Ergaenzung)

class Settings(BaseSettings):
    # ... bestehende Felder ...

    # REQ-029: Plant Identification (alle optional)
    plant_id_api_key: str | None = None        # Plant.id by Kindwise
    plantnet_api_key: str | None = None         # PlantNet (Fallback)

    # Schwellenwerte
    identification_confidence_auto_accept: float = 0.85
    identification_confidence_min_show: float = 0.10
    identification_max_image_size_mb: int = 5

    # Rate Limits (pro User pro Tag, 0 = Adapter-Default)
    identification_rate_limit_per_user_day: int = 0
```

**Helm Values (Ergaenzung):**

```yaml
# In helm/kamerplanter/values.yaml
backend:
  env:
    # REQ-029: Plant Identification (optional)
    # PLANT_ID_API_KEY: ""      # Plant.id — set via secret
    # PLANTNET_API_KEY: ""      # PlantNet — set via secret
    IDENTIFICATION_CONFIDENCE_AUTO_ACCEPT: "0.85"
    IDENTIFICATION_CONFIDENCE_MIN_SHOW: "0.10"
    IDENTIFICATION_MAX_IMAGE_SIZE_MB: "5"
```

## 4. Frontend-Integration

### 4.1 Identifikations-Dialog (Wiederverwendbare Komponente)

**`PlantIdentificationDialog`** — Modal mit Kamera/Upload und Ergebnis-Anzeige:

| Element | Beschreibung |
|---------|-------------|
| Kamera-Button | `navigator.mediaDevices.getUserMedia()` oder `<input type="file" accept="image/*" capture="environment">` (Mobile) |
| Datei-Upload | Drag & Drop oder Dateiauswahl (Desktop) |
| Organ-Auswahl | Optional: Chips (Blatt, Blüte, Frucht, Rinde) — Default "Auto" |
| Lade-Zustand | Skeleton + "Pflanze wird analysiert..." |
| Ergebnis-Liste | Top-3 Vorschläge als Cards mit Konfidenz-Bar, Referenzbild, Common Name |
| Auswahl-Button | "Diese Pflanze anlegen" → ruft `/confirm` + öffnet PlantInstance-Dialog |
| Manuelle Suche | Fallback-Link: "Pflanze nicht dabei? Manuell suchen" |
| Krankheitsdiagnose | Separater Tab/Toggle: "Ist meine Pflanze krank?" |
| Fehlerzustände | API nicht konfiguriert, Rate-Limit erreicht, kein Internet, kein Pflanzenmaterial erkannt |

### 4.2 Integration in bestehende Seiten

| Seite | Integration | Bedingung |
|-------|-------------|-----------|
| **Onboarding-Wizard** (REQ-020) | Neuer optionaler Schritt 0: "Pflanze fotografieren" vor Kit-Auswahl. Nur für Beginner/Intermediate. Bei Identification → direkt PlantInstance + CareProfile anlegen. | `identification_status.available == true` |
| **Stammdaten-Übersicht** (REQ-001) | FAB (Floating Action Button) "Pflanze per Foto hinzufügen" neben "Neue Pflanze" | `identification_status.available == true` |
| **PlantInstance-Detail** | Button "Per Foto identifizieren" in der Toolbar (wenn Species noch nicht gesetzt) | `identification_status.available == true` |
| **IPM-Inspektion** (REQ-010) | Button "Foto-Diagnose" im Inspektions-Dialog | `identification_status.supports_health == true` |
| **Pflege-Dashboard** (REQ-022) | Quick-Action "Pflanze krank?" mit Kamera-Shortcut | `identification_status.supports_health == true` |

### 4.3 Erfahrungsstufen-Integration (REQ-021)

| Element | Beginner | Intermediate | Expert |
|---------|----------|-------------|--------|
| Kamera-Button | Prominent (primär CTA) | Sichtbar | Sichtbar |
| Organ-Auswahl | Ausgeblendet (Auto) | Sichtbar | Sichtbar |
| Konfidenz-Werte | Ausgeblendet | Prozent | Prozent + Raw Score |
| Referenz-Bilder | Groß (Vergleich) | Mittel | Klein |
| GBIF-Link | Ausgeblendet | Ausgeblendet | Link anzeigen |
| API-Response-Rohdaten | Ausgeblendet | Ausgeblendet | Expandable JSON |
| Manuelle Fallback-Suche | Text-Link | Text-Link | Prominent |

### 4.4 i18n-Keys (Ergänzung)

```json
{
  "pages": {
    "identification": {
      "title": "Pflanze identifizieren",
      "takePhoto": "Foto aufnehmen",
      "uploadPhoto": "Foto hochladen",
      "analyzing": "Pflanze wird analysiert...",
      "results": "Ergebnisse",
      "confidence": "Übereinstimmung",
      "selectPlant": "Diese Pflanze anlegen",
      "manualSearch": "Pflanze nicht dabei? Manuell suchen",
      "notAPlant": "Es konnte kein Pflanzenmaterial im Bild erkannt werden.",
      "noResults": "Keine Übereinstimmung gefunden.",
      "rateLimitReached": "Tages-Limit für Bilderkennung erreicht. Morgen wieder verfügbar.",
      "notConfigured": "Bilderkennung ist nicht eingerichtet. Der Administrator muss einen API-Key konfigurieren.",
      "organLabel": "Was ist auf dem Foto?",
      "organLeaf": "Blatt",
      "organFlower": "Blüte",
      "organFruit": "Frucht",
      "organBark": "Rinde",
      "organHabit": "Ganze Pflanze",
      "organAuto": "Automatisch erkennen",
      "diagnoseTitle": "Pflanzen-Diagnose",
      "diagnoseButton": "Ist meine Pflanze krank?",
      "diagnoseAnalyzing": "Gesundheit wird analysiert...",
      "diagnoseHealthy": "Die Pflanze sieht gesund aus!",
      "diagnoseDiseases": "Erkannte Probleme",
      "diagnoseTreatment": "Behandlungsvorschläge",
      "diagnoseSeverity": "Schweregrad",
      "consentTitle": "Bilderkennung aktivieren",
      "consentText": "Um Pflanzen per Foto zu identifizieren, wird das Bild an den externen Dienst Plant.id gesendet. Das Bild wird dort nicht dauerhaft gespeichert. Möchten Sie diese Funktion aktivieren?",
      "consentAccept": "Aktivieren",
      "consentDecline": "Nein, danke",
      "historyTitle": "Letzte Identifikationen"
    }
  }
}
```

## 5. DSGVO-Konformität (REQ-025)

### 5.1 Consent-Anforderungen

| Consent-Zweck | Typ | Beschreibung |
|---------------|-----|-------------|
| `plant_identification` | Optional | Bilder werden an Plant.id / PlantNet gesendet. Kein Consent = Feature nicht nutzbar, App funktioniert vollständig ohne. |

**Consent-Dialog:** Wird beim ersten Zugriff auf `/identify` oder `/diagnose` angezeigt (Frontend). Revokable jederzeit über Einstellungen → Datenschutz.

### 5.2 Datenverarbeitung

| Datum | Speicherort | Aufbewahrung | Löschung |
|-------|------------|-------------|----------|
| Bilddaten | Nur im RAM während API-Call | Keine persistente Speicherung | Sofort nach API-Response |
| Image-Hash | `identification_requests` | 90 Tage | Celery Retention Task |
| API-Response (ohne Bild) | `identification_requests` | 90 Tage | Celery Retention Task |
| Ausgewählte Species | Edge `identified_as` | Lebenszeit der PlantInstance | Mit PlantInstance gelöscht |

### 5.3 Datenweitergabe an Dritte

| Empfänger | Daten | Rechtsgrundlage | Auftragsverarbeitung |
|-----------|-------|----------------|---------------------|
| Kindwise s.r.o. (Plant.id) | Bilddaten (temporär) | Einwilligung (Art. 6 Abs. 1 lit. a) | AVV erforderlich bei kommerzieller Nutzung |
| PlantNet (CIRAD/INRIA) | Bilddaten (temporär) | Einwilligung (Art. 6 Abs. 1 lit. a) | Akademische Nutzung, Terms of Use beachten |

### 5.4 EXIF-Stripping

Vor dem Senden an die API werden **alle EXIF-Metadaten entfernt**, insbesondere:
- GPS-Koordinaten
- Geräte-Informationen
- Datum/Uhrzeit der Aufnahme

```python
from PIL import Image
import io


def strip_exif(image_data: bytes) -> bytes:
    """Entfernt alle EXIF-Metadaten aus einem Bild."""
    img = Image.open(io.BytesIO(image_data))
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    buffer = io.BytesIO()
    fmt = "JPEG" if img.format == "JPEG" else "PNG"
    clean.save(buffer, format=fmt, quality=95)
    return buffer.getvalue()
```

## 6. Konfiguration & Deployment

### 6.1 Benötigte Accounts

| Dienst | Registrierung | Kosten | Erforderlich |
|--------|--------------|--------|-------------|
| **Plant.id** (Kindwise) | https://web.plant.id → Registrieren → API-Key kopieren | Free: 0 € (100/Tag), Paid: ab 29 €/Mo | Nein (optional) |
| **PlantNet** | https://my.plantnet.org → Account → API-Key generieren | Free: 0 € (500/Tag, non-commercial) | Nein (optional, Fallback) |

**Kein Account nötig = Feature deaktiviert.** Die App funktioniert vollständig ohne externe Bilderkennungs-Keys.

### 6.2 Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kamerplanter-identification
type: Opaque
stringData:
  PLANT_ID_API_KEY: "your-plant-id-api-key"     # Optional
  PLANTNET_API_KEY: "your-plantnet-api-key"      # Optional
```

### 6.3 Feature-Toggle-Logik

```
PLANT_ID_API_KEY gesetzt?
  ├── Ja → Plant.id aktiv (Artbestimmung + Krankheitsdiagnose)
  └── Nein → PLANTNET_API_KEY gesetzt?
        ├── Ja → PlantNet aktiv (nur Artbestimmung)
        └── Nein → Feature komplett deaktiviert
                   (Kamera-Buttons ausgeblendet, kein Consent nötig)
```

### 6.4 Kostenübersicht

| Szenario | Plant.id | PlantNet | Gesamt/Monat |
|----------|----------|----------|-------------|
| **Self-Hosted Single-User** (< 100 IDs/Tag) | Free | Free | **0 €** |
| **Kleine Community** (~3.000 IDs/Monat) | Free (bei <100/Tag) oder 29 € | Free | **0–29 €** |
| **Mittelgroße Instanz** (~10.000 IDs/Monat) | ~29–99 € | Free (Fallback) | **29–99 €** |
| **Große Community** (~50.000 IDs/Monat) | Individuell | — | Individuell |

## 7. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Auth gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung).

**Standardregel:** Alle Endpunkte erfordern JWT Bearer Token und Tenant-Mitgliedschaft.

| Endpoint | Auth | Consent | Rate-Limit |
|----------|------|---------|------------|
| `GET /status` | Keine (public) | Nein | — |
| `POST /identify` | JWT + Tenant | `plant_identification` | Pro User/Tag |
| `POST /diagnose` | JWT + Tenant | `plant_identification` | Pro User/Tag |
| `POST /identify/{key}/confirm` | JWT + Tenant | Nein | — |
| `GET /history` | JWT + Tenant | Nein | — |

**Rate-Limiting:**

| Scope | Limit | Fenster |
|-------|-------|---------|
| Pro User (identify + diagnose) | Adapter-Default (100/Tag Plant.id, 500/Tag PlantNet) | 24 Stunden (rolling) |
| Global (alle User einer Instanz) | Adapter-Default | 24 Stunden |
| Burst | 5 Requests | 10 Sekunden |

## 8. Abhängigkeiten

**Benötigt:**
- **REQ-001** v5.0 (Stammdatenverwaltung) — Species-Collection für Matching
- **REQ-011** v1.0 (Adapter-Pattern) — Architektur-Vorbild, AdapterRegistry-Pattern
- **REQ-020** v1.6 (Onboarding-Wizard) — Integration als optionaler Schritt 0
- **REQ-024** v1.3 (Mandantenverwaltung) — Tenant-Scoping aller Requests
- **REQ-025** (Datenschutz) — Consent-Mechanismus für Bildübertragung

**Optional (Synergie):**
- **REQ-010** v1.0 (IPM) — Krankheits/Schädlings-Matching bei Diagnose
- **REQ-021** v1.0 (Erfahrungsstufen) — UI-Anpassung pro Level
- **REQ-022** v2.4 (Pflegeerinnerungen) — CareProfile-Anlage nach Identifikation

**Systemabhängigkeiten:**
- ArangoDB (Persistenz der Identification/Diagnosis Requests)
- Redis (Rate-Limiting via Redis-Counter)
- httpx (Async HTTP-Client für externe APIs)
- Pillow (EXIF-Stripping)

**Externe Abhängigkeiten (alle optional):**
- Plant.id API v3 (API-Key, https://web.plant.id)
- PlantNet API v2 (API-Key, https://my.plantnet.org)
- Netzwerkzugang zu externen APIs

**Wird benötigt von:**
- Keine bestehende REQ hängt von REQ-029 ab (vollständig optional)

## 9. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Adapter-Interface:** `PlantIdentificationAdapter`-Interface mit `identify()` und `diagnose()` implementiert
- [ ] **Plant.id Adapter:** Funktionsfähiger Adapter für Plant.id v3 API (Artbestimmung + Krankheitsdiagnose)
- [ ] **PlantNet Adapter:** Funktionsfähiger Fallback-Adapter (nur Artbestimmung)
- [ ] **Adapter-Registry:** Neue Dienste durch Registrierung anbindbar, ohne bestehenden Code zu ändern
- [ ] **Species-Matching:** Identifikations-Ergebnisse werden gegen lokale Species-Stammdaten gematcht
- [ ] **IPM-Matching:** Diagnose-Ergebnisse werden gegen lokale Pests/Diseases gematcht (REQ-010)
- [ ] **EXIF-Stripping:** Alle Metadaten werden vor dem API-Call entfernt
- [ ] **Consent-Check:** Erst nach expliziter Einwilligung (`plant_identification`) nutzbar
- [ ] **Rate-Limiting:** Pro User und global, Redis-basiert
- [ ] **Graceful Degradation:** Ohne API-Key sind alle Kamera-Buttons ausgeblendet, App funktioniert vollständig
- [ ] **Identifikations-Dialog:** Wiederverwendbare MUI-Komponente (Kamera/Upload + Ergebnis-Cards)
- [ ] **Onboarding-Integration:** Optionaler Schritt 0 im Wizard (REQ-020) wenn Feature verfügbar
- [ ] **Erfahrungsstufen:** UI-Anpassung gemäß REQ-021 (Beginner: kein Organ-Selector; Expert: Raw-Daten)
- [ ] **i18n:** Alle Texte in DE und EN
- [ ] **REST-Endpunkte:** `/identify`, `/diagnose`, `/confirm`, `/history`, `/status`
- [ ] **Keine Bild-Persistenz:** Bilddaten werden nicht dauerhaft gespeichert (nur Hash + Ergebnis)
- [ ] **Testabdeckung:** Unit-Tests für Adapter (gemockte API-Responses), Engine und Service

### Testszenarien:

**Szenario 1: Erfolgreiche Identifikation — Species im System**
```
GIVEN: Species "Monstera deliciosa" existiert in den Stammdaten
  AND: Plant.id API-Key ist konfiguriert
  AND: Nutzer hat Consent "plant_identification" erteilt
WHEN: Nutzer laed ein Foto einer Monstera hoch
THEN:
  - Plant.id liefert "Monstera deliciosa" mit Konfidenz 0.94
  - System matched gegen lokale Species (species_in_database = true)
  - Ergebnis-Card zeigt: Name, Konfidenz-Bar, Referenzbild
  - Button "Diese Pflanze anlegen" fuehrt zu PlantInstance-Dialog mit vorausgefuellter Species
```

**Szenario 2: Identifikation — Species NICHT im System**
```
GIVEN: Species "Alocasia zebrina" existiert NICHT in den Stammdaten
WHEN: Nutzer laed ein Foto einer Alocasia hoch
THEN:
  - Plant.id liefert "Alocasia zebrina" mit Konfidenz 0.87
  - matched_species_key = null, species_in_database = false
  - Ergebnis-Card zeigt: Name + Hinweis "Diese Art ist noch nicht im System"
  - Button "Art hinzufuegen und Pflanze anlegen"
    → Erstellt Species aus Plant.id-Daten (Name, Familie, Gattung)
    → Danach PlantInstance anlegen
```

**Szenario 3: Niedrige Konfidenz — Manuelle Suche**
```
GIVEN: Nutzer laed ein unscharfes Foto hoch
WHEN: Plant.id liefert Top-Ergebnis mit Konfidenz 0.35
THEN:
  - Alle Vorschlaege werden angezeigt (Konfidenz >= 0.10)
  - Keiner ist als "auto_accept" markiert
  - Prominenter Hinweis: "Die Erkennung ist unsicher. Bitte pruefen Sie die Vorschlaege."
  - Link "Manuell suchen" fuehrt zur Species-Suche
```

**Szenario 4: Kein Pflanzenmaterial erkannt**
```
GIVEN: Nutzer laed ein Foto eines Steins hoch
WHEN: Plant.id liefert is_plant = false
THEN:
  - Meldung: "Es konnte kein Pflanzenmaterial im Bild erkannt werden."
  - Button "Neues Foto aufnehmen" und "Manuell suchen"
```

**Szenario 5: Feature nicht konfiguriert**
```
GIVEN: Weder PLANT_ID_API_KEY noch PLANTNET_API_KEY sind gesetzt
WHEN: Frontend ruft GET /status auf
THEN:
  - Response: { "plant_id": { "configured": false }, "plantnet": { "configured": false } }
  - Alle Kamera-Buttons und "Per Foto identifizieren"-Links sind ausgeblendet
  - App funktioniert vollstaendig ohne Einschraenkung
```

**Szenario 6: Rate-Limit erreicht**
```
GIVEN: Nutzer hat heute bereits 100 Identifikationen durchgefuehrt (Plant.id Free Tier)
WHEN: Nutzer startet eine weitere Identifikation
THEN:
  - HTTP 429: "Daily identification limit reached"
  - UI zeigt: "Tages-Limit fuer Bilderkennung erreicht. Morgen wieder verfuegbar."
  - PlantNet-Fallback wird automatisch versucht (falls konfiguriert)
```

**Szenario 7: Krankheitsdiagnose mit IPM-Match**
```
GIVEN: Disease "Echter Mehltau" existiert in IPM-Stammdaten (REQ-010)
  AND: Nutzer hat PlantInstance "monstera_01"
WHEN: Nutzer laed Foto eines befallenen Blatts hoch mit plant_instance_key
THEN:
  - Plant.id Health Assessment liefert "Powdery Mildew" mit Konfidenz 0.87
  - System matched gegen lokale Disease "Echter Mehltau"
  - Behandlungsvorschlaege aus IPM-Stammdaten werden angezeigt
  - Diagnose wird als diagnosis_request gespeichert (ohne Bild)
```

**Szenario 8: EXIF-Datenschutz**
```
GIVEN: Foto enthaelt GPS-Koordinaten und Geraete-Info in EXIF
WHEN: Foto wird zur Identifikation hochgeladen
THEN:
  - EXIF-Daten werden vor dem API-Call vollstaendig entfernt
  - Nur bereinigte Pixeldaten werden an Plant.id gesendet
  - Kein GPS, kein Kameramodell, kein Aufnahmedatum wird uebertragen
```

**Szenario 9: Onboarding mit Foto-Identifikation**
```
GIVEN: Feature ist konfiguriert, Nutzer startet Onboarding-Wizard (REQ-020)
WHEN: Wizard zeigt optionalen Schritt 0 "Pflanze fotografieren"
THEN:
  - Nutzer kann Foto aufnehmen oder ueberspringen
  - Bei Foto: Identifikation → Ergebnis-Auswahl → PlantInstance wird im Wizard-Flow angelegt
  - Bei Ueberspringen: Normaler Wizard-Flow (Kit-Auswahl etc.)
  - Schritt 0 erscheint nur wenn identification_status.available == true
```

**Szenario 10: Consent-Widerruf**
```
GIVEN: Nutzer hat Consent "plant_identification" erteilt und 15 Identifikationen durchgefuehrt
WHEN: Nutzer widerruft Consent in Einstellungen → Datenschutz
THEN:
  - Alle Kamera-Buttons werden ausgeblendet
  - Identification History bleibt (keine Bilddaten gespeichert)
  - Erneuter Versuch /identify liefert HTTP 403 + Consent-Hinweis
  - Nutzer kann Consent jederzeit erneut erteilen
```

---

**Hinweise für RAG-Integration:**
- Keywords: Bilderkennung, Pflanzenidentifikation, Plant.id, PlantNet, Kamera, Foto, Artbestimmung, Krankheitsdiagnose, Health Assessment
- Fachbegriffe: EXIF-Stripping, Confidence Score, Species-Matching, Rate-Limiting, Consent, Adapter-Pattern
- Verknüpfung: Erweitert REQ-020 (Onboarding), nutzt REQ-011 (Adapter-Pattern), synergiert mit REQ-010 (IPM) und REQ-022 (Pflege)
