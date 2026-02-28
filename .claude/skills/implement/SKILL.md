---
name: implement
description: "Implementiert ein Feature basierend auf einem REQ-Dokument. Liest Spec, analysiert Patterns, erstellt Plan und implementiert Backend (Python/FastAPI) und Frontend (React/TypeScript). Nutze diesen Skill wenn ein neues Feature aus einer Anforderung umgesetzt werden soll."
argument-hint: "[REQ-nnn]"
disable-model-invocation: true
---

# Feature implementieren: $ARGUMENTS

## Schritt 1: Kontext laden

Lies folgende Dokumente:

1. **REQ-Dokument:** Suche `spec/req/$ARGUMENTS_*.md` (Glob-Pattern)
2. **Architektur-NFRs:**
   - `spec/nfr/NFR-001_Separation-of-Concerns.md`
   - `spec/nfr/NFR-003_Code-Standard-Linting.md`
3. **Tech-Stack:** `spec/stack.md`
4. **CLAUDE.md** — fuer Architektur-Entscheidungen und Domain-Konzepte
5. **MEMORY.md** — fuer Implementierungsstatus und bekannte Patterns

Falls das REQ-Dokument nicht gefunden wird, melde den Fehler und brich ab.

## Schritt 2: Bestehende Patterns analysieren

Analysiere die bestehende Codebasis fuer Konventionen:

- **Backend-Patterns:** Lies ein bereits implementiertes Feature als Referenz (z.B. `src/backend/app/api/v1/substrates/`, `src/backend/app/domain/models/substrate.py`, `src/backend/app/domain/services/substrate_service.py`)
- **Frontend-Patterns:** Lies eine bestehende Page als Referenz (z.B. `src/frontend/src/pages/standorte/`)
- **Test-Patterns:** Lies bestehende Tests (z.B. `src/backend/tests/test_substrate_lifecycle_manager.py`)

## Schritt 3: Plan erstellen

Wechsle in den **Plan-Mode** und erstelle einen Implementierungsplan:

Der Plan MUSS enthalten:
1. **Domain Models** — Pydantic v2 Modelle, ArangoDB Collections (Doc + Edge)
2. **Engines/Calculators** — Business-Logic-Klassen
3. **Services** — Orchestrierungsschicht
4. **Repositories** — ArangoDB Data-Access
5. **API Router** — FastAPI Endpoints mit Schemas
6. **Frontend Pages** — React-Komponenten, Redux Slices, API-Endpoints
7. **Tests** — Backend-Tests (pytest), Frontend-Tests (vitest)
8. **Celery Tasks** — Falls zeitgesteuerte/asynchrone Operationen noetig
9. **i18n** — Uebersetzungsschluessel (DE + EN)
10. **Graph-Erweiterungen** — Neue Collections im `kamerplanter_graph`

## Schritt 4: Implementierung

Nach Plan-Genehmigung, implementiere das Feature unter Beachtung von:

- **NFR-001:** 5-Schichten-Architektur strikt einhalten
- **NFR-003:** Source-Code auf Englisch, Docs auf Deutsch
- **Tech-Stack:** Python 3.14+, FastAPI, Pydantic v2, React 19, TypeScript strict, MUI 7, Redux Toolkit
- **Patterns:** `type` keyword fuer Pydantic Aliases, structlog Logging, async/await
- **Auth:** Alle API-Endpoints mit `get_current_user` Dependency (REQ-023)
- **Multi-Tenancy:** Tenant-scoped Endpoints unter `/t/{slug}/` (REQ-024)

## Schritt 5: Qualitaetssicherung

Fuehre nach der Implementierung aus:

1. `cd src/backend && ruff check .` — Python Linting
2. `cd src/backend && pytest tests --tb=short -q` — Backend-Tests
3. `cd src/frontend && npx tsc -b` — TypeScript Type-Check
4. `cd src/frontend && npm run lint` — ESLint
5. `cd src/frontend && npm test -- --run` — Frontend-Tests

Behebe alle Fehler bevor du fertig meldest.

## Schritt 6: MEMORY.md aktualisieren

Aktualisiere die auto-memory Datei `MEMORY.md` (aus dem persistenten Memory-Verzeichnis) mit:
- Implementierungsstatus des neuen Features
- Neue Collections/Edges
- Neue API-Endpoints (Anzahl)
- Neue Engines/Services
