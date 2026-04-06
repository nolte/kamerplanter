---
name: check-architecture
description: "Prueft ein Backend-Modul oder Frontend-Verzeichnis auf NFR-001-Konformitaet: 5-Schichten-Architektur, Layer-Verletzungen, Namenskonventionen (Service/Engine/Repository). Nutze diesen Skill nach der Implementierung neuer Features oder bei Code-Reviews."
argument-hint: "[Pfad zum Modul, z.B. src/backend/app/domain/services/substrate_service.py oder REQ-nnn]"
disable-model-invocation: true
---

# Architektur-Check (NFR-001): $ARGUMENTS

## Schritt 1: Ziel-Dateien bestimmen

Falls `$ARGUMENTS` ein REQ-Identifier ist (z.B. `REQ-013`):
- Suche alle zugehoerigen Dateien via Glob:
  - `src/backend/app/api/v1/*/router.py` (Router-Dateien)
  - `src/backend/app/domain/models/*.py`
  - `src/backend/app/domain/services/*.py`
  - `src/backend/app/domain/engines/*.py`
  - `src/backend/app/data_access/repositories/*.py`
  - Filtere nach thematisch passendem Namen

Falls `$ARGUMENTS` ein Dateipfad ist:
- Lies die angegebene Datei direkt

Lies die NFR als Referenz: `spec/nfr/NFR-001_Separation-of-Concerns.md` (erste 80 Zeilen fuer Layer-Definitionen)

## Schritt 2: Layer-Zuordnung pruefen

Ordne jede gelesene Datei einer der 5 Schichten zu:

| Layer | Erlaubte Importe | Verbotene Importe |
|-------|-----------------|-------------------|
| **1. API (router.py)** | Services, Schemas, Auth-Dependencies | Repositories, Engines, DB-Driver direkt |
| **2. Service** | Engines, Repositories | FastAPI, Request/Response, DB-Driver direkt |
| **3. Engine/Calculator** | Domain Models, Pure Python | Services, Repositories, FastAPI |
| **4. Repository** | DB-Driver (python-arango), Domain Models | Services, Engines, FastAPI |
| **5. Domain Models** | Pydantic BaseModel, enums | Alle obigen Schichten |

## Schritt 3: Namenskonventionen pruefen

Prüfe die folgenden Konventionen (NFR-001 + BACKEND.md):

- **Router-Dateien:** In `api/v1/<entity>/router.py`, Prefix `/<entity>`
- **Services:** Suffix `*Service`, Methoden sind `async`, orchestrieren Engines + Repositories
- **Engines:** Suffix `*Engine` oder `*Calculator`, pure Business Logic, kein async noetig
- **Repositories:** Suffix `*Repository`, nur AQL-Queries, kein Business Logic
- **Tenant-Scoping:** Alle tenant-spezifischen Endpoints unter `/t/{slug}/`, globale Stammdaten unter `/api/v1/`

## Schritt 4: Violations identifizieren

Suche konkret nach diesen Anti-Patterns:

```python
# ❌ Layer-Violation: Repository-Import im Router
from app.data_access.repositories.plant_repository import PlantRepository

# ❌ Business Logic im Repository
def get_active_plants(self):
    # Filterlogik gehoert in Engine/Service, nicht Repository
    return [p for p in self._query_all() if p.status == "active"]

# ❌ DB-Driver direkt im Service
from arango import ArangoClient
db = ArangoClient().db(...)

# ❌ FastAPI-Dependency im Engine
from fastapi import Depends
```

## Schritt 5: Report ausgeben

```markdown
# Architektur-Review: {Modul/Pfad}

## Layer-Zuordnung
{Tabelle: Datei → Layer → Korrekt/Verletzung}

## Gefundene Violations
{Nummerierte Liste mit Dateipfad:Zeile und Beschreibung}

## Namenskonventions-Check
{Abweichungen von Service/Engine/Repository-Pattern}

## Tenant-Scoping
{Prüfung ob tenant-spezifische Endpoints korrekt unter /t/{slug}/ liegen}

## Bewertung
- ✅ NFR-001-konform / ❌ Violations gefunden (N Probleme)
```

## Hinweis

Style-Guide-Referenz: `spec/style-guides/BACKEND.md` fuer detaillierte Pattern-Beschreibungen.
