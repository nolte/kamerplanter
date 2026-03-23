# Backend Style Guide — Python / FastAPI

> Verbindlicher Style Guide fuer den Kamerplanter Python-Backend-Code.
> Wird durch **Ruff** (Linting + Formatting), **MyPy** (Typsicherheit) und **pytest** (Tests) automatisch geprueft.

**Scope:** `src/backend/`

---

## 1. Statische Analyse & Tooling

| Tool | Zweck | Config |
|------|-------|--------|
| **Ruff** | Linting + Import-Sortierung + Formatting | `pyproject.toml` → `[tool.ruff]` |
| **MyPy** | Statische Typanalyse (strict) | `pyproject.toml` → `[tool.mypy]` |
| **pytest** | Unit-/Integrationstests | `pyproject.toml` → `[tool.pytest]` |

### 1.1 Ruff-Konfiguration

```toml
[tool.ruff]
line-length = 120
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]
ignore = ["B008"]   # FastAPI Depends() in Default-Argumenten erlaubt
```

| Regel-Set | Zweck |
|-----------|-------|
| **E** | PEP 8 Errors |
| **F** | Pyflakes (unbenutzte Imports, undefinierte Namen) |
| **I** | isort-kompatible Import-Sortierung |
| **N** | pep8-naming (Namenskonventionen) |
| **W** | PEP 8 Warnings |
| **UP** | pyupgrade (moderne Python-Syntax erzwingen) |
| **B** | flake8-bugbear (haeufige Fehlerquellen) |
| **SIM** | flake8-simplify (unnoetige Komplexitaet) |

### 1.2 MyPy-Konfiguration

```toml
[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]
```

- **Alle** Funktionsparameter und Rueckgabewerte muessen typisiert sein.
- `# type: ignore[...]` nur mit spezifischem Error-Code, nie blanko.

### 1.3 CI-Pruefung

```bash
ruff check src/backend/        # Linting
ruff format --check src/backend/ # Formatting
mypy src/backend/app/           # Typpruefung
pytest src/backend/tests/       # Tests
```

---

## 2. Projektstruktur (5-Schichten-Architektur)

```
src/backend/app/
├── api/v1/                          # Schicht 1: Presentation (FastAPI Router)
│   └── {feature}/
│       ├── router.py                # Globale Endpunkte (/api/v1/...)
│       ├── tenant_router.py         # Tenant-scoped Endpunkte (/api/v1/t/{slug}/...)
│       └── schemas.py               # Request/Response Pydantic-Modelle
├── domain/                          # Schicht 2+3: Business Logic
│   ├── models/                      # Domain-Modelle (Pydantic BaseModel)
│   ├── services/                    # Orchestrierung (DB-Zugriff via Repos)
│   ├── engines/                     # Reine Geschaeftslogik (stateless, kein DB)
│   ├── calculators/                 # Berechnungsutilities
│   └── interfaces/                  # ABC-Interfaces fuer Repositories/Adapter
├── data_access/                     # Schicht 4: Data Access
│   ├── arango/                      # ArangoDB-Repositories
│   │   ├── base_repository.py
│   │   ├── collections.py           # Collection-Namen als Konstanten
│   │   └── {entity}_repository.py
│   └── external/                    # Externe Adapter (GBIF, Perenual, HA, ...)
├── common/                          # Cross-Cutting Concerns
│   ├── exceptions.py                # Alle Custom Exceptions
│   ├── enums.py                     # Alle StrEnum-Definitionen
│   ├── types.py                     # Type-Aliases
│   ├── dependencies.py              # FastAPI DI-Factories
│   ├── auth.py                      # Auth-Utilities
│   ├── middleware.py                # HTTP-Middleware
│   └── tenant_guard.py             # Multi-Tenancy Guard
├── config/
│   ├── settings.py                  # Pydantic BaseSettings
│   ├── constants.py                 # App-Konstanten
│   └── logging.py                   # structlog-Setup
├── tasks/                           # Celery Async Tasks
├── migrations/                      # Seed-Daten & Schema-Migrationen
└── main.py                          # FastAPI App-Initialisierung
```

