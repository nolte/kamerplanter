---
ID: DEVTOOL-001
Titel: MCP-Server-Integration für Claude Code — Konfiguration, Server-Katalog, Verwendungsregeln
Kategorie: Entwickler-Tooling
Unterkategorie: Claude Code, Model Context Protocol, AI-gestützte Entwicklung
Fokus: Beides (Backend & Frontend & HA-Integration)
Technologie: Claude Code, MCP (Model Context Protocol), npx, Docker
Status: Verbindlich
Priorität: Mittel
Version: 1.0
Autor: Tooling
Datum: 2026-04-25
Tags: [mcp, claude-code, dev-tooling, ai, debugging, browser, playwright, chrome-devtools, context7, kubernetes, postgres, github]
Abhängigkeiten: [NFR-008, NFR-008a]
Betroffene Module: [.mcp.json, ~/.claude.json, .claude/settings.json]
---

# DEVTOOL-001: MCP-Server-Integration für Claude Code

## 1. Zweck

Dieses Dokument legt fest, **welche MCP-Server (Model Context Protocol) im Kamerplanter-Projekt eingesetzt werden, wie sie konfiguriert werden und wann sie zu verwenden sind**.

Es richtet sich an:

- **Entwickler**, die ihre lokale Claude-Code-Umgebung einrichten,
- **Claude-Code-Agents**, die diese Server bei Bedarf nutzen,
- **Reviewer**, die prüfen, ob Tooling-Änderungen den hier definierten Konventionen entsprechen.

## 2. Abgrenzung

| Dokument | Fokus |
|----------|-------|
| `spec/stack.md` | **Produktiver** Tech-Stack der Applikation (Python, React, ArangoDB …) |
| `spec/style-guides/*.md` | Code-Konventionen, durchgesetzt durch Linter/Compiler |
| `spec/nfr/NFR-008*.md` | Test-Strategie und verbindliche **Selenium**-E2E-Konventionen |
| **DEVTOOL-001 (dieses Dokument)** | Tooling, das **Claude Code** zusätzlich zur reinen Codebasis nutzt |

**Wichtig — Abgrenzung zu NFR-008/NFR-008a:**

> Die in `tests/e2e/` definierte Selenium-Test-Suite (`docker-compose.e2e.yml`, Selenium Grid + Chrome Node) bleibt **die einzige Quelle der Wahrheit** für E2E-Tests. MCP-Server sind **kein Test-Framework-Ersatz**, sondern Debug-, Verifikations- und Recherche-Hilfsmittel für die Entwicklung. Selenium-PageObjects, TC-IDs und Testprotokolle werden nicht durch MCP-Server abgelöst.

## 3. Grundlagen MCP

Das **Model Context Protocol** ist ein offener Standard, über den Claude Code zusätzliche Tools (Browser, Datenbanken, externe APIs) ansprechen kann. Jeder MCP-Server läuft als separater Prozess auf dem Host des Entwicklers (oder in einem zugewiesenen Container) und kommuniziert mit Claude Code über stdio oder HTTP/WebSocket.

### 3.1 Konfigurationsorte

Claude Code liest MCP-Konfigurationen aus drei Ebenen (Reihenfolge = Präzedenz, oben gewinnt):

| Datei | Scope | Eingecheckt? | Verwendungsempfehlung |
|-------|-------|--------------|------------------------|
| `.mcp.json` (Repo-Root) | Projekt | **Ja** (git-tracked) | Server, die das **gesamte Team** für Kamerplanter braucht |
| `~/.claude.json` | Benutzer (alle Projekte) | Nein | Persönliche Server (Sentry-Token, GitHub-PAT etc.) |
| `.claude/settings.json` | Projekt-Override | Optional | Ausnahmen / lokale Overrides |

**Regel:** Server mit Secrets (PATs, API-Keys) gehören **nie** in `.mcp.json`. Sie werden über `~/.claude.json` mit Umgebungsvariablen-Referenzen konfiguriert.

### 3.2 Konfigurations-Schema (Beispiel)

```jsonc
{
  "mcpServers": {
    "<name>": {
      "command": "<binary-or-npx>",
      "args": ["<arg1>", "<arg2>"],
      "env": { "API_KEY": "${ENV_VAR_NAME}" }
    }
  }
}
```

