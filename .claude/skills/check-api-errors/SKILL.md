---
name: check-api-errors
description: "Prueft FastAPI-Router-Dateien auf NFR-006-Konformitaet: Einheitliches ErrorResponse-Schema, error_id-Generierung, Keine internen Details exponiert, feldspezifische Fehlermeldungen, HTTP-Status-Code-Korrektheit. Nutze diesen Skill nach Implementierung neuer API-Endpoints."
argument-hint: "[Router-Pfad oder REQ-nnn, z.B. src/backend/app/api/v1/plants/router.py]"
disable-model-invocation: true
---

# API-Fehlerbehandlungs-Check (NFR-006): $ARGUMENTS

## Schritt 1: Router-Dateien laden

Falls `$ARGUMENTS` ein REQ-Identifier (z.B. `REQ-013`):
- Suche zugehoerige Router via Glob: `src/backend/app/api/v1/*/router.py`
- Filtere nach thematisch passendem Modul-Namen

Falls `$ARGUMENTS` ein Dateipfad:
- Lies die angegebene Datei direkt

Lies ausserdem:
- `src/backend/app/common/error_schemas.py` (falls vorhanden) — fuer das ErrorResponse-Schema
- `src/backend/app/common/exceptions.py` (falls vorhanden) — fuer eigene Exceptions
- `spec/nfr/NFR-006_API-Fehlerbehandlung.md` (erste 80 Zeilen) — fuer das Error-Format

## Schritt 2: ErrorResponse-Schema pruefen

**Das Pflicht-Schema (NFR-006 §2.1):**

```json
{
  "error_id": "err_<uuid4>",
  "error_code": "ENTITY_NOT_FOUND",
  "message": "Die Spezies existiert nicht.",
  "details": [
    {"field": "species_key", "reason": "...", "code": "ENTITY_NOT_FOUND"}
  ],
  "timestamp": "2026-01-01T00:00:00.000Z",
  "path": "/api/v1/plants",
  "method": "POST"
}
```

Prüfe ob:
- `ErrorResponse` Pydantic-Modell existiert und alle Pflichtfelder enthaelt
- `error_id` wird mit `f"err_{uuid4()}"` generiert (nicht statisch)
- `timestamp` ist `datetime.utcnow().isoformat()`

## Schritt 3: Exception-Handler pruefen

Prüfe in `router.py` und dem globalen Exception-Handler:

```python
# ✅ KORREKT — Strukturierter Fehler
@router.post("/")
async def create_plant(...):
    try:
        result = await plant_service.create(...)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error_code="ENTITY_NOT_FOUND",
                message=str(e),
                ...
            ).model_dump()
        )

# ❌ FALSCH — Rohfehler exponiert
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # Stack-Trace!

# ❌ FALSCH — Kein error_id
raise HTTPException(status_code=404, detail="Not found")
```

## Schritt 4: HTTP-Status-Code-Korrektheit pruefen

| Situation | Erwarteter Status-Code |
|-----------|----------------------|
| Entitaet nicht gefunden | 404 |
| Validierungsfehler | 422 |
| Nicht autorisiert | 401 |
| Keine Berechtigung | 403 |
| Business-Rule-Verletzung (z.B. Karenz) | 422 |
| Server-interner Fehler | 500 (ohne Details!) |
| Duplikat-Konflikt | 409 |

## Schritt 5: Security-Check — Keine internen Details exponieren

Suche nach Anti-Patterns:

```python
# ❌ Stack-Trace in Response
raise HTTPException(detail=traceback.format_exc())

# ❌ DB-Fehlermeldung exponiert
raise HTTPException(detail=str(arango_exception))

# ❌ Interner Service-Fehler sichtbar
raise HTTPException(detail=f"ArangoDB query failed: {aql_query}")
```

## Schritt 6: Report ausgeben

```markdown
# API-Fehlerbehandlungs-Review: {Modul}

## ErrorResponse-Schema
{Existiert: ja/nein | Alle Pflichtfelder: ja/nein}

## error_id-Generierung
{Dynamisch (UUID4): ja/nein}

## Exception-Handler-Coverage
{N von M Endpoints verwenden strukturiertes ErrorResponse}

## Security-Findings
{Stack-Traces exponiert: ja/nein | DB-Details sichtbar: ja/nein}

## HTTP-Status-Code-Korrektheit
{Falsche Codes: Liste mit Pfad:Zeile}

## Violations (priorisiert)
{Nummerierte Liste nach Schweregrad}

## Bewertung
- ✅ NFR-006-konform / ❌ {N} Violations gefunden
```
