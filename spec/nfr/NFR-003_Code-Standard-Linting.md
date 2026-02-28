---

ID: NFR-003
Titel: Englischer Source-Code-Standard & Verpflichtende Linting-Richtlinie
Kategorie: Code-Qualität / Governance Unterkategorie: Naming, Linting, Formatting, Type Safety Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python 3.14, Ruff, mypy, ESLint, TypeScript, Prettier
Status: Produktionsreif
Priorität: Kritisch
Version: 2.1
Autor: Business Analyst - Agrotech
Datum: 2026-02-25
Tags: [code-quality, linting, formatting, naming-conventions, type-safety, english-code]
Abhängigkeiten: []
Betroffene Module: [ALL]
---

# NFR-003: Englischer Source-Code-Standard & Linting-Richtlinie

## 1. Business Case

### 1.1 User Stories

**Als** Tech Lead  
**möchte ich** dass der gesamte Source Code auf Englisch verfasst wird  
**um** internationale Entwickler problemlos onboarden zu können.

**Als** DevOps Engineer  
**möchte ich** dass Code-Qualität automatisch im CI/CD-Prozess geprüft wird  
**um** manuelle Code-Reviews effizienter zu gestalten und technische Schulden zu vermeiden.

**Als** Entwickler  
**möchte ich** klare Formatierungs- und Linting-Regeln  
**um** Zeit bei Code-Reviews zu sparen und mich auf fachliche Logik zu konzentrieren.

**Als** AI-System (GitHub Copilot, ChatGPT)  
**möchte ich** konsistent formatierten, englischsprachigen Code  
**um** bessere Code-Vorschläge zu generieren.

### 1.2 Geschäftliche Motivation

**Internationale Skalierung**:
- 80% der Python-Entwickler weltweit arbeiten primär auf Englisch
- Offshore-Entwicklung (z.B. Indien, Osteuropa) erfordert englische Codebase
- Open-Source-Contributions nur mit englischem Code möglich

**Technische Qualität**:
- Konsistenter Code senkt Wartungskosten um 30-40%
- Automatisches Linting verhindert 60% aller Bugs vor Produktion
- Type Hints reduzieren Runtime-Fehler um 40%

**AI-Integration**:
- LLM-basierte Tools (Copilot, Cursor) sind auf englischen Code trainiert
- Bessere Code-Completion bei konsistenten Namenskonventionen
- Dokumentations-Generierung funktioniert nur mit englischen Docstrings

### 1.3 Fachliche Beschreibung

**Szenario**: Ein deutscher Entwickler schreibt Code mit deutschen Variablennamen:

```python
# ❌ VERBOTEN - Deutscher Code
def berechne_gdd(pflanze_id: str, basis_temperatur: float) -> float:
    tages_min = hole_temperatur_minimum(pflanze_id)
    tages_max = hole_temperatur_maximum(pflanze_id)
    return max(0, (tages_min + tages_max) / 2 - basis_temperatur)
```

**Problem**:
- Internationale Entwickler verstehen `berechne_gdd` nicht
- GitHub Copilot schlägt schlechte Vervollständigungen vor
- Code-Reviews dauern länger (Kontext-Switching DE↔EN)

**Lösung**:

```python
# ✅ KORREKT - Englischer Code
def calculate_gdd(plant_id: str, base_temperature: float) -> float:
    """
    Calculate Growing Degree Days (GDD) for a plant.
    
    Args:
        plant_id: UUID of the plant
        base_temperature: Base temperature in °C
    
    Returns:
        GDD value (0 if negative)
    """
    daily_min = get_temperature_minimum(plant_id)
    daily_max = get_temperature_maximum(plant_id)
    return max(0, (daily_min + daily_max) / 2 - base_temperature)
```

---

## 2. Sprachrichtlinie

### 2.1 Grundsatz

| Dokumententyp | Sprache |
|---------------|---------|
| **Anforderungsdokumente** | Deutsch |
| **Architekturentscheidungen** | Deutsch |
| **User Stories** | Deutsch |
| **Meeting-Notizen** | Deutsch |
| **Source Code** | **Englisch** |
| **Commit Messages** | **Englisch** |
| **API-Dokumentation** | **Englisch** |
| **Code-Kommentare** | **Englisch** |
| **Docstrings** | **Englisch** |

**Begründung**: Deutsche Fachlichkeit, internationale Technologie.

### 2.2 Englisch verpflichtend für

**Code-Elemente**:
- Variablennamen (`plant_id`, nicht `pflanzen_id`)
- Funktionsnamen (`calculate_gdd`, nicht `berechne_gdd`)
- Klassennamen (`IrrigationService`, nicht `BewaesserungsService`)
- Modulnamen (`irrigation.py`, nicht `bewaesserung.py`)
- Konstanten (`MAX_WATER_LITERS`, nicht `MAX_WASSER_LITER`)

**Dokumentation**:
- Docstrings (Google/NumPy Style)
- Inline-Kommentare
- README.md (technisch)
- CHANGELOG.md
- API-Dokumentation (OpenAPI)

