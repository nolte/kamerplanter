---
plan-type: implementation-plan
title: Umsetzungsplan — fünf gescaffoldte Backend-Domänen zu echter Implementierung bringen
epic: backend-domain-scaffolds
covers: [REQ-008, REQ-016, REQ-017, REQ-018, REQ-026]
source-audit: spec/analysis/code-review-fable5-2026-07.md (GAP-B1)
status: ready
created: 2026-07-10
verified-against: develop
parallelizable: true
specialist: fullstack-developer
---

# Umsetzungsplan: fünf gescaffoldte Backend-Domänen ausimplementieren

**Zweck.** Fünf Backend-Domänen wurden im Bulk-Close #127 (`661e7ecb4`) nur *gescaffoldt* und
sind seither unverändert: jeder Router ist ein leeres `APIRouter(prefix=…)`, jeder Service wirft
`NotImplementedError`, jede Frontend-Page ist ein ~21–27-zeiliger Platzhalter mit `scaffoldNotice`.
Dieser Plan überführt sie **code-geerdet** in produktionsreife Implementierung. Jedes Arbeitspaket
nennt die real betroffenen Dateien, die Spec-Sollmenge (Modelle, Endpunkte, AQL/Graph), testbare
Akzeptanzkriterien, den Spezialisten-Agenten, Aufwand und Abhängigkeiten. Der Plan ist so
geschnitten, dass `issue-orchestrate` / `fullstack-developer` ihn ohne Rückfragen in fünf parallele,
datei-disjunkte Work Packages zerlegen kann.

**Abgrenzung.** Es geht **nicht** um neue fachliche Anforderungen — die Specs unter `spec/req/`
sind vollständig. Es geht um das Schließen der Implementierungslücke zwischen Scaffold und Spec-Soll.

---

## Ziel

Nach Abschluss aller fünf WPs gilt für **jede** Domäne:

1. Der Service ist echt implementiert (keine `NotImplementedError` mehr), gegen ein Repository und
   ArangoDB verdrahtet.
2. Der Router trägt die in der jeweiligen Spec spezifizierten Endpunkte und ist im zentralen Router
   (`api/v1/router.py` bzw. `api/v1/tenant_scoped/router.py`) registriert.
3. Die Frontend-Page zeigt eine echte Arbeitsoberfläche; der `scaffoldNotice`-Key ist entfernt und
   die Page ist im Routing registriert.
4. Backend-Coverage ≥ 60 %, Frontend-Coverage ≥ 80 % (nur wo Frontend Teil des WP ist), i18n de/en
   vollständig, Coverage-Audit grün.

---

## Ist-Stand (verifiziert 2026-07-10 gegen develop)

Alle Pfade relativ zu `src/backend/app/` bzw. `src/frontend/src/`. Verifikation per Read/Grep am
Quellcode.

**Architektur-Randbedingungen (gelten für ALLE WPs):**

- **`domain/models/__init__.py` ist LEER (0 Bytes).** Es gibt **kein** Re-Export-Aggregat; jedes
  Modell wird direkt aus seinem Modul importiert (`from app.domain.models.actuator import Actuator`).
  → **Kein** Serialisierungspunkt an dieser Datei; neue Modelle sind additiv und kollisionsfrei.
- **Keiner der fünf Scaffold-Router ist registriert.** Weder `api/v1/router.py` (globaler
  `api_router`, Prefix `/api/v1`, Registrierung per `api_router.include_router(...)`, teils
  modusabhängig `if settings.kamerplanter_mode == "full"`) noch `api/v1/tenant_scoped/router.py`
  importieren post_harvest / inventree / propagation / actuators / aquaponik. → **Diese beiden
  Wiring-Dateien sind der zentrale Serialisierungspunkt** (Merge-Konflikt-Risiko, siehe unten).
- **Frontend-Routing + i18n sind Serialisierungspunkte.** Die vier existierenden Scaffold-Pages sind
  in **keinem** `routes/`-File referenziert; alle vier `scaffoldNotice`-Keys liegen in
  `i18n/locales/{de,en}/translation.json`.
- **ArangoDB ist schemalos.** Neue optionale Felder sind für Bestandsdokumente unkritisch. Neue
  Collections/Edges müssen im Graph-Setup (named graph `kamerplanter_graph`) registriert werden.
- **Enum-Single-Source dreifach:** `common/enums.py` (Python `StrEnum`) · Seed-Schema-`$defs` ·
  `frontend/src/api/types.ts` (manuell, kein OpenAPI-Codegen). Jeder neue Enum-Wert = 3 Stellen + i18n.

