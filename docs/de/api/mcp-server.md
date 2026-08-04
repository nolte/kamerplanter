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

Der MCP-Server läuft im Backend-Prozess mit und stellt seine Werkzeuge unter `/api/v1/mcp/` bereit:

| Methode | Pfad | Zweck |
|---------|------|-------|
| `GET` | `/mcp/tools` | REST-freundliche Werkzeug-Übersicht — zeigt die Werkzeuge, die die Rollen des Aufrufers freischalten, samt der Gärten, die der Key abdeckt |
| `POST` | `/mcp/tools/{tool_name}` | REST-freundlicher Werkzeug-Aufruf mit JSON-Body als Argumenten |
| `POST` | `/mcp` | **Der MCP-Endpunkt**: JSON-RPC 2.0 über Streamable HTTP — `initialize`, `tools/list`, `tools/call`, `ping` |
| `GET` | `/mcp` | `405` — dieser Server sendet keine server-initiierten Nachrichten; der Transport erlaubt diese Antwort ausdrücklich |
| `DELETE` | `/mcp` | Beendet die Sitzung aus dem `Mcp-Session-Id`-Header |
| `POST` | `/mcp/rpc` | Beibehaltener Alias von `POST /mcp` (veraltet) |

!!! info "Nur über API / Betreiber-Konfiguration: Transport"
    Ein eigenständiger `stdio`-Transport (Server wird lokal vom Client gestartet, wie es für Claude-Desktop-Konfigurationen typisch ist) ist in der Spezifikation vorgesehen, aber noch nicht umgesetzt — aktuell ist ausschließlich Streamable HTTP verfügbar. Ein MCP-Client verbindet sich über die volle Backend-URL, z. B. `https://api.kamerplanter.example.com/api/v1/mcp`.

## Authentifizierung: dein eigener API-Key

