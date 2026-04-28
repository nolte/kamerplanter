---
ID: NFR-015
Titel: OWASP-ZAP-Security-Scanning — Tiefes DAST-Scanning Frontend & Backend
Kategorie: Sicherheit / Qualitätssicherung
Unterkategorie: DAST, Dynamic Application Security Testing, Authenticated Scanning
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: OWASP ZAP, ZAP Action (Baseline / Full / API), AjaxSpider, GitHub Actions, SARIF
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: QA / Security Engineering
Datum: 2026-04-28
Tags: [security, dast, zap, owasp, ajax-spider, active-scan, passive-scan, api-scan, authenticated-scan, sarif, ci-gate]
Abhängigkeiten: [NFR-007, NFR-008, NFR-008a, NFR-009, NFR-014]
Betroffene Module: [src/backend, src/frontend, helm, .github/workflows, tests/security]
---

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.0 | 2026-04-28 | Erstversion — OWASP ZAP Baseline-, Full- und API-Scan-Profile; authentifizierte Scans gegen Tenant-Routing; AjaxSpider für React-SPA; SARIF-Reporting, Build-Gate, Triage. |

# NFR-015: OWASP-ZAP-Security-Scanning

## Abgrenzung zu bestehenden NFRs

| NFR | Fokus | Definiert |
|---|---|---|
| NFR-008 | Funktionale Teststrategie | **Funktionale** Tests (Unit, Integration, E2E) |
| NFR-008a | E2E-Selenium-Konventionen | Wie Selenium-Tests aufgebaut sind |
| NFR-009 | Dependency-CVE-Scanning | **Sicherheit der Dependencies** |
| NFR-014 | Nuclei — template-basiertes Vulnerability-Scanning | **Breite, schnelle** Schwachstellenprüfung |
| **NFR-015 (dieses Dokument)** | OWASP ZAP — Spider + Active/Passive Scan + API-Scan | **Tiefe** verhaltensbasierte DAST-Analyse |

NFR-014 (Nuclei) und NFR-015 (ZAP) sind **bewusst komplementär** — ein Lauf ersetzt nicht den anderen:

| Aspekt | Nuclei (NFR-014) | OWASP ZAP (NFR-015) |
|---|---|---|
| **Methodik** | Templates (Pattern-Matching) | Spider + Fuzzing + Heuristiken |
| **Geschwindigkeit** | < 5 Minuten (PR), < 30 Minuten (Nightly) | 10–30 Minuten (Baseline), 1–6 Stunden (Full) |
| **Stärke** | Bekannte CVEs, Misconfigurations, exponierte Pfade | Injection, XSS, Broken Auth, Business-Logic-Klassen |
| **Auth-Fähigkeit** | Eingeschränkt (Header-basiert) | Vollständig (Form, JSON, Script, Anti-CSRF) |
| **SPA-Rendering** | Passiv (kein JS-Rendering im PR-Profil) | AjaxSpider rendert React-SPA über Selenium |
| **Findings-Klassen** | Tausende Templates, eng abgegrenzt | OWASP Top 10, breit angelegte Risk-Klassen |

NFR-015 deckt explizit **authentifizierte** Tests gegen die Anwendung ab — inkl. Tenant-Isolation, Permission-Matrix-Verletzungen und API-Schema-Konformität.

---

## 1. Business Case

### 1.1 User Stories

**Als** Security Officer
**möchte ich** dass jede produktive Freigabe einen vollständigen DAST-Scan durchlaufen hat
**um** Klassen von Schwachstellen wie Injection, XSS oder Broken Authentication systematisch auszuschliessen.

**Als** Backend-Entwickler
**möchte ich** dass die OpenAPI-Spec gegen die laufende API gescannt wird
**um** sicherzustellen, dass alle Endpunkte auch in der Implementierung den deklarierten Auth-/Tenant-Annahmen folgen.