### REQ-008 Post-Harvest — **STILL_SCAFFOLD**
- `domain/services/post_harvest_service.py:23` (`list_for_batch`), `:27` (`advance_stage`) → NotImplementedError.
- `domain/models/post_harvest.py:19` `PostHarvestBatch` existiert (Header als Scaffold markiert).
- `api/v1/post_harvest/router.py:11` leerer Router, Prefix `/post-harvest`, tags `["post-harvest"]`; nicht registriert.
- `frontend/src/pages/post-harvest/PostHarvestPage.tsx` scaffoldNotice-Key `pages.postHarvest.scaffoldNotice`, `data-testid="post-harvest-page"`; nicht im Routing.
- Spec: `spec/req/REQ-008_Post-Harvest.md` (1934 Z.). §2 Nodes: `StorageProtocol` (`protocol_type: drying|curing|aging|hardening|storage`), `CuringPhase`, `StorageCondition`, `StorageLocation`, `StorageObservation`, `BurpingEvent`, `DryingProgress`, `MoldAlert`; Edges u. a. `has_drying_progress`. §3 Domänenlogik: `DryingProtocol.calculate_dryness_progress` (Ziel-Trocknung, `ready_for_curing >= 95%`), Wasseraktivität `a_w` als Endpunkt-Indikator. **Keine explizite Endpunkt-Tabelle** in der Spec — Endpunkt-Set unten aus §2/§3 abgeleitet.

### REQ-016 InvenTree (optional) — **STILL_SCAFFOLD**
- `data_access/external/inventree_adapter.py:23` (`list_stock_for_part`), `:27` (`reserve_part`) → NotImplementedError; `health_check` (:29–36) gibt Stub `{"ready": false, "reason": "scaffolding …"}`.
- **Kein Service, kein Domain-Model, keine Frontend-Page.**
- `api/v1/inventree/router.py:9` leerer Router, Prefix `/inventree`; nicht registriert.
- Spec: `spec/req/REQ-016_InvenTree-Integration.md` (1485 Z.). §3.2 Adapter-Interface, §3.3 HTTP-Impl (`GET /api/part/`, `GET /api/stock/`, `POST /api/stock/{action}/`), §3.4 Sync-Engine, §3.5 ConsumptionTracker, §3.6 Celery-Tasks, §3.7 **18 REST-Endpunkte** (Tabelle Z. 1320–1337): 13× `/api/v1/inventree/*` + 5× `/api/v1/equipment/*`. §1.2 Mapping Fertilizer/Substrate → InvenTree-Part.

### REQ-017 Vermehrung/Lineage — **PARTIAL**
- `domain/services/propagation_service.py`: `record()` (:28–38) echt implementiert und bereits per DI verdrahtet (`common/dependencies.py:161`/`:181`, `plant_instance_service.py:61`/`:85`, D10-Follow-up). **Nur** `:41` (`list_for_plant`) → NotImplementedError.
- `domain/engines/lineage_engine.py:24` (`trace_ancestors`), `:27` (`is_graft_compatible`) → NotImplementedError; nirgends verwendet.
- `domain/models/propagation.py:18` `PropagationEvent` existiert.
- `api/v1/propagation/router.py:5` leerer Router, Prefix `/propagation`; nicht registriert.
- `frontend/src/pages/propagation/PropagationPage.tsx` scaffoldNotice `pages.propagation.scaffoldNotice`, `data-testid="propagation-page"`; nicht im Routing.
- Spec: `spec/req/REQ-017_Vermehrungsmanagement.md` (1736 Z.). §3 REST-Endpunkte (Z. 1404–1448): ~30 Endpunkte in Gruppen Events / Batches / Protocols / Mothers / Lineage (`/api/v1/plant-instances/{key}/lineage`, `/descendants`, `/graft-compatibility`) / Phenotypes / Stats. §2 Collections + Edges `descended_from`. §4/§5 Phasen-Eintrittsmatrix (Deps REQ-003/013/019).

### REQ-018 Umgebungssteuerung/Aktorik — **STILL_SCAFFOLD**
- `domain/services/actuator_service.py:17` (`list_for_tenant`), `:20` (`set_state`) → NotImplementedError.
- `domain/models/actuator.py:14` `Actuator` existiert.
- `data_access/external/ha_client.py:9` `HomeAssistantClient` **voll implementiert** (`fire_event`, `call_service`, `list_sensor_entities`, `get_state`, …), aber vom actuator_service **nicht** genutzt → als Vorleistung einbinden.
- `api/v1/actuators/router.py:5` leerer Router, Prefix `/actuators`; nicht registriert.
- `frontend/src/pages/environment/EnvironmentControlPage.tsx` scaffoldNotice `pages.environmentControl.scaffoldNotice`, `data-testid="environment-control-page"`; nicht im Routing.
- Spec: `spec/req/REQ-018_Umgebungssteuerung.md` (1685 Z.). §3 REST-Endpunkte (Z. 1346–1398): ~35 Endpunkte in Gruppen Actuators-CRUD / Command+Override / Schedules / Rules / Events+Stats / Phase-Control-Profiles / HA-Integration (`/api/v1/integrations/home-assistant/*`) / Location-Status+Energy; zusätzlich Notabschaltung `POST /api/v1/emergency-stop` (Z. 117). §2 Collections + embedded Rule-Modelle. §3 Engines: Control-Loop mit Hysterese, HA-Service-Call (`{base_url}/api/services/{domain}/{service}`).

