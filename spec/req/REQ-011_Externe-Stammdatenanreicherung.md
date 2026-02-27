# Spezifikation: REQ-011 - Externe Stammdatenanreicherung

```yaml
ID: REQ-011
Titel: Externe Stammdatenanreicherung via Drittanbieter-APIs
Kategorie: Stammdaten
Fokus: Backend
Technologie: Python, Celery, ArangoDB, REST-APIs
Status: Entwurf
Version: 1.0
```

## 1. Business Case

**User Story:** "Als Systemadministrator möchte ich Stammdaten automatisch aus externen botanischen Datenbanken anreichern, damit Pflanzeninformationen stets aktuell und vollständig sind, ohne jede Spezies manuell pflegen zu müssen."

**Beschreibung:**
Das System synchronisiert Pflanzenstammdaten periodisch mit externen APIs und reichert die lokale Wissensbasis an. Dabei gilt ein **Adapter-Pattern**, das neue Quellen modular anbindbar macht, sowie eine klare Priorisierung bei Datenkonflikten.

**Grundprinzipien:**

- **Lokale Hoheit:** Manuell eingegebene oder bestätigte Daten haben Vorrang vor externen Quellen
- **Datenprovenienz:** Jedes Feld trägt eine Herkunftsangabe (Quelle, Zeitstempel, Konfidenz)
- **Graceful Degradation:** Ausfall einer externen Quelle darf bestehende Daten nicht beeinträchtigen
- **Rate-Limiting:** Einhaltung der API-Limits aller Drittanbieter
- **Idempotenz:** Wiederholte Synchronisationen erzeugen identische Ergebnisse

### 1.1 Externe Quellen

| Prio | Quelle | Basis-URL | Datentyp | Lizenz | Rate-Limit |
|------|--------|-----------|----------|--------|------------|
| 1 | **Perenual** | `https://perenual.com/api/v2/` | Pflegedaten (Bewässerung, Licht, pH, Temperatur) | Freemium | 100 req/Tag (Free) |
| 2 | **OpenFarm** | `https://openfarm.cc/api/v1/` | Growing Guides, Companion Planting | CC-BY-4.0 | Kein hartes Limit |
| 3 | **GBIF** | `https://api.gbif.org/v1/` | Taxonomie, wissenschaftliche Namen, Synonyme | Frei | Kein Auth nötig |
| 4 | **Trefle** | `https://trefle.io/api/v1/` | Botanische Merkmale, Wuchshöhe, Temperaturbereich | Open Source | 120 req/Min |
| 5 | **Otreeba** | `https://api.otreeba.com/` | Cannabis-Sorten, Genetik, Effekte | Frei | Kein Auth nötig |

**Zukünftig vorgesehen (API noch nicht aktiv):**

| Quelle | Status | Datentyp |
|--------|--------|----------|
| **Seed Radar** | API angekündigt | Cannabis-Sorten (Community-Fork von SeedFinder.eu) |

### 1.2 Daten-Mapping auf Stammdaten

Die externen Quellen reichern die bestehenden Stammdaten-Entitäten aus REQ-001 an:

| Externes Feld | Ziel-Entität | Ziel-Feld | Primärquelle | Fallback |
|---------------|-------------|-----------|-------------|----------|
| Wissenschaftlicher Name | `Species` | `scientific_name` | GBIF | Trefle |
| Synonym-Namen | `Species` | `synonyms` | GBIF | — |
| Taxonomische Klassifikation | `Species`, `BotanicalFamily` | `family`, `genus` | GBIF | Trefle |
| Hardiness Zones | `Species` | `hardiness_zones` | Perenual | Trefle |
| Bewässerungsbedarf | `GrowthPhase` | `watering_frequency` | Perenual | OpenFarm |
| Lichtbedarf (PPFD) | `GrowthPhase` | `light_requirements_ppfd` | Perenual | OpenFarm |
| Temperaturbereich | `GrowthPhase` | `temperature_tolerance_range` | Perenual | Trefle |
| pH-Bereich | `GrowthPhase` | `ph_range` | Perenual | OpenFarm |
| Wuchshöhe | `Species` | `max_height_cm` | Trefle | Perenual |
| Companion Planting | Edge `COMPATIBLE_WITH` | `compatibility_score` | OpenFarm | — |
| Blütezeit | `LifecycleConfig` | `flowering_period_days` | Perenual | Trefle |
| Cannabis-Genetik | `Cultivar` | `genetic_lineage` | Otreeba | — |
| Cannabis-Blütezeit | `Cultivar` | `flowering_time_days` | Otreeba | — |
| Cannabis-Typ | `Cultivar` | `strain_type` | Otreeba | — |

