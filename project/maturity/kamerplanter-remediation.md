# Capability Maturity — Remediation Backlog (Kamerplanter)

> **Zweck.** Task-ready Ableitung aus [`kamerplanter.md`](./kamerplanter.md): pro Capability die
> konkreten, autonom abarbeitbaren Arbeitspakete, die den Reifegrad Richtung **Gold** heben —
> mit betroffenen Dateien/Funktionen, Umsetzungsschritten und einer testbaren Definition of Done.
>
> **Grenze (load-bearing).** Dies ist weiterhin eine *advisory* Beschreibung der Lücken, **kein**
> Gate und **keine** Priorisierung. Die *Auswahl der Reihenfolge* und die *Ausführung* der Tasks
> sind nachgelagert: dieses Dokument ist der Input für `issue-orchestrate` / `feature-decompose` /
> `implementation-plan-author`, nicht deren Ersatz. Die „Kern-Reihenfolge"-Hinweise am Ende jedes
> Clusters sind Umsetzungs-*Empfehlungen* aus der Ist-Soll-Analyse, keine Roadmap-Entscheidung.
>
> **Task-ID-Schema.** `SYS-n` = systemischer Enabler · `Cn-A/B/C k` = Capability n, Achse A/B/C,
> Task k. Größen: XS/S/M/L. Jede Achsen-B/C-Gold-Task hängt am zutreffenden `SYS-`Enabler.

---

## Systemische Enabler (SYS) — Voraussetzung für Gold auf Achse B & C app-weit

Solange diese offen sind, ist **kein** Capability auf Achse B oder C Gold-fähig — unabhängig von der
capability-eigenen Codequalität. Sie sind Voraussetzung (`Abhängigkeit`) für die meisten Tasks unten.

- **SYS-1 — Complexity-Gate (McCabe ≤ 10).** *Fehlt:* kein Komplexitäts-Signal (ruff `select` ohne `C90`; kein radon/lizard). *Umsetzung:* Backend `C90` in `[tool.ruff.lint].select` + `[tool.ruff.lint.mccabe] max-complexity = 10`; Frontend ESLint `complexity: ["warn",10]`. Verletzer refactoren oder begründet `# noqa`. *DoD:* `ruff check --select C90` + ESLint-Complexity grün in CI. *Größe:* M.
- **SYS-2 — Duplication-Gate (≤ 3 %).** *Fehlt:* kein Duplication-Tool. *Umsetzung:* `jscpd` über `src/frontend/src` + `src/backend/app`, `--threshold 3`, Report als CI-Artefakt; Baseline abbauen. *DoD:* jscpd in CI, Duplication < 3 %. *Größe:* M.
- **SYS-3 — Source-SAST.** *Fehlt:* Nuclei/ZAP (NFR-014/015) scannen nur die deployte Instanz, nicht den Quellcode. *Umsetzung:* `bandit` (Backend) + `semgrep`/`eslint-plugin-security` (Frontend), SARIF → GitHub Code Scanning. *DoD:* SAST-Job je PR, keine offenen High/Critical. *Größe:* M.
- **SYS-4 — mypy strict + Backend-Coverage in CI.** *Fehlt:* `mypy strict` konfiguriert aber nicht in CI; `backend.yml` fährt `pytest tests/unit/` **ohne** `--cov` und **ohne** `tests/api/`+`tests/integration/`. *Umsetzung:* `mypy app` als CI-Schritt; `pytest --cov=app --cov-report=xml` inkl. `tests/api/`; Coverage als Signal (nicht als Gate). *DoD:* Backend-Coverage-% je Package sichtbar; `mypy app` grün; API-Test-Suite im CI-Scope. *Größe:* S–M.
- **SYS-5 — E2E- + Integrationstests an CI anbinden.** *Fehlt:* die Selenium-E2E-Suite hat **keinen CI-Runner** (bewusst, nur lokal `task test:e2e`); `tests/integration/` (3 echte Tests) laufen mangels ArangoDB `skip`. **Alle E2E-Journeys existieren bereits** (`tests/e2e/test_req0NN_*.py`) — es fehlt nur der Runner. *Umsetzung:* E2E-Job (nightly + gelabelt pro PR) mit Service-Containern (ArangoDB, PostgreSQL/pgvector, Redis/Valkey); Integrationstests entskippen; Traceability über `req<NNN>`-Marker. *DoD:* E2E- und Integration-Tier grün in CI, je Capability den Markern zuordenbar. *Größe:* L. *Der breiteste Enabler — schaltet Gold-C für praktisch alle 30 Capabilities frei.*

---

# Per-Capability-Tasks (C1 – C30)

## C1 — Stammdatenverwaltung (A=Silver B=Bronze C=Silver → **Bronze**) · GROW, CGA
**Haupthebel: Axis B (NFR-001-Layering).**

**Axis A → Gold**
- **C1-A1 Optimistic-Locking bei Species-Update** (M) — *Fehlt:* `revision`-basierte Konflikterkennung (REQ-001 §2). *Betroffen:* `species_service.py:31`, `api/v1/species/router.py:106`, `species/schemas.py`. *Umsetzung:* `revision` im Body, bei Mismatch `409 ConflictError`, sonst `revision+=1`. *DoD:* veraltete revision→409, Erfolg inkrementiert; Unit+API-Test.
- **C1-A2 Duplikatsprüfung Species/Cultivar anlegen** (S) — *Fehlt:* DoD „verhindert Mehrfach-Einträge". *Betroffen:* `species_service.py:20/59`. *Umsetzung:* vor Insert `scientific_name`(+tenant)-Scope prüfen → 409. *DoD:* Duplikat→409; Unit+API.
- **C1-A3 End-User-Doc „Stammdaten pflegen"** (M) — *Fehlt:* kein Doc für Species/Familien/Cultivar-Pflege. *Betroffen:* neu `docs/{de,en}/user-guide/stammdaten.md`, `mkdocs.yml`. *DoD:* DE+EN, Nav, strict-Build; deckt Filter/Overlay/hidden/Autoflower.
- **C1-A4 Autoflower-/Lifecycle-Pflichtfeld-Validierung** (M) — *Fehlt:* Cross-Field-Validator (`autoflower_*` nur bei `photoperiod_type='autoflower'`), v4.7-Achsen als Enum-Dropdowns statt Freitext. *Betroffen:* `species/schemas.py`, `models/species.py`. *DoD:* 422 bei Fehlkonfiguration; FE-Dropdowns.

**Axis B → Gold (Kern)**
- **C1-B1 `BotanicalFamilyService` + Interface einführen** (M) — *Fehlt:* es gibt weder Service noch `IBotanicalFamilyRepository`; Router spricht Arango-Repo direkt. *Betroffen:* neu `domain/interfaces/botanical_family_repository.py`, `domain/services/botanical_family_service.py`; `data_access/arango/botanical_family_repository.py` implementiert ABC. *DoD:* Service da, Repo implementiert ABC, `mypy` grün. *Abh:* SYS-4.
- **C1-B2 `botanical_families/router.py` auf Service umstellen** (M) — *Betroffen:* Router Z.7,9,28,30,36,46,57,64,71; neue `get_family_service`-Dependency. *DoD:* kein `data_access`-Import mehr; FE-Tests grün. *Abh:* C1-B1.
- **C1-B3 Familiennamen-Auflösung in `species/router.py` via Service** (M) — *Betroffen:* `species/router.py:12-15,23-52,55-62,93-115`. *Umsetzung:* `resolve_family_names(keys)` an Service ziehen; Router injiziert nur Services. *DoD:* keine `ArangoBotanicalFamilyRepository`-Ref mehr; `family_name` bleibt in Response. *Abh:* C1-B1, SYS-3.

**Axis C → Gold**
- **C1-C1 API-Integrationstests species + botanical_families** (M) — neu `tests/api/test_species_router.py`, `test_botanical_families_router.py`; CRUD+Family-Filter+404+409+Overlay-Merge. *Abh:* SYS-5, C1-B*.
- **C1-C2 E2E „Familie→Species→Cultivar anlegen"** (M) — `spec/e2e-testcases/TC-REQ-001.md`→Selenium, `req001`-Marker, −aceae-Validierung. *Abh:* SYS-5.
- **C1-C3 FE-Branch-Coverage stammdaten ≥90 %** (M) — 82.7 %→90 %; Overlay/hidden, Autoflower-Validierung, Filter-Leerzustand. *Betroffen:* `SpeciesCreateDialog/SpeciesListPage/BotanicalFamilyCreateDialog.test.tsx`.

## C2 — Standortverwaltung (A=Silver B=Silver C=Silver → **Silver**) · GROW, CGA, HOST