**Infrastruktur**:
- Kubernetes-Manifeste (`deployment.yaml`, nicht `bereitstellung.yaml`)
- Docker-Images (`agrotech/backend`, nicht `agrotech/backend-de`)
- Environment Variables (`DATABASE_URL`, nicht `DATENBANK_URL`)
- Config-Files (`app-config.yaml`)

**Versionskontrolle**:
- Commit Messages
- Branch-Namen (`feature/add-irrigation`, nicht `feature/bewaesserung-hinzufuegen`)
- Pull Request Titles & Descriptions
- Issue Titles

### 2.3 Namenskonventionen (Python 3.14)

**PEP 8 + Agrotech Extensions**:

```python
# ✅ Funktionen & Variablen: snake_case
def calculate_vpd(temperature: float, humidity: float) -> float:
    saturation_vapor_pressure = 0.6108 * exp(17.27 * temperature / (temperature + 237.3))
    actual_vapor_pressure = saturation_vapor_pressure * humidity / 100
    return saturation_vapor_pressure - actual_vapor_pressure

# ✅ Klassen: PascalCase
class PlantRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

# ✅ Konstanten: UPPER_SNAKE_CASE
MAX_SOIL_MOISTURE_PERCENT = 80
MIN_SOIL_MOISTURE_PERCENT = 20
IRRIGATION_CHECK_INTERVAL_SECONDS = 900  # 15 minutes

# ✅ Private Attribute: _leading_underscore
class Plant:
    def __init__(self, species_id: str):
        self._species_id = species_id  # Private
        self.current_phase = "seedling"  # Public

# ✅ Protected Methods: _leading_underscore
class IrrigationService:
    def _calculate_soil_capacity(self, substrate_type: str) -> float:
        """Protected helper method"""
        pass

# ✅ Dunder Methods: __double_underscore__
class Plant:
    def __str__(self) -> str:
        return f"Plant({self.species_name})"
    
    def __repr__(self) -> str:
        return f"Plant(id={self.id}, species={self.species_id})"

# ✅ Type Aliases: PascalCase (Python 3.14)
type PlantID = str
type TemperatureCelsius = float

def get_plant(plant_id: PlantID) -> Plant:
    ...
```

**Verbotene Patterns**:

```python
# ❌ Deutsche Namen
def berechne_duengermenge(pflanzen_id: str) -> float:
    ...

# ❌ Gemischte Sprachen
def calculate_duengermenge(plant_id: str) -> float:
    ...

# ❌ camelCase (nicht Python-konform)
def calculateGdd(plantId: str) -> float:
    ...

# ❌ Abkürzungen ohne Kontext
def calc_gdd(pid: str) -> float:
    ...

# ✅ Erlaubte Abkürzungen (etabliert)
def calc_gdd(plant_id: str) -> float:  # calc, vpd, gdd sind OK
    ...
```

<!-- Quelle: Smart-Home-HA-Integration Review A-006 -->
### 2.4 API-Response-Konsistenz

Externe Consumer (Home Assistant Custom Integration, IoT-Gateways, Monitoring) benötigen vorhersagbare JSON-Strukturen. Die folgenden Regeln gelten für alle REST-API-Endpoints:

| Regel | Beschreibung | Beispiel |
|-------|-------------|---------|
| **Pydantic `response_model`** | Alle Endpoints MÜSSEN ein Pydantic `response_model` deklarieren. Keine rohen `dict`- oder `list`-Rückgaben. | `@router.get("/plants", response_model=list[PlantResponse])` |
| **Fehler-Responses** | Strukturiertes JSON mit `detail`-Feld (FastAPI `HTTPException`). Kein Freitext, keine HTML-Fehlerseiten. | `{"detail": "Plant not found"}` |
| **Datumsformat** | ISO 8601 mit UTC und Z-Suffix. Pydantic serialisiert `datetime` automatisch korrekt. | `"2026-02-27T14:30:00Z"` |
| **Pagination** | Konsistente Felder: `items`, `total`, `page`, `page_size`. | `{"items": [...], "total": 42, "page": 1, "page_size": 20}` |
| **Optionale Felder** | `null` statt fehlende Keys. Pydantic `Optional`-Felder werden immer serialisiert. | `{"ha_entity_id": null}` |
| **Enum-Werte** | Als String serialisiert (nicht als Integer). Pydantic `use_enum_values=True`. | `"phase": "vegetative"` |

```python
# ✅ Korrekt: response_model mit Pydantic
@router.get("/plants", response_model=list[PlantResponse])
async def list_plants(page: int = 1, page_size: int = 20):
    ...

# ❌ Verboten: rohe dict-Rückgabe
@router.get("/plants")
async def list_plants():
    return {"data": [{"name": "Tomate"}]}  # Kein response_model!

# ❌ Verboten: inkonsistente Pagination
@router.get("/plants")
async def list_plants():
    return {"results": [...], "count": 42}  # "results" statt "items", "count" statt "total"
```

### 2.5 ArangoDB-Namenskonventionen

**Collections, Edges, Attributes**:

```javascript
// ✅ Collections: PascalCase (Plural)
db._create("plants");
db._create("species");
db._create("locations");

// ✅ Edge Collections: PascalCase + descriptive
db._createEdgeCollection("located_in");
db._createEdgeCollection("requires_nutrient");
db._createEdgeCollection("incompatible_with");

// ✅ Document Attributes: snake_case
db.plants.save({
    _key: "plant_001",
    species_id: "tomato_brandywine",
    planted_date: "2026-02-25",
    current_phase: "vegetative",
    gdd_accumulated: 450.5,
    is_active: true
});

// ✅ AQL Queries: English
FOR plant IN plants
    FILTER plant.current_phase == "flowering"
    LET location = FIRST(
        FOR v IN 1..1 OUTBOUND plant located_in
            RETURN v
    )
    RETURN {
        plant: plant,
        location: location.name
    }

// ❌ VERBOTEN - Deutsche Collection-Namen
db._create("pflanzen");  // NIEMALS!
db._create("standorte");  // NIEMALS!
```

**Relationship Types**: `UPPER_SNAKE_CASE`

```javascript
// ✅ Beschreibende Relationship-Namen
db.located_in.save({
    _from: "plants/plant_001",
    _to: "locations/greenhouse_a_slot_12"
});

db.incompatible_with.save({
    _from: "species/tomato",
    _to: "species/potato",
    reason: "Solanaceae family - disease transmission",
    allelopathy_score: -0.8
});

// ❌ VERBOTEN - Deutsche Relationships
db.befindet_sich_in.save(...)  // NIEMALS!
```

---

## 3. Linting- und Formatierungsrichtlinie

### 3.1 Verbindlicher Python-Linting-Stack

**Tools-Matrix**:

| Tool | Version | Zweck | Verpflichtend |
|------|---------|-------|---------------|
| **Ruff** | >= 0.1.9 | All-in-One Linter (ersetzt Flake8, isort, etc.) | ✅ Ja |
| **Black** | >= 23.12.0 | Code Formatter (unforgiving) | ✅ Ja |
| **mypy** | >= 1.8.0 | Static Type Checker | ✅ Ja |
| **Bandit** | >= 1.7.5 | Security Linter | ⚠️ Empfohlen |
| **Safety** | >= 3.0.0 | Dependency Vulnerability Scanner | ⚠️ Empfohlen |
| **Pylint** | - | Redundant mit Ruff | ❌ Nicht nutzen |
| **Flake8** | - | Durch Ruff ersetzt | ❌ Nicht nutzen |

### 3.2 pyproject.toml Konfiguration

**Komplette Konfiguration**:

```toml
# pyproject.toml
[project]
name = "agrotech-backend"
version = "1.0.0"
description = "Agrotech Plant Care Backend API"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pyarango>=2.0.2",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.9",
    "black>=23.12.0",
    "mypy>=1.8.0",
    "pytest>=7.4.3",
    "pytest-cov>=4.1.0",
    "bandit>=1.7.5",
    "safety>=3.0.0",
]

# ========== RUFF CONFIGURATION ==========
[tool.ruff]
target-version = "py314"
line-length = 100
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "C",      # flake8-comprehensions
    "B",      # flake8-bugbear
    "UP",     # pyupgrade
    "N",      # pep8-naming
    "YTT",    # flake8-2020
    "ASYNC",  # flake8-async
    "S",      # flake8-bandit (security)
    "BLE",    # flake8-blind-except
    "A",      # flake8-builtins
    "COM",    # flake8-commas
    "C4",     # flake8-comprehensions
    "DTZ",    # flake8-datetimez
    "T10",    # flake8-debugger
    "EM",     # flake8-errmsg
    "ISC",    # flake8-implicit-str-concat
    "ICN",    # flake8-import-conventions
    "G",      # flake8-logging-format
    "PIE",    # flake8-pie
    "T20",    # flake8-print
    "PT",     # flake8-pytest-style
    "Q",      # flake8-quotes
    "RSE",    # flake8-raise
    "RET",    # flake8-return
    "SLF",    # flake8-self
    "SIM",    # flake8-simplify
    "TID",    # flake8-tidy-imports
    "ARG",    # flake8-unused-arguments
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented-out code)
    "PL",     # pylint
    "TRY",    # tryceratops
    "RUF",    # ruff-specific rules
]
ignore = [
    "E501",   # Line too long (handled by Black)
    "COM812", # Trailing comma (conflicts with Black)
    "ISC001", # Single-line-implicit-string-concatenation (conflicts with Black)
]
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    ".eggs",
    "*.egg-info",
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports OK in __init__.py
"tests/**/*.py" = [
    "S101",   # Use of assert OK in tests
    "ARG",    # Unused function args OK in tests
    "PLR2004" # Magic values OK in tests
]

[tool.ruff.mccabe]
max-complexity = 10

[tool.ruff.isort]
known-first-party = ["agrotech"]
force-single-line = true
force-sort-within-sections = true

[tool.ruff.pydocstyle]
convention = "google"

# ========== BLACK CONFIGURATION ==========
[tool.black]
line-length = 100
target-version = ["py314"]
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | __pycache__
  | build
  | dist
)/
'''

# ========== MYPY CONFIGURATION ==========
[tool.mypy]
python_version = "3.14"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
pretty = true
show_error_codes = true
show_error_context = true

# Ignore missing imports for third-party libs
[[tool.mypy.overrides]]
module = [
    "pyArango.*",
    "celery.*",
    "prometheus_client.*",
]
ignore_missing_imports = true

# ========== PYTEST CONFIGURATION ==========
[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=agrotech",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=80",
]
testpaths = ["tests"]
pythonpath = ["src"]

# ========== COVERAGE CONFIGURATION ==========
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/migrations/*",
]

[tool.coverage.report]
precision = 2
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "@(abc\\.)?abstractmethod",
]

# ========== BANDIT CONFIGURATION ==========
[tool.bandit]
exclude_dirs = ["/tests"]
skips = ["B101"]  # assert_used (OK in tests)

# ========== SAFETY CONFIGURATION ==========
# safety check --json
```

