---
title: Agent- und Skill-Katalog
description: Uebersicht aller verfuegbaren Claude Code Agents und Skills im Kamerplanter-Projekt
---

# Agent- und Skill-Katalog

Uebersicht aller verfuegbaren Claude Code Agents und Skills im Kamerplanter-Projekt.

!!! info "Stand: April 2026 -- 35 Agents, 19 Skills registriert"
    Dieser Katalog wird vom `/update-catalog` Skill automatisch generiert.

---

## Schnellnavigation

| Kategorie | Technisch | Fachlich | Gesamt |
|-----------|-----------|----------|--------|
| **Analyse & Review** | 5 | 5 | 10 |
| **Entwicklung** | 3 | 4 | 7 |
| **Testing & QA** | 5 | 0 | 5 |
| **Dokumentation** | 2 | 0 | 2 |
| **Spezialagenten** | 6 | 5 | 11 |
| **Skills** | 12 | 7 | 19 |

---

## Agents

### Analyse & Review (10 Agents)

Pruefung bestehender Dokumente, Code oder Anforderungen auf Qualitaet, Fehler, Luecken.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `agrobiology-requirements-reviewer` | F | sonnet | Botanische Korrektheit und Vollstaendigkeit von Anforderungen |
| `cannabis-indoor-grower-reviewer` | F | opus | Indoor-Growing-Perspektive fuer professionelle Nutzer |
| `casual-houseplant-user-reviewer` | F | opus | Laien-Nutzer-Perspektive, Anfaenger-Freundlichkeit |
| `code-security-reviewer` | T | sonnet | OWASP Top 10, Injection, Auth-Bypass, Tenant-Isolation |
| `docs-freshness-checker` | T | sonnet | MkDocs auf Aktualitaet, Vollstaendigkeit, DE/EN-Paritaet |
| `i18n-completeness-checker` | T | haiku | i18n-Dateien auf fehlende Keys, verwaiste Keys pruefen |
| `it-security-requirements-reviewer` | T | sonnet | IT-Sicherheit, Datensparsamkeit, DSGVO-Konformitaet |
| `outdoor-garden-planner-reviewer` | F | sonnet | Outdoor-Gartenbau-Perspektive fuer Anforderungen |
| `requirements-contradiction-analyzer` | T | sonnet | Widersprueche zwischen REQ/NFR erkennen |
| `smart-home-ha-reviewer` | F | sonnet | Home-Assistant-Integrations-Tauglichkeit pruefen |

### Entwicklung (7 Agents)

Schreiben produktiven Code, APIs, Komponenten und Integrationen.

| Agent | Typ | Modell | Aufgabe |
|-------|-----|--------|---------|
| `frontend-usability-optimizer` | T | sonnet | React/MUI-Seiten und Formulare auf Usability optimieren |
| `fullstack-developer` | T | opus | Backend (Python/FastAPI) + Frontend (React/TS) implementieren |
| `ha-integration-developer` | F | opus | Home-Assistant Custom Integration entwickeln |
| `ha-integration-sync` | F | opus | HA-Integration mit Backend-API synchronisieren |
| `knowledge-chunk-author` | F | sonnet | RAG-Knowledge-Base-Chunks erstellen und verbessern |
| `plant-info-document-generator` | F | sonnet | Detaillierte Pflanzen-Informationsdokumente recherchieren |
| `plant-info-to-seed-yaml` | F | sonnet | Pflanzendokumente in YAML-Seed-Eintraege konvertieren |

### Testing & QA (5 Agents)

Test-Erstellung, -Verwaltung und Analyse.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `e2e-result-reviewer` | T | opus | E2E-Testergebnisse visuell gegen Specs pruefen |
| `e2e-testcase-extractor` | T | sonnet | E2E-Testfaelle aus Anforderungen systematisch ableiten |
| `selenium-test-generator` | T | opus | NFR-008-konforme Selenium-E2E-Tests generieren |
| `selenium-test-reviewer` | T | sonnet | Selenium-Tests auf NFR-008-Konformitaet reviewen |
| `unit-test-runner` | T | sonnet | Unit-Tests (pytest, vitest) + Linting (Ruff, ESLint) ausfuehren |

### Dokumentation (2 Agents)

Dokumentations-Erstellung und -Pflege.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `mkdocs-documentation` | T | sonnet | MkDocs-Material-Dokumentation (DE+EN) erstellen |
| `gemini-graphic-prompt-generator` | T | sonnet | KI-Bildgenerations-Prompts fuer Icons und Illustrationen |

