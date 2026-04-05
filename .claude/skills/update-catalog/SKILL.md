---
name: update-catalog
description: "Generiert den Agent- und Skill-Katalog (docs/de/development/agent-catalog.md) neu. Liest alle Definitionen aus .claude/agents/ und .claude/skills/, erstellt eine kompakte Uebersicht mit Kategorien, Einsatzempfehlungen und Workflow-Szenarien. Nutze diesen Skill nach Aenderungen an Agents oder Skills."
disable-model-invocation: true
---

# Agent- und Skill-Katalog neu generieren

## Schritt 1: Agent-Definitionen einlesen

Lies alle Agent-Dateien:

```
.claude/agents/*.md
```

Extrahiere aus jeder Datei:

- **Frontmatter:** `name`, `description`, `tools`, `model`
- **Body:** Rolle (erster Absatz), Workflow-Phasen (Ueberschriften), Output-Pfade

## Schritt 2: Skill-Definitionen einlesen

Lies alle Skill-Dateien:

```
.claude/skills/*/SKILL.md
```

Extrahiere aus jeder Datei:

- **Frontmatter:** `name`, `description`
- **Body:** Schritte/Workflow, was der Skill tut

## Schritt 3: Kategorisierung

### 3a. Funktionale Kategorie

Ordne jeden Agent genau einer funktionalen Kategorie zu:

| Kategorie | Kriterium |
|-----------|-----------|
| **Analyse & Review** | Prueft bestehende Dokumente/Code auf Qualitaet, Fehler, Luecken |
| **Entwicklung** | Schreibt produktiven Code (Backend, Frontend, Infra) |
| **Testing & QA** | Erzeugt oder prueft Testfaelle und Tests |
| **Dokumentation** | Erstellt oder pflegt Dokumentation |

Ordne jeden Skill genau einer funktionalen Kategorie zu:

| Kategorie | Kriterium |
|-----------|-----------|
| **Quality & Checks** | Prueft Code-Qualitaet, Architektur, Dependencies |
| **Deployment** | Baut, deployed oder verifiziert Infrastruktur |
| **Workflow** | Review, Implementierung, PR-Vorbereitung |
| **Generierung** | Erzeugt Dokumente, Tests, Wissen |

### 3b. Typ-Klassifikation (Technisch vs. Fachlich)

Ordne ZUSAETZLICH jeden Agent und Skill einem Typ zu:

| Typ | Kriterium | Beispiele |
|-----|-----------|-----------|
| **Technisch** | Allgemeine Softwareentwicklung, Testing, CI/CD, Security, Architektur, Release-Management. Wiederverwendbar in jedem Softwareprojekt. | `fullstack-developer`, `code-security-reviewer`, `unit-test-runner`, `pr-to-develop`, `/check-quality`, `/pre-pr` |
| **Fachlich** | Domaenenspezifisch fuer Pflanzenpflege, Agrobiologie, Indoor-Growing, Home-Assistant-Integration, RAG-Pflanzenwissen. Nur im Kamerplanter-Kontext sinnvoll. | `agrobiology-requirements-reviewer`, `cannabis-indoor-grower-reviewer`, `growing-phase-auditor`, `ha-integration-developer`, `plant-info-document-generator`, `/gen-knowledge`, `/deploy-ha` |

**Entscheidungsregel:** Waere der Agent/Skill in einem beliebigen anderen Softwareprojekt (z.B. E-Commerce, Fintech) nuetzlich? → **Technisch**. Bezieht er sich auf Pflanzen, Botanik, Growing, Home-Assistant-fuer-Pflanzen, oder Kamerplanter-spezifisches Domaenenwissen? → **Fachlich**.

## Schritt 4: Katalog-Dokument schreiben

Schreibe die Datei `docs/de/development/agent-catalog.md` im MkDocs-Material-Format.

### Pflicht-Struktur (diese Reihenfolge einhalten):

```markdown
---
title: Agent- und Skill-Katalog
description: Uebersicht aller verfuegbaren Claude Code Agents und Skills im Kamerplanter-Projekt
---

# Agent- und Skill-Katalog

Uebersicht aller verfuegbaren Claude Code Agents und Skills im Kamerplanter-Projekt.

!!! info "Stand: [Monat Jahr] -- [N] Agents, [M] Skills registriert"
    Dieser Katalog wird vom `/update-catalog` Skill automatisch generiert.

---

## Schnellnavigation

| Kategorie | Technisch | Fachlich | Gesamt |
|-----------|-----------|----------|--------|
| **Analyse & Review** | [N] | [N] | [N] |
| **Entwicklung** | [N] | [N] | [N] |
| **Testing & QA** | [N] | [N] | [N] |
| **Dokumentation** | [N] | [N] | [N] |
| **Skills** | [N] | [N] | [N] |

---

## Agents

### Analyse & Review ([N] Agents)

Pruefen bestehende Dokumente, Code oder Anforderungen.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `name` | T/F | modell | Einzeiler max. 10 Woerter |

### Entwicklung ([N] Agents)

Schreiben produktiven Code.

| Agent | Typ | Modell | Aufgabe |
|-------|-----|--------|---------|
| `name` | T/F | modell | Einzeiler |

### Testing & QA ([N] Agents)

Test-Erstellung und -Verwaltung.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `name` | T/F | modell | Einzeiler |

### Dokumentation ([N] Agents)

Dokumentations-Erstellung und -Pflege.

| Agent | Typ | Modell | Fokus |
|-------|-----|--------|-------|
| `name` | T/F | modell | Einzeiler |

---

!!! note "Legende: Typ-Spalte"
    **T** = Technisch (allgemeine Softwareentwicklung, in jedem Projekt nuetzlich)
    **F** = Fachlich (domaenenspezifisch fuer Pflanzenpflege/Kamerplanter)

---

## Skills

### Quality & Checks

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/name` | T/F | Einzeiler |

