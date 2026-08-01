---
ID: NFR-015
Titel: OWASP-ZAP-Security-Scanning — Tiefes DAST-Scanning Frontend & Backend
Kategorie: Sicherheit / Qualitätssicherung
Unterkategorie: DAST, Dynamic Application Security Testing, Authenticated Scanning
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: OWASP ZAP, ZAP Action (Baseline / Full / API), AjaxSpider, GitHub Actions, SARIF
Status: Genehmigt
Priorität: Hoch
Version: 1.1
Autor: QA / Security Engineering
Datum: 2026-04-28
Tags: [security, dast, zap, owasp, ajax-spider, active-scan, passive-scan, api-scan, authenticated-scan, sarif, ci-gate]
Abhängigkeiten: [NFR-007, NFR-008, NFR-008a, NFR-009, NFR-014]
Betroffene Module: [src/backend, src/frontend, helm, .github/workflows, tests/security]
---

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.1 | 2026-04-29 | Spec-Followup nach PR-#115-Review: §3.2 von einem klassischen Authentication-Script auf ein **HttpSender-Script** umgestellt (Bearer-Header für ALLE Folgerequests, JWT-Refresh bei 401). §3.3 um konkretes **Passive-Rule-Script-Skelett** für Cross-Tenant-Detection erweitert (extrahiert Tenant aus URL und JWT-Payload, raised High-Alert bei Mismatch). §5.1 Severity-Mapping auf striktes 1:1-Mapping ZAP→NFR-Modell mit expliziter Critical-Eskalations-Regel für Cross-Tenant. §4.1 Beschreibung: Baseline-Profil aktiviert AjaxSpider explizit auch passive (nicht erst im Full). §4.3 Replacer-Konfig in `zap-context.xml` zentralisiert statt CLI-Override. Drei Test-Identitäten als Pflicht-Pre-Deploy-Check ergänzt (dürfen nicht in Prod-DB-Snapshots auftauchen). §3.1 Domain-Korrektur: `@kamerplanter.test` (von Pydantic abgelehnt) → `@zap.kamerplanter.example`; Setup-Tooling unter `tests/security/zap-setup/` statt im Backend-Code; Pre-Deploy-Check als AQL-Daten-Prüfung formuliert. PR-#117-Review-Followup: §4.2 um zwei Pässe (auth + anonym) für Auth-Bypass-Detection erweitert (Findings-Logik-Tabelle, Out-of-Scope-Routen referenziert §3.4). §3.2 dokumentiert die Limitation, dass ZAP einen 401-Request nicht automatisch nach `refreshToken()` replay-t — Mitigation über erhöhte Test-Token-Lifetime und Pre-Auth via Setup-Skript. |
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
**um** Klassen von Schwachstellen wie Injection, XSS oder Broken Authentication systematisch auszuschließen.

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
- REQ-024 (Mandantenverwaltung) verlangt strikte Tenant-Isolation. Diese Eigenschaft lässt sich nicht passiv ableiten, sondern nur durch explizite Tests nachweisen — und dafür braucht es authentifizierte Cross-Tenant-Scans.
- Eine versehentlich fehlende `require_permission()`-Dependency in einem neuen Endpunkt ist genau die Art von Bug, die der ZAP-Active-Scan in Kombination mit zwei authentifizierten Sessions zuverlässig erkennt.

**API-Schema-Konformität**:
- Die FastAPI-OpenAPI-Spec dokumentiert die deklarierte Schnittstelle. ZAP-API-Scan prüft, ob die Implementierung dieser Deklaration auf Sicherheitsebene folgt (Auth, Schema-Validation, Error-Handling).
- Drift zwischen Spec und Implementierung ist eine verbreitete Quelle für Information Disclosure.

**Abdeckung dynamischer SPAs**:
- React-Apps (REQ-009 Dashboard, alle Pflegemasken aus NFR-010) sind für klassische HTML-Spider nicht erreichbar, weil die Routen clientseitig gerendert werden.
- ZAP AjaxSpider startet eine echte Browser-Instanz (Chrome Headless via Selenium), klickt durch die SPA und erfasst dadurch alle erreichbaren Routen.

### 1.3 Fachliche Beschreibung

Praktisches Beispiel:

> **Szenario**: Ein neuer Endpunkt `GET /api/v1/t/{tenant_slug}/harvest/{key}` wird hinzugefügt, vergisst aber die `require_permission()`-Dependency. Authentifizierte Nutzer eines anderen Mandanten können den Endpunkt aufrufen, weil die JWT-Validierung greift, die Tenant-Autorisierung jedoch nicht.
> **Ohne NFR-015**: Der Bug bleibt unbemerkt, bis ein Mandant zufällig auf fremde Daten stößt — oder ein Angreifer ihn gezielt sucht.
> **Mit NFR-015**: ZAP führt einen authentifizierten Scan mit Session A (Mandant α) gegen Routen aus, die Session B (Mandant β) erstellt hat. Eine erfolgreiche 200-Antwort auf Cross-Tenant-Daten ist als Fail-Bedingung konfiguriert — das CI-Gate blockiert den Merge.

---

## 2. Scope & Geltungsbereich

### 2.1 Drei verpflichtende Scan-Profile

| Profil | Wann | Dauer | Ziel | Action |
|---|---|---|---|---|
| **Baseline** | Pro PR | < 20 min | Passive-only Scan + AjaxSpider (`-j`) gegen Frontend + Backend | `zaproxy/action-baseline` |
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
- **Source-Code-Analyse (SAST)** → außerhalb des Scopes.
- **Penetration-Testing** durch externe Auditoren — NFR-015 ergänzt manuelle Pentests, ersetzt sie aber nicht.
- **Last-/Performance-Tests** → eigenes Themengebiet.

---

## 3. Authentifizierungsstrategie

### 3.1 Test-Identitäten

**MUSS**: Drei dedizierte Testkonten existieren ausschließlich in der Staging-/CI-Umgebung:

| Login | Tenant | Rolle | Zweck |
|---|---|---|---|
| `zap-tenant-a-admin@zap.kamerplanter.example` | `zap-tenant-a` | admin | Authentifizierte Active-Scans innerhalb Mandant α |
| `zap-tenant-a-viewer@zap.kamerplanter.example` | `zap-tenant-a` | viewer | Permission-Matrix-Tests |
| `zap-tenant-b-admin@zap.kamerplanter.example` | `zap-tenant-b` | admin | Cross-Tenant-Negativtests gegen Mandant α |

**Domain-Wahl**: `@zap.kamerplanter.example` ist eine Subdomain unter der von RFC 2606 reservierten `.example`-TLD. Die ursprünglich vorgesehene `.test`-Domain wird vom Pydantic-`email-validator` als „special-use reserved name" abgelehnt (RFC 6761), sodass eine Registrierung auch über die öffentliche `/api/v1/auth/register`-Route fehlschlagen würde. Die Subdomain `zap.` macht zusätzlich klar, dass jedes Konto unter diesem Suffix ein DAST-Fixture ist.

**MUSS**: Diese Konten:
- werden über externe Test-Tooling unter `tests/security/zap-setup/` angelegt — **nicht** über produktive Backend-Module. Das Setup-Skript spricht ausschließlich gegen die öffentliche REST-API (`/api/v1/auth/register`, `/api/v1/tenants/...`),
- existieren NICHT in produktiven Umgebungen,
- bekommen ihr Passwort **pro Lauf neu erzeugt** (kryptografischer Zufall, mindestens 32 Zeichen) und reichen es über die Umgebungsvariablen `KP_ZAP_PWD_TENANT_A_ADMIN`, `KP_ZAP_PWD_TENANT_A_VIEWER`, `KP_ZAP_PWD_TENANT_B_ADMIN` an das Setup-Tooling weiter,
- werden bei jedem Re-Build der Staging-Umgebung neu angelegt; Cleanup erfolgt durch Namespace-Lifecycle, nicht durch ein dediziertes Lösch-Skript.

