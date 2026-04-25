# Spezifikation: REQ-033 - MCP-Server fuer LLM-gestuetzte Garten- und Anbauverwaltung

```yaml
ID: REQ-033
Titel: Model Context Protocol (MCP) Server fuer Kamerplanter
Kategorie: Integration & KI
Fokus: Beides
Technologie: Python 3.14+, FastAPI, Model Context Protocol SDK (Anthropic), ArangoDB, Redis, Pydantic v2
Status: Entwurf
Version: 1.1
Abhaengigkeit: REQ-001 v5.0 (Stammdaten), REQ-002 v4.2 (Standortverwaltung), REQ-006 v2.7 (Aufgabenplanung), REQ-013 v2.0 (Pflanzdurchlauf), REQ-014 v1.4 (Tankmanagement), REQ-019 (Substratverwaltung), REQ-020 v1.1 (Onboarding), REQ-022 v2.4 (Pflegeerinnerungen), REQ-010 v1.0 (IPM), REQ-007 v1.0 (Erntemanagement), REQ-023 v1.7 (Service Accounts), REQ-024 v1.4 (RBAC Permission-Matrix), REQ-025 v1.0 (DSGVO), REQ-031 v1.0 (KI-Assistent / RAG)
```

## 1. Business Case

**User Story (Casual User — Voice/Chat):** "Als Zimmerpflanzen-Besitzer moechte ich Claude oder einen lokalen LLM-Client fragen koennen 'Welche Pflanzen muss ich heute giessen?' und direkt eine vollstaendige Liste mit Standort und Dringlichkeit bekommen — damit ich keine separate App oeffnen muss."

**User Story (Grower — Diagnose-Workflow):** "Als Indoor-Grower moechte ich Claude bitten koennen 'Meine Tomate in Beet 2 hat gelbe Blaetter, schlage eine Diagnose und ein Treatment vor' und das LLM ruft eigenstaendig Inspection-, Sensor-, IPM- und Karenz-APIs auf — damit ich eine fundierte Empfehlung mit Verweis auf meine echten Daten erhalte, statt einer halluzinierten Antwort."

**User Story (Power-User — Autonome Agenten):** "Als technisch versierter Nutzer moechte ich einen Claude-Agenten einrichten koennen, der morgens automatisch meinen Pflege-Stand prueft, ueberfaellige Tasks meldet und mir Tageszusammenfassungen schickt — ueber den MCP-Server als saubere, typisierte Schnittstelle."

**User Story (Self-Hosted-Nutzer — Datenschutz):** "Als datenschutzbewusster Self-Hosted-Nutzer moechte ich den MCP-Server lokal betreiben und ueber lokale LLM-Clients (Ollama-Anbindung, Claude Desktop, custom MCP-Clients) ansprechen — damit meine Pflanz- und Sensor-Daten nicht ueber Cloud-Provider laufen."

**User Story (Tenant-Admin — Service-Account-Bindung):** "Als Tenant-Admin moechte ich pro MCP-Client einen Service-Account mit definierter Permission-Matrix anlegen koennen — damit ein Read-Only-Diagnose-Agent keine Pflanzdurchlaeufe loeschen oder Treatments anwenden kann."

**User Story (Knowledge-Bruecke):** "Als Nutzer moechte ich ueber den MCP-Server auch die globale Wissensbasis (Companion Planting, Schaedlingsbestimmung, Naehrstoffmangel-Symptome) durchsuchen koennen — damit Claude/LLM-Clients fundierte fachliche Empfehlungen geben, gegruendet auf der kuratierten Kamerplanter-RAG-Wissensbasis statt auf Halluzinationen."

**Beschreibung:**

REQ-033 stellt einen **Model Context Protocol (MCP) Server** bereit, der Kamerplanter als Werkzeug-Sammlung an externe LLM-Clients (Claude Desktop, Claude Code, Cursor, lokale Ollama-MCP-Bridges, custom Agenten) anbindet. Im Gegensatz zur generischen REST-API exponiert der MCP-Server eine **kuratierte, semantisch hochstufige Tool-Palette** — keinen 1:1-CRUD-Spiegel — sodass LLMs in wenigen Schritten Aufgaben erledigen, die ueber die REST-API viele kettenfoermige Aufrufe erfordern wuerden.

**Grundprinzipien:**

- **Semantische Tools statt REST-Mirror:** Tools wie `get_due_care_tasks(tenant)`, `apply_starter_kit(...)`, `diagnose_plant(plant_key)` — nicht 200 CRUD-Endpoints. Jedes Tool kapselt einen kompletten Use-Case und gibt LLM-freundliches, kompaktes JSON zurueck.
- **Permission-gebunden ueber Service Accounts (REQ-023 v1.7):** Authentifizierung ausschliesslich per API-Key eines Service Accounts. Permission-Matrix (REQ-024 v1.4) entscheidet pro Tool-Aufruf, ob der Account Lese- oder Schreibrechte hat.
- **Tenant-isoliert:** Jeder MCP-Client ist an genau einen Tenant gebunden. Cross-Tenant-Lookups sind unmoeglich.
- **Local-First & optional:** Der Server ist eine eigenstaendige optionale Komponente. Ohne MCP-Server funktioniert Kamerplanter unveraendert.
- **RAG-Bruecke zu REQ-031:** Tool `search_plant_knowledge(query)` ruft die bestehende RAG-Infrastruktur auf — kein paralleles Wissenssystem.
- **Read-Heavy by Default:** Schreibtools (Task-Quittierung, Diary-Eintrag) sind explizit gekennzeichnet und unterliegen pro Service Account einer separaten `mcp.write`-Permission.
- **DSGVO-konform (REQ-025):** Audit-Log jedes Tool-Aufrufs mit Service-Account-Key, Tenant, Tool-Name, Input-Hash, Output-Size. Keine PII im Log.
- **Streaming-faehig:** Lange Operationen (z. B. `generate_growing_report`) liefern via MCP-Notifications inkrementelle Fortschrittsupdates.