### 3.3 Pre-Commit Hooks

**.pre-commit-config.yaml**:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: check-toml
      - id: debug-statements
      - id: mixed-line-ending

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.5.0
          - types-redis
        args: [--strict, --ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
        additional_dependencies: ["bandit[toml]"]

  - repo: https://github.com/python-poetry/poetry
    rev: 1.7.0
    hooks:
      - id: poetry-check
      - id: poetry-lock
        args: [--no-update]

  - repo: local
    hooks:
      - id: safety
        name: safety
        entry: safety check --json
        language: system
        pass_filenames: false
```

**Installation & Nutzung**:

```bash
# Pre-Commit installieren
pip install pre-commit

# Hooks installieren
pre-commit install

# Manuell auf allen Dateien ausführen
pre-commit run --all-files

# Hooks bei Commit ausführen (automatisch)
git commit -m "Add irrigation service"
# Output: Ruff, Black, mypy laufen automatisch
```

### 3.4 IDE-Integration (VS Code)

**.vscode/settings.json**:

```json
{
  // Python Interpreter
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  
  // Ruff
  "ruff.enable": true,
  "ruff.lint.run": "onSave",
  "ruff.organizeImports": true,
  
  // Black
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  
  // Format on Save
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll": true
  },
  
  // mypy
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.mypyArgs": [
    "--strict",
    "--ignore-missing-imports",
    "--show-error-codes"
  ],
  
  // Type Checking Mode
  "python.analysis.typeCheckingMode": "strict",
  
  // Editor Settings
  "editor.rulers": [100],
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  
  // Python-specific
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

**.vscode/extensions.json** (Empfohlene Extensions):

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-python.black-formatter",
    "matangover.mypy",
    "tamasfe.even-better-toml"
  ]
}
```

---

## 4. Typisierungsrichtlinie

### 4.1 Type Hints Verpflichtungen

**Alle öffentlichen Funktionen**:

```python
# ✅ KORREKT - Vollständige Type Hints
from collections.abc import Sequence
from datetime import date

def get_plants_by_phase(
    phase: str,
    location_id: str | None = None,
    limit: int = 100
) -> Sequence[Plant]:
    """
    Retrieve plants filtered by growth phase.
    
    Args:
        phase: Growth phase (seedling, vegetative, flowering, harvest)
        location_id: Optional location filter
        limit: Maximum number of results
    
    Returns:
        Sequence of Plant objects
    """
    ...

# ❌ VERBOTEN - Fehlende Type Hints
def get_plants_by_phase(phase, location_id=None, limit=100):
    ...
```

**Pydantic Models** (Python 3.14):

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from uuid import UUID

class PlantCreate(BaseModel):
    """Schema for creating a new plant."""
    
    species_id: UUID = Field(
        ...,
        description="UUID of the plant species"
    )
    location_id: UUID = Field(
        ...,
        description="UUID of the location"
    )
    planted_date: date = Field(
        default_factory=date.today,
        description="Date when planted"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "species_id": "550e8400-e29b-41d4-a716-446655440000",
                "location_id": "660e8400-e29b-41d4-a716-446655440001",
                "planted_date": "2026-02-25"
            }
        }
    )

class PlantResponse(BaseModel):
    """Schema for plant API responses."""
    
    id: UUID
    species_name: str
    current_phase: str
    gdd_accumulated: float
    is_active: bool
    
    model_config = ConfigDict(
        from_attributes=True,
        strict=True
    )
```

**Type Aliases (Python 3.14)**:

```python
# Neue Syntax in Python 3.14
type PlantID = str
type SpeciesID = str
type LocationID = str
type TemperatureCelsius = float
type GDD = float

def calculate_gdd(
    plant_id: PlantID,
    temp_min: TemperatureCelsius,
    temp_max: TemperatureCelsius,
    base_temp: TemperatureCelsius
) -> GDD:
    """Calculate Growing Degree Days."""
    avg_temp = (temp_min + temp_max) / 2
    return max(0, avg_temp - base_temp)
```