## 2. Datenmodell-Erweiterung (ArangoDB)

### Neue Collections:

**`external_sources` (Document Collection):**
```json
{
  "_key": "perenual",
  "name": "Perenual",
  "base_url": "https://perenual.com/api/v2/",
  "auth_type": "api_key",
  "rate_limit_per_day": 100,
  "rate_limit_per_minute": null,
  "is_active": true,
  "priority": 1,
  "last_sync_at": "2026-02-26T03:00:00Z",
  "last_sync_status": "success",
  "total_records_synced": 4230
}
```

**`external_mappings` (Document Collection):**
```json
{
  "_key": "species_12345_perenual_678",
  "internal_collection": "species",
  "internal_key": "12345",
  "source_key": "perenual",
  "external_id": "678",
  "field_mappings": {
    "hardiness_zones": {
      "external_value": ["7a", "7b", "8a"],
      "mapped_at": "2026-02-26T03:15:00Z",
      "confidence": 0.95,
      "accepted": true
    },
    "max_height_cm": {
      "external_value": 180,
      "mapped_at": "2026-02-26T03:15:00Z",
      "confidence": 0.80,
      "accepted": false
    }
  },
  "last_checked_at": "2026-02-26T03:15:00Z",
  "checksum": "sha256:abc123..."
}
```

**`sync_runs` (Document Collection):**
```json
{
  "_key": "run_20260226_030000_perenual",
  "source_key": "perenual",
  "started_at": "2026-02-26T03:00:00Z",
  "finished_at": "2026-02-26T03:18:42Z",
  "status": "success",
  "records_fetched": 150,
  "records_created": 12,
  "records_updated": 38,
  "records_skipped": 100,
  "records_failed": 0,
  "errors": [],
  "triggered_by": "celery_schedule"
}
```

### Neue Edges:

```
(species)-[:ENRICHED_BY {fields: [...], last_sync: datetime}]->(external_sources)
(cultivar)-[:ENRICHED_BY {fields: [...], last_sync: datetime}]->(external_sources)
```

### AQL-Beispielabfragen:

**Stammdaten mit Provenienz laden:**
```aql
FOR s IN species
  FILTER s.scientific_name == @scientific_name
  LET enrichments = (
    FOR em IN external_mappings
      FILTER em.internal_collection == "species"
         AND em.internal_key == s._key
      FOR src IN external_sources
        FILTER src._key == em.source_key
      RETURN {
        source: src.name,
        fields: em.field_mappings,
        last_checked: em.last_checked_at
      }
  )
  RETURN MERGE(s, { _enrichments: enrichments })
```

**Nicht-angereicherte Spezies ermitteln (Sync-Kandidaten):**
```aql
FOR s IN species
  LET mapping_count = LENGTH(
    FOR em IN external_mappings
      FILTER em.internal_collection == "species"
         AND em.internal_key == s._key
      RETURN 1
  )
  FILTER mapping_count == 0
  RETURN { _key: s._key, scientific_name: s.scientific_name }
```

**Sync-Historie einer Quelle:**
```aql
FOR run IN sync_runs
  FILTER run.source_key == @source_key
  SORT run.started_at DESC
  LIMIT 10
  RETURN run
```

## 3. Technische Umsetzung (Python)

### 3.1 Adapter-Interface