### 1.1 Abgrenzung zu benachbarten REQs

| REQ | Beziehung |
|-----|-----------|
| **REQ-031 (KI-Assistent)** | Komplementaer. REQ-031 ist die *interne* RAG-/Chat-Funktion, in Kamerplanter eingebaut, fuer App-Nutzer. REQ-033 ist die *externe* Schnittstelle, ueber die fremde LLM-Clients Kamerplanter als Tool benutzen. Gemeinsame RAG-Wissensbasis (`spec/knowledge/rag/`). |
| **REQ-030 (Notifications)** | Komplementaer. REQ-030 *pusht* Erinnerungen aus Kamerplanter heraus (HA, E-Mail, Apprise). REQ-033 erlaubt es einem LLM, *aktiv* den Pflege-Stand abzufragen. |
| **REQ-016 (InvenTree)** | Aehnliches Muster: optionale externe Integration. MCP-Server ist nicht InvenTree-spezifisch, sondern protokoll-getrieben. |
| **REQ-023 (Service Accounts)** | Hartes Prerequisite. MCP-Server akzeptiert ausschliesslich Service-Account-API-Keys. |
| **REQ-024 (Permission-Matrix)** | Jeder Tool-Aufruf wird ueber `require_permission()` geroutet. |

### 1.2 Architekturueberblick

```
+---------------------------+
|  LLM-Client               |
|  (Claude Desktop, Cursor, |
|   Claude Code, custom)    |
+-------------+-------------+
              |
              |  MCP Protocol (stdio | HTTP+SSE)
              v
+---------------------------+
|  Kamerplanter MCP Server  |       eigenstaendiger Prozess /
|  src/mcp-server/          |       eigener Helm-Chart
|                           |
|  +---------------------+  |
|  | Tool Registry       |  |
|  +----------+----------+  |
|             v             |
|  +---------------------+  |
|  | AuthInterceptor     |  |  <-- Service-Account-API-Key
|  | (REQ-023)           |  |
|  +----------+----------+  |
|             v             |
|  +---------------------+  |
|  | PermissionGuard     |  |  <-- Permission-Matrix (REQ-024)
|  | (REQ-024)           |  |
|  +----------+----------+  |
|             v             |
|  +---------------------+  |
|  | Tool-Handler        |  |
|  +----------+----------+  |
+-------------|-------------+
              |
              |  internes Backend-API (HTTP, Service-Account-Token)
              v
+---------------------------+
|  Kamerplanter Backend     |
|  (FastAPI, ArangoDB, RAG) |
+---------------------------+
```

**Deployment-Modi:**

| Modus | Transport | Use-Case |
|-------|-----------|----------|
| **stdio** | stdin/stdout | Lokal ueber Claude Desktop / Claude Code config — Server wird vom Client gestartet |
| **HTTP+SSE** | HTTPS | Self-Hosted-Deployments — Server laeuft als eigener Pod, Clients verbinden via URL |

## 2. Tool-Inventar (Cut 1.0)

Die initiale Tool-Palette ist bewusst kuratiert (~30 Tools), abgeleitet aus den haeufigsten LLM-Use-Cases mit Schwerpunkt **Onboarding (Wohnung/Garten einrichten)**, **Bestandsaufnahme (Pflanzen erfassen)** und **Tagesbetrieb (Pflege, Diagnose)**. Erweiterung erfolgt nach Nutzungsmessung.

**Schreibzugriffs-Philosophie:** Schreibtools folgen vier festen Mustern, damit ein LLM sie sicher und idempotent verwenden kann:

1. **Dry-Run-Vorschau:** Jedes Schreibtool akzeptiert `dry_run: bool = false`. Bei `true` wird nur der geplante Effekt zurueckgeliefert, nichts persistiert. Pflicht fuer LLM-Bestaetigungs-Workflows.
2. **Idempotency-Key:** Jedes Schreibtool akzeptiert optionalen `idempotency_key: str`. Identische Keys innerhalb 24 h liefern das urspruengliche Ergebnis statt Duplikat anzulegen — kritisch bei LLM-Retries.
3. **Bulk-Faehig wo sinnvoll:** "Lege 6 Tomaten an" muss in einem Tool-Aufruf gehen, nicht 6× hintereinander. Bulk-Tools haben Suffix `_bulk` und liefern Pro-Eintrag-Status.
4. **Macro-Tools fuer Onboarding:** Hochstufige Setup-Tools (`setup_apartment`, `setup_growbox`) fassen Site + Locations + Slots in einem Aufruf zusammen — der LLM-User-Dialog wird kurz und natuerlich.

### 2.1 Read-Tools (Permission `mcp.read`)

