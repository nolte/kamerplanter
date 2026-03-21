# Spezifikation: REQ-016 - Optionale InvenTree-Integration

```yaml
ID: REQ-016
Titel: Optionale InvenTree-Integration (Inventar- & Verbrauchsmaterialverwaltung)
Kategorie: Integration & Inventar
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery
Status: Entwurf
Version: 1.0
```

## 1. Business Case

**User Story (Inventaranbindung):** "Als Gärtner möchte ich meine Dünger, Tanks und Verbrauchsmaterialien mit meiner bestehenden InvenTree-Inventarverwaltung verknüpfen — damit ich Bestandsänderungen zentral nachvollziehen kann und doppelte Pflege entfällt."

**User Story (Verbrauchstracking):** "Als Gärtner möchte ich, dass der Verbrauch von Düngern und Reinigungsmitteln bei Düngungen, Tankbefüllungen und Wartungen automatisch an InvenTree gemeldet wird — damit mein Lagerbestand immer aktuell ist und ich rechtzeitig nachbestellen kann."

**User Story (Betriebsmittel):** "Als Gärtner möchte ich meine Ausrüstung (Pumpen, Messgeräte, Werkzeuge, Reinigungsmittel) als eigenständige Objekte verwalten und deren Standort, Zustand und InvenTree-Verknüpfung nachhalten — damit ich den Überblick über mein gesamtes Equipment behalte."