**Generic Types**:

```python
from collections.abc import Sequence
from typing import TypeVar, Protocol

T = TypeVar("T")

class Repository[T](Protocol):
    """Generic repository interface."""
    
    def get_by_id(self, id: str) -> T | None:
        ...
    
    def list_all(self, limit: int = 100) -> Sequence[T]:
        ...
    
    def create(self, entity: T) -> T:
        ...

class PlantRepository(Repository[Plant]):
    """Plant-specific repository implementation."""
    
    def get_by_id(self, id: str) -> Plant | None:
        ...
```

### 4.2 mypy Strict Mode

**mypy.ini** (alternativ zu pyproject.toml):

```ini
[mypy]
python_version = 3.14
strict = True
warn_return_any = True
warn_unused_configs = True

# Keine impliziten Any-Typen
disallow_any_unimported = True
disallow_any_expr = False  # Zu strikt für Produktion
disallow_any_decorated = False  # Zu strikt für FastAPI
disallow_any_explicit = False
disallow_any_generics = True
disallow_subclassing_any = True

# Function Definitions
disallow_untyped_calls = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True

# Optionals
no_implicit_optional = True
strict_optional = True

# Warnings
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_return_any = True
warn_unreachable = True

# Misc
strict_equality = True
strict_concatenate = True

[mypy-tests.*]
disallow_untyped_defs = False  # Tests dürfen weniger strikt sein
```

**Beispiel: mypy-Fehler beheben**:

```python
# ❌ mypy-Fehler: Missing return statement
def get_plant(plant_id: str) -> Plant:
    if plant_id in cache:
        return cache[plant_id]
    # Fehlt: return für else-Fall!

# ✅ Korrigiert
def get_plant(plant_id: str) -> Plant | None:
    if plant_id in cache:
        return cache[plant_id]
    return None

# ❌ mypy-Fehler: Implicit Any
def process_data(data):  # data hat Typ Any!
    return data.get("value")

# ✅ Korrigiert
def process_data(data: dict[str, Any]) -> Any:
    return data.get("value")
```

---

## 5. CI/CD-Integration

### 5.1 GitHub Actions Workflow

**.github/workflows/python-lint.yml**:

```yaml
name: Python Code Quality

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.14
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run Ruff (Linting)
        run: |
          ruff check . --output-format=github
      
      - name: Run Ruff (Formatting Check)
        run: |
          ruff format --check .
      
      - name: Run Black (Formatting Check)
        run: |
          black --check --diff .
      
      - name: Run mypy (Type Checking)
        run: |
          mypy .
      
      - name: Run Bandit (Security)
        run: |
          bandit -r . -f json -o bandit-report.json
      
      - name: Run Safety (Dependency Check)
        run: |
          safety check --json > safety-report.json
        continue-on-error: true  # Warnings nicht blockieren
      
      - name: Upload Security Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json
  
  test:
    needs: lint
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.14
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run Tests with Coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=html
      
      - name: Upload Coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
      
      - name: Check Coverage Threshold
        run: |
          COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
          echo "Coverage: $COVERAGE%"
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage below 80%!"
            exit 1
          fi
```

### 5.2 GitLab CI Pipeline

**.gitlab-ci.yml**:

```yaml
stages:
  - lint
  - test
  - security
  - build

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - .venv/

before_script:
  - python -m venv .venv
  - source .venv/bin/activate
  - pip install -e ".[dev]"

lint:ruff:
  stage: lint
  script:
    - ruff check .
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'

lint:format:
  stage: lint
  script:
    - black --check --diff .
    - ruff format --check .
  allow_failure: false

lint:mypy:
  stage: lint
  script:
    - mypy .
  allow_failure: false

test:unit:
  stage: test
  script:
    - pytest --cov=. --cov-report=term --cov-report=xml
    - coverage report --fail-under=80
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

security:bandit:
  stage: security
  script:
    - bandit -r . -f json -o bandit-report.json
  artifacts:
    reports:
      sast: bandit-report.json
  allow_failure: true

security:safety:
  stage: security
  script:
    - safety check --json > safety-report.json
  artifacts:
    paths:
      - safety-report.json
  allow_failure: true
```

### 5.3 Branch Protection Rules

**GitHub Branch Protection (main)**:

```yaml
# .github/settings.yml (mit probot/settings)
branches:
  - name: main
    protection:
      required_pull_request_reviews:
        required_approving_review_count: 1
        dismiss_stale_reviews: true
        require_code_owner_reviews: true
      
      required_status_checks:
        strict: true
        contexts:
          - "lint"
          - "test"
          - "Python Code Quality / lint"
          - "Python Code Quality / test"
      
      enforce_admins: true
      required_linear_history: true
      allow_force_pushes: false
      allow_deletions: false
      
      restrictions:
        users: []
        teams: ["backend-team"]
```

---

## 6. Code-Review-Richtlinien

### 6.1 Pull Request Checkliste

**PR-Template** (.github/pull_request_template.md):