Der MCP-Server akzeptiert **API-Keys** — deinen persönlichen ebenso wie den eines Service Accounts. Niemals akzeptiert werden ein JWT-Access-Token oder eine interaktive Sitzung. Der Key wird als `X-API-Key`-Header oder als `Authorization: Bearer kp_...` gesendet und trägt immer das Präfix `kp_` (siehe auch [Authentifizierung — API-Keys (M2M-Integration)](authentication.md#api-keys-m2m-integration)).

Deinen persönlichen Key erstellst du dir selbst über `POST /api/v1/auth/api-keys`; du kannst ihn jederzeit einzeln widerrufen, ohne dein Passwort zu ändern.

!!! warning "Ein API-Key ist ein Dauerschlüssel"
    Anders als ein Login-Token läuft ein API-Key nicht nach Minuten ab — genau deshalb eignet er sich für einen dauerhaft laufenden MCP-Client. Behandle ihn wie ein Passwort: Wer ihn hat, kann alles, was du in deinen Gärten kannst. Lege für jeden Client einen eigenen Key an, dann kannst du einzelne gezielt widerrufen.

### Du siehst ausschließlich deine eigenen Daten

Ein Key gewährt genau die Gärten (Mandanten), in denen sein Konto **aktives Mitglied** ist — aufgelöst über dieselbe Quelle, auf die auch die normale API zugreift. Über MCP ist dadurch nichts erreichbar, was du nicht auch in der Weboberfläche siehst. Ein Garten, in dem du nicht Mitglied bist, verhält sich exakt so, als gäbe es ihn nicht (`not_found`) — die Schnittstelle verrät also nicht einmal seine Existenz.

Innerhalb eines Gartens gilt die normale Sichtbarkeit: In einem Gemeinschaftsgarten sehen alle Mitglieder dieselben Pflanzen, in der App wie über MCP.

```http
POST /api/v1/mcp/tools/get_due_care_tasks
X-API-Key: kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{"urgency": "actionable", "tenant": "mein-garten"}
```

### Mehrere Gärten: der `tenant`-Parameter

Bist du Mitglied in mehreren Gärten, gilt dein Key für alle. Welcher gemeint ist, entscheidest du pro Aufruf über das Argument `tenant` (den Slug des Gartens). Bei genau einer Mitgliedschaft kannst du es weglassen; bei mehreren ist es Pflicht — der Server rät nicht, sondern fordert dich auf, den Garten zu benennen. Welche Slugs zur Verfügung stehen, verrät dir das Werkzeug `list_tenants`.

Wichtig ist die Reihenfolge dahinter: Der Server bestimmt **erst** den Garten und prüft **danach**, was du dort darfst. Denn deine Rolle kann sich je Garten unterscheiden — im eigenen Garten Admin, im Gemeinschaftsgarten nur Betrachter. Umgekehrt geprüft, hättest du überall die stärkste deiner Rollen.

### Key-Kontext auflösen (M2M)

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
  "tenants": [
    {
      "tenant_key": "t-home",
      "tenant_slug": "home",
      "role": "viewer",
      "mcp_permissions": ["mcp.read"]
    }
  ]
}
```

Dieser Endpunkt ist bewusst auf Service Accounts beschränkt. Ein ungültiger, widerrufener oder persönlicher Key liefert hier denselben generischen `401 Unauthorized` — die API verrät nie, ob überhaupt ein gültiger Key mit anderen Eigenschaften existiert. Für den MCP-Server selbst gilt diese Einschränkung nicht: dort funktioniert dein persönlicher Key.

### Key beziehen

**Als Nutzer:in — Selbstbedienung:** Melde dich an und erstelle dir über `POST /api/v1/auth/api-keys` einen Key. Er gilt sofort für alle deine Gärten mit genau den Rollen, die du dort hast. Mit `tenant_scope` kannst du ihn beim Anlegen auf einen einzigen Garten begrenzen, wenn ein Client nur dort arbeiten soll.

**Als Service Account — Betreiber-Schritt:**

!!! warning "Noch nicht implementiert"
    Die vollständige, selbstständige Service-Account-Verwaltung (Erstellen, Rotieren, Deaktivieren über die API — siehe [Service Accounts & API-Keys](service-accounts.md)) ist spezifiziert, aber noch nicht umgesetzt. Aktuell ist das Anlegen eines Nutzerkontos mit `account_type: "service"` ein **Betreiber-Schritt** außerhalb der öffentlichen API, kein Selbstbedienungsfluss (interne Referenz: REQ-023).

Damit ein maschineller MCP-Client heute einen funktionierenden Key bekommt, sind folgende Zutaten nötig:

1. Ein Nutzerkonto mit `account_type: "service"` (kein Passwort, kein interaktiver Login) — vom Betreiber der Instanz angelegt.
2. Eine Mandanten-Mitgliedschaft dieses Kontos mit genau der Rolle (`viewer`/`grower`/`admin`), die dem gewünschten [Berechtigungsniveau](#berechtigungsmodell-mcpread-mcpwrite-mcpsetup) entspricht.
3. Ein API-Key für dieses Konto, technisch derselbe Mechanismus wie unter [Service Accounts & API-Keys — API-Key verwenden](service-accounts.md#api-key-verwenden) beschrieben — da ein Service Account jedoch nie interaktiv angemeldet ist, kann er den Key nicht selbst über den `/auth/api-keys`-Endpunkt anfordern; auch dieser Schritt läuft heute über den Betreiber.

## Client einrichten (Claude Code)

Claude Code liest MCP-Server aus einer `.mcp.json` im Projektverzeichnis (oder aus deiner globalen Konfiguration). Trage den Kamerplanter-Server als HTTP-Server ein:

```json
{
  "mcpServers": {
    "kamerplanter": {
      "type": "http",
      "url": "https://kamerplanter.example.com/api/v1/mcp",
      "headers": {
        "X-API-Key": "kp_dein_persoenlicher_api_key"
      }
    }
  }
}
```

Für eine lokale Entwicklungsumgebung ist die URL `http://localhost:8000/api/v1/mcp`.

!!! danger "Der Key steht im Klartext in der Datei"
    `.mcp.json` gehört **nicht** ins Git-Repository, wenn ein echter Key darin steht — trage sie in `.gitignore` ein oder nutze die globale Claude-Code-Konfiguration außerhalb des Projekts. Wer die Datei liest, kann alles, was du in deinen Gärten kannst. Widerrufen kannst du einen Key jederzeit einzeln.

### Vorher prüfen, ob die Verbindung steht

Bevor du den Eintrag hinzufügst, lohnt ein direkter Test — er zeigt sofort, ob URL und Key stimmen:

```bash
# 1. Handschlag: Antwortet der Server als MCP-Server?
curl -sS -X POST https://kamerplanter.example.com/api/v1/mcp \
  -H "X-API-Key: kp_dein_persoenlicher_api_key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}'

# 2. Welche Werkzeuge schaltet mein Key frei?
curl -sS -X POST https://kamerplanter.example.com/api/v1/mcp \
  -H "X-API-Key: kp_dein_persoenlicher_api_key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# 3. Ein echter Aufruf: Welche Gärten deckt der Key ab?
curl -sS -X POST https://kamerplanter.example.com/api/v1/mcp \
  -H "X-API-Key: kp_dein_persoenlicher_api_key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_tenants","arguments":{}}}'
```

Kommt bei Schritt 1 ein `404`, ist der MCP-Server auf dieser Instanz nicht freigeschaltet (`MCP_SERVER_ENABLED`). Ein `401` bedeutet, dass der Key ungültig, widerrufen oder abgelaufen ist.

Danach kannst du im Dialog direkt fragen: *"Welche Pflanzen muss ich heute gießen?"* — Claude ruft `get_due_care_tasks` selbst auf. Deckt dein Key mehrere Gärten ab, nenne den gewünschten mit (*"…in meinem Balkongarten"*), damit das Modell den `tenant`-Parameter füllen kann.

!!! info "Transport: Streamable HTTP"
    Der Server implementiert den **Streamable-HTTP-Transport** (Protokollrevisionen `2025-06-18`, `2025-03-26` und `2024-11-05`). Beim `initialize` handelt er die Revision mit deinem Client aus und vergibt eine `Mcp-Session-Id`, die der Client danach mitsendet; eine abgelaufene Sitzung beantwortet er mit `404`, worauf der Client neu initialisiert. Antworten kommen immer als `application/json` — vom Transport ausdrücklich erlaubt. Einen server-initiierten Stream bietet er nicht: `GET` auf den Endpunkt antwortet mit `405`. Das ist die vom Transport vorgesehene Antwort und bedeutet, dass Fortschrittsmeldungen bei langen Operationen derzeit nicht möglich sind.

!!! warning "Noch nicht implementiert: Claude Desktop"
    Claude Desktop startet einen MCP-Server als lokalen Unterprozess und spricht ihn über `stdio` an — es kann eine HTTP-URL nicht direkt einbinden. Der dafür nötige schlanke Brücken-Client ist spezifiziert, aber noch nicht umgesetzt (interne Referenz: REQ-033). Die obige Konfiguration gilt daher für Claude Code und andere Clients mit HTTP-Transport.

## Berechtigungsmodell: `mcp.read` / `mcp.write` / `mcp.setup`

Jedes Werkzeug verlangt genau eine von drei MCP-Berechtigungen. Diese sind nicht separat vergebbar, sondern an die Rolle gekoppelt, die dein Konto **in dem gerade angesprochenen Garten** hat — dieselbe Rolle, die auch für menschliche Mitglieder gilt ([Mandanten & Gärten](../user-guide/tenants.md)):

| Mandanten-Rolle | `mcp.read` | `mcp.write` | `mcp.setup` | Typischer Einsatz |
|-----------------|:----------:|:-----------:|:-----------:|--------------------|
| **viewer** | ✓ | ✗ | ✗ | Nur-Lese-Diagnose-Bot |
| **grower** | ✓ | ✓ | ✗ | Tagesbetrieb (Pflege quittieren, Pflanzen verschieben/archivieren) |
| **admin** | ✓ | ✓ | ✓ | Einmaliges Onboarding, Standort-Anlage |

Ein Aufruf ohne die erforderliche Berechtigung wird mit dem Fehlercode `permission.denied` abgelehnt und im Audit-Log als `status: "denied"` festgehalten (siehe [Audit-Trail & Datenschutz](#audit-trail-und-datenschutz)). `mcp.setup` ist absichtlich die restriktivste Klasse: Sie steuert Standort-Anlage — Zugriffe, die eine ganze Pflanzendaten-Hierarchie betreffen können — und ist deshalb ausschließlich der Rolle `admin` vorbehalten.

Weil die Rolle je Garten gilt, kann derselbe Key in deinem eigenen Garten schreiben und im Gemeinschaftsgarten, in dem du nur Betrachter bist, dieselbe Aktion verweigert bekommen. Die Werkzeug-Übersicht (`GET /mcp/tools`) zeigt deshalb alles, was du **irgendwo** darfst; verbindlich ist die Prüfung beim einzelnen Aufruf.

## Werkzeug-Katalog (aktueller Stand)

!!! note "Teilweise verfügbar: Werkzeug-Umfang"
    Die Spezifikation sieht rund 30 Werkzeuge vor (u. a. Setup-Makros für Wohnung/Growbox/Freiland-Garten, Massen-Anlage von Pflanzen, IPM-Inspektionen, Ernte-Erfassung, Düngeereignisse und eine Brücke zur RAG-Wissensbasis). Umgesetzt ist bislang der folgende Kern-Werkzeugsatz — Erweiterung ist ein dokumentierter Folgeschritt.

### Lese-Werkzeuge (`mcp.read`)

| Werkzeug | Zweck |
|----------|-------|
| `list_tenants` | Deine Gärten auflisten, mit deiner Rolle je Garten — liefert die Slugs für den `tenant`-Parameter |
| `list_species` | Pflanzenarten-Katalog auflisten (paginiert) |
| `get_species_info` | Stammdaten zu einer Art inkl. Mischkultur-Hinweisen (Companion Planting) |
| `list_planting_runs` | Pflanzdurchläufe des Mandanten auflisten, optional nach Status gefiltert |
| `list_tasks` | Aufgaben des Mandanten auflisten, optional nach Status gefiltert |
| `get_due_care_tasks` | Heute fällige/überfällige Pflegeerinnerungen, gruppiert nach Dringlichkeit |
| `get_harvest_readiness` | Erntebereitschafts-Überblick über alle aktiven Pflanzen |
| `get_mcp_activity` | Eigener MCP-Aufrufverlauf des Kontos (Selbstauskunft, siehe unten) |

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

Jedes Werkzeug prüft die referenzierten Schlüssel (Pflanze, Standort, Bereich, Slot) grundsätzlich gegen den für diesen Aufruf aufgelösten Mandanten. Ein Fremdschlüssel aus einem anderen Mandanten liefert konsequent `not_found` — niemals `permission.denied` — damit kein Werkzeug die Existenz fremder Ressourcen verrät.

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
- **`idempotency_key: str`** (optional) — identische Keys desselben Kontos, Mandanten und Werkzeugs liefern innerhalb von 24 Stunden das ursprüngliche Ergebnis erneut, statt eine zweite Ressource anzulegen. Das schützt vor Doppel-Aktionen bei LLM-Retries (z. B. wenn eine Netzwerkantwort verloren geht).

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

Jeder Werkzeug-Aufruf wird protokolliert — unabhängig davon, ob er erfolgreich war, wegen fehlender Berechtigung abgelehnt wurde oder ein `dry_run` war. Der Eintrag enthält Konto, Mandant, Werkzeugname, einen **SHA-256-Hash der Argumente** (niemals Klartext), Antwortgröße, Dauer und Status — nie den API-Key selbst und keine personenbezogenen Freitextinhalte wie Tagebucheinträge.

Ein Konto kann seinen eigenen Aufrufverlauf über das Werkzeug `get_mcp_activity` oder direkt per REST einsehen:

```http
GET /api/v1/privacy/mcp-activity
Authorization: Bearer <access_token>
```

Die Antwort enthält die letzten Einträge (Werkzeugname, Status, Antwortgröße, Dauer, Fehlerklasse, Zeitstempel) — keine Argumente im Klartext. Audit-Einträge werden nach 90 Tagen automatisch entfernt (siehe [Datenschutz & DSGVO](../user-guide/privacy.md)).

## Häufige Fragen

??? question "Kann ich mein persönliches Konto am MCP-Server nutzen?"
    Ja — erstelle dir über `POST /api/v1/auth/api-keys` einen API-Key und sende ihn als `X-API-Key`. Nicht verwendbar sind ein JWT-Access-Token oder eine interaktive Sitzung; MCP authentifiziert ausschließlich API-Keys.

??? question "Kann ein MCP-Client auf mehrere Mandanten gleichzeitig zugreifen?"
    Ja, sofern das Konto in mehreren Mitglied ist. Der Key gilt dann für alle, und jeder Aufruf benennt den handelnden Garten über das Argument `tenant`. Wer einen Key auf einen einzigen Garten begrenzen will, setzt beim Anlegen `tenant_scope`.

??? question "Kann ein MCP-Client fremde Gärten sehen?"
    Nein. Ein Key erreicht genau die Gärten, in denen sein Konto aktives Mitglied ist. Jeder andere Garten liefert `not_found` — dieselbe Antwort wie für einen Garten, den es gar nicht gibt. Die Schnittstelle taugt damit nicht dazu, fremde Gärten aufzuspüren.

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
