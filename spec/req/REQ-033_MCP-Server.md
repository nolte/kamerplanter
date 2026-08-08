# Spezifikation: REQ-033 - MCP-Server fuer LLM-gestuetzte Garten- und Anbauverwaltung

```yaml
ID: REQ-033
Titel: Model Context Protocol (MCP) Server fuer Kamerplanter
Kategorie: Integration & KI
Fokus: Beides
Technologie: Python 3.14+, FastAPI, Model Context Protocol SDK (Anthropic), ArangoDB, Redis, Pydantic v2
Status: Teilweise umgesetzt (Framework, API-Key-Auth mit Mehrmandanten-Bindung, Audit, Streamable-HTTP-Transport, Bild-Content und 56 Werkzeuge; Rest des Werkzeugkatalogs und die stdio-Bruecke offen, siehe §4.1 und §9)
Version: 1.6
Abhaengigkeit: REQ-001 v4.7 (Stammdaten), REQ-002 v4.3 (Standortverwaltung), REQ-006 v3.0 (Aufgabenplanung), REQ-013 v2.4 (Pflanzdurchlauf), REQ-014 v1.6 (Tankmanagement), REQ-019 v4.1 (Substratverwaltung), REQ-020 v1.6 (Onboarding), REQ-022 v2.8 (Pflegeerinnerungen), REQ-010 v1.4 (IPM), REQ-007 v2.6 (Erntemanagement), REQ-023 v1.10 (Service Accounts), REQ-024 v1.6 (RBAC Permission-Matrix), REQ-025 v1.5 (DSGVO), REQ-031 v2.0 (KI-Assistent / RAG), REQ-049 v1.3 (Rollenvokabular), REQ-050 v1.3 (KI-Analyse von Tagebuch-Eintraegen), NFR-013 v1.3 (Thumbnail-Renditions)
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
- **Permission-gebunden ueber API-Keys (REQ-023):** Authentifizierung ausschliesslich per `kp_`-API-Key — nie per JWT und nie per interaktiver Session. Der Key kann einem **persoenlichen Konto** oder einem **Service Account** gehoeren. Die Permission-Matrix (REQ-024) entscheidet pro Tool-Aufruf, ob Lese-, Schreib- oder Setup-Rechte bestehen.
- **Ein Nutzer sieht ausschliesslich seine eigenen Daten:** Ein persoenlicher Key gewaehrt genau die Mandanten, in denen sein Besitzer aktives Mitglied ist — aufgeloest ueber dieselbe Quelle (`TenantService.list_my_tenants`), auf die auch die REST-API scoped. Ueber MCP ist damit nichts erreichbar, was der Nutzer nicht auch in der Weboberflaeche sieht.
- **Tenant-isoliert, Mandant pro Aufruf:** Ein Key kann mehrere Mandanten umfassen (eigener Garten + Gemeinschaftsgarten). Welcher Mandant gilt, entscheidet das Argument `tenant` pro Tool-Aufruf; der Dispatcher loest es gegen die Mitgliedschaften auf, **bevor** eine Rechtepruefung stattfindet — denn die Rolle ist je Mandant verschieden. Ein fremder Mandant liefert `not_found`, nie `permission.denied`, damit die Schnittstelle keine fremden Mandanten preisgibt.
- **Local-First & optional:** Der Server ist eine eigenstaendige optionale Komponente. Ohne MCP-Server funktioniert Kamerplanter unveraendert.
- **RAG-Bruecke zu REQ-031:** Tool `search_plant_knowledge(query)` ruft die bestehende RAG-Infrastruktur auf — kein paralleles Wissenssystem.
- **Read-Heavy by Default:** Schreibtools (Task-Quittierung, Diary-Eintrag) sind explizit gekennzeichnet und verlangen `mcp.write` — abgeleitet aus der Rolle im handelnden Mandanten (§4.4).
- **DSGVO-konform (REQ-025):** Audit-Log jedes Tool-Aufrufs mit Konto-Key, handelndem Mandanten, Tool-Name, Input-Hash, Output-Size. Keine PII im Log.
- **Streaming-faehig:** Lange Operationen (z. B. `generate_growing_report`) liefern via MCP-Notifications inkrementelle Fortschrittsupdates.

### 1.1 Abgrenzung zu benachbarten REQs

| REQ | Beziehung |
|-----|-----------|
| **REQ-031 (KI-Assistent)** | Komplementaer. REQ-031 ist die *interne* RAG-/Chat-Funktion, in Kamerplanter eingebaut, fuer App-Nutzer. REQ-033 ist die *externe* Schnittstelle, ueber die fremde LLM-Clients Kamerplanter als Tool benutzen. Gemeinsame RAG-Wissensbasis (`spec/knowledge/rag/`). |
| **REQ-030 (Notifications)** | Komplementaer. REQ-030 *pusht* Erinnerungen aus Kamerplanter heraus (HA, E-Mail, Apprise). REQ-033 erlaubt es einem LLM, *aktiv* den Pflege-Stand abzufragen. |
| **REQ-016 (InvenTree)** | Aehnliches Muster: optionale externe Integration. MCP-Server ist nicht InvenTree-spezifisch, sondern protokoll-getrieben. |
| **REQ-023 (API-Keys & Service Accounts)** | Hartes Prerequisite. MCP-Server akzeptiert ausschliesslich `kp_`-API-Keys — persoenliche wie Service-Account-Keys —, nie JWT oder interaktive Sessions. |
| **REQ-024 (Permission-Matrix)** | Jeder Tool-Aufruf wird ueber `require_permission()` geroutet. |

### 1.2 Architekturueberblick

```
+---------------------------+
|  LLM-Client               |
|  (Claude Desktop, Cursor, |
|   Claude Code, custom)    |
+-------------+-------------+
              |
              |  MCP Streamable HTTP (JSON-RPC 2.0 ueber POST)
              v
+---------------------------------------------+
|  Kamerplanter Backend (FastAPI)              |
|                                              |
|  +----------------------------------------+  |
|  | api/v1/mcp/  Transport + Enabled-Gate  |  |
|  +-------------------+--------------------+  |
|                      v                       |
|  +----------------------------------------+  |
|  | McpAuthenticator                       |  |  <-- API-Key (persoenlich | Service)
|  | (REQ-023: Key, IP-Allowlist, Ratelimit)|  |
|  +-------------------+--------------------+  |
|                      v                       |
|  +----------------------------------------+  |
|  | ToolDispatcher                         |  |
|  |  Permission-Bindung (REQ-024)          |  |
|  |  Dry-Run / Idempotency / Audit         |  |
|  +-------------------+--------------------+  |
|                      v                       |
|  +----------------------------------------+  |
|  | Tool-Handler (Registry)                |  |
|  +-------------------+--------------------+  |
|                      |  direkter Aufruf      |
|                      v                       |
|  +----------------------------------------+  |
|  | Domain-Services / Repositories         |  |
|  | (dieselben wie hinter der REST-API)    |  |
|  +----------------------------------------+  |
+----------------------+-----------------------+
                       v
            ArangoDB / Valkey / RAG