## 4. Server-Katalog

### 4.1 Übersicht

| Server | Scope | Konfig-Ort | Priorität | Status |
|--------|-------|-----------|-----------|--------|
| chrome-devtools-mcp | Projekt | `.mcp.json` | Hoch | Verbindlich |
| @playwright/mcp | Projekt | `.mcp.json` | Hoch | Verbindlich |
| context7 (Upstash) | Projekt | `.mcp.json` | Hoch | Verbindlich |
| kubernetes-mcp-server | Projekt | `.mcp.json` | Hoch | Verbindlich (read-only) |
| github-mcp-server | Benutzer | `~/.claude.json` | Mittel | Optional |
| postgres-mcp (Timescale) | Benutzer | `~/.claude.json` | Niedrig | Optional |
| sentry-mcp | Benutzer | `~/.claude.json` | Niedrig | Optional |

### 4.2 chrome-devtools-mcp

**Zweck:** Direkter Zugriff auf Chrome DevTools Protocol — Console-Logs auslesen, Netzwerk inspizieren, Stack-Traces, Performance-Snapshots, Screenshots aus einem laufenden Chrome.

**Quelle:** https://github.com/ChromeDevTools/chrome-devtools-mcp (offiziell, Chrome DevTools Team)

**Installation & Konfiguration:**

```jsonc
// .mcp.json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

**Voraussetzung:** Chrome muss mit Debug-Port laufen, z. B.

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

**Wann verwenden:**

- Frontend-Crash, dessen Stack-Trace nur in der Browser-Console steht (z. B. fehlender i18n-Key, MUI-Prop-Fehler).
- API-Calls debuggen (Status-Codes, Headers, Payloads) ohne Network-Tab manuell zu öffnen.
- Visuelle Regression: Screenshot eines Zustands für Vergleich/Bericht.

**Wann NICHT verwenden:**

- Für reproduzierbare E2E-Verifikation → Selenium (`tests/e2e/`).
- Für UI-Tests in CI → ungeeignet, da Chrome-Instanz lokal benötigt wird.

### 4.3 @playwright/mcp

**Zweck:** Interaktive Browser-Automatisierung über Playwright — Seiten öffnen, klicken, Formulare ausfüllen, Selektoren ermitteln, Screenshots erzeugen. Headless oder mit sichtbarem Browser.

**Quelle:** https://github.com/microsoft/playwright-mcp (offiziell, Microsoft)

**Integrationsmodell für Kamerplanter (verbindlich):**

> **Modell A — Host-only.** Playwright-MCP läuft auf dem Entwickler-Host. Es greift **nicht** in die `docker-compose.e2e.yml` ein. Selenium-Stack bleibt unverändert.

```jsonc
// .mcp.json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--browser", "chromium"]
    }
  }
}
```

**Verbindung zur Anwendung:**

| Quelle | URL | Bemerkung |
|--------|-----|-----------|
| Vite Dev-Server (Skaffold/Kind oder lokal) | `http://localhost:5173` | Standard-Workflow |
| E2E-Compose-Stack (für Live-Debug) | `http://localhost:8080` | Nur, wenn Frontend-Port in `docker-compose.e2e.yml` **temporär** publiziert wird; nicht ins git committen |

**Wann verwenden:**

- Schnelle Klick-Verifikation neuer UI-Komponenten, ohne erst Selenium-Test zu schreiben.
- Selektoren für neue Selenium-PageObjects ermitteln.
- Failed Selenium-Test live nachvollziehen (manuell denselben Pfad gehen, Console + Network beobachten).

**Wann NICHT verwenden:**

- Als Ersatz für Selenium-Tests — NFR-008a verlangt weiterhin pytest + Selenium für jede E2E-Anforderung.
- In CI-Pipelines.
- Für Last- oder Performance-Tests.

**Verhältnis zum Selenium-Stack:**

```
docker-compose.e2e.yml
  ├─ selenium-hub          ◄── unverändert, Single Source of Truth für E2E (NFR-008a)
  ├─ chrome (Selenium Node) ◄── unverändert
  └─ e2e-tests (pytest)    ◄── unverändert

Host (Entwicklung)
  └─ playwright-mcp        ◄── ergänzendes Debug-Werkzeug, nur für Claude Code
```

### 4.4 context7 (Upstash)