```python
from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field


class ExternalSpeciesData(BaseModel):
    """Normalisierte Pflanzendaten aus externer Quelle."""

    external_id: str
    scientific_name: str | None = None
    common_names: list[str] = Field(default_factory=list)
    family: str | None = None
    genus: str | None = None
    hardiness_zones: list[str] = Field(default_factory=list)
    max_height_cm: float | None = None
    temperature_min_c: float | None = None
    temperature_max_c: float | None = None
    light_requirements_ppfd: int | None = None
    watering_frequency: str | None = None
    ph_min: float | None = None
    ph_max: float | None = None
    flowering_period_days: int | None = None
    companions: list[str] = Field(default_factory=list)
    incompatibles: list[str] = Field(default_factory=list)
    raw_data: dict = Field(default_factory=dict)


class ExternalCultivarData(BaseModel):
    """Normalisierte Sortendaten aus externer Quelle."""

    external_id: str
    name: str
    species_scientific_name: str | None = None
    breeder: str | None = None
    genetic_lineage: str | None = None
    strain_type: str | None = None
    flowering_time_days: int | None = None
    traits: list[str] = Field(default_factory=list)
    raw_data: dict = Field(default_factory=dict)


class SyncResult(BaseModel):
    """Ergebnis eines Sync-Laufs."""

    source_key: str
    started_at: datetime
    finished_at: datetime | None = None
    records_fetched: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_failed: int = 0
    errors: list[str] = Field(default_factory=list)


class ExternalSourceAdapter(ABC):
    """Basis-Adapter für externe Pflanzen-Datenquellen."""

    @property
    @abstractmethod
    def source_key(self) -> str:
        """Eindeutiger Schlüssel der Quelle (z.B. 'perenual')."""

    @property
    @abstractmethod
    def rate_limit_per_minute(self) -> int | None:
        """Maximale Anfragen pro Minute, None = unbegrenzt."""

    @abstractmethod
    async def search_species(
        self, query: str
    ) -> list[ExternalSpeciesData]:
        """Sucht Pflanzen anhand Name (wissenschaftlich oder common)."""

    @abstractmethod
    async def get_species_by_id(
        self, external_id: str
    ) -> ExternalSpeciesData | None:
        """Lädt Detail-Daten einer Pflanze per externer ID."""

    @abstractmethod
    async def get_species_list(
        self, page: int = 1, per_page: int = 30
    ) -> tuple[list[ExternalSpeciesData], int]:
        """Paginierte Liste aller Pflanzen. Returns: (data, total_count)."""

    async def get_cultivars(
        self, species_external_id: str
    ) -> list[ExternalCultivarData]:
        """Optional: Sorten einer Spezies laden."""
        return []

    async def health_check(self) -> bool:
        """Prüft Erreichbarkeit der API."""
        return True
```

### 3.2 Adapter-Implementierungen

**Perenual-Adapter (Prio 1):**
```python
import httpx
from app.config import settings


class PerenualAdapter(ExternalSourceAdapter):
    """Adapter für die Perenual Plant API (v2)."""

    source_key = "perenual"
    rate_limit_per_minute = None  # Tages-Limit: 100 (Free)

    def __init__(self) -> None:
        self._base_url = "https://perenual.com/api/v2"
        self._api_key = settings.perenual_api_key

    async def search_species(
        self, query: str
    ) -> list[ExternalSpeciesData]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/species-list",
                params={"key": self._api_key, "q": query},
            )
            resp.raise_for_status()
            data = resp.json()
            return [self._map_species(item) for item in data.get("data", [])]

    async def get_species_by_id(
        self, external_id: str
    ) -> ExternalSpeciesData | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/species/details/{external_id}",
                params={"key": self._api_key},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return self._map_species(resp.json())

    async def get_species_list(
        self, page: int = 1, per_page: int = 30
    ) -> tuple[list[ExternalSpeciesData], int]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/species-list",
                params={"key": self._api_key, "page": page},
            )
            resp.raise_for_status()
            data = resp.json()
            species = [self._map_species(item) for item in data.get("data", [])]
            total = data.get("total", 0)
            return species, total

    def _map_species(self, raw: dict) -> ExternalSpeciesData:
        return ExternalSpeciesData(
            external_id=str(raw.get("id", "")),
            scientific_name=raw.get("scientific_name"),
            common_names=[n for n in [raw.get("common_name")] if n],
            family=raw.get("family"),
            hardiness_zones=self._parse_hardiness(raw),
            watering_frequency=raw.get("watering"),
            light_requirements_ppfd=self._map_sunlight(raw.get("sunlight")),
            ph_min=raw.get("soil_ph_min"),
            ph_max=raw.get("soil_ph_max"),
            flowering_period_days=raw.get("flowering_season_days"),
            raw_data=raw,
        )

    @staticmethod
    def _parse_hardiness(raw: dict) -> list[str]:
        hardiness = raw.get("hardiness", {})
        if not hardiness:
            return []
        h_min = hardiness.get("min", "")
        h_max = hardiness.get("max", "")
        return [z for z in [h_min, h_max] if z]

    @staticmethod
    def _map_sunlight(sunlight: list[str] | None) -> int | None:
        mapping = {
            "full_shade": 100,
            "part_shade": 200,
            "sun-part_shade": 400,
            "full_sun": 600,
        }
        if not sunlight:
            return None
        return mapping.get(sunlight[0])
```