**Axis A → Gold**
- **C2-A1 Rekursive Hierarchie- & Fruchtfolge-Edge-Cases** (M) — `MAX_LOCATION_DEPTH`-Soft-Warning, zyklische `contains`, verwaister `parent_location_key`, LocationType-in-Verwendung→403, Fruchtfolge CRITICAL/WARNING/OK. *Betroffen:* `site_service.py`, `site_repository.py`, `sites/tenant_router.py:266`, `locations/`, `location_types/`. *DoD:* je Edge-Case grüner Negativtest.
- **C2-A2 GPS-Erfassung Graceful Degradation** (S–M) — `PERMISSION_DENIED`/`POSITION_UNAVAILABLE`/`TIMEOUT`/kein-HTTPS je lokalisiert, ohne `gps_coordinates` zu überschreiben. *Betroffen:* `SiteCreateDialog.tsx`, `SiteClimateSection.tsx`, `siteForm.ts`. *DoD:* 4 Fehlerpfade+Happy als Component-Test.
- **C2-A3 WaterSource-Soft-Warnings** (S) — GH-Plausibilität (`Ca*2.497+Mg*4.116` vs `gh_ppm` >30 %), Messalter >12 M, RO-Membran `ec_ms>0.05`; `ro_water_profile` bei `has_ro_system=false` ignoriert. *DoD:* 3 Regeln getestet, Warnungen im FE.
- **C2-A4 End-User-Doc je Audience** (M) — CGA (Zuweisung/Rollen) + HOST (Config/Retention) fehlen; nur GROW-Track da. *Betroffen:* `docs/{de,en}/user-guide/locations-substrates.md`.

**Axis B → Gold**
- **C2-B1 Messbare Signale + Interface-Docs** (S nach Enablern) — SYS-1/2/3/4; Router-Komplexität + Service-Docstrings prüfen. *Abh:* SYS-1..4.

**Axis C → Gold**
- **C2-C1 Coverage standorte ≥90 %** (M) — 82.6 %/83.3 %→90 %; Fehlerzweige aus A1/A2/A3; v8-Scope Page+Sections. *Abh:* C2-A1/A2/A3.
- **C2-C2 CI-E2E „Site→Location→Slot" + Contract** (M) — `TC-REQ-002`, `req002`, Contract gegen `sites/schemas.py`. *Abh:* SYS-5.

## C3 — Phasensteuerung / Lifecycle-Engine (A=Silver B=Silver C=Silver → **Silver**) · GROW
**Schnellster erster Gold-Kandidat.** E2E existiert (`test_req003_phasensteuerung.py::TestCoreLifecycleJourneyPhaseTransitions`, TC-003-046..048).