### REQ-026 Aquaponik — **STILL_SCAFFOLD**
- `domain/services/aquaponik_service.py:19` (`get_loop_status`), `:22` (`record_water_test`) → NotImplementedError.
- `domain/engines/hydro_system_monitor.py:16` `HydroSystemMonitor` **voll implementiert** (`analyze_runoff` :22–85, `validate_ec_for_substrate` :87–97, Default-EC-Limits) + Unit-Test, aber **nirgends verdrahtet** → als Vorleistung einbinden.
- **Kein `aquaponik.py`-Model** (verwandt: `tank.py`, `sensor.py`).
- `api/v1/aquaponik/router.py:5` leerer Router, Prefix `/aquaponik`; nicht registriert.
- `frontend/src/pages/aquaponik/AquaponikPage.tsx` scaffoldNotice `pages.aquaponik.scaffoldNotice`, `data-testid="aquaponik-page"`; nicht im Routing.
- Spec: `spec/req/REQ-026_Aquaponik-Management.md` (1795 Z.). §2 Nodes (`AquaponicSystem`, `FishStock`, `WaterTest`, `FishSpecies`) + Edges `compatible_fish_plant`/`incompatible_fish_plant`. §3 Enums + Logik (freie Ammoniak-Berechnung, Cycling, FCR, Defizit-Analyse). §4 **~32 Endpunkte in 8 Gruppen**: tenant-scoped `/api/v1/t/{tenant_slug}/aquaponics/*` (Systems 6, Fish-Stocks 6, Water-Tests 5, Feeding 4, Supplementation 3, Safety 2, Health 2) **plus global** `/api/v1/fish-species/*` (4, Seed-Daten). §2 Seed-Daten für Fischarten + Kompatibilitäts-Edges.

---

## Arbeitspakete

### WP-008 — REQ-008 Post-Harvest ausimplementieren

**Problem.** Die Nacherntebehandlung ist reines Scaffold: `PostHarvestService` wirft
NotImplementedError, der Router ist leer und nicht registriert, es gibt kein Repository und keine
Stage-State-Machine. Ernte-Chargen (REQ-007) können nicht in Trocknung/Curing/Storage überführt werden.

**Umzusetzen (Spec-Soll §2/§3):**
- Repository `data_access/repositories/post_harvest_repository.py` für `PostHarvestBatch` +
  `StorageProtocol`, `CuringPhase`, `StorageCondition`, `StorageLocation`, `StorageObservation`,
  `BurpingEvent`, `DryingProgress`, `MoldAlert` (Collections + Edge `has_drying_progress`).
- Stage-State-Machine im Service: `drying → curing → storage` (`protocol_type` gemäß §2), keine
  Rückwärtstransition, `advance_stage()` prüft Fortschrittskriterien (`DryingProgress`-Berechnung
  `ready_for_curing >= 95%`, `a_w`-Ziele je Kultur).
- Endpunkte am `/post-harvest`-Router: `POST /post-harvest/start-drying` (Charge aus Harvest
  übernehmen), `GET /post-harvest/{key}` (Batch-Detail inkl. Stage + DryingProgress),
  `POST /post-harvest/{key}/advance` (Stage-Übergang), plus Lese-Endpunkte für Observations/Alerts
  und `GET /post-harvest?batch=…` (Liste je Charge). MoldAlert-Erzeugung bei RH-Überschreitung.
- Verknüpfung zu REQ-007 (Harvest-Batch-Referenz) und REQ-010 (Karenz-/Qualitäts-Gate, ADR-001).
- ArangoDB-Collections + Edges im Graph-Setup registrieren.
- Frontend-Workflow-UI: `pages/post-harvest/PostHarvestPage.tsx` zu Charge-Liste + Stage-Ansicht +
  Advance-Aktion ausbauen; API-Layer + Redux-Slice; scaffoldNotice entfernen; Routing + i18n.

**Betroffene Dateien/Pfade:**
- `domain/services/post_harvest_service.py`, `domain/models/post_harvest.py` (erweitern),
  neue `data_access/repositories/post_harvest_repository.py`, `api/v1/post_harvest/router.py`,
  neue `api/v1/post_harvest/schemas.py`.