**GBIF-Adapter (Prio 3 — Taxonomie):**
```python
class GBIFAdapter(ExternalSourceAdapter):
    """Adapter für die GBIF Species API (Taxonomie-Normalisierung)."""

    source_key = "gbif"
    rate_limit_per_minute = None

    def __init__(self) -> None:
        self._base_url = "https://api.gbif.org/v1"

    async def search_species(
        self, query: str
    ) -> list[ExternalSpeciesData]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/species/search",
                params={"q": query, "rank": "SPECIES", "limit": 20},
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return [self._map_species(r) for r in results]

    async def get_species_by_id(
        self, external_id: str
    ) -> ExternalSpeciesData | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self._base_url}/species/{external_id}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return self._map_species(resp.json())

    async def get_species_list(
        self, page: int = 1, per_page: int = 30
    ) -> tuple[list[ExternalSpeciesData], int]:
        offset = (page - 1) * per_page
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/species",
                params={"limit": per_page, "offset": offset},
            )
            resp.raise_for_status()
            data = resp.json()
            species = [self._map_species(r) for r in data.get("results", [])]
            return species, data.get("count", 0)

    async def resolve_synonyms(self, scientific_name: str) -> list[str]:
        """GBIF-spezifisch: Synonyme eines Namens auflösen."""
        async with httpx.AsyncClient() as client:
            match_resp = await client.get(
                f"{self._base_url}/species/match",
                params={"name": scientific_name, "strict": True},
            )
            match_resp.raise_for_status()
            match = match_resp.json()
            usage_key = match.get("usageKey")
            if not usage_key:
                return []

            syn_resp = await client.get(
                f"{self._base_url}/species/{usage_key}/synonyms"
            )
            syn_resp.raise_for_status()
            return [
                s.get("scientificName", "")
                for s in syn_resp.json().get("results", [])
            ]

    def _map_species(self, raw: dict) -> ExternalSpeciesData:
        return ExternalSpeciesData(
            external_id=str(raw.get("key", raw.get("usageKey", ""))),
            scientific_name=raw.get("scientificName")
            or raw.get("canonicalName"),
            family=raw.get("family"),
            genus=raw.get("genus"),
            raw_data=raw,
        )
```

### 3.3 Adapter-Registry

```python
from typing import ClassVar


class AdapterRegistry:
    """Registry für externe Datenquellen-Adapter."""

    _adapters: ClassVar[dict[str, type[ExternalSourceAdapter]]] = {}

    @classmethod
    def register(cls, adapter_cls: type[ExternalSourceAdapter]) -> type[ExternalSourceAdapter]:
        """Dekorator zum Registrieren eines Adapters."""
        key = adapter_cls.source_key
        if isinstance(key, property):
            raise ValueError("source_key must be a class attribute, not a property")
        cls._adapters[key] = adapter_cls
        return adapter_cls

    @classmethod
    def get(cls, source_key: str) -> ExternalSourceAdapter:
        """Instanziiert einen Adapter anhand des Source-Keys."""
        adapter_cls = cls._adapters.get(source_key)
        if not adapter_cls:
            raise KeyError(
                f"Unknown source '{source_key}'. "
                f"Available: {list(cls._adapters.keys())}"
            )
        return adapter_cls()

    @classmethod
    def all_keys(cls) -> list[str]:
        return list(cls._adapters.keys())
```

