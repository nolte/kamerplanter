# i18n Ist-Zustand-Aufnahme (N-Sprachen-Mehrsprachigkeit)

> Vollständiges Inventar jeder lokalisierten Fläche im Stack — Seed/Stammdaten, Schemas,
> Domain/DTO, Frontend, Backend/API + Fehler, RAG/Knowledge + Docs-Site.
> Erstellt für Issue #568. Zielarchitektur: `spec/analysis/i18n-implementation-concept.md`.
> Anforderung: `spec/nfr/NFR-017_Skalierbare-Mehrsprachigkeit.md`. Rollout: `.audits/plans/07-i18n-nlanguage-rollout.md`.
>
> Alle `file:line`-Angaben und Zählungen sind per Grep gegen `develop`
> (Worktree-Stand 2026-07-12) real ermittelt.

## 0. Executive Summary

Der Codebestand ist **zwischen zwei Modellen gespalten**:

- **Per-Sprache-Attribut (Anti-Pattern, skaliert NICHT):** Felder mit Sprachsuffix
  (`common_name_de`, `name_de`, `label_de`, `name_en`). Jede weitere Sprache erzwingt neue
  Felder auf **jeder** Entität (Seed, Schema, Domain, DTO, Frontend-Selektion).
- **Locale-Map (skalierbares Zielmuster, bereits vorhanden):** `dict[str, str]`, nach
  Sprachcode verschlüsselt, mit Resolver + Fallback — heute nur in `glossary_terms` und
  `starter_kits`.

### Kern-Kennzahlen (Anti-Pattern)

| Fläche | Metrik | Zahl |
|--------|--------|------|
| Seed-YAML | `*_de`/`*_en`-Feld-Vorkommen | **784** (in 15 Dateien; ~68 % nur-DE) |
| Seed-Schemas | Schema-Dateien mit Suffix-Properties | **6** |
| Backend Domain/DTO | `_de`/`_en`-Felddefinitionen | **141** |
| Frontend | `_de`/`_en`-Feldzugriffe | **246** (16 Dateien) |
| Frontend | binäre Sprach-Zweige (`=== 'de'`, `startsWith('en')`) | **~76** |
| Frontend | hartkodierte Locale-Literale (`de-DE`/`en-US`/`en-GB`) | **45** |
| **Summe per-Sprache-Attribut-Stellen (Daten+Code)** | Seed 784 + BE 141 + FE 246 | **1171** |

### Kern-Kennzahlen (bereits skalierbar / N-Sprachen-fähig)

| Fläche | Metrik | Zahl |
|--------|--------|------|
| Seed Locale-Maps | Instanzen (`glossary_terms`, `starter_kits`) | **150** in 2 Dateien |
| Backend Locale-Maps | `dict[str,str]`-Felder + Resolver | 5 Felder (glossary, starter_kit) |
| Frontend i18n-Katalog | Blatt-Keys (de/en, react-i18next) | ~5368 |
| Frontend Plurals | i18next `_one`/`_other`-Keys | 32 (`{{count}}`: 108) |
| Docs-Site | bilingual gepflegte Seiten (DE/EN) | 118 / 118 |

### Zentrale strukturelle Befunde

1. **Keine serverseitige Locale-Resolution.** Kein `Accept-Language`, kein `babel`/`gettext`.
   Sprache ist überall ein durchgereichter Request-Parameter mit Default `"de"`.
2. **`user.locale` wird gespeichert, aber nie zur Sprachwahl gelesen** (nur 3 Echo-Stellen).
3. **Fehlermeldungen gemischt:** strukturierter `error_code`-Katalog (36 Codes) + englischer
   Freitext; ~10 nutzerseitige Meldungen sind Deutsch (Aquaponik, Hardiness).
4. **Frontend-Katalog + Plurals sind N-Sprachen-fähig**, aber alles Backend-Content-, Format-
   und KI-Sprach-bezogene ist **binär hart** auf `de`/`en` verdrahtet; **RTL fehlt vollständig**.
5. **RAG/Knowledge ist zu 100 % DE**, mehrsprachig *fähig* über einen `language`-Spaltenfilter
   + parallele DE/EN-Prompt-Strings; `Literal["de","en"]` blockiert N-Sprachen ohne Migration.

---

## 1. Seed-/Stammdaten

Basis: `src/backend/app/migrations/seed_data/`. **51 YAML-Dateien** (17 Schemas unter `schemas/`).

