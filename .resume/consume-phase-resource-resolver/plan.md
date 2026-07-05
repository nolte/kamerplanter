# Plan — feat/consume-phase-resource-resolver (Issue #383)

**Issue:** [#383](https://github.com/nolte/kamerplanter/issues/383) — feat(lifecycle):
consume the phase resource resolver (E7/E8) in watering/nutrient services
**Worktree:** `/home/nolte/repos/.worktrees/kamerplanter/consume-phase-resource-resolver`
**Branch:** `feat/consume-phase-resource-resolver` (off `origin/develop`)
**Follow-up von:** #305 / #385 (REQ-003 Lifecycle-Engine, bereits gemerged)

---

## Goal

Den fertig implementierten, aber **inerten** `phase_resource_resolver` in die
Produktions-Service-Pfade verdrahten, sodass die E7/E8-Regime-Logik (flush =
0:0:0 / water-only, rest = kein Feed + reduzierte Bewässerung, dry_storage =
Volumen 0, `waterlogging_tolerance`-Cap, E8 `target_ph` + pH-gated
Mikronährstoff-Verfügbarkeit) tatsächlich Empfehlungen beeinflusst und in der
API/Plant-Detail-View sichtbar wird. Am Ende: Resolver hat echte Consumer,
Service-Level-Tests belegen die Konsumtion, Tests grün, PR nach `develop`.

## Current state (recherchiert am 2026-07-05)

> **Terminologie-Korrektur:** Es gibt **keine Klasse `PhaseResourceResolver`**.
> Der Resolver ist ein **Modul mit reinen, stateless Funktionen**. Im gesamten
> Produktionscode wird das Modul **nirgends importiert** — einziger Consumer sind
> Unit-Tests. Das bestätigt die Issue-Prämisse.

**Resolver (Ist-Zustand, fertig + getestet):**
- `src/backend/app/domain/engines/phase_resource_resolver.py`
  - `resolve_irrigation(phase_name, *, base_frequency_days=3.0, base_volume_ml=300.0, waterlogging_tolerance=None) -> IrrigationRegime` (`:94`)
  - `resolve_nutrient(phase_name, *, base_npk=(3,1,2), base_ec_ms=1.5, base_ph=6.0, nutrient_demand_level=None) -> NutrientRegime` (`:130`)
  - `ph_micronutrient_availability(target_ph) -> tuple[bool, str]` (`:47`)
  - Return-Typen sind **frozen dataclasses** (nicht Pydantic): `IrrigationRegime`
    (frequency_days, volume_ml_per_plant, water_only, note), `NutrientRegime`
    (feed, npk_ratio, target_ec_ms, note, target_ph, micros_available, ph_note).
  - Abhängig von `phase_role_map.py` (`core_phase`, `is_rest_phase`) und
    `NutrientDemandLevel`.
- Unit-Tests: `tests/unit/domain/engines/test_phase_resource_resolver.py`;
  zusätzlich konsumiert von `test_flow_templates_d9_d12.py`.

**Watering-Pfad (Einhängepunkt Irrigation):**
- `src/backend/app/domain/services/watering_service.py` — `WateringService`.
  Zentraler Empfehlungspfad: **`suggest_volume()` (`:208`)** — löst `phase_name`
  bereits auf (PhaseSequence bevorzugt `:264`, Fallback LifecycleConfig `:278`),
  delegiert an `WateringVolumeEngine.suggest_volume()`.
- `watering_volume_engine.py` — `WateringVolumeEngine.suggest_volume()` (`:85`)
  hat eigene `_PHASE_FACTOR`-Tabelle (`:67`) → **konzeptionell überlappend mit dem
  Resolver, aber unabhängig implementiert** (Divergenz-Risiko!).
- REQ-037 (ET/Evapotranspiration): **existiert NICHT** — nur Doc-Referenz im
  Resolver-Header. REQ-005 (Sensoren): vorhanden (`sensor_service.py`,
  DI `dependencies.py:682`), aber **nicht** mit dem Watering-Empfehlungspfad
  verdrahtet.
- `waterlogging_tolerance` liegt am Species-Modell (`species.py:31`, Literal-Werte
  matchen exakt die Resolver-Caps sensitive/moderate/tolerant).

**Nutrient-/Dosing-Pfad (Einhängepunkt Nutrient):**
- `src/backend/app/domain/services/nutrient_plan_service.py` — `NutrientPlanService`,
  `calculate_dosages()` (`:316`, REQ-004 §4b 3-stufige Pipeline).
- `resource_profile_generator.py` — `ResourceProfileGenerator` mit
  `_DEFAULT_PROFILES`-Tabelle (`:7`, npk_ratio/target_ec_ms/target_ph pro Phase)
  → **zweite überlappende Logik-Quelle**.
- pH-gated Mikros existieren am `NutrientProfile` (`phase.py:63`), aber
  eigenständig, **nicht** über `ph_micronutrient_availability()`.
- `nutrient_demand_level` am Species-Modell (`species.py:254`, enum `enums.py:306`).

**G2-Consumer (rohe per-phase Profile in der Detail-View):**
- `src/backend/app/api/v1/profiles/router.py` — `GET /profiles/requirements/{phase_key}`
  (`:18`), `GET /profiles/nutrients/{phase_key}` (`:31`) liefern rohe Profile via
  `to_response`. Das ist der Pfad, der laut Issue die **berechnete Guidance NICHT**
  zeigt.

**DI-Muster:** `common/dependencies.py` Factory-Funktionen; etabliertes Muster für
Engine-Konsumtion ist der **optionale Konstruktor-Parameter mit Default-Instanz**
(`WateringService._volume_engine = volume_engine or WateringVolumeEngine()`,
`watering_service.py:44`). Da der Resolver stateless Modul-Funktionen sind, ist
direkter Import + Aufruf im Service ebenso legitim.

Referenzen: `spec/req/REQ-003_Phasensteuerung.md` (§E7/E8),
`spec/req/REQ-004_*`, `spec/req/REQ-037*`, `spec/req/REQ-005*`,
`spec/style-guides/BACKEND.md` (5-Layer, Service/Engine-Trennung).

## Load-bearing design decision

**Wie verhält sich der Resolver zu den zwei bereits existierenden, überlappenden
Logik-Quellen (`WateringVolumeEngine._PHASE_FACTOR` und
`ResourceProfileGenerator._DEFAULT_PROFILES`)?**

Kern-Spannung: Der Resolver darf nicht als *dritte* parallele Wahrheit
danebengestellt werden — das Issue will ihn *als* die maßgebliche Phasen-Regime-
Quelle konsumieren. Vorschlag (in requirements-elicit zu bestätigen): Der Resolver
wird die **autoritative Phasen-Modulationsschicht**; die Engines rufen ihn auf,
statt eigene Phasen-Faktoren zu halten. Statische Defaults (Species-Guide,
Substrat) bleiben Basis-Input; ET/Sensor-Override (falls im Scope) schlägt sie;
`waterlogging_tolerance` cappt final. Reihenfolge laut Issue:
**ET/Sensor > statische Defaults > waterlogging-Cap.**

### Open questions — VOR Arbeitsbeginn klären (via requirements-elicit)

1. **REQ-037 ET-Scope:** ET existiert nicht. Voll-ET in diesem PR implementieren
   (großer Scope-Sprung, zieht Wetter/REQ-037-Pfad rein) **oder** nur den
   Override-**Einhängepunkt** vorbereiten (Resolver-Konsumtion + dokumentierter
   Hook, ET-Wert = None/Fallback) und REQ-037 als Follow-up ausgliedern?
   **Empfehlung:** Override-Hook vorbereiten, ET-Vollimplementierung ausgliedern —
   sonst sprengt #383 den Rahmen.
2. **REQ-005 Sensor-Override:** Soll der real vorhandene Sensor-Pfad
   (Bodenfeuchte) in diesem PR schon den statischen Default schlagen, oder
   ebenfalls nur als Hook vorbereiten? Abhängig von verfügbaren Sensor-Metriken.
3. **De-Duplizierung:** Ersetzt der Resolver die `_PHASE_FACTOR`- und
   `_DEFAULT_PROFILES`-Tabellen (Risiko: Verhaltensänderung bestehender Tests),
   oder wird er *vorgeschaltet/nachgelagert* ohne die Tabellen zu entfernen?
   Rückwärtskompatibilität der bestehenden Volumen-Tests prüfen.
4. **API-Surfacing:** Wie wird die berechnete Guidance (flush/rest/water_only,
   pH-Verfügbarkeit, `ph_note`) an die Plant-Detail-View gebracht — neue Felder in
   den bestehenden `/profiles/*`-Responses, ein neuer `resolved`-Endpoint, oder
   Anreicherung von `VolumeSuggestion`/`DosageCalculationResult`?
5. **Frontend-Umfang:** Gehört ein Frontend-Teil (Anzeige der Guidance +
   pH-Warnung) in **diesen** PR, oder Backend-only + Frontend-Follow-up? (Beachte
   PFLICHT-3-Agent-Kette UI-Review→Tests→Doku bei Frontend-Änderungen.)
6. **Nutrient-Einhängepunkt:** `resolve_nutrient` in `calculate_dosages()`
   (Live-Dosing) **oder** in `ResourceProfileGenerator` (Default-Generierung) —
   oder beide? Bestimmt, ob Guidance bei jeder Dosierung oder nur bei
   Profil-Erzeugung greift.

## Ordered work steps

1. **requirements-elicit** — Open Questions 1–6 klären, Scope-Schnitt festlegen
   (v. a. ET-Scope und De-Duplizierungsstrategie). Requirement-Artefakt ≥ Schwelle.
2. **Irrigation-Verdrahtung:** `resolve_irrigation` in `WateringService.suggest_volume()`
   /`WateringVolumeEngine` einhängen; `waterlogging_tolerance` aus Species laden
   (Repo-Pfad prüfen); Override-Reihenfolge ET/Sensor > Default > Cap umsetzen.
3. **Nutrient-Verdrahtung:** `resolve_nutrient` + `ph_micronutrient_availability`
   im festgelegten Pfad (calculate_dosages und/oder ResourceProfileGenerator)
   einhängen; `nutrient_demand_level` laden; flush/rest/pH-Guidance surfacen.
4. **API-Surfacing:** Guidance-Felder gemäß Entscheidung (OQ4) in Response-Schemas;
   Plant-Detail-View zeigt berechnete statt roher Werte.
5. **Service-Level-Tests:** Konsumtion des Resolver-Outputs testen (flush→0:0:0,
   rest→kein Feed/reduziert, dry_storage→0 Volumen, waterlogging-Cap, pH>6.5→
   Mikro-Lockout). Bestehende Volumen-/Dosing-Tests auf Regressionen prüfen.
6. **(falls Frontend im Scope)** UI + PFLICHT-Kette UI-Review→Tests→Doku.
7. **Quality-Gate:** ruff/eslint/tsc + pytest/vitest grün; `unit-test-runner`.
8. **PR nach develop** via `pull-request-create` (englisch, Issue #383 verlinkt).

## Invariants & guardrails

- **5-Layer (NFR-001):** Resolver bleibt Domain-Engine (pure), Konsumtion in der
  Service-Schicht. Keine Business-Logik in API-Router.
- **Source-Code Englisch (NFR-003);** Kommunikation mit mir Deutsch.
- **Keine dritte Wahrheit:** Resolver soll überlappende Logik konsolidieren, nicht
  duplizieren.
- **Rückwärtskompatibilität:** bestehende Watering-/Dosing-Tests dürfen nicht
  unbemerkt brechen — Verhaltensänderungen bewusst + getestet.
- **Feature-Branch von develop; Arbeit nur im Worktree** (nicht Primary-Checkout).
- **Bei Frontend-Änderungen:** Mobile-First, beschreibende Texte/Fachbegriff-
  Erklärungen, PFLICHT-3-Agent-Kette.
- Merge-Review ernst nehmen (in ähnlichen REQ-003-PRs fing die Review-Kette real
  mehrere Crash-/500-Bugs vor Merge).

## Confirmed scope (requirements-elicit, 2026-07-05)

Artefakt: `project/requirements/consume-phase-resource-resolver.md` (≥ Schwelle,
U_gate=0.7, load-bearing Dims confirmed). Entscheidungen (Teach-back):
- **OQ1/OQ2 (ET/Sensor):** Sensor-Override **aktiv** (Bodenfeuchte schlägt Default),
  ET nur **dokumentierter Hook** (Param=None). REQ-037-Voll-ET **+ REQ-005-Wetter-
  Ingestion (existiert im Code NICHT)** = Follow-up-Issues. Grund: „Voll ET" wäre
  faktisch 3–4 Features/PR.
- **OQ3 (De-Dup):** Resolver wird **autoritative** Phasen-Schicht; Engines rufen ihn,
  `_PHASE_FACTOR`/`_DEFAULT_PROFILES` konsolidieren (nicht dritte Wahrheit).
- **OQ4 (API):** bestehende Responses **anreichern** (kein neuer Endpoint).
- **OQ5 (Frontend):** **inkl.** Frontend-Guidance-Anzeige + pH-Warnung + PFLICHT-Kette.
- **OQ6 (Nutrient-Hook):** `resolve_nutrient` konsolidiert `ResourceProfileGenerator`
  (Default-Gen) + Guidance in Dosing-Response.
- **Sensor-Caveat (A3):** `soil_moisture`-metric_type + plant→location→sensor→latest
  Resolution sind greenfield (Bausteine da: `ObservationService.get_latest_reading`,
  Arango-Sensor-Registry). Falls es sprengt → R2 als Follow-up abspalten.

## Status / resume-anchor checklist

- [x] **requirements-elicit ausgeführt**, Open Questions geklärt, Scope-Schnitt
      festgelegt (Sensor aktiv + ET-Hook; Resolver konsolidiert). Artefakt ≥ Schwelle.
- [x] Irrigation-Resolver konsolidiert: `resolve_irrigation` absorbiert `_PHASE_FACTOR`
      (germ 0.30/seed 0.50/flowering 1.20/flushing 1.40 water_only/ripening 0.60),
      waterlogging als Multiplikator (nicht Hard-Cap → flowering/flushing bleiben elevated
      für moderate/None). Engine delegiert, `VolumeSuggestion.water_only/regime_note` neu.
      66 Engine/Resolver/Flow-Tests grün, ruff clean.
- [x] WateringService: `waterlogging_tolerance` aus Species geladen→Engine (Cap phase-unabhängig).
      Live-Bodenfeuchte-Override (`sensor_service` DI, `soil_moisture`-metric, plant→slot→location→
      HA-read-through), reduziert nur (wet→0), graceful Fallback ohne Sensor/Reading. ET-Seam
      `et_net_demand_ml` (inert, getestet). `VolumeSuggestionResponse` um water_only/regime_note
      erweitert. 9 neue Service-Tests + 39 grün, ruff clean.
- [x] Nutrient-Konsolidierung: `ResourceProfileGenerator.generate_nutrient_profile` routet
      durch `resolve_nutrient` (fixt dormancy-feeds-Bug → 0:0:0; flush/rest zeroing zentral).
      pH-Gating gehört an `target_ph` (NutrientProfile), NICHT an Nutrient-Plan-Entry (hat kein target_ph)
      → im Profiles-API surfaced. Live-Dosing flush schon via bestehender EC=0-Warning.
- [x] Guidance im Profiles-API: `NutrientProfileResponse` um feed/micros_available/ph_note
      (aus `ph_micronutrient_availability(target_ph)`) angereichert; `VolumeSuggestionResponse`
      um water_only/regime_note (Task 2). Irrigation-Guidance via suggest-volume-Endpoint.
- [x] Service-/API-Tests grün: watering-suggest (9), resolver (12 neu), engine-consolidation (4),
      generator dormancy-fix (2), profiles-guidance (3). **453 Tests im Umkreis grün, ruff clean.**
- [x] Frontend Guidance-Anzeige (fullstack-developer): types + PlantInstanceDetailPage
      (water_only-Chip + regime_note + Sensor-Hinweis) + ProfilesSection (pH-Sperre-Alert +
      no-feed-Chip) + DE/EN-i18n. tsc/eslint clean.
- [x] PFLICHT-Kette: **UI-Review** (frontend-usability-optimizer fand+fixte a11y-Bug:
      Tooltip-Chips tastatur-unerreichbar → tabIndex/role/aria-label) → **Tests**
      (4 ProfilesSection-Guidance-Tests, vitest 1893 grün; Watering-Card bewusst geskippt =
      2476-Zeilen-Page ohne Test-Infra) → **Doku** (mkdocs-agent läuft).
- [x] Quality-Gate grün: Backend ruff clean + **3624 pytest passed** (`-p no:randomly`);
      Frontend tsc clean, eslint 0 errors, **vitest 1893 passed**; mkdocs `--strict` grün.
      **Falle gefangen:** pre-commit `ruff format 0.15.x` zerlegte `except (TypeError, ValueError):`
      → SyntaxError (bekannt, `feedback_ruff_format_except_tuple.md`) → durch Typ-Narrowing ersetzt.
      Rebase auf origin/develop (#387) clean.
- [x] **PR #388 (Draft) nach develop erstellt**, Closes #383, Labels enhancement+documentation.
      https://github.com/nolte/kamerplanter/pull/388

## FERTIG — Issue #383 vollständig bis zum PR abgearbeitet.
Nächster manueller Schritt (nicht Teil von „bis zum PR"): Draft→Ready + automerge via
`pull-request-merge`-Skill nach grüner CI. Follow-ups: REQ-037 Voll-ET, REQ-005 Wetter-Ingestion,
persistierter Bodenfeuchte-Pfad, Watering-Card-Subkomponente für Testbarkeit.