### 3.4 Sync-Engine

```python
import hashlib
import json
from datetime import datetime, timezone

import structlog

from app.repositories.external_mapping_repository import ExternalMappingRepository
from app.repositories.species_repository import SpeciesRepository
from app.repositories.sync_run_repository import SyncRunRepository

logger = structlog.get_logger()


class EnrichmentEngine:
    """Orchestriert die Stammdaten-Anreicherung aus externen Quellen."""

    def __init__(
        self,
        species_repo: SpeciesRepository,
        mapping_repo: ExternalMappingRepository,
        sync_run_repo: SyncRunRepository,
    ) -> None:
        self._species_repo = species_repo
        self._mapping_repo = mapping_repo
        self._sync_run_repo = sync_run_repo

    async def sync_source(
        self,
        adapter: ExternalSourceAdapter,
        *,
        full_sync: bool = False,
    ) -> SyncResult:
        """
        Synchronisiert eine externe Quelle mit den lokalen Stammdaten.

        Args:
            adapter: Der Quell-Adapter
            full_sync: True = alle Einträge, False = nur fehlende Mappings
        """
        result = SyncResult(
            source_key=adapter.source_key,
            started_at=datetime.now(tz=timezone.utc),
        )

        try:
            if full_sync:
                await self._full_sync(adapter, result)
            else:
                await self._incremental_sync(adapter, result)
        except Exception as exc:
            result.errors.append(str(exc))
            logger.error(
                "sync_failed",
                source=adapter.source_key,
                error=str(exc),
            )

        result.finished_at = datetime.now(tz=timezone.utc)
        await self._sync_run_repo.save(result)
        return result

    async def _incremental_sync(
        self,
        adapter: ExternalSourceAdapter,
        result: SyncResult,
    ) -> None:
        """Synchronisiert nur Spezies ohne bestehendes Mapping."""
        unmapped = await self._mapping_repo.find_unmapped_species(
            adapter.source_key
        )

        for species in unmapped:
            try:
                matches = await adapter.search_species(
                    species["scientific_name"]
                )
                if not matches:
                    result.records_skipped += 1
                    continue

                result.records_fetched += 1
                best_match = matches[0]
                await self._apply_enrichment(
                    species, best_match, adapter.source_key
                )
                result.records_updated += 1

            except Exception as exc:
                result.records_failed += 1
                result.errors.append(
                    f"{species['scientific_name']}: {exc}"
                )

    async def _full_sync(
        self,
        adapter: ExternalSourceAdapter,
        result: SyncResult,
    ) -> None:
        """Synchronisiert alle verfügbaren Daten der Quelle."""
        page = 1
        while True:
            batch, total = await adapter.get_species_list(
                page=page, per_page=30
            )
            if not batch:
                break

            for ext_species in batch:
                result.records_fetched += 1
                local = await self._species_repo.find_by_scientific_name(
                    ext_species.scientific_name
                )
                if not local:
                    result.records_skipped += 1
                    continue

                checksum = self._compute_checksum(ext_species)
                existing = await self._mapping_repo.find_mapping(
                    "species", local["_key"], adapter.source_key
                )

                if existing and existing.get("checksum") == checksum:
                    result.records_skipped += 1
                    continue

                await self._apply_enrichment(
                    local, ext_species, adapter.source_key
                )
                result.records_updated += 1

            page += 1

    async def _apply_enrichment(
        self,
        local_species: dict,
        external_data: ExternalSpeciesData,
        source_key: str,
    ) -> None:
        """Wendet externe Daten auf lokale Stammdaten an (mit Konflikt-Prüfung)."""
        field_mappings = {}
        enrichable_fields = [
            "hardiness_zones",
            "max_height_cm",
            "temperature_min_c",
            "temperature_max_c",
            "light_requirements_ppfd",
            "watering_frequency",
            "ph_min",
            "ph_max",
            "flowering_period_days",
        ]

        for field in enrichable_fields:
            ext_value = getattr(external_data, field, None)
            if ext_value is None:
                continue

            local_value = local_species.get(field)
            auto_accept = local_value is None  # Nur leere Felder automatisch

            field_mappings[field] = {
                "external_value": ext_value,
                "mapped_at": datetime.now(tz=timezone.utc).isoformat(),
                "confidence": 0.9 if auto_accept else 0.7,
                "accepted": auto_accept,
            }

            if auto_accept:
                await self._species_repo.update_field(
                    local_species["_key"], field, ext_value
                )

        checksum = self._compute_checksum(external_data)
        await self._mapping_repo.upsert(
            internal_collection="species",
            internal_key=local_species["_key"],
            source_key=source_key,
            external_id=external_data.external_id,
            field_mappings=field_mappings,
            checksum=checksum,
        )

    @staticmethod
    def _compute_checksum(data: ExternalSpeciesData) -> str:
        raw = json.dumps(data.model_dump(exclude={"raw_data"}), sort_keys=True)
        return f"sha256:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
```