**Beschreibung:**
Das System bietet eine **optionale** Anbindung an [InvenTree](https://github.com/inventree/inventree) — ein Open-Source-Inventarverwaltungssystem (Python/Django, REST-API). Ziel ist die eindeutige Identifikation von Produkten, organisierte Verwaltung von Verbrauchsmaterialien und bidirektionale Bestandssynchronisation.

**Kernkonzepte:**

**Optionalität:**
- InvenTree ist **keine Pflichtkomponente** — alle Kernfunktionen von Kamerplanter funktionieren ohne InvenTree-Anbindung
- Die Integration wird pro Installation über eine `inventree_connections`-Konfiguration aktiviert/deaktiviert
- Fällt InvenTree aus, arbeitet Kamerplanter uneingeschränkt weiter (Graceful Degradation)

**Bidirektionaler Sync:**
- **READ (Stock-Pull):** Periodischer Import der aktuellen Bestandsmengen aus InvenTree in den lokalen Cache (`inventree_references.cached_stock`)
- **WRITE (Consumption-Push):** Automatische Rückmeldung von Verbrauchsbuchungen (Düngung, Wartung, Tankbefüllung) an InvenTree als Stock-Adjustments

**Equipment als First-Class-Entity:**
- Neue `equipment`-Collection für Betriebsmittel, die weder Dünger noch Tanks sind: Pumpen, pH-Meter, Lux-Meter, Desinfektionsmittel, Werkzeuge, Filter, Beleuchtung
- Equipment hat einen eigenen Typ (`EquipmentType`), Status-Lifecycle und Location-Zuordnung
- Optional mit InvenTree verknüpfbar für Bestands- und Seriennummern-Tracking

**Lose Kopplung:**
- Generische `inventree_references`-Link-Tabelle verbindet beliebige Kamerplanter-Entitäten (Fertilizer, Tank, Equipment) mit InvenTree-Parts
- `inventree_part_id` auf `fertilizers` und `tanks` ist ein denormalisierter Shortcut für häufige Lesezugriffe
- Immutables `stock_transactions`-Log für Audit-Trail aller Verbrauchsbuchungen

### 1.1 InvenTree-Überblick

| Eigenschaft | Wert |
|-------------|------|
| Projekt | [InvenTree](https://github.com/inventree/inventree) |
| Technologie | Python/Django, PostgreSQL |
| API | REST (v1), Token-basiert |
| API-Dokumentation | `{base_url}/api/schema/` (OpenAPI) |
| Authentifizierung | Token-Auth (`Authorization: Token <api_key>`) |
| Relevante Endpunkte | `/api/part/`, `/api/stock/`, `/api/stock/adjust/`, `/api/company/`, `/api/part/category/` |

### 1.2 Mapping Kamerplanter-Entitäten → InvenTree-Parts

| Kamerplanter-Entität | InvenTree-Konzept | Beispiel | Sync-Richtung |
|----------------------|-------------------|----------|---------------|
| `Fertilizer` | Part (purchaseable) | "BioBizz Bio-Bloom 1L" | READ + WRITE |
| `Tank` | Part (trackable, serial) | "IBC-Container 1000L #SN-042" | READ |
| `Equipment` (tool) | Part (trackable, serial) | "Bluelab pH Pen" | READ |
| `Equipment` (consumable) | Part (purchaseable) | "H2O2 3% 5L" | READ + WRITE |
| `Equipment` (sensor) | Part (trackable, serial) | "Trolmaster Hydro-X Controller" | READ |
| `Equipment` (filter) | Part (purchaseable) | "Inline-Sedimentfilter 10µm" | READ + WRITE |

### 1.3 Abgrenzung

REQ-016 deckt **nicht** ab:
- **Einkaufsplanung/PO:** Bestellungen in InvenTree anlegen (wird manuell in InvenTree erledigt)
- **Lieferantenverwaltung:** Companies/Suppliers werden ausschließlich in InvenTree gepflegt
- **Build Orders:** Kamerplanter erzeugt keine InvenTree-Build-Orders für Mischrezepte
- **Attachment-Sync:** Bilder/Dokumente werden nicht zwischen den Systemen synchronisiert
- **Multi-InvenTree:** Nur eine InvenTree-Instanz pro Kamerplanter-Installation

## 2. ArangoDB-Modellierung

### Neue Document-Collections:

**`inventree_connections` — Server-Konfiguration:**
```json
{
  "_key": "main",
  "name": "Haupt-Inventar",
  "base_url": "https://inventree.local/api/",
  "api_token_encrypted": "gAAAAA...",
  "is_active": true,
  "sync_interval_minutes": 60,
  "push_interval_minutes": 5,
  "last_health_check_at": "2026-02-26T10:00:00Z",
  "last_health_check_ok": true,
  "last_stock_sync_at": "2026-02-26T10:00:00Z",
  "last_push_at": "2026-02-26T10:03:00Z",
  "created_at": "2026-01-15T08:00:00Z",
  "updated_at": "2026-02-26T10:00:00Z"
}
```

**`equipment` — Betriebsmittel:**
```json
{
  "_key": "eq_001",
  "name": "Bluelab pH Pen",
  "equipment_type": "sensor",
  "status": "active",
  "brand": "Bluelab",
  "model": "pH Pen",
  "serial_number": "BL-PH-2024-0042",
  "purchase_date": "2025-06-15",
  "warranty_until": "2027-06-15",
  "inventree_part_id": 1247,
  "notes": "Kalibrierung alle 2 Wochen",
  "created_at": "2025-06-15T10:00:00Z",
  "updated_at": "2026-02-20T14:30:00Z"
}
```

**`inventree_references` — Generische Link-Tabelle:**
```json
{
  "_key": "ref_fert_001_part_42",
  "entity_collection": "fertilizers",
  "entity_key": "fert_001",
  "inventree_part_id": 42,
  "inventree_part_name": "BioBizz Bio-Bloom 1L",
  "inventree_ipn": "FERT-BB-001",
  "cached_stock": 12.5,
  "cached_stock_unit": "liters",
  "cached_stock_updated_at": "2026-02-26T10:00:00Z",
  "auto_deduct": true,
  "deduct_unit": "ml",
  "created_at": "2026-01-20T09:00:00Z",
  "updated_at": "2026-02-26T10:00:00Z"
}
```

**`stock_transactions` — Immutables Transaktions-Log:**
```json
{
  "_key": "txn_20260226_100500_feed_42",
  "reference_key": "ref_fert_001_part_42",
  "inventree_part_id": 42,
  "transaction_type": "remove",
  "quantity": 5.0,
  "unit": "ml",
  "reason": "FeedingEvent feed_042: CalMag 5ml/L × 1L",
  "source_event_collection": "feeding_events",
  "source_event_key": "feed_042",
  "status": "pending",
  "retry_count": 0,
  "last_error": null,
  "inventree_response": null,
  "created_at": "2026-02-26T10:05:00Z",
  "synced_at": null
}
```

### Erweiterung bestehender Collections:

**`fertilizers` + optionales InvenTree-Feld (denormalisiert):**
```json
{
  "inventree_part_id": 42
}
```

**`tanks` + optionales InvenTree-Feld (denormalisiert):**
```json
{
  "inventree_part_id": 1089
}
```

> **Hinweis:** `inventree_part_id` auf `fertilizers` und `tanks` ist ein Convenience-Shortcut. Die kanonische Verknüpfung läuft über `inventree_references` und die `has_inventree_ref`-Edge.

### Neue Edge-Collections:

```
has_inventree_ref:     fertilizers | tanks | equipment → inventree_references
has_stock_transaction: inventree_references → stock_transactions
equipment_at:          equipment → locations
```

**`has_inventree_ref` — Entität → InvenTree-Referenz:**
```json
{
  "_from": "fertilizers/fert_001",
  "_to": "inventree_references/ref_fert_001_part_42",
  "linked_at": "2026-01-20T09:00:00Z"
}
```

**`has_stock_transaction` — Referenz → Transaktions-Log:**
```json
{
  "_from": "inventree_references/ref_fert_001_part_42",
  "_to": "stock_transactions/txn_20260226_100500_feed_42",
  "created_at": "2026-02-26T10:05:00Z"
}
```

**`equipment_at` — Equipment → Location-Zuordnung:**
```json
{
  "_from": "equipment/eq_001",
  "_to": "locations/loc_zelt_1",
  "assigned_at": "2025-07-01T08:00:00Z",
  "notes": "Fest installiert am Mischtank"
}
```

### AQL-Beispielabfragen:

**Alle Dünger mit InvenTree-Bestandsinfo laden:**
```aql
FOR f IN fertilizers
  LET ref = FIRST(
    FOR r IN inventree_references
      FILTER r.entity_collection == "fertilizers"
         AND r.entity_key == f._key
      RETURN r
  )
  RETURN MERGE(f, {
    inventree: ref != null ? {
      part_id: ref.inventree_part_id,
      part_name: ref.inventree_part_name,
      ipn: ref.inventree_ipn,
      stock: ref.cached_stock,
      stock_unit: ref.cached_stock_unit,
      stock_updated_at: ref.cached_stock_updated_at,
      auto_deduct: ref.auto_deduct
    } : null
  })
```

**Offene (pending) Stock-Transaktionen für Retry:**
```aql
FOR txn IN stock_transactions
  FILTER txn.status == "pending"
     AND txn.retry_count < 3
  SORT txn.created_at ASC
  RETURN {
    _key: txn._key,
    part_id: txn.inventree_part_id,
    type: txn.transaction_type,
    quantity: txn.quantity,
    unit: txn.unit,
    reason: txn.reason,
    retry_count: txn.retry_count,
    created_at: txn.created_at
  }
```

**Equipment pro Location mit InvenTree-Status:**
```aql
FOR loc IN locations
  FILTER loc._key == @location_key
  LET equip = (
    FOR eq IN equipment
      FOR e IN equipment_at
        FILTER e._from == CONCAT("equipment/", eq._key)
           AND e._to == CONCAT("locations/", loc._key)
      LET ref = FIRST(
        FOR r IN inventree_references
          FILTER r.entity_collection == "equipment"
             AND r.entity_key == eq._key
          RETURN r
      )
      RETURN MERGE(eq, {
        assigned_at: e.assigned_at,
        inventree: ref != null ? {
          part_id: ref.inventree_part_id,
          stock: ref.cached_stock,
          auto_deduct: ref.auto_deduct
        } : null
      })
  )
  RETURN { location: loc, equipment: equip }
```

## 3. Technische Umsetzung (Python)

### 3.1 Enums & Pydantic-Modelle

**Enums:**
```python
from enum import StrEnum


class EquipmentType(StrEnum):
    """Typ des Betriebsmittels."""

    TOOL = "tool"                    # Scheren, Skalpelle, Lupen
    CONSUMABLE = "consumable"        # H2O2, Isopropanol, Neem-Öl
    SENSOR = "sensor"                # pH-Meter, EC-Meter, Lux-Meter
    LIGHTING = "lighting"            # LED-Panels, HPS, CMH
    PUMP = "pump"                    # Umwälzpumpen, Dosierperistaltik
    FILTER = "filter"                # Sedimentfilter, Aktivkohle, UV
    CONTAINER = "container"          # Töpfe, Netcups, Trays
    CLEANING_AGENT = "cleaning_agent"  # Reinigungsmittel, Enzyme
    OTHER = "other"


class EquipmentStatus(StrEnum):
    """Lebenszyklus-Status eines Equipments."""

    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    STORED = "stored"
    DEFECTIVE = "defective"
    RETIRED = "retired"


class StockTransactionType(StrEnum):
    """Art der Bestandsbuchung."""

    REMOVE = "remove"    # Verbrauch (Düngung, Wartung)
    ADD = "add"          # Manuelle Korrekturbuchung
    COUNT = "count"      # Inventur-Abgleich


class StockTransactionStatus(StrEnum):
    """Sync-Status einer Transaktion."""

    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
```

**Pydantic-Modelle:**
```python
from datetime import date, datetime
from pydantic import BaseModel, Field, HttpUrl


class InvenTreeConnection(BaseModel):
    """Server-Konfiguration für InvenTree-Anbindung."""

    name: str
    base_url: HttpUrl
    api_token: str = Field(exclude=True)  # Nie in API-Responses; AES-256-verschlüsselt gespeichert (Fernet, analog ha_token_encrypted in REQ-023)
    is_active: bool = True
    verify_ssl: bool = True  # TLS-Zertifikat des InvenTree-Servers validieren; nur bei Self-Signed auf false setzen
    sync_interval_minutes: int = Field(default=60, ge=5, le=1440)
    push_interval_minutes: int = Field(default=5, ge=1, le=60)
    last_health_check_at: datetime | None = None
    last_health_check_ok: bool | None = None
    last_stock_sync_at: datetime | None = None
    last_push_at: datetime | None = None


class Equipment(BaseModel):
    """Betriebsmittel (Pumpe, Sensor, Werkzeug, etc.)."""

    name: str
    equipment_type: EquipmentType
    status: EquipmentStatus = EquipmentStatus.ACTIVE
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    purchase_date: date | None = None
    warranty_until: date | None = None
    inventree_part_id: int | None = None
    notes: str | None = None


class InvenTreeReference(BaseModel):
    """Verknüpfung Kamerplanter-Entität ↔ InvenTree Part."""

    entity_collection: str
    entity_key: str
    inventree_part_id: int
    inventree_part_name: str | None = None
    inventree_ipn: str | None = None
    cached_stock: float | None = None
    cached_stock_unit: str | None = None
    cached_stock_updated_at: datetime | None = None
    auto_deduct: bool = False
    deduct_unit: str | None = None


class StockTransaction(BaseModel):
    """Immutables Transaktions-Log für Verbrauchsbuchungen."""

    reference_key: str
    inventree_part_id: int
    transaction_type: StockTransactionType
    quantity: float
    unit: str
    reason: str
    source_event_collection: str | None = None
    source_event_key: str | None = None
    status: StockTransactionStatus = StockTransactionStatus.PENDING
    retry_count: int = 0
    last_error: str | None = None
    inventree_response: dict | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=__import__("datetime").timezone.utc))
    synced_at: datetime | None = None
```

### 3.2 Adapter-Interface

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class InvenTreePartData(BaseModel):
    """Normalisierte Part-Daten aus InvenTree."""

    pk: int
    name: str
    ipn: str | None = None
    description: str | None = None
    category_name: str | None = None
    is_purchaseable: bool = False
    is_trackable: bool = False
    total_in_stock: float = 0.0
    stock_unit: str | None = None


class InvenTreeStockItemData(BaseModel):
    """Normalisierte Stock-Item-Daten aus InvenTree."""

    pk: int
    part_id: int
    quantity: float
    serial: str | None = None
    location_name: str | None = None
    status: int = 10  # 10 = OK in InvenTree


class StockAdjustmentResult(BaseModel):
    """Ergebnis einer Stock-Buchung."""

    success: bool
    items_affected: int = 0
    error: str | None = None


class InvenTreeCategoryData(BaseModel):
    """Normalisierte Kategorie-Daten aus InvenTree."""

    pk: int
    name: str
    parent: int | None = None
    path: str = ""
    part_count: int = 0


class InvenTreeAdapter(ABC):
    """Adapter-Interface für InvenTree-Kommunikation."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Prüft Erreichbarkeit der InvenTree-API."""

    @abstractmethod
    async def get_part(self, part_id: int) -> InvenTreePartData | None:
        """Lädt ein Part per ID."""

    @abstractmethod
    async def search_parts(
        self, query: str, *, category_id: int | None = None, limit: int = 25
    ) -> list[InvenTreePartData]:
        """Sucht Parts anhand Name/IPN/Description."""

    @abstractmethod
    async def get_stock_items(
        self, part_id: int
    ) -> list[InvenTreeStockItemData]:
        """Lädt alle Stock-Items eines Parts."""

    @abstractmethod
    async def remove_stock(
        self, items: list[dict], *, notes: str = ""
    ) -> StockAdjustmentResult:
        """Entfernt Stock (Verbrauchsbuchung). items: [{pk, quantity}]."""

    @abstractmethod
    async def add_stock(
        self, items: list[dict], *, notes: str = ""
    ) -> StockAdjustmentResult:
        """Fügt Stock hinzu (Korrekturbuchung). items: [{pk, quantity}]."""

    @abstractmethod
    async def count_stock(
        self, items: list[dict], *, notes: str = ""
    ) -> StockAdjustmentResult:
        """Inventur-Abgleich. items: [{pk, quantity}]."""

    @abstractmethod
    async def get_categories(
        self, *, parent_id: int | None = None
    ) -> list[InvenTreeCategoryData]:
        """Lädt Part-Kategorien (optional gefiltert nach Parent)."""
```

### 3.3 Adapter-Implementierung

```python
import httpx
import structlog

logger = structlog.get_logger()


class InvenTreeRestAdapter(InvenTreeAdapter):
    """REST-Implementierung des InvenTree-Adapters mit httpx (async)."""

    def __init__(self, base_url: str, api_token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json",
        }
        self._timeout = httpx.Timeout(10.0, connect=5.0)

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(
                headers=self._headers, timeout=self._timeout
            ) as client:
                resp = await client.get(f"{self._base_url}/api/")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def get_part(self, part_id: int) -> InvenTreePartData | None:
        async with httpx.AsyncClient(
            headers=self._headers, timeout=self._timeout
        ) as client:
            resp = await client.get(f"{self._base_url}/api/part/{part_id}/")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return self._map_part(resp.json())

    async def search_parts(
        self, query: str, *, category_id: int | None = None, limit: int = 25
    ) -> list[InvenTreePartData]:
        params: dict = {"search": query, "limit": limit}
        if category_id is not None:
            params["category"] = category_id
        async with httpx.AsyncClient(
            headers=self._headers, timeout=self._timeout
        ) as client:
            resp = await client.get(
                f"{self._base_url}/api/part/", params=params
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", data) if isinstance(data, dict) else data
            return [self._map_part(item) for item in results]

    async def get_stock_items(
        self, part_id: int
    ) -> list[InvenTreeStockItemData]:
        async with httpx.AsyncClient(
            headers=self._headers, timeout=self._timeout
        ) as client:
            resp = await client.get(
                f"{self._base_url}/api/stock/",
                params={"part": part_id},
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", data) if isinstance(data, dict) else data
            return [self._map_stock_item(item) for item in results]

    async def remove_stock(
        self, items: list[dict], *, notes: str = ""
    ) -> StockAdjustmentResult:
        return await self._adjust_stock("remove", items, notes=notes)

    async def add_stock(
        self, items: list[dict], *, notes: str = ""
    ) -> StockAdjustmentResult:
        return await self._adjust_stock("add", items, notes=notes)

    async def count_stock(
        self, items: list[dict], *, notes: str = ""
    ) -> StockAdjustmentResult:
        return await self._adjust_stock("count", items, notes=notes)

    async def get_categories(
        self, *, parent_id: int | None = None
    ) -> list[InvenTreeCategoryData]:
        params: dict = {}
        if parent_id is not None:
            params["parent"] = parent_id
        async with httpx.AsyncClient(
            headers=self._headers, timeout=self._timeout
        ) as client:
            resp = await client.get(
                f"{self._base_url}/api/part/category/", params=params
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", data) if isinstance(data, dict) else data
            return [self._map_category(item) for item in results]

    async def _adjust_stock(
        self, action: str, items: list[dict], *, notes: str = ""
    ) -> StockAdjustmentResult:
        payload = {"items": items, "notes": notes}
        try:
            async with httpx.AsyncClient(
                headers=self._headers, timeout=self._timeout
            ) as client:
                resp = await client.post(
                    f"{self._base_url}/api/stock/{action}/",
                    json=payload,
                )
                resp.raise_for_status()
                return StockAdjustmentResult(
                    success=True, items_affected=len(items)
                )
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "inventree_stock_adjust_failed",
                action=action,
                status=exc.response.status_code,
                detail=exc.response.text,
            )
            return StockAdjustmentResult(
                success=False, error=f"HTTP {exc.response.status_code}: {exc.response.text}"
            )

    @staticmethod
    def _map_part(raw: dict) -> InvenTreePartData:
        return InvenTreePartData(
            pk=raw["pk"],
            name=raw.get("name", ""),
            ipn=raw.get("IPN"),
            description=raw.get("description"),
            category_name=raw.get("category_detail", {}).get("name"),
            is_purchaseable=raw.get("purchaseable", False),
            is_trackable=raw.get("trackable", False),
            total_in_stock=raw.get("in_stock", 0.0),
            stock_unit=raw.get("units"),
        )

    @staticmethod
    def _map_stock_item(raw: dict) -> InvenTreeStockItemData:
        return InvenTreeStockItemData(
            pk=raw["pk"],
            part_id=raw.get("part", 0),
            quantity=raw.get("quantity", 0.0),
            serial=raw.get("serial"),
            location_name=raw.get("location_detail", {}).get("name"),
            status=raw.get("status", 10),
        )

    @staticmethod
    def _map_category(raw: dict) -> InvenTreeCategoryData:
        return InvenTreeCategoryData(
            pk=raw["pk"],
            name=raw.get("name", ""),
            parent=raw.get("parent"),
            path=raw.get("pathstring", ""),
            part_count=raw.get("part_count", 0),
        )
```

### 3.4 Sync-Engine

```python
from datetime import datetime, timezone

import structlog

from app.domain.interfaces.inventree_adapter import InvenTreeAdapter

logger = structlog.get_logger()

STOCK_DRIFT_THRESHOLD = 0.20  # 20% Abweichung → Warning


class InvenTreeSyncEngine:
    """Orchestriert bidirektionale Synchronisation mit InvenTree."""

    def __init__(
        self,
        adapter: InvenTreeAdapter,
        reference_repo,  # InvenTreeReferenceRepository
        transaction_repo,  # StockTransactionRepository
    ) -> None:
        self._adapter = adapter
        self._ref_repo = reference_repo
        self._txn_repo = transaction_repo

    async def sync_stock_levels(self) -> dict:
        """
        READ: Zieht aktuelle Bestandsmengen aus InvenTree
        und aktualisiert den lokalen Cache.
        """
        stats = {"updated": 0, "skipped": 0, "errors": 0, "drift_warnings": []}

        references = await self._ref_repo.list_all()
        for ref in references:
            try:
                part = await self._adapter.get_part(ref["inventree_part_id"])
                if part is None:
                    stats["skipped"] += 1
                    continue

                old_stock = ref.get("cached_stock")
                new_stock = part.total_in_stock

                # Drift-Detection
                if old_stock is not None and old_stock > 0:
                    drift = abs(new_stock - old_stock) / old_stock
                    if drift > STOCK_DRIFT_THRESHOLD:
                        stats["drift_warnings"].append({
                            "entity": f"{ref['entity_collection']}/{ref['entity_key']}",
                            "part_id": ref["inventree_part_id"],
                            "old_stock": old_stock,
                            "new_stock": new_stock,
                            "drift_pct": round(drift * 100, 1),
                        })
                        logger.warning(
                            "inventree_stock_drift",
                            entity=f"{ref['entity_collection']}/{ref['entity_key']}",
                            part_id=ref["inventree_part_id"],
                            old=old_stock,
                            new=new_stock,
                            drift_pct=round(drift * 100, 1),
                        )

                await self._ref_repo.update_cached_stock(
                    ref["_key"],
                    stock=new_stock,
                    unit=part.stock_unit,
                    updated_at=datetime.now(tz=timezone.utc),
                )
                stats["updated"] += 1

            except Exception as exc:
                stats["errors"] += 1
                logger.error(
                    "inventree_stock_sync_error",
                    ref_key=ref["_key"],
                    error=str(exc),
                )

        return stats

    async def push_pending_transactions(self) -> dict:
        """
        WRITE: Sendet ausstehende Verbrauchsbuchungen an InvenTree.
        Retry-Logik: max 3 Versuche mit exponentiellem Backoff.
        """
        stats = {"synced": 0, "failed": 0, "skipped": 0}

        pending = await self._txn_repo.find_pending(max_retries=3)
        for txn in pending:
            try:
                stock_items = await self._adapter.get_stock_items(
                    txn["inventree_part_id"]
                )
                if not stock_items:
                    await self._txn_repo.mark_failed(
                        txn["_key"], error="No stock items found"
                    )
                    stats["failed"] += 1
                    continue

                # Verwende erstes verfügbares Stock-Item
                item = {"pk": stock_items[0].pk, "quantity": txn["quantity"]}

                if txn["transaction_type"] == "remove":
                    result = await self._adapter.remove_stock(
                        [item], notes=txn["reason"]
                    )
                elif txn["transaction_type"] == "add":
                    result = await self._adapter.add_stock(
                        [item], notes=txn["reason"]
                    )
                else:
                    result = await self._adapter.count_stock(
                        [item], notes=txn["reason"]
                    )

                if result.success:
                    await self._txn_repo.mark_synced(
                        txn["_key"],
                        response=result.model_dump(),
                        synced_at=datetime.now(tz=timezone.utc),
                    )
                    stats["synced"] += 1
                else:
                    await self._txn_repo.increment_retry(
                        txn["_key"], error=result.error
                    )
                    stats["failed"] += 1

            except Exception as exc:
                await self._txn_repo.increment_retry(
                    txn["_key"], error=str(exc)
                )
                stats["failed"] += 1
                logger.error(
                    "inventree_push_error",
                    txn_key=txn["_key"],
                    error=str(exc),
                )

        return stats

    async def link_entity(
        self,
        entity_collection: str,
        entity_key: str,
        inventree_part_id: int,
        *,
        auto_deduct: bool = False,
        deduct_unit: str | None = None,
    ) -> dict:
        """Verknüpft eine Kamerplanter-Entität mit einem InvenTree-Part."""
        part = await self._adapter.get_part(inventree_part_id)
        if part is None:
            raise ValueError(
                f"InvenTree Part {inventree_part_id} not found"
            )

        ref = await self._ref_repo.upsert(
            entity_collection=entity_collection,
            entity_key=entity_key,
            inventree_part_id=inventree_part_id,
            inventree_part_name=part.name,
            inventree_ipn=part.ipn,
            cached_stock=part.total_in_stock,
            cached_stock_unit=part.stock_unit,
            auto_deduct=auto_deduct,
            deduct_unit=deduct_unit,
        )

        return ref
```

### 3.5 ConsumptionTracker

```python
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()


class ConsumptionTracker:
    """
    Erzeugt automatische stock_transactions bei Verbrauchsereignissen.
    Hooks in: FeedingEvent (REQ-004), TankFillEvent (REQ-014), MaintenanceLog (REQ-014).
    """

    def __init__(
        self,
        reference_repo,    # InvenTreeReferenceRepository
        transaction_repo,  # StockTransactionRepository
    ) -> None:
        self._ref_repo = reference_repo
        self._txn_repo = transaction_repo

    async def on_feeding_event(self, feeding_event: dict) -> list[str]:
        """
        Hook: Nach FeedingEvent (REQ-004).
        Erstellt pending stock_transactions für jeden verwendeten Dünger
        mit auto_deduct=true.
        """
        txn_keys = []
        for component in feeding_event.get("components", []):
            fert_key = component.get("fertilizer_key")
            amount_ml = component.get("amount_ml", 0)
            if not fert_key or amount_ml <= 0:
                continue

            ref = await self._ref_repo.find_by_entity("fertilizers", fert_key)
            if ref is None or not ref.get("auto_deduct"):
                continue

            txn_key = await self._txn_repo.create(
                reference_key=ref["_key"],
                inventree_part_id=ref["inventree_part_id"],
                transaction_type="remove",
                quantity=amount_ml,
                unit=ref.get("deduct_unit", "ml"),
                reason=(
                    f"FeedingEvent {feeding_event['_key']}: "
                    f"{component.get('fertilizer_name', fert_key)} "
                    f"{amount_ml}ml"
                ),
                source_event_collection="feeding_events",
                source_event_key=feeding_event["_key"],
            )
            txn_keys.append(txn_key)

        if txn_keys:
            logger.info(
                "consumption_tracked_feeding",
                event_key=feeding_event["_key"],
                transactions=len(txn_keys),
            )
        return txn_keys

    async def on_tank_fill_event(self, fill_event: dict) -> list[str]:
        """
        Hook: Nach TankFillEvent (REQ-014).
        Erstellt pending stock_transactions für Dünger im Befüllungs-Snapshot.
        """
        txn_keys = []
        for component in fill_event.get("fertilizer_snapshot", []):
            fert_key = component.get("fertilizer_key")
            amount_ml = component.get("amount_ml", 0)
            if not fert_key or amount_ml <= 0:
                continue

            ref = await self._ref_repo.find_by_entity("fertilizers", fert_key)
            if ref is None or not ref.get("auto_deduct"):
                continue

            txn_key = await self._txn_repo.create(
                reference_key=ref["_key"],
                inventree_part_id=ref["inventree_part_id"],
                transaction_type="remove",
                quantity=amount_ml,
                unit=ref.get("deduct_unit", "ml"),
                reason=(
                    f"TankFillEvent {fill_event['_key']}: "
                    f"{component.get('fertilizer_name', fert_key)} "
                    f"{amount_ml}ml"
                ),
                source_event_collection="tank_fill_events",
                source_event_key=fill_event["_key"],
            )
            txn_keys.append(txn_key)

        if txn_keys:
            logger.info(
                "consumption_tracked_tank_fill",
                event_key=fill_event["_key"],
                transactions=len(txn_keys),
            )
        return txn_keys

    async def on_maintenance_log(self, maintenance_log: dict) -> list[str]:
        """
        Hook: Nach MaintenanceLog (REQ-014).
        Erstellt pending stock_transactions für verbrauchte Reinigungsmittel/Chemikalien.
        """
        txn_keys = []
        for product in maintenance_log.get("products_used", []):
            entity_collection = product.get("entity_collection", "equipment")
            entity_key = product.get("entity_key")
            amount = product.get("amount", 0)
            unit = product.get("unit", "ml")
            if not entity_key or amount <= 0:
                continue

            ref = await self._ref_repo.find_by_entity(
                entity_collection, entity_key
            )
            if ref is None or not ref.get("auto_deduct"):
                continue

            txn_key = await self._txn_repo.create(
                reference_key=ref["_key"],
                inventree_part_id=ref["inventree_part_id"],
                transaction_type="remove",
                quantity=amount,
                unit=unit,
                reason=(
                    f"MaintenanceLog {maintenance_log['_key']}: "
                    f"{product.get('name', entity_key)} "
                    f"{amount}{unit} ({maintenance_log.get('maintenance_type', '')})"
                ),
                source_event_collection="maintenance_logs",
                source_event_key=maintenance_log["_key"],
            )
            txn_keys.append(txn_key)

        if txn_keys:
            logger.info(
                "consumption_tracked_maintenance",
                log_key=maintenance_log["_key"],
                transactions=len(txn_keys),
            )
        return txn_keys
```

### 3.6 Celery-Tasks

```python
from celery import shared_task

import structlog

logger = structlog.get_logger()


@shared_task(
    name="inventree.sync_stock_levels",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def sync_stock_levels_task(self) -> dict:
    """Periodisch: Zieht aktuelle Bestandsmengen aus InvenTree (READ)."""
    import asyncio
    from app.common.dependencies import get_inventree_sync_engine

    engine = get_inventree_sync_engine()
    if engine is None:
        return {"skipped": True, "reason": "InvenTree not configured"}

    try:
        result = asyncio.run(engine.sync_stock_levels())
        logger.info("inventree_stock_sync_complete", **result)
        return result
    except Exception as exc:
        logger.error("inventree_stock_sync_failed", error=str(exc))
        self.retry(exc=exc)


@shared_task(
    name="inventree.push_pending_transactions",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def push_pending_transactions_task(self) -> dict:
    """Periodisch: Sendet ausstehende Verbrauchsbuchungen an InvenTree (WRITE)."""
    import asyncio
    from app.common.dependencies import get_inventree_sync_engine

    engine = get_inventree_sync_engine()
    if engine is None:
        return {"skipped": True, "reason": "InvenTree not configured"}

    try:
        result = asyncio.run(engine.push_pending_transactions())
        logger.info("inventree_push_complete", **result)
        return result
    except Exception as exc:
        logger.error("inventree_push_failed", error=str(exc))
        self.retry(exc=exc)


@shared_task(name="inventree.sync_all")
def sync_all_task() -> dict:
    """Convenience: Stock-Pull + Transaction-Push in einem Aufruf."""
    stock_task = sync_stock_levels_task.delay()
    push_task = push_pending_transactions_task.delay()
    return {
        "stock_sync_task_id": stock_task.id,
        "push_task_id": push_task.id,
    }
```

**Celery-Beat Schedule:**
```python
# In app/celery_config.py — Ergänzung

CELERY_BEAT_SCHEDULE_INVENTREE = {
    "inventree-stock-sync-hourly": {
        "task": "inventree.sync_stock_levels",
        "schedule": 3600.0,  # Stündlich
    },
    "inventree-push-pending-5min": {
        "task": "inventree.push_pending_transactions",
        "schedule": 300.0,  # Alle 5 Minuten
    },
}
```

### 3.7 REST-API Endpunkte

**Connection-Management (5 Endpunkte):**
```python
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/api/v1/inventree", tags=["inventree"])


@router.get("/connections")
async def list_connections(
    connection_repo=Depends(get_connection_repo),
) -> list[dict]:
    """Listet alle InvenTree-Verbindungen."""
    return await connection_repo.list_all()


@router.post("/connections")
async def create_connection(
    data: InvenTreeConnectionCreate,
    connection_repo=Depends(get_connection_repo),
) -> dict:
    """Erstellt eine neue InvenTree-Verbindung."""
    return await connection_repo.create(data.model_dump())


@router.get("/connections/{connection_key}")
async def get_connection(
    connection_key: str,
    connection_repo=Depends(get_connection_repo),
) -> dict:
    """Lädt eine InvenTree-Verbindung."""
    conn = await connection_repo.get(connection_key)
    if not conn:
        raise HTTPException(404, "Connection not found")
    return conn


@router.put("/connections/{connection_key}")
async def update_connection(
    connection_key: str,
    data: InvenTreeConnectionUpdate,
    connection_repo=Depends(get_connection_repo),
) -> dict:
    """Aktualisiert eine InvenTree-Verbindung."""
    return await connection_repo.update(
        connection_key, data.model_dump(exclude_unset=True)
    )


@router.post("/connections/{connection_key}/health-check")
async def health_check(
    connection_key: str,
    connection_repo=Depends(get_connection_repo),
    sync_engine=Depends(get_sync_engine),
) -> dict:
    """Prüft die Erreichbarkeit der InvenTree-Instanz."""
    ok = await sync_engine._adapter.health_check()
    await connection_repo.update_health_check(connection_key, ok=ok)
    return {"healthy": ok}
```

**Referenz-Management (4 Endpunkte):**
```python
@router.post("/references/link")
async def link_entity(
    entity_collection: str,
    entity_key: str,
    inventree_part_id: int,
    auto_deduct: bool = False,
    deduct_unit: str | None = None,
    sync_engine=Depends(get_sync_engine),
) -> dict:
    """Verknüpft eine Kamerplanter-Entität mit einem InvenTree-Part."""
    return await sync_engine.link_entity(
        entity_collection,
        entity_key,
        inventree_part_id,
        auto_deduct=auto_deduct,
        deduct_unit=deduct_unit,
    )


@router.get("/references")
async def list_references(
    entity_collection: str | None = Query(None),
    reference_repo=Depends(get_reference_repo),
) -> list[dict]:
    """Listet alle InvenTree-Referenzen (optional gefiltert nach Collection)."""
    if entity_collection:
        return await reference_repo.find_by_collection(entity_collection)
    return await reference_repo.list_all()


@router.delete("/references/{reference_key}")
async def unlink_entity(
    reference_key: str,
    reference_repo=Depends(get_reference_repo),
) -> dict:
    """Entfernt eine InvenTree-Verknüpfung."""
    await reference_repo.delete(reference_key)
    return {"deleted": reference_key}


@router.post("/references/{reference_key}/sync")
async def sync_single_reference(
    reference_key: str,
    sync_engine=Depends(get_sync_engine),
    reference_repo=Depends(get_reference_repo),
) -> dict:
    """Synchronisiert den Bestand einer einzelnen Referenz."""
    ref = await reference_repo.get(reference_key)
    if not ref:
        raise HTTPException(404, "Reference not found")
    part = await sync_engine._adapter.get_part(ref["inventree_part_id"])
    if part is None:
        raise HTTPException(404, "InvenTree Part not found")
    await reference_repo.update_cached_stock(
        reference_key,
        stock=part.total_in_stock,
        unit=part.stock_unit,
    )
    return {"stock": part.total_in_stock, "unit": part.stock_unit}
```

**InvenTree-Browse (2 Endpunkte):**
```python
@router.get("/browse/parts")
async def browse_parts(
    query: str = Query(..., min_length=2),
    category_id: int | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
    sync_engine=Depends(get_sync_engine),
) -> list[dict]:
    """Durchsucht InvenTree-Parts (für Verknüpfungs-Dialog)."""
    parts = await sync_engine._adapter.search_parts(
        query, category_id=category_id, limit=limit
    )
    return [p.model_dump() for p in parts]


@router.get("/browse/categories")
async def browse_categories(
    parent_id: int | None = Query(None),
    sync_engine=Depends(get_sync_engine),
) -> list[dict]:
    """Lädt InvenTree-Kategorien (für Kategorie-Browser)."""
    categories = await sync_engine._adapter.get_categories(parent_id=parent_id)
    return [c.model_dump() for c in categories]
```

**Sync & Transaktions-Log (2 Endpunkte):**
```python
@router.post("/sync/trigger")
async def trigger_sync() -> dict:
    """Löst manuellen Full-Sync aus (Stock-Pull + Transaction-Push)."""
    result = sync_all_task.delay()
    return {"task_id": result.id}


@router.get("/transactions")
async def list_transactions(
    status: str | None = Query(None),
    entity_collection: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    transaction_repo=Depends(get_transaction_repo),
) -> list[dict]:
    """Listet Stock-Transaktionen (optional gefiltert nach Status/Collection)."""
    return await transaction_repo.find(
        status=status,
        entity_collection=entity_collection,
        limit=limit,
    )
```

**Equipment-CRUD (5 Endpunkte):**
```python
equipment_router = APIRouter(
    prefix="/api/v1/equipment", tags=["equipment"]
)


@equipment_router.get("/")
async def list_equipment(
    equipment_type: str | None = Query(None),
    status: str | None = Query(None),
    location_key: str | None = Query(None),
    equipment_repo=Depends(get_equipment_repo),
) -> list[dict]:
    """Listet Equipment (optional gefiltert nach Typ, Status, Location)."""
    return await equipment_repo.find(
        equipment_type=equipment_type,
        status=status,
        location_key=location_key,
    )


@equipment_router.post("/")
async def create_equipment(
    data: EquipmentCreate,
    equipment_repo=Depends(get_equipment_repo),
) -> dict:
    """Erstellt ein neues Equipment."""
    return await equipment_repo.create(data.model_dump())


@equipment_router.get("/{equipment_key}")
async def get_equipment(
    equipment_key: str,
    equipment_repo=Depends(get_equipment_repo),
) -> dict:
    """Lädt ein Equipment per Key."""
    eq = await equipment_repo.get(equipment_key)
    if not eq:
        raise HTTPException(404, "Equipment not found")
    return eq


@equipment_router.put("/{equipment_key}")
async def update_equipment(
    equipment_key: str,
    data: EquipmentUpdate,
    equipment_repo=Depends(get_equipment_repo),
) -> dict:
    """Aktualisiert ein Equipment."""
    return await equipment_repo.update(
        equipment_key, data.model_dump(exclude_unset=True)
    )


@equipment_router.get("/by-location/{location_key}")
async def equipment_by_location(
    location_key: str,
    equipment_repo=Depends(get_equipment_repo),
) -> list[dict]:
    """Listet Equipment einer Location (via equipment_at Edge)."""
    return await equipment_repo.find_by_location(location_key)
```

**Zusammenfassung API-Endpunkte:**

| # | Methode | Pfad | Beschreibung | Auth |
|---|---------|------|-------------|------|
| 1 | GET | `/api/v1/inventree/connections` | Alle Verbindungen | Admin |
| 2 | POST | `/api/v1/inventree/connections` | Verbindung anlegen | Admin |
| 3 | GET | `/api/v1/inventree/connections/{key}` | Verbindung laden | Admin |
| 4 | PUT | `/api/v1/inventree/connections/{key}` | Verbindung aktualisieren | Admin |
| 5 | POST | `/api/v1/inventree/connections/{key}/health-check` | Health-Check | Admin |
| 6 | POST | `/api/v1/inventree/references/link` | Entität verknüpfen | Mitglied |
| 7 | GET | `/api/v1/inventree/references` | Referenzen auflisten | Mitglied |
| 8 | DELETE | `/api/v1/inventree/references/{key}` | Verknüpfung lösen | Mitglied |
| 9 | POST | `/api/v1/inventree/references/{key}/sync` | Einzelne Referenz synchronisieren | Mitglied |
| 10 | GET | `/api/v1/inventree/browse/parts` | Parts suchen | Mitglied |
| 11 | GET | `/api/v1/inventree/browse/categories` | Kategorien laden | Mitglied |
| 12 | POST | `/api/v1/inventree/sync/trigger` | Manueller Full-Sync | Mitglied |
| 13 | GET | `/api/v1/inventree/transactions` | Transaktions-Log | Mitglied |
| 14 | GET | `/api/v1/equipment/` | Equipment auflisten | Mitglied |
| 15 | POST | `/api/v1/equipment/` | Equipment anlegen | Mitglied |
| 16 | GET | `/api/v1/equipment/{key}` | Equipment laden | Mitglied |
| 17 | PUT | `/api/v1/equipment/{key}` | Equipment aktualisieren | Mitglied |
| 18 | GET | `/api/v1/equipment/by-location/{key}` | Equipment pro Location | Mitglied |

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Connection-Config | Admin | Admin | Admin |
| References & Sync | Mitglied | Mitglied | — |
| Equipment | Mitglied | Mitglied | Admin |

### 4.1 Sicherheitsanforderungen für InvenTree-Anbindung

<!-- Quelle: IT-Security-Review SEC-H-005 -->

| # | Regel | Stufe |
|---|-------|-------|
| IT-001 | Der InvenTree API-Token MUSS mit AES-256 (Fernet) verschlüsselt in ArangoDB gespeichert werden. Entschlüsselung erfolgt ausschließlich zur Laufzeit im Service-Layer. | MUSS |
| IT-002 | API-Token DÜRFEN NICHT in API-Responses, Logs oder Fehler-Traces erscheinen (Pydantic `Field(exclude=True)`, structlog-Filter). | MUSS |
| IT-003 | HTTPS-Zertifikate des InvenTree-Servers MÜSSEN standardmäßig validiert werden (`verify_ssl: true`). Deaktivierung nur explizit und mit UI-Warnung. | MUSS |
| IT-004 | Token-Rotation SOLL unterstützt werden: Endpoint zum Aktualisieren des API-Tokens ohne Neuanlage der Connection. | SOLL |
| IT-005 | Kamerplanter→InvenTree-Requests MÜSSEN auf 60 req/min pro Connection begrenzt werden (Client-seitiges Rate-Limiting). | MUSS |
| IT-006 | Health-Check-Endpoint (`/inventree/connections/{key}/health`) DARF NICHT offenlegen, ob die URL eine gültige InvenTree-Instanz ist, wenn die Authentication fehlschlägt — generische Fehlermeldung. | MUSS |

## 5. Abhängigkeiten

**Benötigt:**
- **REQ-002** (Standort & Substrat) — Location-Entität für Equipment-Zuordnung (`equipment_at` Edge)
- **REQ-004** (Dünge-Logik) — Fertilizer-Entität und FeedingEvent-Hook für Verbrauchstracking
- **REQ-014** (Tankmanagement) — Tank-Entität, TankFillEvent und MaintenanceLog für Verbrauchstracking
- **NFR-006** (API-Fehlerbehandlung) — Einheitliche Fehlerbehandlung bei InvenTree-Kommunikationsfehlern

**Systemabhängigkeiten:**
- ArangoDB (Persistenz aller Collections)
- Redis + Celery (Periodische Sync-Tasks)
- httpx (Async HTTP-Client für InvenTree-API)
- cryptography (Verschlüsselung des API-Tokens in `inventree_connections`)

**Wird benötigt von:**
- **REQ-004** (Dünge-Logik) — MITTEL: Bestandswarnung bei niedrigem Dünger-Stock, Anzeige InvenTree-Bestand in Mixing-UI
- **REQ-009** (Dashboard) — NIEDRIG: Optionales Dashboard-Widget "Lagerbestand kritisch"
- **REQ-014** (Tankmanagement) — NIEDRIG: InvenTree-Bestand in Tank-Detail-Ansicht, Verbrauchstracking bei Wartung

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Connection-CRUD:** InvenTree-Verbindung anlegen, lesen, aktualisieren, löschen
- [ ] **Health-Check:** Erreichbarkeit der InvenTree-Instanz per Endpunkt prüfbar
- [ ] **Equipment-CRUD:** Equipment anlegen, lesen, aktualisieren, filtern (Typ, Status, Location)
- [ ] **Referenz-Verlinkung:** Kamerplanter-Entität (Fertilizer/Tank/Equipment) mit InvenTree-Part verknüpfbar, inkl. initialem Stock-Pull
- [ ] **Stock-Pull (READ):** Periodischer Import (hourly) der Bestandsmengen aus InvenTree in lokalen Cache
- [ ] **Stock-Push (WRITE):** Automatische Verbrauchsrückmeldung bei FeedingEvent, TankFillEvent und MaintenanceLog (wenn `auto_deduct=true`)
- [ ] **Transaktions-Log:** Immutables Log aller Verbrauchsbuchungen mit Status-Tracking (pending → synced/failed)
- [ ] **Retry-Mechanismus:** Fehlgeschlagene Transaktionen werden 3× mit exponentiellem Backoff wiederholt
- [ ] **Optionalität:** System funktioniert vollständig ohne InvenTree-Konfiguration; kein Blocking bei InvenTree-Ausfall
- [ ] **Testabdeckung:** Unit-Tests für Adapter (gemockte HTTP-Responses), Engine, ConsumptionTracker und API-Endpunkte

### Testszenarien:

**Szenario 1: InvenTree-Verbindung anlegen und Health-Check**
```
GIVEN: Kamerplanter ohne InvenTree-Konfiguration
WHEN: POST /api/v1/inventree/connections mit gültiger URL und Token
THEN:
  - Connection wird in inventree_connections gespeichert
  - Token wird verschlüsselt abgelegt (nicht im Klartext)
  - POST /api/v1/inventree/connections/{key}/health-check liefert {"healthy": true}
  - last_health_check_at und last_health_check_ok werden aktualisiert
```

**Szenario 2: Dünger mit InvenTree-Part verlinken**
```
GIVEN: Fertilizer "BioBizz Bio-Bloom" (fert_001) und InvenTree-Part #42 mit 12.5L Bestand
WHEN: POST /api/v1/inventree/references/link mit entity_collection="fertilizers", entity_key="fert_001", inventree_part_id=42, auto_deduct=true
THEN:
  - inventree_references-Dokument erstellt mit cached_stock=12.5
  - has_inventree_ref-Edge von fertilizers/fert_001 → inventree_references/ref_*
  - fertilizers/fert_001.inventree_part_id = 42 (denormalisiert)
  - GET /api/v1/fertilizers/fert_001 enthält InvenTree-Bestandsinfo
```

**Szenario 3: Automatische Bestandsreduktion bei FeedingEvent**
```
GIVEN: Fertilizer "CalMag" mit InvenTree-Ref (auto_deduct=true), Bestand 500ml
WHEN: FeedingEvent erstellt mit 5ml/L × 10L = 50ml CalMag
THEN:
  - ConsumptionTracker erzeugt stock_transaction (type="remove", quantity=50, unit="ml", status="pending")
  - Nächster push_pending_transactions-Lauf (max. 5 Min) sendet POST /api/stock/remove/ an InvenTree
  - Transaction-Status wechselt zu "synced", synced_at wird gesetzt
  - InvenTree-Bestand: 500 - 50 = 450ml
```

**Szenario 4: InvenTree nicht erreichbar — Graceful Degradation**
```
GIVEN: InvenTree-Verbindung konfiguriert, Server nicht erreichbar (HTTP 503)
WHEN: Nutzer erstellt FeedingEvent und Celery-Sync läuft
THEN:
  - FeedingEvent wird OHNE Fehler gespeichert (InvenTree blockiert nicht)
  - stock_transaction wird als "pending" erstellt
  - sync_stock_levels_task loggt Warning und retried (max 3×)
  - push_pending_transactions_task markiert Transaktion mit retry_count++ und last_error
  - Health-Check zeigt {"healthy": false}
  - Nach Wiederherstellung: pending Transaktionen werden beim nächsten Lauf gesynct
```

**Szenario 5: Equipment anlegen und Location zuordnen**
```
GIVEN: Location "Growzelt 1" (loc_zelt_1) existiert
WHEN: POST /api/v1/equipment/ mit name="Bluelab pH Pen", type="sensor", inventree_part_id=1247
THEN:
  - Equipment-Dokument in equipment-Collection erstellt
  - equipment_at-Edge zu locations/loc_zelt_1
  - Optional: has_inventree_ref-Edge zu inventree_references (wenn InvenTree konfiguriert)
  - GET /api/v1/equipment/by-location/loc_zelt_1 listet den pH Pen
```

**Szenario 6: Periodischer Stock-Level-Sync mit Drift-Warning**
```
GIVEN: Fertilizer "BioGrow" mit cached_stock=1000ml, InvenTree zeigt 750ml
WHEN: Stündlicher sync_stock_levels_task läuft
THEN:
  - cached_stock wird auf 750ml aktualisiert
  - Drift = |750-1000|/1000 = 25% > 20% Schwellwert
  - structlog Warning "inventree_stock_drift" wird geloggt
  - Sync-Stats enthalten drift_warnings mit entity, old/new stock, drift_pct
```

**Szenario 7: Wartungsprodukt-Verbrauch über MaintenanceLog**
```
GIVEN: Equipment "H2O2 3% 5L" (type="cleaning_agent") mit InvenTree-Ref (auto_deduct=true)
WHEN: MaintenanceLog für Tank (type="sanitization") erstellt mit products_used: [{entity_key: "h2o2_5l", amount: 250, unit: "ml"}]
THEN:
  - ConsumptionTracker erzeugt stock_transaction (type="remove", quantity=250, unit="ml")
  - reason: "MaintenanceLog maint_042: H2O2 3% 5L 250ml (sanitization)"
  - Transaction wird beim nächsten Push-Lauf (5 Min) an InvenTree gesendet
```

---

**Hinweise für RAG-Integration:**
- Keywords: InvenTree, Inventar, Verbrauchsmaterial, Equipment, Betriebsmittel, Stock-Adjustment, Bidirektionaler Sync, Consumption Tracking, auto_deduct, IPN, Seriennummer, Barcode
- Fachbegriffe: Adapter-Pattern, Graceful Degradation, Lose Kopplung, Denormalisierung, Immutable Log, Drift-Detection
- Verknüpfung: Erweitert REQ-004 (Dünger-Bestand), REQ-014 (Tank-/Wartungs-Tracking), REQ-002 (Equipment-Location)