```

**Transport-Modi:**

| Modus | Transport | Use-Case | Stand |
|-------|-----------|----------|-------|
| **Streamable HTTP** | HTTPS | Self-Hosted-Deployments — Clients verbinden sich mit dem MCP-Endpunkt `/api/v1/mcp` | umgesetzt (§4.3a) |
| **stdio** | stdin/stdout | Lokal ueber Claude-Desktop-/Claude-Code-Konfiguration — Prozess wird vom Client gestartet | **nicht umgesetzt**; vorgesehen als schlanker Bridge-Client beim Nutzer, der stdio auf `/mcp/rpc` durchreicht (§9) |

## 2. Tool-Inventar (Cut 1.0)

Die initiale Tool-Palette ist bewusst kuratiert (~30 Tools), abgeleitet aus den haeufigsten LLM-Use-Cases mit Schwerpunkt **Onboarding (Wohnung/Garten einrichten)**, **Bestandsaufnahme (Pflanzen erfassen)** und **Tagesbetrieb (Pflege, Diagnose)**. Erweiterung erfolgt nach Nutzungsmessung.

**Mandanten-Parameter:** Jedes Tool, das nutzereigene Daten beruehrt, akzeptiert `tenant` (Slug des handelnden Mandanten). Bei genau einer Mitgliedschaft darf es entfallen, bei mehreren ist es Pflicht — der Server waehlt nie selbst einen aus. Tools auf globalen Katalogdaten (`list_species`, `get_species_info`) und auf kontobezogenen Daten (`list_tenants`, `get_mcp_activity`) fuehren den Parameter nicht. Die Aufloesung passiert zentral im Dispatcher, nicht im Tool (§4.3).

**Schreibzugriffs-Philosophie:** Schreibtools folgen vier festen Mustern, damit ein LLM sie sicher und idempotent verwenden kann:

1. **Dry-Run-Vorschau:** Jedes Schreibtool akzeptiert `dry_run: bool = false`. Bei `true` wird nur der geplante Effekt zurueckgeliefert, nichts persistiert. Pflicht fuer LLM-Bestaetigungs-Workflows.
2. **Idempotency-Key:** Jedes Schreibtool akzeptiert optionalen `idempotency_key: str`. Identische Keys innerhalb 24 h liefern das urspruengliche Ergebnis statt Duplikat anzulegen — kritisch bei LLM-Retries.
3. **Bulk-Faehig wo sinnvoll:** "Lege 6 Tomaten an" muss in einem Tool-Aufruf gehen, nicht 6× hintereinander. Bulk-Tools haben Suffix `_bulk` und liefern Pro-Eintrag-Status.
4. **Macro-Tools fuer Onboarding:** Hochstufige Setup-Tools (`setup_apartment`, `setup_growbox`) fassen Site + Locations + Slots in einem Aufruf zusammen — der LLM-User-Dialog wird kurz und natuerlich.

### 2.1 Read-Tools (Permission `mcp.read`)

| Tool | Zweck | Backend-Endpoints (intern) |
|------|-------|---------------------------|
| `list_tenants` | Die Mandanten, in denen der Key handeln darf, samt Rolle je Mandant — liefert die Slugs fuer den `tenant`-Parameter | aus dem `McpPrincipal` (keine eigene Abfrage) |
| `get_due_care_tasks` | Heute / die naechsten N Tage faellige Pflegeaufgaben, gruppiert nach Dringlichkeit | `GET /t/{slug}/care/dashboard` |
| `list_planting_runs` | Aktive Pflanzdurchlaeufe inkl. Phase, Standort, Dauer | `GET /t/{slug}/planting-runs?status=active` |
| `get_planting_run` | Detaildaten zu einem Run: Phase, naechste Tasks, juengste Sensor-/Care-Events, Karenz-Status | `GET /t/{slug}/planting-runs/{key}` (+ Aggregation) |
| `list_plants` | Pflanzen des Mandanten auflisten, optional nach Name/Art gefiltert — loest einen Pflanzennamen in den `plant_key` auf, den alle Schreibwerkzeuge verlangen | `plant_instance_service.list_plants` |
| `get_plant` | Stammdaten einer Pflanze: Art (inkl. aufgeloestem Namen), Phase, Standort, Lebenszyklus-Daten sowie das **Substrat** der Instanz (`substrate_key` plus aufgeloester `substrate_type`/`substrate_name`) — ohne diesen Bezug ist `list_substrates` ein Katalog, den kein Werkzeug an eine Pflanze bindet. Ist `current_phase_key` null, ergaenzt das Werkzeug ausserdem `phase_state` (denselben Wert wie `get_plant_phase_status` via `_classify_phase_state`: `never_initialised` / `unresolved` / `between_cycles`; `unknown`, wenn der Phasendienst nicht erreichbar ist), damit die Detailansicht die drei Situationen hinter dem null-Wert ohne zweiten Werkzeugaufruf unterscheidet | `plant_instance_service.get_plant` (+ `phase_service` nur bei null-Phase) |
| `get_plant_care_log` | Quittierte Pflegehistorie einer Pflanze (Giessprotokoll via `reminder_type=watering`) | `care_reminder_service.get_confirmation_history` |
| `list_diary_entries` | Tagebuch-Eintraege durchsehen — filterbar nach Pflanze, Art, Eintragstyp, Tag, Analyse-Zustand und Zeitraum, **neueste zuerst** (`created_at` absteigend, `_key` als Tiebreaker). Liefert je Zeile Titel, Tags und **`measurements`**, aber **keinen** Freitext (§7.3 REQ-050: dafuer `get_diary_entry`) und kennt bewusst keine Volltextsuche | `plant_diary_service.list_overview` |
| `list_plants_at_location` | Alle Pflanzen an einem Standort/Beet/Slot | `plant_instance_service.list_plants` + Filter |
| `get_plant_diagnostics` | Aggregierter Diagnose-Snapshot fuer eine Pflanze: Sensorwerte, EC/pH-Trend, IPM-Inspections, Karenz, juengste Tips | mehrere Endpoints, im Tool aggregiert |
| `list_nutrient_plans` | Verfuegbare Naehrstoffplaene — eigene plus global geseedete Vorlagen (Hybrid-Katalog, REQ-004) | `nutrient_plan_service.list_plans` |
| `get_nutrient_plan` | Ein Plan mit seinen Phasen-Eintraegen: NPK-Verhaeltnis, Ziel-EC, Sekundaernaehrstoffe, Wochenfenster | `nutrient_plan_service.get_plan` + `get_phase_entries` |
| `get_plant_nutrient_plan` | Der einer Pflanze zugewiesene Plan samt Phasenzielen | `nutrient_plan_service.get_plant_plan` |
| `get_sowing_calendar` | Aussaat-, Auspflanz- und Erntefenster je Art fuer ein Jahr, verschoben gegen die Frostdaten des Standorts (REQ-015) | `calendar_service.get_sowing_calendar` |
| `list_pests` / `get_pest` | Schaedlingskatalog mit Filter ueber Namen **und Schadbild**; das Detail liefert Gegenmassnahmen nach IPM-Hierarchie plus die passenden **Nuetzlinge** (REQ-010) | `ipm_service.list_pests` / `get_pest_detail` |
| `list_diseases` / `get_disease` | Krankheitskatalog: Erreger, Inkubationszeit, ausloesende Bedingungen, betroffene Pflanzenteile | `ipm_service.list_diseases` / `get_disease` |
| `get_treatment` | Behandlung im Detail — inkl. **Karenzzeit** (`safety_interval_days`), Schutzausruestung und Anwendung | `ipm_service.get_treatment` |
| `get_plant_inspections` | IPM-Inspektionshistorie einer Pflanze: Befallsdruck, Funde, Symptome | `ipm_service.get_inspections` |
| `list_fertilizers` | Verfuegbare Duenger inkl. EC-Beitrag je ml und Maximaldosis — liefert die `fertilizer_keys` des Rechners | `fertilizer_service.list_fertilizers` |
| `calculate_mixing_protocol` | Duengerechner: Dosierung je Produkt fuer Zielvolumen und Ziel-EC ueber die EC-Budget-Pipeline (REQ-004-A), inkl. Mischreihenfolge | `EcBudgetCalculator` |
| `search_plant_knowledge` | Volltext-/Vektor-Suche in Wissensbasis (RAG ueber `spec/knowledge/rag/`) | `POST /knowledge/search` (REQ-031) |
| `get_species_info` | **Vollstaendige** Stammdaten einer Art: Aussaat-/Ernte-/Bluetefenster, Winterhaerte, Frostempfindlichkeit, Naehrstoffbedarf, Toxizitaet, Anbaueigenschaften, Companion Planting und die zugehoerigen Sorten | `species_service.get_species` + `list_cultivars` + `get_compatible_species` |
| `list_cultivars` / `get_cultivar` | Sorten einer Art: Zuechter, Merkmale, Saatgut-Typ, Tage bis zur Reife | `species_service.list_cultivars` / `get_cultivar` |
| `list_substrates` | Substratkatalog (REQ-019) | `substrate_service.list_substrates` |
| `list_overwintering_profiles` | Ueberwinterungsprofile: Schutzmethode, Lagerbedingungen, Zeitpunkte (REQ-047) | `overwintering_profile_service.list_profiles` |
| `list_starter_kits` | Onboarding-Starter-Kits des Mandanten (REQ-020) | `starter_kit_service.list_kits_for_tenant` |
| `list_phase_definitions` | Wachstumsphasen-Definitionen der Lifecycle-Engine (REQ-003) — die **Bausteine**, nicht die Abfolgen | `phase_sequence_service.list_definitions` |
| `get_species_phase_sequence` | Die aufgeloeste PhaseSequence einer Art: `cycle_type`, `is_repeating`, `dormancy_required` sowie die geordneten Entries mit `effective_duration_days`, `is_terminal` und `allows_harvest`. Dazu abgeleitet `total_duration_days` und `terminates_in_harvest` — die Konjunktion, an der ein terminaler Ernte-Zyklus erkennbar wird (REQ-003) | `phase_sequence_service.get_sequence_by_species` + `get_full_sequence` |
| `list_phase_sequences` | Der PhaseSequence-Katalog mit Topologie je Abfolge (optional inkl. Entries) — eine falsche Zuordnung zu *diagnostizieren* reicht nicht, die richtige muss **benennbar** sein | `phase_sequence_service.list_sequences` + `get_full_sequence` |
| `list_species_by_phase_sequence` | Rueckwaertssuche: alle Arten an einer Abfolge. Macht aus einer Einzelbeschwerde einen systemischen Befund (Vorlagen-Kollision) | `phase_sequence_service.get_species_for_sequence` |
| `get_species_lifecycle` | LifecycleConfig einer Art: `cycle_type`, `cultivation_cycle_type`, `grown_as_annual`, `flowering_strategy`, `growth_determinacy`, `typical_lifespan_years`, `dormancy_required`, `phase_sequence_key`. Eine **fehlende** Config wird als Befund gemeldet statt als 404 — sie ist genau das, was die Resolver-Fallback-Regel ausloest | `phase_service.get_lifecycle_by_species` |
| `get_plant_phase_status` | Phasenstand einer Instanz: `days_in_phase`, `next_phase`, `cycle_number`, `has_harvest_phase` — plus `phase_state` (`never_initialised` / `unresolved` / `between_cycles` / `in_phase`), das die drei Situationen trennt, die `current_phase_key: null` zusammenwirft | `phase_service.get_current_phase` + `get_phase_history` |
| `get_plant_phase_history` | Phasenverlauf einer Instanz mit `transition_reason`, Ein-/Austrittsdatum, tatsaechlicher Dauer und `cycle_number` | `phase_service.get_phase_history` |
| `list_hardiness_zones` | Winterhaertezonen mit Temperaturbereichen | `hardiness_zone_service.list_zones` |
| `search_glossary` | Fachbegriffe aus dem projekteigenen Glossar (VPD, EC, Karenz, …) | `glossary_service.list_terms` |
| `list_overdue_tasks` | Ueberfaellige Tasks (alle Sources: REQ-006, REQ-022) | `GET /t/{slug}/tasks?status=overdue` |
| `get_harvest_readiness` | Erntebereitschaftssignale aller aktiven Runs (Karenz, Indikatoren) | `GET /t/{slug}/harvest/readiness` |

### 2.2 Write-Tools — Tagesbetrieb (Permission `mcp.write`)

| Tool | Zweck | Backend-Endpoints (intern) |
|------|-------|---------------------------|
| `confirm_care_task` | Pflegeaufgabe quittieren ("ich habe gegossen") | `POST /t/{slug}/care/confirmations` |
| `add_plant_diary_entry` | Freitext-Eintrag zur Pflanze (REQ-013 v2.0 PlantDiaryEntry), **ohne** `photo_refs` — MCP hat keinen Upload-Weg, und SEC-003 laesst nur den Hochladenden (oder die Leitung) ein Foto anhaengen | `POST /t/{slug}/plant-instances/{key}/diary` |
| `create_inspection` | IPM-Inspektion mit Symptomen anlegen | `POST /t/{slug}/ipm/inspections` |
| `transition_planting_run` | Phase eines Runs vorruecken (sofern HSTValidator zustimmt) | `POST /t/{slug}/planting-runs/{key}/transition` |
| `record_feeding_event` | Duenge-Vorgang erfassen (Menge, EC/pH, Tank) | `POST /t/{slug}/feeding-events` |
| `record_harvest` | Ernte-Eintrag mit Frischgewicht + Quality-Notes | `POST /t/{slug}/harvest/batches` |
| `apply_treatment` | IPM-Treatment anwenden (Karenz-Gate aktiv) | `POST /t/{slug}/ipm/treatment-applications` |
| `assign_nutrient_plan` | Einen **bestehenden** Naehrstoffplan an eine Pflanze binden — **kein** Plan-Editor | `POST /t/{slug}/plant-instances/{key}/nutrient-plan` |
| `transition_plant_phase` | Die Phase einer **Instanz** setzen oder korrigieren. Das Ziel wird gegen die PhaseSequence geprueft, die die Art *dieser* Pflanze aufloest — nicht gegen die Gesamtmenge aller Phasenschluessel, sonst landet die Pflanze in einer Phase, aus der ihr Lebenszyklus nie wieder herausfindet | `POST /t/{slug}/plant-instances/{key}/phases/transition` |

`assign_nutrient_plan` kam nachtraeglich hinzu (Issue #931). AC-25 spricht von "dem einer Pflanze zugewiesenen Plan" als bestehendem Zustand, waehrend die Palette nur die lesende Seite kannte — die Zuweisung kam also von einer Stelle, die die MCP-Oberflaeche nicht erreichte, und jede Plan-Empfehlung eines Agenten endete als Handanweisung, deren Befolgung er nie nachpruefen konnte. Plaene zu **verfassen** bleibt bewusst ausserhalb: Phasenfenster, Produktdosen und Mischreihenfolge sind Redaktionsarbeit mit einer dafuer gebauten Oberflaeche.

### 2.2a Werkzeuge fuer die Tagebuch-KI-Analyse (REQ-050)

REQ-050 laesst einen **externen, vom Nutzer betriebenen** Agenten markierte Tagebuch-Eintraege
analysieren. Kamerplanter ruft dabei selbst kein Sprachmodell auf — es stellt Daten bereit und
nimmt ein Ergebnis entgegen. Diese fuenf Werkzeuge sind der vollstaendige Vertrag dafuer; ihre
Ein- und Ausgaben, Fehlerfaelle und Grenzen sind normativ in **REQ-050 §4** beschrieben.

| Tool | Permission | Zweck |
|------|-----------|-------|
| `list_pending_diary_analyses` | `mcp.read` | Arbeitsvorrat: markierte Eintraege ohne Freitext und ohne Bilder |
| `get_diary_entry` | `mcp.read` | Eintrag samt Pflanzenkontext, **ohne** Bilddaten |
| `get_diary_entry_photos` | `mcp.read` | Die Fotos des Eintrags als **Bild-Content** (§4.3b) |
| `claim_diary_analysis` | `mcp.write` | Eintrag exklusiv beanspruchen (Vergleiche-und-Setze auf `_rev` + Lease) |
| `submit_diary_analysis` | `mcp.write` | Ergebnis am Eintrag persistieren |

`get_diary_entry_photos` ist das erste Werkzeug ueberhaupt, das etwas anderes als Text
zurueckgibt, und erzwingt deshalb die Protokoll-Erweiterung in §4.3b.

### 2.3 Write-Tools — Setup & Stammdaten (Permission `mcp.setup`)

Die `mcp.setup`-Permission ist getrennt von `mcp.write`, damit ein "Diary-Bot" nicht versehentlich Standorte loescht.

> **Abweichung Ist-Zustand:** Die hier beschriebene gezielte Einzelvergabe ("Tenant-Admin gibt einem Account `mcp.setup` einmalig fuers Onboarding und widerruft danach") ist **nicht** umgesetzt. `mcp.setup` haengt an der Rolle `admin` im jeweiligen Mandanten (§4.4); ein temporaeres Anheben und Zuruecknehmen ginge heute nur ueber einen Rollenwechsel. Siehe §9.

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
| `assign_species_phase_sequence` | Eine Art an eine **bestehende** PhaseSequence binden — **kein** Sequence-Editor | `PUT /species/{key}/lifecycle` (Feld `phase_sequence_key`) |

`assign_species_phase_sequence` steht hier und nicht unter §2.2, obwohl es keine Standorte anfasst: Arten und PhaseSequences sind **globale** Katalogdaten. Eine einzige Bindung aendert den Zeitplan aller Pflanzen dieser Art in *jedem* Mandanten, was ein `mcp.write`-Diary-Bot nicht koennen soll. Sequences zu **definieren** — Entries ordnen, Dauern setzen, `is_terminal`/`allows_harvest` vergeben — bleibt bewusst ausserhalb der Palette, dieselbe Linie, die #931 fuer Naehrstoffplaene zieht.

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

`summary` ist eine 1-Satz-Zusammenfassung fuer das LLM, `data` das strukturierte Ergebnis, `links` zeigen dem Endnutzer, wo er Details findet. Die `links` eines mandantenbezogenen Tools tragen den Slug des **aufgeloesten** Mandanten (`/t/{slug}/...`), nie den rohen Argumentwert.

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

> **Das ist die Innenansicht, nicht die Drahtform.** Die hier gezeigten Objekte sind der Inhalt
> von `structuredContent` in der MCP-Antwort — **nicht** die oberste Ebene dessen, was der Client
> empfaengt. Auf dem Draht liegt darum herum die MCP-Standardhuelle:
>
> ```json
> {
>   "content": [{ "type": "text", "text": "<summary>" }],
>   "structuredContent": { "summary": "…", "data": { … }, "links": [ … ] },
>   "isError": false
> }
> ```
>
> `dry_run`, `idempotency_key` und `idempotent_replay` stehen entsprechend **innerhalb**
> `structuredContent`, neben `summary`. Ein Client liest `structuredContent`; der Textblock
> traegt nur `summary` und ist das Einzige, was ein Sprachmodell ohne Werkzeugkenntnis sieht.
>
> Fehler eines Werkzeugs kommen als Ergebnis mit `isError: true` und einem `error_code` in
> `structuredContent` an — **nicht** als JSON-RPC-`error`. Ein JSON-RPC-`error` bedeutet
> ausschliesslich Protokoll- oder Authentifizierungsversagen. Die vollstaendige Ausformulierung
> dieses Vertrags samt Fehlercodes steht in REQ-050 §4.0; sie gilt fuer **alle** Werkzeuge, nicht
> nur die dort spezifizierten fuenf.

Werkzeuge, die Bilder liefern (§2.2a), haengen zusaetzlich **Content-Bloecke** an. `summary`
bleibt auch dort der fuehrende Block — siehe §4.3b.

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
+-- _key                   # idempotency_key (auf Konto + Mandant + Tool gescoped)
+-- service_account_key
+-- tool_name
+-- input_hash
+-- result_payload         # serialisiertes Ergebnis (max 32 kB)
+-- created_at
+-- expires_at             # ArangoDB TTL Index
```