**Axis A → Gold**
- **C3-A1 growth-phases.md gegen Edge-Cases abgleichen** (M) — Korrekturmodus, Rückwärts-Sperre, Autoflower, Perennial-Restart, monokarpe Terminalphase, `is_reversion`/`is_premature`. *Betroffen:* `docs/{de,en}/user-guide/growth-phases.md`. *DoD:* jede Critical/Edge-Aktion aus TC-REQ-003 hat Doc-Abschnitt DE+EN.
- **C3-A2 Run-Membership-409 als Nutzerfehler dokumentieren** (S) — `phase.run_owned` („Phase wird vom Durchlauf verwaltet"). *Betroffen:* `growth-phases.md`/`planting-runs.md`.

**Axis B → Gold**
- **C3-B1 PhaseTransitionEngine Public-Interface dokumentieren** (S) — Docstrings `assert_transition_allowed`, `check_transition_due`, Restart/Zyklus, Raises `RunMembershipConflictError`. *Betroffen:* `phase_transition_engine.py` (305 Z.). *Abh:* SYS-1 (restliche B-Anhebung).

**Axis C → Gold**
- **C3-C1 `pages/phasen` in Coverage-Snapshot + ≥90 % Lines** (M) — heute „unavailable"; v8-Scope erweitern (misst nur importierte Dateien), 6 Komponenten auffüllen.
- **C3-C2 Phasen-Journey-E2E in CI** (M→S) — `test_req003_phasensteuerung.py`, `req003`, TC-003-046..048. *Abh:* SYS-5.

## C4 — Dünge-/Nährstoff-Logik (A=Silver B=Silver C=Silver → **Silver**) · GROW
**Einziger A-Gap ist Feature-Lücke (nicht nur Doc): copy-as-template — Backend-Clone existiert bereits.**

**Axis A → Gold**
- **C4-A1 Backend: Clone um `as_template` erweitern** (S) — *Fehlt:* System-Plan als tenant-eigene **Vorlage** (`is_template=true`); `repo.clone` setzt hart `False`. *Betroffen:* `nutrient_plans/schemas.py:203` (`CloneRequest`), `tenant_router.py:101`, `nutrient_plan_service.py:179`, `nutrient_plan_repository.py:249`. *Umsetzung:* `as_template: bool=False` durchreichen; `is_template=as_template`. *DoD:* `POST /{key}/clone` mit `as_template:true` → tenant-eigener Plan `is_template=true`, `cloned_from_key`, Deep-Copy; Unit+API testen beide Fälle.
- **C4-A2 FE: „Als Vorlage kopieren" verdrahten** (S) — *Fehlt:* Button hart `disabled` + veralteter Kommentar. *Betroffen:* `NutrientPlanDetailPage.tsx:90-106`, `api/endpoints/nutrient-plans.ts:57`, `useNutrientPlanData.ts`. *Umsetzung:* `as_template?` im Payload-Typ; `copyAsTemplate()`-Handler→clone→Notification→navigate; `disabled` weg; Kommentar löschen. *DoD:* Klick auf System-Plan kopiert+navigiert; Component-Test `data-testid=copy-as-template-button`. *Abh:* C4-A1.

**Axis B → Gold**
- **C4-B1 9 react-hooks-Warnings duengung beseitigen** (M) — `set-state-in-effect`/`preserve-manual-memoization` in `pages/duengung/**`. *DoD:* `eslint 'src/pages/duengung/**'`→0 Warnings.

**Axis C → Gold**
- **C4-C1 Branch-Coverage duengung ≥90 %** (M) — 84.5 %→90 %; Water-Mix-Modi (RO/Leitung), Legacy-EC-Fallback, neuer `as_template`-Zweig. *Abh:* C4-A2.
- **C4-C2 Nährstoffplan-E2E in CI** (M→S) — `test_req004_nutrient_plan.py`, `req004`. *Abh:* SYS-5.

## C5 — Hybrid-Sensorik (A=**Bronze** B=Silver C=Silver → **Bronze**) · GROW, HA
**Overall Bronze: substanzielle REQ-005-Feature-Lücken (Axis A). Zweitgrößter Substanz-Gap der App.**

**Axis A → Silver → Gold**
- **C5-A1 Fallback-Stufe 1: direkte IoT/MQTT-Ingestion** (L) — *Fehlt:* MQTT-Subscriber/Modbus-Pfad; Readings mit `source∈{mqtt_auto,modbus_auto}`+Provenance; Resolver-Kette auto→HA→weather→manual. *Betroffen:* `tasks/sensor_ingestion_tasks.py`, neuer MQTT-Adapter `data_access/external/`, `observation_service.py`, `models/observation.py`. *DoD:* MQTT-Reading mit korrekter `source`; Fallback-Reihenfolge unit-getestet; `data_freshness` OK/WARNING/CRITICAL; Doku „geplant"→„umgesetzt".
- **C5-A2 Provenance & Datenqualität** (L) — *Fehlt:* `quality_score` (Güte/Alterspenalty/Z-Score), Ausreißer-Flag (Z>3 warn/Z>4 crit), Interpolation kurzer Lücken (`source='interpolated'`, `MAX_INTERPOLATION_HOURS`). *Betroffen:* `observation_service.py`, neuer `SensorReadingValidator`, `SensorHistoryChart.tsx`. *DoD:* TC-005-035/-036 + Quality-Badge als Tests. *Abh:* C5-A1.
- **C5-A3 Kalibrierungs-Workflow (1-/2-/Multi-Point)** (L) — *Fehlt:* `SensorCalibration` (Offset/Factor, Factor 0.5–2.0), 90-Tage-Overdue. *Betroffen:* `sensor_service.py`, Sensor-Router, FE-Kalibrier-Dialog. *DoD:* TC-005-027..031; Overdue-Badge.
- **C5-A4 Sensor-Health & Offline-Auto-Task** (M) — *Fehlt:* `SensorHealth` online/degraded/offline, `check_sensor_health`, idempotente Manual-Task bei >24 h. *Betroffen:* `sensor_ingestion_tasks.py`, `sensor_service.py`, FE-Offline-Badge. *DoD:* TC-005-024/-025/-026; Idempotenz-Test.
- **C5-A5 End-User-Doc je Audience** (M) — `sensors.md` auf „umgesetzt"; HA-Integrator Sensor-Import-Contract; EN-Spiegel. *Abh:* C5-A1..A4.

**Axis B → Gold**
- **C5-B1 Neue Ingestion/Quality-Logik layer-konform + belegt** (S nach Enablern) — Adapter in `data_access/external/`, ABC in `domain/interfaces/`, Docstrings; SYS-1..4. *Abh:* SYS-1..4, C5-A1..A4.

**Axis C → Gold**
- **C5-C1 TimescaleDB-Repo-Tests in CI + neue Pfade abdecken** (M) — `test_observation_repository.py` (psycopg) in CI; Tests für MQTT/Interpolation/Z-Score/Kalibrierung/Health. *Abh:* SYS-4, C5-A1..A4.
- **C5-C2 CI-E2E Sensor-Workflow + HA-Contract** (M) — `TC-REQ-005`, `req005`; Contract gegen HA-facing Vertrag. *Abh:* SYS-5, C5-A4.

## C6 — Aufgabenplanung (A=Silver B=Silver C=Silver → **Silver**) · GROW, CGA
**Befund: Copy-as-Template-Backend + FE-API existieren bereits — nur der Button ist nicht verdrahtet (veralteter Kommentar).**

**Axis A → Gold**
- **C6-A1 Copy-as-Template-Button verdrahten** (S) — *Betroffen:* `WorkflowDetailPage.tsx:583-595`, `api/endpoints/tasks.ts:81` (`duplicateWorkflow` da), i18n `common.origin.*`. *Umsetzung:* onClick→Namens-Dialog („{name} (Kopie)")→`duplicateWorkflow`→navigate+Toast; Tooltip `copyAsTemplateUnavailable`→`copyAsTemplate`. *DoD:* System-Workflow erzeugt editierbare tenant-eigene Kopie inkl. Phasen/Task-Templates; Component-Test Dialog→API→Navigation.
- **C6-A2 End-User-Doc Copy-as-Template** (S) — `docs/{de,en}/user-guide/tasks.md`. *Abh:* C6-A1.

**Axis B → Gold**
- **C6-B1 Debt-Marker + toten Zweig entfernen** (XS) — `WorkflowDetailPage.tsx:579-595`; `grep "not implemented"` leer. *Abh:* C6-A1.

**Axis C → Gold**
- **C6-C1 Duplicate-Endpoint Contract-Test** (S) — `{name}`→201, tenant_key=Dupli-Tenant, `auto_generated=false`; Cross-Tenant-Isolation. *Abh:* SYS-5.
- **C6-C2 E2E Copy-as-Template** (S) — `TC-REQ-006.md` (in-edit), `req006`, Coverage neuer Zweige ≥90 %. *Abh:* C6-A1, SYS-5.

## C7 — Erntemanagement (A=Silver B=Silver C=Silver → **Silver**) · GROW

**Axis A → Gold**
- **C7-A1 Edge-/Failure Karenz-Gate + Reife-Prognose** (M) — fehlende GDD-Basis→Konfidenz „niedrig" statt Crash; Ernte trotz Karenz→422 klare i18n; leere Ertragsmetriken. *Betroffen:* harvest-Engines/Service, `pages/ernte/`. *DoD:* jeder TC-REQ-007-Störfall definiertes UI-Verhalten.
- **C7-A2 End-User-Doc Ernte** (S) — `harvest.md`, Reifefenster-Konfidenz + Karenz, Grading-Fact-Table A+/A/B/C/D.

**Axis B → Gold**
- **C7-B1 Docstrings Harvest-Engines** (S) — GDD, HarvestWindowPredictor. *Abh:* SYS-1/3.

**Axis C → Gold**
- **C7-C1 Contract-Test Harvest-API + Karenz-422** (S) — `complete_harvest_for_run` ändert NICHT `run.status` (#415). *Abh:* SYS-5.
- **C7-C2 E2E Ernte-Journey** (M) — „Charge→Qualität→Ertrag→abschließen"+Karenz-Blockade, `req007`. *Abh:* SYS-5.

## C8 — Post-Harvest (A=Silver B=Silver C=Silver → **Silver**) · GROW (+Mobile)

**Axis A → Gold**
- **C8-A1 Störfall-/Edge-Protokolle** (M) — Schimmel-Alert, Übertrocknung, RH-Grenze, illegale Statusübergänge (`fresh→drying→curing→aging→stored→consumed/disposed`). *Betroffen:* Service/Engine + pages (Mobile). *DoD:* alle TC-REQ-008-Störfälle, mobile-first.
- **C8-A2 End-User-Doc je Audience** (S) — `post-harvest.md` + guides/, spezies-spezifisch + Mobile.

**Axis B → Gold**
- **C8-B1 Statusmaschine entkomplexen + Interfaces** (M) — Transition-Tabelle/Guard statt Verzweigung. *Abh:* SYS-1.

**Axis C → Gold**
- **C8-C1 Statusmaschinen-Contract-Test** (M) — alle gültigen/ungültigen Übergänge + Karenz-Vorbedingung. *Abh:* SYS-4.
- **C8-C2 E2E Post-Harvest + Mobile** (M) — „fresh→curing mit Burping" Mobile-Breakpoint, `req008`. *Abh:* SYS-5.

## C9 — Dashboard (A=Silver B=Silver C=Silver → **Silver**) · GROW, CGA
**Am nächsten an Gold; dominanter Hebel = Branch-Coverage 61.3 %→90 %.**

**Axis A → Gold**
- **C9-A1 Edge-Cases Personalisierung/Edit-Grid dok + absichern** (M) — Overflow-Clamp (`useContentRowFloors`), md→sm-Repack, deterministische `instance_ids`, optimist. Save-Rollback. *DoD:* in `dashboard-personalization.md` + testgedeckt (C9-C1).
- **C9-A2 Community-Admin-Doku** (S) — viewer read-only-Sicht.

**Axis B → Gold**
- Systemisch (SYS-1/2/3/4); kein capability-lokaler Debt-Marker. Nach Enablern re-assessen.

**Axis C → Gold (Kern)**
- **C9-C1 Edit-Grid-Geometrie-Branches** (M) — `dashboardEditGridGeometry.ts` (87 LOC) + `useDashboardLayout.ts`: Overflow-Clamp, md/sm-Repack, Kollision, Leer-Layout, Reset. *DoD:* branches dieser Module ≥90 %.
- **C9-C2 WidgetConfigDialog + widgetRegistry Fallback-Branches** (M) — Validierung/Abbruch/Save; `GenericWidget`-Fallback.
- **C9-C3 `dashboard_service.py` Backend-Branches** (M) — `hasattr`-maskierte 0-Werte (#399-Regression), Care-Reminder-Kategorie-Filter. *Abh:* SYS-4.
- **C9-C4 Storage-Failure-Pfad** (S) — korrupter/fehlender localStorage→Fallback-Default (jsdom-Gap).

## C10 — IPM-System (A=**Bronze** B=**Bronze** C=Silver → **Bronze**) · GROW, GDPR, HOST
**Der einzige real unbuilt Fusion-Kern der App ist C10-A1 (REQ-043, Spec-Status `Entwurf`). Kindwise/Local-Pest-TODOs sind extern blockiert — nur kapselbar.**

**Axis A → Silver → Gold**
- **C10-A1 `HealthAssessmentEngine` (REQ-043 §4.3) implementieren** (L) — *Fehlt:* pure-logic Engine, die Bild+Kontext zu `health_status` (0–100, Ampel, Konfidenz, Faktoren, Abstention) fusioniert. `get_pest_signal_for_plant` (`pest_detection_service.py:183-207`) liefert das Befall-Signal bereits konsumierbar; die Fusion fehlt. *Betroffen:* neu `domain/engines/health_assessment_engine.py`; Collection `health_assessments` (§5.1) + Repo+Service. *Umsetzung:* Signatur/Gewichte aus §4.3 (`WEIGHTS={image:.40,sensor:.20,ipm:.20,care:.10,symptom:.10}`, `CONFIDENCE_ABSTAIN=.35`); Teil-Scores 0..1; auf vorhandene Signale renormalisierte Fusion; Ampel green≥70/yellow40-69/red<40/unknown; `contributing_signals[]`; Bild optional. *DoD:* pure-logic, deterministisch; Snapshot persistiert (Bild NICHT, nur `image_hash`); **löst nie** Behandlung/Karenz aus. *Abh:* SYS-4; REQ-005/022-Resolver (sonst als injizierte Callables mocken).
- **C10-A2 Kindwise-DSGVO/Schema-Deferral kapseln (WP-7)** (S) — TODO `kindwise_pest_adapter.py:8,69`→Tracking-Issue; Adapter default-disabled hinter `pest_detection_cloud_enabled`+Consent; `_parse` defensiv. *DoD:* kein Inline-TODO; `_parse`-Test für leere Payload; `is_configured()==False` bei fehlendem Flag. *Abh:* extern (nur Kapselung autonom).
- **C10-A3 Lokale Modellwahl-Deferral kapseln (WP-1/2/3)** (S) — TODO `local_pest_adapters.py:104`→Issue; Graceful-Degradation testen; Symptom-Adapter als aktiver Default. *DoD:* kein Inline-TODO; `get_status()` meldet Detector `configured=false` ohne Crash.

**Axis B → Gold**
- **C10-B1 Kernpfad-TODOs auflösen** (S) — deckt A1/A2/A3; `grep "TODO(REQ-04" src/backend/app` leer. Rest systemisch SYS-1/3/4.

**Axis C → Gold**
- **C10-C1 Unit-Tests `HealthAssessmentEngine`** (M) — Fusion-Matrix, nur-Kontext, Abstention, Renormalisierung, Ampel-Grenzen, Konfidenz. *Abh:* C10-A1.
- **C10-C2 Karenz-Gate + „nie Auto-Treatment"-Negativtest** (S) — Detection/Assessment erzeugt nie `treatment_application`.
- **C10-C3 Branch-Lift pflanzenschutz 76 %→90 %** (M) — Consent-Gate (Light→`ConsentRequiredError`), EXIF-Strip-Fehler, Größen-/Leer-Upload-Guard. *Abh:* SYS-4.

## C11 — Externe Stammdatenanreicherung (A=Silver B=Silver C=Silver → **Silver**) · GROW, PROV

**Axis A → Gold**
- **C11-A1 OpenFarm-Adapter implementieren** (L) — *Fehlt:* REQ-011 §6 verlangt 3 Adapter (Perenual/GBIF/**OpenFarm**); OpenFarm fehlt → auch Companion-`compatible_with`-Edge (Szenario 4). *Betroffen:* neu `data_access/external/openfarm_adapter.py`, Registry, Sync-Mapping. *DoD:* Sync erzeugt `compatible_with`-Edge (Daucus carota/Allium cepa); Unit mit Mock.
- **C11-A2 Operator-Doc „Externe Anreicherung"** (M) — Quellenverwaltung, Sync (inkr./full), Accept/Reject, Health. *Betroffen:* neu `docs/{de,en}/user-guide/enrichment.md`.
- **C11-A3 inaturalist-TODO auflösen/umhängen** (S) — `inaturalist_media_client.py:46` (REQ-044 §8 Fallback)→implementieren oder als REQ-044-Issue verlinken.

**Axis B → Gold**
- **C11-B1 Adapter-Boilerplate deduplizieren** (M) — Retry/Backoff (max 3, Szenario 6)+Rate-Limit in `_base_http_adapter.py`. *DoD:* jscpd <3 %. *Abh:* SYS-2, C11-A1. (Rest SYS-1/3.)

**Axis C → Gold**
- **C11-C1 Contract-Tests Provider-Grenze** (M) — fixe JSON-Fixtures GBIF/Perenual/OpenFarm→Mapping (Schema-Drift-Guard). *Abh:* C11-A1.
- **C11-C2 Failure-/Edge Sync-Resilienz** (M) — 503+3 Retries (andere Quellen laufen), lokale Hoheit (kein Overwrite). *DoD:* Backend-Coverage Enrichment ≥90 %. *Abh:* SYS-4.

## C12 — Stammdaten-Import (A=Silver B=Silver C=**Bronze** → **Bronze**) · GROW, CGA
**Zweitgrößter Hebel: Axis C — `ImportPage.tsx` komplett ungetestet.**

**Axis A → Gold**
- **C12-A1 Dateivalidierung Edge-Cases** (M) — 10-MB-Limit (413/422), Nicht-`.csv` ablehnen, Encoding/Delimiter-Sniffing. *Betroffen:* `import_service.py:26`, `import/router.py`.
- **C12-A2 Duplikatstrategie-Vollpfad update/fail** (M) — Szenario 4/5 (`records_updated`/`records_failed`, Rollback). *Betroffen:* `import_engine.py`, `import_service.py:52`.
- **C12-A3 Feeding-Chart-Import + Fuzzy-Matching** (L) — §3.8 NutrientPlan-Import, exakt+fuzzy Produkt-Match, 5 Community-Templates, `CLONED_FROM`. *DoD:* Feeding-CSV→NutrientPlan+gematchte Fertilizer.

**Axis B → Gold**
- **C12-B1 Validator-Komplexität & Duplication senken** (M) — Feldregeln datengetrieben (Registry) statt per-Entität-Copy. *DoD:* ruff C90≤10, jscpd<3 %. *Abh:* SYS-1/2.

**Axis C → Gold (Kern)**
- **C12-C1 FE-Component-Test `ImportPage.tsx`** (M) — Upload-Formular, Entitäts-Dropdown, Duplikatstrategie, Button-Disable, Template-Download, Preview-Farbkodierung. *DoD:* Component-Test grün, kein act()-Warning.
- **C12-C2 API-Integrationstest Import-Router** (M) — Upload→preview_ready→confirm, Template-Download, Abbruch, Größen-/Typ-Reject. *Abh:* SYS-5, C12-A1.
- **C12-C3 E2E CSV-Import + Failure/Edge** (M) — Szenario 1/2/3, `req012`; Backend-Coverage ≥90 %. *Abh:* SYS-5, SYS-4.

## C13 — Pflanzdurchlauf (A=Silver B=Silver C=**Bronze** → **Bronze**) · GROW, CGA
**Overall-Bronze-Treiber: Axis C (Coverage 72.6 %). Höchste Warning-Dichte des Repos (22). B+C zusammen umsetzen.**

**Axis A → Gold**
- **C13-A1 planting-runs.md um Sukzession + Batch-409** (M) — Sukzessions-Intervalle, `phase.batch_run_owned` (All-or-Nothing). *Betroffen:* `docs/{de,en}/user-guide/planting-runs.md`.

**Axis B → Gold**
- **C13-B1 22 react-hooks-Warnings durchlaeufe auf 0** (M) — 11 Dateien: `ActivityPlanTab`, `AdoptPlantsDialog`, `BatchPhaseTransitionDialog`, `PhaseHistoryTable` (+`exhaustive-deps`-disable), `PlantingRunCreateDialog` (2×), `PlantingRunDetailPage` (2×), `PlantingRunEditDialog` (`immutability`), `RunPhaseEditor` (+disable), `WaterMixSummaryCard`, `WateringConfirmDialog`. *DoD:* `eslint 'src/pages/durchlaeufe/**'`→0 Warnings, keine neuen Disables.

**Axis C → Gold (Kern)**
- **C13-C1 Component-Tests ungetestete durchlaeufe-Kernkomponenten** (L) — nur 4/19 getestet; Priorität verzweigungsreiche: `BatchPhaseTransitionDialog` (Konfliktpfad), `RunPhaseEditor` (Korrekturmodus), `WaterMixSummaryCard` (RO-Modi), `PlantingRunCreateDialog`. *DoD:* durchlaeufe Lines **und** Branches ≥90 %.
- **C13-C2 Pflanzdurchlauf-E2E in CI** (M→S) — `test_req013_planting_run.py`, `req013`. *Abh:* SYS-5.

## C14 — Tankmanagement (A=Silver B=Silver C=Silver → **Silver**) · GROW

**Axis A → Gold**
- **C14-A1 Tank-Alert-Matrix & Sicherheits-Edge-Cases** (M–L) — pH/EC/Temp/DO/ORP je Tank-Typ, EC-Abweichung vs NutrientPlan (>20 % warn/>30 % alarm), Q10-Lösungsalter, Füllstand<20 %, `tank_safe=false`→WateringEvent-Empfehlung, `stock_solution` A+B via `feeds_from`. *Betroffen:* `tank_service.py`, `tank_engine.py`, `TankDetailPage.tsx`.
- **C14-A2 Wasserquellen-Kaskade-Transparenz** (S–M) — `water_defaults_source` (explicit/nutrient_plan/site_profile/manual) via `WaterMixCalculator.resolve_water_defaults()`. *Betroffen:* `tanks/schemas.py`, `TankFillCreateDialog.tsx`. *Abh:* REQ-004.
- **C14-A3 GROW-Doku auf Gold** (S–M) — Tank-Typen, Intervalle, Alerts, Befüllungshistorie. *Abh:* C14-A1.

**Axis B → Gold**
- **C14-B1 4 ESLint-Warnings auf 0** (S) — `TankDetailPage.tsx:303` (`set-state-in-effect`), `TankFillCreateDialog.tsx:83` (`watch()` incompatible-library). *DoD:* 0 Warnings, kein blindes disable.
- **C14-B2 Messbare Signale + Interfaces** (S nach Enablern) — SYS-1..4.

**Axis C → Gold**
- **C14-C1 Tank in Coverage-Snapshot + ≥90 %** (M) — Alert-Matrix/Kaskade-Tests; v8-Scope. *Abh:* C14-A1/A2.
- **C14-C2 CI-E2E „Tank befüllen→Alert/Wartung" + Contract** (M) — `TC-REQ-014`, `req014`. *Abh:* SYS-5.

## C15 — Kalenderansicht (A=**Bronze** B=**Bronze** C=Silver → **Bronze**) · GROW, CGA, iCal-Abonnent
**Kern-Task = C15-B1: Aggregations-AQL verliert für PhaseSequence-Arten stillschweigend Daten. Migration bereits gelaufen → JETZT umsetzbar.**

**Bronze → Silver (Kernpfad, Axis A+B)**
- **C15-B1 Aggregations-AQL um HAS_PHASE_SEQUENCE-Pfad erweitern (KERN)** (L) — *Defekt:* `calendar_aggregation_engine.py:18-20` TODO; AQL in `_phase_transition_events` (96-139), `_watering_forecast_events` (329-399), `_build_phase_intervals` traversiert nur Legacy `HAS_LIFECYCLE→GrowthPhase`. Bruch 1: `DOCUMENT(growth_phases/<pi.current_phase_key>)` → bei migrierten Plants ist der Key ein `phase_sequence_entries`-Key → null. Bruch 2: `FILTER LENGTH(gps)>0` filtert sequence-only-Arten komplett aus Timeline+Gieß-Vorschau. *Umsetzung:* (1) Zweig `Species-[HAS_PHASE_SEQUENCE]→PhaseSequence`→`phase_sequence_entries` SORT sequence_order, je Entry `DOCUMENT(phase_definitions/<phase_definition_key>)`; (2) Mapping name/duration(`override_duration_days??typical`)/watering_interval/`_key=entry._key`/is_terminal/allows_harvest; (3) phase_histories-Join über `phase_name` (PhaseDefinition.name==phase_histories.phase_name verifizieren); (4) `current_phase` cross-keyspace: growth_phases, bei null phase_sequence_entries→phase_definition_key→name; (5) pro Art EINEN Pfad (PhaseSequence Vorrang), `FILTER` durch „GrowthPhases ODER PhaseSequence-Entries" ersetzen. *DoD:* sequence-only-Art zeigt Phasen-Spans+Gieß-Vorschau; Legacy unverändert; keine Duplikate; TODO entfernt; Test beide Keyspaces+gemischter Tenant.
- **C15-B2 Regression-/Traceability-Test Doppelpfad** (S) — fail-closed Test: Art ohne LifecycleConfig fällt nicht aus Timeline (vor B1 rot). *Abh:* C15-B1.

**Silver → Gold (Axis A)**
- **C15-A1 iCal-Feed Sicherheits-/Edge-Cases (CF-001..007)** (M) — Token-Hash, Tenant-Bindung, Revocation, Anon-Rate-Limit 30/min, `expires_at`→410, keine PII in Titeln, Light-Token. *DoD:* jede MUSS-Regel Test + HTTP-Verhalten (403/410).
- **C15-A2 End-User-Doc je Audience** (M) — `calendar.md`: zentrale Ansicht/Filter, Aussaatkalender+Frost, webcal-Abo. *Abh:* C15-B1.

**Axis B → Gold**
- **C15-B3 AQL entkomplexen/refaktorieren** (M) — verzweigte Methoden in Helfer; kein Dup zwischen `_build_phase_intervals`/`_phase_transition_events`. *DoD:* SYS-1 grün, SYS-2 <3 %. *Abh:* C15-B1.

**Axis C → Gold**
- **C15-C1 Contract-Test Feed-Endpoint** (S) — Token→iCal RFC5545 + 403/410/Rate-Limit. *Abh:* C15-A1, SYS-5.
- **C15-C2 E2E Kalender+Aussaat+Feed** (M) — ≥1 E2E je Audience, `req015`, Coverage ≥90 %. *Abh:* SYS-5.

## C16 — InvenTree-Integration (optional) (A=Silver B=Silver C=**Bronze** → **Bronze**) · HOST, GROW

**Axis A → Gold**
- **C16-A1 End-User-Docs beide Audiences** (M) — HOST-Setup (URL/Token/SSL/Intervall/Health) + GROW-Nutzung (Part-Verlinkung, auto_deduct, Bestand); als „optional" markieren (Admonition). *Referenz:* TC-016-003..009/019..024/032.
- **C16-A2 Edge-/Failure-Cases verifizieren & dokumentieren** (M) — Graceful Degradation (TC-036/037), Retry-Zähler (038), Drift>20 % (045), SSL-Warnung (006). *Betroffen:* `inventree_sync_engine.py`, `inventree_adapter.py`, `InventreePage.tsx`. *DoD:* Kernfunktionen blocken nicht bei Ausfall; kein TODO/Stub im Sync-Pfad.

**Axis B → Gold**
- **C16-B1 Interface-Doku Adapter/Engine** (S) — Docstrings inkl. Token-Handling-Kontrakt (nie Klartext, TC-040).
- **C16-B2 SAST/Complexity/Duplication-Freigabe** (S nach Enablern) — *Abh:* SYS-1/2/3.

**Axis C → Gold (Kern)**
- **C16-C1 FE-Component-Tests EquipmentDialog + InventreePage-Ausbau** (M) — `EquipmentDialog.test.tsx` (fehlt komplett), Filter/Status-Lifecycle, Token nie Klartext (040), Rotation (041). *DoD:* Coverage inventree lines ≥90 %.
- **C16-C2 Integration/Contract-Test Sync-Engine + ConsumptionTracker** (M) — auto_deduct nach FeedingEvent/MaintenanceLog (032/034), no-tracking-ohne-flag (033), no-blocking-ohne-Verlinkung (035), gemockte HTTP-Responses+Drift+Timeout. *Abh:* C16-A2.
- **C16-C3 E2E InvenTree-Kernpfad in CI** (M) — neu `tests/e2e/test_req016_inventree.py`, HOST-Journey (Verbindung→Health→Part→verlinken→Bestand). *Abh:* SYS-5.

## C17 — Vermehrung/Lineage (A=Silver B=Silver C=Silver → **Silver**) · GROW
**C17-C1 (ArangoDB-Service-Job) aktiviert die einzige real vorhandene Tenant-Isolations-Integrationsprüfung — heute stumm geskippt.**

**Axis A → Gold**
- **C17-A1 propagation.md gegen Vermehrungsarten + Graft abgleichen** (S) — Klon/Samenkreuzung/Veredelung/Teilung + Graft-Kompatibilität (Genus/Familie). *Betroffen:* `docs/{de,en}/user-guide/propagation.md`.

**Axis B → Gold**
- **C17-B1 Lineage-Repo/Engine Public-Interface-Docstrings** (S) — ancestors/descendants/paths + Tenant-Pruning; PRUNE-vor-OPTIONS (#571). *Abh:* SYS-1.

**Axis C → Gold**
- **C17-C1 ArangoDB-Service + Integrationstest-Job in CI** (M) — `test_propagation_lineage_tenant_isolation.py` ist `skipif(not ARANGO_AVAILABLE)`; `backend.yml:62` fährt nur `tests/unit/`. *Umsetzung:* `services: arangodb:3.11` (Port 8529, `ARANGO_ROOT_PASSWORD=rootpassword`), Step `pytest tests/integration/ -v`; Skip löst automatisch aus. *DoD:* Test **passed** (nicht skipped). *Abh:* SYS-5 (sibling; eigenständig als Service-Job umsetzbar).
- **C17-C2 Lineage-E2E in CI** (M→S) — `test_req017_propagation.py`, `req017`. *Abh:* SYS-5.

## C18 — Umgebungssteuerung/Aktorik (A=**Bronze** B=Silver C=Silver → **Bronze**) · GROW, HA
**Größter Substanz-Gap der App: vollständiges Backend, aber keine UI. Alle A-Tasks bauen die fehlende Bedienoberfläche.**

**Axis A → Silver → Gold**
- **C18-A1 UI für Zeitpläne & Regeln (Hysterese/Compound/Safety)** (L) — *Fehlt:* FE-Formulare/Listen gegen `.../schedules`, `.../rules`, `/toggle` inkl. Hysterese-Config, Compound-AND/OR, `is_safety_rule`. *Betroffen:* `EnvironmentControlPage.tsx`+neue Dialoge, FE-API, i18n. *DoD:* TC-018-010..023 per UI; Docs „nur über API"-Admonition entfernt.
- **C18-A2 UI für Override, Phasen-Profile & Event-Log** (L) — Override-Dialog (`expires_at` Pflicht)+Banner; PhaseControlProfile-CRUD+„anwenden"; ControlEvent-Log (Aktor+Location); Energie-Ansicht. *Betroffen:* neue Views gegen `/override`, `/phase-control-profiles`, `/events`, `/control-events`, `/energy`. *DoD:* TC-018-024..038,040.
- **C18-A3 Failure-Cases sichtbar: Fail-Safe, HA-Degradation, Emergency, Dark-Phase** (M–L) — Sicherheits-Wertebereich/Fail-Safe je Aktor; `fallback_task`-Events bei HA-Ausfall; Emergency `water_leak`/`co2_leak` (heute nur `fire_alarm`); Dry-Run (`/rules/{key}/test`); Dark-Phase-Guard-Dialog. *DoD:* TC-018-008/022/030/039 + Emergency-Szenarien. *Abh:* C18-A1/A2.
- **C18-A4 Doku je Audience** (M) — `actuator-control.md` „nur über API"→„im UI"; HA-Integrator-Contract. *Abh:* C18-A1..A3.

**Axis B → Gold**
- **C18-B1 Neue UI + Signale sauber** (S–M nach Enablern) — ESLint 0-Warnings neue Env-Komponenten (useMemo-Konvention); SYS-1..4; Review. *Abh:* SYS-1..4, C18-A1..A3.

**Axis C → Gold**
- **C18-C1 Component/Unit-Coverage neue Steuerungs-UI ≥90 %** (M) — Schedule/Rule/Override/Profile/Log-Views + Backend-Unit `actuator_control_engine` (Priorität manual>safety>rule>schedule, Hysterese, Fail-Safe). *Abh:* C18-A1..A3.
- **C18-C2 CI-E2E „Regel→Aktor-Aktion" + HA-Contract** (M) — Regel→Dry-Run/Trigger→Event-Log, `req018`. *Abh:* SYS-5, C18-A1..A3.

## C19 — Substratverwaltung (A=Silver B=Silver C=Silver → **Silver**) · GROW

**Axis A → Gold**
- **C19-A1 Spec-Inkonsistenz Substrattyp-Anzahl (13 vs 14)** (S) — §6 „13" vs TC-019-009 „14". *Betroffen:* `REQ-019:327`, `TC-REQ-019:275`, `enums.py` `SubstrateType`. *DoD:* Enum/§6/TC nennen dieselbe Zahl.
- **C19-A2 Validierungs-Grenzen + Composition-Summe (=1.0)** (M) — pH∈[0,14], EC≥0, air_porosity∈[0,100], max_reuse≥1, Komponenten=1.0±ε. *Betroffen:* `substrates/schemas.py`/`models/substrate.py`.
- **C19-A3 Substrattemperatur-Warnung + CEC + Bewässerungs-Mapping** (M) — <12/>28 °C-Warnung, CEC-Feld, Substrattyp→Bewässerungsstrategie (REQ-018). *Betroffen:* `substrate_service.py`, `SubstrateBatch`.

**Axis B → Gold**
- **C19-B1 Docstrings `SubstrateService`/EC-Adapter** (S) — Recycling-Kriterien, EC-Netto. Rest SYS-1/3.

**Axis C → Gold**
- **C19-C1 API-Integrationstest Substrate-Router** (M) — CRUD+Batch+Typ-Filter+422+`filled_with`. *Abh:* SYS-5, C19-A2.
- **C19-C2 E2E Substrat-Recycling** (M) — `TC-REQ-019` Recycling+Create, `req019`. *Abh:* SYS-5.
- **C19-C3 Backend-Coverage sichtbar + ≥90 %** (S) — Substrat-Pakete in Messung. *Abh:* SYS-4.

## C20 — Onboarding-Wizard (A=Silver B=Silver C=**Bronze** → **Bronze**) · GROW, CGA

**Axis A → Gold**
- **C20-A1 Mode-Switch-Integration abschließen (TODO onboarding_service.py:240)** (M) — *geteilt mit C26-A1*; Light↔Full-Übernahme-Flow (TC-020 Gr.J, TC-027 §4/§5). *DoD:* kein TODO im Kernpfad. *Abh:* C26-A1.
- **C20-A2 End-User-Docs Onboarding** (S) — Erfahrungsstufe/Starter-Kit/Favoriten/Standort/Resume.

**Axis B → Gold**
- **C20-B1 2 Warnings + SAST-Freigabe** (S) — `pages/onboarding/**`; SYS-1/2/3.

**Axis C → Gold (Kern)**
- **C20-C1 Component-Tests pro Wizard-Step** (L) — 8 Steps ungetestet: `ExperienceLevelStep`(TC-007..011), `StarterKitStep`(014..019), `FavoriteSpeciesStep`(020..024), `SiteSetupStep`(025..032), `PlantSelection/PlantCountStep`(033..037), `NutrientPlanStep`(038..043), `SummaryStep`(044/045). *DoD:* Coverage onboarding lines ≥90 %.
- **C20-C2 Wizard-Orchestrierungstest** (M) — `OnboardingWizard.tsx`: dyn. Stepper-Anzahl, Resume(006), Skip(005), Complete(049), Fehler(047). *Abh:* C20-C1.
- **C20-C3 E2E-CI-Anbindung** (S) — `test_req020_*` in CI. *Abh:* SYS-5.

## C21 — UI-Erfahrungsstufen (A=Silver B=Silver C=**Bronze** → **Bronze**) · GROW

**Axis A → Gold**
- **C21-A1 End-User-Docs Erfahrungsstufen** (S) — Anfänger/Fortgeschritten/Experte, Wechsel, Downgrade behält Daten, „Alle Felder"-Toggle, Sichtbarkeitsmatrix §3.3.

**Axis B → Gold**
- **C21-B1 SAST/Complexity-Freigabe Querschnitt** (S) — `useExpertiseLevel.ts`, `ExpertiseFieldWrapper.tsx`, `ShowAllFieldsToggle.tsx`, Enums, Widget-Katalog; SYS-1/2/3.

**Axis C → Gold (Kern)**
- **C21-C1 Dedizierter Hook-/Wrapper-Test** (M) — kein `test_experience_level*`; `useExpertiseLevel` (Default Anfänger TC-012), `ExpertiseFieldWrapper` (ein-/ausblenden), `ShowAllFieldsToggle` (temporär+Reset, TC-020/021/022).
- **C21-C2 Feld-Sichtbarkeit pro Dialog + Navigations-Tiering** (L) — je Dialog (`SpeciesCreateDialog`, `PlantingRunCreateDialog`, `SiteCreateDialog`, `GrowthPhaseDialog`, `FertilizerCreateDialog`, TC-017..032) Feldmenge je Stufe; Navigations-Matrix (19 Pfade×3 Stufen, TC-058), gesperrter Menüpunkt-Tooltip (059). *Abh:* C21-C1.
- **C21-C3 E2E-CI-Anbindung** (S) — `test_req021_experience_level.py`. *Abh:* SYS-5.

## C22 — Pflegeerinnerungen (A=Silver B=Silver C=Silver → **Silver**) · GROW

**Axis A → Gold**
- **C22-A1 care-reminders.md/overwintering.md gegen Saison-/Hemisphären-Edge** (S) — Südhalbkugel-Verschiebung, SpringReturn-Uncovering. *Referenz:* TC-REQ-022.

**Axis B → Gold**
- **C22-B1 Care-Reminder-Engine Public-Interface-Docstrings** (S) — Preset-Auflösung/`FAMILY_CARE_MAP`/Reschedule. *Abh:* SYS-1.

**Axis C → Gold**
- **C22-C1 Ungemessenen pflege-FE-Baum + Component-Tests** (M) — nur `SpringReturnAssistant` gemessen; `CareProfileForm/CareProfileEditDialog/CareConfirmDialog` ungetestet. *DoD:* ganzer `pages/pflege`-Baum gemessen, Lines ≥90 %.
- **C22-C2 SpringReturnAssistant Branch 54.7 %→≥90 %** (M) — ~35 Bedingungen: Hemisphäre, Saison-Fenster, Schutzmethoden, Uncovering-Timing.
- **C22-C3 Pflege-E2E in CI** (M→S) — `test_req022_*` (3 Journeys), `req022`. *Abh:* SYS-5.

## C23 — Auth & Benutzerverwaltung (A=Silver B=Silver C=Silver → **Silver**) · GROW, CGA, HOST, GDPR

**Axis A → Gold**
- **C23-A1 Docs GROW/CGA (Login/Reset) + HOST (OIDC/Service-Accounts)** (M) — user-docs (Registrierung/Login/2-Provider) + developer-docs (OIDC-Config, API-Keys, JWT 15min/Refresh 30d, IP-Allowlist). *Referenz:* TC-023 §1-4/§8.

**Axis B → Gold**
- **C23-B1 13 eslint-Warnings pages/auth beseitigen** (S) — react-hooks/useMemo, kein Suppress. *DoD:* 0 Warnings.
- **C23-B2 SAST-Freigabe Auth-Pfad** (S) — `*auth_provider.py`, `oauth_engine`, `common/auth.py`; SYS-3.

**Axis C → Gold**
- **C23-C1 Branch-Coverage auth ≥90 %** (M) — 75.7 %→90 %: falsches Passwort(013), Sperre nach 5(014), unverifiziert(015), Enumeration-Schutz(005/020/021), Remember-Me(010), SSO-Buttons(011/012), Redirects(016/017).
- **C23-C2 Contract-Test Token/Refresh** (M) — Access-Ablauf→Refresh→Rotation→alte invalid; Service-Account API-key-only. *Abh:* SYS-4, teils SYS-5.
- **C23-C3 E2E Login/Refresh in CI** (M) — `test_req023_*`, Session-Persistenz über Refresh. *Abh:* SYS-5.

## C24 — Mandanten & RBAC (A=Silver B=Silver C=Silver → **Silver**) · CGA, HOST
**Cross-Tenant-Negativ-E2E (NFR-015) ist sicherheitskritisch — Findings blocken laut Spec immer.**

**Axis A → Gold**
- **C24-A1 Docs Rollen/Einladungen/Platform-Admin** (M) — CGA (admin/grower/viewer, Permission-Matrix, Einladung, Zuweisung TC-030..035) + HOST (Suspend/Reaktivieren TC-042..047).

**Axis B → Gold**
- **C24-B1 SAST/Complexity-Freigabe Tenant-Guards** (S) — `common/tenant_guard*`, `core/permissions`; SYS-1/3.

**Axis C → Gold**
- **C24-C1 Cross-Tenant-Negativ-E2E (NFR-015) in CI** (L) — neu `test_req024_cross_tenant_isolation.py`: Grower A liest/schreibt Tenant B nicht; Phasen-Transition fremd blockiert (039); persönlicher Tenant unsichtbar(002); suspendiert blockiert(045). *DoD:* negative Assertions (403/404, kein Leak). *Abh:* SYS-5.
- **C24-C2 Integration-Test un-skippen** (M) — `test_propagation_lineage_tenant_isolation.py`; ArangoDB-Service in CI. *Abh:* SYS-5.
- **C24-C3 FE-Page-Tests RBAC-UI** (M) — `TenantSettingsPage/AssignmentListPage/InvitationAcceptPage`; Viewer/Gärtner ohne Create/Assign(036..038), letzter-Admin-Schutz(017/019), abgelaufene Einladung(026/027). *DoD:* Coverage tenant-UI ≥90 %.

## C25 — DSGVO/Betroffenenrechte (A=Silver B=Silver C=Silver → **Silver**) · GDPR, GROW

**Axis A → Gold**
- **C25-A1 Guarded Email-Change-Pfad absichern (privacy_service.py:274)** (M) — *Befund:* `except NotImplementedError:` in `request_email_change` (Art. 16) verschluckt fehlenden Email-Adapter → in Full-Mode erhält Nutzer nie den Token (TC-025-032 unvollständig, ohne Fehler). *Umsetzung:* Full-Mode fail-loud statt silent skip; kein `pending`-Zombie; Start-up-Validierung analog Fail-Fast-Secrets; Guard nur für Light/Test. *DoD:* Full-Mode ohne echten Adapter → deterministischer Fehler; TC-025-032 reproduzierbar. *Abh:* C26 (Mode-Unterscheidung).
- **C25-A2 Docs Betroffenenrechte + Retention** (M) — GROW (Export/Löschung/Einschränkung/Email TC-004..034) + GDPR/developer (Retention NFR-011, Anonymisierung vs Löschung, Consent-Gates).

**Axis B → Gold**
- **C25-B1 SAST/Complexity Privacy/Erasure** (S) — `privacy_service.py`, Erasure/Retention-Engines; SYS-1/3.

**Axis C → Gold**
- **C25-C1 E2E Erasure + Export in CI** (M) — Export(010..015)+Löschung mit Passwort+Checkbox→Logout/Sessions invalid(016..020,038)+gelöscht/anonymisiert(021). *Abh:* SYS-5.
- **C25-C2 Retention/Anonymisierung Contract + API-Tests in Gate** (M) — `tests/api/test_privacy_router.py` in CI-Scope; Retention-Kette (90d→2y→5y, IP-Anon nach 7d, CanG/PflSchG). *Abh:* SYS-4.

## C26 — Light-Modus (A=Silver B=Silver C=**Bronze** → **Bronze**) · GROW, HOST

**Axis A → Gold**
- **C26-A1 Mode-Switch vollständig verdrahten (geteilt mit C20-A1)** (M) — `onboarding_service.py:240`; Light→Full (Übernahme-Dialog, Ressourcen-Anzahl TC-027-029/030/031/044) + Full→Light (System-Tenant sichtbar, Fremd-Tenant nicht, 033..036); Roundtrip erhält Daten(037). *DoD:* TC-027 §4/§5/§6, kein TODO. *Abh:* C20-A1.
- **C26-A2 Docs Light deployen (HOST) + nutzen (GROW)** (S) — Env-Flags Light/Full an 2 Stellen, `ENABLE_ENRICHMENT_LIGHTMODE`, kein Login/Consent.

**Axis B → Gold**
- **C26-B1 SAST/Complexity Feature-Flag-Mechanik** (S) — 9 light-Dateien; wiederholte `is_light`-Checks ggf. in Helper (Duplication). SYS-1/2/3.

**Axis C → Gold (Kern)**
- **C26-C1 Kohärente Light-Mode-Suite (Auth-Bypass + Modul-Sichtbarkeit)** (L) — neu `test/light/`+`test_light_mode_guards.py`: Routen Login/Register/Mitglieder nicht erreichbar(005..009), AppBar ohne Avatar/Logout(010), Sidebar ohne Mitglieder(011), AccountSettings limitiert(012), kein Consent-Banner(013), gesicherte Route kein 401(042), Full ohne Auth-Header abgelehnt(045). *DoD:* Coverage light-Pfad ≥90 %.
- **C26-C2 Mode-Endpoint + Seed-Idempotenz** (M) — `/api/v1/mode`(038/039), Seed idempotent(003), Root→System-Tenant(047). *Abh:* SYS-4.
- **C26-C3 E2E Light-Mode + Roundtrip in CI** (M) — `test_req027_light_mode.py`, Roundtrip(037). *Abh:* SYS-5, C26-A1.

## C27 — Mischkultur/Companion (A=Silver B=Silver C=Silver → **Silver**) · GROW, CGA

**Axis A → Gold**
- **C27-A1 Familien-Fallback (×0.8) + `unknown`-Klassifikation** (M) — Schritt 2 des 4-Schritt-Algorithmus (Family-Edge, Score×0.8, `match_level:"family"`); Paare ohne Edge→`unknown`. *Betroffen:* `companion_planting_engine.py` §3.4. *DoD:* Szenario 2 (0.68 family) + Szenario 3.
- **C27-A2 Slot-Nachbarschafts-Check (`adjacent_to`)** (M) — Nachbar-Slots laden, aktive Species prüfen (Szenario 5). *DoD:* `is_compatible:false`+Warnung.
- **C27-A3 Expertise-Level-Anpassung Empfehlungsanzahl** (M) — Beginner Top-3/Intermediate Top-5/Expert alle. *Betroffen:* `CompanionPlantingPage.tsx`, `SpeciesCompanionTab`.
- **C27-A4 Seed-Daten-Mindestmengen** (S) — §9 ≥25 `compatible_with`/≥15 `incompatible_with`/8/3 Familien-Paare. *Betroffen:* `companion_planting.yaml`.

**Axis B → Gold**
- **C27-B1 Engine-Public-Methoden dokumentieren** (S) — `get_companion_recommendations`, `validate_run_compatibility`, `check_compatibility`; 7 Effekt-Typen §2.3. SYS-1/3.

**Axis C → Gold**
- **C27-C1 E2E Mischkultur-Workflow** (M) — `TC-REQ-028` (003/005/007/009), `req028`. *Abh:* SYS-5.
- **C27-C2 Failure/Edge-Tests Engine** (M) — Szenario 2/3/4/5. *DoD:* Engine ≥90 % lines. *Abh:* C27-A1/A2, SYS-4.
- **C27-C3 Contract-Test 7 Companion-Endpoints + Run-Validierung** (M) — Schema (RunCompatibilityResult §5.3)+Auth (GET Mitglieder, POST/DELETE Platform-Admin). *Abh:* SYS-5.

## C28 — Druck/Export (A=Silver B=Silver C=**Bronze** → **Bronze**) · GROW, GDPR, Admin/Grower/Viewer
**Kern: Coverage verbreitern + WeasyPrint/tinyhtml5-Env-Fragilität entschärfen.**

**Axis C → Silver → Gold (Kern)**
- **C28-C1 PDF-Rendering testtechnisch entkoppeln** (M) — *Fehlt:* Trennung Template-Render (Jinja→HTML) von HTML→PDF. *Betroffen:* `print_engine.py`, `test_print_engine.py`, `test_print_service.py`. *Umsetzung:* `render_html(template,ctx,locale)->str` extrahieren; Assertions gegen HTML-String (deterministisch); `%PDF-`-Byte-Test hinter `pytest.importorskip("weasyprint")`/`@pytest.mark.pdf` (nur provisionierter CI-Job mit Pango/Cairo+gepinntem weasyprint/tinyhtml5). *DoD:* Kern-Tests ohne Systemlibs grün; PDF-Test skippt sauber. *Abh:* pyproject-Pin (Dep-SSOT).
- **C28-C2 Coverage auf alle Templates + Formate** (L) — je Template (Nährstoffplan/Pflege-Checkliste/Gießplan/Ernteprotokoll/Beetplan/Steckbrief/Kalender)+CSV+iCal+data-export; FE PrintButton/PlantLabelDialog/@media print. *DoD:* ≥90 %, alle TC-REQ-032-coverage_areas. *Abh:* C28-C1.
- **C28-C3 ≥1 E2E Druck/Export** (M) — Etikett+QR, Urlaubs-Gießplan-PDF, DSGVO-Export, `req032`. *Abh:* SYS-5.

**Axis A → Gold**
- **C28-A1 Fehlerzustände als AC härten** (S) — „keine Daten"/„PDF-Fehler"/„Timeout"→verständliche Meldung. *Betroffen:* `api/v1/print`, `print_service.py`, `PrintButton`.
- **C28-A2 End-User-Doc je Audience** (S) — `print-export.md`: Aushang/Etikett-QR, Urlaubsvertretung, DSGVO-Export, Berechtigungsstufen.

**Axis B → Gold**
- **C28-B1 Interfaces + SAST Render-Pfad** (S) — Docstrings; kein HTML-Injection (Jinja `select_autoescape`), QR-Payload-Sanitisierung. *Abh:* SYS-3.

## C29 — Wissensassistent/RAG (A=Silver B=Silver C=Silver → **Silver**) · GROW, HOST, GDPR
**Korrektur: Das Scanner-„Unrated" war ein Fehlflag auf totem Scaffold. Der echte Pfad ist `AiAssistantService`.**

**Axis A → Gold**
- **C29-A1 Verwaisten Scaffold `KiAssistentService` auflösen** (S) — *Fehlt:* toter Code mit `NotImplementedError` (nur Selbstreferenz). *Betroffen:* `domain/services/ki_assistent_service.py` (löschen). *Umsetzung:* Datei löschen; `grep -rn "KiAssistentService"` muss leer sein; kein neuer Stub. *DoD:* `grep NotImplementedError src/backend/app/domain/services` leer; ruff+pytest grün. *Abh:* keine (Voraussetzung für korrektes Re-Assessment).
- **C29-A2 Failure-/Edge-Cases des echten Antwortpfads härten** (M) — (a) KS-Timeout/Circuit-offen→Fallback `confidence=none`, HTTP 200 (W-011); (b) Cloud ohne `ai_cloud_processing`-Consent→403 (SEC-001); (c) `ConfidenceLevel.NONE`→KS-skip (ADR-002); (d) Light `context=null`, kein Tenant-Leak; (e) SSE-Stream-Abbruch. *Betroffen:* `ai_assistant_service.py` (`ask_public:403`, `stream_chat:508`, `health_check:462`), `knowledge_service_adapter.py`. *Abh:* C29-A1, SYS-5.
- **C29-A3 Audience-Docs vervollständigen** (M) — Self-hoster-Track (3-Stufen-Toggle-Env, Ollama-Local-First, KS-Deploy) + GDPR-Consent-Matrix (`ai_tenant_data_access`/`ai_cloud_processing`, Retention 90d). *Betroffen:* `ai-assistant.md` (user da), `guides/ai-plant-data-pipeline.md`.

**Axis B → Gold**
- **C29-B1 Debt-Marker beseitigen** (S) — deckt C29-A1; `grep "pending follow-up|TODO" *ai*` leer. Rest systemisch.

**Axis C → Gold**
- **C29-C1 Failure-/Edge-Tests Antwortpfad** (M) — je Test für A2 (a–e). *DoD:* `ai_assistant_service.py` branches ≥90 %. *Abh:* C29-A2, SYS-5.
- **C29-C2 Component-Test `KIAssistentPage`** (M) — `aiAvailable=false`→EmptyState; Frage→`AIResponse`; Fehler→`role=alert`; Light versteckt Chat; `<3` Zeichen disabled.
- **C29-C3 Contract-Test KS-Schema** (M) — `IKnowledgeService`-DTOs (`AskResult`, `KnowledgeChunk`, `to_ks_payload`) vs `knowledge-service/app/schemas.py`. *Abh:* SYS-5.
- **C29-C4 Component-Tests `AiChatDrawer`, `WhyDrawer`** (S) — SSE-Render, Fehler/Leer.

## C30 — Foto-Galerie & -Erkennung (A=Silver B=Silver C=Silver → **Silver**) · GROW, HOST, GDPR
**Korrektur: Scanner-Bronze beruhte auf totem `VisionEngine`-Scaffold. Identifikation läuft (DINOv2 #256, PlantNet).**

**Axis A → Gold**
- **C30-A1 Verwaisten Scaffold `VisionEngine` auflösen** (S) — toter Code (kein Referent); Normalisierung passiert inline in `local_embedding_adapter.identify`/`plantnet_adapter`. *Betroffen:* `domain/engines/vision_engine.py` (löschen). *Optional-DRY (SYS-2):* gemeinsame `_suggestion_from_match()` extrahieren statt separatem Scaffold. *DoD:* `grep "VisionEngine|normalise_predictions"` leer; kein `NotImplementedError` unter `domain/engines`.
- **C30-A2 `diagnose`-Out-of-Scope explizit als Kapabilitäts-Kontrakt** (S) — `local_embedding_adapter.py:86`/`plantnet_adapter.py:155` werfen `NotImplementedError` für `diagnose()` (korrekt: kein Health-Zweig). *Umsetzung:* `identification_service` gated via Capability-Flag `supports_health_assessment=False`; alternativ `UnsupportedCapabilityError` statt `NotImplementedError`. *DoD:* Test beweist Raise unerreichbar.
- **C30-A3 EXIF/DSGVO + NFR-013-Docs je Audience** (M) — User (Foto→Art), Self-hoster (Inference/DINOv2/S3), GDPR (EXIF-Strip, Bild nicht persistiert). *Betroffen:* `pest-detection.md`, Galerie-Doc.

**Axis B → Gold**
- **C30-B1 Debt-Marker beseitigen** (S) — deckt A1+A2; `grep "pending follow-up" domain/engines` leer.

**Axis C → Gold**
- **C30-C1 `test_s3_adapter.py` Env-Gap schließen** (M) — boto3 via `moto`/Fake mocken (3 lokale Failures deterministisch grün). *Abh:* SYS-4/5.
- **C30-C2 Branch-Lift recognition 82 %→90 %** (M) — `is_plant=False`, leere `suggestions`, Adapter-nicht-konfiguriert-Degradation, Namespace `local:`/`plantnet:`.
- **C30-C3 Contract-Test Inference-Service-Client** (S) — `InferenceServiceClient.match`-Response-Schema driftfest. *Abh:* SYS-5.

---

## Übergreifende Umsetzungs-Hinweise (advisory, keine Roadmap)

- **Scanner-Fehlflags zuerst schließen (je S):** `KiAssistentService` (C29-A1) + `VisionEngine` (C30-A1) löschen — hebt sofort C29 Unrated→Silver-Nachweis und beseitigt die einzigen lokalen Axis-B-Debt-Marker. Danach Re-Assess (`reassess`).
- **Overall-Bronze-Heber:** C1-B1..B3 (Layering), C15-B1 (Kalender-AQL), C5-A1..A4 (Sensorik-Stufen), C18-A1..A3 (Aktorik-UI), C10-A1 (HealthAssessmentEngine), C12-C1/C2, C13-B1+C1, C16-C*, C20-C1, C21-C1/C2, C26-C1, C28-C1/C2 — jeweils der named improvement-lever aus der Matrix.
- **Größter systemischer Hebel:** **SYS-5** (E2E+Integration in CI) schaltet den Gold-C-Schritt für praktisch alle Capabilities frei — alle 30 E2E-Journeys existieren bereits, nur der Runner fehlt. **SYS-1/2/3/4** deckeln Axis B; ohne sie ist Gold-B nirgends belegbar.
- **Quick Wins (S, kein Neubau):** C4-A1/A2 + C6-A1 (copy-as-template verdrahten — Backend existiert), C17-C1 (ArangoDB-Service-Job aktiviert stumme Tenant-Isolationsprüfung).
- **Extern blockiert (nur kapselbar, nicht autonom lösbar):** C10-A2/A3 (Kindwise-Vertrag/DSGVO, lokale Modellgewichte).

> Ausführung & Priorisierung: an `issue-orchestrate` / `feature-decompose` / `sprint-plan` übergeben.