### 2.1 Schichtenregeln

| Von → Nach | Erlaubt? |
|------------|----------|
| API → Service | Ja |
| API → Engine/Model | Ja (fuer einfache Validierung) |
| Service → Engine | Ja |
| Service → Repository (via Interface) | Ja |
| Engine → Repository | **Nein** (Engines sind stateless/pure) |
| Repository → Domain Model | Ja (Konvertierung dict → Model) |
| Alles → `common/` | Ja |

---

## 3. Namenskonventionen

### 3.1 Dateien

| Element | Konvention | Beispiel |
|---------|-----------|----------|
| Module | `snake_case.py` | `species_service.py` |
| Router | `router.py` / `tenant_router.py` | In Feature-Verzeichnis |
| Schemas | `schemas.py` | In Feature-Verzeichnis |
| Tests | `test_{modul}.py` | `test_care_reminder_engine.py` |

### 3.2 Klassen

| Typ | Konvention | Beispiel |
|-----|-----------|----------|
| Domain Model | PascalCase, Entitaetsname | `Species`, `Fertilizer`, `User` |
| Service | `{Entity}Service` | `SpeciesService`, `NutrientPlanService` |
| Engine | `{Feature}Engine` | `PhaseTransitionEngine`, `TankEngine` |
| Calculator | `{Feature}Calculator` | `VPDCalculator`, `NutrientSolutionCalculator` |
| Repository (konkret) | `Arango{Entity}Repository` | `ArangoSpeciesRepository` |
| Repository (Interface) | `I{Entity}Repository` | `ISpeciesRepository` |
| Adapter (konkret) | `{Service}{Type}Adapter` | `GbifAdapter`, `SmtpEmailAdapter` |
| Adapter (Interface) | `I{Type}Adapter` | `IEmailService`, `IEnrichmentAdapter` |
| Exception | `{Feature}Error` | `NotFoundError`, `PhaseTransitionError` |
| Schema (Request) | `{Entity}Create` / `{Entity}Update` | `SpeciesCreate`, `FertilizerUpdate` |
| Schema (Response) | `{Entity}Response` / `{Entity}ListResponse` | `SpeciesResponse` |

### 3.3 Funktionen & Variablen

| Element | Konvention | Beispiel |
|---------|-----------|----------|
| Oeffentliche Methoden | `snake_case` | `get_species()`, `validate_transition()` |
| Private Methoden | `_snake_case` | `_check_algae_risk()`, `_build_query()` |
| Boolean-Getter | `is_`, `has_`, `can_` Praefix | `is_active`, `has_cultivars` |
| Variablen | `snake_case` | `tank_state`, `fill_percent` |
| Private Attribute | `self._name` | `self._repo`, `self._db` |
| Konstanten | `UPPER_SNAKE_CASE` | `PH_RANGES`, `FILL_LEVEL_LOW_PERCENT` |

---

## 4. Typisierung

### 4.1 Allgemeine Regeln

```python
# RICHTIG: Moderne Union-Syntax (PEP 604)
def get_species(key: str) -> Species | None:

# FALSCH: Alte Optional-Syntax
def get_species(key: str) -> Optional[Species]:

# RICHTIG: Lowercase Generics (PEP 585)
items: list[Species]
mapping: dict[str, Any]
result: tuple[list[Species], int]

# FALSCH: typing-Modul Generics
items: List[Species]
mapping: Dict[str, Any]
```

### 4.2 Type-Aliases

```python
# In app/common/types.py — mit `type` Keyword (Python 3.12+)
type SpeciesKey = str
type FamilyKey = str
type DocumentKey = str
```

### 4.3 Keyword-Only Argumente

```python
# Fuer Klarheit: * erzwingt benannte Argumente
async def execute_transition(
    self,
    plant_key: str,
    target_phase_key: str,
    reason: str = "manual",
    *,                          # Alles danach ist keyword-only
    force: bool = False,
) -> PlantInstance:
```

---

## 5. Pydantic-Modelle

### 5.1 Domain Models

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Self