| Tool | Zweck | Backend-Endpoints (intern) |
|------|-------|---------------------------|
| `list_tenants` | Liste der Tenants des Service Accounts (typischerweise 1) | `GET /tenants/me` |
| `get_due_care_tasks` | Heute / die naechsten N Tage faellige Pflegeaufgaben, gruppiert nach Dringlichkeit | `GET /t/{slug}/care/dashboard` |
| `list_planting_runs` | Aktive Pflanzdurchlaeufe inkl. Phase, Standort, Dauer | `GET /t/{slug}/planting-runs?status=active` |
| `get_planting_run` | Detaildaten zu einem Run: Phase, naechste Tasks, juengste Sensor-/Care-Events, Karenz-Status | `GET /t/{slug}/planting-runs/{key}` (+ Aggregation) |
| `list_plants_at_location` | Alle Pflanzen an einem Standort/Beet/Slot | `GET /t/{slug}/locations/{key}/plants` |
| `get_plant_diagnostics` | Aggregierter Diagnose-Snapshot fuer eine Pflanze: Sensorwerte, EC/pH-Trend, IPM-Inspections, Karenz, juengste Tips | mehrere Endpoints, im Tool aggregiert |
| `search_plant_knowledge` | Volltext-/Vektor-Suche in Wissensbasis (RAG ueber `spec/knowledge/rag/`) | `POST /knowledge/search` (REQ-031) |
| `get_species_info` | Stammdaten zu einer Species/Cultivar inkl. Companion Planting, Karenz-relevanter Treatments | `GET /species/{key}` |
| `list_overdue_tasks` | Ueberfaellige Tasks (alle Sources: REQ-006, REQ-022) | `GET /t/{slug}/tasks?status=overdue` |
| `get_harvest_readiness` | Erntebereitschaftssignale aller aktiven Runs (Karenz, Indikatoren) | `GET /t/{slug}/harvest/readiness` |

### 2.2 Write-Tools — Tagesbetrieb (Permission `mcp.write`)

| Tool | Zweck | Backend-Endpoints (intern) |
|------|-------|---------------------------|
| `confirm_care_task` | Pflegeaufgabe quittieren ("ich habe gegossen") | `POST /t/{slug}/care/confirmations` |
| `add_plant_diary_entry` | Freitext-Eintrag zur Pflanze (REQ-013 v2.0 PlantDiaryEntry) | `POST /t/{slug}/plants/{key}/diary` |
| `create_inspection` | IPM-Inspektion mit Symptomen anlegen | `POST /t/{slug}/ipm/inspections` |
| `transition_planting_run` | Phase eines Runs vorruecken (sofern HSTValidator zustimmt) | `POST /t/{slug}/planting-runs/{key}/transition` |
| `record_feeding_event` | Duenge-Vorgang erfassen (Menge, EC/pH, Tank) | `POST /t/{slug}/feeding-events` |
| `record_harvest` | Ernte-Eintrag mit Frischgewicht + Quality-Notes | `POST /t/{slug}/harvest/batches` |
| `apply_treatment` | IPM-Treatment anwenden (Karenz-Gate aktiv) | `POST /t/{slug}/ipm/treatment-applications` |

### 2.3 Write-Tools — Setup & Stammdaten (Permission `mcp.setup`)

Die `mcp.setup`-Permission ist getrennt von `mcp.write`, damit ein "Diary-Bot" nicht versehentlich Standorte loescht. Tenant-Admins koennen einem Service Account `mcp.setup` gezielt zuweisen — typischerweise einmalig waehrend des Onboardings, danach widerrufen.

| Tool | Zweck | Backend-Endpoints (intern) |
|------|-------|---------------------------|
| `setup_apartment` | Macro: Site "Wohnung" + N Raeume in einem Aufruf | `POST /t/{slug}/sites` + `POST /t/{slug}/locations` (Bulk) |
| `setup_growbox` | Macro: Indoor-Site + Growzelt-Location + Slots + Substrat-Charge | mehrere Endpoints in Transaktion |
| `setup_outdoor_garden` | Macro: Outdoor-Site + Beete + WaterProfile (Leitung/RO) | mehrere Endpoints in Transaktion |
| `create_site` | Standort-Wurzel anlegen (Wohnung, Garten, Balkon, Gewaechshaus) | `POST /t/{slug}/sites` |
| `update_site` | Site-Eigenschaften aendern (GPS, Wasserprofil, Klimazone) | `PATCH /t/{slug}/sites/{key}` |
| `create_location` | Raum/Regal/Beet/Slot anlegen, beliebig tief verschachtelt | `POST /t/{slug}/locations` |
| `create_locations_bulk` | Mehrere Locations in einem Schritt (z. B. "12 Beete im 4×3-Raster") | `POST /t/{slug}/locations/bulk` |
| `update_location` | Location umbenennen, Eigenschaften aendern, Eltern wechseln | `PATCH /t/{slug}/locations/{key}` |
| `delete_location` | Location loeschen (rekursiv mit Pflanzen-Sicherheitsabfrage) | `DELETE /t/{slug}/locations/{key}` |
| `set_water_profile` | Tap-Water- oder RO-Profil an Site haengen (REQ-002 v4.2) | `PUT /t/{slug}/sites/{key}/water-profile` |
| `create_substrate_batch` | Neue Substrat-Charge fuer eine Site anlegen | `POST /t/{slug}/substrates` |
| `apply_starter_kit` | Starter-Kit anwenden (Bypass kompletter Onboarding-Wizard) | `POST /t/{slug}/onboarding/starter-kits/{key}/apply` |

### 2.4 Write-Tools — Pflanzen erfassen (Permission `mcp.write`)

| Tool | Zweck | Backend-Endpoints (intern) |
|------|-------|---------------------------|
| `find_or_create_species` | Species per Name suchen, sonst neu anlegen (Cultivar optional) | `GET /species?q=...` + ggf. `POST /species` |
| `create_plant` | Einzelne Pflanze anlegen (Standalone, optional einer Run zuordnen) | `POST /t/{slug}/plants` |
| `create_plants_bulk` | "6 Tomaten 'San Marzano' in Beet 2 anlegen" in einem Aufruf | `POST /t/{slug}/plants/bulk` |
| `create_planting_run` | Pflanzdurchlauf anlegen (REQ-013 v2.0, Mono-/Klon-Run) | `POST /t/{slug}/planting-runs` |
| `add_plants_to_run` | Bestehende Pflanzen einer Run hinzufuegen | `POST /t/{slug}/planting-runs/{key}/entries` |
| `move_plant` | Pflanze zu anderem Standort/Slot umsiedeln | `PATCH /t/{slug}/plants/{key}/location` |
| `set_plant_phase` | Initial-Phase setzen (Import bestehender Pflanze in laufender Phase) | `PATCH /t/{slug}/plants/{key}/phase` |
| `archive_plant` | Pflanze als entsorgt/abgegeben/gestorben kennzeichnen (kein Hard-Delete) | `POST /t/{slug}/plants/{key}/archive` |

