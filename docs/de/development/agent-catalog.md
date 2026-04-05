---
title: Agent- und Skill-Katalog
description: Uebersicht aller verfuegbaren Claude Code Agents und Skills im Kamerplanter-Projekt
---

# Agent- und Skill-Katalog

Uebersicht aller verfuegbaren Claude Code Agents und Skills im Kamerplanter-Projekt — instrumentiert zum Orchestrieren von komplexen Software-Workflows fuer Pflanzenpflege-Management, IoT-Integration, Anforderungsanalyse und Quality Assurance.

!!! info "Stand: April 2026 — 33 Agents, 19 Skills registriert"
    Dieser Katalog wird vom `/update-catalog` Skill automatisch generiert. Zuletzt aktualisiert: 2026-04-05.

---

## Schnellnavigation

| Kategorie | Technisch | Fachlich | Gesamt |
|-----------|-----------|----------|--------|
| **Analyse & Review** | 5 | 9 | 14 |
| **Entwicklung** | 1 | 2 | 3 |
| **Testing & QA** | 4 | 0 | 4 |
| **Dokumentation** | 2 | 1 | 3 |
| **Weitere** | 2 | 2 | 4 |
| **Skills** | 8 | 4 | 12 |

---

## Agents

### Analyse & Review (14 Agents)

Agents die bestehende Dokumente, Code oder Anforderungen pruefend analysieren.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `agrobiology-requirements-reviewer` | F | sonnet | Fachliche Korrektheit von Anforderungen |
| `cannabis-indoor-grower-reviewer` | F | sonnet | Praxis-Tauglichkeit fuer Cannabis-Anbau |
| `casual-houseplant-user-reviewer` | F | sonnet | Alltagstauglichkeit fuer Laien |
| `code-security-reviewer` | T | sonnet | OWASP-Schwachstellen im Code |
| `docs-freshness-checker` | T | sonnet | Veraltete API-Doku und fehlende Seiten |
| `e2e-result-reviewer` | T | opus | Selenium-Test-Ergebnisse gegen Spec |
| `frontend-design-reviewer` | T | sonnet | Responsive Design, Kiosk, Accessibility |
| `frontend-usability-optimizer` | T | sonnet | MUI-Formulare, Darstellung, i18n |
| `growing-phase-auditor` | F | sonnet | Botanische Korrektheit von Phasen |
| `i18n-completeness-checker` | T | haiku | DE/EN-Uebersetzungen auf Luecken |
| `it-security-requirements-reviewer` | T | sonnet | Sicherheit und DSGVO in Anforderungen |
| `outdoor-garden-planner-reviewer` | F | sonnet | Freiland-Gartenplanung und Aussaen |
| `requirements-contradiction-analyzer` | T | sonnet | Widersprueche in Anforderungen |
| `seed-data-validator` | F | sonnet | YAML-Seed-Daten auf Vollstaendigkeit |

### Entwicklung (3 Agents)

Agents die produktiven Code erstellen.

| Agent | Typ | Modell | Aufgabe |
|-------|-----|--------|---------|
| `fullstack-developer` | T | opus | Backend + Frontend implementieren |
| `ha-integration-developer` | F | opus | HA Custom Integration entwickeln |
| `ha-integration-sync` | F | opus | HA mit Backend-API synchronisieren |

### Testing & QA (4 Agents)

Agents fuer Test-Erstellung und -Verwaltung.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `e2e-testcase-extractor` | T | sonnet | Testfaelle aus Specs ableiten |
| `selenium-test-generator` | T | opus | Selenium E2E-Tests schreiben |
| `selenium-test-reviewer` | T | sonnet | E2E-Test-Qualitaet pruefen |
| `unit-test-runner` | T | sonnet | Unit-Tests + statische Analyse |

### Dokumentation (3 Agents)

Agents fuer Dokumentations-Erstellung und Pflege.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `agent-catalog-generator` | T | haiku | Diesen Katalog generieren |
| `gemini-graphic-prompt-generator` | T | sonnet | KI-Bildgenerations-Prompts |
| `mkdocs-documentation` | T | sonnet | MkDocs-Dokumentation (DE/EN) |

### Weitere Agents (4 Agents)

| Agent | Typ | Modell | Aufgabe |
|-------|-----|--------|---------|
| `ha-integration-requirements-engineer` | F | sonnet | HA-Anforderungen ableiten |
| `knowledge-chunk-author` | F | sonnet | RAG-Knowledge-Chunks erstellen |
| `plant-info-document-generator` | F | sonnet | Pflanzen-Steckbriefe generieren |
| `png-to-transparent-svg` | T | sonnet | PNG → SVG konvertieren |
| `pr-to-develop` | T | sonnet | PR nach develop vorbereiten |
| `rag-eval-runner` | F | sonnet | RAG-Qualitaet benchmarken |
| `target-audience-analyzer` | T | sonnet | Zielgruppen-Analyse |
| `tech-stack-architect` | T | sonnet | Tech-Stack validieren |
| `smart-home-ha-reviewer` | F | sonnet | HA-Integration reviewen |

