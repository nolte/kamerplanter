---
req_id: REQ-001
title: Stammdatenverwaltung von Pflanzen-Entitaetszyklen
category: Stammdaten
test_count: 95
coverage_areas:
  - BotanicalFamily List Page
  - BotanicalFamily Create Dialog
  - BotanicalFamily Detail Page (Edit/Delete)
  - BotanicalFamily Validation
  - Species List Page
  - Species Create Dialog
  - Species Detail Page (Edit/Delete)
  - Species Detail Page Tabs (Cultivars, Lifecycle)
  - Cultivar List Section
  - Cultivar Create Dialog
  - Cultivar Detail Page (Edit/Delete)
  - Lifecycle Config Section (Create/Edit)
  - Growth Phase Management (Create/Edit/Delete)
  - Growth Phase Profiles (Requirement/Nutrient)
  - Companion Planting Page
  - Crop Rotation Page
  - DataTable Features (Search/Sort/Pagination)
  - Navigation and Routing
  - Unsaved Changes Guard
  - Error Handling and Empty States
generated: 2026-02-27
version: "3.0"
---

# TC-REQ-001: Stammdatenverwaltung (Master Data Management)

This document contains end-to-end test cases derived from **REQ-001 Stammdatenverwaltung von Pflanzen-Entitaetszyklen v3.0**, written exclusively from the perspective of an end user interacting with the application in the browser. No API calls, HTTP status codes, or database queries appear in these test cases. All assertions describe what the user sees, clicks, types, and expects on screen.

The UI language is **German** (default locale). All labels, buttons, and messages reference the exact German i18n translations from `src/frontend/src/i18n/locales/de/translation.json`.

REQ-001 is the **foundation module** upon which REQ-002 through REQ-012 depend.

---

## 1. Navigation and Routing

### TC-REQ-001-001: Navigate to Botanical Families list via sidebar

**Requirement**: REQ-001 -- Navigation (Stammdaten section)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The application is loaded in the browser

**Test Steps**:
1. Click on "Stammdaten" in the sidebar navigation
2. Click on "Botanische Familien" in the expanded submenu

**Expected Results**:
- The browser URL changes to `/stammdaten/botanical-families`
- The page title "Botanische Familien" is displayed
- The introductory text "Botanische Familien gruppieren Pflanzenarten nach Verwandtschaft..." is visible below the title
- A "Familie erstellen" button is visible in the top-right area

**Postconditions**:
- The BotanicalFamilyListPage is rendered

**Tags**: [REQ-001, botanical-family, navigation, happy-path]

---

### TC-REQ-001-002: Navigate to Species list via sidebar

**Requirement**: REQ-001 -- Navigation (Stammdaten section)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The application is loaded in the browser

**Test Steps**:
1. Click on "Stammdaten" in the sidebar navigation
2. Click on "Arten" in the expanded submenu

**Expected Results**:
- The browser URL changes to `/stammdaten/species`
- The page title "Arten" is displayed
- The introductory text "Pflanzenarten bilden die Grundlage der Stammdaten..." is visible
- A "Art erstellen" button is visible in the top-right area

**Postconditions**:
- The SpeciesListPage is rendered

**Tags**: [REQ-001, species, navigation, happy-path]

---

### TC-REQ-001-003: Navigate to Companion Planting page via sidebar

**Requirement**: REQ-001 -- Navigation (Stammdaten section)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- The application is loaded in the browser

**Test Steps**:
1. Click on "Stammdaten" in the sidebar navigation
2. Click on "Mischkultur" in the expanded submenu

**Expected Results**:
- The browser URL changes to `/stammdaten/companion-planting`
- The page title "Mischkultur" is displayed
- A species selection dropdown labeled "Art auswaehlen" is visible

**Postconditions**:
- The CompanionPlantingPage is rendered

**Tags**: [REQ-001, companion-planting, navigation, happy-path]

---

### TC-REQ-001-004: Navigate to Crop Rotation page via sidebar

**Requirement**: REQ-001 -- Navigation (Stammdaten section)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- The application is loaded in the browser

**Test Steps**:
1. Click on "Stammdaten" in the sidebar navigation
2. Click on "Fruchtfolge" in the expanded submenu

**Expected Results**:
- The browser URL changes to `/stammdaten/crop-rotation`
- The page title "Fruchtfolge" is displayed
- A family selection dropdown labeled "Von Familie" is visible

**Postconditions**:
- The CropRotationPage is rendered

**Tags**: [REQ-001, crop-rotation, navigation, happy-path]

---

### TC-REQ-001-005: Direct URL access to non-existent route shows 404 page

**Requirement**: REQ-001 -- Routing
**Priority**: Medium
**Category**: Error Handling
**Preconditions**:
- The application is loaded in the browser

**Test Steps**:
1. Navigate directly to URL `/stammdaten/nonexistent`

**Expected Results**:
- The "Seite nicht gefunden" page is displayed
- The message "Die angeforderte Seite existiert nicht." is shown
- A "Zurueck zum Dashboard" link is available

**Postconditions**:
- The NotFoundPage is rendered

**Tags**: [REQ-001, routing, error-handling]

---

## 2. Botanical Family List Page

### TC-REQ-001-006: Display botanical families in a data table

**Requirement**: REQ-001 -- Section 2 (Nodes: BotanicalFamily)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- At least 3 botanical families exist (e.g., Solanaceae, Fabaceae, Brassicaceae from seed data)

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`

**Expected Results**:
- A data table is displayed with the following column headers:
  - "Name"
  - "Deutscher Name"
  - "Naehrstoffbedarf"
  - "Frosttoleranz"
  - "Wurzeltiefe"
  - "Fruchtfolgekategorie"
- Each family row shows the family name (e.g., "Solanaceae"), German common name (e.g., "Nachtschattengewaechse"), and translated enum values
- The "Naehrstoffbedarf" column shows translated values like "Starkzehrer", "Mittelzehrer", or "Schwachzehrer"
- The "Frosttoleranz" column shows translated values like "Empfindlich", "Moderat", "Hardy", or "Sehr hardy"
- The "Wurzeltiefe" column shows translated values like "Flach", "Mittel", or "Tief"
- The table is sorted by "Name" ascending by default

**Postconditions**:
- All families are visible in the table

**Tags**: [REQ-001, botanical-family, list, data-table, happy-path]

---

### TC-REQ-001-007: Search botanical families by name in the data table

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- At least 5 botanical families exist (seed data: 9 families)

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`
2. Type "Solan" into the search field (placeholder: "Tabelle durchsuchen...")
3. Wait for the debounce (300ms)

**Expected Results**:
- Only rows matching "Solan" are displayed (e.g., "Solanaceae")
- A search chip "Suchen: "Solan"" appears in the toolbar
- The showing count updates to reflect the filtered number (e.g., "Zeigt 1-1 von 1 Eintraegen")

**Postconditions**:
- The table is filtered by the search term

**Tags**: [REQ-001, botanical-family, search, data-table]

---

### TC-REQ-001-008: Search botanical families by translated enum value

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Seed data families exist, including "Starkzehrer" families (Solanaceae, Brassicaceae, Cucurbitaceae, Cannabaceae)

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`
2. Type "Starkzehrer" into the search field

**Expected Results**:
- Only families with `typical_nutrient_demand = "heavy"` are shown
- The search matches the translated German enum value, not the raw enum key

**Postconditions**:
- Table is filtered to show heavy feeders only

**Tags**: [REQ-001, botanical-family, search, enum-translation, data-table]

---

### TC-REQ-001-009: Sort botanical families by column

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- At least 3 botanical families exist

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`
2. Click the "Naehrstoffbedarf" column header

**Expected Results**:
- The table is sorted by nutrient demand (ascending)
- A sort chip "Sortiert nach: Naehrstoffbedarf" appears in the toolbar
- Clicking the same column header again reverses the sort direction (descending)

**Postconditions**:
- The table sort state is updated

**Tags**: [REQ-001, botanical-family, sort, data-table]

---

### TC-REQ-001-010: Reset all filters in botanical families table

**Requirement**: REQ-001 -- DataTable features
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- The table has an active search filter and/or sort applied

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`
2. Type "Fabaceae" into the search field
3. Click the "Alle Filter zuruecksetzen" button

**Expected Results**:
- The search field is cleared
- The search chip disappears
- All families are displayed again
- The sort returns to the default (Name ascending)

**Postconditions**:
- Table state is reset to defaults

**Tags**: [REQ-001, botanical-family, reset-filters, data-table]

---

### TC-REQ-001-011: Click on a botanical family row navigates to detail page

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- At least one botanical family exists (e.g., "Solanaceae")

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`
2. Click on the row for "Solanaceae"