```markdown
## Description
<!-- Briefly describe what this PR does -->

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Checklist
- [ ] Code follows English naming conventions
- [ ] All functions have type hints
- [ ] Docstrings added (Google style)
- [ ] Ruff linting passes
- [ ] Black formatting applied
- [ ] mypy type checking passes
- [ ] Tests added/updated
- [ ] Coverage ≥ 80%
- [ ] No commented-out code
- [ ] No debug prints (`print()`, `console.log()`)
- [ ] Commit messages in English

## Testing
<!-- Describe the tests you ran -->

## Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

## Related Issues
Closes #issue_number
```

### 6.2 Code-Review-Fokus

**Automatisch geprüft** (nicht im Review diskutieren):
- ✅ Code-Formatierung (Black)
- ✅ Import-Sortierung (Ruff)
- ✅ Type Hints (mypy)
- ✅ Linting-Fehler (Ruff)

**Manuell prüfen** (Reviewer-Fokus):
- ❓ Logik-Fehler
- ❓ Performance-Probleme
- ❓ Security-Schwachstellen
- ❓ Architektur-Entscheidungen
- ❓ Edge-Cases
- ❓ Testabdeckung (fachlich)

**Verbotene Review-Kommentare**:

```
❌ "Bitte formatiere den Code"
   → Automatisch durch Black

❌ "Imports sind nicht sortiert"
   → Automatisch durch Ruff

❌ "Hier fehlt ein Type Hint"
   → Blockiert durch mypy im CI

✅ "Diese Logik könnte einen Deadlock verursachen bei hoher Last"
   → Fachliches Problem, sinnvoller Review-Kommentar
```

### 6.3 Commit Message Konventionen

**Conventional Commits** (Englisch):

```bash
# ✅ KORREKT
git commit -m "feat: add irrigation scheduling service"
git commit -m "fix: prevent duplicate GDD calculations"
git commit -m "refactor: simplify plant repository query logic"
git commit -m "docs: update API documentation for harvest endpoints"
git commit -m "test: add unit tests for VPD calculator"
git commit -m "chore: update dependencies to latest versions"

# ❌ VERBOTEN - Deutsche Commits
git commit -m "feat: Bewässerungsplanung hinzugefügt"
git commit -m "fix: Doppelte GDD-Berechnung verhindert"

# ❌ VERBOTEN - Unklare Commits
git commit -m "WIP"
git commit -m "fix stuff"
git commit -m "updates"
```

**Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: Neue Features
- `fix`: Bug-Fixes
- `refactor`: Code-Refactoring
- `docs`: Dokumentations-Änderungen
- `test`: Test-Änderungen
- `chore`: Build/Tooling-Änderungen
- `perf`: Performance-Verbesserungen
- `style`: Code-Style (sollte nicht nötig sein mit Black!)

---

## 7. Dokumentationsstandards

### 7.1 Docstring-Konvention (Google Style)

**Funktionen**:

```python
def calculate_irrigation_amount(
    plant_id: str,
    substrate_moisture: float,
    target_moisture: float
) -> float:
    """
    Calculate the required irrigation amount to reach target moisture.
    
    This function considers substrate type, plant water requirements,
    and current moisture levels to determine optimal irrigation volume.
    
    Args:
        plant_id: UUID of the plant to irrigate
        substrate_moisture: Current substrate moisture in percent (0-100)
        target_moisture: Desired substrate moisture in percent (0-100)
    
    Returns:
        Required irrigation volume in liters
    
    Raises:
        ValueError: If moisture values are outside valid range (0-100)
        PlantNotFoundError: If plant_id does not exist
    
    Examples:
        >>> calculate_irrigation_amount("plant-123", 30.0, 60.0)
        2.5
        
        >>> calculate_irrigation_amount("plant-456", 70.0, 60.0)
        0.0  # No irrigation needed
    
    Note:
        This function assumes substrate field capacity is 80%.
        For hydroponic systems, use calculate_reservoir_refill() instead.
    """
    if not 0 <= substrate_moisture <= 100:
        raise ValueError(f"Moisture must be 0-100, got {substrate_moisture}")
    
    # ... Implementation
```

**Klassen**:

```python
class IrrigationService:
    """
    Service for managing automated irrigation scheduling.
    
    This service coordinates between sensor readings, plant water requirements,
    and irrigation hardware to ensure optimal watering schedules.
    
    Attributes:
        db: ArangoDB connection for plant data
        redis: Redis client for caching irrigation schedules
        scheduler: Celery scheduler for automated tasks
    
    Example:
        >>> service = IrrigationService(db_conn, redis_conn)
        >>> service.schedule_irrigation("greenhouse-a")
        {'scheduled_plants': 12, 'total_water_liters': 45.5}
    """
    
    def __init__(
        self,
        db: Connection,
        redis: Redis,
        scheduler: Celery
    ):
        """
        Initialize the irrigation service.
        
        Args:
            db: ArangoDB connection
            redis: Redis client for caching
            scheduler: Celery instance for task scheduling
        """
        self.db = db
        self.redis = redis
        self.scheduler = scheduler
```

### 7.2 README-Struktur

**README.md** (Englisch, technisch):