!!! note "Warum pro Lauf erzeugt statt als GitHub-Secret"

    Die ursprüngliche Fassung verlangte drei langlebige GitHub-Secrets. Das war
    an eine dauerhafte Staging-Umgebung gebunden, in der dieselben Konten über
    Läufe hinweg bestehen bleiben. Seit die Scans gegen einen **ephemeren
    Stack** laufen, der pro Lauf entsteht und danach abgeräumt wird, existieren
    die Konten nur für die Dauer eines Jobs — und ein langlebiges Geheimnis für
    ein Wegwerf-Konto ist Angriffsfläche ohne Gegenwert: Es liegt dauerhaft im
    Repository, muss rotiert werden, kann in Logs auftauchen und gilt nach jeder
    Log-Sichtung als kompromittiert.

    Der Zufallswert wird im Job erzeugt, sofort über `::add-mask::` bei der
    Plattform registriert, an das Setup-Skript gereicht und mit dem Runner
    verworfen. Die Schnittstelle des Setup-Tools ändert sich dadurch nicht — es
    liest weiterhin dieselben Umgebungsvariablen; nur ihre Herkunft ist eine
    andere.

    Für einen künftigen Scan gegen eine **dauerhafte** Umgebung gilt die
    ursprüngliche Regel wieder: dort überleben die Konten den Lauf, und ein
    reproduzierbares Passwort ist dann nötig.

**MUSS**: Ein Pre-Deploy-Check (Pipeline-Stufe vor jedem Prod-Release) führt eine reine **Daten-Prüfung** auf dem Prod-DB-Snapshot aus. Da Kamerplanter ArangoDB nutzt, ist die Prüfung als AQL-Query zu formulieren:

```aql
FOR u IN users
  FILTER ENDS_WITH(u.email, "@zap.kamerplanter.example")
  LIMIT 1
  RETURN u._key
```

Jedes zurückgelieferte Dokument ist ein Block-Finding und lässt das Release scheitern. Da das Setup-Tooling ausschließlich unter `tests/` lebt und nicht ins Produktiv-Image gelangt, ist dies eine reine Daten-Hygiene-Kontrolle und keine Code-Existenz-Prüfung.

### 3.2 ZAP-Auth-Konfiguration (JWT-basiert)

**MUSS**: Authentifizierte Scans nutzen den JWT-Login-Endpoint (REQ-023). JWT-Bearer-Tokens werden über ein **HttpSender-Skript** auf jeden Folgerequest gesetzt — nicht über ein klassisches Authentication-Script. Begründung: Ein Authentication-Script setzt den Header nur auf den initialen Login-Reply; ZAP-interne Spider-/Scanner-Komponenten würden ohne HttpSender-Skript anschließend ohne Bearer-Header weiterlaufen.

```javascript
// tests/security/zap-scripts/jwt-httpsender.js
// HttpSender-Script. Hängt das aktuelle Bearer-Token an jeden ausgehenden
// Request an und triggert bei 401 einen Re-Login.

var SCRIPT_TYPE = "httpsender";
var Model = Java.type("org.parosproxy.paros.model.Model");
var ScriptVars = Java.type("org.zaproxy.zap.extension.script.ScriptVars");

var LOGIN_PATH_REGEX = /\/api\/v1\/auth\/(login|refresh)$/;
var TOKEN_VAR = "kamerplanter.jwt.token";

function sendingRequest(msg, initiator, helper) {
  var url = msg.getRequestHeader().getURI().toString();
  if (LOGIN_PATH_REGEX.test(url)) {
    return; // never recurse into the login itself
  }

  var token = ScriptVars.getGlobalVar(TOKEN_VAR);
  if (token !== null && token.length > 0) {
    msg.getRequestHeader().setHeader("Authorization", "Bearer " + token);
  }
}

function responseReceived(msg, initiator, helper) {
  if (msg.getResponseHeader().getStatusCode() === 401) {
    refreshToken(helper);
  }
}

function refreshToken(helper) {
  // Calls /api/v1/auth/login with credentials provided by the GitHub-Actions
  // secret-injected env vars (KP_ZAP_EMAIL / KP_ZAP_PASSWORD), parses the
  // access_token from the JSON response, and stores it in ScriptVars.
  // Implementation details: see docs/security/zap-auth-setup.md.
}
```

**MUSS**: Das Skript liegt unter `tests/security/zap-scripts/jwt-httpsender.js` und ist in `tests/security/zap-context.xml` als HttpSender-Script registriert.
**MUSS**: Das initiale Token wird vom Setup-Skript `seed-cross-tenant.sh` (vgl. §3.3) in `ScriptVars.setGlobalVar(TOKEN_VAR, ...)` geschrieben — damit der erste Request bereits authentifiziert ist.
**MUSS**: Refresh-Token-Rotation (REQ-023) wird in `refreshToken()` abgebildet — bei `401` wird automatisch neu authentifiziert.