### 1.1 Per-Sprache-Attribut-Anti-Pattern (`*_de` / `*_en`)

**784 Feld-Vorkommen in 15 Seed-Dateien** (verifiziert:
`grep -rhoE '[a-z0-9]+_(de|en):' seed_data/*.yaml | wc -l` = 784).

| Datei | Felder (Vorkommen) | Σ | Abdeckung | Entitätstyp |
|-------|--------------------|---|-----------|-------------|
| `ipm.yaml` | `name_de`(40), `description_de`(40), `mode_of_action_de`(40), `how_to_apply_de`(40), `precautions_de`(40), `common_name_de`(34), `damage_symptoms_de`(34), `host_plants_de`(34), `prevention_tips_de`(34), `monitoring_hints_de`(34) | **370** | **nur DE** | IPM / pests / treatments |
| `activities.yaml` | `name_de`(51), `description_de`(51) | **102** | **nur DE** | care / activities |
| `substrates.yaml` | `name_de`(28), `name_en`(28) | **56** | DE+EN | substrates |
| `phase_sequences.yaml` | `display_name_de`(21), `description_de`(21) | **42** | **nur DE** | phases / growth_phases |
| `botanical_families.yaml` | `common_name_de`(18), `common_name_en`(18) | **36** | DE+EN | botanical_families / enums |
| `fish_species.yaml` | `common_name_de`(8), `common_name_en`(8), `notes_de`(8), `notes_en`(8) | **32** | DE+EN | species (fish) |
| `plant_info_indoor_1.yaml` | `common_name_de`(15), `common_name_en`(15) | **30** | DE+EN | plant_info / species |
| `plant_info_indoor_2.yaml` | `common_name_de`(15), `common_name_en`(15) | **30** | DE+EN | plant_info / species |
| `plant_info_outdoor_2.yaml` | `common_name_de`(15), `common_name_en`(15) | **30** | DE+EN | plant_info / species |
| `plant_info_outdoor_1.yaml` | `common_name_de`(9), `common_name_en`(9) | **18** | DE+EN | plant_info / species |
| `hardiness_zones.yaml` | `description_de`(9), `representative_regions_de`(9) | **18** | **nur DE** | enums / hardiness_zones |
| `location_types.yaml` | `name_en`(12) | **12** | **nur EN** | enums / location_types |
| `adventskalender.yaml` | `common_name_de`(2), `common_name_en`(2) | **4** | DE+EN | species (seasonal) |
| `plant_info_outdoor_3.yaml` | `common_name_de`(1), `common_name_en`(1) | **2** | DE+EN | plant_info / species |
| `plant_info.yaml` | `common_name_de`(1), `common_name_en`(1) | **2** | DE+EN | plant_info / species |

Asymmetrie: **nur-DE Suffix-Felder ohne `_en`-Gegenstück** = **532/784 (~68 %)**
(`ipm.yaml` 10 Felder, `activities.yaml`, `phase_sequences.yaml`, `hardiness_zones.yaml`).
Nur-EN: `location_types.yaml` (`name_en`). Sauber gepaart DE+EN: `plant_info*`, `botanical_families`,
`fish_species`, `substrates`, `adventskalender`.

Keine Suffix-/Map-Felder (0 Treffer): `nutrient_plans_*`, `fertilizers*`, `plagron`, `gardol`,
`companion_planting`, `substrate_defaults`, `light_mode`, `harvest_indicators`,
`overwintering_profiles`, `lifecycles_outdoor`, `workflows`, `species.yaml`.

### 1.2 Skalierbare Locale-Map-Muster (Zielmuster, bereits vorhanden)

**150 Locale-Map-Feld-Instanzen in 2 Dateien.**

| Datei | Feld | Muster | Instanzen | Entität |
|-------|------|--------|-----------|---------|
| `glossary_terms.yaml` | `labels` | inline `{de:…, en:…}` | 32 | glossary |
| `glossary_terms.yaml` | `long_labels` | multi-line `de:`/`en:` | 32 | glossary |
| `glossary_terms.yaml` | `aliases` | multi-line `de:`/`en:` (Listen) | 32 | glossary |
| `glossary_terms.yaml` | `fallback_text` | multi-line `de:`/`en:` | 32 | glossary |
| `starter_kits.yaml` | `name_i18n` | multi-line `de:`/`en:` | 11 | starter_kits / workflows |
| `starter_kits.yaml` | `description_i18n` | multi-line `de:`/`en:` | 11 | starter_kits / workflows |