```markdown
# Agrotech Backend

Plant care and harvest management system with automated irrigation, growth tracking, and pest management.

## Features

- 🌱 Plant lifecycle management (seed to harvest)
- 💧 Automated irrigation scheduling
- 🌡️ Climate monitoring with VPD optimization
- 🐛 Integrated Pest Management (IPM)
- 📊 Harvest predictions with GDD calculations

## Requirements

- Python 3.14+
- ArangoDB 3.11+
- Redis 7.2+
- Kubernetes 1.28+ (production)

## Installation

### Development

```bash
# Clone repository
git clone https://github.com/agrotech/backend.git
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

### Production (Docker)

```bash
docker build -t agrotech/backend:latest .
docker run -p 8000:8000 agrotech/backend:latest
```

## Configuration

See `.env.example` for required environment variables.

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Development

### Code Quality

This project enforces strict code quality standards:

- **Ruff**: Linting and code formatting
- **Black**: Code formatting
- **mypy**: Static type checking
- **Coverage**: Minimum 80% test coverage

Run quality checks:

```bash
# Run all checks
make lint

# Auto-fix issues
make format

# Type checking
make typecheck
```

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov

# Specific test
pytest tests/test_irrigation.py
```

## Project Structure

```
backend/
├── src/
│   └── agrotech/
│       ├── api/          # FastAPI endpoints
│       ├── services/     # Business logic
│       ├── repositories/ # Data access
│       ├── models/       # Pydantic models
│       └── utils/        # Helper functions
├── tests/
├── helm/                 # Kubernetes Helm charts
├── .github/              # GitHub Actions
├── pyproject.toml        # Project configuration
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

Proprietary - All rights reserved

## Support

- Documentation: https://docs.agrotech.example.com
- Issues: https://github.com/agrotech/backend/issues
- Email: support@agrotech.example.com
```

---

## 8. Spezielle Regelungen

### 8.1 Ausnahmen für Legacy-Code

**Grandfathering-Regel**:

Existierender Code mit deutschen Identifiern darf **temporär** bleiben, MUSS aber:

1. **Dokumentiert werden**:
```python
# LEGACY: German naming - scheduled for refactoring in Q3 2026
def berechne_gdd(pflanzen_id: str) -> float:
    """DEPRECATED: Use calculate_gdd() instead."""
    warnings.warn(
        "berechne_gdd is deprecated, use calculate_gdd",
        DeprecationWarning,
        stacklevel=2
    )
    return calculate_gdd(pflanzen_id)
```

2. **Neue Implementierung parallel bereitstellen**:
```python
def calculate_gdd(plant_id: str) -> float:
    """Calculate Growing Degree Days (GDD) for a plant."""
    # New implementation
    ...
```

3. **Migration-Plan haben**:
```markdown
## Legacy Code Migration Plan

### berechne_gdd → calculate_gdd
- **Status**: Deprecated in v1.1.0
- **Removal**: v2.0.0 (Q3 2026)
- **Migration**: Search & Replace all usages
- **Breaking Change**: Yes
```

### 8.2 Frontend TypeScript/JavaScript

**Gleiche Regeln gelten**:

```typescript
// ✅ KORREKT - English naming
interface Plant {
    id: string;
    speciesName: string;
    currentPhase: string;
    gddAccumulated: number;
}

function calculateVpd(temperature: number, humidity: number): number {
    const saturationVaporPressure = 0.6108 * Math.exp(
        (17.27 * temperature) / (temperature + 237.3)
    );
    const actualVaporPressure = saturationVaporPressure * humidity / 100;
    return saturationVaporPressure - actualVaporPressure;
}

// ❌ VERBOTEN - German naming
interface Pflanze {
    id: string;
    artName: string;
    aktuellePhase: string;
}
```

**ESLint + Prettier Konfiguration**:

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "project": "./tsconfig.json"
  },
  "rules": {
    "@typescript-eslint/explicit-function-return-type": "error",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "no-console": ["error", { "allow": ["warn", "error"] }]
  }
}
```

---

## 9. Akzeptanzkriterien

### Definition of Done

- [ ] **Sprachkonformität**
  - [ ] Kein deutscher Identifier im Code
  - [ ] Alle Docstrings auf Englisch
  - [ ] Commit Messages auf Englisch
  - [ ] API-Dokumentation auf Englisch

- [ ] **Linting & Formatting**
  - [ ] Ruff-Check ohne Fehler
  - [ ] Black-Formatierung angewendet
  - [ ] mypy Strict Mode ohne Fehler
  - [ ] Pre-Commit Hooks installiert

- [ ] **Type Safety**
  - [ ] Alle öffentlichen Funktionen mit Type Hints
  - [ ] Pydantic Models für API-Schemas
  - [ ] Keine impliziten Any-Typen

- [ ] **CI/CD**
  - [ ] GitHub Actions Workflow aktiv
  - [ ] Branch Protection Rules gesetzt
  - [ ] Coverage ≥ 80%
  - [ ] Bandit Security Scan