### 2.5 Beispiel-Dialoge

**Beispiel 1 — Wohnung einrichten ("Cold Start"):**
```
User:   "Ich habe eine 3-Zimmer-Wohnung. Wohnzimmer mit grossem Sued-Fenster,
         Schlafzimmer Nord-Fenster, Bad ohne Fenster."
LLM:    setup_apartment(
          name="Meine Wohnung",
          rooms=[
            {name: "Wohnzimmer", light_orientation: "south", brightness: "high"},
            {name: "Schlafzimmer", light_orientation: "north", brightness: "low"},
            {name: "Bad",         light_orientation: "none",  brightness: "very_low"},
          ],
          dry_run=true
        )
        -> Vorschau zeigt 1 Site + 3 Locations
LLM:    "Soll ich es so anlegen?"
User:   "Ja"
LLM:    setup_apartment(... dry_run=false, idempotency_key="setup-2026-04-25-001")
```

**Beispiel 2 — Pflanze erfassen ohne genaue Sorte:**
```
User:   "Ich habe gerade 6 Tomatensetzlinge gekauft, Sorte San Marzano,
         und will sie ins Hochbeet 2 setzen."
LLM:    find_or_create_species(scientific_name="Solanum lycopersicum",
                                cultivar="San Marzano")
        -> species_key="sol-lyc", cultivar_key="cv-san-marzano"
LLM:    create_plants_bulk(
          species_key="sol-lyc",
          cultivar_key="cv-san-marzano",
          count=6,
          location_key="loc-hochbeet-2",
          initial_phase="seedling",
          dry_run=true
        )
        -> Vorschau: 6 Pflanzen, naechste empfohlene Tasks (Anwachskontrolle, ...)
User:   "Mach"
LLM:    create_plants_bulk(... dry_run=false, idempotency_key="plants-tomato-...")
```

**Beispiel 3 — Indoor-Growbox aufsetzen:**
```
User:   "Ich habe eine 80×80×160 Mars Hydro Box im Keller mit 4 Slots fuer Pflanzen."
LLM:    setup_growbox(
          name="Mars Hydro 80",
          parent_site_name="Keller",
          dimensions_cm=[80, 80, 160],
          slot_count=4,
          substrate={type: "soil", batch_name: "Compo Sana 2026-04"},
          dry_run=false,
          idempotency_key="growbox-mars-80-001"
        )
```

### 2.6 Tool-Antwort-Format

Jedes Tool liefert kompaktes, LLM-freundliches JSON mit drei Pflicht-Wrappern:

```json
{
  "summary": "3 Pflanzen muessen heute gegossen werden",
  "data": { ... },
  "links": [
    { "type": "ui", "url": "https://kp.example.org/t/home/care" },
    { "type": "api", "url": "/api/v1/t/home/care/dashboard" }
  ]
}
```

`summary` ist eine 1-Satz-Zusammenfassung fuer das LLM, `data` das strukturierte Ergebnis, `links` zeigen dem Endnutzer, wo er Details findet.

Schreibtools liefern zusaetzlich:

```json
{
  "summary": "6 Pflanzen 'San Marzano' im Beet 2 angelegt",
  "data": { "created_keys": [...], "skipped_keys": [...], "errors": [] },
  "dry_run": false,
  "idempotency_key": "plants-tomato-2026-04-25-001",
  "idempotent_replay": false,
  "links": [...]
}
```

`idempotent_replay: true` signalisiert, dass der Idempotency-Key bereits bekannt war und das fruehere Ergebnis zurueckgegeben wurde.

## 3. ArangoDB-Modellierung

Der MCP-Server fuehrt **keine eigenen Domain-Collections**. Er ist eine reine Adapter-Schicht. Zwei neue Collections:

```
mcp_audit_log  (doc collection)
+-- _key
+-- service_account_key   # FK -> users
+-- tenant_key             # FK -> tenants
+-- tool_name              # str
+-- input_hash             # sha256 ueber Tool-Argumente (keine Klartext-Args)
+-- output_size_bytes      # int
+-- duration_ms            # int
+-- status                 # ok | denied | error | dry_run
+-- error_class            # str | null
+-- created_at             # ISO8601

mcp_idempotency_record  (doc collection, TTL 24h)
+-- _key                   # idempotency_key (Service-Account-scoped)
+-- service_account_key
+-- tool_name
+-- input_hash
+-- result_payload         # serialisiertes Ergebnis (max 32 kB)
+-- created_at
+-- expires_at             # ArangoDB TTL Index
```

Audit-Retention 90 Tage (NFR-011), Idempotency-Retention 24 h, beides via TTL bzw. Celery automatisch.

## 4. Technische Umsetzung

### 4.1 Code-Layout