### 3.5 Celery-Tasks

```python
from celery import shared_task

from app.services.enrichment_engine import EnrichmentEngine
from app.adapters.registry import AdapterRegistry


@shared_task(
    name="enrichment.sync_source",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    rate_limit="2/m",
)
def sync_source_task(self, source_key: str, full_sync: bool = False) -> dict:
    """Celery-Task für periodische Quell-Synchronisation."""
    import asyncio
    from app.dependencies import get_enrichment_engine

    adapter = AdapterRegistry.get(source_key)
    engine = get_enrichment_engine()

    try:
        result = asyncio.run(engine.sync_source(adapter, full_sync=full_sync))
        return result.model_dump(mode="json")
    except Exception as exc:
        self.retry(exc=exc)


@shared_task(name="enrichment.sync_all")
def sync_all_sources_task(full_sync: bool = False) -> dict:
    """Synchronisiert alle aktiven Quellen sequentiell."""
    results = {}
    for key in AdapterRegistry.all_keys():
        result = sync_source_task.delay(key, full_sync=full_sync)
        results[key] = result.id
    return results
```

### 3.6 Celery-Beat Schedule

```python
# In app/celery_config.py

CELERY_BEAT_SCHEDULE = {
    "enrich-stammdaten-daily": {
        "task": "enrichment.sync_all",
        "schedule": 86400.0,  # Täglich
        "kwargs": {"full_sync": False},
    },
    "enrich-stammdaten-weekly-full": {
        "task": "enrichment.sync_all",
        "schedule": 604800.0,  # Wöchentlich
        "kwargs": {"full_sync": True},
    },
}
```

### 3.7 REST-API Endpunkte

