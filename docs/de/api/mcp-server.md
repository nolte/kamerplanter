# MCP-Server (Model Context Protocol)

!!! note "Teilweise verfügbar"
    Das MCP-Framework, die Authentifizierung, das Berechtigungsmodell und ein erster Kern-Werkzeugsatz sind implementiert und aktiv nutzbar. Der vollständige, in der Spezifikation vorgesehene Werkzeugkatalog (rund 30 Werkzeuge, u. a. Setup-Makros, Massen-Anlage von Pflanzen, IPM- und Ernte-Schreibwerkzeuge, die Wissensbasis-Brücke) sowie ein eigenständiger MCP-Prozess mit eigenem Helm-Chart sind noch nicht umgesetzt — der Server läuft heute **im Backend-Prozess mit** (interne Referenz: REQ-033). Die betroffenen Abschnitte sind unten einzeln gekennzeichnet.

Der MCP-Server macht ausgewählte Kamerplanter-Funktionen für externe LLM-Clients (z. B. Claude Desktop, Claude Code, eigene Agenten) nutzbar — über das offene [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), ein Protokoll, mit dem Sprachmodelle strukturierte "Werkzeuge" (Tools) eines Systems aufrufen können. So kann ein LLM-Client zum Beispiel direkt fragen "Welche Pflanzen muss ich heute gießen?" und bekommt eine strukturierte Antwort aus deinen echten Daten — ohne dass du dafür eine eigene App öffnen musst.

---

## Was ist der MCP-Server?

Anders als die generische REST-API spiegelt der MCP-Server **keine** 1:1-CRUD-Endpunkte, sondern stellt eine kuratierte, semantisch hochstufige Werkzeugpalette bereit: Ein Werkzeug wie `get_due_care_tasks` kapselt einen kompletten Anwendungsfall und liefert kompaktes, LLM-freundliches JSON zurück — statt dass das LLM mehrere REST-Aufrufe verketten müsste.

Der MCP-Server ist eine **ergänzende, rein maschinelle Schnittstelle** für externe Clients — er ersetzt nicht den in die Anwendung eingebauten [KI-Assistenten](../user-guide/ai-assistant.md), der Kamerplanter-Nutzer:innen direkt in der App bei Wissensfragen und Chat unterstützt. Beide Funktionen sind komplementär: Der KI-Assistent ist *intern* für App-Nutzer:innen gedacht, der MCP-Server ist die *externe* Schnittstelle, über die fremde LLM-Clients Kamerplanter als Werkzeug benutzen.

## Aktivieren