Beispiel `glossary_terms.yaml:13-26` (Term `vpd`). Hinweis: `glossary_terms.yaml` trägt zusätzlich ein
**DE-only Format-Placeholder-Feld** `rag_query_template` mit `{label_de}` (32 Vork., z.B. `:27`) — bewusst
DE (RAG-Prompt), referenziert aber das Suffix-Schema.

### 1.3 Schemas — Zementierung beider Muster

Anti-Pattern-Deklarationen (Suffix als eigene Properties):

| Schema | Property-Deklarationen (`file:line`) |
|--------|--------------------------------------|
| `schemas/ipm.schema.yaml` | `common_name_de`:62, `description_de`:80, `damage_symptoms_de`:85, `host_plants_de`:96, `prevention_tips_de`:102, `monitoring_hints_de`:106, `name_de`:181, `description_de`:191, `how_to_apply_de`:195, `mode_of_action_de`:199, `precautions_de`:203 |
| `schemas/plant_info.schema.yaml` | `common_name_de`:126, `common_name_en`:127 |
| `schemas/phase_sequences.schema.yaml` | `display_name_de`:31, `description_de`:36, `display_name_de`:68, `description_de`:72 |
| `schemas/activities.schema.yaml` | `name_de`:23, `description_de`:27 |
| `schemas/botanical_families.schema.yaml` | `common_name_de`:24, `common_name_en`:26 |
| `schemas/location_types.schema.yaml` | `name_en`:27 |

Skalierbare Deklaration: `schemas/starter_kits.schema.yaml:25-36` (`name_i18n`/`description_i18n` als
Objekt `properties:{de,en}`, beide `required` :76). `glossary_terms.yaml` hat **kein** Schema.
**Kein** gemeinsames wiederverwendbares i18n-`$def` in `schemas/_defs.schema.yaml`.

### 1.4 Loader-Kopplung (Kontext)

Suffix-Felder sind in den Python-Seedern hart verdrahtet: `seed_plant_info.py:86-87`,
`seed_plant_info_extended.py:90-91`, `seed_adventskalender.py:57-58`,
`seed_phase_sequences.py:38-40,79-81`, `seed_hardiness_zones.py:52,63`, `seed_substrates.py:26,56`,
`seed_location_types.py:24`, `seed_data.py:495` (`taxon.common_name_de`). Eine Migration auf Locale-Maps
betrifft also Loader + ORM-Felder mit.

---

## 2. Backend / API — Locale-Plumbing, Fehler, Modelle

Basis: `src/backend/app/` (846 Python-Dateien).

### 2.1 Locale-Resolution — NICHT VORHANDEN

- **Kein `Accept-Language`** (0 Treffer über alle `*.py`). Header-Reads betreffen nur X-Request-ID
  (`common/middleware.py:17`) und x-forwarded-for (`common/request_ip.py:19`).
- **Kein `babel`/`gettext`/`flask_babel`** (0 Treffer).
- **Keine Locale-Dependency/Middleware** in `common/dependencies.py`, `common/middleware.py`,
  `common/auth.py`.
- **Sprache = expliziter Request-Parameter, Default `"de"`** — 72 `language`/`locale`-Referenzen in
  `api/` über 15 Dateien. Beispiele:
  - `api/v1/pest_detection/tenant_router.py:41,74` — `language: str = Form("de")`
  - `api/v1/glossar/public_router.py:38`, `api/v1/glossar/router.py:37` — `language: Language = "de"`
  - `api/v1/ki_assistent/tenant_router.py:84,104,144` — `language: str = Query("de")`
  - `api/v1/print/tenant_router.py:30,52,81` — `locale: str = Query("de", pattern="^(de|en)$")`
  - `api/v1/diagnose/tenant_router.py:87` — `language: str = Query(default="de")`
  - `api/v1/recognition/tenant_router.py:111` — `language: str = Form("de")`
  - `api/v1/knowledge/router.py:40` — `doc_language: Literal["de","en","all"] | None`
- Auf Service-/Domain-Ebene zieht sich `language: str = "de"` durch die gesamte Aufrufkette
  (`diagnose_service.py:100`, `pest_detection_service.py:91`, `identification_service.py:121,231`,
  `print_service.py:46,149,239`, `engines/identification_engine.py:91,158`, `ai_assistant_service.py`
  ~20 Stellen). Sprache wird **durchgereicht, nie aufgelöst**.