- [ ] **Dokumentation**
  - [ ] README.md auf Englisch (technisch)
  - [ ] Google-Style Docstrings
  - [ ] OpenAPI-Dokumentation generiert

### Testszenarien

#### Szenario 1: Deutscher Code wird abgelehnt

```bash
# 1. Developer schreibt deutschen Code
cat > irrigation.py << EOF
def berechne_wassermenge(pflanzen_id: str) -> float:
    return 2.5
EOF

# 2. Pre-Commit Hook schlägt fehl
git add irrigation.py
git commit -m "Add irrigation function"

# Output:
# Ruff....................................................................Failed
# - hook id: ruff
# - exit code: 1
# 
# irrigation.py:1:5: N816 Variable name should be in snake_case
# irrigation.py:1:32: N803 Argument name should be in snake_case
```

#### Szenario 2: Fehlende Type Hints werden erkannt

```python
# ❌ Code ohne Type Hints
def calculate_gdd(plant_id, base_temp):
    return 42.0
```

```bash
# mypy schlägt fehl
$ mypy .
irrigation.py:1: error: Function is missing a type annotation
```

#### Szenario 3: CI blockiert Merge bei Violations

```yaml
# Pull Request #123
Status: ❌ Failed

lint / Ruff Check: ✅ Passed
lint / Black Format: ❌ Failed
  - Code not formatted correctly
lint / mypy Type Check: ❌ Failed
  - Missing type hints in calculate_gdd()
test / Coverage: ❌ Failed
  - Coverage 65% < 80% threshold

Merging is blocked by required status checks.
```

---

## 10. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|--------|------------|-------------------|------------|
| **Gemischte Sprachen** | Code schwer wartbar, Onboarding verzögert | Hoch | Strikte CI-Checks |
| **Fehlende Type Hints** | Runtime-Fehler, schwache IDE-Unterstützung | Mittel | mypy Strict Mode |
| **Inkonsistente Formatierung** | Merge-Konflikte, Review-Overhead | Hoch | Black + Pre-Commit |
| **Keine Linting** | Bugs in Production, technische Schulden | Hoch | Ruff im CI/CD |
| **Schlechte Dokumentation** | Wissenssilos, langsames Onboarding | Mittel | Docstring-Pflicht |

---

## 11. Migrations-Roadmap

### Phase 1: Tool-Setup (Woche 1)

- [ ] pyproject.toml konfigurieren
- [ ] Pre-Commit Hooks einrichten
- [ ] GitHub Actions Workflow erstellen
- [ ] Branch Protection aktivieren

### Phase 2: Legacy-Code-Analyse (Woche 2-3)

- [ ] Scan nach deutschen Identifiern
- [ ] Priorisierung nach Wichtigkeit
- [ ] Deprecation Warnings hinzufügen
- [ ] Migration-Plan erstellen

### Phase 3: Graduelle Migration (Woche 4-12)

- [ ] Kritische Module zuerst
- [ ] Parallele Implementierung (alt + neu)
- [ ] Schrittweise Migration der Aufrufe
- [ ] Tests aktualisieren

### Phase 4: Enforcement (Woche 13+)

- [ ] CI blockiert deutsche Identifier
- [ ] Legacy-Code entfernen
- [ ] Team-Training
- [ ] Dokumentation aktualisieren

---

## Anhang A: Tool-Referenz

### Ruff Commands

```bash
# Linting
ruff check .                    # Check all files
ruff check --fix .              # Auto-fix issues
ruff check --watch .            # Watch mode

# Formatting
ruff format .                   # Format all files
ruff format --check .           # Check formatting without changes

# Specific rules
ruff check --select E,W,F .     # Only pycodestyle + pyflakes
ruff check --ignore E501 .      # Ignore line length
```

### Black Commands

```bash
# Format
black .                         # Format all files
black --check .                 # Check without changes
black --diff .                  # Show diffs

# Line length
black --line-length 100 .

# Specific files
black src/ tests/
```

### mypy Commands

```bash
# Type check
mypy .                          # Check all files
mypy --strict .                 # Strict mode
mypy --show-error-codes .       # Show error codes

# Specific module
mypy src/agrotech/irrigation.py

# Generate report
mypy --html-report ./mypy-report .
```

---

## Anhang B: Checkliste für neue Repositories

```markdown
## New Repository Setup Checklist

- [ ] Create repository from template
- [ ] Add pyproject.toml with Ruff/Black/mypy config
- [ ] Add .pre-commit-config.yaml
- [ ] Add GitHub Actions workflow
- [ ] Configure branch protection (main)
- [ ] Add CODEOWNERS file
- [ ] Add README.md (English)
- [ ] Add CONTRIBUTING.md (English)
- [ ] Install pre-commit hooks
- [ ] Run initial `ruff check --fix .`
- [ ] Run initial `black .`
- [ ] Run initial `mypy .`
- [ ] Create first PR to verify CI
```

---

**Dokumenten-Ende**

**Version**: 2.0
**Status**: Produktionsreif
**Letzte Aktualisierung**: 2026-02-25
**Review**: Pending
**Genehmigung**: Pending