class Fertilizer(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    product_name: str = Field(min_length=1, max_length=200)
    npk_ratio: tuple[float, float, float] = (0.0, 0.0, 0.0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("npk_ratio")
    @classmethod
    def validate_npk(cls, v: tuple[float, float, float]) -> tuple[float, float, float]:
        for val in v:
            if val < 0:
                raise ValueError("NPK values must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        # Cross-Field-Validierung
        return self
```

**Regeln:**
- `alias="_key"` fuer ArangoDB-Schluesselfelder
- `model_config = {"populate_by_name": True}` wenn Alias verwendet wird
- `@field_validator` fuer Einzelfeld, `@model_validator(mode="after")` fuer Cross-Field
- Rueckgabetyp `Self` bei `model_validator`
- `@classmethod` Dekorator bei `@field_validator`

### 5.2 Request/Response Schemas

```python
# In api/v1/{feature}/schemas.py — getrennt von Domain Models
class SpeciesCreate(BaseModel):
    scientific_name: str = Field(min_length=1, max_length=200)
    common_name: str | None = None

class SpeciesResponse(BaseModel):
    key: str
    scientific_name: str
    common_name: str | None = None

class SpeciesListResponse(BaseModel):
    items: list[SpeciesResponse]
    total: int
    offset: int
    limit: int
```

---

## 6. FastAPI-Patterns

### 6.1 Router-Setup

```python
from fastapi import APIRouter, Depends, Query

router = APIRouter(
    prefix="/species",
    tags=["species"],
)

@router.get("", response_model=SpeciesListResponse)
def list_species(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    service: SpeciesService = Depends(get_species_service),
) -> SpeciesListResponse:
    items, total = service.list_species(offset, limit)
    return SpeciesListResponse(items=items, total=total, offset=offset, limit=limit)
```

**Regeln:**
- Router-Funktionen sind **synchron** (`def`, nicht `async def`)
- `response_model` immer explizit angeben
- Status-Codes: `201` fuer POST, `204` fuer DELETE, `200` Default
- Dependency Injection via `Depends()` Parameter
- Query-Parameter mit `Query()` fuer Validierung

### 6.2 Dependency Injection

```python
# In app/common/dependencies.py
def get_species_service() -> SpeciesService:
    repo = get_species_repo()
    graph_repo = get_graph_repo()
    return SpeciesService(repo, graph_repo)
```

- Factory-Funktionen in `dependencies.py`
- Repos und Services werden pro Request erzeugt

### 6.3 Tenant-Scoped Routing

```python
# In api/v1/{feature}/tenant_router.py
router = APIRouter(
    prefix="/t/{tenant_slug}/{feature}",
    tags=["{feature}"],
    dependencies=[Depends(require_tenant_membership)],
)

@router.get("")
def list_items(
    tenant_slug: str,
    tenant_key: str = Depends(resolve_tenant_key),
    service: Service = Depends(get_service),
) -> ListResponse:
    return service.list_items(tenant_key=tenant_key)
```

---

## 7. Service-Pattern

```python
class NutrientPlanService:
    def __init__(
        self,
        repo: INutrientPlanRepository,
        fert_repo: IFertilizerRepository,
        validator: NutrientPlanValidator,
    ) -> None:
        self._repo = repo
        self._fert_repo = fert_repo
        self._validator = validator

    def get_plan(self, key: str, tenant_key: str = "") -> NutrientPlan:
        plan = self._repo.get_by_key(key)
        if plan is None:
            raise NotFoundError("NutrientPlan", key)
        if tenant_key:
            verify_tenant_ownership(plan, tenant_key, "NutrientPlan")
        return plan
```

**Regeln:**
- Constructor Injection (Repos, Engines als Parameter)
- Private Attribute: `self._repo`
- Domain Exceptions werfen (`NotFoundError`, nicht `HTTPException`)
- `tenant_key` Parameter fuer Multi-Tenancy

---

## 8. Engine-Pattern

```python
class TankEngine:
    """Reine Geschaeftslogik — kein DB-Zugriff."""

    def check_alerts(self, tank: Tank, state: TankState) -> list[dict]:
        alerts: list[dict] = []
        if tank.current_volume_l and tank.capacity_l:
            fill_percent = (tank.current_volume_l / tank.capacity_l) * 100
            if fill_percent < FILL_LEVEL_LOW_PERCENT:
                alerts.append({"type": "low_fill", "severity": "warning"})
        return alerts
```

**Abgrenzung Service vs. Engine:**

| Aspekt | Service | Engine |
|--------|---------|--------|
| DB-Zugriff | Ja (via Repos) | **Nein** |
| State | Hat `self._repo` etc. | Stateless |
| Input | Keys/IDs | Vorgeladene Objekte |
| Output | Domain Models | Berechnungsergebnisse |
| Fehler | `NotFoundError` etc. | `ValueError`, Domain-Errors |

---

## 9. Repository-Pattern

### 9.1 Interface (ABC)

```python
# In domain/interfaces/{entity}_repository.py
from abc import ABC, abstractmethod

class ISpeciesRepository(ABC):
    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[Species], int]: ...

    @abstractmethod
    def get_by_key(self, key: str) -> Species | None: ...

    @abstractmethod
    def create(self, model: Species) -> Species: ...
```

- Abstrakte Methoden verwenden `...` (Ellipsis), nicht `pass`
- Rueckgabetypen immer Domain Models

### 9.2 Konkrete Implementierung

```python
# In data_access/arango/{entity}_repository.py
class ArangoSpeciesRepository(ISpeciesRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.SPECIES)

    def get_by_key(self, key: str) -> Species | None:
        doc = self.collection.get(key)
        return Species(**self._from_doc(doc)) if doc else None
```

- Erbt von Interface **und** `BaseArangoRepository`
- Collection-Namen aus `collections.py` Konstanten
- Dict → Model Konvertierung: `Species(**doc)`

---

## 10. Fehlerbehandlung

### 10.1 Exception-Hierarchie

```python
# In app/common/exceptions.py
class KamerplanterError(Exception):
    def __init__(self, message: str, error_code: str, status_code: int, details: list[dict] | None = None):
        self.error_id = f"err_{uuid.uuid4()}"
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or []

class NotFoundError(KamerplanterError): ...       # 404
class DuplicateError(KamerplanterError): ...      # 409
class ValidationError(KamerplanterError): ...     # 422
class PhaseTransitionError(KamerplanterError): ... # 422
class KarenzViolationError(KamerplanterError): ... # 422
```

- **Alle** Exceptions erben von `KamerplanterError`
- Exception traegt HTTP-Details (wird vom Global Handler konvertiert)
- `error_id` (UUID) fuer Log-Korrelation

### 10.2 Global Handler

```python
# In main.py registriert
app.add_exception_handler(KamerplanterError, app_error_handler)
```

- Services/Engines werfen **nie** `HTTPException` direkt
- Nur der API-Layer (via Global Handler) konvertiert zu HTTP-Responses

---

## 11. Enums

```python
# In app/common/enums.py — ALLE Enums zentral
from enum import StrEnum

class PlantCategory(StrEnum):
    INDOOR_HOUSEPLANT = "indoor_houseplant"
    OUTDOOR_ORNAMENTAL = "outdoor_ornamental"
    BALCONY_PLANT = "balcony_plant"
```

- **Immer** `StrEnum` (Python 3.11+, JSON-serialisierbar)
- Werte: `lowercase_snake_case`
- Alle Enums in **einer** Datei: `common/enums.py`

---

## 12. Konstanten

```python
# Modul-Level, UPPER_SNAKE_CASE, explizite Typisierung
PH_RANGES: dict[TankType, tuple[float, float]] = {
    TankType.NUTRIENT: (5.5, 6.5),
    TankType.RECIRCULATION: (5.5, 6.3),
}

FILL_LEVEL_LOW_PERCENT = 20.0
```

- Definiert am Anfang des Moduls (nach Imports)
- Gruppiert mit Kommentaren bei > 3 Konstanten

---

## 13. Import-Reihenfolge

Automatisch durch Ruff `I` (isort) erzwungen:

```python
# 1. Standardbibliothek
from datetime import UTC, datetime, timedelta
from abc import ABC, abstractmethod

# 2. Drittanbieter
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query

# 3. Lokale Imports
from app.common.exceptions import NotFoundError
from app.domain.models.species import Species
```

- Alphabetisch innerhalb jeder Sektion
- Eine Leerzeile zwischen den Sektionen

---

## 14. Logging

```python
import structlog

logger = structlog.get_logger()

# Key-Value Logging (NIEMALS String-Interpolation)
logger.info("tank_filled", tank_key=tank.key, volume=volume_l)
logger.warning("ec_drift", delta=ec_delta, threshold=0.3)
logger.error("enrichment_failed", source="gbif", error=str(e))
```

- Modul-Level: `logger = structlog.get_logger()`
- Erster Parameter: Event-Name (snake_case)
- Weitere Parameter: Key-Value Paare
- **Keine** f-Strings oder `%`-Formatierung in Log-Calls

---

## 15. Celery Tasks

```python
@celery_app.task(name="notifications.dispatch_due_care")
def dispatch_due_care_notifications() -> dict:
    """Daily dispatch at 06:05 UTC."""
    # Lazy Imports vermeiden Circular Dependencies
    from app.common.dependencies import get_notification_service

    service = get_notification_service()
    count = service.dispatch_pending()
    return {"status": "ok", "count": count}
```

- `@celery_app.task(name="module.task_name")` — expliziter Name
- Rueckgabe: `dict` mit `status` und Metriken
- **Lazy Imports** innerhalb der Task-Funktion
- Beat-Schedule in `tasks/__init__.py`

---

## 16. Tests

### 16.1 Dateistruktur

```
src/backend/tests/
├── unit/
│   ├── domain/
│   │   ├── engines/
│   │   │   └── test_tank_engine.py
│   │   └── services/
│   │       └── test_species_service.py
│   ├── adapters/
│   │   └── test_gbif_adapter.py
│   └── tasks/
│       └── test_notification_tasks.py
└── conftest.py
```

### 16.2 Test-Muster

```python
class TestTankEngine:
    """Testklasse gruppiert verwandte Tests."""

    def test_low_fill_generates_alert(self):
        tank = _make_tank(current_volume_l=5, capacity_l=100)
        engine = TankEngine()
        alerts = engine.check_alerts(tank, _make_state())
        assert any(a["type"] == "low_fill" for a in alerts)

    def test_normal_fill_no_alert(self):
        tank = _make_tank(current_volume_l=80, capacity_l=100)
        alerts = TankEngine().check_alerts(tank, _make_state())
        assert not any(a["type"] == "low_fill" for a in alerts)
```

**Regeln:**
- Testklassen: `Test{Feature}`
- Testmethoden: `test_{szenario}` (beschreibend)
- Factory-Helpers: `_make_{entity}(**overrides)` als modulprivate Funktionen
- Assertions: einfache `assert`-Statements (pytest-Stil)
- Mocking: `unittest.mock.patch` mit vollem Modulpfad
- `pytest.ini`: `asyncio_mode = "auto"`

---

## 17. Docstrings

```python
def validate_transition(self, plant_key: str, target_phase_key: str) -> list[str]:
    """Validate if phase transition is allowed.

    Args:
        plant_key: The plant to transition.
        target_phase_key: Target phase key.

    Returns:
        List of warning messages. Empty = OK.

    Raises:
        PhaseTransitionError: If transition is invalid.
    """
```

- **Google-Style** Format
- Pflicht fuer: oeffentliche Service-/Engine-Methoden, Celery Tasks
- Optional fuer: einfache Getter, private Hilfsfunktionen
- Einzeiler erlaubt: `"""Return species by key."""`

---

## 18. Zusammenfassung der Pruefkette

```
Code-Aenderung
    │
    ├─→ ruff check          → Import-Ordnung, Naming, Bugs, Vereinfachungen
    ├─→ ruff format --check → Formatierung (120 Zeichen, Black-Stil)
    ├─→ mypy --strict       → Typsicherheit, fehlende Annotationen
    └─→ pytest              → Fachliche Korrektheit
```

Alle vier Tools muessen in CI/CD **fehlerfrei** durchlaufen.