### 2.2 Fehler-Sprache

Strukturierter Katalog vorhanden (kein reiner Freitext):
- `common/exceptions.py` — Basis `KamerplanterError` mit `error_code` + `message` + `details`,
  **37 Subklassen**, **36 distinkte `error_code`-Konstanten** (`ENTITY_NOT_FOUND`, `DUPLICATE_ENTRY`,
  `RATE_LIMIT_EXCEEDED`, `WINTER_PATH_VIOLATION`, …).
- `common/error_schemas.py` — `ErrorResponse{error_id, error_code, message, details[], …}`.
- `common/error_handlers.py` — mappt Fehler → JSON mit `error_code` + **englischer** `message`.

Sprache der `message`-Strings = **Englisch (Freitext), kein i18n-Key**:
`"{entity} with key '{key}' not found."`, `"Rate limit exceeded for source '{source}'."`,
`error_handlers.py:61` `"The input data is invalid."`, `:87` `"An internal error occurred. …"`.
**Einzige i18n-Key-Ausnahme:** `AiDisabledError` → `message="ai.disabled_for_tenant"`.

`HTTPException` (14×) / `detail=` (13×) — Englisch bzw. durchgereichter `str(e)`
(`planting_runs/tenant_router.py:249,253`, `phases/router.py:55,59,72`,
`print/tenant_router.py:88,95`, `knowledge/router.py:31`, `ki_assistent/deps.py:23`).

`raise ValueError(...)` — **147 Vorkommen**, überwiegend Englisch (`domain/models/*`).

**Deutsche nutzerseitige Meldungen (~10, Minderheit):**
`domain/models/hardiness_zone.py:56,63`; `domain/services/aquaponik_service.py:131,133,146,172,175,270,313`
(7×); `api/v1/aquaponik/schemas.py:220`. → technische Fehler Englisch, nutzerseitige *überwiegend*
Englisch, punktuell DE — inkonsistent, nicht lokalisiert.

### 2.3 Per-Sprache-Felder in Modellen / DTOs

(a) **Suffix-Felder `_de`/`_en` — 141 Felddefinitionen** über `domain/models/` + `api/`. Top:
`api/v1/ipm/schemas.py`(34), `domain/models/ipm.py`(11), `api/v1/phase_sequences/schemas.py`(12),
`api/v1/aquaponik/schemas.py`(12), `api/v1/tasks/schemas.py`(8),
`domain/models/task.py:66,68,70,91,108,110` (`name_de`,`instruction_de`,`description_de`,`rationale_de`),
`api/v1/substrates/schemas.py`(6), `domain/models/substrate.py:21,22`,
`api/v1/activities/schemas.py`(6), `domain/models/diagnosis.py`(5), `domain/models/privacy.py`(4),
`domain/models/phase_sequence.py`(4), `domain/models/aquaponik.py`(4),
`api/v1/botanical_families/schemas.py`(4), `api/v1/activity_plans/schemas.py`(4),
`api/v1/location_types/schemas.py`(3), `domain/models/hardiness_zone.py:40,41`,
`domain/models/location_type.py:9`, `domain/models/pest_taxonomy.py:52,60,84,100` (nur `_de`, ~40 Schädlinge).

(b) **Locale-Maps `dict[str,str]` (Zielmuster):**
- `domain/models/glossary_term.py:58,59,65` — `labels`/`long_labels`/`fallback_text`; Resolver
  `label_for/long_label_for/fallback_for` mit **Fallback auf `"de"`** (`:73-83`);
  `Language = Literal["de","en"]` (`:25`).
- `api/v1/glossar/schemas.py:21,22,28` (Response-Spiegel).
- `domain/models/starter_kit.py:11,12` + `api/v1/starter_kits/schemas.py:9,10` —
  `name_i18n`/`description_i18n`.

### 2.4 UserPreference / `locale`

- `domain/models/user.py:30` `locale: str = "de"`; `:45` `UserProfile.locale`; `:54`
  `UserProfileUpdate.locale`. `domain/models/user_preference.py:80` `locale: str = "de"`.
  API: `api/v1/users/schemas.py:7`, `api/v1/user_preferences/schemas.py:12,26`, `api/v1/auth/schemas.py:58`.
- **Serverseitige Nutzung: nur Speichern & Echo** — `user_service.py:31-32,61`,
  `auth_service.py:764`. `user.locale` steuert **nirgends** Sprache von Fehlern, Labels, Mails oder
  KI-Antworten; die `language`-Router-Params werden **nicht** aus `user.locale` geseedet.