**Expected Results**:
- The browser URL changes to `/stammdaten/botanical-families/{key}` (where `{key}` is the family's key)
- The BotanicalFamilyDetailPage is displayed
- The page title shows "Solanaceae"

**Postconditions**:
- The detail page for the selected family is rendered

**Tags**: [REQ-001, botanical-family, navigation, row-click, happy-path]

---

### TC-REQ-001-012: Empty state when no botanical families exist

**Requirement**: REQ-001 -- DataTable features
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- No botanical families exist in the system

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`

**Expected Results**:
- Instead of a data table, an empty state component is displayed
- The empty state includes a "Familie erstellen" action button
- Clicking the action button opens the create dialog

**Postconditions**:
- The empty state is shown with an actionable CTA

**Tags**: [REQ-001, botanical-family, empty-state, edge-case]

---

## 3. Botanical Family Create Dialog

### TC-REQ-001-013: Open the create dialog

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The user is on `/stammdaten/botanical-families`

**Test Steps**:
1. Click the "Familie erstellen" button

**Expected Results**:
- A dialog opens with the title "Familie erstellen"
- The introductory text "Legen Sie eine neue Botanische Familie an..." is displayed
- The form contains the following fields with their labels:
  - "Name" (text field, required, helper: "Botanischer Familienname, muss auf '-aceae' enden...")
  - "Deutscher Name" (text field)
  - "Englischer Name" (text field)
  - "Ordnung" (text field, helper: "Taxonomische Ordnung, muss auf '-ales' enden wenn angegeben...")
  - "Beschreibung" (multiline text field)
  - "Naehrstoffbedarf" (select: Schwachzehrer/Mittelzehrer/Starkzehrer)
  - "Stickstofffixierend" (switch toggle)
  - "Wurzeltiefe" (select: Flach/Mittel/Tief)
  - "pH-Minimum" (number field, 3-9, step 0.1)
  - "pH-Maximum" (number field, 3-9, step 0.1)
  - "Frosttoleranz" (select: Empfindlich/Moderat/Hardy/Sehr hardy)
  - "Wuchsformen" (multi-select, required: Kraut/Strauch/Baum/Ranke/Bodendecker)
  - "Haeufige Schaedlinge" (chip input)
  - "Haeufige Krankheiten" (chip input)
  - "Bestaeubungstypen" (multi-select, required: Insektenbestaeubung/Windbestaeubung/Selbstbestaeubung)
  - "Fruchtfolgekategorie" (text field)
- The default values are: Naehrstoffbedarf = "Mittelzehrer", Wurzeltiefe = "Mittel", Frosttoleranz = "Moderat", Wuchsformen = ["Kraut"], Bestaeubungstypen = ["Insektenbestaeubung"]
- An "Erstellen" button and an "Abbrechen" button are visible

**Postconditions**:
- The create dialog is open and ready for input

**Tags**: [REQ-001, botanical-family, create, dialog, form-layout, happy-path]

---

### TC-REQ-001-014: Successfully create a botanical family with all fields

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily), Section 3 (BotanicalFamily-Validator)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Enter "Rosaceae" in the "Name" field
2. Enter "Rosengewaechse" in the "Deutscher Name" field
3. Enter "Rose family" in the "Englischer Name" field
4. Enter "Rosales" in the "Ordnung" field
5. Enter "Obst- und Ziergehoelze" in the "Beschreibung" field
6. Select "Mittelzehrer" for "Naehrstoffbedarf"
7. Leave "Stickstofffixierend" switch off
8. Select "Mittel" for "Wurzeltiefe"
9. Enter "5.5" for "pH-Minimum"
10. Enter "7.0" for "pH-Maximum"
11. Select "Hardy" for "Frosttoleranz"
12. Select "Strauch" and "Baum" for "Wuchsformen"
13. Add "Blattlaeuse" and "Apfelwickler" as chips in "Haeufige Schaedlinge"
14. Add "Mehltau" and "Sternrusstau" as chips in "Haeufige Krankheiten"
15. Select "Insektenbestaeubung" for "Bestaeubungstypen"
16. Enter "rosaceae" for "Fruchtfolgekategorie"
17. Click the "Erstellen" button

**Expected Results**:
- A success notification is displayed
- The dialog closes
- The family list table reloads and now includes "Rosaceae" as a row
- The new row shows "Rosengewaechse" in the "Deutscher Name" column and "Mittelzehrer" in the "Naehrstoffbedarf" column

**Postconditions**:
- "Rosaceae" exists as a botanical family in the system
- The create dialog form is reset to defaults

**Tags**: [REQ-001, botanical-family, create, happy-path, validation]

---

### TC-REQ-001-015: Validation error -- family name does not end with "-aceae"

**Requirement**: REQ-001 -- Section 3 (BotanicalFamily-Validator: `validate_family_name`)
**Priority**: Critical
**Category**: Error Handling
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Enter "Solanidae" in the "Name" field
2. Fill in required fields (select at least one Wuchsform, one Bestaeubungstyp)
3. Click the "Erstellen" button

**Expected Results**:
- The form does NOT submit
- An inline validation error appears below the "Name" field: "Muss auf '-aceae' enden"
- The dialog remains open

**Postconditions**:
- No family is created

**Tags**: [REQ-001, botanical-family, create, validation, error-handling, naming-convention]

---

### TC-REQ-001-016: Validation error -- empty name field

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily: name required)
**Priority**: Critical
**Category**: Error Handling
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Leave the "Name" field empty
2. Fill in other required fields
3. Click the "Erstellen" button

**Expected Results**:
- The form does NOT submit
- An inline validation error appears below the "Name" field indicating it is required
- The dialog remains open

**Postconditions**:
- No family is created

**Tags**: [REQ-001, botanical-family, create, validation, error-handling, required-field]

---

### TC-REQ-001-017: Validation error -- no growth form selected

**Requirement**: REQ-001 -- Section 3 (BotanicalFamily-Validator: `typical_growth_forms min_items=1`)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Enter "Testaceae" in the "Name" field
2. Deselect all options in the "Wuchsformen" multi-select (removing the default "Kraut")
3. Click the "Erstellen" button

**Expected Results**:
- The form does NOT submit
- A validation error is displayed indicating at least one growth form must be selected
- The dialog remains open

**Postconditions**:
- No family is created

**Tags**: [REQ-001, botanical-family, create, validation, error-handling, multi-select]

---

### TC-REQ-001-018: Validation error -- no pollination type selected

**Requirement**: REQ-001 -- Section 3 (BotanicalFamily-Validator: `pollination_type min_items=1`)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Enter "Testaceae" in the "Name" field
2. Deselect all options in the "Bestaeubungstypen" multi-select (removing the default "Insektenbestaeubung")
3. Click the "Erstellen" button

**Expected Results**:
- The form does NOT submit
- A validation error is displayed indicating at least one pollination type must be selected
- The dialog remains open

**Postconditions**:
- No family is created

**Tags**: [REQ-001, botanical-family, create, validation, error-handling, multi-select]

---

### TC-REQ-001-019: Backend validation -- nitrogen_fixing=true with heavy nutrient demand is rejected

**Requirement**: REQ-001 -- Section 3 (BotanicalFamily-Validator: `validate_nitrogen_fixing_demand`)
**Priority**: Critical
**Category**: Error Handling
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Enter "Testaceae" in the "Name" field
2. Select "Starkzehrer" for "Naehrstoffbedarf"
3. Toggle "Stickstofffixierend" switch to ON
4. Fill in remaining required fields
5. Click the "Erstellen" button

**Expected Results**:
- The submission fails
- An error notification is displayed to the user (backend validation: nitrogen_fixing=true is incompatible with heavy nutrient demand)
- The dialog remains open so the user can correct the input

**Postconditions**:
- No family is created

**Tags**: [REQ-001, botanical-family, create, validation, error-handling, nitrogen-fixing, business-rule]

---

### TC-REQ-001-020: Create a family with minimal fields (only required fields)

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Enter "Minimalaceae" in the "Name" field
2. Leave all optional fields at their defaults (Deutscher Name empty, Englischer Name empty, Ordnung empty, etc.)
3. Keep the default Wuchsform ("Kraut") and Bestaeubungstyp ("Insektenbestaeubung")
4. Click the "Erstellen" button

**Expected Results**:
- A success notification is displayed
- The dialog closes
- "Minimalaceae" appears in the family list

**Postconditions**:
- A family with minimal data exists in the system

**Tags**: [REQ-001, botanical-family, create, minimal-data, happy-path]

---

### TC-REQ-001-021: Cancel the create dialog discards unsaved input

**Requirement**: REQ-001 -- Dialog behavior
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Enter "Discardaceae" in the "Name" field
2. Click the "Abbrechen" button

**Expected Results**:
- The dialog closes
- No family is created
- Re-opening the dialog shows an empty "Name" field (form is reset)

**Postconditions**:
- No data was persisted

**Tags**: [REQ-001, botanical-family, create, cancel, dialog]

---

### TC-REQ-001-022: pH range boundary values (min=3.0, max=9.0)

**Requirement**: REQ-001 -- Section 3 (PhRange: min_ph >= 3.0, max_ph <= 9.0)
**Priority**: High
**Category**: Edge Case
**Preconditions**:
- The user has opened the create dialog on `/stammdaten/botanical-families`

**Test Steps**:
1. Enter "Boundaryaceae" in the "Name" field
2. Enter "3.0" for "pH-Minimum"
3. Enter "9.0" for "pH-Maximum"
4. Fill in remaining required fields
5. Click the "Erstellen" button

**Expected Results**:
- The form submits successfully
- A success notification is displayed

**Postconditions**:
- The family is created with the boundary pH range

**Tags**: [REQ-001, botanical-family, create, boundary-value, ph-range]

---

## 4. Botanical Family Detail Page

### TC-REQ-001-023: Display botanical family detail page with populated form

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- "Solanaceae" exists with full seed data (common_name_de: "Nachtschattengewaechse", order: "Solanales", typical_nutrient_demand: "heavy", etc.)

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families/{solanaceae_key}`

**Expected Results**:
- The page title shows "Solanaceae"
- The introductory text "Bearbeiten Sie die Eigenschaften dieser Botanischen Familie..." is displayed
- All form fields are pre-populated with the existing data:
  - Name: "Solanaceae"
  - Deutscher Name: "Nachtschattengewaechse"
  - Englischer Name: "Nightshade family"
  - Ordnung: "Solanales"
  - Naehrstoffbedarf: "Starkzehrer"
  - Stickstofffixierend: OFF
  - Wurzeltiefe: "Mittel"
  - Frosttoleranz: "Empfindlich"
- A red "Loeschen" button with a delete icon is visible in the top-right area

**Postconditions**:
- The detail page is displayed with current data

**Tags**: [REQ-001, botanical-family, detail, form-population, happy-path]

---

### TC-REQ-001-024: Edit a botanical family and save changes

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The user is on the detail page for "Solanaceae"

**Test Steps**:
1. Change the "Beschreibung" field to "Nachtschattengewaechse umfassen Tomate, Paprika und Kartoffel."
2. Add "Kartoffelkaefer" as a chip in "Haeufige Schaedlinge"
3. Click the "Speichern" button

**Expected Results**:
- A success notification is displayed
- The page remains on the detail view
- The form now shows the updated description and the newly added pest

**Postconditions**:
- The botanical family data is updated in the system

**Tags**: [REQ-001, botanical-family, edit, save, happy-path]

---

### TC-REQ-001-025: Unsaved changes guard warns before navigating away

**Requirement**: REQ-001 -- UnsavedChangesGuard component
**Priority**: High
**Category**: Edge Case
**Preconditions**:
- The user is on the detail page for "Solanaceae"

**Test Steps**:
1. Change the "Beschreibung" field to "Modified text"
2. Attempt to navigate away by clicking "Botanische Familien" in the sidebar

**Expected Results**:
- A browser confirmation dialog appears with the message "Sie haben ungespeicherte Aenderungen. Moechten Sie die Seite wirklich verlassen?"
- If the user clicks "Cancel" (stay), the detail page remains visible with the modified text
- If the user clicks "OK" (leave), the browser navigates to the families list and changes are lost

**Postconditions**:
- The guard prevents accidental data loss

**Tags**: [REQ-001, botanical-family, edit, unsaved-changes, navigation-guard]

---

### TC-REQ-001-026: Delete a botanical family via confirmation dialog

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- A botanical family "Deletaceae" exists
- The user is on the detail page for "Deletaceae"

**Test Steps**:
1. Click the red "Loeschen" button
2. A confirmation dialog appears with: "Sind Sie sicher, dass Sie "Deletaceae" loeschen moechten? Diese Aktion kann nicht rueckgaengig gemacht werden."
3. Click "Bestaetigen" in the confirmation dialog

**Expected Results**:
- A success notification for deletion is displayed
- The user is redirected to `/stammdaten/botanical-families` (the list page)
- "Deletaceae" no longer appears in the family list

**Postconditions**:
- The family is deleted from the system

**Tags**: [REQ-001, botanical-family, delete, confirmation-dialog, happy-path]

---

### TC-REQ-001-027: Cancel deletion keeps the family

**Requirement**: REQ-001 -- Delete confirmation
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- The user is on the detail page for a botanical family
- The delete confirmation dialog is open

**Test Steps**:
1. Click "Abbrechen" in the confirmation dialog

**Expected Results**:
- The confirmation dialog closes
- The detail page remains displayed with all data intact
- The family is NOT deleted

**Postconditions**:
- No data is modified

**Tags**: [REQ-001, botanical-family, delete, cancel, confirmation-dialog]

---

### TC-REQ-001-028: Detail page shows error display for non-existent key

**Requirement**: REQ-001 -- Error handling
**Priority**: Medium
**Category**: Error Handling
**Preconditions**:
- No botanical family exists with key "nonexistent123"

**Test Steps**:
1. Navigate directly to `/stammdaten/botanical-families/nonexistent123`

**Expected Results**:
- An error display component is shown (not a blank page)
- A retry/back button is available

**Postconditions**:
- The user can navigate back

**Tags**: [REQ-001, botanical-family, detail, error-handling, not-found]

---

## 5. Species List Page

### TC-REQ-001-029: Display species in a paginated data table

**Requirement**: REQ-001 -- Section 2 (Nodes: Species)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- At least 3 species exist (e.g., Solanum lycopersicum, Ocimum basilicum, Cannabis sativa)

**Test Steps**:
1. Navigate to `/stammdaten/species`

**Expected Results**:
- A data table is displayed with column headers:
  - "Wissenschaftlicher Name"
  - "Gebraeuchliche Namen"
  - "Gattung"
  - "Wuchsform"
  - "Wurzeltyp"
- Each row shows the species' scientific name, comma-separated common names, genus, translated growth habit (e.g., "Kraut"), and translated root type (e.g., "Faserig")
- Pagination controls are visible at the bottom (server-side pagination)
- The default page size options include 10, 25, 50, 100

**Postconditions**:
- The species list is displayed with pagination

**Tags**: [REQ-001, species, list, data-table, pagination, happy-path]

---

### TC-REQ-001-030: Paginate through species list

**Requirement**: REQ-001 -- Section 2 (Species)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- More than 10 species exist in the system
- The user is on `/stammdaten/species` with rowsPerPage set to 10

**Test Steps**:
1. Click the "next page" button in the pagination controls

**Expected Results**:
- The table shows the next set of species (rows 11-20)
- The pagination indicator updates (e.g., page 2 of N)

**Postconditions**:
- The user is viewing the second page of species

**Tags**: [REQ-001, species, list, pagination, happy-path]

---

### TC-REQ-001-031: Click on a species row navigates to detail page

**Requirement**: REQ-001 -- Section 2 (Species)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- At least one species exists (e.g., "Solanum lycopersicum")

**Test Steps**:
1. Navigate to `/stammdaten/species`
2. Click on the row for "Solanum lycopersicum"

**Expected Results**:
- The browser URL changes to `/stammdaten/species/{key}`
- The SpeciesDetailPage is displayed
- The page title shows "Solanum lycopersicum"

**Postconditions**:
- The species detail page is rendered

**Tags**: [REQ-001, species, navigation, row-click, happy-path]

---

### TC-REQ-001-032: Empty state when no species exist

**Requirement**: REQ-001 -- DataTable empty state
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- No species exist in the system

**Test Steps**:
1. Navigate to `/stammdaten/species`

**Expected Results**:
- An empty state is displayed instead of the table
- A "Art erstellen" action button is available
- Clicking it opens the SpeciesCreateDialog

**Postconditions**:
- The user can create a species from the empty state

**Tags**: [REQ-001, species, empty-state, edge-case]

---

## 6. Species Create Dialog

### TC-REQ-001-033: Open the species create dialog and verify form fields

**Requirement**: REQ-001 -- Section 2 (Species), Section 3 (Species-Validator)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The user is on `/stammdaten/species`
- At least one botanical family exists (for the family dropdown)

**Test Steps**:
1. Click the "Art erstellen" button

**Expected Results**:
- A dialog opens with the title "Art erstellen"
- The introductory text "Legen Sie eine neue Pflanzenart an..." is displayed
- The form contains fields with labels:
  - "Wissenschaftlicher Name" (required, helper: "Binomiale Nomenklatur...")
  - "Gebraeuchliche Namen" (chip input)
  - "Familie" (select dropdown populated with existing families + "-" option)
  - "Gattung" (text field)
  - "Beschreibung" (multiline)
  - "Wuchsform" (select: Kraut/Strauch/Baum/Ranke/Bodendecker)
  - "Wurzeltyp" (select: Faserig/Pfahlwurzel/Knollig/Zwiebel)
  - "Winterhaertezonen" (chip input)
  - "Natuerlicher Lebensraum" (text field)
  - "Allelopathie-Wert" (number, -1 to 1, step 0.1)
  - "Basistemperatur" (number)
  - "Synonyme" (chip input)
  - "Taxonomische Autoritaet" (text field)
  - "Taxonomischer Status" (text field)
- Default values: Wuchsform = "Kraut", Wurzeltyp = "Faserig", Allelopathie-Wert = 0, Basistemperatur = 10

**Postconditions**:
- The create dialog is open and ready for input

**Tags**: [REQ-001, species, create, dialog, form-layout, happy-path]

---

### TC-REQ-001-034: Successfully create a species with valid data

**Requirement**: REQ-001 -- Section 2 (Species), Section 3 (Species-Validator)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The species create dialog is open
- "Solanaceae" exists as a botanical family

**Test Steps**:
1. Enter "Solanum lycopersicum" in "Wissenschaftlicher Name"
2. Add "Tomate" and "Tomato" as chips in "Gebraeuchliche Namen"
3. Select "Solanaceae" in the "Familie" dropdown
4. Enter "Solanum" in "Gattung"
5. Select "Kraut" for "Wuchsform"
6. Select "Faserig" for "Wurzeltyp"
7. Add "7a" and "8b" as chips in "Winterhaertezonen"
8. Enter "Suedamerika, Anden" in "Natuerlicher Lebensraum"
9. Set "Allelopathie-Wert" to "0"
10. Set "Basistemperatur" to "10"
11. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The dialog closes
- The species list reloads and now includes "Solanum lycopersicum"
- The row shows "Tomate, Tomato" in the "Gebraeuchliche Namen" column

**Postconditions**:
- The species exists in the system with a `belongs_to_family` edge to Solanaceae

**Tags**: [REQ-001, species, create, happy-path, family-linkage]

---

### TC-REQ-001-035: Validation error -- empty scientific name

**Requirement**: REQ-001 -- Section 3 (Species-Validator: scientific_name required)
**Priority**: Critical
**Category**: Error Handling
**Preconditions**:
- The species create dialog is open

**Test Steps**:
1. Leave "Wissenschaftlicher Name" empty
2. Click "Erstellen"

**Expected Results**:
- The form does NOT submit
- An inline validation error appears below "Wissenschaftlicher Name"
- The dialog remains open

**Postconditions**:
- No species is created

**Tags**: [REQ-001, species, create, validation, error-handling, required-field]

---

### TC-REQ-001-036: Allelopathy score boundary values

**Requirement**: REQ-001 -- Section 2 (Species: allelopathy_score -1.0 to 1.0)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- The species create dialog is open

**Test Steps**:
1. Enter "Boundary testii" in "Wissenschaftlicher Name"
2. Set "Allelopathie-Wert" to "-1"
3. Fill in other fields
4. Click "Erstellen"

**Expected Results**:
- The form submits successfully
- The species is created with allelopathy_score = -1.0

**Postconditions**:
- Species exists with minimum allelopathy score

**Tags**: [REQ-001, species, create, boundary-value, allelopathy]

---

### TC-REQ-001-037: Create species without selecting a family (family_key = null)

**Requirement**: REQ-001 -- Section 2 (Species: family is optional via family_key)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- The species create dialog is open

**Test Steps**:
1. Enter "Orphana speciesii" in "Wissenschaftlicher Name"
2. Leave the "Familie" dropdown at the default "-" (empty) option
3. Fill in other fields
4. Click "Erstellen"

**Expected Results**:
- The form submits successfully
- The species is created without a family association

**Postconditions**:
- Species exists without a `belongs_to_family` edge

**Tags**: [REQ-001, species, create, no-family, edge-case]

---

## 7. Species Detail Page

### TC-REQ-001-038: Display species detail page with three tabs

**Requirement**: REQ-001 -- Section 2 (Species + Cultivar + LifecycleConfig)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- "Solanum lycopersicum" exists with family linkage to "Solanaceae"

**Test Steps**:
1. Navigate to `/stammdaten/species/{key}`

**Expected Results**:
- The page title shows "Solanum lycopersicum"
- Three tabs are displayed: "Bearbeiten", "Sorten", "Lebenszyklus-Konfiguration"
- The first tab ("Bearbeiten") is active by default
- The edit form is populated with the species data
- A red "Loeschen" button is visible in the header

**Postconditions**:
- The species detail page with tabs is rendered

**Tags**: [REQ-001, species, detail, tabs, happy-path]

---

### TC-REQ-001-039: Edit species data on the "Bearbeiten" tab

**Requirement**: REQ-001 -- Section 2 (Species)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The user is on the "Bearbeiten" tab of a species detail page

**Test Steps**:
1. Add "Paradeiser" as a chip in "Gebraeuchliche Namen"
2. Change "Wurzeltyp" to "Pfahlwurzel"
3. Click "Speichern"

**Expected Results**:
- A success notification is displayed
- The page reloads with the updated data
- "Paradeiser" is now shown as a chip in "Gebraeuchliche Namen"
- "Pfahlwurzel" is selected in the "Wurzeltyp" dropdown

**Postconditions**:
- The species data is updated

**Tags**: [REQ-001, species, edit, save, happy-path]

---

### TC-REQ-001-040: Delete a species with confirmation

**Requirement**: REQ-001 -- Section 2 (Species)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- A test species "Deletus testii" exists
- The user is on its detail page

**Test Steps**:
1. Click the red "Loeschen" button
2. The confirmation dialog shows: "Sind Sie sicher, dass Sie "Deletus testii" loeschen moechten?..."
3. Click "Bestaetigen"

**Expected Results**:
- A success notification is displayed
- The user is redirected to `/stammdaten/species`
- "Deletus testii" no longer appears in the species list

**Postconditions**:
- The species is deleted

**Tags**: [REQ-001, species, delete, confirmation-dialog, happy-path]

---

### TC-REQ-001-041: Unsaved changes guard on species detail page

**Requirement**: REQ-001 -- UnsavedChangesGuard
**Priority**: High
**Category**: Edge Case
**Preconditions**:
- The user is on the "Bearbeiten" tab of a species detail page

**Test Steps**:
1. Modify the "Natuerlicher Lebensraum" field
2. Attempt to navigate away

**Expected Results**:
- A browser confirmation dialog warns about unsaved changes

**Postconditions**:
- Navigation is blocked until user confirms

**Tags**: [REQ-001, species, edit, unsaved-changes, navigation-guard]

---

## 8. Cultivar List Section (Species Detail Tab 2)

### TC-REQ-001-042: Display cultivars tab for a species

**Requirement**: REQ-001 -- Section 2 (Edges: has_cultivar)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- "Solanum lycopersicum" exists
- At least 2 cultivars exist for this species (e.g., "San Marzano", "Cherry Belle")

**Test Steps**:
1. Navigate to the species detail page for "Solanum lycopersicum"
2. Click the "Sorten" tab

**Expected Results**:
- A section titled "Sorten" is displayed
- A "Sorte erstellen" button is visible
- A data table shows cultivars with columns:
  - "Name"
  - "Zuechter"
  - "Eigenschaften" (rendered as chips with translated trait names)
  - "Tage bis Reife"
  - "Aktionen" (delete button per row)
- The table is sorted by "Name" ascending by default

**Postconditions**:
- The cultivar list section is rendered

**Tags**: [REQ-001, cultivar, list, species-detail, tab, happy-path]

---

### TC-REQ-001-043: Click on a cultivar row navigates to cultivar detail page

**Requirement**: REQ-001 -- Section 2 (Cultivar)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- "San Marzano" cultivar exists under "Solanum lycopersicum"

**Test Steps**:
1. On the "Sorten" tab, click the "San Marzano" row

**Expected Results**:
- The browser URL changes to `/stammdaten/species/{speciesKey}/cultivars/{cultivarKey}`
- The CultivarDetailPage is displayed
- The page title shows "San Marzano"

**Postconditions**:
- The cultivar detail page is rendered

**Tags**: [REQ-001, cultivar, navigation, row-click, happy-path]

---

### TC-REQ-001-044: Delete a cultivar from the list section via inline button

**Requirement**: REQ-001 -- Section 2 (Cultivar)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- "TestCultivar" exists under a species
- The user is on the "Sorten" tab

**Test Steps**:
1. Click the delete icon button on the "TestCultivar" row
2. A confirmation dialog appears: "Sind Sie sicher, dass Sie "TestCultivar" loeschen moechten?..."
3. Click "Bestaetigen"

**Expected Results**:
- A success notification is displayed
- The cultivar list reloads
- "TestCultivar" is no longer shown

**Postconditions**:
- The cultivar is deleted

**Tags**: [REQ-001, cultivar, delete, inline-action, confirmation-dialog, happy-path]

---

## 9. Cultivar Create Dialog

### TC-REQ-001-045: Create a cultivar with all fields

**Requirement**: REQ-001 -- Section 2 (Cultivar), Section 3 (CultivarDefinition)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The user is on the "Sorten" tab of a species detail page
- The cultivar create dialog is open (clicked "Sorte erstellen")

**Test Steps**:
1. Enter "San Marzano" in the "Name" field
2. Enter "Italian Heritage" in the "Zuechter" field
3. Enter "1950" in the "Zuchtjahr" field
4. Add "high_yield" and "disease_resistant" as chips in "Eigenschaften"
5. Enter "PVP" in "Patentstatus"
6. Enter "80" for "Tage bis Reife"
7. Add "Fusarium" as a chip in "Krankheitsresistenzen"
8. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The dialog closes
- "San Marzano" appears in the cultivar list
- The row shows "Italian Heritage" as the breeder
- The traits column shows chips: "Ertragreich" and "Krankheitsresistent" (translated from high_yield, disease_resistant)
- The maturity column shows "80"

**Postconditions**:
- The cultivar is created and linked to the species via `has_cultivar` edge

**Tags**: [REQ-001, cultivar, create, happy-path, traits]

---

### TC-REQ-001-046: Validation error -- empty cultivar name

**Requirement**: REQ-001 -- Section 3 (CultivarDefinition: name required)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- The cultivar create dialog is open

**Test Steps**:
1. Leave the "Name" field empty
2. Click "Erstellen"

**Expected Results**:
- The form does NOT submit
- An inline validation error appears below "Name"

**Postconditions**:
- No cultivar is created

**Tags**: [REQ-001, cultivar, create, validation, error-handling, required-field]

---

### TC-REQ-001-047: Days to maturity boundary values (1-365)

**Requirement**: REQ-001 -- Section 3 (CultivarDefinition: days_to_maturity ge=1, le=365)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- The cultivar create dialog is open

**Test Steps**:
1. Enter "Boundary Cultivar" in the "Name" field
2. Enter "1" for "Tage bis Reife"
3. Click "Erstellen"

**Expected Results**:
- The form submits successfully (1 is the minimum valid value)

**Postconditions**:
- The cultivar is created with days_to_maturity = 1

**Tags**: [REQ-001, cultivar, create, boundary-value, days-to-maturity]

---

## 10. Cultivar Detail Page

### TC-REQ-001-048: Display and edit cultivar detail page

**Requirement**: REQ-001 -- Section 2 (Cultivar)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- "San Marzano" cultivar exists under "Solanum lycopersicum"

**Test Steps**:
1. Navigate to `/stammdaten/species/{speciesKey}/cultivars/{cultivarKey}`

**Expected Results**:
- The page title shows "San Marzano"
- The introductory text "Bearbeiten Sie die Eigenschaften dieser Sorte..." is displayed
- The form shows populated fields: Name, Zuechter, Zuchtjahr, Eigenschaften, Patentstatus, Tage bis Reife, Krankheitsresistenzen
- A red "Loeschen" button is visible

**Postconditions**:
- The cultivar detail page is rendered

**Tags**: [REQ-001, cultivar, detail, happy-path]

---

### TC-REQ-001-049: Edit cultivar and save

**Requirement**: REQ-001 -- Section 2 (Cultivar)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- The user is on a cultivar detail page

**Test Steps**:
1. Change "Zuchtjahr" to "1960"
2. Add "compact" as a chip in "Eigenschaften"
3. Click "Speichern"

**Expected Results**:
- A success notification is displayed
- The form reloads with updated data
- The breeding year shows "1960"

**Postconditions**:
- The cultivar is updated

**Tags**: [REQ-001, cultivar, edit, save, happy-path]

---

### TC-REQ-001-050: Delete cultivar and redirect to species page

**Requirement**: REQ-001 -- Section 2 (Cultivar)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- The user is on the detail page for cultivar "DeleteMe"

**Test Steps**:
1. Click "Loeschen"
2. Confirm in the dialog

**Expected Results**:
- A success notification is displayed
- The user is redirected to `/stammdaten/species/{speciesKey}` (the parent species page)

**Postconditions**:
- The cultivar is deleted

**Tags**: [REQ-001, cultivar, delete, redirect, happy-path]

---

## 11. Lifecycle Config Section (Species Detail Tab 3)

### TC-REQ-001-051: Display lifecycle config tab with no existing config

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- A species exists without a lifecycle config

**Test Steps**:
1. Navigate to the species detail page
2. Click the "Lebenszyklus-Konfiguration" tab

**Expected Results**:
- A section titled "Lebenszyklus-Konfiguration" is displayed
- The form shows fields:
  - "Zyklustyp" (select: Einjaehrig/Zweijaehrig/Mehrjaehrig)
  - "Lebensdauer (Jahre)" (number)
  - "Photoperioden-Typ" (select: Kurztagpflanze/Langtagpflanze/Tagneutral)
  - "Kritische Tageslaenge (h)" (number, 0-24, step 0.5)
  - "Winterruhe erforderlich" (switch)
  - "Vernalisation erforderlich" (switch)
  - "Vernalisation (Tage)" (number)
- The save button label shows "Erstellen" (since no config exists yet)
- Default values: Zyklustyp = "Einjaehrig", Photoperioden-Typ = "Tagneutral"
- No growth phases section is shown (lifecycle must be created first)

**Postconditions**:
- The lifecycle config form is ready for creation

**Tags**: [REQ-001, lifecycle-config, create, no-existing, tab, happy-path]

---

### TC-REQ-001-052: Create a lifecycle config for an annual species

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig), Section 3 (Species lifecycle_type)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The user is on the "Lebenszyklus-Konfiguration" tab for a species without a config