**Als** Frontend-Entwickler
**möchte ich** dass die React-SPA durch den AjaxSpider gerendert und durchsucht wird
**um** Routen und Formulare zu erfassen, die ein klassischer HTML-Spider nicht sieht.

**Als** Product Owner Multi-Tenancy (REQ-024)
**möchte ich** dass ZAP authentifizierte Scans gegen mindestens zwei Test-Mandanten durchführt
**um** Cross-Tenant-Datenzugriffe zuverlässig zu erkennen.

**Als** Compliance-Auditor
**möchte ich** vollständige ZAP-Reports im HTML- und SARIF-Format mit Commit-Hash und Zeitstempel
**um** den Sicherheitszustand zu jedem freigegebenen Release nachweisen zu können.

### 1.2 Geschäftliche Motivation

**Tiefe vs. Breite**:
- Nuclei findet das, was als Template existiert. ZAP findet Klassen von Schwachstellen, deren konkrete Ausprägung unbekannt ist (z. B. ein neuer SQLi-Vektor in einem Custom-Endpunkt).
- OWASP Top 10 ist die international anerkannte Risiko-Taxonomie für Web-Anwendungen — ZAP deckt diese systematisch ab.

**Multi-Tenant-Pflicht**:
- REQ-024 (Mandantenverwaltung) verlangt strikte Tenant-Isolation. Ohne authentifizierte Cross-Tenant-Scans kann diese Eigenschaft nicht verifiziert werden — sie kann nur explizit getestet werden.
- Eine versehentlich fehlende `require_permission()`-Dependency in einem neuen Endpunkt ist genau die Klasse Bug, die ZAP-Active-Scan in Kombination mit zwei authentifizierten Sessions zuverlässig erkennt.

**API-Schema-Konformität**:
- Die FastAPI-OpenAPI-Spec dokumentiert die deklarierte Schnittstelle. ZAP-API-Scan prüft, ob die Implementierung dieser Deklaration auf Sicherheitsebene folgt (Auth, Schema-Validation, Error-Handling).
- Drift zwischen Spec und Implementierung ist ein verbreiteter Quell für Information Disclosure.

**Abdeckung dynamischer SPAs**:
- React-Apps (REQ-009 Dashboard, alle Pflegemasken aus NFR-010) sind nicht durch klassische HTML-Spider erreichbar — Routen werden client-seitig gerendert.
- ZAP AjaxSpider startet eine echte Browser-Instanz (Chrome Headless via Selenium), klickt durch die SPA und erfasst dadurch alle erreichbaren Routen.

### 1.3 Fachliche Beschreibung

Praktisches Beispiel:

> **Szenario**: Ein neuer Endpunkt `GET /api/v1/t/{tenant_slug}/harvest/{key}` wird hinzugefügt, vergisst aber die `require_permission()`-Dependency. Authentifizierte Nutzer eines anderen Mandanten können den Endpunkt aufrufen, weil JWT-Validierung greift, Tenant-Authorisierung jedoch nicht.
> **Ohne NFR-015**: Der Bug bleibt unbemerkt, bis ein Mandant zufällig auf fremde Daten stößt — oder ein Angreifer ihn gezielt sucht.
> **Mit NFR-015**: ZAP führt einen authentifizierten Scan mit Session A (Mandant α) gegen Routen aus, die Session B (Mandant β) erstellt hat. Eine erfolgreiche 200-Antwort auf cross-tenant-Daten ist konfiguriert als Fail-Bedingung — das CI-Gate blockiert den Merge.

---

## 2. Scope & Geltungsbereich

### 2.1 Drei verpflichtende Scan-Profile

| Profil | Wann | Dauer | Ziel | Action |
|---|---|---|---|---|
| **Baseline** | Pro PR | < 15 min | Passive-only Scan gegen Frontend + Backend | `zaproxy/action-baseline` |
| **API-Scan** | Pro PR | < 15 min | OpenAPI-getriebener Scan gegen Backend | `zaproxy/action-api-scan` |
| **Full-Scan** | Nightly + Pre-Release | 1–6 h | Active + Passive + AjaxSpider, authentifiziert | `zaproxy/action-full-scan` |

