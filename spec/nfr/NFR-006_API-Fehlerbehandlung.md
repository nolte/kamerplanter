---

ID: NFR-006
Titel: Strukturierte API-Fehlerbehandlung mit eindeutiger Tracking-ID
Kategorie: API-Design Unterkategorie: Error Handling, Observability Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python, FastAPI, structlog, Pydantic
Status: Genehmigt
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [api, error-handling, observability, traceability, debugging, developer-experience]
Abhängigkeiten: [NFR-001, NFR-003]
Betroffene Module: [ALL]
---

# NFR-006: Strukturierte API-Fehlerbehandlung mit eindeutiger Tracking-ID

## 1. Business Case

### 1.1 User Story

**Als** Frontend-Entwickler
**möchte ich** bei jedem API-Fehler eine eindeutige Tracking-ID und eine verständliche Fehlerbeschreibung erhalten
**um** Fehler schnell an das Backend-Team eskalieren zu können, ohne Log-Dateien selbst durchsuchen zu müssen.

**Als** DevOps Engineer
**möchte ich**, dass jeder API-Fehler eine korrelierbare ID enthält, die in Logs, Monitoring und Alerting wiederverwendet wird
**um** Fehlerursachen über alle Systemschichten hinweg nachvollziehen zu können.

**Als** Endanwender
**möchte ich** bei einem Fehler eine klare Meldung und eine Referenznummer sehen
**um** dem Support eine präzise Fehlerbeschreibung geben zu können.

### 1.2 Geschäftliche Motivation

Ohne strukturierte Fehlerbehandlung:

1. **Support-Aufwand steigt** – Fehler können nicht reproduziert oder nachverfolgt werden
2. **MTTR (Mean Time to Resolve) erhöht sich** – Entwickler durchsuchen Logs manuell
3. **Kundenzufriedenheit sinkt** – kryptische Fehlermeldungen frustrieren Anwender
4. **Sicherheitsrisiken** – interne Details (Stack-Traces, DB-Fehlermeldungen) werden nach außen preisgegeben

### 1.3 Fachliche Beschreibung

Jede API-Antwort mit HTTP-Statuscode >= 400 muss ein einheitliches Fehler-Schema verwenden. Die Fehlermeldung muss:

- **Maschinenlesbar** sein (fester Error-Code)
- **Menschenlesbar** sein (beschreibende Nachricht)
- **Nachverfolgbar** sein (eindeutige `error_id`)
- **Sicher** sein (keine internen Details wie Stack-Traces oder DB-Queries preisgeben)

Praktisches Beispiel:

> **Szenario**: Ein Gärtner versucht, eine Pflanze mit einem ungültigen `species_key` anzulegen.
> **Erwartung**: Die API antwortet mit HTTP 422, einem Error-Code `ENTITY_NOT_FOUND`, einer lesbaren Nachricht und einer `error_id`, die im Backend-Log korreliert werden kann.

---

## 2. Fehler-Response-Schema

### 2.1 Standardisiertes Error-Format

Jede Fehlerantwort folgt diesem Schema:

```json
{
  "error_id": "err_7f3a9b2c-1d4e-4f5a-8b6c-9d0e1f2a3b4c",
  "error_code": "VALIDATION_ERROR",
  "message": "Die angegebene Spezies existiert nicht.",
  "details": [
    {
      "field": "species_key",
      "reason": "Kein Eintrag mit Key 'xyz-123' gefunden.",
      "code": "ENTITY_NOT_FOUND"
    }
  ],
  "timestamp": "2026-02-26T14:30:00.000Z",
  "path": "/api/v1/plant-instances",
  "method": "POST"
}
```

`entity` fehlt hier bewusst: Das Feld setzt ausschließlich `NotFoundError` (HTTP
404), siehe § 2.2a. Ein Validierungsfehler, der einen nicht auflösbaren Fremd-Key
als Detail meldet, trägt es nicht — sonst hinge der Wert daran, welcher Code-Pfad
die Prüfung zufällig ausgelöst hat.

### 2.2 Pydantic-Schema

```python
# app/common/error_schemas.py
from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str | None = None
    reason: str
    code: str
    entity: str | None = None


class ErrorResponse(BaseModel):
    error_id: str = Field(
        description="Eindeutige ID zur Nachverfolgung (Format: err_<uuid4>)"
    )
    error_code: str = Field(
        description="Maschinenlesbarer Fehlercode (z.B. VALIDATION_ERROR)"
    )
    message: str = Field(
        description="Menschenlesbare Fehlerbeschreibung"
    )
    details: list[ErrorDetail] = Field(default_factory=list)
    timestamp: datetime
    path: str
    method: str
```