```python
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/api/v1/enrichment", tags=["enrichment"])


@router.get("/sources")
async def list_sources(
    source_repo=Depends(get_source_repo),
) -> list[dict]:
    """Listet alle konfigurierten externen Quellen."""
    return await source_repo.list_all()


@router.post("/sources/{source_key}/sync")
async def trigger_sync(
    source_key: str,
    full_sync: bool = Query(False),
) -> dict:
    """Löst manuelle Synchronisation einer Quelle aus."""
    if source_key not in AdapterRegistry.all_keys():
        raise HTTPException(404, f"Unknown source: {source_key}")

    task = sync_source_task.delay(source_key, full_sync=full_sync)
    return {"task_id": task.id, "source": source_key, "full_sync": full_sync}


@router.get("/sources/{source_key}/history")
async def sync_history(
    source_key: str,
    limit: int = Query(10, ge=1, le=100),
    sync_run_repo=Depends(get_sync_run_repo),
) -> list[dict]:
    """Zeigt Sync-Historie einer Quelle."""
    return await sync_run_repo.find_by_source(source_key, limit=limit)


@router.get("/species/{species_key}/enrichments")
async def species_enrichments(
    species_key: str,
    mapping_repo=Depends(get_mapping_repo),
) -> list[dict]:
    """Zeigt alle externen Anreicherungen einer Spezies."""
    return await mapping_repo.find_by_internal("species", species_key)


@router.post("/species/{species_key}/enrichments/{source_key}/accept")
async def accept_enrichment(
    species_key: str,
    source_key: str,
    fields: list[str],
    mapping_repo=Depends(get_mapping_repo),
    species_repo=Depends(get_species_repo),
) -> dict:
    """Übernimmt vorgeschlagene externe Werte in die Stammdaten."""
    mapping = await mapping_repo.find_mapping("species", species_key, source_key)
    if not mapping:
        raise HTTPException(404, "No mapping found")

    accepted_count = 0
    for field in fields:
        fm = mapping["field_mappings"].get(field)
        if not fm:
            continue
        await species_repo.update_field(species_key, field, fm["external_value"])
        fm["accepted"] = True
        fm["accepted_at"] = datetime.now(tz=timezone.utc).isoformat()
        accepted_count += 1

    await mapping_repo.update_field_mappings(
        mapping["_key"], mapping["field_mappings"]
    )
    return {"accepted_fields": accepted_count}


@router.post("/search")
async def search_external(
    query: str,
    source_key: str | None = Query(None),
) -> dict:
    """Sucht in externen Quellen (ohne lokalen Import)."""
    keys = [source_key] if source_key else AdapterRegistry.all_keys()
    results = {}
    for key in keys:
        adapter = AdapterRegistry.get(key)
        try:
            matches = await adapter.search_species(query)
            results[key] = [m.model_dump(exclude={"raw_data"}) for m in matches]
        except Exception as exc:
            results[key] = {"error": str(exc)}
    return results
```

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Enrichment Sources | Ja | Admin | — |
| Enrichment History | Ja | — | — |
| Species-Enrichments | Ja | Admin (Accept) | — |
| Sync-Trigger | — | Admin | — |
| External Search | Ja | — | — |

## 5. Abhängigkeiten

**Benötigt:**
- **REQ-001** (Stammdatenverwaltung) — Ziel-Entitäten (Species, Cultivar, BotanicalFamily)
- **NFR-006** (API-Fehlerbehandlung) — Einheitliche Fehlerbehandlung bei API-Ausfällen

**Systemabhängigkeiten:**
- ArangoDB (Persistenz der Mappings und Sync-Runs)
- Redis + Celery (Periodische Task-Ausführung)
- httpx (Async HTTP-Client für externe APIs)

**Wird benötigt von:**
- REQ-002 (Standortverwaltung) — Angereicherte Klimazonen für Standort-Empfehlungen
- REQ-003 (Phasensteuerung) — Externe Blütezeit- und Temperaturdaten
- REQ-004 (Düngung) — Nährstoffbedarf-Daten aus externen Quellen
- REQ-010 (IPM) — Schädlingsresistenz-Informationen

**Externe Abhängigkeiten:**
- API-Keys: Perenual (erforderlich), Trefle (erforderlich)
- Netzwerkzugang zu externen APIs

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Adapter-Interface:** Abstraktes `ExternalSourceAdapter`-Interface implementiert
- [ ] **Mindestens 3 Adapter:** Perenual, GBIF und OpenFarm Adapter funktionsfähig
- [ ] **Adapter-Registry:** Neue Quellen durch Registrierung anbindbar, ohne bestehenden Code zu ändern
- [ ] **Inkrementeller Sync:** Nur fehlende Mappings werden synchronisiert
- [ ] **Full Sync:** Komplette Neusynchronisation mit Checksum-Vergleich
- [ ] **Datenprovenienz:** Jedes angereicherte Feld hat Quelle, Zeitstempel und Konfidenz
- [ ] **Lokale Hoheit:** Manuell gepflegte Felder werden nicht automatisch überschrieben
- [ ] **Accept/Reject:** Vorgeschlagene Werte können per API akzeptiert oder abgelehnt werden
- [ ] **Celery-Schedule:** Täglicher inkrementeller + wöchentlicher Full-Sync konfiguriert
- [ ] **Rate-Limiting:** API-Limits aller Quellen werden eingehalten
- [ ] **Fehlertoleranz:** Ausfall einer Quelle bricht nicht den gesamten Sync ab
- [ ] **Sync-Historie:** Alle Sync-Läufe mit Statistiken protokolliert
- [ ] **REST-Endpunkte:** CRUD für Quellen, manuelle Sync-Auslösung, Enrichment-Ansicht
- [ ] **Health-Check:** Status aller externen Quellen per Endpunkt abrufbar
- [ ] **Testabdeckung:** Unit-Tests für alle Adapter (mit gemockten API-Responses)