**Limitation — 401-Replay**: ZAPs Spider-/Scanner-Komponenten replayen einen Request, der ein `401` erhalten hat, **nicht** automatisch nach dem `refreshToken()`-Lauf. Das Skript stellt nur sicher, dass jeder *folgende* Request mit einem frischen Bearer ausgestattet wird; der ursprüngliche Request bleibt für die Findings-Auswertung als `401` sichtbar. Mitigation:

- **Token-Lebensdauer ≥ Scan-Laufzeit** — JWT-Lifetime im Login (REQ-023) wird für ZAP-Test-Identitäten so gesetzt, dass die `Full-Scan`-Maximaldauer (6 h, §5.3) zuverlässig unter dem TTL liegt. Empfehlung: 8 h Test-Token-Lifetime, ausschließlich in Staging/CI über die Auth-Service-Settings durchgesetzt.
- **Pre-Auth via Setup-Skript** — `seed-cross-tenant.sh` (§3.3) schreibt unmittelbar vor dem Scan-Start einen frischen Bearer in `ScriptVars`, damit der erste Request der Session bereits authentifiziert läuft.
- **Soft-Fail-Triage** — Findings, die ausschließlich auf einer 401-Response beruhen, werden im Triage-Workflow mit Confidence `Low` versehen und nicht als Auth-Bypass eskaliert.

**MUSS**: Die Credentials sind ausschließlich als GitHub-Secrets (`ZAP_TENANT_A_PASSWORD`, `ZAP_TENANT_B_PASSWORD`) verfügbar — keine Klartext-Credentials in Skript oder Context-XML.

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

**MUSS**: Eine ZAP-Passive-Rule prüft cross-tenant: Wenn der URL-Pfad `/api/v1/t/{tenant_slug}/...` einen anderen `tenant_slug` enthält als der `tenant_slug` im JWT-Payload des `Authorization`-Headers, und der Status `200`/`201` ist, wird ein High-Alert ausgelöst. Skript-Skelett:

```javascript
// tests/security/zap-scripts/cross-tenant-passive.js
// Passive-Rule-Script. Liest tenant_slug aus URL und JWT-Payload und
// raised einen High-Alert bei Mismatch + 2xx-Status.

var SCRIPT_TYPE = "passive";
var Base64 = Java.type("java.util.Base64");
var URL_TENANT_RE = /\/api\/v1\/t\/([a-z0-9-]+)\//;

function scan(helper, msg, src) {
  var url = msg.getRequestHeader().getURI().toString();
  var status = msg.getResponseHeader().getStatusCode();
  if (status !== 200 && status !== 201) return;

  var urlMatch = URL_TENANT_RE.exec(url);
  if (!urlMatch) return;
  var urlTenant = urlMatch[1];

  var auth = msg.getRequestHeader().getHeader("Authorization");
  if (!auth || auth.indexOf("Bearer ") !== 0) return;

  var tokenTenant = parseJwtTenantSlug(auth.substring(7));
  if (!tokenTenant) return;

  if (urlTenant !== tokenTenant) {
    helper.newAlert()
      .setRisk(3)            // High
      .setConfidence(2)      // Medium (header-based, not exploit-confirmed)
      .setName("Cross-Tenant Data Exposure (kamerplanter)")
      .setDescription(
        "JWT belongs to tenant '" + tokenTenant +
        "' but successfully accessed resource of tenant '" + urlTenant + "'. " +
        "Likely missing require_permission() dependency or tenant guard."
      )
      .setUri(url)
      .setEvidence("URL tenant=" + urlTenant + " ; JWT tenant=" + tokenTenant)
      .setSolution("Add require_permission(...) and tenant guard to this endpoint; verify against REQ-024 permission matrix.")
      .setCweId(284)         // Improper Access Control
      .setWascId(2)
      .setMessage(msg)
      .raise();
  }
}

function parseJwtTenantSlug(jwt) {
  var parts = String(jwt).split(".");
  if (parts.length !== 3) return null;
  try {
    var payloadJson = new java.lang.String(Base64.getUrlDecoder().decode(parts[1]));
    var payload = JSON.parse(String(payloadJson));
    return payload.tenant_slug || payload.tenant || null;
  } catch (e) {
    return null;
  }
}
```

