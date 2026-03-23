# E2E Test Case Extractor Memory

## Test Case Perspective Shift (2026-02-27)
- User requested all test cases to be written from **end-user browser perspective only**
- NO API calls, HTTP status codes, DB queries, or backend implementation details
- Assertions describe what the user sees, clicks, types, and expects on screen
- Labels/messages use exact German i18n translation strings from `src/frontend/src/i18n/locales/de/translation.json`
- Backend validation errors are described as "error notification is displayed" without mentioning the HTTP layer

## Spec Document Structure Pattern
- REQ docs follow consistent structure: 1. Business Case, 2. ArangoDB-Modellierung (nodes/edges/AQL), 3. Technische Umsetzung (Python code), 4. Abhängigkeiten, 5. Akzeptanzkriterien (DoD + Testszenarien)
- Testszenarien in Section 5 use GIVEN/WHEN/THEN format -- map to browser-level acceptance test cases
- Seed data tables provide concrete values for UI-level verification test cases

## Frontend Architecture (for Test Case Writing)
- Pages live in `src/frontend/src/pages/{section}/` grouped by domain
- Each entity has: ListPage, CreateDialog, DetailPage pattern
- SpeciesDetailPage has 3 tabs: Bearbeiten, Sorten (CultivarListSection), Lebenszyklus-Konfiguration (LifecycleConfigSection)
- DataTable component provides: search (debounced 300ms), sort (click column headers), pagination, keyboard nav (Enter on rows)
- DataTable shows "Keine Ergebnisse fuer Ihre Suche gefunden" when search matches nothing
- Forms use react-hook-form + zod for client-side validation, backend errors shown via useApiError hook as notifications
- UnsavedChangesGuard on all detail pages: browser confirm dialog on navigate-away with dirty form
- ConfirmDialog with destructive flag for all delete operations
- BotanicalFamily list uses client-side tableState (useTableUrlState); Species list uses server-side pagination (usePagination)

## Key Frontend Validation Rules (Client-Side, from Zod schemas in dialogs)
- BotanicalFamily: name must `.endsWith('aceae')` (refine), typical_growth_forms.min(1), pollination_type.min(1)
- BotanicalFamily: soil_ph_min/max are `z.union([z.number().min(3).max(9), z.literal('')])` -- empty string means "not set"
- Species: scientific_name.min(1) -- no binomial regex in frontend (backend handles that)
- Species: allelopathy_score.min(-1).max(1), family_key nullable
- Cultivar: name.min(1), days_to_maturity.min(1).max(365) nullable
- GrowthPhase: name.min(1), typical_duration_days.min(1), sequence_order.min(0)

## i18n Translation Keys (German labels used in test cases)
- Button labels: "Erstellen", "Speichern", "Loeschen", "Abbrechen"
- Table: "Tabelle durchsuchen...", "Zeigt {{from}}--{{to}} von {{total}} Eintraegen", "Zeilen pro Seite"
- Delete confirm: "Sind Sie sicher, dass Sie \"{{name}}\" loeschen moechten? Diese Aktion kann nicht rueckgaengig gemacht werden."
- Unsaved: "Sie haben ungespeicherte Aenderungen. Moechten Sie die Seite wirklich verlassen?"
- Error messages: "Netzwerkfehler...", "Serverfehler...", "Ein Eintrag mit diesem Namen existiert bereits."

## Test Case Numbering Convention
- Pattern for REQ docs: TC-REQ-{NNN}-{TTT} where NNN=requirement number, TTT=sequential within doc
- Pattern for NFR docs: TC-NFR{NNN}-{TTT} (no hyphen after NFR prefix) e.g. TC-NFR006-001
- Group by functional area/page within document, not by test type
- Coverage summary table at end maps UI sections to test case ranges

## NFR-008 Teststrategie — Key Insights for Test Extraction
See [nfr008_teststrategie.md](nfr008_teststrategie.md) for full details.
- NFR-008 is a meta-NFR: SuT is the test infrastructure (pytest CLI, filesystem, Page-Object compliance), NOT the UI
- QA-Engineer-at-terminal perspective, except Gruppe 8 (E2E Kernfunktionen) which involves a real browser
- Output: `spec/e2e-testcases/TC-NFR-008.md`, 48 test cases TC-NFR008-001 to TC-NFR008-048

## NFR-006 API Error Handling — Key UI Patterns (confirmed from source)
- useApiError hook maps error codes to i18n keys: ENTITY_NOT_FOUND→errors.notFound, DUPLICATE_ENTRY→errors.duplicate, VALIDATION_ERROR→errors.validation, INTERNAL_ERROR→errors.server; Network Error→errors.network
- getFieldErrors() strips `body.` prefix from field names (e.g. `body.name` → `name`) for inline form errors
- ApiErrorDisplay chooses between ErrorPage (illustrated, for status codes in ILLUSTRATED_CODES set) and ErrorDisplay (generic)
- ILLUSTRATED_CODES = {400, 401, 403, 404, 408, 429, 500, 502, 503} — each has SVG illustration
- ErrorPage has data-testid="error-page", error-go-home, error-go-back, error-retry buttons
- error_id format: `err_<uuid4>` — validated by regex `^err_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`
- NFR-006 §7.2 Soll: INTERNAL_ERROR Snackbar should show error_id as support reference — current impl shows only generic errors.server message (gap to document)
- NFR-006 security tests (Gruppe J) are negative tests: assert absence of ArangoDB/arango/AQL/Traceback/.py/localhost strings in visible UI

## NFR-010 — UI Vollständigkeitsmatrix data-testid Map (confirmed from source)
- DataTable: `data-testid="data-table"`, rows: `data-testid="data-table-row"`
- Search input: `data-testid="table-search-input"`, count: `data-testid="showing-count"`
- Active search chip: `data-testid="search-chip"`, sort chip: `data-testid="sort-chip"`
- Reset filters: `data-testid="reset-filters-button"`, no results: `data-testid="no-search-results"`
- ConfirmDialog: `data-testid="confirm-dialog"`, cancel: `data-testid="confirm-dialog-cancel"`, confirm: `data-testid="confirm-dialog-confirm"`
- EmptyState: `data-testid="empty-state"`, action: `data-testid="empty-state-action"`
- LoadingSkeleton: `data-testid="loading-skeleton"`, ErrorDisplay: `data-testid="error-display"`
- Form fields: `data-testid="form-field-{name}"`, submit: `data-testid="form-submit-button"`, cancel: `data-testid="form-cancel-button"`
- Mobile card view: `data-testid="data-table-cards"`

## NFR-010 — CRUD-Vollständigkeitsmatrix Ist-Zustand (§4.1, Stand 2026-02-26)
Fehlende Operationen (zu testen): BotanicalFamily(Edit), Cultivar(Read+Edit), Slot(Edit+Delete), Substrate(Edit+Delete), Batch(List+Edit+Delete), PlantInstance(Edit), GrowthPhase(Delete)
Vollständig implementiert: Species, Site, Location

## Cross-Cutting Concerns (REQ-001)
- REQ-001 is foundation: BotanicalFamily data flows into REQ-002 (rotation), REQ-003 (phases), REQ-004 (nutrient demand), REQ-010 (IPM pests)
- Companion planting has 2-tier fallback: species-level edges first, then family-level with 0.8 score discount
- Crop rotation validation has 3 severity levels: CRITICAL (same family) > WARNING (shared pest risk) > INFO (no specific data)