**Test Steps**:
1. Select "Einjaehrig" for "Zyklustyp"
2. Select "Tagneutral" for "Photoperioden-Typ"
3. Leave "Winterruhe erforderlich" OFF
4. Leave "Vernalisation erforderlich" OFF
5. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The button label changes from "Erstellen" to "Speichern"
- The growth phases section appears below the lifecycle config form (ready to add phases)

**Postconditions**:
- A LifecycleConfig with cycle_type = "annual" is created and linked to the species

**Tags**: [REQ-001, lifecycle-config, create, annual, happy-path]

---

### TC-REQ-001-053: Create a lifecycle config for a short-day perennial with dormancy

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig), Spec Scenario 4 (Photoperiod-Bluete)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- The user is on the "Lebenszyklus-Konfiguration" tab for a species without a config

**Test Steps**:
1. Select "Mehrjaehrig" for "Zyklustyp"
2. Enter "5" for "Lebensdauer (Jahre)"
3. Select "Kurztagpflanze" for "Photoperioden-Typ"
4. Enter "14" for "Kritische Tageslaenge (h)"
5. Toggle "Winterruhe erforderlich" ON
6. Leave "Vernalisation erforderlich" OFF
7. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The lifecycle config is saved with dormancy_required = true
- The growth phases section appears below