### Spezialagenten (11 Agents)

Spezialisierte Aufgaben mit domaenenspezifischem Wissen.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `agent-catalog-generator` | T | haiku | Diesen Agent- und Skill-Katalog regenerieren |
| `frontend-design-reviewer` | T | sonnet | Frontend auf responsive Design, Kiosk-Modus, WCAG pruefen |
| `growing-phase-auditor` | F | sonnet | Wachstumsphasen-Daten auf biologische Korrektheit pruefen |
| `ha-integration-requirements-engineer` | F | sonnet | HA-Integrations-Anforderungen aus REQs ableiten |
| `png-to-transparent-svg` | T | sonnet | PNG mit Schachbrett-Hintergrund zu transparentem SVG |
| `pr-to-develop` | T | sonnet | GitHub PR vorbereiten, lokale CI validieren, mergen |
| `rag-eval-runner` | F | sonnet | RAG-Qualitaets-Benchmarks ausfuehren und analysieren |
| `seed-data-validator` | F | sonnet | YAML-Seed-Daten auf Qualitaet und Konsistenz pruefen |
| `target-audience-analyzer` | T | sonnet | Zielgruppen und Nutzer-Profile aus Anforderungen ableiten |
| `tech-stack-architect` | T | opus | Tech-Stack gegen Anforderungen validieren |

---

!!! note "Legende: Typ-Spalte"
    **T** = Technisch (allgemeine Softwareentwicklung, in jedem Projekt nuetzlich)
    **F** = Fachlich (domaenenspezifisch fuer Pflanzenpflege/Kamerplanter/AgriTech)

---

## Skills

Sind in 4 Kategorien organisiert: Quality, Deployment, Workflow, Generierung.

### Quality & Checks (5 Skills)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/check-quality` | T | Backend Linting (ruff) + Tests (pytest) + Frontend Linting + TypeScript + Tests (vitest) |
| `/check-architecture` | T | 5-Layer-Architektur-Verstaesse in Code erkennen und melden |
| `/check-api-errors` | T | API-Fehlerbehandlung auf NFR-006-Konformitaet pruefen |
| `/check-helm` | T | Helm-Charts auf bjw-s-Common und Skaffold-Konformitaet validieren |
| `/check-test-pyramid` | T | Test-Verteilung (Unit/Integration/E2E) und Coverage validieren |

### Deployment (4 Skills)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/deploy-ha` | F | HA-Integration in Kubernetes deployen (kubectl cp, Cache Clear, Restart) |
| `/verify-ha` | F | HA-Custom-Integration auf Fehler pruefen |
| `/check-slo` | T | SLO-Metriken und Performance-Budgets validieren |
| `/check-retention` | T | Datenschutz-Aufbewahrungsrichtlinien im Code enforcing |

### Workflow (5 Skills)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/implement` | T | Feature aus REQ-Dokument implementieren (Spec→Plan→Code) |
| `/pre-pr` | T | Vor PR: Quality-Gate, Security, i18n, Doku-Check |
| `/review-spec` | F | Anforderungs-Dokumente auf Vollstaendigkeit pruefen |
| `/spec-status` | T | Implementierungs-Status aller REQ/NFR tracken |
| `/test-extract` | T | E2E-Testfaelle aus Anforderungen ableiten |

### Generierung (5 Skills)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/gen-knowledge` | F | RAG-Knowledge-Dokumente (YAML) fuer Pflanzenwissen erstellen |
| `/update-catalog` | T | Diesen Agent- und Skill-Katalog regenerieren |
| `/check-deps` | T | Python + Node Dependency-Updates und CVE-Vulnerabilities scannen |
| `/check-ui-crud` | T | CRUD-UI auf NFR-010 (Listenansicht, Dialoge) validieren |
| `/ha-derive` | F | HA-Integrations-Details aus REQ-Dokumenten ableiten |

---

## Einsatz-Entscheidungshilfe

