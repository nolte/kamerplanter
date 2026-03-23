---
name: REQ-007 Harvest Management — UI Patterns and Test Insights
description: Frontend architecture, validation rules, i18n keys and test patterns for Erntemanagement
type: project
---

## REQ-007 Erntemanagement — UI Patterns and Key Test Insights

**Route structure:**
- `/ernte/batches` → `HarvestBatchListPage.tsx`
- `/ernte/batches/:key` → `HarvestBatchDetailPage.tsx`

**HarvestBatchDetailPage: 4 tabs** (useTabUrl, URL-persistent)
- Tab 0: "Details" — read-only Tabelle (batch_id, plant_key, harvest_date, harvest_type, wet_weight_g, estimated_dry_weight_g, actual_dry_weight_g, quality_grade, harvester, notes)
- Tab 1: "Qualität" — entweder Anzeige-Tabelle (wenn quality vorhanden) ODER Erstellungsformular
- Tab 2: "Ertrag" — entweder Anzeige-Tabelle (wenn yieldMetric vorhanden) ODER Erstellungsformular
- Tab 3: "Bearbeiten" — Edit-Formular mit UnsavedChangesGuard (isDirty-based disabled Speichern-Button)

**Quality Grade Chip Colors:**
- a_plus → success (grün), a → success (grün), b → info (blau), c → warning (orange), d → error (rot)

**Quality Score LinearProgress Colors (Tab Qualität Anzeige):**
- overall_score >= 80 → success (grün), >= 60 → warning (orange), < 60 → error (rot)

**HarvestReadinessCard (standalone component, embedded in plant detail contexts):**
- `data-testid="harvest-readiness-card"`
- Recommendation-Chip colors: optimal=success, approaching=warning, developing=info, default=error
- Score colors: >= 80=success, >= 50=warning, < 50=error
- estimated_days is conditionally rendered (null = hidden)
- Indikator-Chips: peak=success, approaching=warning, overripe=error, others=default

**HarvestCreateDialog Zod Schema:**
- plant_key: z.string().min(1) — PFLICHTFELD
- batch_id: z.string().max(100).optional() — optionale manuelle ID
- harvest_type: z.enum(['partial','final','continuous'])
- wet_weight_g: z.number().min(0).nullable() — min=0!
- harvester: z.string().max(200)
- notes: z.string().nullable()

**HarvestBatchDetailPage Edit Schema:**
- wet_weight_g: z.number().min(0).nullable()
- estimated_dry_weight_g: z.number().min(0).nullable()
- actual_dry_weight_g: z.number().min(0).nullable()

**QualityAssessment Schema:**
- assessed_by: z.string().min(1).max(200) — PFLICHTFELD
- appearance_score: z.number().min(0).max(100)
- aroma_score: z.number().min(0).max(100)
- color_score: z.number().min(0).max(100)
- defects: z.array(z.string()) — via FormChipInput (Enter zum Hinzufügen)
- notes: z.string().nullable()

**YieldMetric Schema:**
- yield_per_plant_g: z.number().min(0)
- yield_per_m2_g: z.number().min(0)
- total_yield_g: z.number().min(0)
- trim_waste_percent: z.number().min(0).max(100)
- usable_yield_g: z.number().min(0)
- Backend validation: usable_yield_g <= total_yield_g

**Column hideBelowBreakpoint in HarvestBatchListPage:**
- plantKey: hideBelowBreakpoint='md' (also gilt als Tablet-Spec-Anforderung UI-NFR-010)
- harvestType: hideBelowBreakpoint='md'

**i18n Keys (pages.harvest.*):**
- Success messages: "created"="Erntecharge erfolgreich erstellt.", "qualityCreated"="Qualitätsbewertung erfolgreich erstellt.", "yieldCreated"="Ertragsmetriken erfolgreich erstellt."
- Common.save used for Edit success (not a dedicated harvest.saved key)

**Karenzzeit-Gate (REQ-010 Integration):**
- Backend blocks batch creation when IPM Karenzzeit nicht eingehalten
- UI zeigt Fehlerbenachrichtigung (keine dedizierte Fehlermeldung im Spec — allgemeine Error-Handling via useApiError)
- karenzSafeDate i18n key: "Sicher ab: {{date}}" — sichtbar in IPM context (KarenzStatusCard)

**Enum Translations:**
- harvestType: partial="Teilernte", final="Endernte", continuous="Fortlaufend"
- qualityGrade: a_plus="A+", a="A", b="B", c="C", d="D"
- ripenessStage: immature="Unreif", approaching="Heranreifend", peak="Optimal", overripe="Überreif"
- readinessRecommendation: optimal="Erntebereit", approaching="Bald erntebereit", developing="In Entwicklung", immature="Unreif"

**Output:** 42 test cases in `spec/e2e-testcases/TC-REQ-007.md`

**Why:** REQ-007 v2.3 has complex domain logic (TrichomeIndicator, FlushingProtocol, HarvestWindowPredictor) but the frontend implementation is simpler — 4-tab Detail pattern with 3 sub-entities (Batch, Quality, Yield). Most domain complexity lives in the backend and is not directly UI-testable.

**How to apply:** Use this file when writing or reviewing harvest-related test cases. The 4-tab Detail pattern with conditional create-form vs. read-table is the key UI pattern to test.
