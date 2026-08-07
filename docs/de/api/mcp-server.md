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

**Über die Oberfläche:** **Kontoeinstellungen → API-Schlüssel → Anlegen.** Der Schlüssel wird **genau einmal** angezeigt — danach ist nur noch sein Hash gespeichert, er lässt sich nicht erneut anzeigen. Kopieren und direkt eintragen. In derselben Tabelle kannst du jeden Schlüssel einzeln widerrufen.

**Über die API:** `POST /api/v1/auth/api-keys` mit `{"label": "claude-code"}`. Der Schlüssel gilt sofort für alle deine Gärten mit genau den Rollen, die du dort hast. Mit `tenant_scope` begrenzt du ihn beim Anlegen auf einen einzigen Garten, wenn ein Client nur dort arbeiten soll.

!!! info "Auch im Light-Modus verfügbar"
    Eine Light-Instanz kennt keine Benutzerkonten — Anmeldung, Sitzungen und Sicherheitseinstellungen fehlen dort bewusst. Die **API-Schlüssel-Verwaltung gibt es trotzdem**, denn sie ist die einzige Anmeldeform, die der MCP-Server akzeptiert. Der Schlüssel gehört dort dem System-Benutzer, der Mitglied des Standard-Gartens ist. Zusätzliche Rechte entstehen dadurch nicht: Wer eine Light-Instanz erreicht, hat ohnehin vollen Zugriff — der Schlüssel macht diesen Zugriff nur von außen nutzbar. Genau deshalb gehört eine Light-Instanz nicht ins offene Internet.

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
    Umgesetzt sind derzeit 56 Werkzeuge — sie decken das Lesen weitgehend ab, dazu die fünf Tagebuch-Analyse-Werkzeuge (siehe [Tagebuch-Analyse: externe Agenten](#tagebuch-analyse-externe-agenten)) und die acht Werkzeuge der Wachstumsphasen-Ebene (siehe [Wachstumsphasen und Lebenszyklus](#wachstumsphasen-und-lebenszyklus)). Beim übrigen **Schreiben** fehlt weiterhin, was die Spezifikation vorsieht: Setup-Makros für Wohnung/Growbox/Freiland-Garten, Massen-Anlage von Pflanzen, Standort- und Bereichsverwaltung sowie das Zurückschreiben einer Ernte (`record_harvest`) und einer angewandten Behandlung (`apply_treatment`). Erweiterung ist ein dokumentierter Folgeschritt.

!!! info "Neu: was ein Analyse-Agent zurückschreiben kann"
    Fünf Werkzeuge sind hinzugekommen, die extern betriebene Analyse-Agenten brauchten. Jedes ist mit dem Lese-Werkzeug gepaart, das sein Ergebnis wiederfindet — ein Schreibvorgang, den anschließend kein Lese-Werkzeug mehr sichtbar macht, gilt hier als Fehler:

    - `record_feeding_event` erfasst **Menge, EC und pH** eines Düngevorgangs samt Tankbezug. Bisher stand im Pflegeprotokoll nur „quittiert" — ein Ja/Nein, aus dem sich Unter- und Überversorgung nicht unterscheiden lassen, obwohl beide gegensätzlich zu korrigieren sind. Sichtbar über `get_plant_diagnostics`.
    - `get_plant_diagnostics` liefert **den Verlauf statt nur des letzten Werts**: EC- und pH-Reihen über einen wählbaren Zeitraum (Zulauf, Nachmessung und Drainage getrennt), Sensor-Momentaufnahme, IPM-Inspektionen, Karenz und jüngste Pflegevorgänge — in einem Aufruf.
    - `create_inspection` legt eine IPM-Inspektion an und behält dabei je Befund die **Sicherheit** und den **betroffenen Pflanzenteil**. Ohne sie blieb die Befallshistorie einer rein per Agent betreuten Pflanze für immer leer. Sichtbar über `get_plant_inspections`.
    - `search_plant_knowledge` durchsucht die Wissensbasis und liefert **zitierfähige Quellenverweise**, damit eine Begründung ihre Quelle benennen kann.
    - `assign_nutrient_plan` bindet einen **vorhandenen** Nährstoffplan an eine Pflanze. Pläne zu *bearbeiten* bleibt bewusst Aufgabe der Oberfläche. Sichtbar über `get_plant_nutrient_plan`.

### Lese-Werkzeuge (`mcp.read`)

| Werkzeug | Zweck |
|----------|-------|
| `list_tenants` | Deine Gärten auflisten, mit deiner Rolle je Garten — liefert die Slugs für den `tenant`-Parameter |
| `list_plants` | Pflanzen auflisten, optional nach Name gefiltert — so wird aus „meine Tomate" der `plant_key`, den die Schreib-Werkzeuge brauchen |
| `get_plant` | Eine Pflanze im Detail: Art (mit aufgelöstem Namen), Phase, Standort, Substrat (mit aufgelöstem Typ und Namen), Pflanz- und Entfernungsdatum |
| `get_plant_care_log` | Pflegehistorie einer Pflanze — mit `reminder_type: "watering"` das Gießprotokoll |
| `get_plant_diagnostics` | Diagnose-Momentaufnahme einer Pflanze in **einem** Aufruf: EC-/pH-**Verlauf** über einen wählbaren Zeitraum (Zulauf, Nachmessung und Drainage getrennt), Sensorwerte am Standort, IPM-Inspektionen, Karenz und jüngste Pflegevorgänge |
| `list_diary_entries` | Tagebuch-Einträge durchsehen, filterbar nach Pflanze, Art, Eintragstyp, Tag, Analyse-Zustand und Zeitraum — neueste zuerst, mit Messwerten, aber ohne Freitext |
| `list_plants_at_location` | Alle Pflanzen an einem Standort, Beet oder Slot |
| `list_nutrient_plans` | Verfügbare Nährstoffpläne — eigene plus globale Vorlagen |
| `get_nutrient_plan` | Ein Plan mit allen Phasen: NPK-Verhältnis, Ziel-EC, Nährstoffe, Wochenfenster |
| `get_plant_nutrient_plan` | Der Plan, der für eine bestimmte Pflanze gilt |
| `get_sowing_calendar` | Aussaat-, Auspflanz- und Erntefenster je Art, verschoben gegen die Frostdaten deines Standorts |
| `list_pests` / `get_pest` | Schädlinge suchen — auch nach Schadbild. Das Detail zeigt Gegenmaßnahmen (sanfteste zuerst) **und passende Nützlinge** |
| `list_diseases` / `get_disease` | Krankheiten: Erreger, Inkubationszeit, auslösende Bedingungen, betroffene Pflanzenteile |
| `get_treatment` | Eine Behandlung im Detail — mit **Karenzzeit** vor der Ernte, Schutzausrüstung und Anwendung |
| `get_plant_inspections` | Die IPM-Inspektionen einer Pflanze: Befallsdruck, Funde, beobachtete Symptome |
| `list_fertilizers` | Verfügbare Dünger mit EC-Beitrag und Maximaldosis |
| `calculate_mixing_protocol` | Düngerechner: Dosierung je Produkt für dein Zielvolumen und deine Ziel-EC, in der richtigen Mischreihenfolge |
| `list_cultivars` / `get_cultivar` | Sorten einer Art: Züchter, Merkmale, Saatgut-Typ, Tage bis zur Reife |
| `list_substrates` | Substratkatalog: Medien und ihre Eigenschaften |
| `list_overwintering_profiles` | Überwinterungsprofile: Schutzmethode, Lagerbedingungen, Zeitpunkte |
| `list_starter_kits` | Starter-Kits für den Einstieg |
| `list_phase_definitions` | Wachstumsphasen-Definitionen der Lebenszyklus-Logik — die einzelnen Bausteine, nicht die Abfolgen |
| `get_species_phase_sequence` | Die Phasen-Abfolge, auf der eine Art tatsächlich läuft: Zyklustyp, ob sie sich wiederholt, ob eine Ruhephase nötig ist — dazu die geordneten Phasen mit ihrer effektiven Dauer und den Kennzeichen „Endphase" und „Ernte erlaubt" |
| `list_phase_sequences` | Der Katalog aller Phasen-Abfolgen — damit sich nicht nur feststellen lässt, dass eine Zuordnung falsch ist, sondern auch die richtige benennen |
| `list_species_by_phase_sequence` | Die Umkehrung: alle Arten, die an einer Abfolge hängen. Sitzt eine Zimmerpflanze in derselben Gruppe wie Rosenkohl und Porree, ist das kein Einzelfall, sondern eine Vorlagen-Kollision |
| `get_species_lifecycle` | Der Lebenszyklus einer Art: ein- oder mehrjährig, ob sie nach der Blüte stirbt (monokarp) oder wieder blüht (polykarp), Lebenserwartung, Ruhebedarf |
| `get_plant_phase_status` | Der Phasenstand einer Pflanze: Tage in der Phase, nächste Phase, Zyklusnummer, ob eine Ernte vorgesehen ist — und ein `phase_state`, das „nie gestartet", „steckt in einer nicht auflösbaren Phase", „zwischen zwei Zyklen" und „läuft" auseinanderhält |
| `get_plant_phase_history` | Der Phasenverlauf einer Pflanze mit Grund, Datum und tatsächlicher Dauer je Übergang |
| `list_hardiness_zones` | Winterhärtezonen mit Temperaturbereichen |
| `search_glossary` | Fachbegriffe aus dem Glossar nachschlagen (VPD, EC, Karenz …) |
| `search_plant_knowledge` | Wissensbasis durchsuchen (RAG) — liefert **zitierfähige** Quellenverweise mit Score, damit eine Begründung ihre Quelle benennen kann. Mandantenunabhängig; nur die Suchanfrage verlässt die Instanz |
| `list_species` | Pflanzenarten-Katalog auflisten (paginiert) |
| `get_species_info` | **Vollständige** Stammdaten einer Art: Aussaat-, Blüte- und Erntefenster, Winterhärte, Frostempfindlichkeit, Nährstoffbedarf, Giftigkeit, Mischkultur-Hinweise und die zugehörigen Sorten |
| `list_planting_runs` | Pflanzdurchläufe des Mandanten auflisten, optional nach Status gefiltert |
| `list_tasks` | Aufgaben des Mandanten auflisten, optional nach Status gefiltert |
| `get_due_care_tasks` | Heute fällige/überfällige Pflegeerinnerungen, gruppiert nach Dringlichkeit |
| `get_harvest_readiness` | Erntebereitschafts-Überblick über alle aktiven Pflanzen |
| `get_mcp_activity` | Eigener MCP-Aufrufverlauf des Kontos (Selbstauskunft, siehe unten) |
| `list_pending_diary_analyses` | Arbeitsvorrat der zur KI-Analyse markierten Tagebuch-Einträge — ohne Freitext und ohne Bilder (siehe [Tagebuch-Analyse: externe Agenten](#tagebuch-analyse-externe-agenten)) |
| `get_diary_entry` | Ein Tagebuch-Eintrag samt Pflanzenkontext, ohne Bilddaten |
| `get_diary_entry_photos` | Die Fotos eines Tagebuch-Eintrags als Bild-Content-Blöcke — das einzige Werkzeug der Palette, das etwas anderes als Text liefert |

### Schreib-Werkzeuge (`mcp.write`)

| Werkzeug | Zweck |
|----------|-------|
| `confirm_care_task` | Pflegeerinnerung für eine Pflanze quittieren ("ich habe gegossen") |
| `archive_plant` | Pflanze als entsorgt/abgegeben/gestorben kennzeichnen — **kein** Hard-Delete, Verlauf bleibt erhalten |
| `set_plant_location` | Pflanze zu einem anderen Standort/Bereich/Slot verschieben |
| `add_plant_diary_entry` | Einen Tagebuch-Eintrag zu einer Pflanze erfassen (Beobachtung, Problem, Messwert) — nur Text, keine Fotos. `measurements` benennt die erkannten Größen mit ihrer Einheit im Schlüssel (`ec_ms_cm`, `ph`, `temperature_c`, `humidity_percent`, `height_cm`, `leaf_count`) und nimmt darüber hinaus weiterhin beliebige eigene Schlüssel an |
| `claim_diary_analysis` | Einen wartenden Tagebuch-Eintrag exklusiv beanspruchen (Lease) |
| `submit_diary_analysis` | Das Analyse-Ergebnis eines beanspruchten Tagebuch-Eintrags zurückschreiben |
| `record_feeding_event` | Einen Düngevorgang erfassen: Menge in Litern, EC und pH vor und nach der Gabe, Drainage-EC/-pH und der Tankbezug. Das Pflegeprotokoll kennt nur „quittiert" — hier stehen die Zahlen |
| `create_inspection` | Eine IPM-Inspektion anlegen: Befallsdruck, Symptome und **strukturierte Befunde** mit Sicherheit (0.0–1.0) und betroffenem Pflanzenteil |
| `assign_nutrient_plan` | Einen **vorhandenen** Nährstoffplan an eine Pflanze binden (eigener Plan oder globale Vorlage). Pläne anzulegen oder zu bearbeiten ist bewusst kein Werkzeug |
| `transition_plant_phase` | Eine Pflanze in eine Phase setzen oder eine falsche korrigieren. Das Ziel wird gegen die Abfolge geprüft, auf der die **Art dieser Pflanze** läuft — ein fremder Phasenschlüssel würde die Pflanze in einer Phase parken, aus der ihr Lebenszyklus nie wieder herausfindet |

### Setup-Werkzeuge (`mcp.setup`)

| Werkzeug | Zweck |
|----------|-------|
| `create_site` | Standort-Wurzel anlegen (Wohnung, Garten, Balkon, Gewächshaus, Fensterbank, Growzelt) |
| `assign_species_phase_sequence` | Eine Art an eine **vorhandene** Phasen-Abfolge binden. Verlangt `mcp.setup` und nicht nur `mcp.write`, weil Arten und Abfolgen zum gemeinsamen Katalog gehören: eine einzige Bindung ändert den Zeitplan aller Pflanzen dieser Art in *jedem* Garten. Abfolgen zu *definieren* bleibt bewusst Aufgabe der Oberfläche |

Jedes Werkzeug prüft die referenzierten Schlüssel (Pflanze, Standort, Bereich, Slot) grundsätzlich gegen den für diesen Aufruf aufgelösten Mandanten. Ein Fremdschlüssel aus einem anderen Mandanten liefert konsequent `not_found` — niemals `permission.denied` — damit kein Werkzeug die Existenz fremder Ressourcen verrät.

## Wachstumsphasen und Lebenszyklus

Die Phasen-Logik steuert Aufgabenplanung, Düngefenster, Erntebereitschaft und Überwinterung (interne Referenz: REQ-003). Über MCP war davon lange nur `list_phase_definitions` sichtbar — der Katalog der einzelnen **Bausteine**. Nicht die Abfolgen, zu denen sie zusammengesetzt sind, nicht welche Abfolge für eine Art gilt, und nicht der Phasenstand einer konkreten Pflanze. Eine gewöhnliche Frage wie „läuft diese Pflanze auf der botanisch richtigen Phasen-Abfolge?" war darüber schlicht nicht zu beantworten.

Acht Werkzeuge schließen diese Lücke. Sechs lesen, zwei schreiben — und jedes Schreib-Werkzeug ist mit dem Lese-Werkzeug gepaart, das seine Verweise auflöst, **und** dem, das sein Ergebnis wiederfindet:

| Schreib-Werkzeug | Löst seine Verweise auf | Macht sein Ergebnis sichtbar |
|------------------|-------------------------|------------------------------|
| `transition_plant_phase` | `get_species_phase_sequence` (liefert die gültigen Phasenschlüssel) | `get_plant_phase_status` |
| `assign_species_phase_sequence` | `list_phase_sequences` | `get_species_phase_sequence` |

### Warum `phase_state` mehr sagt als „keine Phase"

`get_plant` liefert für eine Pflanze ohne Phase nur `current_phase_key: null`. Darin stecken aber drei verschiedene Zustände, die jeweils etwas anderes verlangen:

| `phase_state` | Bedeutung | Was zu tun ist |
|---------------|-----------|----------------|
| `never_initialised` | Es gibt überhaupt keinen Phasenverlauf — der Lebenszyklus wurde nie gestartet | Eine Startphase setzen |
| `unresolved` | Es gibt einen offenen Verlaufseintrag, aber er zeigt auf keine auflösbare Phase. Die Pflanze steht still, ohne dass es auffällt | Auf eine gültige Phase der eigenen Abfolge korrigieren |
| `between_cycles` | Alle Phasen sind abgeschlossen, keine ist offen — bei einer mehrjährigen Pflanze ein normaler Zustand | Nichts; der nächste Zyklus startet |
| `in_phase` | Die Pflanze läuft | Nichts |

### Wie eine Art zu ihrer Abfolge kommt

Ist eine Art nicht ausdrücklich gebunden, leitet Kamerplanter die Abfolge aus ihren botanischen Merkmalen ab. Die Regeln greifen in dieser Reihenfolge; die erste, die passt, gewinnt:

1. **Kurztag-Zierpflanzen**, die mehrjährig sind → photoperiodischer Zierpflanzen-Zyklus (Weihnachtsstern, Kalanchoe). Die Einschränkung auf Mehrjährige ist Absicht: einjährige Kurztag-*Nutzpflanzen* sollen ihren Erntezyklus behalten.
2. **Monokarpe mehrjährige Aufsitzerpflanzen** (Bromelien) → Kindel-Zyklus: Die Mutterpflanze stirbt nach der Blüte, der Nachwuchs führt weiter.
3. **CAM-Sukkulenten** → Zyklus mit kühl-trockener Winterruhe.
4. **Wuchsform**: Farne, Zwiebelpflanzen und Palmen bekommen ihren jeweils eigenen Zyklus.
5. **Jede weitere mehrjährige Art** → immergrüner Blattschmuck-Zyklus (die größte Gruppe im Zimmer).
6. **Bekannt ein- oder zweijährig** → der einjährige Standardzyklus mit Ernte am Ende.
7. **Alles andere** → ebenfalls der immergrüne, sich wiederholende Zyklus.

!!! warning "Fehlende Angaben führen nicht mehr zu einer Ernte"
    Punkt 7 ist eine Sicherheits- und keine botanische Regel. Fehlt einer Art die Lebenszyklus-Angabe ganz, ist das **keine Antwort** und darf nicht als „einjährig" gelesen werden. Früher landete eine solche Art auf dem einjährigen Standardzyklus — 126 Tage, mit Ernte und Lebensende am Schluss. Ein immergrüner, mehrjähriger Yucca-Baum war damit 126 Tage nach dem Pflanzen als erntereif und abgeschlossen eingeplant.

    Die beiden Irrtümer kosten nicht gleich viel: Eine einjährige Pflanze auf einem mehrjährigen Zyklus verpasst nur einen Ernte-Hinweis, den du weiterhin selbst auslösen kannst. Eine mehrjährige Pflanze auf einem einjährigen Zyklus bekommt eine Ernte und ein Lebensende erfunden, die niemand vorgesehen hat. Deshalb fällt der Zweifelsfall auf den sich wiederholenden Zyklus.

Welche Angaben in diese Entscheidung eingehen — und was passiert, wenn eine davon fehlt — zeigt `get_species_info`: Es liefert `plant_category`, `photosynthesis_type`, `growth_habit`, `indoor_suitable`, `mature_height_cm` und `frost_sensitivity`. Leere Felder werden weggelassen; ein dünn besetzter Datensatz sieht also auch dünn aus — was selbst schon die Antwort auf „reicht dieser Datensatz für eine verlässliche Zuordnung?" ist.

Eine falsche Zuordnung korrigierst du mit `assign_species_phase_sequence`; welche Arten sonst noch auf derselben Abfolge sitzen, verrät `list_species_by_phase_sequence`.

## Tagebuch-Analyse: externe Agenten

Die fünf `*_diary_*`-Werkzeuge sind der vollständige technische Vertrag für einen extern betriebenen KI-Agenten, der Tagebuch-Einträge analysiert, die ein Nutzer markiert hat (interne Referenz: REQ-050). Die Endnutzer-Sicht — wie du einen Eintrag markierst und wo du ein Ergebnis liest — steht unter [Tagebuch](../user-guide/plant-diary.md). Dieser Abschnitt beschreibt die Gegenseite: das Rezept eines Agenten, der diese Einträge abholt, bearbeitet und das Ergebnis zurückschreibt.

!!! info "Kamerplanter ruft selbst kein Sprachmodell auf"
    Diese fünf Werkzeuge sind der einzige Weg, über den ein Sprachmodell überhaupt Tagebuchinhalte zu sehen bekommt — und selbst dabei bleibt die Instanz eine reine Datenquelle und -senke. Es gibt weder einen eingebauten Modellaufruf noch einen Modellschlüssel für diesen Pfad. Ein Agenten-Rezept für dieses Werkzeug-Set liegt in einem eigenen, von Kamerplanter getrennten Repository (`kamerplanter-goose`) und ist nicht Bestandteil dieses Produkts.

### Der Ablauf

1. Ein Nutzer markiert einen Tagebuch-Eintrag in der Weboberfläche — der Eintrag wechselt in den Zustand `requested`.
2. `list_pending_diary_analyses` (`mcp.read`) liefert den Arbeitsvorrat — ohne Freitext und ohne Bilder, damit die Antwort klein bleibt.
3. `claim_diary_analysis` (`mcp.write`) beansprucht einen Eintrag exklusiv über ein Lease (Vorgabe 15 Minuten, Obergrenze 60 Minuten) und liefert einen `lease_token`. Ein zweiter Beanspruchungsversuch auf denselben Eintrag scheitert mit `conflict.already_claimed`. Läuft das Lease ab, ohne dass ein Ergebnis zurückgeschrieben wurde, erscheint der Eintrag wieder im Arbeitsvorrat.
4. `get_diary_entry` (`mcp.read`) liefert Text, Tags, Messwerte, den **Umgebungs-Schnappschuss** (`environment`) und den Pflanzenkontext — ohne Bilddaten. Der Schnappschuss steht in einem **eigenen** Feld neben `measurements`, nie darin: `measurements` ist, was ein Mensch getippt hat, `environment` ist, was ein Gerät gemeldet hat, und jeder Wert trägt `source`, `measured_at` und `origin` (`location` | `site` | `weather`). `environment_status` sagt, was eine leere Liste bedeutet — `no_source` („nichts misst diese Pflanze") ist etwas anderes als `unavailable` („die Messung kam nicht durch").
5. `get_diary_entry_photos` (`mcp.read`) liefert die Fotos als Bild-Content-Blöcke, damit ein bildverstehendes Modell sie direkt sieht (siehe [Bild-Auslieferung](#bild-auslieferung) unten).
6. Der Agent ruft das Sprachmodell auf, das der Nutzer selbst betreibt und bezahlt.
7. `submit_diary_analysis` (`mcp.write`) schreibt das Ergebnis mit gültigem `lease_token` zurück und setzt den Zustand auf `completed` oder `failed`.

### Bild-Auslieferung {#bild-auslieferung}

`get_diary_entry_photos` ist das einzige Werkzeug der Palette, dessen Nutzdaten nicht vollständig in `structuredContent` liegen: Die Antwort trägt zusätzlich `image`-Content-Blöcke (Basis-64, `mimeType: image/webp`), einen je geliefertem Foto, in derselben Reihenfolge wie im strukturierten `photos`-Feld.

Ausgeliefert werden ausschließlich die vorhandenen **512- oder 1280-px-WebP-Renditions** — niemals das Originalfoto. Renditions tragen keine EXIF-Daten, auch dann nicht, wenn die Instanz `STORAGE_STRIP_EXIF=false` gesetzt hat; jenes Setting betrifft nur die Originaldatei (siehe [Umgebungsvariablen — Object Storage](../reference/environment-variables.md#object-storage-nfr-013)).

Die Gesamt-Nutzlast eines Aufrufs ist über `MCP_MAX_IMAGE_PAYLOAD_MB` gedeckelt (Vorgabe 4 MB, Base-64-kodiert; siehe [Umgebungsvariablen — MCP-Server](../reference/environment-variables.md#mcp-server)). Wird sie überschritten, antwortet das Werkzeug mit `payload.too_large` und benennt die betroffenen Fotos sowie eine kleinere Rendition, mit der der Abruf passen würde — es wird **nie** still gekürzt. Fehlt eine Rendition noch, erscheint das betroffene Foto in `pending` mit `status: "thumbnail_pending"` (Erzeugung angestoßen, später erneut abrufbar) oder `status: "unavailable"` (wird nie entstehen, z. B. weil der Anhang fehlt) — der Aufruf selbst bleibt in beiden Fällen erfolgreich.

### Fehlercodes

Jeder Fehler eines der fünf Werkzeuge kommt als Werkzeug-Ergebnis mit `isError: true`, nie als JSON-RPC-`error` — derselbe Vertrag wie für die übrige Palette (siehe [Fehlerbehandlung](error-handling.md)). `error_code` ist maschinenlesbar und stabil, `message` ist für Menschen gedacht und darf sich ändern.

| `error_code` | Bedeutung |
|---------------|-----------|
| `not_found` | Mandant oder Eintrag existiert nicht oder liegt außerhalb des aufgelösten Mandanten — auch bei einem fremden Eintrag, nie `permission.denied` |
| `permission.denied` | Die Rolle im aufgelösten Mandanten reicht für das Werkzeug nicht |
| `validation.error` | Eingabe verletzt eine Feldregel (z. B. `confidence` außerhalb 0.0–1.0, fehlendes `summary` bei `status: completed`) |
| `validation.tenant_required` | `tenant` fehlt, obwohl der Schlüssel mehr als eine Mitgliedschaft hat |
| `conflict.already_claimed` | Der Eintrag ist bereits beansprucht und das Lease noch gültig |
| `conflict.concurrent_update` | Die Dokumentrevision hat sich zwischen Lesen und Setzen geändert — ein sofortiger Wiederholungsversuch ist hier richtig |
| `conflict.not_claimed` | `submit_diary_analysis` auf einen Eintrag, der nicht `in_progress` ist |
| `conflict.lease_expired` | Der `lease_token` passt nicht (mehr) zum aktuellen Lease |
| `payload.too_large` | Die Bild-Nutzlast des Aufrufs überschreitet `MCP_MAX_IMAGE_PAYLOAD_MB` |

### Was ein Rezept nicht selbst entscheiden muss

- Der **Vorbehalt** (`disclaimer`) im Ergebnis wird serverseitig gesetzt — ein Agent kann ihn weder weglassen noch abschwächen.
- Ob ein Nutzer überhaupt markieren darf, prüft der Server bei jedem `mcp.write`-Aufruf serverseitig (Rolle, Autorschaft, Einwilligung `diary_ai_analysis`, Betriebsmodus) — ein Rezept muss diese Regel nicht nachbilden.
- Ein Eintrag ohne Fotos ist kein Fehlerfall; `get_diary_entry_photos` liefert dann `photos: []` mit nur dem Text-Block.

### Einen Eintrag schreiben ist eine andere Aufgabe

`add_plant_diary_entry` (`mcp.write`) gehört zur allgemeinen Werkzeug-Palette, nicht zu den fünf oben: Damit **dokumentiert** ein Agent eine Beobachtung — Text, Tags, Messwerte — statt sie zu analysieren. Daraus folgen zwei Grenzen:

- Ein neu geschriebener Eintrag wird **nicht** zur Analyse eingereiht. Das Markieren bleibt eine Nutzerhandlung; ein Agent kann sich also keine eigene Arbeit erzeugen, und die Einwilligungsprüfung auf dem Markier-Pfad wird nie umgangen.
- Das Werkzeug nimmt **keine** Foto-Referenzen entgegen. Ein Foto anzuhängen setzt voraus, es selbst hochgeladen zu haben (oder die Rolle Leitung zu tragen), und MCP hat keinen Upload-Weg — Fotos kommen über die Weboberfläche an den Eintrag.

Wiederfinden lässt sich das Geschriebene mit `list_diary_entries` (`mcp.read`). Das Werkzeug durchsucht die Einträge des Gartens nach Pflanze, Eintragstyp, Tag, Analyse-Zustand und Zeitraum und liefert je Zeile Titel, Tags und Messwerte — den **Freitext** aber nicht. Der kommt aus `get_diary_entry`, einem bewussten Einzelabruf. Eine durchblätterbare Liste aller Beobachtungstexte wäre etwas anderes als das gezielte Lesen eines Eintrags.

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
- [Tagebuch — Benutzerhandbuch](../user-guide/plant-diary.md)
- [KI-Assistent — Benutzerhandbuch](../user-guide/ai-assistant.md)
- [Umgebungsvariablen — MCP-Server](../reference/environment-variables.md#mcp-server)
- [Datenschutz & DSGVO](../user-guide/privacy.md)
- [Fehlerbehandlung](error-handling.md)
- [MCP-Werkzeuge für die Entwicklung (nicht zu verwechseln)](../development/mcp-tools.md)
