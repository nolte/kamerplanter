---
tags:
  - claude-code
  - mcp
  - debugging
  - tooling
---

# MCP-Werkzeuge

Diese Seite beschreibt die im Projekt eingerichteten **MCP-Server (Model Context Protocol)**, die Claude Code zusätzlich zur Codebasis nutzen kann. Sie zeigt **wie du sie verwendest, welchen konkreten Mehrwert sie bringen, wie der Workflow ohne sie aussieht** und **welche Einschränkungen die manuelle Variante hat**.

Verbindliche Spezifikation: [`spec/dev-tooling/MCP-SERVERS.md`](https://github.com/nolte/kamerplanter/blob/main/spec/dev-tooling/MCP-SERVERS.md) (DEVTOOL-001).

!!! info "Selenium bleibt unverändert"
    MCP-Werkzeuge **ersetzen keine E2E-Tests**. Die `tests/e2e/`-Suite und `docker-compose.e2e.yml` bleiben gemäß [NFR-008a](https://github.com/nolte/kamerplanter/blob/main/spec/nfr/NFR-008a_E2E-Selenium-Teststandard.md) die alleinige Quelle der Wahrheit für E2E. MCP-Server sind **Debug- und Recherche-Hilfsmittel** für die Entwicklung.

---

## Schnellstart

```bash
# 1. Einmalig: Playwright-Chromium laden + npx-Cache wärmen
task mcp:setup

# 2. Chrome mit Debug-Port starten (für chrome-devtools-mcp)
task mcp:chrome

# 3. Status aller MCP-Voraussetzungen prüfen
task mcp:status

# 4. Claude Code starten — beim ersten Aufruf eines MCP-Tools
#    fragt Claude einmalig nach Berechtigung
claude

# 5. Verfügbare Server prüfen
/mcp
```

Die `.mcp.json` ist im Repo eingecheckt — Claude Code lädt sie automatisch.

### Verfügbare Tasks

| Task | Zweck |
|------|-------|
| `task mcp:setup` | Einmalig: Playwright-Browser laden, npx-Cache aller MCP-Pakete vorbefüllen |
| `task mcp:chrome` | Chrome mit `--remote-debugging-port=9222` und isoliertem Profil starten |
| `task mcp:chrome:stop` | Debug-Chrome stoppen |
| `task mcp:status` | Übersicht: Chrome-Port, kubectl-Kontext, Playwright-Cache, context7-Erreichbarkeit |
| `task mcp:e2e:debug` | E2E-Stack-Frontend mit publishtem Port `:8080` für Live-Debug starten |

`task mcp:chrome` akzeptiert Variablen:

```bash
# Anderen Start-URL nutzen
MCP_CHROME_URL=http://localhost:8080 task mcp:chrome

# Anderes Profil-Verzeichnis
MCP_CHROME_PROFILE=/tmp/my-debug task mcp:chrome
```

Konfigurierte Server:

| Server | Zweck | Voraussetzung |
|--------|-------|----------------|
| `chrome-devtools` | Browser-Console / Netzwerk / Stack-Traces auslesen | Chrome mit `--remote-debugging-port=9222` |
| `playwright` | UI ferngesteuert klicken, Screenshots, Selektoren ermitteln | Chromium-Binary (lädt automatisch beim ersten Lauf) |
| `context7` | Aktuelle, versions­spezifische Bibliotheks-Docs | Internetverbindung |
| `kubernetes` | Pod-Logs, Status, Describe (read-only) im Skaffold/Kind-Cluster | Funktionierender `kubectl`-Kontext |

---

## chrome-devtools-mcp

### Mehrwert

Claude kann **direkt in deinen laufenden Browser schauen** — Console-Errors, Netzwerk-Requests, Stack-Traces, DOM-Zustand. Damit wird ein typischer „bei mir crashed die Phasen-Detail-Seite"-Zuruf zur konkreten Diagnose statt Rätselraten.

| Aufgabe | Mit `chrome-devtools` | Ohne |
|---------|------------------------|------|
| Frontend-Crash diagnostizieren | Stack-Trace + Console-Error wird automatisch gelesen | Du musst Trace abtippen oder Screenshot teilen |
| Failed API-Call analysieren | Status, Headers, Request- und Response-Body werden ausgelesen | Du öffnest manuell den Network-Tab und kopierst |
| State-Verifikation nach Aktion | DOM, localStorage, Cookies werden direkt inspiziert | Du beschreibst, was du siehst |

### Nutzung

```bash
# Chrome mit Debug-Port starten (einmalig pro Session)
task mcp:chrome
```

Der Task startet Chrome im Hintergrund mit `--remote-debugging-port=9222` und einem isolierten Profil unter `/tmp/chrome-debug`. Bei laufendem Vite-Dev-Server (Port 5173) wird die App direkt geöffnet.

In Claude Code: Frage einfach „Schau in den Browser, da gibt's einen Fehler". Claude verbindet sich auf `localhost:9222`, listet offene Tabs und liest Console + Network.

```bash
# Status prüfen
task mcp:status

# Chrome wieder beenden
task mcp:chrome:stop
```

!!! warning "Isoliertes Browser-Profil"
    `task mcp:chrome` verwendet automatisch `--user-data-dir=/tmp/chrome-debug`. **Niemals** dein persönliches Chrome-Profil verwenden — sonst greift Claude potenziell auf dein gesamtes Browser-Verlauf-, Cookies- und Passwort-Material zu.

### Ohne chrome-devtools-mcp

1. DevTools manuell öffnen (`F12`).
2. Console / Network-Tab fotografieren oder Text kopieren.
3. In Claude einfügen.

**Einschränkungen:**

- **Zeitverlust** — manueller Copy-Paste-Loop bei jedem Iterations­schritt.
- **Unvollständig** — Stack-Trace ist oft eingeklappt, Source-Maps werden vergessen, Network-Body wird nicht mitkopiert.
- **Kein Live-State** — Claude sieht den Browser-Zustand nur zum Zeitpunkt deines Screenshots, kann nicht „nochmal nachschauen".

---

## @playwright/mcp

### Mehrwert

Claude kann **eigenständig durch die UI klicken**, Formulare ausfüllen, Screenshots machen und Selektoren für Tests ermitteln. Statt zu beschreiben „klick auf den Button, dann das Dropdown" kann Claude den Workflow direkt durchspielen und reportet, was passiert.

| Aufgabe | Mit `playwright` | Ohne |
|---------|-------------------|------|
| Schnelle Sichtprüfung neuer UI | Claude öffnet Seite, screenshottet, beschreibt | Du startest Browser, klickst, beschreibst |
| Selektoren für neuen Selenium-Test ermitteln | Claude inspiziert DOM, schlägt stabile `data-testid`-Selektoren vor | Du öffnest DevTools, suchst manuell |
| Failed Selenium-Test reproduzieren | Claude geht denselben Pfad live nach, vergleicht mit Test-Erwartung | Du reproduzierst manuell, beschreibst Diff |
| Visuelle Regression nach UI-Änderung | Vorher/Nachher-Screenshot derselben Seite | Manuelle Screenshots an mehreren Stellen |

### Nutzung

Verbindung zur Anwendung:

| Quelle | URL |
|--------|-----|
| Vite Dev-Server (Skaffold/Kind) | `http://localhost:5173` |
| Vite Dev-Server (lokal `npm run dev`) | `http://localhost:5173` |
| E2E-Compose-Stack (Live-Debug) | `http://localhost:8080` (siehe „Live-Debug gegen E2E-Stack" unten) |

In Claude Code: „Öffne die Phasen-Detail-Seite und prüfe, ob der Speichern-Button beim System-Phasen ausgeblendet ist."

### Live-Debug gegen den E2E-Stack

Wenn ein Selenium-Test in `docker-compose.e2e.yml` failed und du den exakten Zustand live sehen willst:

```bash
task mcp:e2e:debug
```

Der Task startet das Frontend aus `docker-compose.e2e.yml` mit publishtem Port `8080` — **ohne** die Compose-Datei zu verändern. Stoppe mit `Ctrl+C`. Playwright-MCP zeigt dann auf `http://localhost:8080`.

### Ohne @playwright/mcp

1. Browser starten, Anwendung manuell aufrufen.
2. Workflow per Hand klicken.
3. Beschreibung der Beobachtung an Claude zurückgeben.

**Einschränkungen:**

- **Selektoren raten** — beim Schreiben neuer Selenium-Tests muss Claude oft Selektoren raten oder du sie manuell im DevTools-Inspector heraussuchen.
- **Kein Roundtrip** — Claude kann ein Fix vorschlagen, aber nicht selbst überprüfen, ob der Fix die UI tatsächlich repariert hat — du musst nach jedem Patch erneut manuell verifizieren.
- **Screenshots fragmentiert** — keine konsistente Vorher/Nachher-Dokumentation.

!!! note "Verhältnis zu Selenium"
    Playwright-MCP ist **kein Test-Framework-Wechsel**. NFR-008a verlangt weiterhin pytest + Selenium für jede E2E-Anforderung. Playwright-MCP hilft nur Claude beim **Diagnostizieren** und **Vorbereiten** dieser Tests.

---

## context7

### Mehrwert

Liefert **tagesaktuelle, versionsspezifische Doku-Snippets** für Bibliotheken im Stack — verhindert Code, der gegen veraltete oder halluzinierte APIs schreibt.

Konkrete Beispiele aus dem Kamerplanter-Stack, wo das den Unterschied macht:

| Problem ohne context7 | Lösung mit context7 |
|------------------------|----------------------|
| MUI 7: `<Grid item xs={12}>` statt `<Grid size={{ xs: 12 }}>` (Breaking Change in v7) | Aktuelles Beispiel aus MUI-7-Doku wird gezogen |
| React 19: Falsche `use()`-Hook-Signatur | Live-Beispiel aus React-19-Doku |
| Pydantic v2: `@validator` statt `@field_validator` | Korrekte Pydantic-2-Annotation |
| FastAPI ≥ 0.115: Veraltete Lifespan-Pattern | Aktuelle `lifespan`-Context-Manager-Form |
| Authlib statt python-jose (siehe Stack-Entscheidung) | Authlib-spezifische JWT-Code-Beispiele |

### Nutzung

Implizit — Claude greift selbständig zu, wenn er eine Bibliotheks-API verwendet. Du kannst es explizit anfordern: „Nutze context7 für die korrekte MUI-7-Grid-Syntax."

### Ohne context7

1. Manuelle Recherche in offizieller Doku.
2. Trial-and-Error mit Linter/Compiler-Feedback.
3. Stack Overflow oder GitHub-Issues durchsuchen.

**Einschränkungen:**

- **Halluzinations­risiko** — LLMs erzeugen plausibel aussehende, aber faktisch falsche API-Aufrufe, besonders bei kürzlich veröffentlichten Versionen oder Migrationen (MUI 5 → 7, React 18 → 19).
- **Veralteter Trainings­stand** — der LLM-Trainings­stand ist statisch; context7 hängt am Live-Doku-Stand.
- **Iterations­kosten** — jeder „funktioniert nicht, versuch nochmal"-Roundtrip kostet Zeit und Tokens.

---

## kubernetes-mcp-server

### Mehrwert

Claude erhält **read-only-Zugriff auf den lokalen Kind-Cluster** — Pod-Status, Logs, Describe, Events. Der Skaffold-Workflow von Kamerplanter (siehe [Lokales Setup](local-setup.md)) deployt Backend, Frontend, ArangoDB, Valkey und HA-Integration in `default` — beim Debuggen wird der Cluster-State zur Live-Datenquelle für Claude.

| Aufgabe | Mit `kubernetes` | Ohne |
|---------|--------------------|------|
| Backend-Crash-Loop diagnostizieren | Pod-Status + letzte 100 Log-Zeilen werden direkt geholt | `kubectl logs ...` per Bash, manuell scrollen |
| InitContainer-Probleme bei HA-Integration | Pod-Describe zeigt InitContainer-Status sofort | Manuelles `kubectl describe pod ...` |
| Service nicht erreichbar | Endpoint-Liste + Service-Status auf einen Blick | Mehrere `kubectl get`-Aufrufe |
| ArangoDB-PVC-Status prüfen | PVC + Pod-Mount-State in einem Schritt | Mehrere kubectl-Kommandos kombinieren |

### Nutzung

In Claude Code: „Schau im Cluster, warum der Backend-Pod nicht hochkommt" oder „Zeig mir die letzten 50 Log-Zeilen vom Celery-Worker".

Voraussetzung — funktionierender `kubectl`-Kontext:

```bash
kubectl config current-context     # erwartet: kind-kamerplanter o.ä.
kubectl get pods -n default        # muss Backend/Frontend/ArangoDB zeigen
```

!!! danger "Read-Only ist Pflicht"
    Der Server läuft bewusst mit `--read-only`. Die im [`CLAUDE.md`](https://github.com/nolte/kamerplanter/blob/main/CLAUDE.md) dokumentierte Regel **„`kubectl delete pod` verboten für Home-Assistant — `kill 1` verwenden"** wird so strukturell abgesichert. Schreib-Operationen (`apply`, `delete`, `exec`) bleiben sichtbar in `Bash`-Aufrufen mit explizitem Berechtigungs-Prompt.

!!! warning "Skaffold bleibt das einzige Deploy-Tool"
    `kubernetes-mcp-server` ist **kein** Deploy-Werkzeug. Image-Builds und Rollouts laufen weiter ausschließlich über Skaffold (siehe [Lokales Setup](local-setup.md)). Der MCP-Server liest nur — er ändert nichts am Cluster.

### Ohne kubernetes-mcp-server

1. Bash-Kommandos `kubectl get pods`, `kubectl logs`, `kubectl describe` manuell aufrufen.
2. Output an Claude zurückspielen (Copy-Paste oder erneute Bash-Ausführung).

**Einschränkungen:**

- **Mehrere Roundtrips** — Pod-Name finden, dann Logs holen, dann describe — drei separate Bash-Aufrufe statt einem MCP-Call.
- **Kein State-Snapshot** — bei intermittierenden Problemen (Crash-Loop) musst du mehrfach manuell pollen.
- **Kein automatisches Cross-Reference** — Claude muss explizit nach jedem Stück Information fragen, statt parallel mehrere Ressourcen abzugleichen.

---

## Typische Workflows

### Workflow 1: Frontend-Crash diagnostizieren

```
1. Du:    "Schau in den Browser, da gab es einen Absturz"
2. Claude → chrome-devtools: liest Console, holt Stack-Trace
3. Claude → Read: liest die im Trace genannte Datei + Zeile
4. Claude → context7: prüft, ob die verwendete API noch aktuell ist
5. Claude → Edit: Fix
6. Claude → playwright: navigiert zur Seite, verifiziert dass Crash weg ist
7. Du:    Bestätigst und committest
```

**Ohne MCP:** Schritte 2, 4 und 6 erfordern manuelle Aktionen von dir.

### Workflow 2: Neuen Selenium-Test schreiben

```
1. Du:    "Erstelle einen E2E-Test für die neue Phasen-Detail-Seite"
2. Claude → playwright: öffnet Seite, klickt durch den Happy-Path
3. Claude → playwright: identifiziert stabile data-testid-Selektoren
4. Claude → Read: schaut PageObject-Konventionen aus NFR-008a an
5. Claude → Write: erstellt PageObject + pytest-Datei
6. Du:    docker compose -f docker-compose.e2e.yml up e2e-tests
7. Selenium-Test läuft im Compose-Stack — unverändert wie immer
```

**Ohne MCP:** Schritt 2 und 3 muss du manuell durchführen und die Selektoren an Claude übergeben.

### Workflow 3: Bibliotheks-Migration (z. B. MUI 7)

```
1. Du:    "Migriere PhaseDefinitionDetailPage auf die neue Grid-API"
2. Claude → context7: holt aktuelle MUI-7-Grid-Doku
3. Claude → Read: liest Bestandscode
4. Claude → Edit: passt Syntax an
5. Claude → Bash: npm run typecheck && npm run lint
6. Claude → playwright: prüft visuell, dass das Layout intakt ist
```

**Ohne MCP:** Schritt 2 entfällt — Claude rät die neue API mit ~50% Wahrscheinlichkeit korrekt; Schritt 6 wird durch manuellen Klick ersetzt.

---

## Setup-Details

### Was bereits konfiguriert ist

`.mcp.json` (im Repo eingecheckt):

```json
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

### Voraussetzungen

| Tool | Versionsanforderung | Hinweis |
|------|---------------------|---------|
| Node.js | ≥ 20 | Bereits durch Frontend-Toolchain erfüllt |
| `npx` | mit Node.js mitgeliefert | — |
| Chrome / Chromium | aktuell | Für `chrome-devtools-mcp` |
| Internetverbindung | — | Für `context7` und initialen `npx`-Download |

### Erstmaliger Aufruf

Beim ersten Start jedes MCP-Servers lädt `npx` das Paket (10–30 s) und Claude Code fragt einmalig nach Berechtigung. Bestätige mit `Allow always` für regelmäßige Nutzung.

`@playwright/mcp` lädt zusätzlich beim ersten Lauf eine Chromium-Binary (~200 MB) nach `~/.cache/ms-playwright/`.

### Status prüfen

In Claude Code:

```
/mcp
```

Listet aktive Server und ihren Verbindungs­status.

---

## Optionale Erweiterungen

Die folgenden Server sind in [DEVTOOL-001 §4.5–4.9](https://github.com/nolte/kamerplanter/blob/main/spec/dev-tooling/MCP-SERVERS.md) dokumentiert und können bei Bedarf in `~/.claude.json` (Benutzer-Scope, **nicht** ins Repo committen wegen Tokens) ergänzt werden:

| Server | Wann sinnvoll |
|--------|----------------|
| `github-mcp-server` | PR-/Issue-/Workflow-Management ohne `gh`-CLI-Roundtrip |
| `postgres-mcp` | Ad-hoc-Queries gegen TimescaleDB (sobald REQ-005 implementiert) |
| `sentry-mcp` | Frontend-/Backend-Fehler aus Sentry direkt holen (REQ-025-konform) |

---

## Sicherheits- und Datenschutz-Hinweise

| Risiko | Maßnahme |
|--------|----------|
| Geheimnisse in `.mcp.json` | **Verboten** — Tokens leben in `~/.claude.json` |
| Persönliches Browser-Profil | Immer `--user-data-dir=/tmp/chrome-debug` (oder ähnlich isoliert) |
| Schreibzugriff auf Cluster | `kubernetes-mcp-server` nur mit `--read-only` |
| Personenbezogene Produktivdaten | Niemals an externe MCP-Server (context7, sentry-mcp) leaken — DSGVO/REQ-025 gilt |
| `npx`-Supply-Chain | `@latest` ist bequem, bei stabilen Setups auf konkrete Version pinnen |

---

## Wann auf MCP-Werkzeuge verzichten?

Auch ohne MCP-Erweiterungen ist Kamerplanter-Entwicklung uneingeschränkt möglich. Die manuelle Variante reicht völlig aus, wenn:

- Du **nur Backend-Code** schreibst, der über `pytest` und Pod-Logs validiert wird.
- Du **kurze, isolierte Änderungen** machst, deren Verifikation in einer Iteration erledigt ist.
- Die **Aufgabe spezifikations­getrieben** ist (REQ-/NFR-Implementierung) und kein Live-Browser-Feedback erfordert.
- Du in einer **eingeschränkten Umgebung** arbeitest (CI-Container, Air-Gapped-Setup).

In allen anderen Fällen — insbesondere bei iterativen UI-Arbeiten, Bibliotheks-Migrationen oder schwer reproduzier­baren Frontend-Bugs — beschleunigt der Minimal-Stack (chrome-devtools + playwright + context7) den Entwicklungs-Loop spürbar.

---

## Weiterführende Referenzen

- Spezifikation: [`spec/dev-tooling/MCP-SERVERS.md`](https://github.com/nolte/kamerplanter/blob/main/spec/dev-tooling/MCP-SERVERS.md) (DEVTOOL-001)
- Test-Strategie: [`spec/nfr/NFR-008_Teststrategie-Testprotokoll.md`](https://github.com/nolte/kamerplanter/blob/main/spec/nfr/NFR-008_Teststrategie-Testprotokoll.md)
- E2E-Konventionen: [`spec/nfr/NFR-008a_E2E-Selenium-Teststandard.md`](https://github.com/nolte/kamerplanter/blob/main/spec/nfr/NFR-008a_E2E-Selenium-Teststandard.md)
- Lokales Setup: [Lokales Setup](local-setup.md)
- Debugging-Übersicht: [Debugging](debugging.md)
- MCP-Standard: <https://modelcontextprotocol.io/>
