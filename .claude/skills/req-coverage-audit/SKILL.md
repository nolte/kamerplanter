---
name: req-coverage-audit
description: "Auditiert pro REQ-, NFR- und UI-NFR-Dokument die Coverage. Pro REQ: Backend (API/Service/Engine/Repo/Models), Frontend (Pages/Redux/i18n), Tests (E2E + Backend Unit + Frontend Vitest), Spec-Drift (Versionen, Cross-Refs, MEMORY.md). Pro NFR/UI-NFR: erwartete Artefakte (Configs/Tools/Patterns), Validierung (Tests/CI/Hooks), Drift. Erzeugt persistentes Audit-Artefakt unter .audits/req-coverage-audit.md mit Coverage-Score je Anforderung und priorisierter Handlungsliste. Nutze diesen Skill periodisch oder vor einem Release fuer eine vollstaendige Coverage-Bilanz; ohne Argument werden alle REQ+NFR+UI-NFR geprueft, mit Argument (z.B. REQ-013, NFR-001, UI-NFR-007) nur eine einzelne Anforderung."
argument-hint: "[optional: REQ-/NFR-/UI-NFR-Identifier z.B. REQ-013, NFR-001, UI-NFR-007]"
disable-model-invocation: true
---

# Requirements-Coverage-Audit: $ARGUMENTS

## Ziel

Erzeuge ein persistentes Audit-Artefakt unter `.audits/req-coverage-audit.md`, das fuer jedes
REQ-, NFR- und UI-NFR-Dokument im Repo die Coverage in passenden Dimensionen quantifiziert und
priorisierte Findings ausgibt. Drei Anforderungstypen mit unterschiedlicher Coverage-Logik:

- **REQ** (funktional, `spec/req/REQ-*.md`): vier Dimensionen — Backend / Frontend / Tests / Drift
- **NFR** (cross-cutting, `spec/nfr/NFR-*.md`): drei Dimensionen — Artefakte / Validierung / Drift
- **UI-NFR** (UI-uebergreifend, `spec/ui-nfr/UI-NFR-*.md`): drei Dimensionen — Frontend-Artefakte / Tests / Drift

Modi:

- **Full-Audit** (`$ARGUMENTS` leer): Alle REQ + NFR + UI-NFR werden geprueft.
  Output: `.audits/req-coverage-audit.md` (rerun ueberschreibt).
- **Single-Audit** (`$ARGUMENTS` = `REQ-013`, `NFR-001` oder `UI-NFR-007`): Nur eine
  Anforderung wird geprueft. Output: `.audits/req-coverage-audit/<ID>.md` (Per-Anforderungs-
  Plan im Sub-Verzeichnis). Das Full-Aggregate wird **nicht** ueberschrieben.

## Schritt 0: Erwartungs-Manifest laden (PFLICHT)

Lese `.claude/skills/req-coverage-audit/expectations.yaml`. Diese Datei ist die **Quelle der
Wahrheit** dafuer, welche Artefakte (Files, Globs, Patterns, Configs) pro Anforderung erwartet
werden. Ohne Manifest bricht der Skill ab — Heuristik allein liefert keine Vollstaendigkeits-
Garantie.

Manifest-Schema (vereinfacht):

```yaml
requirements:
  <ID>:                          # REQ-001, NFR-001, UI-NFR-007 etc.
    title: <Kurzbezeichnung>
    type: req|nfr|ui-nfr
    spec_path: spec/<bereich>/<datei>.md
    spec_version: <auto-detected|<x.y>>
    expected_artefacts:
      <dimension>:               # backend/frontend/tests/artefacts/validation
        - kind: file|glob|dir|pattern
          path: <repo-relativer Pfad oder Glob>
          role: <router|model|service|engine|repository|page|slice|test|config|...>
          contains: <optional: substring der im File vorkommen muss>
          optional: true|false   # default false — fehlend zaehlt sonst als fail
          rationale: <warum dieses Artefakt fuer diese Anforderung erwartet wird>
    drift:
      memory_status_field: <Pfad in MEMORY.md zur Drift-Pruefung; optional>
      cross_refs: [<REQ-NNN>, <NFR-NNN>]   # die referenziert sein sollen
```

## Schritt 1: Datenquellen parallel laden