**MUSS**: Cross-Tenant-Findings sind immer **Critical** (vgl. §5.1 Severity-Mapping) und blockieren immer den Merge.
**MUSS**: Das Skript ist in `tests/security/zap-context.xml` als Passive-Script registriert und wird in allen authentifizierten Profilen (Full-Scan + API-Scan mit Auth) aktiv.
**SOLL**: Eine Spike-Story prototypisiert das Skript gegen einen lokalen Stack und verifiziert beide Pfade (TP: tatsächlicher Cross-Tenant-Treffer; TN: Same-Tenant-Zugriff erzeugt keinen Alert) bevor das Build-Gate scharfgeschaltet wird.

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

**MUSS**: Pro PR läuft ein Baseline-Scan (passiv + AjaxSpider) gegen die Frontend-URL des ephemeren Stacks.

!!! note "Umsetzung weicht bewusst von `zaproxy/action-baseline` ab"

    Die Implementierung in `.github/workflows/security-zap-baseline.yml` ruft
    ZAP über `docker run` auf, nicht über die Wrapper-Action. Zwei Gründe, beide
    nicht umgehbar:

    1. **Netzwerk.** `docker-compose.security.override.yml` bindet den Stack
       absichtlich nur an `127.0.0.1` — „so a CI runner does not advertise the
       internal stack to the wider network". Ein Container erreicht das
       Loopback des Hosts nicht, und die ZAP-Actions bieten keine
       Netzwerk-Option. Die Alternativen wären, die Bindung auf `0.0.0.0`
       aufzuweichen oder ZAP ans Compose-Netz zu hängen. Letzteres ist sicherer
       und ändert nichts am Override.
    2. **Skripte.** §3.2 und §3.3 verlangen ein HttpSender- und ein
       Passive-Rule-Skript in ZAP. Die Wrapper-Actions bieten dafür keinen Weg,
       das Full-Profil bräuchte also ohnehin `docker run`; ein Mechanismus für
       beide Profile hält sie vergleichbar.

    Das ZAP-Image ist per Digest gepinnt (NFR-018 §3), nicht per `:stable`.

**MUSS**: Beide PR-Scans laufen mit `-I` (kein Abbruch bei Warnungen). Das
Urteil fällt `scripts/security/zap_gate.py` nach der Matrix aus §5.1 und dem
Confidence-Filter aus §5.2 — ZAPs eigene Exit-Codes kennen weder Severity-Stufen
noch Confidence und könnten die hier festgelegte Politik nicht abbilden. Das Gate
behandelt einen fehlenden oder strukturell unerwarteten Report als **Fehlschlag**,
nicht als „keine Findings".

Ursprünglicher Entwurf (Referenz, nicht die Implementierung):

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

**MUSS**: Der API-Scan deckt ausschließlich Routen ab, die in der OpenAPI deklariert sind. Routen, die in der Implementierung existieren, aber nicht in OpenAPI auftauchen, bilden eine eigene Finding-Class (siehe §4.4).

#### Auth-Bypass-Detection (zwei Pässe)

**MUSS**: Der API-Scan im **Full-Profil** (Nightly) läuft gegen jede authentifiziert deklarierte Route **zweimal**:

1. **Authentifizierter Pass** — mit gültigem Bearer-Token via HttpSender-Skript (§3.2). Erwartete Status-Klasse: `2xx` für GET / List / Detail, `2xx`/`4xx` (Validation) für POST.
2. **Anonymer Pass** — derselbe Request ohne `Authorization`-Header. Erwartete Status-Klasse: `401`/`403`.

**MUSS**: Findings-Logik:

| Anonymer Status | Authentifizierter Status | Klassifikation | Severity |
|---|---|---|---|
| `200` / `201` | `200` / `201` | **Auth-Bypass** — authentifizierter Endpunkt liefert ohne Bearer eine erfolgreiche Antwort. | **Critical** (§5.1 Eskalation) |
| `200` / `201` | `401` / `403` | Möglicher Spec-Drift: Endpunkt ist als auth-pflichtig deklariert, in der Realität aber öffentlich. | Medium |
| `401` / `403` | `200` / `201` | Erwarteter Default — kein Finding. | — |
| `401` / `403` | `401` / `403` | Token ist abgelaufen oder fehlerhaft — Lauf wird verworfen. | Job-Diagnose |