**MUSS**: Alle drei Profile sind verpflichtend in CI eingebunden.

### 2.2 Was wird gescannt

| Komponente | Profil | Auth | Bemerkung |
|---|---|---|---|
| Frontend (React-SPA) | Baseline + Full | Optional (bei Full mit Session) | AjaxSpider für SPA-Routing |
| Backend (FastAPI) | API + Full | Pflicht (Full) | OpenAPI-getrieben |
| Reverse-Proxy (Traefik) | Baseline | Anonym | Header-Validierung |
| Tenant-Routing `/t/{slug}/...` | Full | Pflicht (zwei Sessions) | Cross-Tenant-Tests |
| `/api/v1/auth/...` (REQ-023) | Full | Mixed | Login-, Logout-, Refresh-Flows |
| `/api/v1/privacy/...` (REQ-025) | Full | Pflicht | DSGVO-Endpunkte mit personenbezogenen Daten |

### 2.3 Was wird ausdrücklich NICHT durch NFR-015 abgedeckt

- **Schnelles Template-Scanning** für bekannte CVEs / Misconfigurations → siehe NFR-014.
- **Source-Code-Analyse (SAST)** → ausserhalb des Scopes.
- **Penetration-Testing** durch externe Auditoren — NFR-015 ergänzt manuelle Pentests, ersetzt sie aber nicht.
- **Last-/Performance-Tests** → eigenes Themengebiet.

---

## 3. Authentifizierungsstrategie

### 3.1 Test-Identitäten

**MUSS**: Drei dedizierte Testkonten existieren ausschliesslich in der Staging-/CI-Umgebung:

| Login | Tenant | Rolle | Zweck |
|---|---|---|---|
| `zap-tenant-a-admin@kamerplanter.test` | `tenant-a` | admin | Authentifizierte Active-Scans innerhalb Mandant A |
| `zap-tenant-a-viewer@kamerplanter.test` | `tenant-a` | viewer | Permission-Matrix-Tests |
| `zap-tenant-b-admin@kamerplanter.test` | `tenant-b` | admin | Cross-Tenant-Negativtests gegen Mandant A |

**MUSS**: Diese Konten:
- werden über Seed-Daten beim Hochfahren der Staging-/CI-Umgebung angelegt,
- existieren NICHT in produktiven Umgebungen,
- haben Passwörter, die ausschliesslich als GitHub-Secrets verwaltet werden,
- werden bei jedem Re-Seed automatisch zurückgesetzt.

### 3.2 ZAP-Auth-Konfiguration (JWT-basiert)

**MUSS**: Authentifizierte Scans nutzen das JWT-Login-Endpoint (REQ-023) — ZAP-Auth-Script generiert pro Session ein Bearer-Token:

```javascript
// tests/security/zap-scripts/jwt-auth.js
function authenticate(helper, paramsValues, credentials) {
  var loginUrl = paramsValues.get("Login URL");
  var loginBody = JSON.stringify({
    email: credentials.getParam("email"),
    password: credentials.getParam("password")
  });

  var requestUri = new org.apache.commons.httpclient.URI(loginUrl, false);
  var requestMethod = HttpRequestHeader.POST;
  var msg = helper.prepareMessage();
  msg.setRequestHeader(new HttpRequestHeader(requestMethod, requestUri, "HTTP/1.1"));
  msg.getRequestHeader().setHeader("Content-Type", "application/json");
  msg.setRequestBody(loginBody);
  msg.getRequestHeader().setContentLength(msg.getRequestBody().length());

  helper.sendAndReceive(msg);

  var responseBody = msg.getResponseBody().toString();
  var token = JSON.parse(responseBody).access_token;

  msg.getRequestHeader().setHeader("Authorization", "Bearer " + token);
  return msg;
}

function getRequiredParamsNames() { return ["Login URL"]; }
function getOptionalParamsNames() { return []; }
function getCredentialsParamsNames() { return ["email", "password"]; }
```