**Postconditions**:
- A LifecycleConfig with cycle_type = "perennial", photoperiod_type = "short_day", critical_day_length_hours = 14, dormancy_required = true is created

**Tags**: [REQ-001, lifecycle-config, create, perennial, short-day, dormancy, happy-path]

---

### TC-REQ-001-054: Create a lifecycle config for a biennial with vernalization

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig), Section 3 (Species-Validator: biennial must have vernalization), Spec Scenario 2
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- The user is on the "Lebenszyklus-Konfiguration" tab for a species

**Test Steps**:
1. Select "Zweijaehrig" for "Zyklustyp"
2. Select "Langtagpflanze" for "Photoperioden-Typ"
3. Toggle "Vernalisation erforderlich" ON
4. Enter "45" for "Vernalisation (Tage)"
5. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The lifecycle config is saved

**Postconditions**:
- A LifecycleConfig with cycle_type = "biennial", vernalization_required = true, vernalization_min_days = 45 is created

**Tags**: [REQ-001, lifecycle-config, create, biennial, vernalization, happy-path]

---

### TC-REQ-001-055: Edit an existing lifecycle config

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- A lifecycle config already exists for the current species
- The user is on the "Lebenszyklus-Konfiguration" tab

**Test Steps**:
1. Change "Photoperioden-Typ" from "Tagneutral" to "Kurztagpflanze"
2. Enter "12" for "Kritische Tageslaenge (h)"
3. Click "Speichern"