- Wiring: `api/v1/router.py` (include_router), Graph-Setup, `common/dependencies.py` (DI-Factory).
- Frontend: `pages/post-harvest/PostHarvestPage.tsx`, `api/postHarvest.ts` (neu), Routing-File,
  `i18n/locales/{de,en}/translation.json`, `store/` (Slice), `api/types.ts`.

**Akzeptanzkriterien:**
- `POST /post-harvest/start-drying` mit gültiger Harvest-Batch-Referenz legt Batch in Stage `drying` an (201).
- `POST /post-harvest/{key}/advance` von `drying`→`curing` nur bei erfülltem Trocknungskriterium; sonst 422.
- Rückwärtstransition (`storage`→`curing`) wird mit 422 abgelehnt.
- `GET /post-harvest/{key}` liefert aktuelle Stage + DryingProgress-Prozent.
- Kein `NotImplementedError` mehr im Service; Router im OpenAPI sichtbar.
- Frontend-Page zeigt echte Chargen; kein `scaffoldNotice`-Key; `data-testid="post-harvest-page"` bleibt.

**Spezialist-Agent:** `fullstack-developer`. **Aufwand:** L. **Abhängigkeiten:** REQ-007/003/010 (implementiert).

---

### WP-016 — REQ-016 InvenTree-Integration ausimplementieren

**Problem.** Der `InvenTreeAdapter` wirft NotImplementedError, `health_check` ist ein Stub, es gibt
weder Service noch Sync-Engine noch Endpunkte. Bestandsführung gegen eine InvenTree-Instanz ist nicht
möglich. (Feature ist optional — Deaktivierung/Nicht-Konfiguration darf das System nicht brechen.)

**Umzusetzen (Spec-Soll §3):**
- Adapter-HTTP-Calls (§3.3): `list_stock_for_part`, `reserve_part`, echter `health_check`
  (`GET {base_url}/api/`) gegen die InvenTree-REST-API (`/api/part/`, `/api/stock/`, `/api/stock/{action}/`).
- Enums + Pydantic-Modelle (§3.1), Mapping-Collections (§1.2, §2): Referenzen Fertilizer/Substrate/
  Equipment → InvenTree-Part; Edge-Collections gemäß §2.
- Sync-Engine (§3.4), ConsumptionTracker (§3.5), Celery-Sync-Tasks (§3.6, `push_pending_transactions`,
  max. 5 min).
- 18 REST-Endpunkte (§3.7-Tabelle): `/api/v1/inventree` (Connections 5, References 4, Browse 2,
  Sync+Transactions 2) + `/api/v1/equipment` (CRUD 5). Auth: Connection-Management Admin, Rest Mitglied.
- Optionalität: bei fehlender/deaktivierter Konfiguration liefert `health_check` sauberen
  `ready:false`-Zustand statt Crash; Endpunkte antworten deterministisch (kein 500).

**Betroffene Dateien/Pfade:**
- `data_access/external/inventree_adapter.py`, neue `domain/services/inventree_service.py`,
  neue `domain/engines/inventree_sync_engine.py`, neue `data_access/repositories/inventree_repository.py`,
  `api/v1/inventree/router.py` + neue `schemas.py`, neuer `api/v1/equipment/router.py`,
  neue Celery-Tasks in `tasks/`.
- Wiring: `api/v1/router.py`, Graph-Setup, `common/enums.py`, Settings (`config/settings.py`).
- (Frontend optional/nicht Pflicht dieses WP — Spec definiert keine dedizierte Page; Bestandsinfo
  wird additiv in Fertilizer/Equipment-Views gezeigt. Falls out of scope halten → im WP dokumentieren.)

**Akzeptanzkriterien:**
- `POST /api/v1/inventree/connections` + `POST …/{key}/health-check` liefert `{"healthy": true}` gegen gemockte InvenTree-Instanz.
- `POST /api/v1/inventree/references/link` (fertilizer→part, `auto_deduct=true`) persistiert Mapping; `GET /api/v1/fertilizers/{key}` enthält Bestandsinfo.
- Verbrauchsbuchung erzeugt Pending-Transaktion; `push_pending_transactions` sendet `POST /api/stock/remove/` (gemockt) und markiert erledigt.
- `GET /api/v1/equipment/by-location/{key}` listet zugeordnetes Equipment.
- Bei nicht konfigurierter Instanz kein 500; `health_check`→`ready:false`.
- Adapter-Unit-Tests mit gemockten HTTP-Responses; kein `NotImplementedError` mehr.

**Spezialist-Agent:** `fullstack-developer`. **Aufwand:** M. **Abhängigkeiten:** REQ-014/004 (implementiert).

---

### WP-017 — REQ-017 Vermehrung/Lineage vervollständigen