Der MCP-Server ist standardmäßig deaktiviert. Solange `MCP_SERVER_ENABLED` nicht auf `true` gesetzt ist, antworten **alle** `/mcp/*`-Endpunkte mit `404 Not Found` — die Schnittstelle existiert dann faktisch nicht, analog zum Freischalt-Mechanismus des KI-Assistenten. Details zur Umgebungsvariable siehe [Umgebungsvariablen — MCP-Server](../reference/environment-variables.md#mcp-server).

## Transport & Endpunkte

Der MCP-Server läuft im Backend-Prozess mit und stellt seine Werkzeuge über drei Endpunkte unter `/api/v1/mcp/` bereit:

| Methode | Pfad | Zweck |
|---------|------|-------|
| `GET` | `/mcp/tools` | REST-freundliche Werkzeug-Übersicht — zeigt nur die Werkzeuge, die die Rolle des aufrufenden Service Accounts freischaltet |
| `POST` | `/mcp/tools/{tool_name}` | REST-freundlicher Werkzeug-Aufruf mit JSON-Body als Argumenten |
| `POST` | `/mcp/rpc` | MCP JSON-RPC 2.0 — `initialize`, `tools/list`, `tools/call`, `ping` — für protokoll-native MCP-Clients |
| `GET` | `/mcp/sse` | SSE-Handshake für den HTTP+SSE-Transport: liefert ein `endpoint`-Event, das auf `/mcp/rpc` verweist |

!!! info "Nur über API / Betreiber-Konfiguration: Transport"
    Ein eigenständiger `stdio`-Transport (Server wird lokal vom Client gestartet, wie es für Claude-Desktop-Konfigurationen typisch ist) ist in der Spezifikation vorgesehen, aber noch nicht umgesetzt — aktuell ist ausschließlich HTTP(+SSE) verfügbar. Ein MCP-Client verbindet sich über die volle Backend-URL, z. B. `https://api.kamerplanter.example.com/api/v1/mcp/rpc`.

## Authentifizierung: nur Service Accounts

Der MCP-Server akzeptiert **ausschließlich** API-Keys von Service Accounts (`account_type: "service"`) — niemals ein persönliches Nutzerkonto und niemals ein JWT-Access-Token. Der Key wird als `X-API-Key`-Header oder als `Authorization: Bearer kp_...` gesendet und trägt immer das Präfix `kp_` (siehe auch [Authentifizierung — API-Keys (M2M-Integration)](authentication.md#api-keys-m2m-integration)).

```http
POST /api/v1/mcp/tools/get_due_care_tasks
X-API-Key: kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{"urgency": "actionable"}
```

Ein separater Endpunkt löst einen rohen Key in seinen Kontext auf — nützlich für einen zukünftigen eigenständigen MCP-Prozess (siehe Statushinweis oben), der den Key nicht selbst validieren kann:

```http
POST /api/v1/auth/service-accounts/validate
Content-Type: application/json

{"api_key": "kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
```

**Antwort (200):**

```json
{
  "service_account_key": "sa-abc123",
  "display_name": "Diagnose-Bot",
  "tenant_key": "t-home",
  "tenant_slug": "home",
  "role": "viewer",
  "mcp_permissions": ["mcp.read"]
}
```

Ein ungültiger, widerrufener oder nicht-service Key liefert in beiden Fällen denselben generischen `401 Unauthorized` — die API verrät nie, ob überhaupt ein gültiger Key mit anderen Eigenschaften existiert.

### Service-Account-Key beziehen (aktueller Stand)

!!! warning "Noch nicht implementiert"
    Die vollständige, selbstständige Service-Account-Verwaltung (Erstellen, Rotieren, Deaktivieren über die API — siehe [Service Accounts & API-Keys](service-accounts.md)) ist spezifiziert, aber noch nicht umgesetzt. Aktuell ist das Anlegen eines Nutzerkontos mit `account_type: "service"` ein **Betreiber-Schritt** außerhalb der öffentlichen API, kein Selbstbedienungsfluss (interne Referenz: REQ-023). Die folgenden Punkte beschreiben den heutigen Stand, nicht das künftige Selbstbedienungserlebnis.

Damit ein MCP-Client heute einen funktionierenden Key bekommt, sind folgende Zutaten nötig:

1. Ein Nutzerkonto mit `account_type: "service"` (kein Passwort, kein interaktiver Login) — vom Betreiber der Instanz angelegt.
2. Eine Mandanten-Mitgliedschaft dieses Kontos mit genau der Rolle (`viewer`/`grower`/`admin`), die dem gewünschten [Berechtigungsniveau](#berechtigungsmodell-mcpread-mcpwrite-mcpsetup) entspricht — ein Service Account ist immer an **genau einen** Mandanten gebunden.
3. Ein API-Key für dieses Konto, technisch derselbe Mechanismus wie unter [Service Accounts & API-Keys — API-Key verwenden](service-accounts.md#api-key-verwenden) beschrieben — da ein Service Account jedoch nie interaktiv angemeldet ist, kann er den Key nicht selbst über den `/auth/api-keys`-Endpunkt anfordern; auch dieser Schritt läuft heute über den Betreiber.

## Berechtigungsmodell: `mcp.read` / `mcp.write` / `mcp.setup`

Jedes Werkzeug verlangt genau eine von drei MCP-Berechtigungen. Diese sind nicht separat vergebbar, sondern direkt an die Mandanten-Rolle des Service Accounts gekoppelt — dieselbe Rolle, die auch für menschliche Mitglieder gilt ([Mandanten & Gärten](../user-guide/tenants.md)):

| Mandanten-Rolle | `mcp.read` | `mcp.write` | `mcp.setup` | Typischer Einsatz |
|-----------------|:----------:|:-----------:|:-----------:|--------------------|
| **viewer** | ✓ | ✗ | ✗ | Nur-Lese-Diagnose-Bot |
| **grower** | ✓ | ✓ | ✗ | Tagesbetrieb (Pflege quittieren, Pflanzen verschieben/archivieren) |
| **admin** | ✓ | ✓ | ✓ | Einmaliges Onboarding, Standort-Anlage |

Ein Aufruf ohne die erforderliche Berechtigung wird mit dem Fehlercode `permission.denied` abgelehnt und im Audit-Log als `status: "denied"` festgehalten (siehe [Audit-Trail & Datenschutz](#audit-trail-und-datenschutz)). `mcp.setup` ist absichtlich die restriktivste Klasse: Sie steuert Standort-Anlage — Zugriffe, die eine ganze Pflanzendaten-Hierarchie betreffen können — und ist deshalb ausschließlich der Rolle `admin` vorbehalten.

## Werkzeug-Katalog (aktueller Stand)

!!! note "Teilweise verfügbar: Werkzeug-Umfang"
    Die Spezifikation sieht rund 30 Werkzeuge vor (u. a. Setup-Makros für Wohnung/Growbox/Freiland-Garten, Massen-Anlage von Pflanzen, IPM-Inspektionen, Ernte-Erfassung, Düngeereignisse und eine Brücke zur RAG-Wissensbasis). Umgesetzt ist bislang der folgende Kern-Werkzeugsatz — Erweiterung ist ein dokumentierter Folgeschritt.

### Lese-Werkzeuge (`mcp.read`)

| Werkzeug | Zweck |
|----------|-------|
| `list_species` | Pflanzenarten-Katalog auflisten (paginiert) |
| `get_species_info` | Stammdaten zu einer Art inkl. Mischkultur-Hinweisen (Companion Planting) |
| `list_planting_runs` | Pflanzdurchläufe des Mandanten auflisten, optional nach Status gefiltert |
| `list_tasks` | Aufgaben des Mandanten auflisten, optional nach Status gefiltert |
| `get_due_care_tasks` | Heute fällige/überfällige Pflegeerinnerungen, gruppiert nach Dringlichkeit |
| `get_harvest_readiness` | Erntebereitschafts-Überblick über alle aktiven Pflanzen |
| `get_mcp_activity` | Eigener MCP-Aufrufverlauf des Service Accounts (Selbstauskunft, siehe unten) |

### Schreib-Werkzeuge (`mcp.write`)

| Werkzeug | Zweck |
|----------|-------|
| `confirm_care_task` | Pflegeerinnerung für eine Pflanze quittieren ("ich habe gegossen") |
| `archive_plant` | Pflanze als entsorgt/abgegeben/gestorben kennzeichnen — **kein** Hard-Delete, Verlauf bleibt erhalten |
| `set_plant_location` | Pflanze zu einem anderen Standort/Bereich/Slot verschieben |

### Setup-Werkzeug (`mcp.setup`)

| Werkzeug | Zweck |
|----------|-------|
| `create_site` | Standort-Wurzel anlegen (Wohnung, Garten, Balkon, Gewächshaus, Fensterbank, Growzelt) |

Jedes Werkzeug prüft die referenzierten Schlüssel (Pflanze, Standort, Bereich, Slot) grundsätzlich gegen den Mandanten des aufrufenden Service Accounts. Ein Fremdschlüssel aus einem anderen Mandanten liefert konsequent `not_found` — niemals `permission.denied` — damit kein Werkzeug die Existenz fremder Ressourcen verrät.

## Antwortformat

Jedes Werkzeug liefert ein kompaktes, LLM-freundliches JSON mit drei Pflichtfeldern:

```json
{
  "summary": "3 Pflanzen müssen heute gegossen werden.",
  "data": { "count": 3, "items": [ /* ... */ ] },
  "links": [
    { "type": "ui", "url": "/t/home/care" },
    { "type": "api", "url": "/api/v1/t/home/care/dashboard" }
  ]
}
```

`summary` ist eine Ein-Satz-Zusammenfassung für das LLM, `data` das strukturierte Ergebnis, `links` verweisen den Endnutzer auf die passende Stelle in der Oberfläche bzw. der REST-API.

## Dry-Run und Idempotenz

Jedes Schreibwerkzeug akzeptiert zwei zusätzliche, optionale Argumente:

- **`dry_run: bool`** (Standard `false`) — bei `true` wird nur der geplante Effekt zurückgeliefert, ohne dass irgendetwas gespeichert wird. Damit kann ein LLM-Client eine geplante Aktion erst dem Menschen zur Bestätigung vorlegen, bevor er sie tatsächlich ausführt.
- **`idempotency_key: str`** (optional) — identische Keys desselben Service Accounts, Mandanten und Werkzeugs liefern innerhalb von 24 Stunden das ursprüngliche Ergebnis erneut, statt eine zweite Ressource anzulegen. Das schützt vor Doppel-Aktionen bei LLM-Retries (z. B. wenn eine Netzwerkantwort verloren geht).

Eine Wiederholungs-Antwort ist an `"idempotent_replay": true` erkennbar:

```json
{
  "summary": "Confirmed 'watering' for plant 'p-42'.",
  "data": { "plant_key": "p-42", "reminder_type": "watering" },
  "dry_run": false,
  "idempotency_key": "confirm-2026-07-12-001",
  "idempotent_replay": true,
  "links": [{ "type": "ui", "url": "/t/home/care" }]
}
```

Idempotenz-Datensätze werden automatisch nach 24 Stunden gelöscht.

## Audit-Trail und Datenschutz

Jeder Werkzeug-Aufruf wird protokolliert — unabhängig davon, ob er erfolgreich war, wegen fehlender Berechtigung abgelehnt wurde oder ein `dry_run` war. Der Eintrag enthält Service Account, Mandant, Werkzeugname, einen **SHA-256-Hash der Argumente** (niemals Klartext), Antwortgröße, Dauer und Status — nie den API-Key selbst und keine personenbezogenen Freitextinhalte wie Tagebucheinträge.

Ein Service Account kann seinen eigenen Aufrufverlauf über das Werkzeug `get_mcp_activity` oder direkt per REST einsehen:

```http
GET /api/v1/privacy/mcp-activity
Authorization: Bearer <access_token>
```

Die Antwort enthält die letzten Einträge (Werkzeugname, Status, Antwortgröße, Dauer, Fehlerklasse, Zeitstempel) — keine Argumente im Klartext. Audit-Einträge werden nach 90 Tagen automatisch entfernt (siehe [Datenschutz & DSGVO](../user-guide/privacy.md)).

## Häufige Fragen

??? question "Kann ich mich mit meinem persönlichen Account am MCP-Server anmelden?"
    Nein. Der MCP-Server akzeptiert ausschließlich Service-Account-API-Keys. Ein Versuch mit einem persönlichen Konto (`account_type: "user"`) wird abgelehnt.

??? question "Kann ein MCP-Client auf mehrere Mandanten gleichzeitig zugreifen?"
    Nein. Ein Service Account ist immer an genau einen Mandanten gebunden. Für den Zugriff auf mehrere Gärten sind mehrere Service Accounts mit jeweils eigenem Key nötig.

??? question "Was passiert, wenn ich versehentlich einen `idempotency_key` wiederverwende, den ich schon für ein anderes Werkzeug genutzt habe?"
    Nichts Falsches — die Wiederholungserkennung ist zusätzlich nach Werkzeugname und Mandant gescopet. Derselbe Schlüssel bei einem anderen Werkzeug oder in einem anderen Mandanten löst also keine Wiederholung aus.

??? question "Läuft der MCP-Server als eigener Prozess, den ich separat skalieren kann?"
    Aktuell nicht — der MCP-Server läuft im selben Backend-Prozess mit und teilt sich dessen Ressourcen. Ein eigenständiger Prozess mit eigenem Helm-Chart ist als Erweiterung vorgesehen (siehe Statushinweis oben).

## Siehe auch

- [Service Accounts & API-Keys](service-accounts.md)
- [Authentifizierung](authentication.md)
- [KI-Assistent — Benutzerhandbuch](../user-guide/ai-assistant.md)
- [Umgebungsvariablen — MCP-Server](../reference/environment-variables.md#mcp-server)
- [Datenschutz & DSGVO](../user-guide/privacy.md)
- [Fehlerbehandlung](error-handling.md)
- [MCP-Werkzeuge für die Entwicklung (nicht zu verwechseln)](../development/mcp-tools.md)
