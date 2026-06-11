---
ID: NFR-014
Titel: Nuclei-Security-Scanning — Template-basierte Schwachstellenprüfung Frontend & Backend
Kategorie: Sicherheit / Qualitätssicherung
Unterkategorie: DAST, Vulnerability-Scanning, Template-basierte Erkennung
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Nuclei (ProjectDiscovery), GitHub Actions, SARIF, OpenAPI
Status: Genehmigt
Priorität: Hoch
Version: 1.1
Autor: QA / Security Engineering
Datum: 2026-04-28
Tags: [security, dast, nuclei, vulnerability-scanning, cve, misconfiguration, exposures, ci-gate, sarif]
Abhängigkeiten: [NFR-007, NFR-008, NFR-008a, NFR-009, NFR-015]
Betroffene Module: [src/backend, src/frontend, helm, .github/workflows]
---

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.1 | 2026-04-28 | Spec-Followup nach PR-#115-Review: Pinning-Logik in §3.3 auf `git clone` + `git checkout SHA` korrigiert (vorher bestand das `.git`-Verzeichnis bei `-update-templates` nicht zuverlässig). Nightly-Cron in §4.2 von `0 1 * * *` auf `0 0 * * *` vorgezogen, damit das schnellere Tool zuerst gegen Staging läuft (ZAP folgt 60 Min später). Frontend-Storage-Check in `kamerplanter-jwt-leak.yaml` (§3.2) ergänzt. |
| 1.0 | 2026-04-28 | Erstversion — Template-basiertes Security-Scanning für Frontend, Backend und exponierte Infrastruktur. Pflicht-Template-Sets, CI-Gate, SARIF-Reporting, Triage-Workflow und Akzeptanzkriterien definiert. |

# NFR-014: Nuclei-Security-Scanning

## Abgrenzung zu bestehenden NFRs

| NFR | Fokus | Definiert |
|---|---|---|
| NFR-008 | Funktionale Teststrategie, Testpyramide | **Funktionale** Tests (Unit, Integration, E2E) |
| NFR-008a | E2E-Selenium-Konventionen | **Wie** Selenium-Tests aufgebaut sind |
| NFR-009 | Dependency-Lifecycle, CVE-Scanning auf Paket-Ebene (`npm audit`, `pip-audit`) | **Sicherheit der Dependencies** |
| **NFR-014 (dieses Dokument)** | Template-basiertes Schwachstellen-Scanning gegen die laufende Anwendung | **Sicherheit der eingesetzten Anwendung** |
| NFR-015 | OWASP-ZAP-Scanning (Spider + Active/Passive Scan) | **Tiefes** DAST-Scanning, Business-Logic-Schwachstellen |

NFR-014 und NFR-015 sind **komplementär**:

- **Nuclei** (NFR-014) ist breit, schnell und Template-getrieben. Es prüft auf bekannte CVEs, Default-Credentials, Misconfigurations, exponierte Pfade und Tech-Stack-Indikatoren. Laufzeit: Minuten.
- **OWASP ZAP** (NFR-015) ist tief, langsamer und verhaltensbasiert. Es spidert die Anwendung, fuzzed Parameter und sucht nach Klassen von Schwachstellen (Injection, XSS, Broken Auth). Laufzeit: bis zu mehrere Stunden.

NFR-009 schützt vor verwundbaren Bibliotheken **bevor** sie deployt werden. NFR-014 schützt vor Konfigurationsfehlern und unsicheren Endpunkten **nachdem** die Anwendung deployt ist.

---

## 1. Business Case

### 1.1 User Stories

**Als** Security Officer
**möchte ich** automatisierte Schwachstellen-Scans gegen jede deployte Version
**um** Misconfigurations, exponierte Endpunkte und bekannte CVEs vor produktiver Freigabe zu erkennen.