### Deployment

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/name` | T/F | Einzeiler |

### Workflow

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/name` | T/F | Einzeiler |

### Generierung

| Skill | Typ | Beschreibung |
|-------|-----|-------------|
| `/name` | T/F | Einzeiler |

---

## Einsatz-Entscheidungshilfe

!!! tip "Welcher Agent/Skill fuer meine Aufgabe?"

    **Nach Workflow-Phase:**

    | Phase | Agent/Skill |
    |-------|-------------|
    | Anforderungen spezifizieren | `tech-stack-architect`, ... |
    | Anforderungen reviewen | `agrobiology-requirements-reviewer`, ... |
    | Implementieren | `fullstack-developer`, `/implement` |
    | Lokal testen | `unit-test-runner`, `/check-quality` |
    | Code reviewen | `code-security-reviewer`, ... |
    | Doku schreiben | `mkdocs-documentation` |
    | PR vorbereiten | `pr-to-develop`, `/pre-pr` |
    | HA deployen | `ha-integration-developer`, `/deploy-ha` |

---

## Typische Szenarien

### Szenario 1: Feature implementieren

1. Spezifikation pruefen: `tech-stack-architect` + `it-security-requirements-reviewer`
2. Code schreiben: `fullstack-developer`
3. Tests ausfuehren: `/check-quality`
4. Security reviewen: `code-security-reviewer`
5. UI optimieren: `frontend-usability-optimizer`
6. Dokumentation: `mkdocs-documentation`
7. PR vorbereiten: `/pre-pr` + `pr-to-develop`

### Szenario 2: E2E-Tests fuer Feature

1. Testfaelle ableiten: `e2e-testcase-extractor`
2. Tests generieren: `selenium-test-generator`
3. Tests reviewen: `selenium-test-reviewer`
4. Screenshots analysieren: `e2e-result-reviewer`

### Szenario 3: Anforderung reviewen

1. Tech-Machbarkeit: `tech-stack-architect`
2. Botanische Korrektheit: `agrobiology-requirements-reviewer`
3. Security & DSGVO: `it-security-requirements-reviewer`
4. Widersprueche: `requirements-contradiction-analyzer`
5. Nutzer-Perspektive: `casual-houseplant-user-reviewer` + weitere Reviewer

---

## Modellwahl

| Modell | Einsatz | Beispiel |
|--------|---------|----------|
| **opus** | Komplexe Aufgaben, Code-Generierung | fullstack-developer, ha-integration-developer |
| **sonnet** | Standard: Balance Qualitaet/Geschwindigkeit | Meiste Analyse & Reviews |
| **haiku** | Schnell, einfache Pruefungen | i18n-checker, agent-catalog-generator |

---

## Output-Verzeichnisse

| Output-Typ | Verzeichnis |
|------------|------------|
| Analyse-Reports | `spec/analysis/` |
| Testfall-Spezifikationen | `spec/e2e-testcases/` |
| E2E-Test-Reports | `test-reports/` |
| Dokumentation | `docs/de/` + `docs/en/` |
| Design-Prompts | `spec/design/` |
| Seed-Daten | `src/backend/app/migrations/seed_data/` |
| Code | `src/backend/`, `src/frontend/` |

---

## Tipps

- **Agent starten:** Im Claude Code Chat den `agent-catalog-generator` Agent verwenden
- **Skill ausfuehren:** `/update-catalog` im Claude Code Chat
- **Agents koennen parallel laufen** (keine Abhaengigkeiten zwischen Agents)
- **Englischer Code, deutsche Docs:** NFR-003

---

**Katalog-Version:** [Monat Jahr] | **[N] Agents, [M] Skills** | **Zuletzt aktualisiert:** [YYYY-MM-DD]
```

### Wichtige Regeln:

- **Platzhalter ersetzen:** Alle `[N]`, `[M]`, `[Monat Jahr]`, `[YYYY-MM-DD]` durch echte Werte
- **Alphabetisch sortieren:** Agents innerhalb jeder Kategorie nach Name
- **Max. 10 Woerter** pro Fokus/Aufgabe in den Tabellen
- **Keine Wiederholung** des vollstaendigen Agent/Skill-Inhalts
- **Skills mit `/` Praefix** in der Entscheidungshilfe (`/deploy-ha`, `/check-quality`)
- **Deutsch** -- konsistent mit Projekt-Dokumentationssprache
- **Keine Umlaute in der Datei** -- verwende ae, oe, ue, ss (MkDocs-Kompatibilitaet)

## Schritt 5: Zusammenfassung

Gib nach dem Schreiben eine kompakte Zusammenfassung aus:

1. Anzahl Agents (nach Kategorie)
2. Anzahl Skills (nach Kategorie)
3. Modellverteilung (opus/sonnet/haiku)
4. Dateipfad