### 2.2a `entity` — welche Ressource fehlt (optional)

`ENTITY_NOT_FOUND` allein sagt nicht, **was** fehlt. Eine Route, die erst eine
Elternressource und dann eine Kindressource auflöst, antwortet in beiden Fällen
mit demselben `error_code` und demselben HTTP-Status; unterschieden haben sie
sich bislang nur in der englischsprachigen `message` — und die darf ein Client
nicht parsen (NFR-003: API-Texte Englisch, UI übersetzt).

Deshalb trägt jeder `NotFoundError` — einschließlich aller Unterklassen wie
`AttachmentNotFoundError` — den Entitätsnamen **strukturiert** in
`details[0].entity`:

| Fehlerquelle | `error_code` | `details[0].entity` |
|---|---|---|
| `NotFoundError("Task", key)` | `ENTITY_NOT_FOUND` | `task` |
| `AttachmentNotFoundError(id)` | `ENTITY_NOT_FOUND` | `attachment` |

Regeln:

- **Additiv.** `error_code` und Status bleiben unverändert; ein Client, der auf
  `ENTITY_NOT_FOUND` matcht, bricht nicht. Das Feld ist optional — es fehlt bei
  jedem Detail, das kein Nicht-gefunden beschreibt (Validierungsfehler etwa).
- **Normalisiert, nicht durchgereicht.** Die Aufrufstellen schreiben den Namen
  uneinheitlich (`"Task"`, `"attachment"`, `"PlantInstance"`, `"memberships"`,
  `"nutrient plan phase entry"`). `NotFoundError.__init__` faltet ihn über
  `normalise_entity_name()` nach `snake_case`, damit der Wert nicht davon abhängt,
  wie ein Raiser formuliert ist, und idempotent bleibt.
- **Für alle, nicht für eine Unterklasse.** Ein Feld, das nur ein Zweig setzt,
  wird zur Ausnahme, die jeder Client gesondert behandeln muss.