Lade folgende Quellen mit parallelen `Glob`/`Read`-Calls:

1. **REQ-Dokumente:** `spec/req/REQ-*.md` (inkl. Sub-REQs wie `REQ-004-A_*`, `REQ-015-A_*`).
   Lies pro Datei die ersten ~30 Zeilen fuer Titel und Versionsnummer (Pattern: `## Version`,
   `Stand:` oder im Frontmatter).
2. **MEMORY.md:** Aus dem persistenten Memory-Verzeichnis (Pfad ueber Bash via
   `realpath ~/.claude/projects/-home-nolte-repos-github-kamerplanter/memory/MEMORY.md` oder den
   sichtbaren MEMORY-Block aus dem System-Prompt). Enthaelt den bekannten Implementierungsstatus.
3. **HA-Integration:** `spec/ha-integration/HA-REQ-*.md` (falls vorhanden).
6. **Backend-Quellen:**
   - `src/backend/app/api/v1/*/router.py` (Router)
   - `src/backend/app/domain/models/*.py` (Pydantic-Models)
   - `src/backend/app/domain/services/*.py` (Service-Layer)
   - `src/backend/app/domain/engines/*.py` (Engine/Calculator-Layer)
   - `src/backend/app/data_access/arango/*_repository.py` und
     `src/backend/app/data_access/timescale/*_repository.py` (Repository-Layer; polyglott)
7. **Frontend-Quellen:**
   - `src/frontend/src/pages/**/*.tsx` (Page-Komponenten)
   - `src/frontend/src/store/slices/*.ts` (Redux-Slices)
   - `src/frontend/src/api/*.ts` (API-Layer)
   - `src/frontend/src/i18n/locales/de/*.json` und `.../en/*.json` (Uebersetzungen)
8. **Test-Quellen:**
   - `src/backend/tests/**/test_*.py` (Backend pytest)
   - `src/frontend/src/test/**/*.test.{ts,tsx}` (Frontend vitest)
   - `tests/e2e/test_req*.py` (Selenium-E2E)
9. **Infrastruktur-Artefakte (fuer NFRs):**
   - `pyproject.toml` (Python-Build, Ruff-Config)
   - `package.json`, `eslint.config.js`, `vitest.config.ts` (Frontend-Build/Test)
   - `mkdocs.yml`, `docs/{de,en}/` (Doku, NFR-005)
   - `skaffold.yaml`, `helm/**/Chart.yaml`, `helm/**/values.yaml` (NFR-002, NFR-004)
   - `renovate.json5`, `.github/dependabot.yml` (NFR-009)
   - `.github/workflows/*.yml` (CI/CD, NFR-002/003/008)
   - `src/backend/app/api/v1/health/router.py` (NFR-007)
   - `src/backend/app/core/exception_handlers*.py` (NFR-006)
   - `tests/e2e/conftest.py`, `tests/e2e/pages/` (NFR-008a)
   - `src/frontend/src/i18n/i18n.ts`, `public/manifest.json`, `public/sw.js` (UI-NFR-007/012)

Im Single-Modus (`$ARGUMENTS` gesetzt) lies nur die zum jeweiligen Identifier passenden
Dateien. Themenmapping: REQ/NFR-Titel-Token (z.B. "Tank" fuer REQ-014, "Linting" fuer NFR-003)
als Filter ueber die Dateinamen, fuer NFRs zusaetzlich die im NFR-Mapping (Schritt 2b)
hinterlegten Erwartungs-Artefakte.

## Schritt 2: Pro REQ — vier Coverage-Dimensionen pruefen

Pro REQ-Dokument liefere ein strukturiertes Ergebnis. Jede Dimension hat 0–N Sub-Checks; jeder
Sub-Check ist `pass` / `fail` / `n/a`.

### Dimension 1 — Backend (5 Sub-Checks)

