---
title: Agent- und Skill-Katalog
description: Übersicht aller verfügbaren Claude Code Agents und Skills im Kamerplanter-Projekt
---

# Agent- und Skill-Katalog

Übersicht aller verfügbaren Claude Code Agents und Skills im Kamerplanter-Projekt.

!!! info "Stand: April 2026 — 34 Agents registriert"
    Dieser Katalog wird vom `agent-catalog-generator` Agent automatisch generiert. Zuletzt aktualisiert: 2026-04-05.

---

## Schnellnavigation

| Kategorie | Agents |
|-----------|--------|
| **Analyse & Review** | 9 |
| **Entwicklung** | 5 |
| **Testing & QA** | 3 |
| **Dokumentation** | 4 |
| **Knowledge & RAG** | 4 |
| **Home Assistant** | 4 |
| **Sonstiges** | 1 |
| **Gesamt** | **34** |

---

## Agents nach Kategorie

### Analyse & Review (9 Agents)

Prüfen bestehende Dokumente, Code, Anforderungen oder Daten auf Qualität und Korrektheit.

| Agent | Modell | Aufgabe |
|-------|--------|---------|
| `tech-stack-architect` | sonnet | Tech-Stack gegen REQ/NFR/UI-NFR validieren |
| `requirements-contradiction-analyzer` | sonnet | Anforderungen auf Widersprüche prüfen |
| `code-security-reviewer` | sonnet | Python/TypeScript auf OWASP-Top-10-Risiken prüfen |
| `it-security-requirements-reviewer` | opus | IT-Sicherheit & DSGVO in Anforderungen prüfen |
| `agrobiology-requirements-reviewer` | sonnet | Fachliche Korrektheit (Botanik, Anbau) prüfen |
| `frontend-design-reviewer` | sonnet | Responsive Design, Kiosk-Modus, WCAG 2.1 prüfen |
| `smart-home-ha-reviewer` | sonnet | Home Assistant Integration & Automations-Tauglichkeit prüfen |
| `growing-phase-auditor` | sonnet | Wachstumsphasen-Daten auf botanische Konsistenz prüfen (3-Quellen-Verifizierung) |
| `casual-houseplant-user-reviewer` | opus | Anforderungen aus Sicht des Casual-Users bewerten |

### Entwicklung (5 Agents)

Implementieren produktiven Code oder führen komplexe Refactorings durch.

| Agent | Modell | Aufgabe |
|-------|--------|---------|
| `fullstack-developer` | opus | Backend (FastAPI, ArangoDB, Celery) + Frontend (React, MUI) implementieren |
| `ha-integration-developer` | opus | Home Assistant Custom Integration & Lovelace Cards entwickeln |
| `ha-integration-sync` | opus | HA-Integration mit Backend-API-Änderungen synchronisieren |
| `ha-integration-requirements-engineer` | sonnet | HA-spezifische Anforderungen aus REQs ableiten |
| `plant-info-document-generator` | sonnet | Detaillierte Pflanzendokumente mit Tabellen-Mapping recherchieren |

### Testing & QA (3 Agents)

Erstellen, reviewen und automatisieren Tests.

| Agent | Modell | Aufgabe |
|-------|--------|---------|
| `e2e-testcase-extractor` | sonnet | E2E-Testfälle aus Spezifikationen systematisch ableiten |
| `selenium-test-generator` | opus | NFR-008-konforme Selenium-Tests mit Page-Objects generieren |
| `selenium-test-reviewer` | sonnet | Bestehende Selenium-Tests auf NFR-008-Konformität prüfen |

### Dokumentation (4 Agents)

Erstellen, aktualisieren und übersetzen Dokumentation sowie konvertieren Daten.

| Agent | Modell | Aufgabe |
|-------|--------|---------|
| `mkdocs-documentation` | sonnet | MkDocs-Material-Dokumentation (DE/EN) erstellen & pflegen |
| `plant-info-to-seed-yaml` | sonnet | Pflanzendokumente zu schema-konformen YAML-Seed-Einträgen konvertieren |
| `png-to-transparent-svg` | sonnet | PNG zu transparentem SVG mit Tracing konvertieren |
| `gemini-graphic-prompt-generator` | sonnet | KAMI Graphic-Prompts aus Spezifikationen generieren |

### Knowledge & RAG (4 Agents)

Managen und optimieren das RAG-System für botanisches Wissen.

| Agent | Modell | Aufgabe |
|-------|--------|---------|
| `rag-eval-runner` | sonnet | RAG-Qualität benchmarken, Fehler klassifizieren, Verbesserungen vorschlagen |
| `knowledge-chunk-author` | sonnet | Knowledge-Base-Chunks erstellen, validieren, Gaps schließen |
| `cannabis-indoor-grower-reviewer` | opus | Indoor-Growing & Cannabis-Anbau aus Grower-Perspektive reviewen |
| `outdoor-garden-planner-reviewer` | opus | Outdoor-Gartenplanung, Fruchtfolge, Mischkultur & Saisonalität reviewen |

### Home Assistant (4 Agents)

Spezialisiert auf Home Assistant Architektur, Integration und Anforderungen.