**MUSS**: Das Bearer-Token wird in einem `HttpSender`-Skript an alle nachfolgenden Requests angehängt.
**MUSS**: Refresh-Token-Rotation (REQ-023) wird abgebildet — bei `401` wird automatisch neu authentifiziert.

### 3.3 Cross-Tenant-Negativtests

**MUSS**: Vor dem Active-Scan erstellt ein Setup-Skript reproduzierbar Daten in beiden Mandanten:

```bash
# tests/security/zap-setup/seed-cross-tenant.sh
TENANT_A_TOKEN=$(curl -s ... | jq -r .access_token)
TENANT_B_TOKEN=$(curl -s ... | jq -r .access_token)

# Resource in Tenant A erzeugen
RESOURCE_A_KEY=$(curl -s -X POST \
  -H "Authorization: Bearer $TENANT_A_TOKEN" \
  -d '{"name":"ZAP-A-Species"}' \
  "$BASE/api/v1/t/tenant-a/species" | jq -r ._key)

# Resource-Key fuer Cross-Tenant-Probing exportieren
echo "RESOURCE_A_KEY=$RESOURCE_A_KEY" >> "$GITHUB_OUTPUT"
```

**MUSS**: Eine ZAP-Custom-Rule (Active-Rule oder Skript) prüft cross-tenant für Resource-Keys aus Tenant A mit Token von Tenant B und meldet 200-Antworten als High-Severity-Finding.

### 3.4 Out-of-Scope für unauthentifizierte Scans

**MUSS**: Folgende Endpunkte sind in unauthentifizierten Profilen explizit ausgeschlossen, da sie absichtlich öffentlich sind:

- `/api/v1/auth/login`
- `/api/v1/auth/register`
- `/api/v1/auth/oauth/*`
- `/api/v1/calendar/feeds/{token}` (Token-basiert, REQ-015)
- `/health`, `/ready`

Konfiguration via `-c` (Context-File) und `-z "-config api.disablekey=false"`.

---

## 4. Scan-Profile im Detail

### 4.1 Baseline-Scan (PR-Gate, passiv)

**MUSS**: Pro PR läuft `zaproxy/action-baseline` gegen die Ephemeral-Stack-Frontend-URL:

```yaml
# .github/workflows/security-zap-baseline.yml
name: Security — ZAP Baseline

on:
  pull_request:
    branches: [develop, main]

jobs:
  zap-baseline:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    permissions:
      contents: read
      issues: write
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Spin up ephemeral stack
        run: docker compose -f docker-compose.ci.yml up -d

      - name: Wait for stack
        run: ./scripts/wait-for-stack.sh http://localhost:5173 60

      - name: ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.13.0
        with:
          target: "http://localhost:5173"
          rules_file_name: "tests/security/zap-rules.tsv"
          cmd_options: "-a -j -m 5 -T 15"
          allow_issue_writing: true
          fail_action: true

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: report_sarif.sarif
          category: zap-baseline
```

**MUSS**: Der Baseline-Scan darf den PR-Gate maximal 20 Minuten verzögern.

### 4.2 API-Scan (PR-Gate, OpenAPI-getrieben)

**MUSS**: Pro PR läuft `zaproxy/action-api-scan` gegen die OpenAPI-Spec:

```yaml
- name: Generate OpenAPI from running API
  run: curl -s http://localhost:8000/api/v1/openapi.json -o openapi.json

- name: ZAP API Scan
  uses: zaproxy/action-api-scan@v0.9.0
  with:
    target: "openapi.json"
    format: openapi
    rules_file_name: "tests/security/zap-api-rules.tsv"
    cmd_options: "-a -j -T 15"
    fail_action: true
```

**MUSS**: Der API-Scan deckt ausschliesslich Routen ab, die in der OpenAPI deklariert sind. Routen, die in der Implementierung existieren aber nicht in OpenAPI auftauchen, sind ein eigenes Finding-Class (siehe §4.4).