**Als** DevOps Engineer
**möchte ich** dass jeder Pull Request gegen eine Staging-Instanz mit Nuclei gescannt wird
**um** Regressionen in der Sicherheitskonfiguration sofort sichtbar zu machen.

**Als** Backend-Entwickler
**möchte ich** dass exponierte Debug-Endpunkte, Header mit Informationsleck und vergessene Standard-Logins automatisch erkannt werden
**um** keine kritische Konfiguration zu übersehen.

**Als** Frontend-Entwickler
**möchte ich** dass das ausgelieferte Bundle, statische Assets und Reverse-Proxy-Konfiguration auf Information-Disclosure geprüft werden
**um** keine `.env`-Dateien, Source-Maps oder Backup-Dateien produktiv erreichbar zu machen.

**Als** Auditor
**möchte ich** archivierte Scan-Reports mit Commit-Hash und Zeitstempel
**um** den Sicherheitszustand zu jedem deployten Stand nachweisen zu können.

### 1.2 Geschäftliche Motivation

**Sicherheit**:
- Kamerplanter verarbeitet personenbezogene Daten (REQ-023, REQ-024, REQ-025) und Sensor-/Erntedaten — ein Information Disclosure ist unmittelbar DSGVO-relevant.
- Über 60 % aller produktiv ausgenutzten Schwachstellen in Web-Anwendungen sind auf bekannte Misconfigurations oder ungeschützte Standardpfade zurückzuführen, nicht auf neuartige Zero-Days.
- Template-basiertes Scanning erkennt diese Klasse von Fehlern in Sekunden — manuelle Reviews skalieren nicht über alle Service-Updates hinweg.

**Geschwindigkeit & Skalierung**:
- Nuclei führt 10.000+ Templates parallel in unter 10 Minuten gegen eine Staging-Instanz aus.
- Im Vergleich zu OWASP ZAP Full-Scan (Stunden) ist Nuclei für den PR-Gate-Schritt deutlich besser geeignet.
- Die Template-Bibliothek wird kontinuierlich von der Community aktualisiert — neue CVEs sind innerhalb weniger Tage abdeckbar, ohne eigenen Scanner-Code zu schreiben.

**Reproduzierbarkeit**:
- YAML-Templates sind les- und versionierbar — Findings können exakt einer Template-ID zugeordnet werden.
- SARIF-Output integriert sich direkt mit GitHub Code Scanning, womit Findings im PR sichtbar werden.

### 1.3 Fachliche Beschreibung

Praktisches Beispiel:

> **Szenario**: Ein Entwickler fügt versehentlich `app.mount("/static", StaticFiles(directory=".", html=True))` in eine FastAPI-Konfiguration ein. Damit wird das Repository-Root inklusive `.env`, `pyproject.toml` und Backups produktiv ausgeliefert.
> **Ohne NFR-014**: Der Fehler bleibt unerkannt, bis er in einem manuellen Audit auffällt — oder ein Angreifer ihn ausnutzt.
> **Mit NFR-014**: Beim PR-Build deployt Skaffold die Anwendung in eine Ephemeral-Namespace, Nuclei läuft mit den Templates `exposures/files/*` und `misconfiguration/*` und meldet das exponierte `.env` als High-Severity-Finding. Der CI-Gate blockiert den Merge.

---

## 2. Scope & Geltungsbereich

### 2.1 Was MUSS gescannt werden

| Ziel | Erfasst durch | Frequenz |
|---|---|---|
| Backend-API (FastAPI) — `/api/v1/...` | Nuclei `http://backend:8000` | Pro PR + täglich |
| Frontend-Bundle & statische Assets — `/` | Nuclei `http://frontend:5173` | Pro PR + täglich |
| Reverse-Proxy / Ingress (Traefik) | Nuclei gegen Public-Hostname auf Staging | Täglich |
| OpenAPI-Spezifikation — `/api/v1/openapi.json` | Nuclei `-input openapi.json` | Pro PR |
| Kamerplanter-Knowledge-Service (sofern deployt) | Nuclei gegen Service-URL | Pro PR + täglich |