**Zweck:** Liefert tagesaktuelle, versionsspezifische Dokumentations-Snippets für Bibliotheken (React 19, MUI 7, FastAPI ≥ 0.115, Pydantic v2, Authlib …). Verhindert das Schreiben von Code gegen veraltete oder halluzinierte APIs.

**Quelle:** https://github.com/upstash/context7 (Upstash, Open Source)

**Installation & Konfiguration:**

```jsonc
// .mcp.json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

**Wann verwenden:**

- **Vor** dem Schreiben von Code, der eine API verwendet, deren Aktualität unsicher ist (typische Beispiele bei Kamerplanter: MUI 7 `Grid size={{xs:12,sm:4}}`-Syntax, React 19 `use()`-Hook, Pydantic v2 `model_validator`).
- Bei Migrations-Aufgaben (z. B. MUI 5 → 7).
- Wenn ein Codebeispiel in einer Antwort widerlegt wurde („das gibt es so nicht mehr").

**Wann NICHT verwenden:**

- Für interne Kamerplanter-Module → eigene Specs (`spec/req/`, `spec/nfr/`) sind autoritativ.
- Für Bibliotheken, die nicht im `spec/stack.md` aufgeführt sind, ohne vorherige Stack-Diskussion.

### 4.5 github-mcp-server

**Zweck:** Issues, Pull Requests, Workflow-Runs, Reviews und Releases ansprechen, ohne via `gh`-CLI über Bash zu gehen.

**Quelle:** https://github.com/github/github-mcp-server (offiziell, GitHub)

**Konfiguration:** Benutzer-Scope wegen PAT.

```jsonc
// ~/.claude.json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PAT}" }
    }
  }
}
```

**PAT-Anforderungen:** Mindestens `repo`, `read:org`, `read:project`. **Niemals** in `.mcp.json` committen.

**Wann verwenden:**

- PR-Status, Check-Runs und Review-Kommentare prüfen.
- Issues beim Starten einer Implementierung lesen.
- Releases vorbereiten.

**Wann NICHT verwenden:**

- Für git-lokale Operationen (`git diff`, `git log`) → `Bash` nutzen.
- Für PR-Erstellung mit reichhaltigem Body → das spezialisierte Skill / Agent (`pr-to-develop`) nutzen, nicht den MCP-Server allein.

### 4.6 kubernetes-mcp-server

**Zweck:** `kubectl`-äquivalente Operationen (logs, exec, describe, get) als typisierte MCP-Tools — nützlich für den Skaffold/Kind-Workflow von Kamerplanter und das HA-Integration-Deployment.

**Quelle:** https://github.com/manusa/kubernetes-mcp-server (Community, gut gepflegt)

**Konfiguration:** Projekt-Scope, da Kontext und Namespace projektspezifisch sind.

```jsonc
// .mcp.json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "kubernetes-mcp-server@latest", "--read-only"]
    }
  }
}
```

**Sicherheits-Hinweis:** `--read-only` ist die **Default-Empfehlung** im Projekt. Schreib-Operationen (`apply`, `delete`, `exec`) bleiben in Bash-Tool-Aufrufen sichtbar und werden vom Berechtigungsmodell von Claude Code erfasst. Insbesondere die im `CLAUDE.md` dokumentierte Regel **„`kubectl delete pod` verboten für Home-Assistant — `kill 1` verwenden"** wird durch `--read-only` strukturell abgesichert.

**Wann verwenden:**

- Pod-Status / Logs schnell einsehen.
- Health-Checks im Kind-Cluster prüfen.
- Welcher Service hängt? Welcher InitContainer ist nicht durchgelaufen?

**Wann NICHT verwenden:**

- Für Image-Builds oder Deployment → **Skaffold ist das einzige Werkzeug** für den Entwicklungsprozess (siehe CLAUDE.md).
- Für Produktions-Cluster.

### 4.7 postgres-mcp (für TimescaleDB)

**Zweck:** Lese-Zugriff auf PostgreSQL/TimescaleDB-Instanzen — nützlich, sobald REQ-005 (Hybrid-Sensorik) implementiert ist und Sensor-Daten in TimescaleDB liegen.

**Quelle:** https://github.com/modelcontextprotocol/servers/tree/main/src/postgres (offizielle Referenz-Implementierung)

**Konfiguration:** Benutzer-Scope wegen Connection-String mit Credentials.

```jsonc
// ~/.claude.json
{
  "mcpServers": {
    "timescaledb": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://readonly:${PG_PW}@localhost:5432/kamerplanter_sensors"
      ]
    }
  }
}
```

**Pflicht:** Verbindung **ausschließlich** mit Read-Only-User. Niemals mit Application-User oder Superuser.

**Wann verwenden:**

- Ad-hoc-Queries gegen Time-Series-Daten beim Debuggen von Downsampling, Retention oder Sensor-Fallback-Chain.

**Wann NICHT verwenden:**

- Für ArangoDB → siehe Abschnitt 4.8.
- Für DDL-Änderungen → in den Backend-Migrations-Code.

### 4.8 ArangoDB

**Status:** **Kein verbindlicher MCP-Server.** Die existierenden Community-MCP-Server für ArangoDB sind aktuell nicht ausgereift genug für den Produktiveinsatz im Projekt.

**Workaround:** AQL-Queries werden über `Bash` mit `arangosh` oder über das Backend-API ausgeführt.

**Re-Evaluierung:** Bei nächstem Stack-Review (siehe `spec/analysis/`).

### 4.9 sentry-mcp

**Zweck:** Sentry-Issues, Events und Stack-Traces direkt aus Claude Code abfragen — nur relevant, sobald Sentry-Consent (siehe REQ-025) aktiviert und Sentry produktiv im Einsatz ist.

**Quelle:** https://github.com/getsentry/sentry-mcp (offiziell, Sentry)

**Konfiguration:** Benutzer-Scope.

```jsonc
// ~/.claude.json
{
  "mcpServers": {
    "sentry": {
      "command": "npx",
      "args": ["-y", "@sentry/mcp-server@latest"],
      "env": {
        "SENTRY_AUTH_TOKEN": "${SENTRY_TOKEN}",
        "SENTRY_ORG": "kamerplanter"
      }
    }
  }
}
```

**Wann verwenden:** Frontend- oder Backend-Fehler ohne lokale Reproduktion.

**Wann NICHT verwenden:** Vor Aktivierung der Sentry-Integration. Vorher gibt es keine Daten.

## 5. Kombination mit Selenium-E2E-Stack

Der Selenium-Stack in `docker-compose.e2e.yml` und die Konventionen aus NFR-008/NFR-008a bleiben **unverändert**. MCP-Server greifen ausschließlich **außerhalb** des Compose-Netzes:

```
┌──────────────────────────────────────────────────────────────┐
│                    Entwickler-Host                           │
│                                                              │
│  Claude Code                                                 │
│      │                                                       │
│      ├─► chrome-devtools-mcp ──► localhost:9222 (Chrome)     │
│      ├─► playwright-mcp     ──► chromium (host)              │
│      ├─► context7           ──► api.context7.com (HTTPS)     │
│      └─► kubernetes-mcp     ──► kind cluster (kubectl)       │
│                                                              │
│  ┌──────── docker-compose.e2e.yml (unverändert) ─────────┐   │
│  │ selenium-hub  ◄── e2e-tests (pytest)                  │   │
│  │ chrome-node   ◄── frontend ◄── backend ◄── arangodb   │   │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Regel:** Kein MCP-Server darf in `docker-compose.e2e.yml` als Service eingefügt werden. Wenn Live-Debug-Zugriff in den E2E-Stack notwendig ist, geschieht dies durch:

1. **Temporäres** Publizieren des `frontend`-Ports (lokal, nicht ins Repo committen):
   ```bash
   docker compose -f docker-compose.e2e.yml \
     run --service-ports --rm frontend
   ```
2. Playwright-MCP / Chrome-DevTools-MCP auf dem Host gegen `http://localhost:<port>`.

## 6. Operative Tasks (Taskfile)

Für die wiederkehrenden Aufgaben rund um MCP existieren verbindliche `task`-Targets in `Taskfile.yaml`. Sie sind die einzige unterstützte Art, Chrome im Debug-Modus zu starten oder den E2E-Stack für Live-Debug verfügbar zu machen.

| Target | Zweck |
|--------|-------|
| `task mcp:setup` | Einmalig: Playwright-Chromium laden, npx-Cache aller MCP-Pakete vorbefüllen |
| `task mcp:chrome` | Chrome mit `--remote-debugging-port=9222` und isoliertem Profil starten |
| `task mcp:chrome:stop` | Debug-Chrome stoppen |
| `task mcp:status` | Health-Check: Debug-Port, kubectl-Kontext, Playwright-Cache, context7-Erreichbarkeit |
| `task mcp:e2e:debug` | E2E-Frontend aus `docker-compose.e2e.yml` mit publishtem Port `:8080` starten — ohne die Compose-Datei zu verändern |