### 4.3 Full-Scan (Nightly, authentifiziert, AjaxSpider)

**MUSS**: Täglich läuft `zaproxy/action-full-scan` gegen Staging mit aktivem AjaxSpider:

```yaml
# .github/workflows/security-zap-nightly.yml
on:
  schedule:
    - cron: "0 0 * * *"   # 01:00 Europe/Berlin (winter)
  workflow_dispatch:

jobs:
  zap-full-scan:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    permissions:
      contents: read
      issues: write
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Seed cross-tenant data
        env:
          TENANT_A_PASSWORD: ${{ secrets.ZAP_TENANT_A_PASSWORD }}
          TENANT_B_PASSWORD: ${{ secrets.ZAP_TENANT_B_PASSWORD }}
          BASE: ${{ secrets.STAGING_BASE_URL }}
        run: ./tests/security/zap-setup/seed-cross-tenant.sh

      - name: ZAP Full Scan (authenticated, AjaxSpider on)
        uses: zaproxy/action-full-scan@v0.12.0
        with:
          target: ${{ secrets.STAGING_BASE_URL }}
          rules_file_name: "tests/security/zap-rules.tsv"
          cmd_options: >-
            -a
            -j
            -T 60
            -z "-configfile /zap/wrk/zap-context.xml
                -config replacer.full_list(0).description=jwt-auth-A
                -config replacer.full_list(0).enabled=true
                -config replacer.full_list(0).matchtype=REQ_HEADER
                -config replacer.full_list(0).matchstr=Authorization
                -config replacer.full_list(0).regex=false
                -config replacer.full_list(0).replacement=Bearer ${{ secrets.ZAP_TENANT_A_TOKEN }}"
          fail_action: true
          allow_issue_writing: true

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: report_sarif.sarif
          category: zap-nightly

      - name: Archive HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: zap-full-${{ github.sha }}
          path: |
            report_html.html
            report_md.md
            report_json.json
            report_sarif.sarif
          retention-days: 365
```

**MUSS**: Der Full-Scan läuft mit:
- **AjaxSpider aktiviert** (`-j` in der ZAP-Action-CLI) für SPA-Coverage
- **Authentifizierung gegen mindestens zwei Tenant-Identitäten**
- **Kontext-Datei** `tests/security/zap-context.xml` mit Excludes (siehe §3.4)

### 4.4 Spec-Drift-Detection (eigenes Finding)

**SOLL**: Ein zusätzlicher Job vergleicht die von ZAP gespiderten Routen mit der OpenAPI-Spec. Routen, die nicht in OpenAPI dokumentiert sind, werden als Medium-Finding gemeldet.

---

## 5. Akzeptanzkriterien & Build-Gate

### 5.1 Severity-Schwellen

**MUSS**: ZAP-Risk-Level werden auf das gleiche Severity-Modell gemappt wie NFR-014:

| ZAP Risk | Severity (NFR-Modell) | PR-Gate | Nightly | Aktion |
|---|---|---|---|---|
| **High** | Critical / High | Block | Block + Issue + Page | PR-Merge unmöglich, 24 h SLA |
| **Medium** | Medium | Warn | Warn + Issue | Triage in 7 Tagen |
| **Low** | Low | Info | Info | Backlog |
| **Informational** | Info | Sammeln | Sammeln | Reine Inventarisierung |

**MUSS**: Cross-Tenant-Findings (eigene Custom-Rule) sind immer **High** und blockieren immer den Merge.

### 5.2 Confidence-Filter

**MUSS**: Der Build-Gate scheitert nur bei Findings mit Confidence ≥ `Medium`. Findings mit Confidence `Low` oder `Falsche Positive (FP)` sind reine Warnings.

### 5.3 Performance-Schwellen

**MUSS**: Profile-Laufzeiten:

| Profil | Max. Laufzeit | Verhalten bei Überschreitung |
|---|---|---|
| Baseline (PR) | 20 min | Job-Timeout, Fail |
| API-Scan (PR) | 15 min | Job-Timeout, Fail |
| Full-Scan (Nightly) | 6 h | Soft-Fail, Issue mit Diagnose-Links |

### 5.4 Time-to-Patch SLAs

| Severity | SLA | Verantwortlich |
|---|---|---|
| Critical / Cross-Tenant | 24 Stunden | Maintainer + Security-Officer |
| High | 7 Tage | Verantwortliches Team |
| Medium | 30 Tage | Reguläres Sprint-Backlog |
| Low | Best-Effort | Backlog |

---

## 6. Triage & Findings-Management

### 6.1 ZAP-Rules-Tuning

**MUSS**: Regelanpassungen werden ausschliesslich in `tests/security/zap-rules.tsv` und `tests/security/zap-api-rules.tsv` versioniert:

```tsv
# tests/security/zap-rules.tsv
# Format: <PluginID> <THRESHOLD> <Confidence> <Note>
10038	IGNORE	HIGH	CSP-Report-Only — bewusst gewählt fuer Migrationsphase
10054	IGNORE	HIGH	Cookie-Same-Site auf "Lax" — bewusst gesetzt fuer OAuth-Redirects
40012	WARN	HIGH	Reflected XSS — Confidence-Filter behalten, im Issue triagieren
```

**MUSS**: Jede `IGNORE`-Regel hat ein Ablaufdatum als Kommentar (z. B. `# expires 2026-12-31 — approved by security-officer`).

**SOLL**: Abgelaufene IGNORE-Einträge führen in CI zunächst zu einem Warning, nach 30 Tagen zu einem Fail.

### 6.2 Triage-Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│  Nightly-Scan findet neues High-Finding                          │
└──────────────────┬───────────────────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  GitHub-Issue      │  ── Label: security, zap, severity-XX, owasp-top10-AXX
         │  automatisch       │  ── Body: Plugin-ID, URL, Evidence,
         │  geöffnet          │           Reproduktionspfad, HAR-Auszug
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Security-Owner    │  ── Confirms TP / FP
         │  triagiert         │  ── Bei FP: tsv-PR mit Begründung
         │  innerhalb 24 h    │  ── Bei TP: Fix-Branch
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Re-Scan           │  ── Issue schliesst automatisch,
         │                    │     wenn Finding nicht mehr auftritt
         └────────────────────┘
```

**MUSS**: Alle Issues haben Pflicht-Label `security`, `zap`, `severity-{critical|high|medium|low}` und `owasp-top10-A0X`.

### 6.3 Korrelation mit anderen Quellen

**SOLL**: Findings werden mit GitHub Code Scanning (SARIF aus NFR-014 + NFR-015) automatisch dedupliziert. Doppelte Detections (z. B. Nuclei meldet `exposures/files/env-file` und ZAP meldet `Information Disclosure - Suspicious Comments`) werden zusammengeführt.

---

## 7. Reporting & Aufbewahrung

### 7.1 Artefakt-Aufbewahrung

| Artefakt | Aufbewahrungsfrist | Speicherort |
|---|---|---|
| Baseline-SARIF (PR) | 90 Tage | GitHub Code Scanning + Artifacts |
| API-Scan-JSON (PR) | 90 Tage | GitHub Actions Artifacts |
| Full-Scan-HTML (Nightly) | 365 Tage | S3-Bucket + GitHub Code Scanning |
| Full-Scan-SARIF (Nightly) | 365 Tage | GitHub Code Scanning |
| Konsolidierter Markdown-Report | 365 Tage | S3 + `#security-alerts` |

**MUSS**: Reports werden mit `commit_sha`, `run_id`, `timestamp`, `target_url` und `tenant_context` getaggt.

### 7.2 KPIs

**SOLL**: Monatlicher Security-KPI-Report mit folgenden Metriken — gemeinsam mit NFR-014:

| Metrik | Zielwert |
|---|---|
| Offene High/Critical-Findings (ZAP) | 0 |
| Cross-Tenant-Findings | 0 (immer Block) |
| Mean-Time-to-Patch High (ZAP) | < 7 Tage |
| Anteil OpenAPI-Drift-Findings | < 5 % aller Routen |
| Anteil aktiver IGNORE-Regeln im tsv | trendbeobachtet |
| Anteil abgelaufener IGNORE-Regeln | 0 |

---

## 8. Akzeptanzkriterien

### Definition of Done

- [ ] **Profile**
    - [ ] `.github/workflows/security-zap-baseline.yml` läuft auf jedem PR
    - [ ] `.github/workflows/security-zap-api.yml` läuft auf jedem PR
    - [ ] `.github/workflows/security-zap-nightly.yml` läuft täglich gegen Staging
    - [ ] Pre-Release-Workflow startet Full-Scan zusätzlich on-demand
- [ ] **Authentifizierung**
    - [ ] Drei Test-Identitäten existieren in Staging-Seed
    - [ ] JWT-Login-Skript ist in `tests/security/zap-scripts/` versioniert
    - [ ] Refresh-Token-Rotation ist im Auth-Skript abgebildet
    - [ ] Cross-Tenant-Setup-Skript ist in `tests/security/zap-setup/` versioniert
    - [ ] Custom-Rule für Cross-Tenant-Detection meldet 200-Antworten als High
- [ ] **AjaxSpider**
    - [ ] Full-Scan startet AjaxSpider mit Chrome-Headless
    - [ ] Mindestens 95 % der React-Routen werden vom AjaxSpider erfasst
- [ ] **Reporting**
    - [ ] SARIF wird in GitHub Code Scanning hochgeladen
    - [ ] HTML/JSON/MD-Reports werden 365 Tage in S3 archiviert
    - [ ] PR-Annotations sind im Diff sichtbar
- [ ] **Tuning**
    - [ ] `tests/security/zap-rules.tsv` und `zap-api-rules.tsv` existieren
    - [ ] Jede IGNORE-Regel hat Ablaufdatum + Begründung + Freigabe
    - [ ] Abgelaufene IGNORE-Einträge werden vom CI ge-warnt
- [ ] **Triage**
    - [ ] Nightly-Findings öffnen automatisch GitHub-Issues mit Pflicht-Labels
    - [ ] Security-Owner-Rotation ist im Repo dokumentiert
- [ ] **SLAs**
    - [ ] Critical/Cross-Tenant: 24 h Patch-SLA dokumentiert
    - [ ] High: 7 Tage Patch-SLA dokumentiert
- [ ] **Performance**
    - [ ] Baseline-Scan ≤ 20 min
    - [ ] API-Scan ≤ 15 min
    - [ ] Full-Scan ≤ 6 h
- [ ] **Spec-Drift**
    - [ ] Spec-Drift-Job vergleicht ZAP-Spider-Routen mit OpenAPI
    - [ ] Drift-Findings werden als Medium-Finding gemeldet
- [ ] **Dokumentation**
    - [ ] `docs/security/zap-triage.md` enthält Triage-Workflow ausführlich
    - [ ] `docs/security/zap-auth-setup.md` beschreibt JWT-Auth-Skript-Anpassungen
    - [ ] `docs/security/zap-cross-tenant-tests.md` dokumentiert Negativtest-Konzept

---

## 9. Abhängigkeiten

### 9.1 Technische Abhängigkeiten