### 2.2 Was MUSS gefunden werden

**MUSS** erkannt werden — diese Template-Kategorien sind verpflichtend aktiviert:

| Kategorie | Templates | Beispiele für relevante Findings |
|---|---|---|
| `exposures/files` | ~250 Templates | `.env`, `.git/config`, `pyproject.toml`, Backups (`*.bak`, `*~`), Source-Maps |
| `exposures/configs` | ~80 Templates | `nginx.conf`, `application.yml`, `docker-compose.yml`, `kubeconfig` |
| `exposures/tokens` | ~60 Templates | AWS Keys, GitHub Tokens, JWT in Body, Slack-Webhooks |
| `misconfiguration` | ~700 Templates | Debug-Mode aktiv, fehlende Security-Headers, öffentliche Admin-Panels |
| `default-logins` | ~150 Templates | Default-Credentials in Tools, Admin-Panels, Dashboards |
| `cves` | ~5.000 Templates (gefiltert nach Tech-Stack) | Bekannte CVEs in eingesetzten Frameworks |
| `vulnerabilities/generic` | ~200 Templates | Open Redirect, Path Traversal, SSRF (passiv erkannt) |
| `technologies` | ~400 Templates | Tech-Stack-Detection (für nachgelagerte CVE-Filterung) |
| `http/headers` (custom) | Eigene Templates | Pflicht-Security-Headers (CSP, HSTS, X-Content-Type-Options) |

### 2.3 Was wird ausdrücklich NICHT durch NFR-014 abgedeckt

- **Tiefes Fuzzing** und Active-Scan von Parametern → siehe NFR-015 (ZAP Full-Scan).
- **Authentifizierte Business-Logic-Tests** (z. B. Tenant-Isolation, AuthZ-Matrix) → siehe NFR-015 + dedizierte Selenium-Tests aus NFR-008a.
- **CVE-Scanning der Dependencies vor Deployment** → siehe NFR-009.
- **SAST / Source-Code-Analyse** → außerhalb des Scopes dieses NFR (eigenes Backlog).

---

## 3. Template-Strategie

### 3.1 Pflicht-Template-Sets

**MUSS**: Folgende Tag-Kombinationen werden in CI ausgeführt:

```bash
# PR-Gate (schneller Lauf, < 5 min)
nuclei \
  -tags "exposure,misconfig,default-login,token-spray" \
  -severity "medium,high,critical" \
  -target "$STAGING_URL" \
  -j -o results.jsonl \
  -sarif-export results.sarif \
  -rl 50 \
  -timeout 10

# Daily-Scan (vollständig, < 30 min)
nuclei \
  -tags "exposure,misconfig,default-login,cve,vulnerability,intrusive" \
  -severity "low,medium,high,critical" \
  -target "$STAGING_URL" \
  -j -o results.jsonl \
  -sarif-export results.sarif \
  -rl 100 \
  -timeout 15
```

**MUSS**: Das öffentliche `nuclei-templates`-Repository (`projectdiscovery/nuclei-templates`) wird vor jedem Lauf via `-update-templates` aktualisiert.

**SOLL**: Templates der Kategorie `intrusive` und `dos` werden ausschließlich gegen dedizierte Test-Umgebungen ausgeführt — niemals gegen Staging mit produktiven Daten.

### 3.2 Eigene Templates

**MUSS**: Projekt-eigene Templates liegen unter `tests/security/nuclei-templates/` und werden mitversioniert.