```
src/mcp-server/
├── pyproject.toml
├── app/
│   ├── main.py                  # Entry-Point (stdio | HTTP+SSE)
│   ├── config.py                # Pydantic-Settings (Backend-URL, API-Key)
│   ├── auth/
│   │   ├── service_account.py   # API-Key -> User/Tenant-Resolution
│   │   └── permission_guard.py  # require_permission() Wrapper
│   ├── tools/
│   │   ├── _base.py             # ToolBase + Antwort-Wrapper + DryRun + Idempotency
│   │   ├── care.py              # get_due_care_tasks, confirm_care_task
│   │   ├── runs.py              # list_planting_runs, create_planting_run, transition
│   │   ├── plants.py            # create_plant(s)_bulk, move_plant, archive_plant, diagnostics, diary
│   │   ├── species.py           # find_or_create_species, get_species_info
│   │   ├── ipm.py               # create_inspection, apply_treatment
│   │   ├── harvest.py           # get_harvest_readiness, record_harvest
│   │   ├── feeding.py           # record_feeding_event
│   │   ├── knowledge.py         # search_plant_knowledge
│   │   ├── tenants.py           # list_tenants
│   │   ├── setup.py             # setup_apartment, setup_growbox, setup_outdoor_garden
│   │   ├── sites.py             # create_site, update_site, list_sites
│   │   ├── locations.py         # create/update/delete_location, bulk
│   │   ├── substrates.py        # create_substrate_batch
│   │   ├── tanks.py             # create_tank
│   │   └── onboarding.py        # apply_starter_kit, list_starter_kits
│   ├── backend_client.py        # httpx AsyncClient gegen Backend-API
│   ├── audit.py                 # MCPAuditLogger (writes mcp_audit_log)
│   ├── idempotency.py           # IdempotencyStore (ArangoDB-backed)
│   └── server.py                # MCP-Protokoll-Handler (Anthropic SDK)
└── tests/
    ├── unit/
    └── integration/             # gegen Test-Backend
```

### 4.2 Tool-Registrierung (Pattern)

```python
from app.tools._base import ToolBase, WriteToolBase, mcp_tool

# Read-Tool
@mcp_tool(name="get_due_care_tasks", permission="mcp.read")
class GetDueCareTasks(ToolBase):
    """Liefert heute/die naechsten N Tage faellige Pflegeaufgaben."""

    class Input(BaseModel):
        days_ahead: int = Field(0, ge=0, le=14)
        urgency: Literal["all", "high", "critical"] = "all"

    async def run(self, ctx: ToolContext, args: Input) -> Output:
        result = await ctx.backend_client.get(
            f"/t/{ctx.tenant_slug}/care/dashboard",
            params=args.model_dump(),
        )
        return self._build_output(result)


# Write-Tool mit Dry-Run + Idempotency
@mcp_tool(name="create_plants_bulk", permission="mcp.write", destructive=False)
class CreatePlantsBulk(WriteToolBase):
    """Legt mehrere Pflanzen derselben Species in einem Aufruf an."""

    class Input(BaseModel):
        species_key: str
        cultivar_key: str | None = None
        count: int = Field(ge=1, le=100)
        location_key: str
        initial_phase: PlantPhase = PlantPhase.SEEDLING
        run_key: str | None = None
        dry_run: bool = False
        idempotency_key: str | None = None

    async def run(self, ctx: ToolContext, args: Input) -> Output:
        if args.dry_run:
            preview = await self._preview(ctx, args)
            return self._dry_run_response(args, preview)

        async with ctx.idempotency.guard(args.idempotency_key, args) as guard:
            if guard.replayed:
                return guard.cached_result
            result = await ctx.backend_client.post(
                f"/t/{ctx.tenant_slug}/plants/bulk",
                json=args.model_dump(exclude={"dry_run", "idempotency_key"}),
            )
            return guard.store(self._build_output(result))
```

### 4.2.1 Transaktionssemantik fuer Macro-Tools

Macro-Tools (`setup_apartment`, `setup_growbox`, `setup_outdoor_garden`) erzeugen mehrere Ressourcen. Implementierung muss garantieren:

- **All-or-nothing:** Bei Fehler in einem Schritt werden bereits angelegte Ressourcen via Compensating Actions zurueckgerollt. Nutzung der ArangoDB-Transactions API auf Backend-Seite.
- **Partial-Result-Reporting:** Im Erfolgsfall enthaelt `data.created` eine vollstaendige Liste; im Fehlerfall enthaelt `data.attempted` was vorgesehen war und `data.rolled_back: true`.
- **Idempotenz auch bei Macros:** `idempotency_key` deckt die gesamte Macro-Operation ab, nicht einzelne Sub-Schritte.

### 4.3 Authentifizierung

1. MCP-Client uebergibt API-Key des Service Accounts ueber den Transport (HTTP-Header `X-API-Key` oder stdio-Init-Argument).
2. `ServiceAccountAuthenticator` validiert Key gegen Backend (`POST /auth/service-accounts/validate`), erhaelt User/Tenant.
3. Auth-Context wird pro Tool-Aufruf an `PermissionGuard` weitergereicht.
4. Bei abgelaufenem oder rotiertem Key: MCP-Fehler mit code `auth.expired`, Client soll Reconnect ausloesen.

IP-Allowlist und Rate-Limit gemaess REQ-023 v1.7 werden auf Backend-Seite durchgesetzt — der MCP-Server propagiert nur die Client-IP via `X-Forwarded-For`.

### 4.4 Permission-Matrix-Bindung

Jedes Tool deklariert eine von drei Permissions: `mcp.read`, `mcp.write` oder `mcp.setup`. Diese werden in REQ-024 als neue Permissions ergaenzt und sind separat von App-Permissions und voneinander vergebbar:

| Rolle/Account-Typ | mcp.read | mcp.write | mcp.setup |
|-------------------|----------|-----------|-----------|
| Service Account "diagnose-bot" (Read-Only Assistent) | ✓ | ✗ | ✗ |
| Service Account "daily-bot" (Pflege-Quittierung, Diary, Inspections) | ✓ | ✓ | ✗ |
| Service Account "setup-agent" (einmaliges Onboarding) | ✓ | ✓ | ✓ |
| Personal Account (interaktiv) | nicht zugewiesen | nicht zugewiesen | nicht zugewiesen |