| Abhängigkeit | Typ | Beschreibung |
|---|---|---|
| **NFR-007** (Betriebsstabilität) | Voraussetzung | Staging-Umgebung muss reproduzierbar deploybar sein |
| **NFR-008** (Teststrategie) | Ergänzung | NFR-015 ist Stufe „Security DAST" in der Test-Pyramide |
| **NFR-008a** (E2E-Selenium) | Ergänzung | AjaxSpider nutzt Chrome-Headless analog zur E2E-Selenium-Konfiguration |
| **NFR-009** (Dependency-Management) | Ergänzung | NFR-009 prüft Dependency-CVEs, NFR-015 prüft Anwendungssicherheit |
| **NFR-014** (Nuclei) | Komplementär | Nuclei: Breite + Speed; ZAP: Tiefe + Auth |
| **REQ-023** (Authentifizierung) | Voraussetzung | Login-Endpoint und JWT-Schema sind Voraussetzung für authentifizierte Scans |
| **REQ-024** (Mandantenverwaltung) | Voraussetzung | Tenant-Routing und Permission-Matrix sind Voraussetzung für Cross-Tenant-Tests |
| **GitHub Actions** | Infrastruktur | Workflow-Runner, SARIF-Upload, Code Scanning |
| **S3-Bucket** `kamerplanter-security-reports` | Infrastruktur | Langzeit-Archivierung Full-Scan-Reports |
| **Skaffold / docker-compose.ci.yml** | Infrastruktur | Ephemeral-Stack für PR-Gate |

### 9.2 Externe Abhängigkeiten

| Abhängigkeit | Typ | Risiko | Mitigation |
|---|---|---|---|
| **OWASP ZAP** | Open-Source-Tool | Tool wird nicht mehr gepflegt | ZAP ist OWASP-Flagship-Projekt; alternativ self-hosted Mirror |
| **`zaproxy/action-baseline/api-scan/full-scan`** | GitHub Action | Action-Repo verschwindet | Direkter Aufruf des Docker-Images `ghcr.io/zaproxy/zaproxy` |
| **GitHub Code Scanning** | SaaS | Dienstausfall blockiert PR-Annotations | Lokale SARIF-Auswertung als Fallback |
| **Chrome Headless (AjaxSpider)** | Browser-Engine | Browser-Update bricht Spider | Pinning der Chrome-Image-Version analog NFR-008a |

---

## 10. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Cross-Tenant-Datenleak (REQ-024 Bruch)** | Mandant α sieht Daten von Mandant β → DSGVO-Vorfall, Vertrauensschaden, regulatorische Sanktionen | Mittel | Cross-Tenant-Custom-Rule, zwei-Identitäten-Setup, automatisches PR-Block |
| **Injection-Schwachstellen in Custom-Endpunkten** | RCE, SQL-Injection, NoSQL-Injection → Vollkompromittierung | Mittel | Active-Scan im Full-Profil mit OWASP-Top-10-Coverage |
| **XSS in React-SPA** | Session-Hijacking, JWT-Diebstahl, Phishing innerhalb der Anwendung | Mittel | Baseline-Scan + AjaxSpider-Coverage, CSP-Pflicht aus NFR-014 |
| **Broken Auth / Auth Bypass** | Ungeprüfte Endpunkte erlauben Zugriff ohne JWT-Validierung | Hoch | API-Scan gegen OpenAPI mit authentifizierten und unauthentifizierten Sessions |
| **Spec-Drift API ↔ Implementierung** | Endpunkte existieren in der Implementation, aber nicht in OpenAPI → Schatten-API | Hoch | Spec-Drift-Job (§4.4), automatische Findings |
| **Falsch konfigurierte Cookies (REQ-023 RefreshToken)** | Refresh-Token wird ohne `HttpOnly`/`Secure`/`SameSite` ausgeliefert → Session-Hijacking | Mittel | Baseline-Cookie-Rules, Active-Rule für Cookie-Flags |
| **Veraltete IGNORE-Regeln** | Reale Findings werden ohne neue Bewertung dauerhaft unterdrückt | Mittel | Pflicht-Ablaufdaten in tsv, Karenz-CI-Job |
| **Performance-Drift (Full-Scan zu langsam)** | Nightly läuft nicht zuverlässig durch, Findings altern | Niedrig | Performance-Schwellen + Soft-Fail-Issue mit Diagnose |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-04-28
**Review**: Pending
**Genehmigung**: Pending