**Expected Results**:
- A success notification is displayed
- The form retains the updated values

**Postconditions**:
- The lifecycle config is updated

**Tags**: [REQ-001, lifecycle-config, edit, save, happy-path]

---

## 12. Growth Phase Management

### TC-REQ-001-056: Growth phases section appears after lifecycle config creation

**Requirement**: REQ-001 -- Section 2 (GrowthPhase, Edge: consists_of)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- A lifecycle config has just been created for a species

**Test Steps**:
1. Observe the area below the lifecycle config form

**Expected Results**:
- A section titled "Wachstumsphasen" is displayed
- A "Phase erstellen" button is visible
- If no phases exist yet, the table area is empty

**Postconditions**:
- The growth phase section is rendered

**Tags**: [REQ-001, growth-phase, list, lifecycle-prerequisite, happy-path]

---

### TC-REQ-001-057: Create a growth phase via dialog

**Requirement**: REQ-001 -- Section 2 (GrowthPhase: name, typical_duration_days, sequence)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- A lifecycle config exists
- The user is on the "Lebenszyklus-Konfiguration" tab with the growth phases section visible

**Test Steps**:
1. Click "Phase erstellen"
2. A dialog opens with title "Phase erstellen"
3. Enter "germination" in the "Name" field
4. Enter "Keimung" in the "Anzeigename" field
5. Enter "7" for "Typische Dauer (Tage)"
6. Enter "0" for "Reihenfolge"
7. Select "Niedrig" for "Stresstoleranz"
8. Leave "Endphase" switch OFF
9. Leave "Ernte erlaubt" switch OFF
10. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The dialog closes
- The phase "Keimung" appears in the growth phases table
- The row shows: # = 0, Name = "Keimung", Duration = "7d", Stresstoleranz = "Niedrig"

**Postconditions**:
- A GrowthPhase is created and linked via `consists_of` edge with sequence = 0

**Tags**: [REQ-001, growth-phase, create, dialog, happy-path]

---

### TC-REQ-001-058: Create multiple phases to build a complete lifecycle

**Requirement**: REQ-001 -- Section 2 (GrowthPhase), DoD: "Jede Spezies hat mindestens 3 GrowthPhases"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- A lifecycle config exists with 0 phases

**Test Steps**:
1. Create phase: name="germination", display_name="Keimung", duration=7, order=0, stress_tolerance=low
2. Create phase: name="seedling", display_name="Saemling", duration=14, order=1, stress_tolerance=low
3. Create phase: name="vegetative", display_name="Vegetativ", duration=28, order=2, stress_tolerance=medium
4. Create phase: name="flowering", display_name="Bluete", duration=56, order=3, stress_tolerance=medium, is_terminal=false
5. Create phase: name="harvest", display_name="Ernte", duration=14, order=4, stress_tolerance=high, is_terminal=true, allows_harvest=true

**Expected Results**:
- All 5 phases are listed in the table, sorted by sequence_order (Reihenfolge)
- The "harvest" phase shows a "Terminal" chip (yellow) and a "Harvest" chip (green)
- The phases are ordered: Keimung (0) -> Saemling (1) -> Vegetativ (2) -> Bluete (3) -> Ernte (4)

**Postconditions**:
- A complete lifecycle with 5 phases exists

**Tags**: [REQ-001, growth-phase, create, complete-lifecycle, happy-path]

---

### TC-REQ-001-059: Edit an existing growth phase