### Testszenarien:

**Szenario 1: Inkrementelle Anreicherung — neues Feld**
```
GIVEN: Spezies "Solanum lycopersicum" ohne Hardiness Zones im System
WHEN: Perenual-Sync liefert hardiness_zones = ["7a", "7b", "8a"]
THEN:
  - Feld wird automatisch übernommen (accepted = true)
  - external_mappings Eintrag mit Konfidenz 0.9 erstellt
  - Species-Dokument enthält hardiness_zones
```

**Szenario 2: Lokale Hoheit — Konflikt**
```
GIVEN: Spezies "Cannabis sativa" mit manuell gesetztem max_height_cm = 250
WHEN: Trefle-Sync liefert max_height_cm = 300
THEN:
  - Feld wird NICHT automatisch überschrieben
  - external_mappings zeigt Vorschlag (accepted = false, confidence = 0.7)
  - Admin kann Wert per /accept-Endpunkt manuell übernehmen
```

**Szenario 3: Taxonomie-Normalisierung via GBIF**
```
GIVEN: Spezies mit common_name "Tomato" ohne scientific_name
WHEN: GBIF-Suche wird ausgelöst
THEN:
  - GBIF liefert scientific_name = "Solanum lycopersicum"
  - family = "Solanaceae", genus = "Solanum" werden gesetzt
  - Synonyme (z.B. "Lycopersicon esculentum") werden gespeichert
```

**Szenario 4: Companion Planting via OpenFarm**
```
GIVEN: "Daucus carota" (Karotte) und "Allium cepa" (Zwiebel) im System
WHEN: OpenFarm-Sync liefert Companion-Beziehung
THEN:
  - Edge COMPATIBLE_WITH zwischen beiden Species erstellt
  - compatibility_score und source_key gesetzt
  - Mischkultur-Empfehlung in REQ-001 Queries verfügbar
```

**Szenario 5: Cannabis-Sorten via Otreeba**
```
GIVEN: Cannabis sativa als Spezies im System
WHEN: Otreeba-Sync wird ausgeführt
THEN:
  - Cultivar-Einträge mit genetic_lineage und strain_type erstellt
  - flowering_time_days für Sortenplanung verfügbar
  - Daten mit source_key "otreeba" gekennzeichnet
```

**Szenario 6: API-Ausfall — Graceful Degradation**
```
GIVEN: Perenual API nicht erreichbar (HTTP 503)
WHEN: Täglicher Sync läuft
THEN:
  - Perenual-Sync wird als "failed" protokolliert (max 3 Retries)
  - Andere Quellen (GBIF, OpenFarm) werden unabhängig synchronisiert
  - Bestehende Stammdaten bleiben unverändert
  - Alert wird geloggt (structlog warning)
```

**Szenario 7: Checksum-basiertes Überspringen**
```
GIVEN: Species "Ocimum basilicum" hat Mapping zu Perenual mit checksum "sha256:abc123"
WHEN: Full-Sync läuft, Perenual liefert identische Daten
THEN:
  - Checksum-Vergleich ergibt Match
  - Kein Update, Record wird als "skipped" gezählt
  - last_checked_at wird aktualisiert
```

---

**Hinweise für RAG-Integration:**
- Keywords: Externe Datenquellen, API-Adapter, Stammdatenanreicherung, Datenprovenienz, Sync-Engine
- Fachbegriffe: Adapter-Pattern, Rate-Limiting, Checksum, Idempotenz, Graceful Degradation
- Verknüpfung: Erweitert REQ-001, liefert Daten für REQ-002 bis REQ-010