**Problem.** `PropagationService.record()` ist echt und DI-verdrahtet (D10), aber `list_for_plant`
und die **gesamte** `LineageEngine` (Ahnen-Traversal, Graft-Kompatibilität) werfen NotImplementedError.
Der `/propagation`-Router ist leer, keine Lineage-/Batch-/Protocol-/Mother-Endpunkte, keine Frontend-Page.

**Umzusetzen (Spec-Soll §2/§3):**
- `PropagationService.list_for_plant` echt (Query gegen `propagation`-Collection je Pflanze).
- `LineageEngine.trace_ancestors` (Graph-Traversal über Edge `descended_from`, `LineagePath`),
  `LineageEngine.is_graft_compatible` (Genus/Family-Regel gemäß §3), plus Nachkommen-Traversal.
- ~30 REST-Endpunkte (§3, Z. 1404–1448): Events (`POST/GET/GET{key}`, `PATCH …/outcome`,
  `PATCH …/progress`), Batches (inkl. `POST …/{key}/finalize` → Übergabe an PlantingRun), Protocols
  (CRUD + `/stats`), Mothers (`/designate`, `/retire`, `/health`), Lineage
  (`GET /api/v1/plant-instances/{key}/lineage`, `/descendants`,
  `GET /api/v1/propagation/graft-compatibility?scion_key=…&rootstock_key=…`), Phenotypes, Stats.
- Repository für Batches/Protocols/Mothers; Phasen-Eintrittsmatrix (§5) an REQ-003-Lifecycle koppeln.
- Seed-Daten (§ Seed-Daten) für Protokoll-Templates.
- Frontend `pages/propagation/PropagationPage.tsx`: Event-/Batch-Erfassung, Lineage-Ansicht
  (Ahnen/Nachkommen), Graft-Check; API-Layer + Slice; scaffoldNotice entfernen; Routing + i18n.

**Betroffene Dateien/Pfade:**
- `domain/services/propagation_service.py`, `domain/engines/lineage_engine.py`,
  `domain/models/propagation.py` (erweitern), neue `data_access/repositories/propagation_repository.py`,
  `api/v1/propagation/router.py` + neue `schemas.py`, Lineage-Endpunkte ggf. in
  `api/v1/plant_instances/`.
- Wiring: `api/v1/router.py`, Graph-Setup, Seed-Daten unter `migrations/seed_data/`.
- Frontend: `pages/propagation/PropagationPage.tsx`, `api/propagation.ts`, Routing, i18n, `api/types.ts`.

**Akzeptanzkriterien:**
- `POST /api/v1/propagation/events` legt Event an; `PATCH …/{key}/progress` und `…/outcome` aktualisieren korrekt.
- `GET /api/v1/plant-instances/{key}/lineage` liefert Ahnenkette über `descended_from` (mehrstufig).
- `graft-compatibility` liefert `compatible:true` bei gleichem Genus (tomato/tomato) und `false` bei genus-fremd (tomato/cucumber).
- `POST /api/v1/propagation/batches/{key}/finalize` übergibt Ergebnis-Pflanzen an einen PlantingRun.
- Kein `NotImplementedError` mehr in Service **und** Engine; Router registriert und im OpenAPI sichtbar.
- Frontend-Page ohne `scaffoldNotice`; `data-testid="propagation-page"` bleibt.

**Spezialist-Agent:** `fullstack-developer`. **Aufwand:** L. **Abhängigkeiten:** REQ-019/003/013 (implementiert).

---

### WP-018 — REQ-018 Umgebungssteuerung/Aktorik ausimplementieren

**Problem.** `ActuatorService` wirft NotImplementedError, kein Control-Loop, kein Prioritätssystem,
kein Repository, leerer Router. Der voll implementierte `HomeAssistantClient` (`ha_client.py`) wird
nicht genutzt. Die Sensor→Aktor-Schleife (REQ-005 → Aktorik) ist nicht geschlossen.

**Umzusetzen (Spec-Soll §2/§3):**
- `ActuatorService` echt: `list_for_tenant`, `set_state` (Befehl über `HomeAssistantClient.call_service`
  bzw. MQTT/manual je Protokoll), Actuator-Repository.
- Control-Loop-Engine (§3 Engines): Sensor→Aktor mit **Hysterese**; Prioritätssystem
  **manual override > safety rules > sensor rules > schedules**; graceful degradation bei HA-Ausfall
  (Fallback-Task).
- Rule-/Schedule-Modelle (§2 embedded), PhaseControlProfile-Collection.
- ~35 REST-Endpunkte (§3, Z. 1346–1398): Actuators-CRUD (inkl. `/api/v1/locations/{key}/actuators`),
  Command/Override (`/command`, `/override` POST+DELETE, `/state`), Schedules (CRUD + `/toggle`),
  Rules (CRUD + `/toggle`, `POST /api/v1/rules/{key}/test` Dry-Run), Events+Stats,
  PhaseControlProfiles (CRUD + `/apply`), HA-Integration (`/api/v1/integrations/home-assistant/status|entities|test`),
  Location-Status/Energy, plus `POST /api/v1/emergency-stop` (§1, Notabschaltung).