**Requirement**: REQ-001 -- Section 2 (GrowthPhase)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- At least one growth phase exists
- The user is viewing the growth phases table

**Test Steps**:
1. Click on the row for "Vegetativ"
2. The dialog opens with title "Bearbeiten" and pre-populated fields
3. Change "Typische Dauer (Tage)" from 28 to 35
4. Click "Speichern"

**Expected Results**:
- A success notification is displayed
- The dialog closes
- The "Vegetativ" row now shows "35d" in the duration column

**Postconditions**:
- The growth phase is updated

**Tags**: [REQ-001, growth-phase, edit, dialog, happy-path]

---

### TC-REQ-001-060: Delete a growth phase

**Requirement**: REQ-001 -- Section 2 (GrowthPhase)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Multiple growth phases exist

**Test Steps**:
1. Click the delete icon button on the "Keimung" phase row
2. A confirmation dialog appears: "Sind Sie sicher, dass Sie "germination" loeschen moechten?..."
3. Click "Bestaetigen"

**Expected Results**:
- A success notification is displayed
- "Keimung" is removed from the phases table
- Remaining phases are still displayed

**Postconditions**:
- The growth phase is deleted

**Tags**: [REQ-001, growth-phase, delete, confirmation-dialog, happy-path]

---

### TC-REQ-001-061: Validation error -- phase name required

**Requirement**: REQ-001 -- Section 2 (GrowthPhase: name required)
**Priority**: Medium
**Category**: Error Handling
**Preconditions**:
- The growth phase create dialog is open

**Test Steps**:
1. Leave "Name" empty
2. Click "Erstellen"

**Expected Results**:
- The form does NOT submit
- An inline validation error is shown
- The dialog remains open

**Postconditions**:
- No phase is created

**Tags**: [REQ-001, growth-phase, create, validation, error-handling, required-field]

---

### TC-REQ-001-062: Validation error -- duration must be at least 1

**Requirement**: REQ-001 -- Section 2 (GrowthPhase: typical_duration_days min=1)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- The growth phase create dialog is open

**Test Steps**:
1. Enter "testphase" in "Name"
2. Enter "0" for "Typische Dauer (Tage)"
3. Click "Erstellen"

**Expected Results**:
- The form does NOT submit
- A validation error is shown for the duration field

**Postconditions**:
- No phase is created

**Tags**: [REQ-001, growth-phase, create, validation, boundary-value, error-handling]

---

## 13. Growth Phase Profiles

### TC-REQ-001-063: View profiles for a growth phase

**Requirement**: REQ-001 -- Section 2 (GrowthPhase profiles)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- A growth phase "Vegetativ" exists with requirement and nutrient profiles already generated

**Test Steps**:
1. In the growth phases table, click the "Profiles" button on the "Vegetativ" row

**Expected Results**:
- A profiles section appears below the table with the phase name: "Vegetativ -- Profil"
- Two cards are displayed side by side:
  - "Anforderungsprofil" card showing: Licht-PPFD, Photoperiode (h), Tagestemperatur, Nachttemperatur, Luftfeuchtigkeit Tag/Nacht, VPD-Ziel
  - "Naehrstoffprofil" card showing: NPK-Verhaeltnis, Ziel-EC (mS/cm), Ziel-pH, Ca (ppm), Mg (ppm)

**Postconditions**:
- Profile data is displayed for the selected phase

**Tags**: [REQ-001, growth-phase, profiles, requirement, nutrient, happy-path]

---

### TC-REQ-001-064: Generate default profiles for a phase without profiles

**Requirement**: REQ-001 -- Section 2 (GrowthPhase profiles)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- A growth phase exists without any profiles

**Test Steps**:
1. Click the "Profiles" button on a phase row
2. The profiles section shows neither card but displays a "Standardwerte generieren" button
3. Click "Standardwerte generieren"

**Expected Results**:
- A success notification is displayed
- Both profile cards now appear with generated default values
- The "Standardwerte generieren" button disappears

**Postconditions**:
- Default profiles are generated and persisted

**Tags**: [REQ-001, growth-phase, profiles, generate-defaults, happy-path]

---

## 14. Companion Planting Page

### TC-REQ-001-065: Select a species and view companion planting relationships

**Requirement**: REQ-001 -- Section 2 (Edges: compatible_with, incompatible_with)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- At least 3 species exist
- "Solanum lycopersicum" has compatible_with edge to "Ocimum basilicum" (score: 0.9)
- "Solanum lycopersicum" has incompatible_with edge to "Brassica oleracea" (reason: "Allelopathie")

**Test Steps**:
1. Navigate to `/stammdaten/companion-planting`
2. Select "Solanum lycopersicum" from the "Art auswaehlen" dropdown

**Expected Results**:
- Two cards are displayed side by side:
  - "Kompatible Arten" card with a list showing "Ocimum basilicum" and a green chip "0.9"
  - "Inkompatible Arten" card with a list showing "Brassica oleracea" and the reason "Allelopathie" as secondary text
- Each card has an "add" button: "Kompatibilitaet hinzufuegen" and "Inkompatibilitaet hinzufuegen"

**Postconditions**:
- Companion planting relationships are displayed for the selected species

**Tags**: [REQ-001, companion-planting, view-relationships, happy-path]

---

### TC-REQ-001-066: Add a compatible species relationship

**Requirement**: REQ-001 -- Section 2 (Edge: compatible_with with compatibility_score)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- "Solanum lycopersicum" is selected on the Companion Planting page
- "Allium cepa" exists but has no compatibility edge to "Solanum lycopersicum"

**Test Steps**:
1. Click "Kompatibilitaet hinzufuegen"
2. A dialog opens with title "Kompatibilitaet hinzufuegen"
3. Select "Allium cepa" from the species dropdown
4. Set the "Bewertung" (score) to "0.7"
5. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The dialog closes
- "Allium cepa" now appears in the "Kompatible Arten" list with a chip "0.7"

**Postconditions**:
- A `compatible_with` edge exists from Solanum lycopersicum to Allium cepa with score 0.7

**Tags**: [REQ-001, companion-planting, add-compatible, dialog, happy-path]

---

### TC-REQ-001-067: Add an incompatible species relationship

**Requirement**: REQ-001 -- Section 2 (Edge: incompatible_with with reason)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- "Solanum lycopersicum" is selected on the Companion Planting page

**Test Steps**:
1. Click "Inkompatibilitaet hinzufuegen"
2. A dialog opens with title "Inkompatibilitaet hinzufuegen"
3. Select a target species from the dropdown
4. Enter "Wachstumshemmung durch Wurzelexsudate" in the "Grund" field
5. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The dialog closes
- The target species appears in the "Inkompatible Arten" list with the reason text as secondary text

**Postconditions**:
- An `incompatible_with` edge exists with the specified reason

**Tags**: [REQ-001, companion-planting, add-incompatible, dialog, happy-path]

---

### TC-REQ-001-068: Empty state when no relationships exist for a species

**Requirement**: REQ-001 -- Companion Planting page
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- A species exists with no compatible_with or incompatible_with edges

**Test Steps**:
1. Select the species from the dropdown

**Expected Results**:
- Both cards ("Kompatible Arten" and "Inkompatible Arten") show an empty state
- The "add" buttons are still available

**Postconditions**:
- The user can add relationships from the empty state

**Tags**: [REQ-001, companion-planting, empty-state, edge-case]

---

### TC-REQ-001-069: The "Erstellen" button in the add dialog is disabled when no target species is selected

**Requirement**: REQ-001 -- Companion Planting dialog UX
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- The "Kompatibilitaet hinzufuegen" dialog is open

**Test Steps**:
1. Observe the "Erstellen" button without selecting any target species

**Expected Results**:
- The "Erstellen" button is disabled
- After selecting a target species, the button becomes enabled

**Postconditions**:
- The user cannot submit without a target species

**Tags**: [REQ-001, companion-planting, dialog, button-state, edge-case]

---

### TC-REQ-001-070: The current species is excluded from the target dropdown

**Requirement**: REQ-001 -- Companion Planting dialog UX
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- "Solanum lycopersicum" is selected as the source species
- The "add compatible" dialog is open

**Test Steps**:
1. Open the target species dropdown in the dialog

**Expected Results**:
- "Solanum lycopersicum" does NOT appear in the target dropdown
- All other species are available for selection

**Postconditions**:
- Self-referencing edges are prevented in the UI

**Tags**: [REQ-001, companion-planting, self-reference-prevention, edge-case]

---

## 15. Crop Rotation Page

### TC-REQ-001-071: Select a family and view rotation successors

**Requirement**: REQ-001 -- Section 2 (Edge: rotation_after)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed data families exist with rotation_after edges (e.g., Fabaceae after Solanaceae)

**Test Steps**:
1. Navigate to `/stammdaten/crop-rotation`
2. Select "Solanaceae" from the "Von Familie" dropdown

**Expected Results**:
- A list of rotation successors is displayed
- Each list item shows the successor family name and a chip with the wait time (e.g., "3 Wartezeit (Jahre)")
- A "Nachfolger hinzufuegen" button is visible

**Postconditions**:
- Rotation successors for the selected family are displayed

**Tags**: [REQ-001, crop-rotation, view-successors, happy-path]

---

### TC-REQ-001-072: Add a rotation successor

**Requirement**: REQ-001 -- Section 2 (Edge: rotation_after with wait_years)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- "Solanaceae" is selected on the Crop Rotation page