Audit-Retention 90 Tage (NFR-011), Idempotency-Retention 24 h, beides via TTL bzw. Celery automatisch.

## 4. Technische Umsetzung

### 4.1 Code-Layout (Ist-Zustand)

Der MCP-Server ist **kein eigenstaendiger Prozess**, sondern eine In-Prozess-Aggregationsschicht im Backend. Ein frueherer Entwurf dieser Spezifikation sah `src/mcp-server/` als eigene Komponente vor, die das Backend ueber HTTP anspricht. Umgesetzt wurde die In-Prozess-Variante, weil die Werkzeuge damit die Domain-Services direkt aufrufen und Mandanten-Isolation, Validierung und Permission-Invarianten **erben**, statt sie hinter einer zweiten HTTP-Grenze nachzubauen — und weil die Aggregat- und Makro-Werkzeuge (§2.3, §4.2.1) sonst eine Batterie zusaetzlicher REST-Endpoints erzwingen wuerden, die sonst niemand braucht. Die Bedingungen fuer einen spaeteren Split stehen in §9.

```
src/backend/app/
├── mcp_server/
│   ├── server.py            # In-Prozess-Facade ueber die Registry
│   ├── registry.py          # ToolRegistry (Prozess-Singleton) + load_tools()
│   ├── base.py              # ToolBase/WriteToolBase + @mcp_tool (Fail-Fast-Invarianten)
│   ├── dispatcher.py        # Permission -> Validierung -> Dry-Run/Idempotency -> Audit
│   ├── context.py           # ToolContext: Principal + Lazy-Zugriff auf Domain-Services
│   ├── auth.py              # McpAuthenticator (API-Key -> Principal, IP-Allowlist, Rate-Limit)
│   ├── principal.py         # McpPrincipal (Konto + alle Mitgliedschaften mit Rolle)
│   ├── rate_limit.py        # McpRateLimiter (pro Key, fail-closed)
│   ├── audit.py             # MCPAuditLogger + hash_arguments()
│   ├── idempotency.py       # IdempotencyStore (ArangoDB-backed)
│   └── tools/               # kuratierte Palette (§2)
│       └── care.py, harvest.py, plants.py, privacy.py,
│          runs.py, sites.py, species.py, tasks.py
├── api/v1/mcp/
│   ├── router.py            # HTTP-Transport: /mcp/tools, /mcp/rpc, /mcp/sse
│   └── deps.py              # Principal-Aufloesung + Gate auf MCP_SERVER_ENABLED
├── domain/models/mcp.py     # McpToolSpec, McpToolResponse, McpToolLink, McpAuditLogEntry
├── data_access/arango/mcp_repository.py   # Audit- + Idempotency-Repository
├── tasks/mcp_tasks.py       # Retention-Sweeps (Audit 90 d, Idempotency 24 h)
└── migrations/versions/v0017_mcp_collections.py

src/backend/tests/
├── unit/mcp_server/         # auth, dispatcher, tools, rate_limit, server
├── unit/data_access/test_mcp_repository.py
├── unit/test_mcp_migration.py
└── api/test_mcp_endpoints.py
```

**Umsetzungsstand der Werkzeugpalette:** 56 Werkzeuge sind registriert — 44 lesende, 10 schreibende, 2 Setup. Lesend (`mcp.read`): `list_tenants`, `list_species`, `get_species_info`, `list_plants`, `get_plant`, `list_plants_at_location`, `get_plant_care_log`, `get_plant_diagnostics`, `get_plant_inspections`, `list_cultivars`, `get_cultivar`, `list_substrates`, `list_overwintering_profiles`, `list_starter_kits`, `list_phase_definitions`, `get_species_phase_sequence`, `list_phase_sequences`, `list_species_by_phase_sequence`, `get_species_lifecycle`, `get_plant_phase_status`, `get_plant_phase_history`, `list_hardiness_zones`, `search_glossary`, `search_plant_knowledge`, `list_nutrient_plans`, `get_nutrient_plan`, `get_plant_nutrient_plan`, `get_sowing_calendar`, `list_fertilizers`, `calculate_mixing_protocol`, `list_pests`, `get_pest`, `list_diseases`, `get_disease`, `get_treatment`, `list_planting_runs`, `list_tasks`, `get_due_care_tasks`, `get_harvest_readiness`, `get_mcp_activity`, `list_pending_diary_analyses`, `get_diary_entry`, `get_diary_entry_photos`, `list_diary_entries`. Schreibend (`mcp.write`): `confirm_care_task`, `archive_plant`, `set_plant_location`, `add_plant_diary_entry`, `claim_diary_analysis`, `submit_diary_analysis`, `record_feeding_event`, `create_inspection`, `assign_nutrient_plan`, `transition_plant_phase`. Setup (`mcp.setup`): `create_site`, `assign_species_phase_sequence`.