| Template | Zweck | Severity |
|---|---|---|
| `kamerplanter-security-headers.yaml` | Prüft `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` | High |
| `kamerplanter-cors-misconfig.yaml` | Prüft, dass `Access-Control-Allow-Origin: *` nicht in Kombination mit `Allow-Credentials` ausgeliefert wird | High |
| `kamerplanter-debug-endpoints.yaml` | Prüft, dass `/docs`, `/redoc`, `/openapi.json` in produktiver Umgebung gemäß Konfiguration entweder gesperrt oder authentifiziert sind | Medium |
| `kamerplanter-tenant-leak.yaml` | Prüft, dass `tenant_key` / `tenant_slug` nicht in Fehlerantworten unauthentifizierter Requests erscheint | High |
| `kamerplanter-jwt-leak.yaml` | Prüft, dass JWTs nicht in URL-Pfaden, Logs (`/health`-Response), HTML-Antworten oder im Frontend-Bundle in `localStorage`/`sessionStorage`/Service-Worker-Caches geschrieben werden (Headless-Mode mit `headless: true`) | Critical |
| `kamerplanter-source-map.yaml` | Prüft, dass `*.map`-Dateien nicht in produktiven Frontend-Builds ausgeliefert werden | Medium |

Beispiel — `kamerplanter-security-headers.yaml`:

```yaml
id: kamerplanter-security-headers

info:
  name: Kamerplanter — Pflicht-Security-Headers
  author: kamerplanter-security
  severity: high
  description: |
    Verifiziert, dass alle in NFR-014 §3.2 geforderten Security-Headers
    bei jeder HTTP-Antwort des Reverse-Proxy gesetzt sind.
  reference:
    - spec/nfr/NFR-014_Nuclei-Security-Scanning.md
  tags: kamerplanter,headers,misconfig

http:
  - method: GET
    path:
      - "{{BaseURL}}/"
    matchers-condition: and
    matchers:
      - type: word
        part: header
        words:
          - "strict-transport-security:"
          - "content-security-policy:"
          - "x-content-type-options: nosniff"
          - "referrer-policy:"
        condition: and
        case-insensitive: true
      - type: status
        status:
          - 200
          - 301
          - 302
```

### 3.3 Template-Versionierung & Reproduzierbarkeit

**MUSS**: Der Lauf in CI pinnt die Template-Sammlung auf einen konkreten Commit-SHA — nicht auf `latest`. Der Pfad MUSS ein Git-Klon sein, da `nuclei -update-templates` einen Tarball-Sync durchführt und kein `.git`-Verzeichnis erzeugt:

```yaml
- name: Pin Nuclei Templates
  env:
    NUCLEI_TEMPLATES_SHA: ${{ vars.NUCLEI_TEMPLATES_SHA }}
  run: |
    git clone --filter=blob:none \
      https://github.com/projectdiscovery/nuclei-templates.git \
      ./nuclei-templates
    git -C ./nuclei-templates checkout "$NUCLEI_TEMPLATES_SHA"

- name: Run Nuclei against pinned templates
  run: |
    nuclei -t ./nuclei-templates -tags "${TAGS}" -severity "${SEVERITY}" ...
```

**MUSS**: `NUCLEI_TEMPLATES_SHA` ist als Repository-Variable hinterlegt und wird wöchentlich automatisch via Renovate aktualisiert (vgl. NFR-009). Renovate-Custom-Manager pinnt den SHA in einer dedizierten Config-Datei (`.github/renovate-pins.yaml`), damit der Update-PR nur diese Variable berührt.

**SOLL**: Alle eigenen Templates werden vor dem Merge mit `nuclei -validate -t tests/security/nuclei-templates/` syntaktisch geprüft (Pre-Commit-Hook + CI-Schritt).

---

## 4. CI/CD-Integration

### 4.1 PR-Gate (schneller Scan)

**MUSS**: Jeder Pull Request gegen `develop` und `main` löst einen Nuclei-PR-Gate-Scan aus:

```yaml
# .github/workflows/security-nuclei-pr.yml
name: Security — Nuclei PR Gate

on:
  pull_request:
    branches: [develop, main]

jobs:
  nuclei-pr-scan:
    name: Nuclei PR-Scan (fast)
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Spin up ephemeral stack
        run: |
          docker compose -f docker-compose.ci.yml up -d
          ./scripts/wait-for-stack.sh http://localhost:8000/health 60

      - name: Run Nuclei (PR profile)
        uses: projectdiscovery/nuclei-action@v3
        with:
          target: "http://localhost:8000,http://localhost:5173"
          templates: "tests/security/nuclei-templates"
          tags: "exposure,misconfig,default-login,token-spray,kamerplanter"
          severity: "medium,high,critical"
          rate-limit: 50
          output: results.jsonl
          sarif-export: results.sarif

      - name: Upload SARIF to GitHub Code Scanning
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
          category: nuclei-pr

      - name: Archive raw results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: nuclei-pr-results-${{ github.sha }}
          path: |
            results.jsonl
            results.sarif
          retention-days: 90

      - name: Fail on High/Critical findings
        run: |
          jq -r '.info.severity' results.jsonl \
            | grep -E '^(high|critical)$' \
            && { echo "::error::High/Critical Nuclei findings detected"; exit 1; } \
            || echo "No High/Critical findings."
```

**MUSS**: Der PR-Gate-Job darf maximal 15 Minuten dauern (`timeout-minutes`).

### 4.2 Nightly Full-Scan

**MUSS**: Täglich um 02:00 Europe/Berlin läuft ein vollständiger Nuclei-Scan gegen die Staging-Umgebung:

```yaml
# .github/workflows/security-nuclei-nightly.yml
on:
  schedule:
    - cron: "0 0 * * *"  # 01:00 Europe/Berlin (winter) / 02:00 (sommer) — Nuclei zuerst, ZAP folgt 60 Min später (NFR-015 §4.3)
  workflow_dispatch:

jobs:
  nuclei-full-scan:
    timeout-minutes: 60
    permissions:
      contents: read
      security-events: write
      issues: write
    steps:
      - uses: actions/checkout@v4

      - name: Run Nuclei (full profile)
        uses: projectdiscovery/nuclei-action@v3
        with:
          target: "${{ secrets.STAGING_BASE_URL }}"
          templates: "tests/security/nuclei-templates"
          tags: "exposure,misconfig,default-login,cve,vulnerability,kamerplanter"
          severity: "low,medium,high,critical"
          rate-limit: 100
          output: results.jsonl
          sarif-export: results.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
          category: nuclei-nightly

      - name: Open issue for new High/Critical findings
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            // siehe Abschnitt 6.2 — Triage-Workflow
```

**SOLL**: Ergebnisse werden in einem Markdown-Report konsolidiert und im Slack-/Mattermost-Channel `#security-alerts` veröffentlicht.

### 4.3 OpenAPI-Scan

**MUSS**: Vor jedem Merge wird die OpenAPI-Spezifikation mit `-input` gegen Nuclei gescannt — damit deklarierte Routen (auch undokumentierte) abgedeckt sind:

```bash
curl -s http://localhost:8000/api/v1/openapi.json -o openapi.json

nuclei \
  -input openapi.json \
  -input-mode openapi \
  -tags "exposure,misconfig,vulnerability" \
  -severity "high,critical" \
  -j -o openapi-results.jsonl
```

### 4.4 Lokale Ausführung

**MUSS**: Entwickler können Nuclei lokal mit identischer Konfiguration ausführen:

```bash
# Wrapper-Skript: scripts/security/nuclei-local.sh
./scripts/security/nuclei-local.sh --profile pr   # PR-Gate-Profil
./scripts/security/nuclei-local.sh --profile full # Vollständig
```

**SOLL**: Pre-Commit-Hook läuft `nuclei -validate -t tests/security/nuclei-templates/` für eigene Templates.

---

## 5. Akzeptanzkriterien & Build-Gate

### 5.1 Severity-Schwellen