---

!!! note "Legende: Typ-Spalte"
    **T** = Technisch (allgemeine Softwareentwicklung, in jedem Projekt nuetzlich)

    **F** = Fachlich (domaenenspezifisch fuer Pflanzenpflege/Kamerplanter)

---

## Skills

Skills sind automatisierte Workflows ohne UI-Invocation. Sie werden via `/skill-name` aktiviert.

### Quality & Checks (7 Skills)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/check-quality` | T | Linting + Unit-Tests (Backend + Frontend) |
| `/check-api-errors` | T | NFR-006-Konformitaet Error Handling |
| `/check-architecture` | T | NFR-001-Konformitaet (5-Layer) |
| `/check-helm` | T | NFR-002-Konformitaet Helm-Charts |
| `/check-retention` | T | NFR-011-DSGVO-Retention |
| `/check-slo` | T | NFR-007-SLO/Monitoring |
| `/check-test-pyramid` | T | NFR-008-Testpyramiden |

### Deployment (3 Skills)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/check-deps` | T | CVE-Scanning + Lizenz-Compliance |
| `/deploy-ha` | F | HA-Integration zu Kind deployen |
| `/verify-ha` | F | HA-Integration-Logs diagnostizieren |

### Workflow (5 Skills)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/implement` | T | Feature aus REQ implementieren |
| `/pre-pr` | T | Alle Pre-PR-Checks ausfuehren |
| `/review-spec` | T | Parallele Spec-Reviews starten |
| `/ha-derive` | F | HA-Anforderungen ableiten |
| `/check-ui-crud` | T | NFR-010-UI-CRUD-Check |

### Generierung (4 Skills)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/gen-knowledge` | F | RAG-Knowledge-Dokumente |
| `/spec-status` | T | Implementierungsstatus aller REQs |
| `/test-extract` | T | E2E-Testfaelle ableiten |
| `/update-catalog` | T | Agent/Skill-Katalog regenerieren |

---

## Einsatz-Entscheidungshilfe

!!! tip "Welcher Agent/Skill fuer meine Aufgabe?"

    **Nach Workflow-Phase:**

    | Phase | Agent/Skill |
    |-------|-------------|
    | **Anforderungen spezifizieren** | `tech-stack-architect`, `target-audience-analyzer` |
    | **Anforderungen reviewen** | `/review-spec`, `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`, `requirements-contradiction-analyzer` |
    | **Fachliche Perspektiven** | `cannabis-indoor-grower-reviewer`, `casual-houseplant-user-reviewer`, `outdoor-garden-planner-reviewer`, `smart-home-ha-reviewer` |
    | **Implementieren** | `fullstack-developer` (mit `/implement` fuer Struktur) |
    | **Lokal testen** | `/check-quality`, `unit-test-runner` |
    | **Code reviewen** | `code-security-reviewer`, `frontend-usability-optimizer` |
    | **E2E-Tests schreiben** | `e2e-testcase-extractor`, `selenium-test-generator` |
    | **E2E-Results pruefen** | `e2e-result-reviewer`, `selenium-test-reviewer` |
    | **Doku schreiben** | `mkdocs-documentation`, `plant-info-document-generator`, `knowledge-chunk-author` |
    | **RAG-Qualitaet** | `rag-eval-runner` |
    | **HA integrieren** | `ha-integration-requirements-engineer`, `ha-integration-developer`, `/deploy-ha`, `/verify-ha` |
    | **PR vorbereiten** | `/pre-pr`, `pr-to-develop` |
    | **Architektur pruefen** | `/check-architecture`, `/check-api-errors`, `/check-helm` |

---

## Typische Szenarien

### Szenario 1: Feature von Spec bis PR

1. **Anforderung analysieren**: `tech-stack-architect` + `/review-spec`
2. **Details ableiten**: `ha-integration-requirements-engineer` (falls HA)
3. **Implementieren**: `fullstack-developer` oder `/implement`
4. **Testen**: `unit-test-runner` + E2E-Agents
5. **Code reviewen**: `code-security-reviewer` + `frontend-usability-optimizer`
6. **Doku**: `mkdocs-documentation`
7. **PR**: `/pre-pr` + `pr-to-develop`

### Szenario 2: Anforderung auf Qualitaet pruefen

1. **Parallelreview**: `/review-spec REQ-nnn` (startet 4 Agents parallel)
2. **Fachliche Sicht**: `cannabis-indoor-grower-reviewer`, `casual-houseplant-user-reviewer`
3. **Widersprueche**: `requirements-contradiction-analyzer`

### Szenario 3: E2E-Testing neu aufbauen

1. **Testfaelle ableiten**: `e2e-testcase-extractor REQ-nnn`
2. **Tests generieren**: `selenium-test-generator`
3. **Struktur validieren**: `selenium-test-reviewer`
4. **Screenshots analysieren**: `e2e-result-reviewer`