### 2.5 Logging

`structlog`-Events sind Englisch/`snake_case` (`app_error`, `validation_error`, `email_send_failed`,
`decryption_failed`). Für i18n unkritisch (betreiberseitig) — konform mit der English-only-Regel.

---

## 3. Frontend

Basis: `src/frontend/src/` (ohne `test/`).

### 3.1 react-i18next Setup (N-Sprachen-fähig)

- `i18n/i18n.ts` (37 Z.), `i18n/index.ts`, `i18n/locales/de/translation.json` (6234 Z.),
  `i18n/locales/en/translation.json` (6233 Z.).
- Stack: `i18next@^26`, `react-i18next@^17`, `i18next-browser-languagedetector@^8`.
- Kataloge **statisch importiert** als `resources` (`i18n.ts:4-5,11-14`), kein lazy-load / http-backend.
- `fallbackLng: 'de'` (`:15`); Default-Namespace `translation` (`:12-13`);
  Detektion `order:['localStorage','navigator']`, `lookupLocalStorage:'kamerplanter-lang'` (`:19-23`).
- **Genau 2 Sprachen** (de/en) hart im `resources`-Objekt.
- Katalog: **~5368 Blatt-Keys** (de) / 5367 (en); 20 Top-Level-Gruppen; `enums`-Gruppe mit
  **120 Enum-Unterkatalogen**.

### 3.2 Binäre Sprach-Selektion (Anti-Pattern) — ~76 Zweige + 246 Feldzugriffe

**(a) `startsWith('en'|'de')` — 17 Stellen:**
`components/form/SubstrateSelectField.tsx:65`, `components/ai/DailyTipCard.tsx:59`,
`components/ai/WhyDrawer.tsx:51`, `components/ai/TipCardsPanel.tsx:41`, `components/ai/AiChatDrawer.tsx:63`,
`components/diagnosis/DiagnosisWizard.tsx:24`, `components/glossary/TermTooltip.tsx:42`,
`pages/ki-assistent/KIAssistentPage.tsx:34`, `pages/standorte/SubstrateMixDialog.tsx:47`,
`pages/standorte/SubstrateListPage.tsx:41`, `pages/standorte/SubstrateDetailPage.tsx:223,249,410`,
`pages/glossar/GlossaryPage.tsx:35`, `pages/aquaponik/AquaponikPage.tsx:94`,
`pages/stammdaten/ActivityListPage.tsx:52`, `pages/stammdaten/ActivityDetailPage.tsx:190`.

**(b) `=== 'de'` / `=== 'en'` — 59 Stellen** (Cluster): `hooks/useLocalizedField.ts:16` (zentraler Hook),
`utils/formatting.ts:24` (zentrale Locale-Ableitung), `components/layout/LanguageSelector.tsx:34`,
`components/dashboard/SeasonOverviewPanel.tsx:99`, `pages/phasen/*` (PhaseDefinitionListPage:100,
PhaseSequenceDetailPage:244,359,401,499,632, PhaseDefinitionDetailPage:103,172,232,291,408,
PhaseSequenceEntryDialog:158,159, PhaseSequenceListPage:216), `pages/aufgaben/*`
(WorkflowDetailPage:503,504,866,867,1099,1100, TaskDetailPage:490,515, TaskQueuePage:585,
WorkflowInstantiateDialog:397), `pages/durchlaeufe/*` (ActivityPlanTab:565,568,803,807,873,
WateringCalendarView:237,245,525), `pages/kalender/*` (SowingCalendarView:180, PhaseTimelineView:181,
CalendarPage:529,539,552,569,1254, SeasonOverviewView:38), `pages/pflege/*` (SpringReturnAssistant:165,
PflegeDashboardPage:139), `pages/pflanzen/*` (GrowthPhaseListSection:67,
PlantInstanceDetailPage:2285,2300, OverwinteringSection:104), `pages/stammdaten/*`
(BotanicalFamilyListPage:37,111, ActivityDetailPage:191, ActivityListPage:58,180),
`pages/pflanzenschutz/PestDetailPage.tsx:143`, `pages/standorte/*`
(SubstrateMixDialog:209, SubstrateListPage:78,131).