| Sub-Check | Pass-Kriterium | n/a-Kriterium |
|---|---|---|
| **API-Router** | `src/backend/app/api/v1/<entity>/router.py` mit thematisch passendem Pfad existiert | REQ ist reines UI/Doku-Konzept (z.B. REQ-021 UI-Erfahrungsstufen) |
| **Models** | Mind. ein Pydantic-Model in `app/domain/models/` deckt die im REQ genannten Entitaeten ab | REQ definiert keine eigenen Entitaeten |
| **Service** | `*Service`-Klasse in `app/domain/services/` mit thematisch passendem Namen existiert | wie Models |
| **Engine/Calculator** | `*Engine` oder `*Calculator` existiert, wenn der REQ Business-Logic-Regeln enthaelt (Statemachine, Validatoren, Berechnungen) | REQ ist reines CRUD ohne Regeln |
| **Repository** | `*Repository` existiert, wenn der REQ persistente Daten beschreibt | REQ ist nicht-persistent (z.B. Kalender-Aggregation) |

### Dimension 2 — Frontend (3 Sub-Checks)

| Sub-Check | Pass-Kriterium | n/a-Kriterium |
|---|---|---|
| **Page** | Mind. eine `*.tsx` unter `src/frontend/src/pages/<Bereich>/` deckt den REQ-Use-Case | REQ ist Backend-only (z.B. REQ-018 Aktorik) |
| **i18n DE+EN** | i18n-Keys fuer den Bereich existieren in **beiden** Sprachen | REQ braucht keine UI |
| **State/API-Layer** | Redux-Slice oder API-Modul fuer den REQ-Bereich vorhanden | REQ ohne Frontend-State |

### Dimension 3 — Tests (3 Sub-Checks)

| Sub-Check | Pass-Kriterium | n/a-Kriterium |
|---|---|---|
| **Backend Unit** | Mind. eine `test_*.py` adressiert den REQ-Bereich (Service/Engine) | Backend n/a |
| **Frontend Vitest** | Mind. eine `*.test.{ts,tsx}` adressiert die Page/Slice | Frontend n/a |
| **E2E** | `tests/e2e/test_req<NN>*.py` existiert (Pattern aus NFR-008) | REQ explizit als nicht E2E-relevant markiert |

### Dimension 4 — Spec-Drift (3 Sub-Checks, fuer ALLE Anforderungstypen)

Wird automatisch fuer jede Anforderung (REQ + NFR + UI-NFR) evaluiert, gespeist aus dem
`drift:`-Block des Manifests.

| Sub-Check | Pass-Kriterium | Fail-Indikator | Optional? |
|---|---|---|---|
| **marker_clean** | `drift.memory_status_field` enthaelt KEINE Drift-Schluesselwoerter (`DRIFT`, `NICHT IMPL`, `NOT IMPLEMENTED`, `NICHT IMPLEMENTIERT`, `NICHT AKTIV`, `COMPLIANCE-RISIKO`, `OFFEN`). `Future`/`Idee` zaehlen als `n/a` (bewusst aufgeschoben). | Drift-Schluesselwort gefunden → impl-Luecke ODER Spec-Code-Drift in Produktion | nein |
| **cross_refs_intact** | Alle in `drift.cross_refs` deklarierten `REQ-NNN`/`NFR-NNN`/`UI-NFR-NNN`-Referenzen existieren als Manifest-Eintrag | Tote Referenz auf z.B. `REQ-099` | nein (n/a wenn Liste leer) |
| **spec_version_present** | `## Version X.Y` oder `## X.Y (...)`-Header im Spec-Dokument extrahierbar | keine Versionsangabe in Spec | **ja** — nice-to-have, kein Implementierungsfehler |

## Schritt 2b: Pro NFR — drei Coverage-Dimensionen pruefen

NFRs sind **cross-cutting** (Architektur, Tooling, Patterns, Compliance) und nicht entitaets-
basiert. Pro NFR braucht es ein **Erwartungs-Mapping**: welche Dateien/Configs/Patterns muessen
existieren, damit das NFR umgesetzt ist? Das Mapping ist im NFR-Dokument selbst dokumentiert
(Abschnitt "Akzeptanzkriterien" oder "Anforderungen") und wird hier als Tabelle gepflegt.

### Dimension 1 — Artefakte (variabel, typisch 2–5 Sub-Checks pro NFR)

Erwartete Konfig-/Code-/Doku-Artefakte pro NFR. Beispiele:

| NFR | Erwartete Artefakte |
|---|---|
| NFR-001 Separation of Concerns | `app/api/`, `app/domain/services/`, `app/domain/engines/`, `app/data_access/`, `app/domain/models/`, `spec/style-guides/BACKEND.md` |
| NFR-002 Kubernetes-Plattform | `helm/**/Chart.yaml`, `helm/**/values.yaml`, `skaffold.yaml` |
| NFR-003 Code-Standard Linting | `pyproject.toml` (ruff config), `eslint.config.js`, `.github/workflows/backend.yml`, `.github/workflows/frontend.yml` |
| NFR-004 Lokale Entwicklungsumgebung | `skaffold.yaml`, `docs/**/skaffold*.md` |
| NFR-005 Technische Dokumentation | `mkdocs.yml`, `docs/de/`, `docs/en/`, `docs/requirements.txt` |
| NFR-006 API-Fehlerbehandlung | `app/core/exception_handlers*.py`, Tracking-ID-Middleware, `errors.py` |
| NFR-007 Betriebsstabilitaet | `app/api/v1/health/router.py`, Logging-Konfig (`structlog`), Metrics-Endpunkt |
| NFR-008 Teststrategie | `pyproject.toml [tool.pytest]`, `vitest.config.ts`, `tests/e2e/conftest.py` |
| NFR-008a E2E-Selenium-Standard | `tests/e2e/conftest.py`, `tests/e2e/pages/`, Screenshot-Mechanismus |
| NFR-009 Dependency-Management | `renovate.json5` ODER `.github/dependabot.yml` |
| NFR-010 UI-Pflegemasken | Pro Domain-Entity mind. eine `*ListPage.tsx` |
| NFR-011 Retention Policy | Celery-Task `*_retention*`, IP-Anonymisierung-Test, Retention-Konfig |
| NFR-012 Cloud-Provider Enterprise | HPA-/PDB-/NetworkPolicy-Templates in `helm/` |
| NFR-013 Speicheranbindung Object-Storage | S3/Object-Storage-Adapter im Backend, File-Upload-Endpunkt |

### Dimension 2 — Validierung (Tests + CI-Hooks, 1–3 Sub-Checks)

Wird das NFR durchgesetzt — z.B. Lint-CI fuer NFR-003, Test-Coverage-Schwelle fuer NFR-008,
Architektur-Tests fuer NFR-001 (`import-linter`)? Wenn das NFR nur als Vorgabe existiert ohne
maschinelle Pruefung, ist Sub-Check `unenforced` (zaehlt als `fail`).

### Dimension 3 — Spec-Drift (analog zu REQ)

Versionsnummer aus NFR-Dokument vs. Stand im Repo (z.B. `pyproject.toml`-Ruff-Version vs.
`spec/style-guides/BACKEND.md`-Soll-Version). Tote Cross-References im NFR-Dokument zaehlen wie
bei REQs als Fail.

## Schritt 2c: Pro UI-NFR — drei Coverage-Dimensionen pruefen

UI-NFRs sind **frontend-uebergreifend** (Responsive, i18n, Barrierefreiheit, Brand). Pro UI-NFR:

### Dimension 1 — Frontend-Artefakte

| UI-NFR | Erwartete Artefakte |
|---|---|
| UI-NFR-001 Responsive | MUI Breakpoints in `theme.ts`, mind. ein responsives Komponenten-Beispiel |
| UI-NFR-002 Barrierefreiheit | `accessibility.test.tsx`, ARIA-Attribute in Komponenten |
| UI-NFR-006 Design-System | `theme.ts` (light + dark), `spec/style-guides/FRONTEND.md` |
| UI-NFR-007 i18n | `i18n.ts`, `locales/de/`, `locales/en/` |
| UI-NFR-008 Formulare | `FormTextField.tsx`, `FormSelectField.tsx`, `FormChipInput.tsx`, Tests |
| UI-NFR-010 Tabellen-Datenansichten | `DataTable.tsx`, `DataTable.test.tsx` |
| UI-NFR-012 PWA-Offline | `public/manifest.json`, `public/sw.js`, Service-Worker-Code |
| UI-NFR-013 Consent | Consent-Komponente + Backend-Consent-Service |
| UI-NFR-019 Kiosk-Modus | Spezielle Kiosk-Seiten oder Touch-Mode-Komponenten |
| (uebrige) | Heuristik analog: Token-basierte Datei-Suche im Frontend |

### Dimension 2 — Tests (Frontend Vitest + E2E)