**Begruendung Drei-Stufen-Modell:** `mcp.setup` ist die destruktivste Klasse (Site-/Location-Loeschung kann ganze Pflanzdaten-Hierarchien zerstoeren). Setup-Aktionen sind typischerweise einmalig (Onboarding-Tag) — der Tenant-Admin kann die Permission danach widerrufen, ohne Tagesbetriebs-Tools zu blockieren.

### 4.5 Streaming & Notifications

Lange Operationen (z. B. zukuenftige `generate_growing_report`) nutzen MCP-Notifications fuer Fortschritt. Cut 1.0 enthaelt keine Stream-Tools — Hook in `ToolBase.emit_progress()` ist vorbereitet.

### 4.6 Audit & DSGVO

- Jeder Tool-Aufruf erzeugt einen `mcp_audit_log`-Eintrag.
- `input_hash` statt Klartext-Args, um Aussage-Daten (z. B. Diary-Texte) nicht in Logs zu spiegeln.
- Endpoint `GET /privacy/mcp-activity` (REQ-025 Erweiterung): Nutzer kann Audit-Log seiner Service-Accounts abrufen.
- Audit-Log-Retention 90 Tage, danach Loeschung.
- Idempotency-Records werden nach 24 h via ArangoDB-TTL automatisch entfernt.

## 5. API-Erweiterung Backend

Folgende neue oder erweiterte Backend-Endpoints werden benoetigt (kein eigener REQ noetig — Erweiterung der jeweiligen REQs):

| Endpoint | Quelle-REQ | Status |
|----------|-----------|--------|
| `POST /auth/service-accounts/validate` | REQ-023 | neu |
| `GET /t/{slug}/locations/{key}/plants` | REQ-002 | erweitert |
| `POST /t/{slug}/locations/bulk` | REQ-002 | neu |
| `POST /t/{slug}/plants/bulk` | REQ-013 | neu |
| `PATCH /t/{slug}/plants/{key}/location` | REQ-002/013 | neu |
| `POST /t/{slug}/plants/{key}/archive` | REQ-013 | neu |
| `GET /t/{slug}/harvest/readiness` | REQ-007 | neu (Aggregat) |
| `GET /privacy/mcp-activity` | REQ-025 | neu |
| `POST /knowledge/search` | REQ-031 | bereits geplant |

## 6. Konfiguration

```yaml
# helm/kamerplanter/values.yaml
mcpServer:
  enabled: false                  # opt-in
  transport: http                 # http | stdio (stdio nur Dev)
  backend:
    url: http://kamerplanter-backend:8000
  auth:
    requireServiceAccount: true   # immer true in 1.0
  audit:
    retentionDays: 90
  idempotency:
    ttlHours: 24
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi
```

## 7. Abhaengigkeiten

| REQ | Abhaengigkeitstyp | Impact |
|-----|-------------------|--------|
| REQ-023 v1.7 (Service Accounts) | hart | ohne Service-Account-Auth kein MCP-Server |
| REQ-024 v1.4 (Permission-Matrix) | hart | Tool-Permissions `mcp.read`/`mcp.write`/`mcp.setup` ergaenzen |
| REQ-025 v1.0 (DSGVO) | hart | Audit-Log + Privacy-API |
| REQ-031 v1.0 (KI-Assistent / RAG) | weich | `search_plant_knowledge`-Tool nutzt RAG-Infrastruktur; ohne RAG nutzbar (Tool faellt weg) |
| REQ-002 v4.2 (Standortverwaltung) | weich | Setup-Tools, WaterProfile, Location-CRUD |
| REQ-013 v2.0 (Pflanzdurchlauf) | weich | Tools `list_planting_runs`, `create_plants_bulk`, Diary |
| REQ-019 (Substratverwaltung) | weich | `create_substrate_batch`, `setup_growbox` |
| REQ-014 v1.4 (Tankmanagement) | weich | `create_tank`, `record_feeding_event` |
| REQ-022 v2.4 (Pflegeerinnerungen) | weich | `get_due_care_tasks`, `confirm_care_task` |
| REQ-006 v2.7 (Aufgabenplanung) | weich | `list_overdue_tasks` |
| REQ-007 v1.0 (Erntemanagement) | weich | `get_harvest_readiness`, `record_harvest` |
| REQ-010 v1.0 (IPM) | weich | `create_inspection`, `apply_treatment`, Karenz-Daten |
| REQ-020 v1.1 (Onboarding) | weich | `apply_starter_kit`, `list_starter_kits` |
| NFR-001 (5-Layer-Architektur) | hart | MCP-Server ist eigene Top-Level-Komponente, ruft Backend ueber HTTP — keine direkte DB-Kopplung |
| NFR-008 (Tests) | hart | Unit + Integrationstests gegen Test-Backend |
| NFR-011 (Retention) | hart | mcp_audit_log Retention 90d |

## 8. Akzeptanzkriterien (Definition of Done)

### 8.1 Funktional — Read & Tagesbetrieb