**(c) Per-Sprache-Backend-Felder `_de`/`_en` — 246 Referenzen** (16 Nicht-Test-Dateien).
Häufigkeit: `name_de`(109), `description_de`(62), `name_en`(39), `instruction_de`(15),
`rationale_de`(7), `precautions_de`(5), `message_en`(4), `message_de`(4), `notes_de`(1).
Zentraler Kapsel-Hook (aber weiterhin binär): `hooks/useLocalizedField.ts:16`
(`i18n.language === 'de' ? rec['${field}_de'] : rec[field]`), genutzt in 6 Dateien
(`PestListPage`, `TreatmentDetailPage`, `TreatmentListPage`, `PestDetailPage`, `GenericWidget`).
Typen: `api/types.ts` (nur `_de`/`_en`-Varianten je Feld → hartes 2-Sprachen-Datenmodell).

### 3.3 Enum-Rendering

**Kein zentraler Helper.** **519** inline `t(\`enums.<enumName>.<value>\`)`-Aufrufe (Nicht-Test);
**115 distinkte Enum-Gruppen** referenziert (Katalog: 120). Muster konsistent, aber jeder Call-Site baut
den Key selbst; kein `resolveEnumLabel`/`useEnum`.

### 3.4 Date/Number/Plural

- Zentrale Utility `utils/formatting.ts`: `activeLocale()` (`:24`, `lang === 'de' ? 'de-DE' : 'en-US'`),
  `formatDateTime`/`formatDate`/`formatNumber(WithUnit)` (`Intl` via `toLocale*`).
- **Utility vielfach umgangen:** **99** direkte `toLocale*`-Aufrufe in 39 Dateien; hartkodierte
  Locale-Literale **de-DE 22×, en-US 19×, en-GB 4×** (inkonsistent en-US vs en-GB).
  `Intl` direkt nur 1× (`SiteClimateSection.tsx:51`).
- **dayjs** (`TankStateChart.tsx`, `SensorHistoryChart.tsx`): **hartkodierte DE-Formatstrings**
  (`'DD.MM.'`, `'DD.MM. HH:mm'`, `TankStateChart.tsx:153-158`); **kein** `dayjs.locale()`, **kein**
  `LocalizationProvider`/`AdapterDayjs`-Locale (MUI-X-Pickers ohne konfiguriertes Locale-Adapter).
- **Plural (i18next-nativ, N-Sprachen-fähig):** 108× `{{count}}`, 32 `_one`/`_other`-Keys; mehrere
  `_other` ohne `_one` (unvollständige Paare: `activeFilters_other`, `channels_other`, …).

### 3.5 RTL-Readiness — praktisch 0

Kein `dir=`, kein `'rtl'`, kein `stylis-plugin-rtl`/`rtlPlugin` (Count 0). `theme/theme.ts` setzt
kein `direction`. Logische CSS-Properties: nur schwache False-Positive-Treffer; Layout arbeitet mit
physischen `left/right`. Eine RTL-Sprache (ar/he) erfordert Theme + Emotion-RTL-Plugin + Umstellung
auf logische Properties — 0 Grundlage.

### 3.6 Sprachumschalter

`components/layout/LanguageSelector.tsx`: Sprachen **fest verdrahtet**
(`[{code:'de',label:'Deutsch'},{code:'en',label:'English'}]`, `:8-11`, Labels hartkodiert);
`i18n.changeLanguage(lang.code)` (`:40`); Persistenz via Detector-Cache
(localStorage `kamerplanter-lang`, `i18n.ts:21-22`). Eingebunden in `layouts/MainLayout.tsx`.

---

## 4. RAG / Knowledge / KI / Docs

### 4.1 RAG-Chunks (`spec/knowledge/rag/`)

- **61 YAML-Dateien** in 10 Top-Level-Kategorien (allgemein 3, bewaesserung 4, diagnostik 12, duengung 6,
  outdoor 10, pflege 9, phasen 8, substrat 1, umwelt 7, vermehrung 1).
- **Alle DE**, jede Datei trägt `language: de` (Z.3, 61/61). Kein nicht-DE-Chunk
  (`grep language:\s*(en|fr|es|nl|it)` = 0). **Keine** per-Sprache-Duplikate; kein `en`-Verzeichnis.
- Schema pro Datei: `title, language, category, tags, expertise_level, applicable_phases,
  chunks[{id,title,content,metadata}]`.

### 4.2 knowledge-service (`src/knowledge-service/`)