## Key Validation Rules (REQ-001, Backend)
- BotanicalFamily.name must end with "aceae"
- BotanicalFamily.order must end with "ales" (if not null)
- nitrogen_fixing=true + heavy demand = rejected (model_validator)
- Species.scientific_name must have >= 2 parts (binomial)
- PhRange: min_ph >= 3.0, max_ph <= 9.0, max_ph >= min_ph
- Biennial lifecycle MUST have vernalization_required=true

## Output Path Convention
- All test case docs use: `spec/e2e-testcases/TC-REQ-{NNN}.md` (unified directory)
- TC-REQ-001.md is at `spec/e2e-testcases/TC-REQ-001.md` (62 test cases, IDs TC-001-001 to TC-001-062)
- YAML frontmatter with req_id, title, category, test_count, coverage_areas, generated date, version
- Coverage matrix table at end mapping spec sections to test case ID ranges

## REQ-001 Stammdatenverwaltung — Completed Test Cases
- Output: `spec/e2e-testcases/TC-REQ-001.md`, 62 test cases
- 17 test groups: BotanicalFamily List/Create/Detail/Delete, Species List/Filter/Create/Detail/Cultivar-Tab/Lebenszyklus-Tab, Cultivar Detail, CropRotation, Seed-Daten, i18n, Scoping/Auth, Mobile
- SpeciesDetailPage has 5 tabs (not 3 as in older memory): Bearbeiten, Anbauperioden, Sorten, Lebenszyklus-Konfiguration, Workflows
- SpeciesListPage has 9 Toggle-Chips: favoritesOnly, sowNow, indoor, container, balcony, greenhouse, frostHardy, harvestable, supportNeeded + growthHabit Dropdown
- BotanicalFamily list: client-side filter (useTableUrlState), no server pagination
- Species list: fetchSpeciesList with offset=0, limit=1000 (effectively client-side after load)
- nitrogen_fixing=true + typical_nutrient_demand='heavy' is BOTH a client-side Zod block AND backend model_validator
- Fruchtfolge warnings: CRITICAL (same family) > WARNING (shared_pest_risk) > OK/INFO (rotation_after benefit) — shown in CropRotationPage
- Cultivar detail has phase_watering_overrides section — shown only when species has GrowthPhases

## Spec Sections Most Valuable for UI Test Extraction
1. Section 5 (Frontend-Integration): routes, tabs, UI components, expertise level table
2. Section 9 (Akzeptanzkriterien): DoD checklist + GIVEN/WHEN/THEN scenarios
3. Section 7 (Auth/Authz): which endpoints need auth, rate limits visible in UI
4. Section 6 (Feature-Toggle/Konfiguration): what to test when config is missing (disabled states)
5. Section 1.x (Domain model tables): concrete values for test data