Wird die UI-Anforderung getestet (z.B. `accessibility.test.tsx` fuer UI-NFR-002,
i18n-Coverage-Test fuer UI-NFR-007)?

### Dimension 3 — Spec-Drift (analog)

UI-NFR-Version vs. tatsaechliche Implementierung. Brand-Konsistenz (Farbcodes, Logo) wird
nicht automatisch geprueft — fail nur wenn Spec aktuell ist und Implementierung gar nicht
existiert.

## Schritt 2d: Vollstaendigkeits-Check (Manifest deckt alle Anforderungen ab?)

Vor der Score-Berechnung **MUSS** geprueft werden, dass jede gefundene Anforderung im Manifest
steht:

```python
spec_ids = set(extracted_from(spec/req/, spec/nfr/, spec/ui-nfr/))
manifest_ids = set(expectations_yaml["requirements"].keys())

missing_in_manifest = spec_ids - manifest_ids
extra_in_manifest = manifest_ids - spec_ids
```

- `missing_in_manifest`: jede dieser Anforderungen ist ein **BLOCKER-Finding "manifest-luecke"**
  und wird im Aggregate als nicht-auditierbar markiert. Das Manifest **MUSS** erweitert werden,
  bevor die Coverage als vertrauenswuerdig gilt.
- `extra_in_manifest`: Eintrag im Manifest fuer eine nicht (mehr) existierende Anforderung —
  Manifest-Aufraeumen erforderlich (WARNING).

Zusaetzlicher Heuristik-Check (optional, defensiv): Token-basierter Match aus den ehemaligen
Schritten 2/2b/2c laeuft weiter im Hintergrund, **aber** die Coverage zaehlt **nur das, was
im Manifest steht**. Heuristik dient nur der Plausibilitaets-Pruefung: wenn Heuristik viele
Treffer findet die nicht im Manifest stehen → Manifest-Erweiterungs-Vorschlag im Run-Log.

## Schritt 3: Coverage-Score je Anforderung berechnen

Score je Dimension: `pass-count / (pass-count + fail-count)` (n/a wird nicht gewichtet).
Gesamt-Score:

- **REQ**: arithmetisches Mittel der vier Dimensions-Scores (Backend, Frontend, Tests, Drift).
- **NFR / UI-NFR**: arithmetisches Mittel der drei Dimensions-Scores (Artefakte, Validierung, Drift).

Status-Mapping aus Gesamt-Score (gilt fuer alle drei Anforderungstypen):

- ≥ 90 % → **Implementiert** (gruen)
- 60–89 % → **Teilweise** (gelb)
- 30–59 % → **Lueckenhaft** (orange)
- < 30 % → **Spezifiziert** (rot)
- Alle Dimensionen n/a oder Anforderung nur `## Status: Idee` → **Idee** (grau)

## Schritt 4: Aggregate ausgeben (Full-Audit)

Schreibe `.audits/req-coverage-audit.md` als **Plan-Index + Coverage-Bilanz**. Das Aggregate
ist Roll-up; die Per-Anforderungs-Plans (Schritt 5) sind die actionable Artefakte.

