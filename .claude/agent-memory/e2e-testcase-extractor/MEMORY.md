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
- Pattern: TC-REQ-{NNN}-{TTT} where NNN=requirement number (001-018), TTT=sequential within doc
- Group by functional area/page within document, not by test type
- Coverage summary table at end maps UI sections to test case ranges

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
- Test case docs: `spec/test-cases/TC-REQ-{NNN}.md`
- YAML frontmatter with req_id, title, category, test_count, coverage_areas, generated date, version