**MUSS**: Build-Gate-Verhalten pro Severity-Klasse:

| Severity | PR-Gate | Nightly | Aktion |
|---|---|---|---|
| **Critical** | Block | Block + Issue + Page | PR-Merge unmöglich, Hotfix-Branch |
| **High** | Block | Block + Issue | PR-Merge unmöglich, Triage in 24 h |
| **Medium** | Warn | Warn + Issue | Merge möglich, Triage in 7 Tagen |
| **Low** | Info | Info | Backlog, kein SLA |
| **Info** | Sammeln | Sammeln | Reine Inventarisierung |

**MUSS**: Critical-Findings auf Staging triggern eine sofortige Benachrichtigung im `#security-alerts`-Channel.

### 5.2 Time-to-Patch SLAs

| Severity | SLA Erkennung → Patch | Verantwortlich |
|---|---|---|
| Critical | 24 Stunden | Maintainer + Security-Officer |
| High | 7 Tage | Verantwortliches Team |
| Medium | 30 Tage | Reguläres Sprint-Backlog |
| Low | Best-Effort | Backlog |

### 5.3 Coverage-Akzeptanzkriterien

**MUSS**: Folgende Mindest-Coverage gilt — verifizierbar durch CI-Reports:

- ≥ 95 % der Templates der Kategorien `exposure`, `misconfiguration`, `default-login` werden ausgeführt (kein Filter-Ausschluss).
- 100 % der eigenen Templates unter `tests/security/nuclei-templates/` werden ausgeführt.
- 100 % der per OpenAPI deklarierten API-Routen sind im OpenAPI-Scan abgedeckt.

---

## 6. Triage & Findings-Management

### 6.1 False-Positive-Suppression

**MUSS**: Suppressions werden in einer versionierten Datei `tests/security/nuclei-suppressions.yaml` gepflegt:

```yaml
# tests/security/nuclei-suppressions.yaml
version: 1
suppressions:
  - template_id: tech-detect-fastapi
    reason: "Tech-Stack ist projektintern bekannt; nicht sicherheitskritisch."
    expires: 2026-12-31
    approved_by: security-officer

  - template_id: cors-misconfig
    matched_url: "http://localhost:5173/api/v1/health"
    reason: "Dev-Only-Setup; Staging und Prod nutzen Same-Origin via Ingress."
    expires: 2026-06-30
    approved_by: maintainer
```

**MUSS**: Jede Suppression hat:
- Begründung (`reason`)
- Ablaufdatum (`expires`, max. 12 Monate)
- Freigabe (`approved_by`)

**MUSS**: Nuclei wird mit `-exclude-id <id>` und `-exclude-matchers` aus dieser Datei aufgerufen — automatisch generiert via `scripts/security/build-nuclei-flags.sh`.

**SOLL**: Abgelaufene Suppressions führen in CI zu einem Warning-Job, der nach 30 Tagen Karenz zum Fail-Job wird.

### 6.2 Triage-Workflow für neue Findings

```
┌──────────────────────────────────────────────────────────────────┐
│  Nightly-Scan findet neues High/Critical-Finding                 │
└──────────────────┬───────────────────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  GitHub-Issue      │  ── Label: security, nuclei, severity-XX
         │  automatisch       │  ── Assignee: rotierender Security-Owner
         │  geöffnet          │  ── Body: Template-ID, URL, Snippet
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Security-Owner    │  ── Bestätigt oder lehnt ab
         │  triagiert         │  ── Bei FP: Suppression-PR
         │  innerhalb 24 h    │  ── Bei TP: Fix-Branch erstellen
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Fix gemerged      │  ── Issue schließt automatisch,
         │  → Re-Scan         │     sobald nächster Scan negativ
         └────────────────────┘
```

**MUSS**: Alle Issues haben Pflicht-Label `security`, `nuclei` und `severity-{critical|high|medium|low}`.