| Agent | Modell | Aufgabe |
|-------|--------|---------|
| `smart-home-ha-reviewer` | sonnet | HA-Integrations-Architektur & Entity-Design reviewen |
| `ha-integration-developer` | opus | HA Custom Integration nach Spezifikationen implementieren |
| `ha-integration-sync` | opus | HA-Integration mit geänderten Backend-APIs abgleichen |
| `ha-integration-requirements-engineer` | sonnet | Aus REQ-Dokumenten HA-Entity-Mappings & Coordinators ableiten |

### Sonstiges (1 Agent)

| Agent | Modell | Aufgabe |
|-------|--------|---------|
| `agent-catalog-generator` | haiku | Diesen Katalog (agent-catalog.md) neu generieren |

---

## Skills (3 verfügbar)

Orchestrieren mehrere Agents oder führen wiederverwendbare Workflows durch.

### Quality & Checks (1 Skill)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/check-quality` | Technisch | Ruff-Linting (Python) + ESLint (TypeScript) ausführen |

### Workflow (1 Skill)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/pre-pr` | Technisch | Pull-Request vorbereiten: Security-Check + Unit-Tests + UI-Review |

### Generierung (1 Skill)

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/update-catalog` | Technisch | Agent- & Skill-Katalog regenerieren |

---

## Einsatz-Entscheidungshilfe

!!! tip "Welcher Agent für meine Aufgabe?"

    ### Nach Workflow-Phase

    | Phase | Hauptagent | Alternative |
    |-------|-----------|-------------|
    | **Spec/Anforderungen schreiben** | `tech-stack-architect` | — |
    | **Auf Widersprüche prüfen** | `requirements-contradiction-analyzer` | `it-security-requirements-reviewer` (Security-Fokus) |
    | **Fachlich validieren** | `agrobiology-requirements-reviewer` | `cannabis-indoor-grower-reviewer`, `outdoor-garden-planner-reviewer` |
    | **HA-Integration planen** | `smart-home-ha-reviewer` | `ha-integration-requirements-engineer` |
    | **Testfälle ableiten** | `e2e-testcase-extractor` | — |
    | **Code implementieren** | `fullstack-developer` | `ha-integration-developer` (nur HA) |
    | **Security reviewen** | `code-security-reviewer` | `it-security-requirements-reviewer` (für Requirements) |
    | **UI/UX optimieren** | `frontend-design-reviewer` | — |
    | **Selenium-Tests generieren** | `selenium-test-generator` | — |
    | **Tests reviewen** | `selenium-test-reviewer` | — |
    | **Doku schreiben** | `mkdocs-documentation` | — |
    | **Pflanzendaten recherchieren** | `plant-info-document-generator` | — |
    | **Pflanzendaten zu YAML** | `plant-info-to-seed-yaml` | — |
    | **Wachstumsphasen validieren** | `growing-phase-auditor` | — |
    | **RAG-System optimieren** | `rag-eval-runner` | `knowledge-chunk-author` (um Gaps zu schließen) |

    ### Nach Domäne

    | Domäne | Agents |
    |--------|--------|
    | **Tech-Stack & Architektur** | `tech-stack-architect` |
    | **Anforderungs-Management** | `requirements-contradiction-analyzer` |
    | **Security (Code)** | `code-security-reviewer` |
    | **Security (Requirements)** | `it-security-requirements-reviewer` |
    | **Botanik & Anbau** | `agrobiology-requirements-reviewer`, `cannabis-indoor-grower-reviewer`, `outdoor-garden-planner-reviewer`, `growing-phase-auditor` |
    | **Frontend & UX** | `frontend-design-reviewer` |
    | **Home Assistant** | `smart-home-ha-reviewer`, `ha-integration-developer`, `ha-integration-sync`, `ha-integration-requirements-engineer` |
    | **Testing** | `e2e-testcase-extractor`, `selenium-test-generator`, `selenium-test-reviewer` |
    | **Dokumentation** | `mkdocs-documentation`, `png-to-transparent-svg`, `gemini-graphic-prompt-generator` |
    | **Knowledge & Pflanzendaten** | `rag-eval-runner`, `knowledge-chunk-author`, `plant-info-document-generator`, `plant-info-to-seed-yaml`, `growing-phase-auditor` |
    | **Casual User Feedback** | `casual-houseplant-user-reviewer` |

---

## Typische Workflows

### Workflow 1: Feature aus Spezifikation implementieren

1. **Spezifikation reviewen:** `tech-stack-architect` (Tech-Stack), `requirements-contradiction-analyzer` (Widersprüche)
2. **Fachlich validieren:** `agrobiology-requirements-reviewer` (Botanik), `smart-home-ha-reviewer` (HA)
3. **Code schreiben:** `fullstack-developer`
4. **Tests schreiben:** `e2e-testcase-extractor` (Ableitung), `selenium-test-generator` (Implementierung)
5. **Security reviewen:** `code-security-reviewer`
6. **UI optimieren:** `frontend-design-reviewer`
7. **Doku schreiben:** `mkdocs-documentation`
8. **PR vorbereiten:** `/pre-pr` (orchestriert Steps 4–7)

### Workflow 2: Pflanzendaten erfassen & importieren

1. **Recherchieren:** `plant-info-document-generator` (erstellt Markdown-Dokument)
2. **Zu YAML:** `plant-info-to-seed-yaml` (konvertiert zu schema-konformem YAML)
3. **Validieren:** `growing-phase-auditor` (prüft Phasen-Konsistenz)
4. **Importieren:** manuell oder via Seed-Script

### Workflow 3: Home Assistant Integration erweitern

1. **HA-Anforderungen ableiten:** `ha-integration-requirements-engineer` (aus REQ-Dokumenten)
2. **HA-Architektur reviewen:** `smart-home-ha-reviewer`
3. **Implementieren:** `ha-integration-developer`
4. **Mit Backend synchronisieren:** `ha-integration-sync` (bei Backend-Änderungen)

### Workflow 4: RAG-System optimieren

1. **Benchmarken:** `rag-eval-runner` (Smoke- oder Full-Test)
2. **Gaps schließen:** `knowledge-chunk-author` (neue Chunks erstellen)
3. **Validieren:** `growing-phase-auditor` (für botanische Korrektheit)
4. **Wieder testen:** `rag-eval-runner` (Re-Eval)

### Workflow 5: Casual-User Feedback adressieren

1. **Feedback analysieren:** `casual-houseplant-user-reviewer`
2. **Outdoor-Anforderungen prüfen:** `outdoor-garden-planner-reviewer`
3. **Spec überarbeiten** + Workflow 1

---

## Modellwahl

| Modell | Einsatz | Beispiele |
|--------|---------|----------|
| **opus** | Höchste Qualität (komplexe Generierung, Architektur-Entscheidungen) | `fullstack-developer`, `ha-integration-developer`, `cannabis-indoor-grower-reviewer` |
| **sonnet** | Standard (die Regel für ~80% der Aufgaben) | Alle Review-Agents, die meisten Generierungs-Agents |
| **haiku** | Schnell & günstig (einfache Tasks) | `agent-catalog-generator`, `i18n-completeness-checker` |

---

## Output-Pfade

Wo Agents ihre Ergebnisse speichern:

| Agent-Typ | Typischer Output | Beispiel |
|-----------|-----------------|----------|
| **Analyse/Review** | `spec/analysis/...md` | `spec/analysis/tech-stack-review.md` |
| **Backend-Code** | `src/backend/app/` | `src/backend/app/api/v1/` |
| **Frontend-Code** | `src/frontend/src/` | `src/frontend/src/pages/`, `src/frontend/src/components/` |
| **HA-Code** | `src/ha-integration/` | `src/ha-integration/custom_components/kamerplanter/` |
| **Tests** | `tests/e2e/`, `test-reports/` | `tests/e2e/test_*.py`, `test-reports/protokoll.md` |
| **Dokumentation** | `docs/de/`, `docs/en/` | `docs/de/user-guide/`, `docs/de/development/` |
| **Pflanzen-Daten** | `spec/knowledge/plants/`, `spec/knowledge/rag/` | `spec/knowledge/plants/solanum_lycopersicum.md` |
| **HA-Specs** | `spec/ha-integration/` | `spec/ha-integration/HA-CUSTOM-INTEGRATION.md` |

---

## Häufige Fragen

### Wie starte ich einen Agent?

Im Claude Code Chat:
```
/agent <name>
```

oder einfach:
```
Bitte aktiviere den agent-name Agent, um [Aufgabe] zu erledigen.
```

### Wie orchestriere ich mehrere Agents?

Nutze Skills (z.B. `/pre-pr`) oder beschreibe den Workflow im Chat — Claude Code orchestriert die nötigen Agents automatisch.

### Welcher Agent generiert Tests?

- **Testfälle ableiten:** `e2e-testcase-extractor` (erstellt Spec-Dokumente)
- **Code generieren:** `selenium-test-generator` (schreibt Python-Tests)
- **Testen & Reviewen:** `selenium-test-reviewer` (prüft Qualität)

### Welcher Agent schreibt Dokumentation?

`mkdocs-documentation` für MkDocs-Material-Format (DE/EN). Für Pflanzendaten: `plant-info-document-generator` + `plant-info-to-seed-yaml`.

### Was ist die 3-Quellen-Pflicht?

`growing-phase-auditor` und `seed-data-validator` verifizieren botanische Daten durch mindestens 3 unabhängige wissenschaftliche Quellen, um Halluzinationen auszuschließen.

---

## Hinweise

- **Agents arbeiten am besten mit klaren Anforderungen:** Beschreibe deine Aufgabe so konkret wie möglich.
- **HA-Integration ist optional:** Das System funktioniert auch ohne Home Assistant; HA erweitert die Funktionalität.
- **Code-Standard:** Englisch (source code), Deutsch (Doku/Spezifikationen).
- **Modellkosten:** `opus` ist teurer als `sonnet`, aber besser für komplexe Aufgaben.

---

## Version

Katalog-Version: 2026-04-05  
Agents: 34  
Skills: 3  
Letzte Aktualisierung: `agent-catalog-generator` Agent