- **AC-1:** Ein registrierter Service Account kann sich per API-Key am MCP-Server authentifizieren und alle ihm via Permission-Matrix erlaubten Tools aufrufen.
- **AC-2:** Der MCP-Server lehnt Tool-Aufrufe ohne erforderliche Permission (`mcp.read`/`mcp.write`/`mcp.setup`) mit Fehlercode `permission.denied` ab.
- **AC-3:** `get_due_care_tasks(days_ahead=0)` liefert die heute faelligen Pflegeaufgaben des Tenants in <500 ms (P95) bei 100 Pflanzen.
- **AC-4:** `search_plant_knowledge("Spinnmilben Bekaempfung biologisch")` liefert mindestens 3 RAG-Treffer aus `spec/knowledge/rag/`, jeweils mit Score >= 0.6.
- **AC-5:** `get_plant_diagnostics(plant_key)` aggregiert Sensor-Snapshot, IPM-Status, Karenz und letzte Care-Events in einer Antwort und braucht keine zweite Tool-Round-Trip vom LLM.
- **AC-6:** `confirm_care_task` schreibt eine `CareConfirmation` und der naechste `get_due_care_tasks`-Aufruf zeigt die Aufgabe nicht mehr.
- **AC-7:** `transition_planting_run` respektiert den `HSTValidator` (REQ-006) und blockiert verbotene Phasenruecksprunge mit Fehlercode `validation.phase`.

### 8.2 Funktional — Setup-Tools

- **AC-8:** `setup_apartment` mit 3 Raeumen legt 1 Site + 3 Locations in einer Transaktion an. Bei Teilfehler wird die gesamte Operation rolled-back (kein Half-State).
- **AC-9:** `setup_growbox` fuer eine 80×80-Box mit 4 Slots erzeugt Site (falls neu), Location (Growzelt), 4 Slot-Locations und eine SubstrateBatch — alles in einem Tool-Aufruf.
- **AC-10:** `setup_outdoor_garden` mit Tap-Water-Profil (EC 0.5, pH 7.2) speichert das Wasserprofil korrekt am Site-Knoten und es ist anschliessend ueber `list_sites` (Read-Tool) abrufbar.
- **AC-11:** `delete_location` mit aktiven Pflanzen liefert ohne `force=true` den Fehlercode `validation.location_has_plants` mit der Anzahl betroffener Pflanzen — keine versehentliche Loeschung durch das LLM.
- **AC-12:** `apply_starter_kit("indoor-tomate")` liefert dieselben Ressourcen wie der UI-Wizard (REQ-020) und ist nach Abschluss ueber `list_planting_runs` sichtbar.

### 8.3 Funktional — Pflanzen-Erfassung

- **AC-13:** `find_or_create_species("Solanum lycopersicum", "San Marzano")` findet eine bestehende Species und gibt deren `species_key` zurueck statt zu duplizieren.
- **AC-14:** `create_plants_bulk(count=6, ...)` legt 6 Pflanzen an und gibt eine Liste mit 6 Pro-Eintrag-Status-Objekten zurueck. Bei Teilfehler (z. B. 5 erfolgreich, 1 fehlgeschlagen wegen Slot-Full) ist der Status pro Eintrag korrekt gesetzt; erfolgreiche Pflanzen werden persistiert.
- **AC-15:** `move_plant` zu einem Slot mit voller Belegung (REQ-002 Slot-Capacity) liefert `validation.slot_full`; die Pflanze bleibt am alten Standort.
- **AC-16:** `archive_plant` setzt den Status auf `archived`, entfernt die Pflanze aus aktiven Listen, behaelt aber Diary, Harvest- und Treatment-Historie (NFR-011, REQ-025).
- **AC-17:** `create_planting_run` mit Mono-Konfiguration und 6 Pflanzen erzeugt Run + 6 PlantingRunEntries; Mixed-Culture wird gemaess REQ-013 v2.0 abgelehnt.

### 8.4 Schreibzugriffs-Sicherheit

- **AC-18:** Mit `dry_run=true` wird kein einziger DB-Write durchgefuehrt (verifiziert via Audit-Log: `status="dry_run"` und kein Folge-Log-Eintrag mit `status="ok"`).
- **AC-19:** Zwei Aufrufe desselben Schreibtools mit identischem `idempotency_key` innerhalb 24 h ergeben identische Ergebnis-IDs und legen nur eine Ressource an (Test fuer `create_plant`, `create_plants_bulk`, `setup_apartment`).
- **AC-20:** Bei Fehler waehrend einer Macro-Transaktion (`setup_growbox`) bleibt keine Teil-Hierarchie zurueck — verifiziert per Test mit absichtlich invalider Slot-Anzahl.
- **AC-21:** Schreibtools sind im MCP-Tool-Schema mit `annotations.destructive: true` markiert, wo sie loeschen oder Zustand zerstoeren — Claude Desktop kann den Nutzer warnen.
- **AC-22:** Idempotency-Records werden nach 24 h via ArangoDB-TTL automatisch entfernt.

### 8.5 Sicherheit & Datenschutz

- **AC-S1:** Cross-Tenant-Zugriff ist unmoeglich — ein Service Account von Tenant A kann ueber kein Tool Daten von Tenant B sehen (nachgewiesen via Tests).
- **AC-S2:** API-Keys erscheinen niemals im Audit-Log oder in Fehlermeldungen.
- **AC-S3:** Ein Nutzer kann ueber `GET /privacy/mcp-activity` alle MCP-Aufrufe seiner Service-Accounts der letzten 90 Tage einsehen.
- **AC-S4:** `mcp_audit_log`-Eintraege aelter als 90 Tage werden vom Retention-Master-Task (NFR-011) geloescht.
- **AC-S5:** Tool-Argumente werden vor dem Logging gehasht — keine Diary-Texte oder Symptom-Beschreibungen im Klartext-Log.
- **AC-S6:** Ein Service Account ohne `mcp.setup`-Permission kann ueber kein Tool eine `delete_location` ausloesen — selbst nicht durch indirekte Macros.

### 8.6 Qualitaet & Tests