```markdown
---
review-type: req-coverage-audit
target-repo: kamerplanter
total-count: <N>      # REQ + NFR + UI-NFR
req-count: <N>
nfr-count: <N>
ui-nfr-count: <N>
manifest-coverage: <M/N>      # wie viele Anforderungen sind im Manifest
plans-open: <N>      # Per-Anforderungs-Plans mit Coverage < 100 %
plans-closed: <N>    # in dieser Iteration geloeschte Plans (Coverage = 100 %)
repo-revision: <git rev-parse --short HEAD>
created: <YYYY-MM-DD>
mode: <full|single>
---

## Scope
<Ein Absatz: wie viele Anforderungen geprueft, Manifest-Vollstaendigkeit, welche Quellen.>

## Manifest-Vollstaendigkeit
- REQs im Manifest: <M>/<N> — fehlend: <Liste>
- NFRs im Manifest: <M>/<N> — fehlend: <Liste>
- UI-NFRs im Manifest: <M>/<N> — fehlend: <Liste>
- Verwaiste Manifest-Eintraege (kein Spec-Dokument): <Liste>

**Wenn Manifest unvollstaendig → BLOCKER. Vor jedem Folge-Audit erweitern.**

## Coverage uebersicht (REQ)
| REQ | Titel | Spec | Backend | Frontend | Tests | Drift | Score | Status | Plan |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | Stammdatenverwaltung | v4.1 | 5/5 | 3/3 | 3/3 | 3/3 | 100 % | Implementiert | — |
| REQ-008 | Post-Harvest | v2.2 | 0/5 | 0/3 | 0/3 | 0/3 | 0 % | Spezifiziert | [Plan](req-coverage-audit/REQ-008.md) |

## Coverage uebersicht (NFR)
| NFR | Titel | Spec | Artefakte | Validierung | Drift | Score | Status | Plan |
|---|---|---|---|---|---|---|---|---|
| NFR-001 | Separation of Concerns | v2.3 | 6/6 | 0/1 | 1/1 | 75 % | Teilweise | [Plan](req-coverage-audit/NFR-001.md) |

## Coverage uebersicht (UI-NFR)
| UI-NFR | Titel | Spec | Frontend | Tests | Drift | Score | Status | Plan |
|---|---|---|---|---|---|---|---|---|
| UI-NFR-007 | i18n | v1.0 | 3/3 | 0/1 | 1/1 | 80 % | Teilweise | [Plan](req-coverage-audit/UI-NFR-007.md) |

## Verteilung gesamt
- Implementiert: N (%)
- Teilweise: N (%)
- Lueckenhaft: N (%)
- Spezifiziert: N (%)

## Roadmap (priorisierte Plan-Reihenfolge)
Aus den Per-Anforderungs-Plans abgeleitet, sortiert nach `priority` und `coverage_score`:

| # | Anforderung | Status | Aufwand | Abhaengigkeiten | Plan |
|---|---|---|---|---|---|
| 1 | REQ-025 Datenschutz | spezifiziert | XL | NFR-011 | [Plan](req-coverage-audit/REQ-025.md) |
| 2 | REQ-008 Post-Harvest | spezifiziert | L | REQ-007 | [Plan](req-coverage-audit/REQ-008.md) |
| ... | ... | ... | ... | ... | ... |

## Plan-Index (alle offenen Plans, alphabetisch)
| Anforderung | Plan | Coverage | Letzte Aktualisierung |
|---|---|---|---|
| REQ-008 | [.audits/req-coverage-audit/REQ-008.md](req-coverage-audit/REQ-008.md) | 0 % | <ISO> |
| ... | ... | ... | ... |

## Geschlossene Plans (in dieser Iteration)
<Liste der Anforderungen die jetzt 100 % erreichen — Plan wurde geloescht.>

## Run log
- <ISO> — Manifest geladen: N Eintraege
- <ISO> — Vollstaendigkeits-Check: M/N abgedeckt
- <ISO> — Coverage berechnet
- <ISO> — Per-Anforderungs-Plans geschrieben: <N neu, <M aktualisiert, <K geschlossen
- <ISO> — Aggregate geschrieben
```

## Schritt 5: Per-Anforderungs-Ausfuehrungsplaene erzeugen (PFLICHT)

**Im Full-Audit ebenso wie im Single-Audit** wird fuer **jede Anforderung mit Coverage < 100 %**
ein eigenstaendiger Per-Anforderungs-Plan unter `.audits/req-coverage-audit/<ID>.md`
geschrieben. Coverage = 100 % heisst kein Plan (alles erwartete Artefakt vorhanden, kein
Drift-Finding).

**Plan-Template:**