- Seed-Daten (§ Seed-Daten) für Profile/Regel-Templates.
- Frontend `pages/environment/EnvironmentControlPage.tsx`: Aktor-Liste + Zustand, Command/Override,
  Regel-/Schedule-Verwaltung; API-Layer + Slice; scaffoldNotice entfernen; Routing + i18n.
- **HA-Custom-Integration-Seite** (Entities/Services für Aktorik) liegt im **separaten Repo
  `kamerplanter-ha`** und wird **nicht** in diesem WP geändert — nur Backend-Endpunkte, die die
  HA-Integration konsumiert. Optionale Nachziehung dort per `ha-integration-developer` / Skill
  `/deploy-ha` als eigenständiges Follow-up.

**Betroffene Dateien/Pfade:**
- `domain/services/actuator_service.py`, `domain/models/actuator.py` (erweitern),
  neue `domain/engines/actuator_control_engine.py`, neue
  `data_access/repositories/actuator_repository.py`, `data_access/external/ha_client.py` (nur nutzen),
  `api/v1/actuators/router.py` + neue `schemas.py`, ggf. neue Router `api/v1/rules/`,
  `api/v1/phase_control_profiles/`, `api/v1/integrations/`.
- Wiring: `api/v1/router.py`, Graph-Setup, Celery-Tasks (Control-Loop/Fallback), Seed-Daten.
- Frontend: `pages/environment/EnvironmentControlPage.tsx`, `api/environment.ts`, Routing, i18n, `api/types.ts`.

**Akzeptanzkriterien:**
- `POST /api/v1/actuators/{key}/override` setzt zeitlich begrenzten Manual-Override, der Sensor-Regeln überstimmt.
- Control-Loop schaltet erst bei Überschreiten der oberen Hysterese-Schwelle ein und erst unter der unteren wieder aus (Einheitentest).
- Prioritätsauflösung: bei gleichzeitiger Safety- und Sensor-Regel gewinnt Safety.
- `POST /api/v1/rules/{key}/test` liefert Dry-Run-Ergebnis ohne realen Schaltbefehl.
- HA-Ausfall führt zu Fallback-Task statt Crash (graceful degradation, Test mit gemocktem HA-Fehler).
- `POST /api/v1/emergency-stop` schaltet definierte Szenarien ab.
- Kein `NotImplementedError` mehr; Router registriert; Frontend-Page ohne `scaffoldNotice`.

**Spezialist-Agent:** `fullstack-developer` (Backend + Frontend); **HA-Integration-Seite separat**
`ha-integration-developer` (eigenes Repo, nicht Teil der DoD dieses WP). **Aufwand:** L.
**Abhängigkeiten:** REQ-005/003/006 (implementiert).

---

### WP-026 — REQ-026 Aquaponik-Management ausimplementieren

**Problem.** `AquaponikService` wirft NotImplementedError, es fehlen sämtliche Modelle/Collections,
die pH-/Ammoniak-/Nitrat-Balance-Logik, Fisch-Pflanze-Kompatibilität und ~32 Endpunkte. Der voll
implementierte `HydroSystemMonitor` (Runoff/EC) ist nirgends verdrahtet → als Vorleistung einbinden.

**Umzusetzen (Spec-Soll §2/§3/§4):**
- Modelle + Collections (§2): `AquaponicSystem`, `FishStock`, `WaterTest` (immutable), `FishSpecies`;
  Edges `compatible_fish_plant`/`incompatible_fish_plant`.
- Domänenlogik (§3): freie-Ammoniak-Berechnung aus TAN/pH/Temp, Biofilter-Cycling-Fortschritt,
  FCR-Analyse, Nährstoffdefizit-Analyse (Fe/K/Ca/Mg), Fütterungsempfehlung (temperaturkorrigiert +
  Cycling-Faktor), Safety/Alerts nach Severity. `HydroSystemMonitor` einbinden.
- ~32 Endpunkte (§4, 8 Gruppen), tenant-scoped Router `/api/v1/t/{tenant_slug}/aquaponics`:
  Systems (6, inkl. `POST …/cycling-status`), Fish-Stocks (6, inkl. `/mortality`, `/biomass-history`),
  Water-Tests (5, inkl. `/water-quality-status`, `/nitrogen-cycle-chart`, `/cycling-progress`),
  Feeding (4, inkl. `/feeding-recommendation`, `/fcr-analysis`), Supplementation (3, inkl.
  `/deficiency-check`), Safety (2), Health (2). **Plus globaler** Router `/api/v1/fish-species` (4,
  Seed-Daten, inkl. `/{key}/compatible-plants` Graph-Traversal, `/by-temperature-zone/{zone}`).