**Regel:** Manuelle `google-chrome --remote-debugging-port=…`-Aufrufe sind im Projekt nicht mehr vorgesehen — der `mcp:chrome`-Task erzwingt isoliertes Profil und verhindert versehentliches Verwenden des persönlichen Chrome-Profils. Abweichungen davon müssen begründet im PR dokumentiert werden.

## 7. Setup-Empfehlung

### 6.1 Minimal-Setup (alle Entwickler — verbindlich)

In `.mcp.json` (eingecheckt):

```jsonc
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--browser", "chromium"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "kubernetes-mcp-server@latest", "--read-only"]
    }
  }
}
```

### 6.2 Persönliche Server (mit Tokens)

In `~/.claude.json` (nie committen). Beispiele siehe Abschnitt 4.5, 4.7, 4.9.

### 6.3 Voraussetzung für `kubernetes-mcp-server`

Funktionierender `kubectl`-Kontext auf einen Cluster, in dem Kamerplanter läuft (typischerweise Skaffold/Kind):

```bash
kubectl config current-context   # erwartet: kind-kamerplanter o. ä.
kubectl get pods -n default      # muss Backend/Frontend/ArangoDB zeigen
```

Der MCP-Server greift auf den Default-Kontext aus `~/.kube/config` zu. Read-Only-Modus blockiert mutierende Operationen serverseitig — Schreiboperationen müssen weiter über `Bash` (mit Berechtigungs-Prompt) erfolgen.

## 8. Sicherheits- und DSGVO-Hinweise

| Risiko | Maßnahme |
|--------|----------|
| Geheimnisse in `.mcp.json` | **Verboten.** Nur Umgebungsvariablen-Referenzen, Tokens leben in `~/.claude.json`. |
| Schreibzugriff auf Cluster | `--read-only` für `kubernetes-mcp-server` ist Default. |
| Personenbezogene Daten an externe MCP-Server | Kein MCP-Server darf personenbezogene Produktivdaten (User-Daten, Sensor-Logs einer realen Person) an externe Endpunkte schicken. Bei `context7` und `chrome-devtools-mcp` ist das nicht der Fall. Bei `sentry-mcp` greifen die DSGVO-Regeln aus REQ-025. |
| Browser-Profile-Leakage | `playwright-mcp` und `chrome-devtools-mcp` immer mit isoliertem `--user-data-dir` betreiben — niemals gegen das persönliche Chrome-Profil. |
| Read-Only-DB-User | `postgres-mcp` ausschließlich mit Read-Only-Rolle verbinden. |

## 9. Wartung

- **Versions-Updates:** `@latest` in den `npx`-Argumenten ist im Minimal-Setup akzeptabel; bei stabilen Setups auf konkrete Versionen pinnen, wenn Breaking Changes drohen.
- **Server-Re-Evaluierung:** Mindestens halbjährlich prüfen, ob neue offizielle MCP-Server für ArangoDB, Authlib, Celery oder weitere Stack-Komponenten verfügbar sind.
- **Diese Spec:** Bei jedem Hinzufügen, Entfernen oder Ändern eines MCP-Servers im Projekt aktualisieren.

## 10. Referenzen

- Model Context Protocol Spezifikation: https://modelcontextprotocol.io/
- Claude-Code MCP-Dokumentation: `/help` → MCP-Abschnitt
- NFR-008 Teststrategie & Testprotokoll: `spec/nfr/NFR-008_Teststrategie-Testprotokoll.md`
- NFR-008a E2E-Selenium-Teststandard: `spec/nfr/NFR-008a_E2E-Selenium-Teststandard.md`
- CLAUDE.md (Repo-Root): Skaffold-Workflow, HA-Deploy-Regeln