```markdown
---
audit-type: req-coverage-plan
requirement: <ID>                  # REQ-008, NFR-001, UI-NFR-007
title: <Titel>
type: req|nfr|ui-nfr
spec_path: <pfad zur Spec>
spec_version: <vX.Y>
coverage_score: <0-100>
status: implementiert|teilweise|lueckenhaft|spezifiziert|idee
priority: blocker|warning|info     # abgeleitet aus Score + Drift
created: <ISO-Datum>
audit_run: <git-sha>
---

# Ausfuehrungsplan: <ID> <Titel>

## Kontext
- Spec: <pfad>:<version>
- MEMORY-Status: <kurzer Auszug>
- Coverage: <pass>/<total> Sub-Checks bestanden (<%>)
- Letzte Aenderung der Spec: <git log -1 fuer das Spec-File, wenn ermittelbar>

## Erwartete Artefakte (Manifest-Eintraege)
| Artefakt | Pfad/Glob | Rolle | Status | Optional? |
|---|---|---|---|---|
| <name>   | <path>    | <role>| GEFUNDEN/FEHLT | yes/no |

## Drift-Findings
- **Versionsabgleich**: <Spec vY.Z> vs <MEMORY/ADR vX.Y> → <pass/fail/n/a>
- **Cross-References**: <pass/fail mit konkreten toten Links>
- **AC-Spurbarkeit**: <pass/fail mit Stichprobe>

## Aufgaben (priorisiert, abarbeitbar)

### Aufgabe 1 — <Kurztitel> [Aufwand: S|M|L]
- **Zu tun**: <konkreter Schritt — Datei anlegen / Test ergaenzen / Logik portieren>
- **Pfad/Datei**: <konkreter Repo-Pfad>
- **Spec-Referenz**: <Spec-Abschnitt §X.Y>
- **Akzeptanzkriterium**: <was muss messbar erfuellt sein, damit Aufgabe als erledigt gilt>
- **Empfohlener Skill/Agent**: `/implement REQ-NNN backend` oder `Agent fullstack-developer ...`

### Aufgabe 2 — ... [Aufwand: ...]
- ... (analog)

## Empfohlene Skill-Sequenz (Reihenfolge der Bearbeitung)
1. <z.B. /implement REQ-008 backend>
2. <z.B. /check-architecture src/backend/app/domain/services/post_harvest_service.py>
3. <z.B. /req-coverage-audit REQ-008> zur Verifikation

## Abhaengigkeiten
- **Vorgaenger**: <REQ-NNN> muss zuerst implementiert sein (begruendet)
- **Nachfolger**: <REQ-NNN> baut auf dieser Anforderung auf
- **Querschnitt**: <NFR-NNN> Architekturvorgabe gilt

## Aufwandsschaetzung
- Total: <S|M|L|XL>
- Begruendung: <Anzahl Files * Komplexitaet>
- Empfohlene Bearbeitungs-Iteration: <Sprint <N> oder Block "Compliance" o.ae.>
```

**Aufwands-Skala:**

- **S** (≤ 4 h): Eine Datei, ein klarer Spec-Abschnitt, kein Datenmodell-Eingriff
- **M** (≤ 1 d): Mehrere Files, Datenmodell-Anpassung, Integrationstest noetig
- **L** (≤ 3 d): Neuer Layer / mehrere Services beruehrt / Migration noetig
- **XL** (> 3 d): Architekturentscheidung, mehrere REQs/NFRs, Teamabstimmung

**Priority-Mapping aus Coverage:**

- `coverage < 30` UND Spec aktiv → **blocker**
- `coverage 30–59` ODER Drift erkannt → **warning**
- `coverage 60–89` UND keine Drift → **info**
- `coverage = 100 %` → kein Plan (siehe oben)

**Plan-Lifecycle:**

- Rerun ueberschreibt den Per-Anforderungs-Plan (`agent-review`-Pattern). History lebt im git log.
- Coverage = 100 % erreicht? → Plan-Datei wird beim naechsten Full-Run **geloescht** (statt
  ueberschrieben); im Aggregate-Run-Log als `plan-closed` vermerkt.
- Manuelle Aktualisierungen am Plan (z.B. Aufgabe als erledigt markieren) ueberleben einen
  Single-Audit-Rerun **nicht** automatisch — der Skill regeneriert. Der `implement`-Skill
  schliesst Aufgaben durch Implementierung; das naechste Audit reflektiert den neuen Stand.

## Schritt 5b: Single-Audit-Modus (`$ARGUMENTS` gesetzt)

Single-Audit erzeugt **nur** den Per-Anforderungs-Plan fuer die genannte Anforderung
(`.audits/req-coverage-audit/<ID>.md`) und **nicht** den Full-Aggregate. Manifest-
Vollstaendigkeits-Check (Schritt 2d) wird auf nur diese eine Anforderung beschraenkt.

## Schritt 6: Naechste Schritte ausgeben

Nach dem Schreiben des Audits gib im Chat eine kompakte Zusammenfassung:

- Pfad zum Audit
- Verteilung (Implementiert/Teilweise/Lueckenhaft/Spezifiziert)
- Top-3 BLOCKER und Top-3 WARNING (mit REQ-ID + 1-Zeilen-Defizit)
- Empfohlener naechster Skill: `implement` fuer das hoechstpriorisierte BLOCKER-REQ ODER
  `check-architecture` fuer Drift-WARNINGs

## Hard rules

- **Niemals** Coverage ohne Manifest berechnen — `.claude/skills/req-coverage-audit/expectations.yaml`
  ist Pflicht-Eingabe. Fehlt es: Skill bricht ab und fordert die Anlage.
- **Niemals** eine Anforderung als "abgedeckt" werten ohne expliziten Manifest-Eintrag.
  Heuristik dient nur Plausibilitaet; Manifest ist die Quelle der Wahrheit.
- **Immer** Vollstaendigkeits-Check ausfuehren: jede Anforderung in `spec/req/`, `spec/nfr/`,
  `spec/ui-nfr/` MUSS einen Manifest-Eintrag haben. Fehlt einer → BLOCKER-Finding
  "manifest-luecke", Audit-Vertrauenswuerdigkeit ist kompromittiert.
- **Immer** Per-Anforderungs-Plan fuer **jede** Anforderung mit Coverage < 100 % erzeugen —
  kein "wir machen nur Top-3 Plans". Das Aggregate ist Index, der Plan ist actionable Output.
- **Niemals** Status raten — fehlende erwartete Artefakte werden als `fail` gewertet, nicht als
  Vermutung "wahrscheinlich vorhanden".
- **Niemals** Drift automatisch fixen — der Skill reportet und plant, der `implement`-Skill
  (oder ein Mensch) fixt.
- **Niemals** Dateien ausserhalb von `.audits/` und `.claude/skills/req-coverage-audit/`
  schreiben — der Skill ist read-only auf dem Repo, schreibend nur ins Audit-Verzeichnis und
  ins Manifest (Manifest-Erweiterungs-Vorschlaege).
- **Niemals** dated copies des Aggregates anlegen (`.audits/req-coverage-audit-2026-04-27.md`
  ist verboten). Pfad ist exakt `.audits/req-coverage-audit.md`; rerun ueberschreibt; History
  lebt im `git log` (analog `agent-fleet-review`).
- **Niemals** den Full-Aggregate in einem Single-Audit-Run anfassen — Single beruehrt nur
  einen einzigen Per-Anforderungs-Plan.
- **Niemals** auf Datenquellen warten oder pollen — wenn ein erwartetes Verzeichnis fehlt
  (z.B. `tests/e2e/` nicht angelegt), dimension entsprechend mit `n/a` markieren und im Run-Log
  vermerken.
- **Per-Anforderungs-Plans werden geloescht** wenn die Anforderung 100 % erreicht — git log
  bewahrt die History, das Audit-Verzeichnis bleibt fokussiert auf offene Punkte.
- **`disable-model-invocation: true`** ist gesetzt: der Skill wird ausschliesslich per
  `/req-coverage-audit` durch den Nutzer aktiviert, nicht von Claude eigenstaendig.
- Wenn `MEMORY.md` nicht erreichbar ist (z.B. ausserhalb dieser Claude-Session), Drift-Dimension
  Sub-Check 1 als `n/a` markieren und im Skipped-Block vermerken — kein Fail, weil die Quelle
  fehlt.

## Hinweise

- Themen-Mapping REQ ↔ Dateinamen ist heuristisch (REQ-014 Tankmanagement → Dateien mit
  `tank` im Namen). Bei Ambiguitaet (z.B. REQ-024 Mandantenverwaltung → `tenant`,
  `membership`, `invitation`) lies die ersten 60 Zeilen des REQ-Dokuments und extrahiere die
  Entitaets-Namen aus den Spec-Sektionen.
- Backend-Single-File-Pruefung: Falls ein Service mehrere REQs gleichzeitig adressiert (z.B.
  `auth_service.py` deckt REQ-023 + REQ-024), zaehle ihn fuer beide REQs.
- Verwandte Skills:
  - `spec-status` — schnelle Tabelle ohne persistentes Audit, ohne Drift-Detection
  - `check-architecture` — NFR-001-Layer-Pruefung pro Modul, fuer Drift-Followups
  - `pre-pr` — Pre-Merge-Sammelpruefung (kein Coverage)