> Diese Zahl ist gegen die *laufende* Registry gepinnt: `test_the_palette_grew_by_exactly_the_five_specified_tools` in `tests/unit/mcp_server/test_palette_registration.py` zaehlt die unter `app.mcp_server.tools` deklarierten Werkzeuge und schlaegt fehl, wenn sie von `PALETTE_SIZE` abweicht. Diese Aufzaehlung, `docs/*/api/mcp-server.md` und die Konstante werden gemeinsam fortgeschrieben — sie sind schon einmal auseinandergelaufen (#931).

Die Zahl stand bis hierhin auf 36 und listete die fuenf Tagebuch-Werkzeuge aus REQ-050 nicht mit, obwohl sie laengst registriert waren — ein Abgleich, der beim Nachziehen von §2.2a unterblieb.

**Diese Aufzaehlung wird maschinell gegen die Registry geprueft.** Sie ist die einzige annaehernd autoritative Werkzeugliste im Repository und ist genau deshalb schon zweimal von der Realitaet abgewichen. `tests/unit/mcp_server/test_palette_registration.py` haelt die Zahl fest und nennt im Fehlerfall die drei Stellen, die gemeinsam nachzuziehen sind: diesen Abschnitt und die beiden `docs/*/api/mcp-server.md`. Gezaehlt wird dabei nur, was unter `app.mcp_server.tools` deklariert ist — die Registry ist ein prozessweites Singleton, in das Testmodule eigene Sonden eintragen, und eine nackte Zaehlung waere von der Sammelreihenfolge abhaengig statt eine Messung.

**Fuenf Werkzeuge fuer die externen Analyse-Prozesse (Issue #931).** Zwei Prozess-Spezifikationen in `kamerplanter-goose` — bildgestuetzte Pflanzengesundheits-Analyse und Naehrstoff-Unter-/Ueberversorgung — waren auf der schreibenden Haelfte blockiert. Jedes der fuenf Werkzeuge ist zusammen mit dem Lesewerkzeug geplant, das sein Ergebnis wiederfindet:

| Werkzeug | Loest Referenzen auf | Macht das Ergebnis sichtbar |
|----------|---------------------|------------------------------|
| `record_feeding_event` | `list_plants`, `list_fertilizers` | `get_plant_diagnostics` |
| `create_inspection` | `list_plants`, `list_pests`, `list_diseases` | `get_plant_inspections` |
| `assign_nutrient_plan` | `list_plants`, `list_nutrient_plans` | `get_plant_nutrient_plan` |
| `get_plant_diagnostics` | `list_plants` | — (Lesewerkzeug) |
| `search_plant_knowledge` | — (mandantenfrei) | — (Lesewerkzeug) |

- **`record_feeding_event`** war die teuerste Luecke. Die Beweiskette der Naehrstoff-Analyse hat auf Stufe 2 den Vergleich *Plan-Ziel gegen tatsaechliche Gabe*; die tatsaechliche Seite existierte in keiner maschinenlesbaren Form. `get_plant_care_log` liefert `action: "confirmed"` — ein Ja/Nein, aus dem sich Unter- und Ueberversorgung **nicht** unterscheiden lassen, obwohl beide gegensaetzlich zu korrigieren sind. Das Werkzeug persistiert Menge, EC, pH und den Tankbezug.
- **`get_plant_diagnostics`** erfuellt AC-5 und liefert den **Verlauf**, nicht nur den letzten Wert: EC und pH je als Reihe fuer Zulauf (`measured_*_before`), Nachmessung (`measured_*_after`) und Drainage (`runoff_*`), jeweils mit `first`/`latest`/`delta`/`direction`. Damit ist auch die bis hierhin offene Frage beantwortet, ob Drainage- und Tank-EC im Datensatz unterscheidbar sind: sie sind es, in getrennten Feldern und getrennten Reihen. `direction` meldet innerhalb eines Rauschbands `stable`, damit kein Trend aus der dritten Nachkommastelle behauptet wird. Die Karenz wird bewusst **nicht** vom Zeitfenster beschnitten — sonst haenge das Ernte-Gate daran, wie der Aufrufer `window_days` gewaehlt hat.
- **`create_inspection`** schliesst eine Schleife: der Bildanalyse-Prozess *liest* `get_plant_inspections`, um seinen Prior zu setzen, konnte aber nie eine Inspektion *schreiben*. Auf einer rein per Agent betreuten Pflanze blieb die Historie damit dauerhaft leer und der Prior baute sich nie auf. Die Befundform ist die, die ein Agent erzeugt (Symptom, Sicherheit, betroffener Pflanzenteil) — dafuer traegt `Inspection` das additive Feld `findings`; `symptoms_observed` bleibt die kanonische flache Liste und wird aus den Befunden mitgefuellt, damit bestehende Leser (Oberflaeche) nichts verlieren.
- **`search_plant_knowledge`** liefert **zitierfaehige** Chunk-Referenzen (`source_key`, `source_type`, `title`, `score`, `language`) und nutzt bewusst `search` statt `ask`: `ask` schiebt ein Sprachmodell zwischen Aufrufer und Korpus. Das Werkzeug ist mandantenfrei und PII-frei — nur die Suchanfrage verlaesst die Instanz, kein `QuestionContext`, keine Pflanze, keine aufgeloeste Art. Faellt der Knowledge-Service aus, endet der Aufruf mit `service.unavailable` (HTTP 503) statt mit einer leeren Trefferliste: „nichts gefunden" und „gar nicht gesucht" sind verschiedene Antworten, und nur eine davon rechtfertigt das Weglassen einer Aussage.
- **`assign_nutrient_plan`** bindet einen **vorhandenen** Plan an eine Pflanze. Ein Plan-Editor ist ausdruecklich **nicht** vorgesehen: Phasenfenster, Produktdosen und Mischreihenfolge sind Redaktionsarbeit mit einer dafuer gebauten Oberflaeche, und ein Werkzeug, das Plaene anlegen kann, laedt ein Modell dazu ein, Duengeziele zu erfinden statt einen von Menschen geprueften Plan zu waehlen. Der Dry-Run benennt den Plan, der ersetzt wuerde — die Repository-Zuweisung loescht die bestehende `follows_plan`-Kante stillschweigend.

**`measurements` hat jetzt deklarierte Groessen und bleibt trotzdem offen.** Das Feld an `add_plant_diary_entry` war ein offenes Objekt (`additionalProperties: true`, keine deklarierten Eigenschaften), dokumentiert allein durch das Beispiel `{'height_cm': 42, 'ph': 6.3}`. Einheit und Herkunft waren unbekannt, eine konsumierende Spezifikation musste mehrdeutige Werte **verwerfen** — eine Zahl, die der Leser wegwerfen muss, ist schlechter als keine. Deklariert sind nun `ec_ms_cm`, `ph`, `temperature_c`, `humidity_percent`, `height_cm` und `leaf_count`, keines davon Pflicht, mit physikalischen Grenzen dort, wo sie eindeutig sind. `ph`, `height_cm` und `leaf_count` behalten die Schreibweise, die **bereits in den Daten steht** — die Lesewerkzeuge geben `measurements` unveraendert zurueck und koennen Bestand nicht migrieren, eine Umbenennung haette also jede Pflanzenhistorie auf zwei Schluesselraeume aufgeteilt. Nur Groessen ohne etablierte Schreibweise (EC, Temperatur, Luftfeuchte) bekamen einen einheitentragenden Namen. Das Objekt bleibt `additionalProperties: true`: die Weboberflaeche schreibt es ueber einen freien Schluessel/Wert-Editor, ein Schliessen haette jeden dort vergebenen Schluessel zur Ablehnung gemacht. Das **REST**-Request-Schema bleibt unveraendert offen — es bedient jenen Editor, waehrend das MCP-Schema einen Leser bedient, der nichts nachfragen kann.

**Geseedete Stammdaten pruefbar machen.** Rund 40 Collections werden aus `app/migrations/seed_data/*.yaml` befuellt; der groesste Anteil sind die 210 Pflanzen-Steckbriefe. `get_species_info` lieferte davon urspruenglich nur fuenf Felder — man konnte pruefen, *dass* eine Art existiert, praktisch nichts an ihrem Inhalt. Das Werkzeug gibt jetzt den vollstaendigen Stammdatensatz zurueck; leere Felder werden ausgelassen, damit ein duenn befuellter Datensatz auch duenn aussieht. `False` und `0` bleiben erhalten: auf diesem Katalog sind beide eine Aussage (`allows_harvest=False`), kein fehlender Wert.

**Ausnahme fuer Sicherheitsfelder (#1005):** Die Auslassungsregel gilt *nicht* fuer `toxicity`, `toxicity_severity`, `allergen_info` und `allows_harvest`. Diese Felder werden immer ausgegeben — als explizites `null`, wenn nicht befuellt. Grund: bei einem Sicherheitsfeld liest ein Konsument die *Abwesenheit* als negative Antwort ("nicht giftig"), also als eine Entwarnung, die niemand gegeben hat. Ein `null` trennt "keine Daten" von "ungefaehrlich"; ein ausgelassenes Feld tut das nicht. Fuer alle uebrigen Felder bleibt duenn-liest-sich-duenn die richtige Semantik (die Vollstaendigkeit eines Datensatzes ist selbst eine Antwort), deshalb ist die Ausnahme bewusst auf diese vier Felder begrenzt.

**Abgrenzung:** Diese Werkzeuge zeigen den **Zustand in der Datenbank**. Der Abgleich gegen die YAML-Quelle ist ein eigener Schritt und bleibt beim `seed-data-validator` — eine erfolgreiche Abfrage belegt „ist angekommen", nicht „stimmt mit der Seed-Datei ueberein".

Der Schaedlings-, Krankheits- und Behandlungskatalog ist **global** — dieselben Daten fuer alle Mandanten, wie der Artenkatalog —, daher fuehren diese Werkzeuge kein `tenant`-Argument. Die Inspektionshistorie gehoert dagegen zu einer Pflanze und ist mandantengebunden.

**Adressierbarkeit als Palettenregel:** Jedes Schreibwerkzeug verlangt einen `plant_key`. Solange kein Lesewerkzeug diesen Key liefert, ist das Schreibwerkzeug fuer die betroffene Pflanze unbenutzbar — ein Argument, das der Aufrufer nicht befuellen kann. Vor `list_plants`/`get_plant` erzeugten nur `get_due_care_tasks` (Pflanzen mit offener Pflege) und `get_harvest_readiness` (Keys ohne Namen) ueberhaupt einen `plant_key`. Neue Schreibwerkzeuge sind daher stets zusammen mit dem Lesewerkzeug zu planen, das ihre Referenzen aufloest.

Die Regel hat sich unmittelbar bewaehrt: `add_plant_diary_entry` schrieb Eintraege, die anschliessend **kein** Lesewerkzeug wiederfand — `list_pending_diary_analyses` zeigt nur markierte, `get_diary_entry` verlangt einen Schluessel, den man bereits haelt. Ein Agent konnte dokumentieren und das Dokumentierte nicht mehr einsehen. `list_diary_entries` schliesst genau diese Luecke und ist damit die Umkehrung des ueblichen Falls: nicht ein Schreibwerkzeug ohne aufloesendes Lesewerkzeug, sondern eines, dessen Ergebnis unauffindbar blieb. Die Regel ist entsprechend in beide Richtungen zu lesen.

Offen sind insbesondere die Setup-Makros, saemtliche Bulk-Werkzeuge, die Standort- und Bereichsverwaltung, `transition_planting_run` sowie die beiden verbliebenen Schreibwerkzeuge `record_harvest` und `apply_treatment`. §2 beschreibt weiterhin den Zielumfang, nicht den Ist-Zustand. `add_plant_diary_entry` (REQ-050 §9, O-04) sowie `record_feeding_event`, `get_plant_diagnostics`, `create_inspection`, `search_plant_knowledge` und `assign_nutrient_plan` (Issue #931) sind umgesetzt und fallen aus dieser Liste heraus.

`apply_treatment` ist von den beiden verbliebenen das sicherheitsrelevante: es setzt eine Karenz in Kraft, die `get_plant_diagnostics` und `get_harvest_readiness` anschliessend als Ernte-Sperre melden. Solange nur die Oberflaeche eine Behandlung erfassen kann, entsteht die Sperre auch nur dort — ein Agent kann eine Behandlung empfehlen, aber ihre Folge nicht in die Daten bringen.

Werkzeuge, deren `Input` von `TenantToolInput` erbt, wirken in genau einem Mandanten (Argument `tenant`); die uebrigen (`list_tenants`, Species-Katalog, `search_plant_knowledge`, `get_mcp_activity`) lesen mandantenfreie Daten. Die Unterscheidung wird aus dem Input-Modell **abgeleitet** (`ToolBase.__init_subclass__`), nicht von Hand gesetzt — sonst koennte ein Werkzeug ein `tenant`-Argument fuehren, das der Dispatcher nie aufloest, und ungebunden laufen.

**Anbindung an das Protokoll:** Der Transport ist handgeschrieben (JSON-RPC 2.0 ueber FastAPI, siehe §1.2); das MCP-SDK von Anthropic wird derzeit nicht eingebunden.

### 4.2 Tool-Registrierung (Pattern)

Ein Werkzeug ist ein duenner, typisierter Adapter auf einen bestehenden Domain-Service — es enthaelt **keine** Geschaeftslogik. Dry-Run-, Idempotency- und Audit-Orchestrierung liegen im `ToolDispatcher`, nicht im Werkzeug: ein Read-Tool implementiert nur `run()`, ein Write-Tool nur `preview()` (geplanter Effekt, nichts persistiert) und `execute()` (der echte Schreibvorgang).

```python
from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import ToolBase, ToolInput, WriteToolBase, WriteToolInput, mcp_tool
from app.mcp_server.context import ToolContext

# Read-Tool
@mcp_tool(name="get_due_care_tasks", permission=McpPermission.READ)
class GetDueCareTasks(ToolBase):
    """Liefert faellige und ueberfaellige Pflegeaufgaben, nach Dringlichkeit gruppiert."""

    class Input(ToolInput):
        urgency: str = Field(default="actionable")

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entries = ctx.care_service.get_care_dashboard_for_tenant(ctx.tenant_key)
        selected = _filter(entries, args.urgency)
        return self._response(
            summary=f"{len(selected)} care reminders match '{args.urgency}'.",
            data={"count": len(selected), "items": [...]},
            links=[ctx.api_link("/care/dashboard"), ctx.ui_link("/care")],
        )


# Write-Tool: preview() + execute(); dry_run/idempotency_key erbt es aus WriteToolInput
@mcp_tool(name="create_plants_bulk", permission=McpPermission.WRITE)
class CreatePlantsBulk(WriteToolBase):
    """Legt mehrere Pflanzen derselben Species in einem Aufruf an."""

    class Input(WriteToolInput):
        species_key: str
        cultivar_key: str | None = None
        count: int = Field(ge=1, le=100)
        location_key: str
        initial_phase: PlantPhase = PlantPhase.SEEDLING

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        ...  # geplanten Effekt beschreiben, ohne zu persistieren

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        created = ctx.plant_service.create_bulk(ctx.tenant_key, ...)
        return self._response(summary=..., data={"created_keys": created}, links=[...])
```

Der Decorator prueft zwei Invarianten bereits bei der Registrierung und laesst den Prozess sonst gar nicht erst starten (SEC-006): ein `WriteToolBase` darf niemals `McpPermission.READ` tragen (stille Rechte-Absenkung), und ein `destructive=True`-Werkzeug ist zwingend an `McpPermission.SETUP` gebunden (AC-S6).

### 4.2.1 Transaktionssemantik fuer Macro-Tools

Macro-Tools (`setup_apartment`, `setup_growbox`, `setup_outdoor_garden`) erzeugen mehrere Ressourcen. Implementierung muss garantieren:

- **All-or-nothing:** Bei Fehler in einem Schritt werden bereits angelegte Ressourcen via Compensating Actions zurueckgerollt. Nutzung der ArangoDB-Transactions API auf Backend-Seite.
- **Partial-Result-Reporting:** Im Erfolgsfall enthaelt `data.created` eine vollstaendige Liste; im Fehlerfall enthaelt `data.attempted` was vorgesehen war und `data.rolled_back: true`.
- **Idempotenz auch bei Macros:** `idempotency_key` deckt die gesamte Macro-Operation ab, nicht einzelne Sub-Schritte.

### 4.3 Authentifizierung

1. Der MCP-Client uebergibt einen `kp_`-API-Key ueber den Transport (HTTP-Header `X-API-Key` oder `Authorization: Bearer kp_...`). Der Key stammt entweder aus dem persoenlichen Konto des Nutzers (`POST /auth/api-keys`, jederzeit einzeln widerrufbar) oder aus einem Service Account.
2. `McpAuthenticator` haesht den Key einmalig und schlaegt ihn nach; der Rohwert verlaesst den Authenticator nie (AC-S2). Widerrufene und abgelaufene Keys werden abgewiesen.
3. IP-Allowlist und Rate-Limit des Keys (REQ-023) werden direkt hier durchgesetzt, fail-closed, bevor weitere Kontoaufloesung stattfindet.
4. Der Authenticator loest **alle aktiven Mandanten-Mitgliedschaften** des Kontos auf und legt sie samt der jeweiligen Rolle in den `McpPrincipal`. Traegt der Key ein `tenant_scope`, wird auf diesen einen Mandanten eingeschraenkt — so bleibt ein Ein-Mandanten-Token moeglich.
5. Der **Dispatcher** waehlt pro Tool-Aufruf genau eine Mitgliedschaft (§4.4) und bindet den `ToolContext` darauf. Ein Werkzeug sieht dadurch immer nur einen Mandanten und nie den rohen Argumentwert.
6. Bei abgelaufenem oder rotiertem Key: MCP-Fehler mit Code `auth.expired`, der Client soll einen Reconnect ausloesen.

### 4.3a Transport-Konformitaet (Streamable HTTP)

Der Server implementiert den **Streamable-HTTP-Transport** (Protokollrevision 2025-03-26 und neuer), der den frueheren Zwei-Endpunkt-Transport "HTTP+SSE" abloest. Ein einziger MCP-Endpunkt nimmt JSON-RPC-Nachrichten per `POST` entgegen; der zuvor vorhandene, funktionslose `/mcp/sse`-Endpunkt ist entfallen.

| Anforderung des Transports | Umsetzung |
|----------------------------|-----------|
| Ein MCP-Endpunkt fuer alle Nachrichten | `POST /api/v1/mcp`. `POST /api/v1/mcp/rpc` bleibt als veralteter Alias bestehen. |
| Antwort als `application/json` **oder** SSE-Stream | Immer `application/json` — vom Transport ausdruecklich erlaubt. |
| Notification/Response erhaelt keine Antwort | `202 Accepted` mit leerem Rumpf. Zuvor beantwortete der Server `notifications/initialized` mit einem `-32601`-Fehler und verletzte damit JSON-RPC 2.0. |
| `protocolVersion` verhandeln | `initialize` spiegelt die Revision des Clients, wenn sie unterstuetzt wird (`2025-06-18`, `2025-03-26`, `2024-11-05`), sonst antwortet der Server mit seiner neuesten. |
| `MCP-Protocol-Version`-Header auf Folgeanfragen | Wird geprueft; eine nicht unterstuetzte Revision wird mit `400` abgelehnt. Fehlt der Header, gilt die vom Transport vorgeschriebene Annahme `2025-03-26`. |
| Sitzungsverwaltung (optional) | `initialize` vergibt `Mcp-Session-Id`; Folgeanfragen mit unbekannter oder fremder Sitzung erhalten `404`, worauf der Client neu initialisiert. `DELETE /api/v1/mcp` beendet die Sitzung. |
| Server-zu-Client-Stream (optional) | `GET /api/v1/mcp` antwortet mit `405` — die vom Transport vorgesehene Antwort fuer einen Server ohne server-initiierte Nachrichten. Dieser Stream ist die Voraussetzung fuer die Fortschritts-Notifications aus §4.5. |

**Die Sitzung ist kein Authentifizierungsmerkmal.** Die Autorisierung haengt vollstaendig am API-Key (§4.3): eine gueltige Sitzung ohne Key wird abgelehnt, ein gueltiger Key ohne Sitzung funktioniert. Die Sitzung traegt ausschliesslich Protokoll-Kontinuitaet. Deshalb degradiert ihr Speicher bei einem Valkey-Ausfall bewusst **offen** (die Sitzung gilt weiter), waehrend die Ratenbegrenzung aus §4.3 fail-closed arbeitet: ein Ausfall wuerde hier jeden Client abmelden, ohne einem Angreifer irgendetwas zu verwehren. Sitzungen sind an das erzeugende Konto gebunden, damit eine abgeflossene Sitzungs-ID unter einem anderen Key wertlos ist.

**Warum kein JWT:** Ein MCP-Client wie Claude Desktop laeuft dauerhaft; das 15-Minuten-Access-Token waere binnen einer Viertelstunde tot, und der zugehoerige Refresh-Token ist ein HttpOnly-Cookie, das nur der Browser besitzt. Ein widerrufbarer API-Key ist der passende Dauer-Credential.

**Konto ohne Mitgliedschaft:** Ein Key, dessen Konto in keinem aktiven Mandanten Mitglied ist, wird abgewiesen — es gaebe nichts, worin er handeln koennte.

**Light-Modus (REQ-027):** Eine Light-Instanz kennt keine Konten — jede Anfrage wird ueber den `LightAuthProvider` zum System-User aufgeloest, und der komplette Auth-Router ist dort nicht gemountet. Genau deshalb ist die **API-Key-Verwaltung (`/auth/api-keys`) in beiden Betriebsmodi verfuegbar**: Ohne sie liesse sich der MCP-Server im Light-Modus zwar einschalten, aber niemals benutzen — der Endpunkt haette dauerhaft mit `401` geantwortet, ohne dass ein Weg zu einem Key existiert. Der ausgestellte Key gehoert dem System-User, der im Light-Seed Mitglied des Standard-Mandanten (`mein-garten`, Rolle `admin`) ist; MCP funktioniert damit unveraendert.

Sicherheitlich verschiebt das nichts: Im Light-Modus hat ohnehin jeder, der die Instanz erreicht, vollen Zugriff auf alle Daten — ein Key verleiht keine zusaetzliche Autoritaet, er macht denselben Zugriff nur von einem externen Client aus nutzbar. Die Vertrauensgrenze einer Light-Instanz ist ihr Netz, weshalb REQ-027 ein solches Deployment nicht ins offene Internet stellt. Login, Registrierung, Sitzungen und OAuth bleiben dem Full-Modus vorbehalten.

### 4.3b Nicht-Text-Content (Bilder)

**Ist-Zustand:** Der Server liefert in `tools/call` ausschliesslich einen Text-Block; das
strukturierte Ergebnis geht zusaetzlich als `structuredContent` mit. Andere Content-Typen
(`image`, `audio`, eingebettete Ressourcen) sind nicht vorgesehen.

`get_diary_entry_photos` (§2.2a, REQ-050) braucht Bilder. Das ist die noetige Erweiterung:

| Ebene | Aenderung |
|-------|-----------|
| Antwort-Modell | `McpToolResponse` erhaelt ein optionales Feld fuer **Content-Bloecke**. Ein `image`-Block traegt die Daten als Basis-64 und den `mimeType`. |
| Werkzeug-Basisklasse | Ein eigener Erzeuger fuer Bild-Antworten neben dem bestehenden Text-Erzeuger; kein Werkzeug baut Content-Bloecke von Hand. |
| Transport | Der `tools/call`-Zweig baut die Content-Liste **aus der Antwort**, statt sie fest auf einen Text-Block zu setzen. |
| Faehigkeitsanzeige | Keine. Content-Typen in Werkzeug-Ergebnissen sind Teil des Basisprotokolls und werden nicht gesondert ausgehandelt. |

**Der fuehrende Block bleibt `summary`.** Er ist heute das Einzige, was ein Sprachmodell aus einer
Werkzeug-Antwort sieht; Bild-Bloecke werden **angehaengt**, nie vorangestellt. Damit aendert sich
fuer die 12 bestehenden Werkzeuge nichts.

**Bilder laufen ueber `tools/call`, nicht ueber MCP-Ressourcen.** Ressourcen waeren
protokollarisch die elegantere Form (§9), sind aber nicht implementiert — und vor allem fuehrte
ein eigener Ressourcen-Lesepfad am `ToolDispatcher` vorbei, dem einzigen Ort, an dem
Mandantenbindung, Rechtepruefung, Idempotenz und Protokollierung zusammenlaufen. Fuer Bilddaten
aus Nutzerbestaenden ist das die falsche Reihenfolge: erst der Kontrollpunkt, dann die Eleganz.
Wer Ressourcen spaeter nachruestet, muss sie durch denselben Kontrollpunkt fuehren.

**Grenzen** (normativ in REQ-050 §4.4):

- Ausgeliefert werden ausschliesslich die WebP-Renditions aus NFR-013 §8.2 (512 oder 1280 px),
  **nie** Originalbilder. Ein Original darf 25 MB gross sein und waere als Basis-64 fuer jedes
  Modell unbrauchbar; Renditions tragen zudem keine EXIF-Daten.
- Die Gesamt-Nutzlast eines Aufrufs ist begrenzt (`MCP_MAX_IMAGE_PAYLOAD_MB`, Vorgabe 4). Bei
  Ueberschreitung antwortet das Werkzeug mit `payload.too_large` und benennt die betroffenen
  Bilder. **Stilles Kuerzen ist unzulaessig.**

**Auswirkung auf das Audit:** Die protokollierte Antwortgroesse (`output_size_bytes`) zaehlt sonst
Basis-64-Bytes mit und laesst einen einzigen Fotoabruf jede andere Werkzeug-Statistik erschlagen.
Bild-Nutzlasten sind daher gesondert auszuweisen oder zu deckeln. Der Argument-Hash (§4.6) bleibt
unveraendert — Bilder stehen in der Antwort, nicht in den Argumenten.

### 4.4 Permission-Matrix-Bindung

Jedes Tool deklariert eine von drei Permissions: `mcp.read`, `mcp.write` oder `mcp.setup`. Sie werden **nicht** einzeln zugewiesen, sondern aus der Rolle abgeleitet, die das Konto **in dem Mandanten** haelt, in dem der Aufruf stattfindet:

| Rolle im Mandanten | mcp.read | mcp.write | mcp.setup |
|--------------------|----------|-----------|-----------|
| `viewer` — Read-Only-Assistent, Gast im Gemeinschaftsgarten | ✓ | ✗ | ✗ |
| `grower` — Tagesbetrieb (Pflege-Quittierung, Diary, Inspections) | ✓ | ✓ | ✗ |
| `admin` — Einrichtung und Struktur | ✓ | ✓ | ✓ |

**Die Rolle gilt pro Mandant, nicht pro Key.** Derselbe persoenliche Key kann im eigenen Garten `admin` sein und im Gemeinschaftsgarten `viewer`. Deshalb bindet der Dispatcher erst den Mandanten und prueft **danach** die Permission (§4.3 Schritt 5); die umgekehrte Reihenfolge wuerde die staerkste Rolle ueberall gewaehren. Ein Nutzer erhaelt ueber MCP damit exakt die Rechte, die er in der Weboberflaeche in genau diesem Garten auch haette — nicht mehr.

**Werkzeug-Uebersicht (`tools/list`)** zeigt die Vereinigung ueber alle Mitgliedschaften, denn ein Werkzeug zu verbergen, das der Nutzer irgendwo verwenden darf, waere falsch. Verbindlich ist die Pruefung beim Aufruf: ein gelistetes Werkzeug kann fuer einen Mandanten, in dem der Nutzer nur `viewer` ist, weiterhin mit `permission.denied` abgelehnt werden.

**Begruendung Drei-Stufen-Modell:** `mcp.setup` ist die destruktivste Klasse (Site-/Location-Loeschung kann ganze Pflanzdaten-Hierarchien zerstoeren) und bleibt deshalb der Admin-Rolle vorbehalten (AC-S6). Die feinere, vom Rollenmodell entkoppelte Vergabe pro Service Account steht weiterhin in §9 als offener Punkt.

### 4.5 Streaming & Notifications

Lange Operationen (z. B. zukuenftige `generate_growing_report`) nutzen MCP-Notifications fuer Fortschritt. Cut 1.0 enthaelt keine Stream-Tools. Voraussetzung ist der server-initiierte Kanal, den `GET /api/v1/mcp` derzeit mit `405` ablehnt (§4.3a) — Fortschritts-Notifications erfordern zuerst dessen Implementierung.

### 4.6 Audit & DSGVO

- Jeder Tool-Aufruf erzeugt einen `mcp_audit_log`-Eintrag.
- `input_hash` statt Klartext-Args, um Aussage-Daten (z. B. Diary-Texte) nicht in Logs zu spiegeln.
- Der Eintrag haelt fest, in **welchem Mandanten** der Aufruf stattfand. Scheitert ein Aufruf, bevor der Mandant gebunden ist (unbekannter Mandant, ungueltige Argumente), bleibt `tenant_key` leer statt geraten zu werden.
- Endpoint `GET /privacy/mcp-activity` (REQ-025 Erweiterung): Nutzer kann das Audit-Log seiner eigenen Keys und Service-Accounts abrufen — gefiltert auf das eigene Konto (AC-S1).
- Audit-Log-Retention 90 Tage, danach Loeschung.
- Idempotency-Records werden nach 24 h via ArangoDB-TTL automatisch entfernt.

## 5. API-Erweiterung Backend

Folgende neue oder erweiterte Backend-Endpoints werden benoetigt (kein eigener REQ noetig — Erweiterung der jeweiligen REQs):

| Endpoint | Quelle-REQ | Status |
|----------|-----------|--------|
| `POST /auth/api-keys` | REQ-023 | bestand bereits — der Weg, auf dem ein Nutzer sich seinen persoenlichen MCP-Key ausstellt. Seit der Light-Modus-Freigabe (§4.3) in **beiden** Betriebsmodi gemountet, waehrend der restliche Auth-Router weiterhin nur im Full-Modus existiert. |
| `POST /auth/service-accounts/validate` | REQ-023 | umgesetzt; liefert seit der Mehrmandanten-Umstellung eine `tenants[]`-Liste statt eines einzelnen Mandanten |
| `GET /t/{slug}/locations/{key}/plants` | REQ-002 | erweitert |
| `POST /t/{slug}/locations/bulk` | REQ-002 | neu |
| `POST /t/{slug}/plants/bulk` | REQ-013 | neu |
| `PATCH /t/{slug}/plants/{key}/location` | REQ-002/013 | neu |
| `POST /t/{slug}/plants/{key}/archive` | REQ-013 | neu |
| `GET /t/{slug}/harvest/readiness` | REQ-007 | neu (Aggregat) |
| `GET /privacy/mcp-activity` | REQ-025 | neu |
| `POST /knowledge/search` | REQ-031 | bereits geplant |

## 6. Konfiguration (Ist-Zustand)

Weil der MCP-Server im Backend-Prozess mitlaeuft (§4.1), gibt es **keinen eigenen Helm-Chart und keinen `mcpServer`-Wertebaum**. Konfiguriert wird ueber drei Umgebungsvariablen des Backends (`app/config/settings.py`) — keine Host-, Port- oder Credential-Konfiguration, da ArangoDB- und Valkey-Verbindung des Backends mitgenutzt werden:

| Variable | Standard | Wirkung |
|----------|---------|---------|
| `MCP_SERVER_ENABLED` | `false` | Gesamtschalter (opt-in). Solange nicht `true`, antworten **alle** `/mcp/*`-Endpunkte mit HTTP 404 — die Schnittstelle existiert dann faktisch nicht (spiegelt den Freischalt-Mechanismus des KI-Assistenten). |
| `MCP_IDEMPOTENCY_TTL_HOURS` | `24` | Gueltigkeitsdauer eines `idempotency_key` (§2.6, AC-22). |
| `MCP_AUDIT_RETENTION_DAYS` | `90` | Aufbewahrungsdauer des `mcp_audit_log` (NFR-011, AC-S4). |

Ressourcen-Limits, Netzwerk-Policies und Probes sind die des Backend-Deployments; die Komponente verursacht keine zusaetzlichen Pods. `requireServiceAccount` ist keine Option, sondern eine harte Invariante des Authenticators (§4.3): ein Nicht-Service-Konto wird immer abgelehnt.

Die Freigabe pro Client erfolgt nicht ueber Betreiber-Konfiguration, sondern ueber API-Keys aus der Benutzerverwaltung (REQ-023) — persoenliche Keys stellt sich jede:r Nutzer:in selbst aus, Service-Account-Keys legt der Betreiber an. Jeder Key traegt seine eigene Mandanten-Reichweite (`tenant_scope`), IP-Allowlist und Ratenbegrenzung.

Betreiber-Doku: `docs/*/reference/environment-variables.md#mcp-server` und `docs/*/api/mcp-server.md`.

## 7. Abhaengigkeiten

| REQ | Abhaengigkeitstyp | Impact |
|-----|-------------------|--------|
| REQ-023 (API-Keys & Service Accounts) | hart | ohne API-Key-Auth kein MCP-Server; der Key kann persoenlich oder maschinell sein |
| REQ-024 v1.4 (Permission-Matrix) | hart | Tool-Permissions `mcp.read`/`mcp.write`/`mcp.setup` ergaenzen |
| REQ-025 v1.0 (DSGVO) | hart | Audit-Log + Privacy-API |
| REQ-031 v1.0 (KI-Assistent / RAG) | weich | `search_plant_knowledge`-Tool nutzt RAG-Infrastruktur; ohne RAG nutzbar (Tool faellt weg) |
| REQ-002 v4.2 (Standortverwaltung) | weich | Setup-Tools, WaterProfile, Location-CRUD |
| REQ-013 v2.0 (Pflanzdurchlauf) | weich | Tools `list_planting_runs`, `create_plants_bulk`, Diary |
| REQ-019 v4.1 (Substratverwaltung) | weich | `create_substrate_batch`, `setup_growbox` |
| REQ-014 v1.4 (Tankmanagement) | weich | `create_tank`, `record_feeding_event` |
| REQ-022 v2.4 (Pflegeerinnerungen) | weich | `get_due_care_tasks`, `confirm_care_task` |
| REQ-006 v2.7 (Aufgabenplanung) | weich | `list_overdue_tasks` |
| REQ-007 v1.0 (Erntemanagement) | weich | `get_harvest_readiness`, `record_harvest` |
| REQ-010 v1.0 (IPM) | weich | `create_inspection`, `apply_treatment`, Karenz-Daten |
| REQ-020 v1.1 (Onboarding) | weich | `apply_starter_kit`, `list_starter_kits` |
| NFR-001 (5-Layer-Architektur) | hart | MCP-Server ist eine Adapter-Schicht **innerhalb** des Backends (§4.1). Er sitzt auf Hoehe der API-Schicht und delegiert an die Business-Logik-Schicht — dieselben Domain-Services wie die REST-API. Kein Werkzeug spricht Repositories oder ArangoDB direkt an; einzige Ausnahme sind die MCP-eigenen Adapter-Collections `mcp_audit_log` und `mcp_idempotency_record` (§3). |
| NFR-008 (Tests) | hart | Unit + Integrationstests gegen Test-Backend |
| NFR-011 (Retention) | hart | mcp_audit_log Retention 90d |

## 8. Akzeptanzkriterien (Definition of Done)

### 8.1 Funktional — Read & Tagesbetrieb

- **AC-1:** Ein Konto — persoenlich oder Service Account — kann sich per `kp_`-API-Key am MCP-Server authentifizieren und alle Tools aufrufen, die ihm die Permission-Matrix im jeweils angesprochenen Mandanten erlaubt.
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

- **AC-23:** `list_plants(query="tomate")` liefert die passenden Pflanzen mitsamt `plant_key`, sodass ein LLM einen Pflanzennamen ohne Zwischenschritt in die Referenz aufloesen kann, die `confirm_care_task`, `set_plant_location` und `archive_plant` verlangen.
- **AC-24:** `get_plant_care_log(plant_key, reminder_type="watering")` liefert das Giessprotokoll der Pflanze in absteigender Zeitfolge. Der Mandanten-Besitz wird zuvor an der Pflanze geprueft, da die Historie selbst keinen Mandanten fuehrt (SEC-001).

- **AC-25:** `get_plant_nutrient_plan(plant_key)` liefert die Phasenziele (NPK, Ziel-EC, Wochenfenster) des der Pflanze zugewiesenen Plans. Der Mandanten-Besitz wird zuvor an der Pflanze geprueft, da die Zuweisung selbst keinen Mandanten fuehrt (SEC-001).
- **AC-26:** `get_sowing_calendar` mit `site_key` prueft den Standort gegen den handelnden Mandanten, bevor dessen Frostdaten und Pflanzdurchlaeufe gelesen werden. Ohne `query` und oberhalb des Seitenlimits wird der Aufruf **abgelehnt** statt stillschweigend gekuerzt — ein gekuerzter Kalender liest sich wie ein vollstaendiger.

- **AC-27:** `get_pest(pest_key)` liefert die Gegenmassnahmen nach IPM-Hierarchie (Praevention vor Intervention) **und** die passenden Nuetzlinge in einer Antwort — biologische Alternativen sind damit ohne Folgeaufruf sichtbar.
- **AC-28:** Jede Behandlungsauskunft nennt die Karenzzeit, und zwar auch in der `summary`: ein Modell, das nur die Zusammenfassung liest, darf die Ernte-Sperre nicht verpassen.
- **AC-29:** `calculate_mixing_protocol` weist einen Duenger eines fremden Mandanten mit `not_found` ab, statt ihn in die Mischung aufzunehmen. Beruht eine Dosierung auf geschaetzten EC-Beitraegen (`ec_contribution_uncertain`), wird das in der `summary` gekennzeichnet — zusaetzlich zu einer etwaigen Ungueltigkeits-Warnung, nicht an deren Stelle.

- **AC-30:** `get_species_info` liefert die geseedeten Stammdaten einer Art vollstaendig — Aussaat-/Ernte-/Bluetefenster, Winterhaerte, Frostempfindlichkeit, Naehrstoffbedarf, Toxizitaet und Sorten —, sodass geseedeter Inhalt ueber MCP inhaltlich pruefbar ist und nicht nur auf Existenz.
- **AC-31:** Die uebrigen geseedeten Kataloge (Substrate, Ueberwinterungsprofile, Starter-Kits, Phasendefinitionen, Winterhaertezonen, Glossar) sind lesend erreichbar. Mandantengebunden sind dabei genau jene, die pro Mandant aufgeloest werden (Ueberwinterungsprofile, Starter-Kits); die uebrigen sind globale Referenzdaten ohne `tenant`-Argument.

### 8.4 Schreibzugriffs-Sicherheit

- **AC-18:** Mit `dry_run=true` wird kein einziger DB-Write durchgefuehrt (verifiziert via Audit-Log: `status="dry_run"` und kein Folge-Log-Eintrag mit `status="ok"`).
- **AC-19:** Zwei Aufrufe desselben Schreibtools mit identischem `idempotency_key` innerhalb 24 h ergeben identische Ergebnis-IDs und legen nur eine Ressource an (Test fuer `create_plant`, `create_plants_bulk`, `setup_apartment`).
- **AC-20:** Bei Fehler waehrend einer Macro-Transaktion (`setup_growbox`) bleibt keine Teil-Hierarchie zurueck — verifiziert per Test mit absichtlich invalider Slot-Anzahl.
- **AC-21:** Schreibtools sind im MCP-Tool-Schema mit `annotations.destructive: true` markiert, wo sie loeschen oder Zustand zerstoeren — Claude Desktop kann den Nutzer warnen.
- **AC-22:** Idempotency-Records werden nach 24 h via ArangoDB-TTL automatisch entfernt.

### 8.5 Sicherheit & Datenschutz

- **AC-S1:** Cross-Tenant-Zugriff ist unmoeglich — ein Key kann ueber kein Werkzeug Daten eines Mandanten sehen, in dem sein Konto nicht aktives Mitglied ist (nachgewiesen via Tests).
- **AC-S1a:** Ein persoenlicher API-Key gewaehrt genau die Mandanten aus `list_my_tenants` — dieselbe Quelle, auf die die REST-API scoped. Ueber MCP ist nichts erreichbar, was der Nutzer nicht auch in der Weboberflaeche sieht.
- **AC-S1b:** Die Rechtepruefung erfolgt gegen die Rolle im **aufgerufenen** Mandanten. Ein Nutzer, der in Mandant A `admin` und in Mandant B `viewer` ist, kann in B kein Schreibwerkzeug ausfuehren (nachgewiesen via Test).
- **AC-S1c:** Ein Werkzeug erhaelt den Mandanten ausschliesslich aus der aufgeloesten Mitgliedschaft, nie aus dem rohen Argument — ein Werkzeug kann seinen Wirkungsbereich nicht selbst erweitern.
- **AC-S2:** API-Keys erscheinen niemals im Audit-Log oder in Fehlermeldungen.
- **AC-S3:** Ein Nutzer kann ueber `GET /privacy/mcp-activity` alle MCP-Aufrufe seiner eigenen Keys (und der ihm zugeordneten Service-Accounts) der letzten 90 Tage einsehen.
- **AC-S4:** `mcp_audit_log`-Eintraege aelter als 90 Tage werden vom Retention-Master-Task (NFR-011) geloescht.
- **AC-S5:** Tool-Argumente werden vor dem Logging gehasht — keine Diary-Texte oder Symptom-Beschreibungen im Klartext-Log.
- **AC-S6:** Ein Konto ohne `mcp.setup` im angesprochenen Mandanten kann dort ueber kein Tool eine `delete_location` ausloesen — selbst nicht durch indirekte Macros.
- **AC-S7:** Kein Werkzeug liefert ein Originalbild aus. Bild-Content stammt ausschliesslich aus den WebP-Renditions (NFR-013 §8.2) und traegt daher keine EXIF-Daten — auch dann nicht, wenn der Mandant `STORAGE_KEEP_EXIF_<CATEGORY>=true` gesetzt hat (§4.3b).
- **AC-S8:** Ueberschreitet ein Bild-Abruf die konfigurierte Nutzlast-Obergrenze, antwortet das Werkzeug mit `payload.too_large` und benennt die betroffenen Bilder. Es kuerzt **nie** still — ein Agent darf nicht glauben, alle Bilder gesehen zu haben, waehrend welche fehlten.
- **AC-S9:** Die protokollierte Antwortgroesse weist Bild-Nutzlasten gesondert aus oder deckelt sie, sodass ein Fotoabruf die Werkzeug-Statistik nicht erschlaegt.

### 8.6 Qualitaet & Tests

- **AC-T1:** Unit-Test-Coverage >= 80% in `src/backend/app/mcp_server/` und `src/backend/app/api/v1/mcp/`.
- **AC-T2:** Integrationstest pro Tool gegen Test-Backend (alle ~30 Tools).
- **AC-T3:** End-to-End-Test mit echtem Claude Desktop / mcp-inspector als Client (Smoke-Test: Wohnung anlegen → 3 Pflanzen → Pflege quittieren).
- **AC-T4:** Ruff + mypy clean.

### 8.7 Deployment

- **AC-D1:** Mit `MCP_SERVER_ENABLED=true` am Backend-Deployment ist die Werkzeugschnittstelle unter `/api/v1/mcp/` erreichbar und ein gueltiger API-Key kann `tools/list` und `tools/call` ausfuehren — ohne zusaetzlichen Pod (§6).
- **AC-D2:** Mit `MCP_SERVER_ENABLED=false` (Default) antworten alle `/mcp/*`-Endpunkte mit HTTP 404 — Kamerplanter funktioniert unveraendert und die Schnittstelle ist von aussen nicht unterscheidbar von "existiert nicht".
- **AC-D5:** Auf einer Light-Instanz kann ein Nutzer ueber die Kontoeinstellungen einen API-Key erzeugen und damit den MCP-Server benutzen. `POST /auth/api-keys` ist dort erreichbar, `POST /auth/login` weiterhin nicht.
- **AC-D4:** Ein Streamable-HTTP-Client absolviert den vollstaendigen Handschlag gegen `POST /api/v1/mcp`: `initialize` (mit Versionsverhandlung und `Mcp-Session-Id`), `notifications/initialized` (Antwort `202`, kein Rumpf), `tools/list`. Eine unbekannte Sitzung liefert `404`, `GET` auf den Endpunkt `405`, `DELETE` beendet die Sitzung mit `204`.
- **AC-D3:** Dokumentation in `docs/` enthaelt eine Konfigurations-Anleitung fuer MCP-Clients (HTTP-Transport: Backend-URL + `X-API-Key`) sowie die Betreiber-Variablen aus §6. Das `claude_desktop_config.json`-Beispiel setzt den stdio-Bridge-Client voraus und wird mit diesem nachgereicht (§9).

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

**Szenario 8: Eine Person, zwei Gaerten, zwei Rollen**
- **GIVEN** eine Nutzerin mit persoenlichem API-Key, die in ihrem eigenen Garten `admin` und im Gemeinschaftsgarten `viewer` ist
- **WHEN** der Client ein Schreibwerkzeug mit `tenant: "<eigener-garten>"` aufruft
- **THEN** wird es ausgefuehrt
- **WHEN** derselbe Client dasselbe Werkzeug mit `tenant: "<gemeinschaftsgarten>"` aufruft
- **THEN** lehnt der Server mit `permission.denied` ab — die Rolle des *angesprochenen* Mandanten entscheidet, nicht die staerkste Rolle des Keys
- **AND** ein Aufruf ohne `tenant` wird als mehrdeutig zurueckgewiesen, statt einen Garten zu raten.

**Szenario 9: Fremder Garten bleibt unsichtbar**
- **GIVEN** ein persoenlicher API-Key, dessen Konto nur im eigenen Garten Mitglied ist
- **WHEN** der Client ein Werkzeug mit dem Slug eines fremden Gartens aufruft
- **THEN** liefert der Server `not_found` — dieselbe Antwort wie fuer einen nicht existierenden Mandanten, ohne dessen Existenz preiszugeben.

**Szenario 7: RAG-Bruecke**
- **GIVEN** ein Tenant ohne aktive Pflanzdurchlaeufe
- **AND** Service Account mit `mcp.read`
- **WHEN** der Client `search_plant_knowledge("Tomate Mischkultur")` aufruft
- **THEN** liefert das Tool RAG-Treffer aus der globalen Wissensbasis (tenant-unabhaengig, keine PII).

## 9. Offene Punkte / Spaetere Erweiterungen

- **Werkzeugkatalog vervollstaendigen:** **21** der in §2 spezifizierten Werkzeuge fehlen noch. Die Zahl ist hier zum ersten Mal aus den Tabellen von §2 nachgezaehlt und aufgeschluesselt, weil die zuvor genannten "18" sich daraus nicht reproduzieren liessen — eine Zahl, deren Herkunft niemand pruefen kann, veraltet unbemerkt:
    - §2.1 lesend (1): `get_planting_run`. `list_overdue_tasks` zaehlt **nicht** mit, es ist ueber `list_tasks` mit Status-Filter erreichbar.
    - §2.2 schreibend (3): `transition_planting_run`, `record_harvest`, `apply_treatment`.
    - §2.3 Setup (11): `setup_apartment`, `setup_growbox`, `setup_outdoor_garden`, `update_site`, `create_location`, `create_locations_bulk`, `update_location`, `delete_location`, `set_water_profile`, `create_substrate_batch`, `apply_starter_kit`.
    - §2.4 Pflanzen erfassen (6): `find_or_create_species`, `create_plant`, `create_plants_bulk`, `create_planting_run`, `add_plants_to_run`, `set_plant_phase`. `move_plant` ist als `set_plant_location` umgesetzt.

    Abgehakt: `add_plant_diary_entry` (REQ-050 O-04) sowie `record_feeding_event`, `get_plant_diagnostics`, `create_inspection`, `search_plant_knowledge` und `assign_nutrient_plan` (Issue #931). `assign_nutrient_plan` stand in keiner §2-Tabelle — es schliesst die Luecke, die AC-25 offenliess, indem es einen bereits *bestehenden* Plan bindet.
- **`apply_treatment` und `record_harvest` (bewusst zurueckgestellt, Issue #931):** Beide Analyse-Prozesse erzeugen *empfohlene* Massnahmen und halten dort an — die Entscheidung trifft ein Mensch. Ohne die beiden Werkzeuge endet eine getroffene Entscheidung als Handarbeit in der Oberflaeche. `apply_treatment` ist dabei das gewichtigere: es setzt die Karenz in Kraft, die `get_plant_diagnostics` und `get_harvest_readiness` als Ernte-Sperre melden, und es traegt mit `ResistanceWarningError` eine eigene Ablehnungsklasse, die im MCP-Fehlervertrag noch keinen Code hat.
- **stdio-Bridge-Client:** Claude Desktop startet einen MCP-Server als lokalen Subprozess und kann keinen Pod ansprechen. Vorgesehen ist dafuer **kein zweiter Dienst**, sondern ein schlanker, beim Nutzer laufender Bridge-Client, der `MCP_SERVER_URL` + `X-API-Key` entgegennimmt und JSON-RPC an `/api/v1/mcp/rpc` durchreicht. Damit wird AC-D3 vollstaendig erfuellt, ohne den Server zu spalten.
- **Eigenstaendiger Prozess (bewusst zurueckgestellt):** Ein Split von `app/mcp_server/` in eine eigene Komponente mit eigenem Helm-Chart wuerde die direkte Service-Anbindung durch eine HTTP-Grenze ersetzen und damit zusaetzliche Bulk-/Transaktions-Endpoints, eine zweite Fehleruebersetzung und DB-Zugriff ueber Umwege erzwingen (§4.1). Sinnvoll wird der Split erst, wenn MCP-Verkehr das Backend messbar beeintraechtigt oder eigene Ressourcen-/Skalierungsgrenzen braucht — etwa im Mehrmandanten-Hosting. Der `ToolDispatcher` ist als einziger Choke-Point fuer Auth, Permission, Idempotency und Audit die vorgesehene Schnittkante.
- **Granulare MCP-Permissions:** `mcp.read`/`mcp.write`/`mcp.setup` werden aus der Mandanten-Rolle abgeleitet (viewer/grower/admin, §4.4), nicht einzeln pro Key zugewiesen. Der in §2.3 beschriebene Ablauf "Admin vergibt `mcp.setup` einmalig fuers Onboarding und widerruft danach" ist damit nur ueber einen Rollenwechsel moeglich. Sinnvolle Ausbaustufe: eine optionale Rechte-Obergrenze **pro Key** (z. B. "dieser Key darf nur lesen, auch wenn sein Besitzer Admin ist"), damit ein Nutzer einem LLM-Client weniger geben kann als er selbst hat.
- **Feingranulare Sichtbarkeit innerhalb eines Mandanten:** "Nur seine Daten" endet heute an der Mandantengrenze — innerhalb eines Gemeinschaftsgartens sehen alle Mitglieder dieselben Pflanzen, wie in der Weboberflaeche auch. Eine Einschraenkung auf die selbst angelegten Datensaetze existiert im Datenmodell nicht (`LocationAssignment` waere der Ansatzpunkt). **REQ-050 §7.2 ist der erste Fall, der daran nicht vorbeikommt:** Weil ein markierter Tagebuch-Eintrag samt Fotos an ein Sprachmodell geht, darf dort nur markieren, wer den Eintrag selbst verfasst hat (oder die Rolle Leitung haelt). Diese Pruefung findet im Werkzeug statt, nicht im Datenmodell — sie ist damit die erste Ausnahme von "Mandantengrenze = Sichtbarkeitsgrenze" und ein Argument dafuer, die feingranulare Sichtbarkeit endlich zu modellieren.
- **Tagebuch-Schreibwerkzeug (erledigt):** `add_plant_diary_entry` (§2.2) ist umgesetzt — REQ-050 §9 (O-04) ist mit **ja, ohne `photo_refs`** entschieden. Ein Agent kann damit dokumentieren und nicht nur analysieren. Zwei Grenzen bleiben bewusst bestehen: Der geschriebene Eintrag wird **nicht** zur Analyse markiert (das bleibt eine Nutzerhandlung nach REQ-050 §1.3, sonst erzeugte sich ein Agent seine eigene Arbeit und umginge die Einwilligungspruefung aus §7.1), und Fotos kommen ausschliesslich ueber die Weboberflaeche an einen Eintrag.
- **Server-zu-Client-Stream:** `GET /api/v1/mcp` lehnt mit `405` ab (§4.3a). Erst mit diesem Kanal sind Fortschritts-Notifications, `tools/list_changed` und wiederaufnehmbare Streams (`Last-Event-ID`) moeglich.
- **Streaming-Tools:** `generate_growing_report(run_key)` als Long-Running mit Progress-Notifications.
- **Resource-Bindings:** MCP unterstuetzt neben Tools auch `resources` (lesbare Inhalte). Pflanzen-Detailseiten als `resource://kamerplanter/plant/{key}` exponieren. **Bewusst nicht der Weg fuer Bilder:** Die Foto-Auslieferung aus REQ-050 laeuft ueber `tools/call` (§4.3b), weil ein eigener Ressourcen-Lesepfad am `ToolDispatcher` als einzigem Kontrollpunkt vorbeifuehrte. Wer Ressourcen nachruestet, muss sie durch denselben Kontrollpunkt fuehren.
- **MCP-Prompts:** Vordefinierte Prompts ("Tagesabschluss-Report", "Diagnose-Workflow") als MCP-Prompts ausliefern.
- **Sampling-Bridge:** Ueber MCP-`sampling` REQ-031-Antworten an externe Clients zurueckgeben — vermeidet Doppel-LLM-Aufrufe.
- **Bidirektionale HA-Bruecke:** MCP-Tool `trigger_ha_automation(automation_id)` als Aktorik-Schnittstelle (REQ-018).
- **Token-Budget-Optimierung:** Wenn Tool-Antwort > N kB, automatische Zusammenfassung und Pagination-Hint.