## REQ-003 Phasensteuerung — UI Patterns and Key Test Insights
- Output: `spec/e2e-testcases/TC-REQ-003.md`, 42 test cases, IDs TC-003-001 to TC-003-042
- Key pages: LifecycleConfigSection (stammdaten/species/:key Tab 3), GrowthPhaseListSection+Dialog (same tab, subsection), PlantInstanceDetailPage Tab "phases", CalculationsPage `/pflanzen/calculations`
- PhaseTransitionDialog data-testids: `phase-transition-dialog`, `target-phase-select`, `transition-reason`, `force-transition-switch`, `transition-cancel`, `transition-confirm`
- Force/Korrekturmodus: Schalter "Phase korrigieren (Fehlanlage)" aktivieren → Button wird orange, zeigt "Phase korrigieren", Alert erscheint, erlaubt Rückwärts-Transition
- Rückwärts-Transition-Sperre: Ohne force → Fehlerbenachrichtigung; mit force → erlaubt. Ausnahme: `is_cycle_restart=true` bei Perennials (Seneszenz→Dormanz) erlaubt ohne force
- Autoflower (cultivar.photoperiod_type='autoflower'): Photoperiode bleibt konstant 20h bei Blüte (kein 12h-Wechsel); HST-Methoden erzeugen Warnung, keine Blockade
- GrowthPhaseDialog Zod: name.min(1), typical_duration_days.min(1), sequence_order.min(0), watering_interval_days.min(1).max(90) nullable
- ProfileEditDialog Zod: light_ppfd_target.min(0), photoperiod_hours.min(0).max(24), target_ec_ms.min(0), target_ph.min(0).max(14)
- Backend validates: temperature_night_c must be <= temperature_day_c; target_ec_ms le=4.0; target_ph ge=4.0 le=8.0
- Biennial: server rejects vernalization_required=false (TC-003-004 is spec-forward, current Zod doesn't enforce it client-side)
- GrowthPhaseListSection: sorted by sequence_order asc by default; "Profil"-Button per row opens ProfilesSection inline below table
- ProfilesSection: "Standardwerte generieren" button calls phasesApi.generateDefaultProfiles → shows requirement + nutrient cards

## REQ-009 Dashboard — Implementation Status and Test Notes
- REQ-009 spec is v2.0 (maximal erweitert), but current frontend implementation (`DashboardPage.tsx`) is minimal:
  only a welcome message + 6 Schnellaktions-Kacheln. No live widgets, no VPD gauge, no Plant Grid yet.
- All widget-level test cases (TC-009-009 through TC-009-043) are forward-looking spec tests — they verify
  the PLANNED dashboard, not the current stub. Mark as "blocked: pending implementation" in test runners.
- Output path for REQ-001-028 is `spec/e2e-testcases/TC-REQ-{NNN}.md` (same directory as REQ-030).
- Test case IDs use pattern TC-009-{NNN} (3-digit sequential), not TC-REQ-009-{NNN}.
- AQL business logic maps directly to UI states: null sensor values → "--" or empty state message.
- VPD thresholds visible in UI: LOW=red (< target−tolerance), HIGH=red (> target+tolerance), OPTIMAL=green.
- Health score algorithm (0–100) visible as card colours in Plant Grid (not just a number).

## REQ-028 Companion Planting — UI Patterns and Key Test Insights
- Two UI entry points: (1) CompanionPlantingPage at `/stammdaten/companion-planting` (Platform-Admin manages edges), (2) Mischkultur-Partner-Panel inside PlantingRunCreateDialog (all members)
- CompanionPlantingPage: species-select dropdown → two side-by-side cards (kompatibel/inkompatibel) with Add-buttons
- data-testid attributes: `species-select`, `add-compatible-button`, `add-incompatible-button`, `target-species-select`, `score-input`, `reason-input`
- Familien-Level Fallback shows "Familien-Empfehlung" badge with 20% score discount (score × 0.8)
- Run-Header badge: green=COMPATIBLE, yellow=WARNING (>=1 incompatible pair), red=INCOMPATIBLE (>50% pairs incompatible)
- Expertise-Level filter: Beginner=Top-3 recommendations, Intermediate=Top-5 + effect icons, Expert=all + scores + match-level + source
- Effekt-Typ sort order in panel: pest_repellent > growth_enhancer > soil_improver > nutrient_fixer > pollinator_attractor > space_optimizer > general
- Beetplan visualisation (REQ-002): green lines=compatible, red lines=incompatible, grey lines=unknown between adjacent slots
- Slot assignment shows warning (non-blocking) when chosen species is incompatible with neighbour slot
- i18n keys: `companion.panel.*`, `companion.badge.familyLevel`, `companion.effect.*`, `companion.severity.*`, `companion.validation.*`
- Seed data concrete values for test preconditions: Tomate(0.9,Basilikum), Tomate(0.85,Tagetes), Moehre(0.85,Zwiebel), Tomate-Fenchel=incompatible/moderate

## REQ-014 Tankmanagement — See Detailed Notes
- See [req_014_tankmanagement.md](req_014_tankmanagement.md) for full UI patterns, thresholds, i18n keys
- TankDetailPage: 6 tabs (Details/Zustand/Wartung/Wartungsplaene/Befuellungen/Bearbeiten), UnsavedChangesGuard
- Source-Badge colors: manual=grey, ha_auto=blue, ha_live=green, mqtt_auto=purple
- Freshness: <5min=green-live, 5-60min=yellow-recent, >60min=red-stale
- Live-Query: button → GET /states/live; "Alle uebernehmen" → POST /states (Dual-Write)
- Auto-schedules on create: nutrient=5, recirculation=6 maintenance plans
- TankFill warnings (non-blocking): top_up>50%, full_change<50%, EC/pH deviation, tank-safety, chlor
- WateringEvent: is_supplemental+fertigation = validation error; foliar >0.5L/slot = warning
- 72 test cases in `spec/e2e-testcases/TC-REQ-014.md`, IDs: TC-014-{NNN}

## REQ-010 IPM System — UI Patterns and Key Test Insights
- Frontend: `src/frontend/src/pages/pflanzenschutz/` contains only: PestListPage, DiseaseListPage, TreatmentListPage, KarenzStatusCard, and their Create-Dialogs
- Routes: `/t/{slug}/pflanzenschutz/pests`, `/diseases`, `/treatments` (no DetailPages yet)
- KarenzStatusCard is a component embedded in plant detail pages — not a standalone route
- Chip color mapping: pest.detectionDifficulty(easy=success/green, medium=warning/orange, hard=error/red); disease.pathogenType(fungal=warning, bacterial=error, viral=secondary, physiological=info); treatment.treatmentType(chemical=error, biological=success, cultural=info, mechanical=default)
- Karenz-Chip only shown when safety_interval_days > 0; otherwise shows em-dash "—"
- hideBelowBreakpoint="md" on: pest cols(pestType, lifecycleDays); disease cols(incubationPeriodDays); treatment cols(activeIngredient, applicationMethod)
- Zod schema: Pest(scientific_name.min(1), common_name.min(1), pest_type enum, lifecycle_days nullable positive int); Disease(scientific_name/common_name min(1), pathogen_type enum, incubation_period_days nullable positive int, environmental_triggers[], affected_plant_parts[]); Treatment(name.min(1), treatment_type enum, safety_interval_days.min(0), dosage_per_liter nullable positive)
- MAJOR UI GAPS (spec-forward test cases): No Inspection-Create UI, no TreatmentApplication UI, no resistance warning dialog, no hermaphroditism finding form, no pollination-check form — these are spec-forward tests for future implementation
- i18n key block: `pages.ipm.*` for all labels; `enums.pestType.{insect,mite,nematode,mollusk}`, `enums.pathogenType.{fungal,bacterial,viral,physiological}`, `enums.treatmentType.{cultural,biological,chemical,mechanical}`, `enums.ipmApplicationMethod.{spray,drench,granular,release,cultural}`, `enums.detectionDifficulty.{easy,medium,hard}`
- Hermaphrodismus protocol: 3 severity levels (isolated=keep_monitoring, spreading=isolate, critical=remove_immediately); each has specific immediate_actions[] and follow_up[] steps
- ResistanceManager: MAX_CONSECUTIVE_APPLICATIONS=3, ROTATION_WINDOW_DAYS=90; warning="RESISTENZWARNUNG: Wirkstoff-Rotation erforderlich"
- Cross-req: hermie critical → auto-marks cultivar hermie_prone (REQ-001), generates REQ-013 PlantingRun pollination-check tasks, documents lineage in REQ-017

## REQ-011 Externe Stammdatenanreicherung — Test Insights
- REQ-011 is backend-focused (v1.0): no dedicated Frontend Enrichment-Admin-UI implemented yet
- Enriched fields (hardiness_zones, synonyms, taxonomy) ARE visible in existing SpeciesDetailPage at `/stammdaten/arten/:key`
- No `enrichment` API endpoint file in `src/frontend/src/api/endpoints/` — all 28 test cases with dedicated admin UI are marked "UI ausstehend"
- Test cases fall into 2 tiers: (1) currently testable via Species form, (2) spec-forward requiring future Enrichment-Admin section
- Key spec sections for test derivation: §1.2 Daten-Mapping table, §3.4 apply_enrichment logic, §3.7 REST endpoints, §4 Auth matrix, §6 all 7 Szenarien
- Core business rule: `auto_accept = local_value is None` — only empty fields auto-filled (confidence 0.9), existing values propose-only (confidence 0.7)
- Auth matrix: Lesen=all, Schreiben/Sync-trigger=Admin only, Delete=not supported
- 5 external sources: Perenual (prio 1, 100 req/day), OpenFarm (prio 2), GBIF (prio 3, taxonomie), Trefle (prio 4), Otreeba (prio 5, cannabis)
- Species-Detailseite tabs (actual): edit, growing-periods, cultivars, lifecycle, workflows — no enrichment tab yet

## REQ-016 InvenTree-Integration — UI Patterns and Key Test Insights
- REQ-016 is spec v1.0, NOT YET IMPLEMENTED in frontend (2026-03-21); no pages in `src/frontend/src/pages/` for InvenTree or Equipment
- Only existing InvenTree references in frontend: `TankDetailPage.tsx` (i18n key `pages.tanks.equipment`), `types.ts` (protective_equipment in treatment)
- Output: `spec/e2e-testcases/TC-REQ-016.md`, 52 test cases, IDs TC-016-{NNN}
- Key domain split: Admin-only (Connection-CRUD) vs. Mitglied (Equipment, References, Sync, Transactions)
- Equipment is a First-Class-Entity INDEPENDENT of InvenTree — visible in nav even without InvenTree config
- InvenTree sections on Duenger/Tank detail pages appear ONLY when InvenTree is configured (feature-toggle)
- auto_deduct flag on InvenTreeReference controls whether ConsumptionTracker creates stock_transactions
- STOCK_DRIFT_THRESHOLD = 0.20 (20%) — warning shown in sync results + entity detail view
- Security rules visible in UI: API-Token always masked (never cleartext), SSL warning when verify_ssl=false
- IT-006: Health-check error message must be generic (no information leak about server type)
- TankFillEvent-Consumption-Tracking has no explicit UI scenario in spec — positive E2E test cannot be written without Tank fill UI details
- Rate-limiting (IT-005, 60 req/min) is backend-only — no UI signal defined in spec v1.0
- Retry counter visible in Transactions-Log: "Versuche: N von 3", last error text sichtbar
- Browse endpoint min_length=2 for part search — enforce as client-side validation hint

## REQ-001 Stammdatenverwaltung — See Detailed Notes
- See [req_001_stammdatenverwaltung.md](req_001_stammdatenverwaltung.md) for routes, Zod rules, seed-data values, spec-forward tests
- Output: `spec/e2e-testcases/TC-REQ-001.md`, 78 test cases v4.0, IDs TC-001-001 to TC-001-078
- Stammdaten-Scoping v4.0: tenant_has_access, TenantSpeciesConfig.hidden, has_overlay, Promotion — TC-001-058 to TC-001-063
- Autoflower fields (TC-001-040 to TC-001-043) and Promotion UI (TC-001-062) are SPEC-FORWARD tests

## REQ-004 Dünge-Logik + REQ-004-A EC-Budget — See Detailed Notes
- See [req004_duenge_logik.md](req004_duenge_logik.md) for full UI patterns, validation rules, EC-Budget formulas
- Pages in `src/frontend/src/pages/duengung/` (22 files including Gantt, WaterMix, DeliveryChannel, NutrientPlan)
- 88 test cases in `spec/e2e-testcases/TC-REQ-004.md`, IDs: TC-004-{NNN}
- Foliar-Warnung (G-013): Phase=flowering, Woche≥2 → gelbes ⚠ Alert (WARNING); Woche=1 → INFO nur; is_emergency=true → unterdrückt
- Multi-Channel: Beginner=ausgeblendet, Expert=voll sichtbar (REQ-021 Integration)
- EC-Budget-Pipeline: WaterMix → CalMag-Korrektur → Rezept-Skalierung (Proportionen bleiben erhalten)
- Living Soil: EC-Budget deaktiviert, organische Empfehlung statt EC-Budget
- EC_max-Werte: Coco Seedling=1.0 mS, Coco Vegetative=2.0 mS, Hydro Flowering=2.8 mS
- WateringSchedule: Plan-Level darf KEIN fertigation enthalten; Channel-Level darf fertigation haben

## REQ-025 Datenschutz/DSGVO — UI Patterns and Key Test Insights
- PrivacySettingsPage at `/settings/privacy` with 4 tabs: Einwilligungen, Datenexport, Account loeschen, Verarbeitungseinschraenkung — NOT YET IMPLEMENTED
- i18n key prefix: `pages.privacy.*`; tabs: `pages.privacy.tabs.consents|export|delete|restrictions`
- Consent toggles: required purposes (core_functionality) = disabled toggle + "Erforderlich fuer den Betrieb"; optional = ON/OFF toggle with timestamps
- Four consent purposes: core_functionality (required, Art.6(1)(b)), error_tracking, hibp_check, external_enrichment (all optional, Art.6(1)(a))
- Data export: max 1 active export (button disabled while pending/processing); download link valid 72h; statuses: pending→processing→completed→expired→failed
- Account erasure: password confirm → checkbox-Dialog ("Ich verstehe...") → soft-delete + session invalidation → hard-delete after 90 days; AK-08a: must show fully_deleted vs. anonymized categories (CanG/PflSchG)
- E-Mail-Aenderung is in AccountSettingsPage Profil-Tab, NOT on PrivacySettingsPage; token valid 24h; all sessions invalidated on confirm
- Art.18 Restriction scopes: all | sensor_data | analytics | enrichment; reasons: accuracy_contested | unlawful_processing | purpose_expired | objection_pending
- Art.21 Widerspruch uses same ProcessingRestriction model with reason=objection_pending + Freitext
- Datenschutzrichtlinie at `/privacy/policy` is PUBLIC (no auth) — AK-15
- AK-09 (Hard-Delete nach 90 Tagen) and AK-10 (Erasure-Audit-Log) are Celery tasks — no direct E2E test possible

## REQ-017 Vermehrungsmanagement — UI Patterns and Key Test Insights
- NOT YET IMPLEMENTED in frontend (2026-03-21); no pages in `src/frontend/src/pages/vermehrung/`; no routes in AppRoutes.tsx
- Output: `spec/e2e-testcases/TC-REQ-017.md`, 72 test cases, IDs TC-017-{NNN}

## REQ-008 Post-Harvest — See topic file
- Output: `spec/e2e-testcases/TC-REQ-008.md` (68 test cases), NOT YET IMPLEMENTED in frontend
- Key patterns, threshold values, and design ambiguities: `req008_post_harvest_patterns.md`
- Primary UI routes: /vermehrung/events, /vermehrung/batches, /vermehrung/protokolle, /vermehrung/mutterpflanzen, /vermehrung/statistiken
- PlantInstance-Detailseite gets 3 new tabs: "Abstammung" (lineage), "Nachkommen" (descendants), "Phaenotyp" (phenotype notes)
- Key conditional-display rules: cutting_type field only visible when method='cutting'; vaterpflanze field only visible for seed_sowing; quarantine_days only when quarantine_required=true
- Warnungen (non-blocking, gelb): Erholungszeit nicht eingehalten, virus_status=infected (WARNUNG=rot), somatische Mutationslast ab Gen.10, PPFD>150 unter Dome, Hormon-Konzentration ueber Max
- Blockierende Fehler: Temperaturgradient>8°C, Substrat<Luft, timeline-Reihenfolge (Kallus>Wurzeln>Transplant), survived>quantity, Edelreis=Unterlage
- Graft-Compatibility: 3 levels sichtbar als Banner: gruen=compatible (gleiche Gattung), gelb=possibly_compatible (gleiche Familie), rot=incompatible (verschiedene Familien)
- Navigation-Tiering (REQ-021): "Vermehrung" Menupunkt nur fuer Experten; Einsteiger sieht es nicht (aber URL zugaenglich)
- HORMONE_RANGES key mappings: softwood/quick_dip=500-1500, hardwood/long_soak=50-200 ppm; >2x max = KRITISCH (rot, ev. blockierend)
- Seed-Daten: 10 Protokoll-Vorlagen (proto_cannabis_std, proto_tomato_rockwool, proto_basil_water, proto_pothos_water, proto_sansevieria_leaf, proto_monstera_airlayer, proto_aloe_offset, proto_rose_hardwood, proto_strawberry_runner, proto_seed_general)
- Spec section 6 has AK-01 to AK-17 (functional) + FK-01 to FK-05 (frontend) — all mapped in TC-REQ-025.md

## REQ-018 Umgebungssteuerung — See Detailed Notes
- See [req_018_umgebungssteuerung.md](req_018_umgebungssteuerung.md) for full patterns, validation rules, seed data, auth matrix
- Output: `spec/e2e-testcases/TC-REQ-018.md`, 72 test cases; NOT YET IMPLEMENTED in frontend (2026-03-21)

## REQ-015 Kalenderansicht — UI Patterns and Key Test Insights
- CalendarPage at `src/frontend/src/pages/kalender/CalendarPage.tsx` — IMPLEMENTED
- ViewMode type: `'month' | 'list' | 'phases' | 'sowing' | 'season'` (5 ansichten, not 6 as in spec)
- Subcomponents: SowingCalendarView, SeasonOverviewView, PhaseTimelineView, PlantFilterTree
- Redux slices: `calendarSlice` (events, feeds, sowingEntries, sowingFrostConfig, seasonOverview)
- `useSowingFavorites` hook for "Nur Favoriten" filter (spec: "Nur geplante Pflanzen")
- CATEGORY_COLORS in frontend differ slightly from spec (harvest: `#F44336` red, not `#FFC107` gold)
- REQ-015-A is a companion spec document (§Berechnungsregeln) — both must be read together
- REQ-015-A §6 GrowingPeriod model is the main complexity: each period = separate calendar row with suffix
- Key edge cases: Voranzucht-Kappung (1. Jan), Wrap-around Ernte (31. Dez), Eisheiligen-Delay (only fallback), Bluetooth-Luecke (AB-010 Viola)
- Test precondition data: Paprika(10w, sensitive), Stiefmuetterchen(12w, hardy, ornamental, bloom=[3,4,5,6,9,10]), Winterweizen(GrowingPeriod), Winterporree(harvest=[12,1,2,3])
- Feed security: token stored as SHA-256 hash (CF-001), no PII in iCal (CF-006)
- i18n keys: `pages.calendar.*` (not `calendar.*` as spec says) — check actual translation.json
- Output: `spec/e2e-testcases/TC-REQ-015.md` with 52 test cases

## NFR-011 Retention/Aufbewahrungsfristen — Test Extraction Insights
- 38 Testfaelle in `spec/e2e-testcases/TC-NFR-011.md`; 3 Kategorien: sofort testbar, zeitabhaengig, ausstehend (UI fehlt)
- Sofort testbar: Konto loeschen (handleDeleteAccount → browser confirm → /login redirect), Sitzungswiderruf, Token-Ablauf-Fehlermeldungen (R-08/R-09: "Ungueltiger oder abgelaufener Token"), Einladungs-Status "Abgelaufen"-Chip
- Zeitabhaengig: IP-Anonymisierung (R-03), unbestaet. Accounts weg nach 7T (R-02), Export expired (R-05), Sensor-Downsampling (R-14 3 Stufen), Ernte-/Behandlungs-Anonymisierung nach Account-Loeschung
- Ausstehend (PrivacySettingsPage fehlt): R-04 Consent-History, R-05 Export-Liste, R-13 ProcessingRestriction, Celery-Monitoring-Widget, Retention-Config-Admin
- Key UI-Mapping: deleteAccount = `data-testid="delete-account-btn"` + `window.confirm` (kein custom Dialog!); Admin-Delete = zweistufig (Button → roter Alert → "Endgueltig loeschen")
- i18n fuer Account-Delete: `pages.auth.deleteAccountConfirm`, `pages.auth.deleteAccountWarning`, `pages.auth.deleteAccountDescription`
- Sensor-Downsampling sichtbar als Datenpunktdichte-Aenderung im Diagramm — kein explizites UI-Label fuer Stufe; Grenzpunkt bei 90 Tagen und 2 Jahren

## REQ-012 Stammdaten-Import — UI Patterns and Key Test Insights
- ImportPage at `src/frontend/src/pages/stammdaten/ImportPage.tsx` — IMPLEMENTED (3-step Stepper)
- Route: `/stammdaten/import` (Sidebar under "Stammdaten")
- Stepper 3 steps: step 0="Datei hochladen", step 1="Vorschau", step 2="Ergebnis"
- data-testid: `import-step-upload`, `import-step-preview`, `import-step-result`, `import-error`, `import-entity-type`, `import-duplicate-strategy`, `import-file-select`, `import-upload-button`, `import-confirm-button`, `import-back-button`, `import-download-template`, `import-new-button`
- File input: `accept=".csv,.tsv,.txt"` — note spec says only .csv, frontend also accepts .tsv/.txt
- Status chips use `STATUS_COLORS`: valid=success/green, invalid=error/red, duplicate=warning/yellow
- Error tooltip shows: `${e.field}: ${e.message}` for each row error
- currentJob.preview_rows (not preview_data) — note field naming difference between API and frontend types
- Result chips: created, updated (only shown when > 0), skipped, failed (always shown)
- "Vorlage herunterladen" triggers `getImportTemplate(entityType)` → downloads as `${entityType}_template.csv`
- i18n keys: `pages.import.*` (title, description, stepUpload, stepPreview, stepResult, entityType, entitySpecies, entityCultivar, entityFamily, duplicateStrategy, strategySkip, strategyUpdate, strategyFail, selectFile, downloadTemplate, upload, file, rows, data, status, errors, confirm, resultTitle, created, updated, skipped, failed, newImport)
- Feeding-Chart-Import route/page NOT yet implemented (only API endpoints in spec §3.8.7)
- Community-Templates page NOT yet implemented (only API in spec §3.8.5/3.8.6)
- Import-History page NOT yet implemented (spec §4.4 — only API endpoint `GET /api/v1/import/jobs`)
- Redux slice: `importSlice` with `currentJob`, `loading`, `error` state; actions: `uploadFile`, `confirmImportJob`, `clearCurrentJob`
- Output: `spec/e2e-testcases/TC-REQ-012.md` with 54 test cases

## REQ-006 Aufgabenplanung — UI Patterns and Key Test Insights
- Routes: `/aufgaben/queue` (TaskQueuePage), `/aufgaben/tasks/:key` (TaskDetailPage), `/aufgaben/workflows` (WorkflowTemplateListPage), `/aufgaben/workflows/:key` (WorkflowDetailPage), `/aufgaben/activity-plans` (ActivityPlanOverviewPage)
- TaskQueuePage: unified queue mixing tasks + care reminders; source toggle (all/tasks/care); 4 urgency groups (overdue=red, today=orange, thisWeek=blue, future=grey); quick-actions (Play/Check/Skip); Bulk-mode checkbox + action bar
- TaskDetailPage: 5 tabs when pending/in_progress (Details, Abschließen, Kommentare, Verlauf, Bearbeiten); 4 tabs when completed/skipped
- TaskTimer (W-006): Start/Pause/Reset + circular progress; client-only (no server state); does NOT block task completion
- Foto-Upload-Enforcement: `requires_photo=true` tasks reject completion without photo upload
- HST: Topping/FIM/Mainlining blocked in flowering + early_flowering; Supercropping blocked mid/late only; Recovery warning with `can_override=true` button
- Autoflower-Guard: warning (not critical) for HST on autoflower cultivar; LST/SCROG-Tucking always allowed
- Dormant tasks: separate "Geplant" section; activated on phase transition (REQ-003 hook)
- WorkflowTemplateListPage: System-badge (blue); delete disabled for system templates
- ActivityPlanOverviewPage: auto-generates plans for all species; cards show phases/activities/duration chips
- Gießplan-Tasks: category=feeding, planting_run_key set; Celery-generated; idempotent (no duplicates per run+date)
- Canopy-Evenness-Score < 0.7 → Intervention recommendation shown
- Test ID pattern: TC-006-{NNN}, 72 test cases, grouped by functional area
- Output: `spec/e2e-testcases/TC-REQ-006.md`

## REQ-013 Pflanzdurchlauf — UI Patterns and Key Test Insights
- Routes: `/durchlaeufe/planting-runs` (PlantingRunListPage), `/durchlaeufe/planting-runs/:key` (PlantingRunDetailPage)
- DetailPage has 5 tabs: details, plants, phases, nutrient-watering, activity-plan (TAB_SLUGS constant, URL-synced)
- Status-Chip colors: planned=default/grey, active=primary/blue, harvesting=warning/orange, completed=success/green, cancelled=error/red
- data-testid on key elements: `planting-run-list-page`, `create-button`, `status-chip`, `status-chip-{key}`, `edit-button`, `create-plants-button`, `batch-transition-button`, `end-run-button`, `batch-target-phase-select`, `batch-transition-confirm`, `batch-phase-transition-dialog`, `phases-tab`, `nutrient-plan-tab`, `activity-plan-tab`, `run-summary-bar`, `remove-entry-{index}`, `open-plant-{key}`, `planting-run-edit-dialog`
- Conditional buttons: planned → [createPlants + delete], active/harvesting → [batchTransition + endRun], completed/cancelled → none
- ID-Prefix auto-generation: genus name → first 3 uppercase letters; overridden by cultivar name when selected
- EndRun dialog: ToggleButtonGroup cancelled(warning)/completed(success); default=cancelled for active, default=completed for harvesting
- NutrientPlan tab: assign/change/remove buttons disabled when status=completed|cancelled
- Mixed-culture batch-transition shows Info-Alert (mixedCultureWarning) when speciesKeys.length > 1
- Detach button only visible when !r.detached_at AND run.status === 'active'
- Delete button only visible when run.status === 'planned'; DELETE requires Admin role (§5)
- ExpertiseFieldWrapper fields: run_type/site_key/location_key/notes=intermediate+; substrate_batch_key/source_plant_key=expert+
- source_plant_key field only rendered when runType === 'clone' (dynamic conditional)
- Location resets when Site changes (both create and edit dialogs)
- Zod schema: name.min(1).max(200), entries.min(1), entry.species_key.min(1), entry.quantity.min(1), entry.id_prefix regex `/^[A-Z]{2,5}$/`
- Backend 422 constraints: clone needs source_plant_key; monoculture/clone = exactly 1 entry; mixed_culture >= 2 entries (1 primary + 1 secondary); sum(entry.quantities) == planned_quantity
- Output: `spec/e2e-testcases/TC-REQ-013.md` with 52 test cases, IDs TC-013-{NNN}

## REQ-005 Hybrid-Sensorik — UI Patterns and Key Test Insights
- Sensor CRUD: `SensorCreateDialog` used for Site (SiteDetailPage), Location (LocationDetailPage), Tank (TankDetailPage)
- data-testid: `add-sensor-button` (site/location), `tank-add-sensor-button` (tank)
- metric_type enum (12 values): ph, ec_ms, water_temp_celsius, fill_level_percent, tds_ppm, dissolved_oxygen_mgl, orp_mv, temperature_celsius, humidity_percent, co2_ppm, vpd_kpa, ppfd
- Smart-Home toggle: `data-testid="smart-home-master-toggle"` in AccountSettings → Tab "Integrationen"
- i18n: `pages.auth.smartHome.{title,description,toggle,disabledInfo}`, `pages.onboarding.smartHome.{title,toggle,enabledHint,disabledHint}`
- HA config: AccountSettings → Tab "Integrationen" (only visible when smart_home_enabled=true)
- HA i18n: `pages.admin.{haSection,haUrl,haAccessToken,testConnection,testSuccess,testFailed}`
- Freshness badges in TankDetailPage: `pages.tanks.{freshLive,freshRecent,freshStale,freshOffline,sourceManual,sourceHaAuto,sourceHaLive}`
- "Messung übernehmen" (i18n: adoptReading) and "Alle Werte als Messung übernehmen" (adoptAllReadings) in TankDetailPage
- PARAMETER_WARNING_HOURS: temp/humidity/vpd=2h, co2=3h, ppfd=4h, ec/ph=6h, soil_moisture/water_level=8h
- VALID_RANGES for manual input: temp(-10,50), humidity(0,100), ec(0,15), ph(0,14), ppfd(0,2500), co2(150,10000)
- Calibration type='calibration' in MaintenanceLogDialog (already implemented)
- ha_entity_id format: must start with 'sensor.' or 'binary_sensor.'
- Smart-Home disabled hides: Sidebar sensor/actuator links, live-EC in REQ-004, sensor-trigger in REQ-013, tank sensor section in REQ-014
- Output: `spec/e2e-testcases/TC-REQ-005.md` with 58 test cases

## REQ-026 Aquaponik-Management — UI Patterns and Key Test Insights
- Output: `spec/e2e-testcases/TC-REQ-026.md`, 68 test cases, IDs TC-026-001 to TC-026-068
- NOT YET IMPLEMENTED in frontend (spec v1.0, Status: Entwurf, 2026-03-21) — all tests are spec-forward
- WaterTest + FeedingEvent + SupplementationEvent: immutable (insert-only), no Edit/Delete buttons
- Emerson-Formel DoD-Testvektor: pH 7.0, 25°C, TAN 1.0 → free NH3 ≈ 0.0057 mg/L (±5%) — must be TC
- Cycling state machine: new→cycling (TAN>0.5) → cycled (7d stable TAN<0.25+NO2<0.1+temp>15°C) → dormant (temp<10°C 7d) → cycling (Frühling)
- Safety Hard-Blocks: no synthetic fertilizers (aquaponic_safe=false), no Cu-PSM, no acid pH-down (Einsteiger); Experten-Ausnahme H3PO4 max 0.5mL/100L (REQ-021)
- NH3 critical threshold: 0.02 mg/L free ammonia → Fütterungsstopp 0g + Sofortmaßnahmen
- KH<4°dH = pH-Crash critical; GH<4°dH = Ca/Mg Warnung; DO<70% Sättigung = Belüftungswarnung
- Ramp-up nach Dormanz: ≥20°C=7 Wochen (25/50/75/100%), 15–20°C=14 Wochen; Gate: TAN<0.5 AND NO2<0.5
- System type validation: DWC/NFT/Hybrid/Wicking → biofilter_type required; Media-Bed → not required
- Clarias-Gattung (EU-VO 1143/2014) invasive art warning shown in FishSpecies detail
- Borsäure H3BO3 enger Toxizitätsbereich (>1 ppm) — Warnung sofort bei Auswahl im Supplementierungs-Dialog
- 8 FishSpecies Seed-Daten: tilapia_nile(warmwater), trout_rainbow(coldwater), carp_common(temperate), catfish_european(temperate), perch_european(temperate), goldfish(temperate), zander(temperate), char_arctic(coldwater)

## REQ-019 Substratverwaltung — UI Patterns and Key Test Insights
- Routes: `/t/{slug}/standorte/substrates` (SubstrateListPage), `/t/{slug}/standorte/substrates/{key}` (SubstrateDetailPage), `/t/{slug}/standorte/substrates/batches/{key}` (BatchDetailPage)
- SubstrateListPage: DataTable (favorite-star, Typ, Bezeichnung, pH-Basis, EC-Basis, Wiederverwendbar); useLocalFavorites('kamerplanter-substrate-favorites'); FilterListIcon nur wenn hasFavorites=true
- Two create buttons: "Substrat erstellen" (SubstrateCreateDialog) and "Mischung erstellen" (SubstrateMixDialog with BlenderIcon)
- SubstrateDetailPage: 4 fieldset-Cards (Identifikation, Chemische Eigenschaften, Physikalische Eigenschaften, Wiederverwendung); `data-testid="substrate-detail-page"` on root; Chargen-Tabelle darunter
- Reusability results = Alert below batch table; `severity="success"` for can_reuse=true, `severity="warning"` for false; accumulates per batch key
- SubstrateMixDialog: min 2 rows, Slider (0.01–1.0), `canSubmit = rows.length>=2 && isBalanced && allSelected && noDuplicates`; keine geschachtelten Mischungen (is_mix=true gefiltert)
- Zod: ph_base(min=0,max=14), ec_base_ms(min=0), air_porosity_percent(min=0,max=100), max_reuse_cycles(min=1), batch_id(min=1)
- i18n keys: `pages.substrates.*`, `pages.batches.*`, `enums.substrateType.*` (14 values), `enums.waterRetention.*`, `enums.bufferCapacity.*`, `enums.irrigationStrategy.*`
- Reusability i18n: `reusabilityOk`="Charge {{batch}}: Wiederverwendbar"; `reusabilityRequired`="Charge {{batch}}: Behandlung erforderlich — {{treatments}}"
- Output: `spec/e2e-testcases/TC-REQ-019.md` with 38 test cases

## REQ-023 Benutzerverwaltung & Authentifizierung — Key Test Insights
- Auth pages in `src/frontend/src/pages/auth/`: LoginPage, RegisterPage, EmailVerificationPage, PasswordResetRequestPage, PasswordResetConfirmPage, AccountSettingsPage, OAuthCallbackPage
- AccountSettingsPage tabs Full-Modus (8): profile, security, sessions, apikeys, experience, ha, platform, account
- AccountSettingsPage tabs Light-Modus (3): profile, experience, ha — no security/sessions/apikeys/platform/account
- SEC-H-009: PasswordResetRequestPage catch block ALSO calls setSent(true) — intentional; both "E-Mail exists" and "not found" return same success message
- i18n auth keys: `pages.auth.registrationSuccess`, `pages.auth.resetEmailSent`, `pages.auth.passwordMismatch`, `pages.auth.passwordHelp`="Mindestens 10 Zeichen", `pages.auth.rememberMe`, `pages.auth.apiKeyCreatedWarning`, `pages.auth.apiKeyRevoked`, `pages.auth.passwordChanged`="Passwort geändert. Alle Sitzungen wurden beendet."
- Service Account pages NOT YET IMPLEMENTED in frontend (spec §5b.10 is forward-looking)
- Platform-Admin detection in AccountSettingsPage: if fetchAdminStats+Tenants+Users all succeed → isPlatformAdmin=true
- Token refresh: Axios interceptor handles 401 → refresh → retry transparently; test by waiting 15min for access token expiry
- ProtectedRoute redirects unauthenticated to /login; PublicOnlyRoute redirects authenticated to /dashboard
- Service Account Erfahrungsstufe: hidden for `beginner`, visible from `intermediate`
- Tenant-Admin: max roles for Service Accounts = grower or viewer (not admin)
- 72 test cases in `spec/e2e-testcases/TC-REQ-023.md`

## REQ-024 Multi-Tenant — Key Test Extraction Insights
- TenantSettingsPage (`/t/{slug}/settings`) has 2 tabs: "Mitglieder" (all roles) and "Einladungen" (Admin only)
- Tab-visibility is role-conditional: `isAdmin` from `useTenantPermissions()` hook drives tab/button visibility
- i18n: `pages.tenants.{tabMembers, tabInvitations, invitationSent, linkCopied, memberRemoved, noMembers, noInvitations, invitationAccepted, linkCopied}`
- No dedicated MemberListPage/InvitationListPage — both are tabs within TenantSettingsPage
- Write-control pattern: for same resource test all 3 conditions: (1) admin role, (2) grower + assigned to me, (3) grower + no assignment (community resource)
- Letzter-Admin-Schutz: applies to role-change AND member-remove AND leave-tenant — 3 separate test cases needed
- Platform-Tenant (`is_platform: true`): slug=`platform`, only one exists, enables cross-tenant powers
- Seeded test tenants: "demo-garten" (personal, Admin), "gemeinschaftsgarten-sonnenschein" (organization, Admin)
- 5 permission layers to test: (1) tenant role, (2) assignment-based write-control, (3) invitation permissions, (4) platform roles, (5) collaboration features (duty/bulletin/shopping)
- 82 test cases in `spec/e2e-testcases/TC-REQ-024.md`

## REQ-021 Erfahrungsstufen — Key Implementation Facts
- AccountSettingsPage Tab "Erfahrungsstufe" (key `tabExperience`): ToggleButtonGroup (not segment control), `data-testid="experience-toggle-{level}"`
- Downgrade uses `window.confirm()` (browser native dialog), NOT a MUI Dialog — i18n key: `pages.auth.experienceLevelDowngradeWarning`
- Upgrade (beginner→intermediate or any level-up): NO confirmation dialog, immediate save + Snackbar "Gespeichert"
- `fieldConfigs.ts` is the canonical source for all field-level visibility rules — read this file first before writing SpeciesCreateDialog/PlantingRun/Site/GrowthPhase/Fertilizer test cases
- SpeciesCreateDialog v1.1: ALL fields are `intermediate` or `expert` — no `beginner` fields (Quick-Add replaces CRUD for beginners)
- `navItemConfig` + `navSectionConfig` in `fieldConfigs.ts` define exact nav tiering — `/kalender` is `intermediate` (not beginner as spec prose suggests)
- `isNavVisible` does NOT have `showAllOverride` (nav tiering cannot be temporarily overridden — only field visibility can)
- QuickAddPlantDialog: NOT yet implemented in frontend (spec-forward); Beginner adds plants via this flow, Expert uses full Species→PlantInstance workflow
- Output: `spec/e2e-testcases/TC-REQ-021.md` with 52 test cases

## REQ-029 KI-Bilderkennung — UI Patterns
- See detailed notes: [req_029_ki_bilderkennung.md](req_029_ki_bilderkennung.md)
- 58 test cases in `spec/e2e-testcases/TC-REQ-029.md`
- Feature-Toggle: buttons absent when no key; confidence thresholds 0.85=auto-accept, 0.10=min-show
- Consent purpose `plant_identification` — own dialog on first use, revocable in Datenschutz
- PlantNet (fallback): Artbestimmung only, Diagnose-Tab hidden; Expert: +GBIF link +expandable JSON

## REQ-007 Erntemanagement — UI Patterns
- See detailed notes: [req_007_harvest.md](req_007_harvest.md)
- 42 test cases in `spec/e2e-testcases/TC-REQ-007.md`
- 4-tab Detail pattern: Details / Qualität / Ertrag / Bearbeiten (useTabUrl, URL-persistent)
- Conditional render on Quality+Yield tabs: create-form when no data exists, read-table otherwise
- Quality Score LinearProgress: >= 80=green, >= 60=orange, < 60=red

## REQ-030 Notification System — UI Patterns
- AccountSettingsPage gains Tab 6 "Benachrichtigungen" (not yet implemented, spec v1.0)
- Bell-Icon in AppBar with Badge (unread count), opens Drawer/Dropdown Notification Center
- Feature-Toggle: channels only active when server-side config present (HA_URL+HA_TOKEN, SMTP, VAPID)
- Erfahrungsstufen (REQ-021) affect channel visibility: Beginner=HA+Email, Intermediate=+PWA, Expert=+Apprise+TypeOverrides
- Actionable Erledigt-Button in notifications triggers REQ-022 CareConfirmation
- Test-Notification rate-limited to 5/hour (visible as disabled state or error message in UI)
- InApp is always the fallback when no external channel configured

## REQ-020 Onboarding-Wizard — UI Patterns
- See detailed notes: [req_020_onboarding.md](req_020_onboarding.md)
- 53 test cases in `spec/e2e-testcases/TC-REQ-020.md`
- Dynamic steps: beginner=5, intermediate+favorites=7; `nutrientPlans` step conditional on favoriteSpeciesKeys.length>0
- Smart-Home toggle (v1.6): hidden for beginner, visible for intermediate/expert
- Water section in site step: only intermediate/expert; fields tap_water_ec (0-2.0), tap_water_ph (3-10), ro_toggle
- Resume via onboarding_state.wizard_step > 0 restores all wizard state
- Kit auto-populate: site_type, site_name (unless manually changed), plant_configs, favorites

## REQ-022 Pflegeerinnerungen — Key Test Extraction Insights
- PflegeDashboardPage at `/pflege`; ReminderCards sorted: overdue(red)→due_today(yellow)→upcoming(grey)
- Optimistic Updates: confirmReminder removes card immediately; snoozeReminder moves to upcoming; rollback+snackbar on error
- CareProfileEditDialog: all Sliders (not text fields); Monats-Chips (multi-select); conditional fields (humidity/location months hidden when toggle off)
- Care-Style-Wechsel requires confirmation dialog (styleChangeConfirm) — resets ALL sliders to preset defaults
- 3 Guard systems to test: (1) Dünge-Guard (season months + DORMANCY_PHASES), (2) Gießplan-Guard (active Run+NutrientPlan+WateringSchedule suppresses only watering+fertilizing), (3) Winterschutz-Guard (frost_sensitivity=hardy → no winter reminders)
- Acclimatization-Phase: watering interval × 1.3 (lengthened); fertilizing blocked (in DORMANCY_PHASES)
- Winter-Multiplikator: cactus=3.0×, succulent=2.5×, mediterranean=2.0×, tropical=1.5×, calathea/fern=1.3×
- Location_check: only first 15 days of Oct (NH) and Mar (NH); configurable per CareProfile via location_check_months dict
- Humidity_check: only in winter months (Nov-Feb NH) AND humidity_check_enabled=true (calathea/fern/tropical=true, rest=false)
- Water quality hints shown only for orchid/calathea/fern; null for tropical/succulent/cactus/mediterranean
- Deadheading: only outdoor_annual_ornamental preset; blocked for Cultivar.traits=['self_cleaning'] (AB-016)
- CareConfirmation: immutable event-log; auto-created when watering plan confirmed (REQ-014 interop) — only if CareProfile exists
- i18n prefix: pages.care.* for all labels; enums.careStyle.* for style labels; enums.wateringMethod.* for method labels
- 68 test cases in spec/e2e-testcases/TC-REQ-022.md

## REQ-002 Standortverwaltung — Key Test Extraction Insights
- Frontend pages: SiteListPage, SiteCreateDialog, SiteDetailPage (WaterSourceSection embedded), LocationTreeSection (MUI SimpleTreeView), LocationCreateDialog, LocationDetailPage, SlotCreateDialog, SlotDetailPage
- Zod schemas: Site(name.min(1), climate_zone string, total_area_m2.min(0), timezone string); Location(name.min(1), location_type_key string, area_m2.min(0), light_type enum, irrigation_system enum, lights_on/off HH:MM regex nullable, use_dynamic_sunrise bool); Slot(slot_id regex ^[A-Z0-9]+_[A-Z0-9]+$, capacity_plants min(1) max(20))
- Slot-ID transform: `.transform(v => v.toUpperCase())` — auto-uppercased before validation
- Light type drives field visibility: led/hps/cmh → lights_on/lights_off editable; natural/mixed → use_dynamic_sunrise toggle visible
- WaterSource soft-warnings (non-blocking): GH-Plausibilität (>30% Ca+Mg vs. GH), Messalter (>12 months), RO-Membran (ec_ms > 0.05)
- i18n keys: `pages.sites.water.{ghPlausibilityWarning, measurementAgeWarning, roMembraneWarning}`; `pages.locationTypes.cannotDeleteSystem`
- LocationType CRUD: 10 system seeds (is_system=true, undeletable HTTP 403); delete also blocked if referenced (HTTP 409 shown as snackbar)
- Cascading delete: blocked if any slot in subtree occupied; error shows count + first 3 slot IDs
- Crop rotation: CRITICAL (same family, 3y window), WARNING (3× heavy feeders), OK (no warning); shown at slot assignment
- 62 test cases; output: `spec/e2e-testcases/TC-REQ-002.md`

## NFR-007 Betriebsstabilitaet — Test Extraction Insights
- NFR docs have a fundamentally different test extraction profile than REQ docs: most tests require a full Monitoring-Stack (Prometheus, Alertmanager, Grafana, Kubernetes) — mark as [Infra-Test]
- Only 12 of 42 tests are standard browser/HTTP-client tests; the rest require infrastructure
- Use two-tier test labelling: standard E2E (runs in any env) vs. [Infra-Test] (needs full K8s+monitoring stack)
- Health-check endpoints (`/health/live`, `/health/ready`) ARE browser-accessible — these are concrete E2E tests
- Key liveness vs. readiness distinction: liveness only checks if the process is alive; readiness also checks DB connectivity (implemented in `src/backend/app/api/v1/health/router.py`)
- `readiness` returns `{"status": "ready"|"not_ready", "database": true|false}` — test both values
- `/metrics` endpoint is testable from browser: must contain `http_requests_total`, `circuit_breaker_state`, `connection_pool_active_connections`, `service_degraded`
- Graceful degradation table (§4.5) generates browser-observable test cases: "Daten verzoegert", "Stale-Markierung", cache-bypass (no error visible), Celery-fallback for phase transitions
- Circuit Breaker UI effect: OPEN state → immediate 503 with Retry-After instead of hanging timeout — test for absence of endlos-spinner
- NFR test IDs use pattern TC-NFR007-{NNN} (not TC-NFR-007-{NNN}) — note no zero-padding on NFR number
- Output path: `spec/e2e-testcases/TC-NFR-007.md`
- 42 test cases covering all 8 major sections of NFR-007

## REQ-027 Light-Modus — Key Test Extraction Insights
- NOT yet implemented in frontend (spec v1.2, marked "Entwurf") — all test cases are spec-forward
- Two deployment environment variables drive all behavior: `KAMERPLANTER_MODE` (backend) + `VITE_KAMERPLANTER_MODE` (frontend)
- Primary test categories: (1) ausgeblendete UI-Elemente, (2) nicht erreichbare Routen, (3) Kernfunktionalitaet im Light-Modus, (4) Moduswechsel Light↔Full
- AccountSettingsPage Light-Modus: only 2 tabs (Allgemein + Erfahrungsstufe); Full-Modus note in TC-REQ-023 says 3 tabs (profile+experience+ha) — spec may differ from impl, verify when implemented
- Uebernahme-Dialog after Upgrade Light→Full: triggered only for FIRST registering user; subsequent users get normal flow
- Roundtrip-Test (TC-027-037) is the most complex integration test: requires cycling through all 4 phases
- Contrast tests (TC-027-045, TC-027-048) verify Full-Modus behavior as baseline for Light-Modus tests
- Scope-Abgrenzung tests (TC-027-051, TC-027-052): verify ABSENCE of features (no runtime switch, no tenant switcher)
- 52 test cases in `spec/e2e-testcases/TC-REQ-027.md`; IDs TC-027-{NNN}