**Test Steps**:
1. Click "Nachfolger hinzufuegen"
2. A dialog opens with title "Nachfolger hinzufuegen"
3. Select "Apiaceae" from the "Zu Familie" dropdown
4. Set "Wartezeit (Jahre)" to "2"
5. Click "Erstellen"

**Expected Results**:
- A success notification is displayed
- The dialog closes
- "Apiaceae" (or its name) now appears in the successor list with chip "2 Wartezeit (Jahre)"

**Postconditions**:
- A `rotation_after` edge is created

**Tags**: [REQ-001, crop-rotation, add-successor, dialog, happy-path]

---

### TC-REQ-001-073: Empty state when no successors exist

**Requirement**: REQ-001 -- Crop Rotation page
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- A botanical family exists with no rotation_after edges

**Test Steps**:
1. Select the family from the "Von Familie" dropdown

**Expected Results**:
- An empty state is displayed
- The "Nachfolger hinzufuegen" button is still available

**Postconditions**:
- The user can add successors from the empty state

**Tags**: [REQ-001, crop-rotation, empty-state, edge-case]

---

### TC-REQ-001-074: The current family is excluded from the successor dropdown

**Requirement**: REQ-001 -- Crop Rotation dialog UX
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- "Solanaceae" is selected as the source family
- The "Nachfolger hinzufuegen" dialog is open

**Test Steps**:
1. Open the "Zu Familie" dropdown

**Expected Results**:
- "Solanaceae" does NOT appear in the target dropdown
- All other families are available

**Postconditions**:
- Self-referencing rotation edges are prevented in the UI

**Tags**: [REQ-001, crop-rotation, self-reference-prevention, edge-case]

---

### TC-REQ-001-075: The "Erstellen" button is disabled without a target family

**Requirement**: REQ-001 -- Crop Rotation dialog UX
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- The "Nachfolger hinzufuegen" dialog is open

**Test Steps**:
1. Do not select any target family

**Expected Results**:
- The "Erstellen" button is disabled

**Postconditions**:
- The user must select a target before submitting

**Tags**: [REQ-001, crop-rotation, dialog, button-state, edge-case]

---

## 16. Error Handling and Backend Validation

### TC-REQ-001-076: Network error shows error notification

**Requirement**: REQ-001 -- Error handling (NFR-006)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- The backend server is unreachable (simulated by disconnecting network or stopping the API server)

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`

**Expected Results**:
- A loading skeleton is displayed briefly
- An error notification or error display is shown with a message like "Netzwerkfehler. Bitte ueberpruefen Sie Ihre Verbindung."

**Postconditions**:
- The user is informed about the network issue

**Tags**: [REQ-001, error-handling, network-error, notification]

---

### TC-REQ-001-077: Server error (500) shows error notification

**Requirement**: REQ-001 -- Error handling (NFR-006)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- The backend returns a 500 server error for a request

**Test Steps**:
1. Trigger an action that causes a server error (e.g., a malformed request that the backend cannot process)

**Expected Results**:
- An error notification is displayed: "Serverfehler. Bitte versuchen Sie es spaeter erneut."
- The user can continue using the application

**Postconditions**:
- The application remains functional

**Tags**: [REQ-001, error-handling, server-error, notification]

---

### TC-REQ-001-078: Duplicate family name shows backend validation error

**Requirement**: REQ-001 -- Section 5 DoD: "Duplikatspruefung"
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- "Solanaceae" already exists

**Test Steps**:
1. Open the botanical family create dialog
2. Enter "Solanaceae" in the "Name" field
3. Fill in required fields
4. Click "Erstellen"

**Expected Results**:
- An error notification is displayed indicating a duplicate: "Ein Eintrag mit diesem Namen existiert bereits."
- The dialog remains open so the user can correct the name

**Postconditions**:
- No duplicate family is created

**Tags**: [REQ-001, botanical-family, create, duplicate, error-handling, business-rule]

---

## 17. Data Table Features (Shared Component)

### TC-REQ-001-079: Search with no results shows empty search state

**Requirement**: REQ-001 -- DataTable component
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- At least 3 botanical families exist

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`
2. Type "ZZZNONEXISTENT" into the search field

**Expected Results**:
- The table body is replaced by a "no results" state with a search-off icon
- The message "Keine Ergebnisse fuer Ihre Suche gefunden" is displayed
- A "Alle Filter zuruecksetzen" button is shown below the message

**Postconditions**:
- The user can reset filters to see all data again

**Tags**: [REQ-001, data-table, search, no-results, empty-state]

---

### TC-REQ-001-080: Keyboard navigation -- press Enter on a table row

**Requirement**: REQ-001 -- DataTable accessibility
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- The botanical families table has rows

**Test Steps**:
1. Use Tab to focus on a table row
2. Press Enter

**Expected Results**:
- The same action as clicking the row is triggered (navigation to detail page)
- Rows have visible focus indication (outline)

**Postconditions**:
- The detail page is displayed

**Tags**: [REQ-001, data-table, keyboard-navigation, accessibility]

---

### TC-REQ-001-081: Showing count displays correct range

**Requirement**: REQ-001 -- DataTable pagination
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- 9 botanical families exist (seed data)

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`

**Expected Results**:
- The showing count displays "Zeigt 1-9 von 9 Eintraegen" (or the actual count)
- Pagination controls show the total number of entries

**Postconditions**:
- The count accurately reflects the data

**Tags**: [REQ-001, data-table, showing-count, pagination]

---

### TC-REQ-001-082: Change page size in the data table

**Requirement**: REQ-001 -- DataTable pagination
**Priority**: Low
**Category**: Happy Path
**Preconditions**:
- The botanical families table is displayed with default page size

**Test Steps**:
1. Click the "Zeilen pro Seite" dropdown in the pagination area
2. Select "10"

**Expected Results**:
- The table shows at most 10 rows per page
- The pagination updates to reflect the new page size

**Postconditions**:
- The page size is changed

**Tags**: [REQ-001, data-table, page-size, pagination]

---

## 18. Loading States

### TC-REQ-001-083: Loading skeleton shown while fetching botanical families

**Requirement**: REQ-001 -- UX loading states
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- The network has some latency

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`

**Expected Results**:
- A table-variant loading skeleton is displayed while data is being fetched
- Once data arrives, the skeleton is replaced by the actual data table

**Postconditions**:
- The user sees a smooth loading experience

**Tags**: [REQ-001, loading-skeleton, ux, happy-path]

---

### TC-REQ-001-084: Loading skeleton on species detail page

**Requirement**: REQ-001 -- UX loading states
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- The network has some latency

**Test Steps**:
1. Navigate to `/stammdaten/species/{key}`

**Expected Results**:
- A form-variant loading skeleton is displayed while the species data loads
- Once data arrives, the form is rendered with populated fields

**Postconditions**:
- The user sees a smooth loading experience

**Tags**: [REQ-001, loading-skeleton, species, detail, ux]

---

## 19. Seed Data Verification (Acceptance Criteria)

### TC-REQ-001-085: Verify seed data -- 9 botanical families with correct attributes

**Requirement**: REQ-001 -- Section 2 (Seed data: BotanicalFamily table), DoD: "Alle 9 Seed-Familien mit vollstaendigen erweiterten Attributen"
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The system has been initialized with seed data

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`

**Expected Results**:
- Exactly 9 families are listed:
  - Solanaceae -- Nachtschattengewaechse -- Starkzehrer -- Empfindlich -- Mittel
  - Brassicaceae -- Kreuzbluetler -- Starkzehrer -- Hardy -- Mittel
  - Fabaceae -- Huelsenfruechtler -- Schwachzehrer -- Moderat -- Tief
  - Cucurbitaceae -- Kuerbisgewaechse -- Starkzehrer -- Empfindlich -- Flach
  - Apiaceae -- Doldenbluetler -- Mittelzehrer -- Hardy -- Tief
  - Asteraceae -- Korbbluetler -- Mittelzehrer -- Moderat -- Mittel
  - Poaceae -- Suesgraeser -- Mittelzehrer -- Sehr hardy -- Flach
  - Lamiaceae -- Lippenbluetler -- Schwachzehrer -- Moderat -- Flach
  - Cannabaceae -- Hanfgewaechse -- Starkzehrer -- Empfindlich -- Tief

**Postconditions**:
- All seed families are verified

**Tags**: [REQ-001, botanical-family, seed-data, verification, acceptance-criteria]

---

### TC-REQ-001-086: Verify Fabaceae has nitrogen_fixing = true

**Requirement**: REQ-001 -- Section 2 (Seed data: Fabaceae nitrogen_fixing=true)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed data is loaded

**Test Steps**:
1. Navigate to the detail page for "Fabaceae" (`/stammdaten/botanical-families/{fabaceae_key}`)

**Expected Results**:
- The "Stickstofffixierend" switch is toggled ON
- The "Naehrstoffbedarf" shows "Schwachzehrer"

**Postconditions**:
- Fabaceae seed data is verified

**Tags**: [REQ-001, botanical-family, seed-data, nitrogen-fixing, fabaceae]

---

### TC-REQ-001-087: Verify Cannabaceae seed data

**Requirement**: REQ-001 -- Section 2 (Seed data: Cannabaceae)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed data is loaded

**Test Steps**:
1. Navigate to the detail page for "Cannabaceae"

**Expected Results**:
- Name: "Cannabaceae"
- Deutscher Name: "Hanfgewaechse"
- Englischer Name: "Hemp family"
- Ordnung: "Rosales"
- Naehrstoffbedarf: "Starkzehrer"
- Stickstofffixierend: OFF
- Wurzeltiefe: "Tief"
- Frosttoleranz: "Empfindlich"
- Bestaeubungstypen includes: "Windbestaeubung"

**Postconditions**:
- Cannabaceae seed data is verified

**Tags**: [REQ-001, botanical-family, seed-data, cannabaceae, cannabis]

---

### TC-REQ-001-088: Verify rotation successors for Solanaceae

**Requirement**: REQ-001 -- Section 2 (Seed data: rotation_after edges)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed data rotation_after edges are loaded

**Test Steps**:
1. Navigate to `/stammdaten/crop-rotation`
2. Select "Solanaceae" from the "Von Familie" dropdown

**Expected Results**:
- The successor list shows families that are "good successors after Solanaceae"
- Based on seed data, "Fabaceae" should appear as a successor (benefit_score: 0.95, reason: nitrogen_fixation)

**Postconditions**:
- Rotation edges for Solanaceae are verified

**Tags**: [REQ-001, crop-rotation, seed-data, rotation-after, solanaceae]

---

## 20. Cross-Entity Workflows

### TC-REQ-001-089: Complete workflow -- create family, species, cultivar, lifecycle, and phases

**Requirement**: REQ-001 -- All sections (end-to-end workflow)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- The system is clean or has minimal data

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families` and click "Familie erstellen"
2. Create "Testaceae" with Naehrstoffbedarf "Mittelzehrer", Frosttoleranz "Moderat"
3. Navigate to `/stammdaten/species` and click "Art erstellen"
4. Create "Testus speciesii" with family = "Testaceae", genus = "Testus"
5. Click on the newly created species in the list to go to its detail page
6. Click the "Sorten" tab and then "Sorte erstellen"
7. Create cultivar "Test Variety" with days_to_maturity = 90
8. Click the "Lebenszyklus-Konfiguration" tab
9. Create a lifecycle config with cycle_type = "Einjaehrig", photoperiod_type = "Tagneutral"
10. Click "Phase erstellen" and create 3 phases: germination (order 0), vegetative (order 1), harvest (order 2, terminal, allows_harvest)