- **AC-T1:** Unit-Test-Coverage >= 80% in `src/mcp-server/app/`.
- **AC-T2:** Integrationstest pro Tool gegen Test-Backend (alle ~30 Tools).
- **AC-T3:** End-to-End-Test mit echtem Claude Desktop / mcp-inspector als Client (Smoke-Test: Wohnung anlegen → 3 Pflanzen → Pflege quittieren).
- **AC-T4:** Ruff + mypy clean.

### 8.7 Deployment

- **AC-D1:** Helm-Chart `mcpServer.enabled=true` startet einen lauffaehigen Pod, der ueber Service erreichbar ist.
- **AC-D2:** Mit `mcpServer.enabled=false` (Default) ist die Komponente nicht im Cluster — Kamerplanter funktioniert unveraendert.
- **AC-D3:** Dokumentation in `docs/` enthaelt eine Konfigurations-Anleitung fuer Claude Desktop (`claude_desktop_config.json`-Beispiel) und Claude Code.

### 8.8 GIVEN/WHEN/THEN — Beispiel-Szenarien

**Szenario 1: LLM fragt nach faelligen Aufgaben**
- **GIVEN** ein Tenant mit 5 Pflanzen, von denen 3 heute Wasser brauchen
- **AND** ein Service Account mit `mcp.read`-Permission
- **WHEN** der MCP-Client `get_due_care_tasks(days_ahead=0)` aufruft
- **THEN** liefert das Tool 3 Eintraege mit summary `"3 Pflanzen muessen heute gegossen werden"` und data inklusive Pflanzen-Namen, Standort und Dringlichkeit.

**Szenario 2: Wohnung per Sprachdialog einrichten**
- **GIVEN** ein leerer Tenant und ein Service Account mit `mcp.setup`
- **WHEN** der Client `setup_apartment(rooms=[Wohnzimmer, Schlafzimmer, Bad], dry_run=true)` aufruft
- **THEN** liefert das Tool eine Vorschau mit 1 Site + 3 Locations, ohne irgendwas zu persistieren
- **AND** der nachfolgende Aufruf mit `dry_run=false, idempotency_key="setup-001"` legt die Ressourcen an
- **AND** ein Wiederholungs-Aufruf mit demselben `idempotency_key` liefert `idempotent_replay: true` und legt nichts Neues an.

**Szenario 3: 6 Pflanzen mit unbekannter Sorte erfassen**
- **GIVEN** Tenant mit Hochbeet "Beet 2" und Service Account mit `mcp.write`
- **AND** Species "Solanum lycopersicum" existiert global, Cultivar "San Marzano" noch nicht
- **WHEN** der Client `find_or_create_species("Solanum lycopersicum", "San Marzano")` aufruft
- **THEN** wird der Cultivar neu angelegt und der Key zurueckgegeben
- **WHEN** der Client `create_plants_bulk(count=6, location_key=Beet 2, ...)` aufruft
- **THEN** entstehen 6 Pflanzen mit korrekter Species/Cultivar/Standort-Zuordnung.

**Szenario 4: Read-Only-Account versucht Schreibzugriff**
- **GIVEN** ein Service Account "diagnose-bot" mit nur `mcp.read`
- **WHEN** der Client `confirm_care_task(...)` aufruft
- **THEN** lehnt der Server mit Fehlercode `permission.denied` ab und schreibt einen Audit-Log-Eintrag mit `status="denied"`.

**Szenario 5: Setup-Bot versucht Pflanzen-Standort mit aktiven Pflanzen zu loeschen**
- **GIVEN** Service Account mit `mcp.setup` und Location "Beet 2" mit 3 aktiven Pflanzen
- **WHEN** der Client `delete_location("loc-beet-2")` ohne `force=true` aufruft
- **THEN** lehnt das Tool mit Fehlercode `validation.location_has_plants` ab und nennt die 3 betroffenen Pflanzen
- **AND** bei `force=true` werden die Pflanzen vorher per `archive_plant` archiviert, dann die Location geloescht.

**Szenario 6: Cross-Tenant-Schutz**
- **GIVEN** Service Account aus Tenant "haus" mit `mcp.read`
- **WHEN** der Client `get_planting_run(key="<aus-Tenant-garten>")` aufruft
- **THEN** liefert das Tool `not_found`, NICHT `permission.denied` (kein Tenant-Information-Leak).

**Szenario 7: RAG-Bruecke**
- **GIVEN** ein Tenant ohne aktive Pflanzdurchlaeufe
- **AND** Service Account mit `mcp.read`
- **WHEN** der Client `search_plant_knowledge("Tomate Mischkultur")` aufruft
- **THEN** liefert das Tool RAG-Treffer aus der globalen Wissensbasis (tenant-unabhaengig, keine PII).

## 9. Offene Punkte / Spaetere Erweiterungen

- **Streaming-Tools:** `generate_growing_report(run_key)` als Long-Running mit Progress-Notifications.
- **Resource-Bindings:** MCP unterstuetzt neben Tools auch `resources` (lesbare Inhalte). Pflanzen-Detailseiten als `resource://kamerplanter/plant/{key}` exponieren.
- **MCP-Prompts:** Vordefinierte Prompts ("Tagesabschluss-Report", "Diagnose-Workflow") als MCP-Prompts ausliefern.
- **Sampling-Bridge:** Ueber MCP-`sampling` REQ-031-Antworten an externe Clients zurueckgeben — vermeidet Doppel-LLM-Aufrufe.
- **Bidirektionale HA-Bruecke:** MCP-Tool `trigger_ha_automation(automation_id)` als Aktorik-Schnittstelle (REQ-018).
- **Token-Budget-Optimierung:** Wenn Tool-Antwort > N kB, automatische Zusammenfassung und Pagination-Hint.