Multilingual *vorbereitet*, aber DE-defaultet und faktisch monolingual DE befüllt.
- Ingestion: `app/ingestor.py:61` `language = data.get("language","de")`; `:62`
  `ts_config = LANG_TO_TSCONFIG.get(language,"simple")`; `:109` schreibt `language` pro Chunk.
  `LANG_TO_TSCONFIG = {"de":"german","en":"english"}` (`app/vectordb/repository.py:15`).
- DB: `migrations/003_add_language_column.sql:6` `language TEXT NOT NULL DEFAULT 'de'` (+`ts_config`
  Default `german`, Index `idx_ai_chunks_language`).
- Retrieval (harte Sprachfilterung): `repository.py:194-196` (vector), `:255-257,278-279` (hybrid)
  `if language and language != "all": conditions.append("language = %s")`; `:272` Query-Regconfig
  Default `german`. `service.py:74` `effective_lang = doc_language or self._default_doc_language`.
- Prompting: `app/prompt_engine.py` — **parallele DE/EN-Prompt-Dictionaries** (`_TYPED_PROMPTS` :57-117,
  `_EXTRACTION_SUFFIX` :39-55, `_VERIFICATION_PROMPT` :120-145, `_ANTI_INJECTION` :152-165);
  `build_system_prompt(question_type, language="de")` :216 mit **`de`-Fallback** (`base.get(language,
  base["de"])` :219-221). EN-Prompts: „Answer in the SAME LANGUAGE…"; DE-Prompts: „Antworte auf Deutsch".
- Defaults: `config.py:55-56` `rag_doc_language="de"`, `rag_prompt_language="de"`; `main.py:100-101,169`.
  Schemas `schemas.py:35,52,53` `Literal["de","en","all"]` / `Literal["de","en"]`.
- Embedding: `embedding.py:12` `multilingual-e5-base`, produktiv `multilingual-e5-large`
  (`config.py:36`, 1024-dim). Multilingual → Embeddings sprachagnostisch; Sprachtrennung rein über
  DB-`language`-Filter.
- **Effekt:** `docker-compose.yml:149,186` mountet nur `./spec/knowledge/rag` (alles `language: de`) →
  Vektor-Store faktisch nur DE.

### 4.3 Plant-Docs (`spec/knowledge/plants/`)

**210 Markdown-Steckbriefe, alle DE**, kein Frontmatter-`language`/`lang` (0 Treffer). Nicht im
RAG-Store (Ingestor liest nur `*.yaml`); dienen dem Stammdaten-Import.

### 4.4 Docs-Site (`docs/`, `mkdocs.yml`)

Voll bilingual DE/EN über mkdocs-static-i18n, Folder-Struktur, DE=default.
- `docs/de/` und `docs/en/`, identische Sektionsstruktur; **DE 118 `.md`, EN 118 `.md`**.
- `mkdocs.yml:80` `- i18n:`, `:81` `docs_structure: folder`, `:82-89` `languages:` (`de` default:true,
  `en` build:true), `:90-119+` `nav_translations`; Search `:75-77` `lang:[de,en]`.

### 4.5 Sonstige KI-Flächen (Backend / Inference / Eval)

- Backend-Prompt-Templates (parallele DE/EN, DE-Default): `diagnosis_analysis_engine.py:112-158`
  (`if language == "en": … else: "Du bist ein Assistent …"`); `ai_assistant_service.py`
  (`ask_public` :403, `_run_ask` :627; KS-Aufrufe mit `doc_language="all"`, `prompt_language=language`
  :414-415,538-539,638-639; hartkodierte DE/EN-Fallback-Texte :335-338,368-371,431-435);
  `glossary_service.py:220-221` (`doc_language="all"`), `_normalise_language` :105.
- explain-Templates: `spec/knowledge/explain-templates/care.yaml` zweisprachig als `question_de`/
  `question_en` (`:7,10,17,20…`), gebaut via `_explain.build_question(id, language, slots)`
  (`ai_assistant_service.py:329`).
- API-Ränder (DE-Default, per Request überschreibbar): `ki_assistent/public_router.py:41`
  (`language=body.language or "de"`), `ki_assistent/tenant_router.py:84,104,144`,
  `glossar/router.py:37`, `glossar/public_router.py:38`, `pest_detection/tenant_router.py:41,74`.
- Vision/Pest-Adapter (Default `language="de"`): `pest_detection_adapter.py:81`,
  `local_pest_adapters.py:74`, `kindwise_pest_adapter.py:46`, `demo_pest_adapter.py:39`,
  `pest_inference_client.py:61`; Inference `src/inference-service/app/main.py:513`.