- Seed-Daten (§2): Fischarten + Kompatibilitäts-Edges. Enums (§3) in dreifacher Single-Source.
- Frontend `pages/aquaponik/AquaponikPage.tsx`: System-Übersicht, Wassertest-Erfassung + N-Zyklus-
  Diagramm, Fischbestand, Alerts; API-Layer + Slice; scaffoldNotice entfernen; Routing + i18n.

**Betroffene Dateien/Pfade:**
- `domain/services/aquaponik_service.py`, neue `domain/models/aquaponik.py`,
  `domain/engines/hydro_system_monitor.py` (nur einbinden), neue
  `data_access/repositories/aquaponik_repository.py`, `api/v1/aquaponik/router.py` (+ tenant_router)
  + neue `schemas.py`, neuer `api/v1/fish_species/router.py`.
- Wiring: **`api/v1/tenant_scoped/router.py`** (aquaponics) **und** `api/v1/router.py` (fish-species),
  Graph-Setup, Seed-Daten, `common/enums.py`.
- Frontend: `pages/aquaponik/AquaponikPage.tsx`, `api/aquaponik.ts`, Routing, i18n, `api/types.ts`.

**Akzeptanzkriterien:**
- `POST /api/v1/t/{slug}/aquaponics/systems` + `POST …/fish-stocks` legt System mit Besatz an.
- `POST …/water-tests` berechnet `free_ammonia` aus TAN/pH/Temp und persistiert immutable.
- `GET …/water-quality-status` liefert artspezifische Alarmstufen; `GET …/cycling-progress` schätzt Fertigstellung.
- `GET /api/v1/fish-species/{key}/compatible-plants` liefert kompatible Pflanzenarten via Graph-Traversal.
- `GET …/deficiency-check` liefert Fe/K/Ca/Mg-Defizit-Empfehlung.
- Kein `NotImplementedError` mehr; `HydroSystemMonitor` real genutzt; beide Router registriert; Frontend-Page ohne `scaffoldNotice`.

**Spezialist-Agent:** `fullstack-developer`. **Aufwand:** L. **Abhängigkeiten:** REQ-014/019/001 (implementiert).

---

## Parallelisierungs-Strategie

**Grundsatz.** Die fünf WPs sind fachlich und datei-disjunkt (eigener Service-/Model-/Router-/Page-
Namespace) → **fünf parallele Worktree-Agenten** (`isolation: worktree`, je ein Feature-Branch von
`develop`, gemäß `feedback_parallel_agents_shared_tree.md` — schreibende Agenten NIE auf geteiltem Tree).

**Empfohlene Worktrees:**
`task worktree:add -- feat/req-008-post-harvest` · `… feat/req-016-inventree` ·
`… feat/req-017-propagation` · `… feat/req-018-actuator` · `… feat/req-026-aquaponik`.

**Serialisierungspunkte (Merge-Konflikt-Risiko — zentrale Wiring-Dateien).** Diese Dateien berühren
mehrere WPs; sie sind **nicht** parallel gefahrlos editierbar:

| Datei | Betroffene WPs | Auflösung |
|---|---|---|
| `api/v1/router.py` (`api_router.include_router`) | 008, 016, 017, 018, **026 (fish-species)** | Additive One-Line-Includes; bei Merge sequenziell nachziehen. **Kein** Serienzwang zur Implementierung, nur der Include-Zeilen-Merge. |
| `api/v1/tenant_scoped/router.py` | **nur 026 (aquaponics)** | Einziges tenant-scoped WP → kollisionsfrei zu 008/016/017/018. |
| `frontend/src/` Routing-File (routes) | 008, 017, 018, 026 | Additive Route-Elemente; sequenziell mergen. |
| `i18n/locales/{de,en}/translation.json` | 008, 017, 018, 026 | Getrennte `pages.<domain>`-Teilbäume → geringes echtes Konfliktrisiko, aber gleiche Datei → beim Merge prüfen. |
| `common/enums.py` + `api/types.ts` + Seed-`$defs` | 016, 018, 026 (neue Enums) | Getrennte Enum-Namen → additiv; dreifach synchron halten. |
| Graph-Setup (Collections/Edges im named graph) | alle | Additive Registrierungen; sequenziell mergen. |

**Ausdrücklich KEIN Konflikt:** `domain/models/__init__.py` ist leer und wird nicht als Aggregat
genutzt → neue Modelle sind kollisionsfrei. WP-018 und WP-026 lesen Sensorik (REQ-005) und Tank
(REQ-014) **additiv** (kein Schreibkonflikt).