**MUSS**: Die Implementierung nutzt entweder zwei `action-api-scan`-Steps mit unterschiedlichen Context-Files (`zap-context-auth.xml` / `zap-context-anon.xml`) oder ein eigenes Active-Rule-Skript, das pro Route den anonymen Variant-Request schickt. Beide Pfade sind zulässig — die Wahl wird in `docs/security/zap-auth-bypass-impl.md` (Phase 3) festgelegt.

**MUSS**: Routen, die in §3.4 als „Out-of-Scope für unauthentifizierte Scans" markiert sind (`/auth/login`, `/auth/register`, `/auth/oauth/*`, `/calendar/feeds/{token}`, `/health`, `/ready`), werden vom anonymen Pass ausgeschlossen.

### 4.3 Full-Scan (Nightly, authentifiziert, AjaxSpider)

**MUSS**: Täglich läuft `zaproxy/action-full-scan` gegen Staging mit aktivem AjaxSpider:

```yaml
# .github/workflows/security-zap-nightly.yml
on:
  schedule:
    - cron: "0 1 * * *"   # 02:00 Europe/Berlin (winter) — 60 Min nach NFR-014 Nuclei-Nightly, damit Nuclei zuerst läuft
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
          # Auth-Header + HttpSender-/Passive-Skripte werden zentral
          # in tests/security/zap-context.xml registriert. Replacer- oder
          # Token-Konfiguration NICHT als CLI-Override — siehe §3.2 / §3.3.
          cmd_options: >-
            -a
            -j
            -T 60
            -n /zap/wrk/tests/security/zap-context.xml
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

**MUSS**: ZAP-Risk-Level werden strikt 1:1 auf das Severity-Modell aus NFR-014 gemappt; **Critical** entsteht ausschließlich durch explizite Eskalations-Regeln, da ZAP von Haus aus nur drei Risiko-Stufen kennt:

| ZAP Risk | Severity (NFR-Modell) | PR-Gate | Nightly | Aktion |
|---|---|---|---|---|
| **High** | High | Block | Block + Issue | PR-Merge unmöglich, 7 Tage SLA |
| **Medium** | Medium | Warn | Warn + Issue | Triage in 7 Tagen |
| **Low** | Low | Info | Info | Backlog |
| **Informational** | Info | Sammeln | Sammeln | Reine Inventarisierung |

**Critical-Eskalation** — Findings folgender Klassen werden unabhängig vom ZAP-Risk auf **Critical** angehoben und blockieren immer (auch im Nightly):

| Eskalations-Regel | Quelle | Begründung |
|---|---|---|
| Cross-Tenant-Treffer | `cross-tenant-passive.js` (§3.3) | REQ-024-Bruch — direkter Datenleak zwischen Mandanten |
| Auth-Bypass auf authentifiziertem Endpunkt | API-Scan, Status `200` ohne Bearer | Vollständiger Schutzverlust |
| JWT-Leak in Response-Body / URL / Header | passive-Rule + NFR-014 `kamerplanter-jwt-leak.yaml` | Session-Hijacking-Vektor |

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

**MUSS**: Regelanpassungen werden ausschließlich in `tests/security/zap-rules.tsv` und `tests/security/zap-api-rules.tsv` versioniert:

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
| **Spec-Drift API ↔ Implementierung** | Endpunkte existieren in der Implementierung, aber nicht in OpenAPI → Schatten-API | Hoch | Spec-Drift-Job (§4.4), automatische Findings |
| **Falsch konfigurierte Cookies (REQ-023 RefreshToken)** | Refresh-Token wird ohne `HttpOnly`/`Secure`/`SameSite` ausgeliefert → Session-Hijacking | Mittel | Baseline-Cookie-Rules, Active-Rule für Cookie-Flags |
| **Veraltete IGNORE-Regeln** | Reale Findings werden ohne neue Bewertung dauerhaft unterdrückt | Mittel | Pflicht-Ablaufdaten in tsv, Karenz-CI-Job |
| **Performance-Drift (Full-Scan zu langsam)** | Nightly läuft nicht zuverlässig durch, Findings altern | Niedrig | Performance-Schwellen + Soft-Fail-Issue mit Diagnose |

---

**Dokumenten-Ende**

**Version**: 1.1
**Status**: Genehmigt
**Letzte Aktualisierung**: 2026-04-28
**Review**: Genehmigt
**Genehmigung**: Genehmigt (2026-06-11)