### 6.3 GitHub Code Scanning Integration

**MUSS**: SARIF-Reports werden in GitHub Code Scanning hochgeladen — damit Findings:
- Direkt im PR-Diff sichtbar sind (Inline-Annotations)
- In `Security` → `Code scanning alerts` zentral landen
- Über die GraphQL-API abrufbar sind (für Dashboards)

---

## 7. Reporting & Aufbewahrung

### 7.1 Artefakt-Aufbewahrung

| Artefakt | Aufbewahrungsfrist | Speicherort |
|---|---|---|
| `results.jsonl` (PR-Gate) | 90 Tage | GitHub Actions Artifacts |
| `results.sarif` (PR-Gate) | 90 Tage | GitHub Code Scanning + Artifacts |
| `results.jsonl` (Nightly) | 365 Tage | S3-Bucket `kamerplanter-security-reports` |
| `results.sarif` (Nightly) | 365 Tage | GitHub Code Scanning + S3 |
| Konsolidierter Markdown-Report | 365 Tage | S3 + `#security-alerts` |

**MUSS**: Reports werden mit `commit_sha`, `run_id`, `timestamp` und `target_url` getaggt.

### 7.2 KPIs

**SOLL**: Monatlicher Security-KPI-Report mit folgenden Metriken:

| Metrik | Zielwert |
|---|---|
| Offene Critical-Findings | 0 |
| Offene High-Findings | 0 |
| Mean-Time-to-Detect (MTTD) Critical | < 24 h |
| Mean-Time-to-Patch (MTTP) Critical | < 24 h |
| Mean-Time-to-Patch (MTTP) High | < 7 Tage |
| Anzahl aktiver Suppressions | trendbeobachtet |
| Anteil abgelaufener Suppressions | 0 |

---

## 8. Akzeptanzkriterien

### Definition of Done

- [ ] **Template-Setup**
    - [ ] `tests/security/nuclei-templates/` enthält die in §3.2 gelisteten Pflicht-Templates
    - [ ] Alle eigenen Templates validieren mit `nuclei -validate`
    - [ ] `NUCLEI_TEMPLATES_SHA` ist in CI auf einen Commit-SHA gepinnt
- [ ] **CI-Integration**
    - [ ] `.github/workflows/security-nuclei-pr.yml` läuft auf jedem PR gegen `develop`/`main`
    - [ ] `.github/workflows/security-nuclei-nightly.yml` läuft täglich gegen Staging
    - [ ] OpenAPI-Scan ist Teil des PR-Workflows
    - [ ] PR-Gate scheitert bei High/Critical-Findings
- [ ] **Reporting**
    - [ ] SARIF-Reports werden in GitHub Code Scanning hochgeladen
    - [ ] Nightly-Reports werden in S3 archiviert (365 Tage)
    - [ ] PR-Reports sind 90 Tage als Action-Artifact verfügbar
- [ ] **Triage**
    - [ ] `tests/security/nuclei-suppressions.yaml` ist initial leer und commited
    - [ ] Neue Findings öffnen automatisch GitHub-Issues mit Pflicht-Labels
    - [ ] Security-Owner-Rotation ist im Repository dokumentiert
- [ ] **SLAs**
    - [ ] Critical: 24 h Patch-SLA dokumentiert und kommuniziert
    - [ ] High: 7 Tage Patch-SLA dokumentiert und kommuniziert
- [ ] **Lokaler Workflow**
    - [ ] `scripts/security/nuclei-local.sh` existiert und funktioniert mit `--profile pr`/`--profile full`
    - [ ] Pre-Commit-Hook validiert eigene Templates
- [ ] **Dokumentation**
    - [ ] Pflicht-Template-Sets in §3.1 sind aktuell
    - [ ] Eigene Templates in §3.2 sind dokumentiert und referenziert
    - [ ] Triage-Workflow ist in `docs/security/nuclei-triage.md` ausführlicher beschrieben