**Empfohlene Merge-Reihenfolge** (kleinste Wiring-Fläche zuerst, um Include-Konflikte zu minimieren):
WP-016 → WP-008 → WP-017 → WP-018 → WP-026. Jeder Merge zieht die `include_router`-Zeile additiv nach.

---

## Definition of Done (pro WP)

Ein WP ist erst „done", wenn **alle** Punkte erfüllt sind:

1. **Service echt implementiert** — keine `NotImplementedError` mehr in Service **und** zugehöriger
   Engine (WP-017: LineageEngine; WP-018: Control-Engine; WP-026: HydroSystemMonitor verdrahtet).
2. **Router-Endpunkte** — die in der jeweiligen Spec-Sektion gelisteten Endpunkte existieren, sind im
   OpenAPI sichtbar und im zentralen Router registriert (WP-026 zusätzlich im tenant_scoped-Router).
3. **Repository** — Persistenz über ein Repository gegen ArangoDB; neue Collections/Edges im
   Graph-Setup registriert.
4. **Tests** — Backend-Coverage ≥ 60 % (pytest + pytest-asyncio; Adapter/Engine gemockt),
   Frontend-Coverage ≥ 80 % (vitest) für WPs mit Frontend-Anteil (008, 017, 018, 026; 016 optional).
5. **i18n de/en vollständig** — alle neuen Keys in beiden Locales; `enums.<name>.<value>` gepflegt.
6. **`scaffoldNotice` entfernt** — die Frontend-Page zeigt echte Funktion; `data-testid` bleibt
   erhalten; Page im Routing registriert.
7. **Coverage-Audit grün** — `ruff` + `eslint` + `tsc` clean; Coverage-Gates erfüllt (vgl.
   MEMORY: v8-Scope-Falle → Page-Tests inkl. transitiver Kind-Module).
8. **Spec-Pflege** — REQ-Dokument bei Modelländerung mit Versions-Bump + Changelog-Zeile aktualisiert.
9. **PR-Flow** — Conventional-Commits-Titel, PR-Body 5 Sektionen, Label-Ableitung; einziger required
   Check ist `static` (Coverage-Fail = non-required Flake, vgl. MEMORY).

---

## Risiko-Hinweise

- **Wiring-Merge-Konflikte.** `api/v1/router.py`, `api/v1/tenant_scoped/router.py`, das Frontend-
  Routing-File und `i18n/…/translation.json` werden von mehreren parallelen WPs additiv berührt.
  Include-/Route-/Key-Zeilen beim Merge sequenziell nachziehen (empfohlene Reihenfolge oben). Muster
  bekannt aus #440 (parallele PSS-Fixes) und #404/#406 (tasks/__init__.py Celery-beat).
- **HA-Seite (WP-018) im separaten Repo.** Die Aktorik-Anbindung an Home Assistant (Entities/Services)
  lebt im Repo `kamerplanter-ha`; Skaffold deployt HA **nicht**. Dieses WP liefert nur die Backend-
  Endpunkte; die HA-Custom-Integration ist ein eigenständiges Follow-up (`ha-integration-developer`,
  Skill `/deploy-ha`: `kubectl cp` nach `homeassistant-0`, `kill 1` statt Pod-Delete).
- **REQ-016 Optionalität.** InvenTree ist optional (REQ-016 „optional"). Fehlende/deaktivierte
  Konfiguration darf keinen Startup-Crash oder 500 erzeugen — `health_check`→`ready:false` als
  definierter Zustand (vgl. MEMORY: Startup-Fail-Fast-Fallen bei Pflicht-Secrets/HA_URL).
- **Enum-dreifach-Drift.** Neue Enums (WP-016/018/026) müssen `common/enums.py`, Seed-`$defs` und
  `frontend/src/api/types.ts` synchron halten — es gibt **kein** OpenAPI-Codegen. Entfernter/umbenannter
  Enum ohne Migration crasht Seed-Reads auf Alt-Volumes (vgl. MEMORY: Enum-Retirement-Startup-Crash).
- **Frontend-Coverage-v8-Scope-Falle.** Neue Page-Tests senken die Quote, wenn transitive Kind-Module
  nicht mitgedeckt sind → Page **plus** Kinder testen (Expand-Ansatz, vgl. #435).
- **guard-nested-worktree-Hook.** Agent-Commits aus `.claude/worktrees/` werden abgelehnt; Worktrees
  über den zentralen Worktree-Root anlegen (`task worktree:add`), sonst Dateien manuell aus dem
  Worktree kopieren (vgl. MEMORY: REQ-395/#418).
- **REQ-017 Teil-Implementierung nicht brechen.** `propagation_service.record()` ist bereits per DI
  produktiv verdrahtet (D10) — beim Ausbauen die bestehende Factory-Signatur (`common/dependencies.py:161/181`)
  nicht regressiv verändern.