!!! tip "Welcher Agent/Skill fuer meine Aufgabe?"

    **Nach Workflow-Phase:**

    | Phase | Agent/Skill |
    |-------|-------------|
    | Anforderungen schreiben | `tech-stack-architect`, `/review-spec` |
    | Anforderungen reviewen | `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`, `casual-houseplant-user-reviewer` |
    | Implementieren | `fullstack-developer`, `/implement` |
    | Lokal testen | `/check-quality`, `unit-test-runner` |
    | Code reviewen | `code-security-reviewer`, `frontend-usability-optimizer` |
    | Doku schreiben | `mkdocs-documentation` |
    | Doku pruefen | `docs-freshness-checker` |
    | PR vorbereiten | `/pre-pr`, `pr-to-develop` |
    | E2E-Tests | `e2e-testcase-extractor` → `selenium-test-generator` |
    | E2E-Results | `e2e-result-reviewer` |
    | HA-Integration | `ha-integration-requirements-engineer` → `ha-integration-developer` |
    | HA deployen | `/deploy-ha` |
    | Knowledge-Base | `/gen-knowledge`, `knowledge-chunk-author` |
    | RAG-Qualitaet | `rag-eval-runner` |

---

## Typische Szenarien

### Szenario 1: Feature implementieren (Spec → Code → PR)

1. Spezifikation pruefen: `tech-stack-architect`
2. Anforderungen reviewen: `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`
3. Implementieren: `fullstack-developer`
4. Lokal testen: `/check-quality`
5. Security reviewen: `code-security-reviewer`
6. UI optimieren: `frontend-usability-optimizer`
7. Dokumentation: `mkdocs-documentation`
8. PR vorbereiten: `/pre-pr`, `pr-to-develop`

### Szenario 2: E2E-Tests fuer Feature

1. Testfaelle ableiten: `e2e-testcase-extractor`
2. Tests generieren: `selenium-test-generator` (NFR-008-konform)
3. Tests reviewen: `selenium-test-reviewer`
4. Ergebnisse analysieren: `e2e-result-reviewer`

### Szenario 3: Anforderung reviewen

1. Tech-Machbarkeit: `tech-stack-architect`
2. Botanische Korrektheit: `agrobiology-requirements-reviewer`
3. IT-Security & DSGVO: `it-security-requirements-reviewer`
4. Widersprueche: `requirements-contradiction-analyzer`
5. Nutzer-Perspektiven: `casual-houseplant-user-reviewer`, `cannabis-indoor-grower-reviewer`, `outdoor-garden-planner-reviewer`

### Szenario 4: Home Assistant Integration erweitern

1. Anforderungen ableiten: `ha-integration-requirements-engineer`
2. HA reviewen: `smart-home-ha-reviewer`
3. Implementieren: `ha-integration-developer`
4. Mit Backend synchronisieren: `ha-integration-sync`
5. Deployen: `/deploy-ha`

### Szenario 5: RAG-System verbessern

1. Qualitaet benchmarken: `rag-eval-runner`
2. Gaps schliessen: `knowledge-chunk-author`
3. Neu testen: `rag-eval-runner`

---

## Modellwahl

| Modell | Einsatz | Beispiel |
|--------|---------|----------|
| **opus** | Komplexe Generierung, Architektur-Entscheidungen, umfangreiche Analysen | fullstack-developer, ha-integration-developer, e2e-result-reviewer, casual-houseplant-user-reviewer, tech-stack-architect, selenium-test-generator |
| **sonnet** | Standard: Balance Qualitaet/Geschwindigkeit | Die meisten Agents (Reviews, Code-Fixes, Dokumentation) |
| **haiku** | Schnell, einfache Pruefungen | agent-catalog-generator, i18n-completeness-checker |

---

## Output-Verzeichnisse

| Output-Typ | Verzeichnis |
|------------|------------|
| Analyse-Reports | `spec/analysis/` |
| Testfall-Spezifikationen | `spec/e2e-testcases/` |
| E2E-Test-Reports | `test-reports/` |
| Dokumentation | `docs/de/`, `docs/en/` |
| Design-Prompts | `spec/design/` |
| Seed-Daten | `src/backend/app/migrations/seed_data/` |
| Knowledge-Base | `spec/knowledge/rag/` |
| Code | `src/backend/`, `src/frontend/` |
| HA-Integration | `custom_components/kamerplanter/` |

---

## Tipps

- **Agent starten:** Im Claude Code Chat den Agent-Namen aufrufen
- **Skill ausfuehren:** Im Chat `/skillname` eingeben
- **Agents parallel:** Agents haben keine Abhaengigkeiten, koennen parallel laufen
- **Englischer Code, deutsche Docs:** NFR-003 — Source Code MUSS Englisch sein

---

**Katalog-Version:** April 2026 | **35 Agents, 19 Skills** | **Zuletzt aktualisiert:** 2026-04-06