---

## 9. Abhängigkeiten

### 9.1 Technische Abhängigkeiten

| Abhängigkeit | Typ | Beschreibung |
|---|---|---|
| **NFR-007** (Betriebsstabilität) | Voraussetzung | Staging-Umgebung muss reproduzierbar deploybar sein |
| **NFR-008** (Teststrategie) | Ergänzung | NFR-014 ist eine eigene Stufe in der Test-Pyramide (Security-Layer) |
| **NFR-008a** (E2E-Selenium) | Ergänzung | Authentifizierte Flows werden über Selenium etabliert; Nuclei prüft auf statischer Ebene |
| **NFR-009** (Dependency-Management) | Ergänzung | NFR-009 schützt Code, NFR-014 schützt Deployment |
| **NFR-015** (OWASP ZAP) | Ergänzung | Tiefere DAST-Analyse — Nuclei deckt Breite, ZAP deckt Tiefe |
| **GitHub Actions** | Infrastruktur | Workflow-Runner, SARIF-Upload, Code Scanning |
| **S3-Bucket** `kamerplanter-security-reports` | Infrastruktur | Langzeit-Archivierung Nightly-Reports |
| **Skaffold / docker-compose.ci.yml** | Infrastruktur | Ephemeral-Stack für PR-Gate |

### 9.2 Externe Abhängigkeiten

| Abhängigkeit | Typ | Risiko | Mitigation |
|---|---|---|---|
| **ProjectDiscovery Nuclei** | Open-Source-Tool | Tool wird nicht mehr gepflegt | Pinning auf bekannte stabile Version, Templates lokal versioniert |
| **`projectdiscovery/nuclei-templates`** | Template-Repo | Breaking Changes in Template-Struktur | Pinning auf SHA, Renovate kontrollierter Update-Pfad |
| **`projectdiscovery/nuclei-action`** | GitHub Action | Action-Repo verschwindet | Self-hosted Fallback via `nuclei`-Binary |
| **GitHub Code Scanning** | SaaS | Dienstausfall blockiert PR-Annotations | Lokale SARIF-Auswertung als Fallback |

---

## 10. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Information Disclosure durch ungeprüfte Endpunkte** | Leak von `.env`, JWT-Tokens, Tenant-IDs → DSGVO-Verstoß, Vertrauensschaden | Hoch | NFR-014 PR-Gate, Pflicht-Template-Sets |
| **Bekannte CVEs in eingesetzten Frameworks unentdeckt** | Ausnutzung publik dokumentierter Schwachstellen | Mittel | Nightly-Scan mit `cves`-Tag, NFR-009 als zusätzliche Ebene |
| **Default-Logins in mit-deployten Tools** | Vollständige Übernahme administrativer Komponenten | Mittel | Pflicht-Aktivierung `default-logins`-Templates |
| **Fehlende Security-Headers** | XSS-Filter, MIME-Sniffing-Angriffe, Clickjacking | Hoch | Eigenes Template `kamerplanter-security-headers.yaml` |
| **CORS-Misconfiguration** | Cross-Origin-Datenzugriff auf authentifizierte APIs | Mittel | Eigenes Template `kamerplanter-cors-misconfig.yaml` |
| **Source-Maps in Produktion** | Vollständige Frontend-Logik öffentlich, einschließlich API-Aufrufe | Mittel | Eigenes Template `kamerplanter-source-map.yaml` |
| **False-Positive-Müdigkeit (Alert Fatigue)** | Echte Findings werden ignoriert | Mittel | Triage-Workflow mit verpflichteten Suppression-Begründungen und Ablaufdaten |

---

**Dokumenten-Ende**

**Version**: 1.1
**Status**: Genehmigt
**Letzte Aktualisierung**: 2026-04-28
**Review**: Genehmigt
**Genehmigung**: Genehmigt (2026-06-11)