**Expected Results**:
- All entities are created successfully with notifications at each step
- The species detail page shows:
  - "Bearbeiten" tab: species data with family "Testaceae"
  - "Sorten" tab: "Test Variety" in the cultivar list
  - "Lebenszyklus-Konfiguration" tab: annual config with 3 growth phases listed
- Navigation between tabs preserves data

**Postconditions**:
- A complete entity hierarchy exists: Family -> Species -> Cultivar, Species -> LifecycleConfig -> 3 GrowthPhases

**Tags**: [REQ-001, end-to-end, complete-workflow, family, species, cultivar, lifecycle, growth-phase, happy-path]

---

### TC-REQ-001-090: Species family dropdown shows all available families

**Requirement**: REQ-001 -- Section 2 (Edge: belongs_to_family)
**Priority**: High
**Category**: Integration
**Preconditions**:
- 9 seed families exist
- The species create dialog is open

**Test Steps**:
1. Open the "Familie" dropdown in the species create dialog

**Expected Results**:
- The dropdown contains a "-" (empty) option plus all 9 seed families (Solanaceae, Brassicaceae, Fabaceae, etc.)
- Each option shows the family name

**Postconditions**:
- Family selection is available for species creation

**Tags**: [REQ-001, species, create, family-dropdown, integration]

---

### TC-REQ-001-091: Companion planting page loads species list for selection

**Requirement**: REQ-001 -- Section 2 (companion planting relationships)
**Priority**: Medium
**Category**: Integration
**Preconditions**:
- At least 5 species exist

**Test Steps**:
1. Navigate to `/stammdaten/companion-planting`

**Expected Results**:
- The species dropdown is populated with available species (up to 200)
- Each option shows the scientific name

**Postconditions**:
- Species are available for companion planting analysis

**Tags**: [REQ-001, companion-planting, species-loading, integration]

---

### TC-REQ-001-092: Crop rotation page loads all families for selection

**Requirement**: REQ-001 -- Section 2 (crop rotation relationships)
**Priority**: Medium
**Category**: Integration
**Preconditions**:
- 9 seed families exist

**Test Steps**:
1. Navigate to `/stammdaten/crop-rotation`

**Expected Results**:
- The "Von Familie" dropdown is populated with all 9 botanical families
- Each option shows the family name

**Postconditions**:
- Families are available for crop rotation analysis

**Tags**: [REQ-001, crop-rotation, family-loading, integration]

---

## 21. i18n and Display

### TC-REQ-001-093: All enum values are displayed in German translation

**Requirement**: REQ-001 -- i18n (NFR-003), DoD: "i18n-Anzeige: common_name_de/en in UI je nach Spracheinstellung"
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- The application language is set to German (default)

**Test Steps**:
1. Navigate to `/stammdaten/botanical-families`
2. Observe the table columns for "Naehrstoffbedarf", "Frosttoleranz", and "Wurzeltiefe"

**Expected Results**:
- Nutrient demand values show: "Schwachzehrer" / "Mittelzehrer" / "Starkzehrer" (not "light" / "medium" / "heavy")
- Frost tolerance values show: "Empfindlich" / "Moderat" / "Hardy" / "Sehr hardy" (not raw enum keys)
- Root depth values show: "Flach" / "Mittel" / "Tief" (not "shallow" / "medium" / "deep")

**Postconditions**:
- All enum values are correctly translated

**Tags**: [REQ-001, i18n, enum-translation, german, display]

---

### TC-REQ-001-094: Growth habit enums displayed in German on species list

**Requirement**: REQ-001 -- i18n
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Species exist with various growth habits

**Test Steps**:
1. Navigate to `/stammdaten/species`
2. Observe the "Wuchsform" and "Wurzeltyp" columns

**Expected Results**:
- Growth habits show: "Kraut" / "Strauch" / "Baum" / "Ranke" / "Bodendecker"
- Root types show: "Faserig" / "Pfahlwurzel" / "Knollig" / "Zwiebel"

**Postconditions**:
- All species enum values are correctly translated

**Tags**: [REQ-001, i18n, species, enum-translation, german]

---

### TC-REQ-001-095: Cultivar trait chips show German translations

**Requirement**: REQ-001 -- i18n (plantTrait enum)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- A cultivar exists with traits: ["disease_resistant", "high_yield", "compact"]

**Test Steps**:
1. Navigate to the species detail page and click the "Sorten" tab

**Expected Results**:
- The traits column shows chips with German labels:
  - "Krankheitsresistent" (not "disease_resistant")
  - "Ertragreich" (not "high_yield")
  - "Kompakt" (not "compact")

**Postconditions**:
- Trait names are correctly translated

**Tags**: [REQ-001, cultivar, i18n, traits, enum-translation, german]

---

## Coverage Summary

| Spec Section | Test Cases | Coverage |
|---|---|---|
| Navigation & Routing | TC-001 to TC-005 | All REQ-001 routes verified |
| BotanicalFamily List Page | TC-006 to TC-012 | Table display, search, sort, pagination, row-click, empty state |
| BotanicalFamily Create Dialog | TC-013 to TC-022 | Happy path, all validations (-aceae, required, growth forms, pollination, nitrogen+heavy, pH bounds), minimal fields, cancel |
| BotanicalFamily Detail Page | TC-023 to TC-028 | View, edit, save, unsaved guard, delete+confirm, cancel delete, not-found error |
| Species List Page | TC-029 to TC-032 | Table display, pagination, row-click, empty state |
| Species Create Dialog | TC-033 to TC-037 | Form layout, happy path, required field, boundary values, no-family |
| Species Detail Page | TC-038 to TC-041 | Tabs, edit, delete, unsaved guard |
| Cultivar List Section | TC-042 to TC-044 | Table in tab, row-click nav, inline delete |
| Cultivar Create Dialog | TC-045 to TC-047 | Happy path, required name, boundary days-to-maturity |
| Cultivar Detail Page | TC-048 to TC-050 | View, edit, delete+redirect |
| Lifecycle Config Section | TC-051 to TC-055 | No-config state, annual create, perennial+dormancy, biennial+vernalization, edit existing |
| Growth Phase Management | TC-056 to TC-062 | Section visibility, create dialog, multi-phase lifecycle, edit, delete, name required, duration boundary |
| Growth Phase Profiles | TC-063 to TC-064 | View profiles, generate defaults |
| Companion Planting Page | TC-065 to TC-070 | View relationships, add compatible, add incompatible, empty state, button disabled, self-exclusion |
| Crop Rotation Page | TC-071 to TC-075 | View successors, add successor, empty state, self-exclusion, button disabled |
| Error Handling | TC-076 to TC-078 | Network error, server error, duplicate |
| DataTable Features | TC-079 to TC-082 | No search results, keyboard nav, showing count, page size |
| Loading States | TC-083 to TC-084 | Table skeleton, form skeleton |
| Seed Data Verification | TC-085 to TC-088 | 9 families, Fabaceae nitrogen, Cannabaceae details, rotation successors |
| Cross-Entity Workflows | TC-089 to TC-092 | Full CRUD workflow, dropdown integrations |
| i18n Display | TC-093 to TC-095 | Enum translations for families, species, cultivar traits |