- Print/PDF: `print_service.py:377` `labels.get(locale, labels["de"])`, Default `locale="de"`.
- RAG-Eval (`spec/rag-eval/`): `benchmark_questions.yaml` **100 DE-Fragen** (`language: de` :18),
  `smoke_questions.yaml:14` `language: de`; **keine EN-Benchmarks**.
- **Tote i18n-Infrastruktur:** `language_mismatch_warning: bool` existiert als DTO-Feld
  (`models/ai_assistant.py:52,138`, `models/glossary_term.py:95,138`, `ki_assistent/schemas.py:29,54`),
  wird durchgereicht, aber **nirgends berechnet/gesetzt** (0 Zuweisungen) — vorgesehen, nicht implementiert.

### 4.6 Skalierungsrisiken RAG/Knowledge

1. Wissensinhalte **nur DE**; echte EN-Qualität bräuchte Übersetzung von 61 RAG-Dateien + 210 Plant-Docs;
   heute LLM-Ad-hoc-Übersetzung von DE-Kontext (`doc_language="all"`) — nicht auditierbar/getestet.
2. **Prompt-Strings = hartkodierte DE/EN-Dictionaries** in ≥2 Codebasen — jede Sprache = Code-Änderung.
3. **FTS-Stemming** auf 2 Sprachen fest (`LANG_TO_TSCONFIG`), sonst `simple`.
4. **`Literal["de","en","all"]`** in Schemas blockiert N-Sprachen ohne Migration.
5. **Eval nur DE** (100 DE-Fragen, DE-Judge).
6. `language_mismatch_warning` tote Infrastruktur.
7. Plant-Docs **ohne Sprach-Metadatum**.

---

## 5. Betroffene Requirement-Dokumente

Sprachrelevant und von der Zielarchitektur berührt:

| Dokument | Bezug |
|----------|-------|
| **UI-NFR-007** Internationalisierung | Maßgeblich fürs UI-Rendering; N-Sprachen/RTL bisher nur SOLL — NFR-017 unterlegt das architektonisch. |
| **NFR-003** Englischer Source-Code | Source-Language-Scope; NFR-017 §5 präzisiert Laufzeit-Inhalte vs. Code. |
| **NFR-005** Technische Dokumentation | DE-kanonisch/EN-Mirror = Sonderfall der Gesamtstrategie. |
| **NFR-006** API-Fehlerbehandlung | `error_code`-Katalog trägt lokalisierbare nutzerseitige Meldungen. |
| **REQ-001** Stammdatenverwaltung | Lokalisierte Stammdatenfelder (`common_name_*`) → Locale-Map. |
| **REQ-010** IPM-System | Größte Anti-Pattern-Fläche (`ipm.yaml`, 370 nur-DE-Vorkommen). |
| **REQ-035** KI-Fachbegriff-Glossar | Referenz-Zielmuster (Locale-Maps + Resolver). |
| **REQ-031/036** KI-Assistent/Diagnose | `doc_language`/`prompt_language`, DE-Default-Prompts. |
| **REQ-026** Aquaponik | Deutsche nutzerseitige Fehler-Literale → `error_code`. |
| **REQ-039** Klimazonen/Winterhärte | `hardiness_zones.yaml` nur-DE-Felder. |

---

## 6. Zusammenfassung: was skaliert, was nicht

**Skaliert bereits (N-Sprachen-fähig, ausbauen):** react-i18next-Katalog + Plurals; Locale-Maps in
`glossary_terms`/`starter_kits` mit Resolver + `de`-Fallback; multilinguales Embedding-Modell;
Docs-Site DE/EN via static-i18n; `error_code`-Katalog.

**Skaliert NICHT (Anti-Pattern, migrieren):** 784 Seed-Suffix-Vorkommen + 141 Backend-`_de`/`_en`-Felder
+ 246 FE-Feldzugriffe + 6 Schema-Dateien; ~76 binäre FE-Sprach-Zweige + 45 Locale-Literale + dayjs-DE-
Strings; fehlende Server-Locale-Resolution + ungenutztes `user.locale`; deutsche Fehler-Literale;
`Literal["de","en"]`-Constraints; DE-only Wissensbasis + hartkodierte DE/EN-Prompt-Dictionaries;
fehlendes RTL-Fundament.