Gegenbeispiel aus der Praxis (#1437): `PhotoUpload` entfernte einen Fotoeintrag
bei **jedem** 404 aus der Liste. War die *Aufgabe* verschwunden, wurde nichts
gelöscht, der Eintrag verschwand trotzdem, und das Attachment verwaiste. Der
Client de-staged jetzt nur noch bei `entity === "attachment"`.

#### Geschlossenes Vokabular (#1465)

Normalisieren faltet die *Schreibweise*, nicht die *Bedeutung*. Gemessen über
`app/` ein Issue nach #1437: 146 Aufrufstellen mit Literal schrieben **59**
verschiedene Namen — Prosa (`"LifecycleConfig for species"`), Plurale
(`"tenants"`, `"memberships"`) und Groß-/Kleinschreibungsvarianten — dazu 17
Stellen, die zur Laufzeit einen *Collection*-Namen durchreichten. Ein Client, der
auf `entity === "tenant"` verzweigte, verfehlte sechs Raiser.

**Die Regel, einmal formuliert:** ein veröffentlichter Wert ist der Klassenname
eines Domänenmodells unter `app/domain/models/`, über `normalise_entity_name()`
nach `snake_case` gefaltet — plus die Ausnahmen unten. Nie ein Collection-Name,
nie ein Plural, nie Prosa.

Die Menge ist eine **Obermenge**: der Lauf über das Modellpaket erfasst auch
Request-/Response-Projektionen, die nie ein 404 benennen. Zugesichert ist die
andere Richtung — außerhalb der Menge wird nichts veröffentlicht. Ein Client
vergleicht deshalb exakt und behandelt einen unbekannten Wert wie „keine
Angabe"; eine zweite, handgepflegte Liste „tatsächlich vorkommender" Namen wäre
genau die Kopie, die hier abgeschafft wurde.

Die Menge wird **abgeleitet, nicht gepflegt**: `app/domain/entity_names.py`
(`entity_names()`) liest die Modellklassen; eine Liste von Namen wäre die 60.
Kopie einer Tatsache, die die Klassen bereits tragen, und würde genauso lautlos
driften. Durchgesetzt wird sie von `tests/unit/guards/test_entity_name_vocabulary.py`
über jede Aufrufstelle, jeden Entitätsnamen-Parameter der geteilten Guards, jedes
`_entity_name`-Klassenattribut und jede `NotFoundError`-Unterklasse.

Die Ausnahmen — die einzigen handgeschriebenen Entitätsnamen im Code (der
Test `test_spec_lists_exactly_the_non_model_exceptions` hält diese Tabelle und
`NON_MODEL_ENTITY_NAMES` aneinander):

| `entity` | Warum kein Modell |
|---|---|
| `favorite_target` | Favoriten-Ziel, dessen Key sich in keinem Katalog auflösen lässt; es gibt kein Modell, **weil** die Auflösung fehlschlug (SEC-002: unauflösbar und fremd-mandantig antworten gleich). Seit #1538 sind beide nicht nur gleich *beantwortet*, sondern derselbe Zweig: die Auflösung trägt das Mandantenprädikat, eine für den Aufrufer unsichtbare Zeile löst gar nicht erst auf. |
| `inven_tree_part` | Teil in der entfernten InvenTree-Instanz (REQ-016), hier nicht persistiert. Gefaltet wie die Geschwistermodelle `InvenTreeConnection` / `InvenTreeReference`. |
| `mcp_server` | Der MCP-Endpunkt selbst, der bei abgeschaltetem Feature 404 antwortet (REQ-033) — kein Dokument. |
| `mcp_tool` | Ein dem Dispatcher unbekannter Tool-Name (REQ-033). `McpToolSpec` beschreibt ein *registriertes* Tool, nicht das erfragte. |
| `plant_photo` | `Attachment` in der Galerie-Kategorie (NFR-013). Bewusst von `attachment` getrennt: dieser Wert de-staged im Client ein *Aufgaben*-Foto (#1437). |
| `reference_image` | Referenzbild-Datensatz der Admin-Oberfläche; die Modelle in `reference_image.py` beschreiben den Beschaffungs-*Job*. |
| `resource` | Fail-closed-Rückfall, wenn eine Laufzeit-Collection auf kein Modell zeigt. Bewusst nichtssagend: den Collection-Namen zu spiegeln hieße, Speicherdetails (und bei aufrufergesteuerter Collection: Eingaben) zu veröffentlichen. |
| `session` | Anmeldesitzung, wie `GET /auth/sessions` sie zeigt. Gespeichert als `RefreshToken` (Mechanismus), gelesen als `SessionInfo` (Projektion). |
| `storage_object` | Blob im Objektspeicher (S3/Dateisystem) — unterhalb der Dokumentebene, Key in einem Bucket statt Modell. |

**Additivität.** `error_code` und Status bleiben unverändert; ein Client, der auf
`ENTITY_NOT_FOUND` matcht, bricht nicht. Die *Werte* sind es nicht — neun
veröffentlichte Werte haben sich geändert:

| alt | neu |
|---|---|
| `tenants` | `tenant` |
| `memberships` | `membership` |
| `invitations` | `invitation` |
| `location_assignments` | `location_assignment` |
| `object` | `storage_object` |
| `lifecycle_config_for_species` | `lifecycle_config` |
| `nutrient_profile_for_phase` | `nutrient_profile` |
| `requirement_profile_for_phase` | `requirement_profile` |
| `plant_instance_in_run` | `planting_run_entry` |

Dazu die Collection-Namen, die die generischen Guards zur Laufzeit durchreichten
(`plant_instances`, `cultivars`, …) — sie sind jetzt der Modellname. Nicht
betroffen sind Raiser, deren Prosa bereits auf denselben Wert faltete
(`"nutrient plan phase entry"` → `nutrient_plan_phase_entry`); dort änderte sich
nur die englische `message`.

Gemessen statt angenommen: der einzige Konsument des Feldes im Repository ist
`PhotoUpload.tsx` mit `attachment` und `task` — beide unverändert; unter
`tests/e2e/` prüft keine Zusicherung das Feld.

---

### 2.3 Error-ID-Format

```
err_<uuid4>
```

- Präfix `err_` für einfache Unterscheidung von anderen IDs im System
- UUID v4 für Eindeutigkeit
- Beispiel: `err_7f3a9b2c-1d4e-4f5a-8b6c-9d0e1f2a3b4c`

---

## 3. Error-Codes (Katalog)

### 3.1 Allgemeine Fehler

| HTTP | Error-Code | Beschreibung |
|---|---|---|
| 400 | `BAD_REQUEST` | Anfrage ist syntaktisch fehlerhaft |
| 401 | `UNAUTHORIZED` | Authentifizierung erforderlich oder fehlgeschlagen |
| 403 | `FORBIDDEN` | Autorisierung fehlgeschlagen |
| 404 | `NOT_FOUND` | Ressource nicht gefunden |
| 409 | `CONFLICT` | Konflikt mit bestehendem Zustand (z.B. Duplikat) |
| 422 | `VALIDATION_ERROR` | Eingabedaten sind semantisch ungültig |
| 429 | `RATE_LIMITED` | Zu viele Anfragen |
| 500 | `INTERNAL_ERROR` | Interner Serverfehler |
| 503 | `SERVICE_UNAVAILABLE` | Abhängiger Service nicht erreichbar |

### 3.2 Domänenspezifische Fehler

| HTTP | Error-Code | Beschreibung |
|---|---|---|
| 404 | `ENTITY_NOT_FOUND` | Referenzierte Entität existiert nicht |
| 409 | `DUPLICATE_ENTRY` | Eintrag mit gleichem Schlüssel existiert bereits |
| 409 | `WRITE_CONFLICT` | Gleichzeitiger Schreibvorgang hielt denselben Schlüssel; erneut lesen und wiederholen |
| 422 | `INCOMPATIBLE_SUBSTRATE` | Substrat ist nicht kompatibel mit Spezies |
| 422 | `INCOMPATIBLE_COMPANION` | Mischkultur-Konflikt am Standort |
| 422 | `SLOT_OCCUPIED` | Stellplatz ist bereits belegt |
| 422 | `PHASE_TRANSITION_INVALID` | Ungültiger Phasenübergang |

`WRITE_CONFLICT` ist **nicht** eine Spielart von `DUPLICATE_ENTRY`, auch wenn beide 409 sind.
`DUPLICATE_ENTRY` (ArangoDB-Code 1210) ist eine Aussage **über die Daten**: ein festgeschriebener,
sichtbarer Datensatz belegt den eindeutigen Schlüssel — ein Client darf das als „ein
gleichwertiger Datensatz existiert" lesen und muss seine Eingabe ändern. `WRITE_CONFLICT`
(Code 1200) ist eine Aussage **über die Zeit**: eine gleichzeitige Transaktion hielt denselben
Dokumentschlüssel oder Index-Eintrag, und ob sie festgeschrieben oder zurückgerollt hat, ist
damit gerade nicht gesagt. Die richtige Reaktion ist deshalb erneut lesen und wiederholen, nicht
die Eingabe ändern. Ein Client, der beide Codes gleich behandelt, verliert genau diese
Unterscheidung.

---

## 4. Implementierung

### 4.1 Exception-Hierarchie

```python
# app/common/exceptions.py
import uuid


class AppError(Exception):
    """Basisklasse für alle Anwendungsfehler."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: list[dict] | None = None,
    ):
        self.error_id = f"err_{uuid.uuid4()}"
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


def normalise_entity_name(entity: str) -> str:
    """Faltet "Task" / "PlantInstance" / "memberships" nach snake_case (§ 2.2a).

    Idempotent — ein bereits normalisierter Name kommt unverändert zurück.
    """
    ...


class NotFoundError(AppError):
    def __init__(self, entity: str, key: str):
        super().__init__(
            message=f"{entity} mit Key '{key}' nicht gefunden.",
            error_code="ENTITY_NOT_FOUND",
            status_code=404,
            details=[
                {
                    "field": "key",
                    "reason": f"Kein {entity} mit Key '{key}'.",
                    "code": "ENTITY_NOT_FOUND",
                    # § 2.2a: normalisiert, für *jede* Unterklasse, additiv.
                    "entity": normalise_entity_name(entity),
                }
            ],
        )


class DuplicateError(AppError):
    def __init__(self, entity: str, field: str, value: str):
        super().__init__(
            message=f"{entity} mit {field}='{value}' existiert bereits.",
            error_code="DUPLICATE_ENTRY",
            status_code=409,
            details=[{"field": field, "reason": f"Wert '{value}' ist bereits vergeben.", "code": "DUPLICATE_ENTRY"}],
        )


class ValidationError(AppError):
    def __init__(self, message: str, details: list[dict] | None = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )
```

### 4.2 Exception-Handler (FastAPI)

```python
# app/common/error_handlers.py
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.exceptions import AppError

logger = structlog.get_logger()


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handler für alle AppError-Subklassen."""
    logger.warning(
        "app_error",
        error_id=exc.error_id,
        error_code=exc.error_code,
        message=exc.message,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_id": exc.error_id,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
            "method": request.method,
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler für Pydantic-Validierungsfehler."""
    error_id = f"err_{uuid.uuid4()}"
    details = [
        {
            "field": ".".join(str(loc) for loc in err["loc"]),
            "reason": err["msg"],
            "code": err["type"],
        }
        for err in exc.errors()
    ]
    logger.warning(
        "validation_error",
        error_id=error_id,
        path=request.url.path,
        method=request.method,
        detail_count=len(details),
    )
    return JSONResponse(
        status_code=422,
        content={
            "error_id": error_id,
            "error_code": "VALIDATION_ERROR",
            "message": "Die Eingabedaten sind ungültig.",
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
            "method": request.method,
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler für unerwartete Fehler – keine internen Details exponieren."""
    error_id = f"err_{uuid.uuid4()}"
    logger.error(
        "unhandled_error",
        error_id=error_id,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error_id": error_id,
            "error_code": "INTERNAL_ERROR",
            "message": "Ein interner Fehler ist aufgetreten. Bitte kontaktieren Sie den Support mit der Referenz-ID.",
            "details": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
            "method": request.method,
        },
    )
```

### 4.3 Registrierung in FastAPI

```python
# app/main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.common.error_handlers import (
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.common.exceptions import AppError

app = FastAPI()

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
```

### 4.4 Verwendung in Routen

```python
# app/api/v1/botanical_families/router.py
from app.common.exceptions import DuplicateError, NotFoundError

@router.post("", response_model=FamilyResponse, status_code=201)
def create_family(body: FamilyCreate, repo = Depends(get_family_repo)):
    existing = repo.find_by_name(body.name)
    if existing:
        raise DuplicateError("BotanicalFamily", "name", body.name)

    family = BotanicalFamily(**body.model_dump())
    created = repo.create_family(family)
    return FamilyResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.get("/{key}", response_model=FamilyResponse)
def get_family(key: str, repo = Depends(get_family_repo)):
    f = repo.get_by_key(key)
    if f is None:
        raise NotFoundError("BotanicalFamily", key)
    return FamilyResponse(key=f.key or "", **f.model_dump(exclude={"key"}))
```

---

## 5. Log-Korrelation

### 5.1 Strukturiertes Logging mit error_id

Jede `error_id` wird im strukturierten Log mitgeschrieben:

```json
{
  "event": "app_error",
  "error_id": "err_7f3a9b2c-1d4e-4f5a-8b6c-9d0e1f2a3b4c",
  "error_code": "ENTITY_NOT_FOUND",
  "message": "BotanicalFamily mit Key 'xyz-123' nicht gefunden.",
  "path": "/api/v1/botanical-families/xyz-123",
  "method": "GET",
  "timestamp": "2026-02-26T14:30:00.000Z",
  "level": "warning"
}
```

### 5.2 Suche über Log-Aggregation

```bash
# Kibana / Loki / CloudWatch Query
error_id="err_7f3a9b2c-1d4e-4f5a-8b6c-9d0e1f2a3b4c"
```

Ein einziger Suchbegriff liefert die vollständige Fehlerhistorie inklusive:
- Request-Details (Path, Method, Body)
- Stack-Trace (nur im Log, nie in der API-Response)
- Kontext (User-ID, Session-ID)

### 5.3 Request-ID-Middleware (optional)

```python
# app/middleware/request_id.py
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

---

## 6. Sicherheitsanforderungen

### 6.1 Grundprinzip: Minimale Preisgabe von Informationen

Fehlermeldungen an den Client dürfen **ausschließlich fachliche Informationen** enthalten. Jede Information, die Rückschlüsse auf die eingesetzte Software, Infrastruktur, Architektur oder interne Systemstruktur zulässt, ist ein potenzieller Angriffsvektor und **MUSS** unterdrückt werden.

**Leitsatz**: Der Client erfährt *was* schiefgelaufen ist – niemals *warum* auf technischer Ebene.

### 6.2 Verbotene Inhalte in Fehler-Responses (Allowlist-Prinzip)

Nur explizit definierte Felder aus dem `ErrorResponse`-Schema (Abschnitt 2.1) dürfen in der API-Response erscheinen. Alles andere ist verboten.

#### 6.2.1 Software- und Framework-Informationen

| Verboten | Beispiel (DARF NICHT erscheinen) | Begründung |
|---|---|---|
| Programmiersprache / Version | `Python 3.14`, `CPython` | Ermöglicht gezielte Exploit-Suche |
| Framework-Name / Version | `FastAPI 0.115`, `Pydantic v2`, `uvicorn` | Bekannte CVEs gezielt ausnutzbar |
| Library-/Paketversionen | `python-arango 8.1.0`, `celery 5.4` | Supply-Chain-Angriffe |
| Interne Klassennamen | `ArangoSpeciesRepository`, `PhaseTransitionEngine` | Codestruktur offengelegt |
| Interne Methodennamen | `base_repository.create()`, `validate_transition()` | Reverse Engineering erleichtert |

#### 6.2.2 Infrastruktur- und Systeminformationen

| Verboten | Beispiel (DARF NICHT erscheinen) | Begründung |
|---|---|---|
| Datenbanktechnologie | `ArangoDB`, `AQL`, `DocumentInsertError` | DB-spezifische Angriffe |
| Datenbankschema | Collection-/Tabellennamen, Indexnamen, `idx_1858169123378298880` | Schema-Enumeration |
| SQL-/AQL-/Query-Fragmente | `FOR doc IN species FILTER ...` | Injection-Vorbereitung |
| Interne IP-Adressen / Hostnames | `172.21.0.3`, `arangodb:8529`, `redis://redis:6379` | Netzwerktopologie |
| Dateisystem-Pfade | `/app/app/data_access/arango/`, `/usr/local/lib/python3.14/` | Serverstruktur |
| Umgebungsvariablen | `ARANGODB_PASSWORD`, `REDIS_URL` | Credential Exposure |
| Container-/Pod-Informationen | `api_1`, `celery-worker`, Kubernetes Pod-Namen | Orchestrierungsstruktur |
| Betriebssystem-Details | Linux-Kernel-Version, OS-Distribution | Gezielte OS-Exploits |
| Stack-Traces | Jegliche Traceback-Ausgaben | Alle oben genannten Punkte |

#### 6.2.3 Geschäftslogik-Interna

| Verboten | Beispiel (DARF NICHT erscheinen) | Begründung |
|---|---|---|
| Interne Schlüssel-/ID-Formate | `_key: 575`, `_id: botanical_families/575` | Enumeration-Angriffe |
| Vollständige Datenobjekte | Serialisierte Pydantic-Models in Fehlern | Data Leakage |
| Interne Validierungsregeln | Exakte Regex-Patterns, Feldlängen | Bypass-Versuche |

### 6.3 Erlaubte Inhalte in Fehler-Responses

| Erlaubt | Beispiel | Begründung |
|---|---|---|
| Fachliche Entitätsbezeichnung | `BotanicalFamily`, `Species` | Domänensprache, kein technisches Detail |
| Vom Client gesendete Werte | `name='Solanaceae'` | Client kennt seine eigenen Eingaben |
| Fachliche Feldnamen | `field: "name"`, `field: "species_key"` | Für Formular-Fehleranzeige nötig |
| Standardisierte Error-Codes | `DUPLICATE_ENTRY`, `ENTITY_NOT_FOUND` | Maschinenlesbar, keine Implementierungsdetails |
| error_id (UUID) | `err_7f3a9b2c-...` | Für Support-Korrelation, kein technischer Rückschluss |

### 6.4 Beispiel: Verbotene vs. erlaubte Fehlerantworten

```python
# ❌ VERBOTEN – exponiert Datenbank, Index, Schlüssel und Stack-Trace
{
    "detail": "arango.exceptions.DocumentInsertError: [HTTP 409][ERR 1210] unique constraint violated - in index idx_1858169123378298880 of type hash over 'name'; conflicting key: 575"
}

# ❌ VERBOTEN – exponiert interne Datenstrukturen
{
    "error": "DUPLICATE",
    "message": "botanical_families with key '{'name': 'Solanaceae', 'typical_nutrient_demand': 'heavy', ...}' already exists"
}

# ✅ ERLAUBT – fachliche Information ohne technische Details
{
    "error_id": "err_abc123",
    "error_code": "DUPLICATE_ENTRY",
    "message": "BotanicalFamily mit name='Solanaceae' existiert bereits.",
    "details": [
        {
            "field": "name",
            "reason": "Wert 'Solanaceae' ist bereits vergeben.",
            "code": "DUPLICATE_ENTRY"
        }
    ],
    "timestamp": "2026-02-26T14:30:00.000Z",
    "path": "/api/v1/botanical-families",
    "method": "POST"
}

# ✅ ERLAUBT – interner Fehler ohne jegliche technische Information
{
    "error_id": "err_def456",
    "error_code": "INTERNAL_ERROR",
    "message": "Ein interner Fehler ist aufgetreten. Bitte kontaktieren Sie den Support mit der Referenz-ID.",
    "details": [],
    "timestamp": "2026-02-26T14:30:00.000Z",
    "path": "/api/v1/botanical-families",
    "method": "POST"
}
```

### 6.5 Enforcement

- **Code Reviews**: Jede Exception-Handler-Änderung muss auf Information Leakage geprüft werden
- **Automatisierte Tests**: Integrationstests müssen prüfen, dass 5xx-Responses keine verbotenen Inhalte enthalten (Regex-Check auf Datenbankbegriffe, Pfade, Versionsnummern)
- **CI-Pipeline**: Ein dedizierter Testschritt prüft, dass kein Error-Response-Body verbotene Patterns enthält (`ArangoDB`, `arango`, `Traceback`, `File "/"`, `.py`, `localhost:`, `redis://`, etc.)
- **Penetration Tests**: Regelmäßige Prüfung der Error-Responses auf Information Disclosure

---

## 7. Frontend-Integration

### 7.1 Error-Handling im API-Client

```typescript
// frontend/src/api/error-handler.ts
interface ApiError {
  error_id: string;
  error_code: string;
  message: string;
  details: Array<{
    field?: string;
    reason: string;
    code: string;
  }>;
  timestamp: string;
  path: string;
  method: string;
}

export function handleApiError(error: ApiError): void {
  switch (error.error_code) {
    case "VALIDATION_ERROR":
      // Feldspezifische Fehler anzeigen
      error.details.forEach((detail) => {
        if (detail.field) {
          showFieldError(detail.field, detail.reason);
        }
      });
      break;
    case "NOT_FOUND":
    case "ENTITY_NOT_FOUND":
      showNotification("warning", error.message);
      break;
    case "INTERNAL_ERROR":
      showNotification(
        "error",
        `${error.message}\nReferenz: ${error.error_id}`
      );
      break;
    default:
      showNotification("error", error.message);
  }
}
```

### 7.2 Anzeige für Endanwender

```
┌──────────────────────────────────────────────┐
│  ⚠ Ein Fehler ist aufgetreten               │
│                                              │
│  Ein interner Fehler ist aufgetreten.        │
│  Bitte kontaktieren Sie den Support.         │
│                                              │
│  Referenz: err_7f3a9b2c-1d4e-...            │
│                                              │
│  [ Erneut versuchen ]   [ Support ]          │
└──────────────────────────────────────────────┘
```

---

## 8. OpenAPI-Dokumentation

### 8.1 Fehler-Responses in Swagger

```python
# Alle Router verwenden einheitliche Error-Responses
from app.common.error_schemas import ErrorResponse

@router.get(
    "/{key}",
    response_model=FamilyResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Entität nicht gefunden"},
        422: {"model": ErrorResponse, "description": "Validierungsfehler"},
        500: {"model": ErrorResponse, "description": "Interner Serverfehler"},
    },
)
def get_family(key: str):
    ...
```

---

## 9. Akzeptanzkriterien

### Definition of Done

- [ ] **Einheitliches Fehlerformat**
    - [ ] Alle API-Fehler (4xx, 5xx) verwenden das `ErrorResponse`-Schema
    - [ ] Jede Fehlerantwort enthält eine eindeutige `error_id`
    - [ ] Pydantic `RequestValidationError` wird in das Standardformat überführt
    - [ ] Unbehandelte Exceptions werden abgefangen und als `INTERNAL_ERROR` zurückgegeben
- [ ] **Sicherheit**
    - [ ] Keine Stack-Traces in Fehlerantworten
    - [ ] Keine AQL-Queries in Fehlerantworten
    - [ ] Keine internen Pfade oder Versionsinfos exponiert
- [ ] **Nachverfolgbarkeit**
    - [ ] `error_id` wird im strukturierten Log mitgeschrieben
    - [ ] Log-Einträge enthalten error_code, path, method und message
    - [ ] `error_id` kann in Log-Aggregation gesucht werden
- [ ] **Dokumentation**
    - [ ] Error-Codes sind im OpenAPI-Schema dokumentiert
    - [ ] Fehler-Responses sind in Swagger UI sichtbar
    - [ ] Error-Code-Katalog ist gepflegt
- [ ] **Testing**
    - [ ] Unit-Tests für alle Exception-Handler
    - [ ] Integrationstests prüfen Fehlerformat bei 4xx und 5xx
    - [ ] Kein Test exponiert interne Details in der Response

### Testszenarien

#### Szenario 1: Nicht existierende Ressource

```bash
$ curl -s http://localhost:8000/api/v1/botanical-families/nicht-vorhanden | jq .
{
  "error_id": "err_...",
  "error_code": "ENTITY_NOT_FOUND",
  "message": "BotanicalFamily mit Key 'nicht-vorhanden' nicht gefunden.",
  "details": [...],
  "timestamp": "...",
  "path": "/api/v1/botanical-families/nicht-vorhanden",
  "method": "GET"
}
```

#### Szenario 2: Validierungsfehler

```bash
$ curl -s -X POST http://localhost:8000/api/v1/botanical-families \
  -H 'Content-Type: application/json' \
  -d '{"typical_nutrient_demand": "invalid"}' | jq .
{
  "error_id": "err_...",
  "error_code": "VALIDATION_ERROR",
  "message": "Die Eingabedaten sind ungültig.",
  "details": [
    {
      "field": "body.name",
      "reason": "Field required",
      "code": "missing"
    },
    {
      "field": "body.typical_nutrient_demand",
      "reason": "Input should be 'low', 'medium' or 'high'",
      "code": "enum"
    }
  ],
  "timestamp": "...",
  "path": "/api/v1/botanical-families",
  "method": "POST"
}
```

#### Szenario 3: Interner Fehler exponiert keine Details

```bash
# Simulierter DB-Ausfall
$ curl -s http://localhost:8000/api/v1/botanical-families | jq .
{
  "error_id": "err_...",
  "error_code": "INTERNAL_ERROR",
  "message": "Ein interner Fehler ist aufgetreten. Bitte kontaktieren Sie den Support mit der Referenz-ID.",
  "details": [],
  "timestamp": "...",
  "path": "/api/v1/botanical-families",
  "method": "GET"
}

# Der Stack-Trace erscheint NUR im Backend-Log:
# {"event": "unhandled_error", "error_id": "err_...", "exc_info": "...", "level": "error"}
```

#### Szenario 4: error_id im Log auffindbar

```bash
# 1. Fehler provozieren
ERROR_ID=$(curl -s http://localhost:8000/api/v1/botanical-families/xyz | jq -r .error_id)

# 2. Im Log suchen
kubectl logs deployment/agrotech-backend | grep "$ERROR_ID"
# Output: {"event": "app_error", "error_id": "err_...", ...}
```

---

## 10. Abhängigkeiten

### 10.1 Technische Abhängigkeiten

| Abhängigkeit | Typ | Begründung |
|---|---|---|
| NFR-001 (Separation of Concerns) | Architektur | Fehlerbehandlung gehört in den API-Layer |
| NFR-003 (Code Standards) | Code Quality | Englische Error-Codes, konsistente Benennung |

### 10.2 Externe Abhängigkeiten

- **FastAPI** >= 0.109.0 (Exception Handler)
- **Pydantic** >= 2.0 (ErrorResponse-Schema)
- **structlog** (Strukturiertes Logging mit error_id)
- **uuid** (Stdlib, Error-ID-Generierung)

---

## 11. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Inkonsistente Fehlerformate** | Frontend muss verschiedene Formate parsen | Hoch | Zentrale Exception-Handler |
| **Fehlende Nachverfolgbarkeit** | Support kann Fehler nicht reproduzieren | Hoch | error_id in jedem Fehler |
| **Sicherheitslücken** | Stack-Traces exponieren interne Details | Mittel | Unhandled-Error-Handler, Code Reviews |
| **Hoher Support-Aufwand** | Fehlermeldungen ohne Kontext | Hoch | Strukturiertes Logging |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Genehmigt
**Letzte Aktualisierung**: 2026-02-26
**Review**: Genehmigt
**Genehmigung**: Genehmigt (2026-06-11)