### Szenario 4: Datenqualitaet sichern

1. **Seeds validieren**: `seed-data-validator`
2. **Botanische Korrektheit**: `agrobiology-requirements-reviewer`
3. **Phasen auditieren**: `growing-phase-auditor`
4. **RAG-Knowledge**: `knowledge-chunk-author`

### Szenario 5: HA-Integration erweitern

1. **API-Aenderungen erfassen**: `ha-integration-sync`
2. **HA-Anforderungen ableiten**: `ha-integration-requirements-engineer`
3. **Code implementieren**: `ha-integration-developer`
4. **Deployen**: `/deploy-ha` + `/verify-ha`

---

## Modellwahl

| Modell | Einsatz | Beispiel | Vorteile |
|--------|---------|----------|-----------|
| **opus** | Komplexe Code-Generierung, lange Kontexte | `fullstack-developer`, `e2e-result-reviewer`, `ha-integration-developer` | Hoechste Qualitaet |
| **sonnet** | Standard: Balance Qualitaet/Geschwindigkeit | Meiste Review/Analyzer-Agents | Zuverlassig, schnell |
| **haiku** | Schnelle Textverarbeitung, einfache Checks | `agent-catalog-generator`, `i18n-completeness-checker` | Niedrige Latenz |

---

## Output-Verzeichnisse

| Output-Typ | Verzeichnis | Agents |
|------------|------------|---------|
| Analyse-Reports | `spec/analysis/` | Alle Review-Agents |
| Testfaelle-Specs | `spec/e2e-testcases/` | `e2e-testcase-extractor` |
| E2E-Test-Reports | `test-reports/e2e/` | `selenium-test-generator`, `e2e-result-reviewer` |
| Dokumentation | `docs/de/`, `docs/en/` | `mkdocs-documentation` |
| Pflanzen-Steckbriefe | `spec/knowledge/plants/` | `plant-info-document-generator` |
| RAG-Knowledge | `spec/knowledge/rag/` | `knowledge-chunk-author` |
| Seed-Daten | `src/backend/app/migrations/seed_data/` | `plant-info-document-generator` |
| Source-Code | `src/backend/`, `src/frontend/`, `src/ha-integration/` | `fullstack-developer`, `ha-integration-developer` |

---

## Tipps zur Arbeit mit Agents

### Agent initialisieren

Im Claude Code Chat:
```
/agent tech-stack-architect
Pruefe den Tech-Stack gegen REQ-001
```

### Skills ausfuehren

```
/check-quality
/pre-pr
/review-spec REQ-003
```

### Agents in Sequenzen

Der `pr-to-develop` Agent orchestriert:
1. `unit-test-runner` (Quality Gate)
2. `code-security-reviewer` (bei Security-Changes)
3. Push + PR-Erstellung

### Parallele Reviews via `/review-spec`

Der Skill startet automatisch 4 Agents parallel:
- `agrobiology-requirements-reviewer`
- `it-security-requirements-reviewer`
- `requirements-contradiction-analyzer`
- Optional: `smart-home-ha-reviewer`

### Abhaengigkeiten zwischen Agents

**Sequenziell:**
- `fullstack-developer` → `code-security-reviewer`
- `fullstack-developer` → `frontend-usability-optimizer`

**Parallel (unabhaengig):**
- Alle Review-Agents auf Spezifikationen
- Unit-Test-Runner und Code-Security-Reviewer auf Code

---

## Abgrenzung: Agents vs. Skills

| Kriterium | Agent | Skill |
|-----------|-------|-------|
| **Invocation** | `/agent <name>` | `/skill-name` oder automatisch |
| **Model** | Opus/Sonnet/Haiku | Keine KI (deterministisch) |
| **Interaktiv** | Ja — Nutzer kann Fragen stellen | Nein — praeskriptiv |
| **Output** | Reports, Code, Doku | Checklisten, Fehler |

---

## Code-Sprache & Dokumentation

**Regel (NFR-003):** Source-Code MUSS auf Englisch sein. Dokumentation auf Deutsch.

- Agent-Beschreibungen & Dokumentation: **Deutsch**
- Variablennamen, Klassennamen, Funktionssignaturen: **Englisch**
- Docstrings: Google-Format, Englisch

---

## Katalog-Versioning

**Katalog-Version:** April 2026
**Agents:** 33
**Skills:** 19
**Zuletzt aktualisiert:** 2026-04-05 (via `/update-catalog`)

**Seit v1.0 (Januar 2026):**
- HA-Integration Agents hinzugefuegt
- Skills modularisiert (17 → 19)
- Agent-Typ-Klassifikation eingefuehrt (Technisch vs. Fachlich)
- Kategorisierung nach Workflow-Phase

---

**Feedback oder Fehler?** Bitte aktualisiere diesen Katalog via `/update-catalog` wenn neue Agents oder Skills hinzugefuegt werden.
