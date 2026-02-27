---
req_id: REQ-001
title: Stammdatenverwaltung von Pflanzen-Entitaetszyklen
category: Stammdaten
test_count: 78
coverage_areas:
  - Species CRUD & Validation
  - BotanicalFamily CRUD & Validation
  - Cultivar CRUD & Validation
  - LifecycleConfig & Biennial/Perennial Logic
  - GrowthPhase Management
  - Companion Planting (Species-Level Edges)
  - Companion Planting (Family-Level Fallback)
  - Crop Rotation (rotation_after Edges)
  - Pest Risk (shares_pest_risk Edges)
  - Family Compatibility/Incompatibility Edges
  - Dormancy Trigger Logic
  - Vernalization Tracker Logic
  - Photoperiod Calculation
  - Acceptance Scenarios (Spec Section 5)
generated: 2026-02-27
version: "3.0"
---

# TC-REQ-001: Stammdatenverwaltung (Master Data Management)

This document contains end-to-end test cases derived from **REQ-001 Stammdatenverwaltung von Pflanzen-Entitaetszyklen v3.0**. The specification defines the botanical taxonomy foundation layer: Species, BotanicalFamily, Cultivar, LifecycleConfig, and GrowthPhase entities, along with graph edges for companion planting, crop rotation, pest risk sharing, and family compatibility.

REQ-001 is the **foundation module** upon which REQ-002 through REQ-012 depend.

---

## 1. Species CRUD and Validation

### TC-REQ-001-001: Create a valid species with binomial nomenclature

**Requirement**: REQ-001 -- Section 2 (Nodes: Species), Section 3 (Species-Validator)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- System is running with an empty or seeded ArangoDB `species` collection
- A BotanicalFamily with key `solanaceae` exists (optional, for `family_key` linkage)

**Test Steps**:
1. Send `POST /api/v1/species` with body:
   ```json
   {
     "scientific_name": "Solanum lycopersicum",
     "common_names": ["Tomate", "Tomato"],
     "family_key": "solanaceae",
     "genus": "Solanum",
     "hardiness_zones": ["7a", "7b", "8a"],
     "native_habitat": "South America",
     "growth_habit": "herb",
     "root_type": "fibrous",
     "allelopathy_score": -0.3,
     "base_temp": 10.0
   }
   ```

**Expected Results**:
- HTTP 201 Created
- Response contains a generated `key` (non-empty string)
- `scientific_name` equals `"Solanum lycopersicum"`
- `common_names` contains exactly `["Tomate", "Tomato"]`
- `growth_habit` equals `"herb"`
- `allelopathy_score` equals `-0.3`
- `created_at` is set to a recent timestamp

**Postconditions**:
- Species document exists in `species` collection with the returned key
- `GET /api/v1/species/{key}` returns the same data

**Tags**: [REQ-001, species, crud, happy-path, api]

---

### TC-REQ-001-002: Reject species with single-word scientific name

**Requirement**: REQ-001 -- Section 3 (Species-Validator: validate_binomial)
**Priority**: Critical
**Category**: Error Handling
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/species` with body:
   ```json
   {
     "scientific_name": "Solanum",
     "common_names": ["Tomate"]
   }
   ```

**Expected Results**:
- HTTP 422 Unprocessable Entity
- Error message indicates that the scientific name must follow binomial nomenclature (at least two parts)

**Postconditions**:
- No new document created in `species` collection

**Tags**: [REQ-001, species, validation, error-handling, binomial-nomenclature, api]

---

### TC-REQ-001-003: Reject species with invalid hardiness zone format

**Requirement**: REQ-001 -- Section 2 (Species), Section 3 (validate_hardiness_zones)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/species` with body:
   ```json
   {
     "scientific_name": "Solanum lycopersicum",
     "common_names": ["Tomate"],
     "hardiness_zones": ["7a", "invalid", "15z"]
   }
   ```

**Expected Results**:
- HTTP 422 Unprocessable Entity
- Error references invalid USDA hardiness zone format for `"invalid"` and/or `"15z"`

**Postconditions**:
- No species created

**Tags**: [REQ-001, species, validation, error-handling, hardiness-zones, api]

---

### TC-REQ-001-004: Allelopathy score boundary values

**Requirement**: REQ-001 -- Section 2 (Species: `allelopathy_score: float`, range -1.0 to 1.0)
**Priority**: High
**Category**: Edge Case
**Preconditions**:
- System is running

**Test Steps**:
1. Create species with `allelopathy_score: -1.0` (minimum valid) -- expect HTTP 201
2. Create species with `allelopathy_score: 1.0` (maximum valid) -- expect HTTP 201
3. Create species with `allelopathy_score: 0.0` (neutral) -- expect HTTP 201
4. Create species with `allelopathy_score: -1.1` (below minimum) -- expect HTTP 422
5. Create species with `allelopathy_score: 1.1` (above maximum) -- expect HTTP 422

**Expected Results**:
- Steps 1-3: HTTP 201, species created with exact allelopathy_score value
- Steps 4-5: HTTP 422 with validation error indicating value out of range

**Postconditions**:
- Three valid species exist in the collection

**Tags**: [REQ-001, species, validation, boundary-value, allelopathy, api]

---

### TC-REQ-001-005: List species with pagination

**Requirement**: REQ-001 -- Section 2 (Species CRUD)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- At least 5 species exist in the database

**Test Steps**:
1. Send `GET /api/v1/species?offset=0&limit=2`
2. Send `GET /api/v1/species?offset=2&limit=2`
3. Send `GET /api/v1/species?offset=0&limit=200`

**Expected Results**:
- Step 1: Response contains `items` (length 2), `total` >= 5, `offset` = 0, `limit` = 2
- Step 2: Response contains `items` (length 2), `offset` = 2, `limit` = 2, items differ from step 1
- Step 3: Response contains all items up to 200, `limit` = 200

**Postconditions**:
- No state change

**Tags**: [REQ-001, species, pagination, happy-path, api]

---

### TC-REQ-001-006: Update an existing species

**Requirement**: REQ-001 -- Section 2 (Species CRUD)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Species with key `tomato-01` exists with `growth_habit: "herb"`

**Test Steps**:
1. Send `PUT /api/v1/species/tomato-01` with body:
   ```json
   {
     "scientific_name": "Solanum lycopersicum",
     "common_names": ["Tomate", "Tomato", "Pomodoro"],
     "growth_habit": "vine",
     "root_type": "fibrous",
     "allelopathy_score": -0.3
   }
   ```
2. Send `GET /api/v1/species/tomato-01`

**Expected Results**:
- Step 1: HTTP 200, response shows `growth_habit: "vine"` and `common_names` with 3 entries
- Step 2: Confirms persisted update, `updated_at` is more recent than `created_at`

**Postconditions**:
- Species document reflects the updated values

**Tags**: [REQ-001, species, crud, update, happy-path, api]

---

### TC-REQ-001-007: Delete a species

**Requirement**: REQ-001 -- Section 2 (Species CRUD)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Species with key `delete-me` exists

**Test Steps**:
1. Send `DELETE /api/v1/species/delete-me`
2. Send `GET /api/v1/species/delete-me`

**Expected Results**:
- Step 1: HTTP 204 No Content
- Step 2: HTTP 404 Not Found

**Postconditions**:
- Species document removed from `species` collection

**Tags**: [REQ-001, species, crud, delete, happy-path, api]

---

### TC-REQ-001-008: Get non-existent species returns 404

**Requirement**: REQ-001 -- Section 2 (Species CRUD), NFR-006 (Error Handling)
**Priority**: Medium
**Category**: Error Handling
**Preconditions**:
- No species with key `nonexistent-key` exists

**Test Steps**:
1. Send `GET /api/v1/species/nonexistent-key`

**Expected Results**:
- HTTP 404 Not Found
- Response body includes error detail identifying the missing resource

**Postconditions**:
- No state change

**Tags**: [REQ-001, species, error-handling, not-found, api]

---

### TC-REQ-001-009: Reject species with invalid growth_habit enum value

**Requirement**: REQ-001 -- Section 3 (GrowthHabit enum: herb, shrub, tree, vine, groundcover)
**Priority**: Medium
**Category**: Error Handling
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/species` with body:
   ```json
   {
     "scientific_name": "Solanum lycopersicum",
     "common_names": ["Tomate"],
     "growth_habit": "bush"
   }
   ```

**Expected Results**:
- HTTP 422 Unprocessable Entity
- Error references invalid value `"bush"` for `growth_habit`; valid values are: herb, shrub, tree, vine, groundcover

**Postconditions**:
- No species created

**Tags**: [REQ-001, species, validation, enum, error-handling, api]

---

### TC-REQ-001-010: Reject species with invalid root_type enum value

**Requirement**: REQ-001 -- Section 3 (RootType enum: fibrous, taproot, tuberous, bulbous)
**Priority**: Medium
**Category**: Error Handling
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/species` with `"root_type": "rhizome"`

**Expected Results**:
- HTTP 422 Unprocessable Entity
- Error identifies invalid `root_type` value

**Postconditions**:
- No species created

**Tags**: [REQ-001, species, validation, enum, error-handling, api]

---

### TC-REQ-001-011: Create species with minimal required fields only

**Requirement**: REQ-001 -- Section 2 (Species), Section 3 (SpeciesDefinition)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/species` with body:
   ```json
   {
     "scientific_name": "Ocimum basilicum"
   }
   ```

**Expected Results**:
- HTTP 201 Created
- Default values applied: `growth_habit: "herb"`, `root_type: "fibrous"`, `allelopathy_score: 0.0`, `base_temp: 10.0`
- `common_names` defaults to empty list `[]`
- `hardiness_zones` defaults to empty list `[]`

**Postconditions**:
- Species exists with all defaults applied

**Tags**: [REQ-001, species, defaults, edge-case, api]

---

## 2. BotanicalFamily CRUD and Validation

### TC-REQ-001-012: Create a valid botanical family with all extended attributes

**Requirement**: REQ-001 -- Section 2 (Nodes: BotanicalFamily), Section 3 (BotanicalFamilyDefinition)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- System is running with empty or seeded `botanical_families` collection

**Test Steps**:
1. Send `POST /api/v1/botanical-families` with body:
   ```json
   {
     "name": "Solanaceae",
     "common_name_de": "Nachtschattengewaechse",
     "common_name_en": "Nightshade family",
     "order": "Solanales",
     "description": "Includes tomatoes, peppers, and eggplants",
     "typical_nutrient_demand": "heavy",
     "nitrogen_fixing": false,
     "typical_root_depth": "medium",
     "soil_ph_preference": {"min_ph": 5.5, "max_ph": 7.0},
     "frost_tolerance": "sensitive",
     "typical_growth_forms": ["herb", "shrub"],
     "common_pests": ["Kartoffelkaefer", "Blattlaeuse"],
     "common_diseases": ["Kraut- und Braunfaeule", "Fusarium"],
     "pollination_type": ["insect", "self"],
     "rotation_category": "fruiting"
   }
   ```

**Expected Results**:
- HTTP 201 Created
- All fields returned in response match the submitted values
- `key` is a generated non-empty string
- `created_at` is populated

**Postconditions**:
- BotanicalFamily document persisted in `botanical_families` collection

**Tags**: [REQ-001, botanical-family, crud, happy-path, api]

---

### TC-REQ-001-013: Reject family name not ending with "-aceae"

**Requirement**: REQ-001 -- Section 3 (BotanicalFamilyDefinition: validate_family_name)
**Priority**: Critical
**Category**: Error Handling
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/botanical-families` with `"name": "Nightshades"`
2. Send `POST /api/v1/botanical-families` with `"name": "Solanum"`
3. Send `POST /api/v1/botanical-families` with `"name": "Solanidae"`

**Expected Results**:
- All three: HTTP 422 Unprocessable Entity
- Error message: "Familienname '...' muss auf '-aceae' enden"

**Postconditions**:
- No families created

**Tags**: [REQ-001, botanical-family, validation, naming-convention, error-handling, api]

---

### TC-REQ-001-014: Reject order name not ending with "-ales"

**Requirement**: REQ-001 -- Section 3 (BotanicalFamilyDefinition: validate_order_name)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/botanical-families` with `"name": "Solanaceae"` and `"order": "Solanidae"`
2. Send `POST /api/v1/botanical-families` with `"name": "Solanaceae"` and `"order": "Nightshade"`

**Expected Results**:
- Both: HTTP 422 Unprocessable Entity
- Error message: "Ordnungsname '...' muss auf '-ales' enden"

**Postconditions**:
- No families created

**Tags**: [REQ-001, botanical-family, validation, naming-convention, error-handling, api]

---

### TC-REQ-001-015: Accept null order (taxonomic order is optional)

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily: `order: Optional[str]`)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/botanical-families` with `"name": "Solanaceae"` and `"order": null`
2. Send `POST /api/v1/botanical-families` with `"name": "Fabaceae"` and no `order` field at all

**Expected Results**:
- Both: HTTP 201 Created
- `order` is `null` in both responses

**Postconditions**:
- Two families created with `order: null`

**Tags**: [REQ-001, botanical-family, validation, optional-field, edge-case, api]

---

### TC-REQ-001-016: Reject nitrogen_fixing=true with heavy nutrient demand

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily: "nitrogen_fixing=true + typical_nutrient_demand='heavy' ist ungueltig"), Section 3 (validate_nitrogen_fixing_demand)
**Priority**: Critical
**Category**: Error Handling
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/botanical-families` with body:
   ```json
   {
     "name": "Fabaceae",
     "nitrogen_fixing": true,
     "typical_nutrient_demand": "heavy"
   }
   ```

**Expected Results**:
- HTTP 422 Unprocessable Entity
- Error message includes: "nitrogen_fixing=true ist inkompatibel mit typical_nutrient_demand='heavy'"

**Postconditions**:
- No family created

**Tags**: [REQ-001, botanical-family, validation, business-rule, nitrogen-fixing, error-handling, api]

---

### TC-REQ-001-017: Accept nitrogen_fixing=true with light or medium demand

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily), Section 3 (validate_nitrogen_fixing_demand)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/botanical-families` with `"name": "Fabaceae"`, `"nitrogen_fixing": true`, `"typical_nutrient_demand": "light"` -- expect HTTP 201
2. Send `POST /api/v1/botanical-families` with `"name": "Mimosaceae"`, `"nitrogen_fixing": true`, `"typical_nutrient_demand": "medium"` -- expect HTTP 201

**Expected Results**:
- Both: HTTP 201 Created
- Returned `nitrogen_fixing` is `true` and `typical_nutrient_demand` is `"light"` / `"medium"` respectively

**Postconditions**:
- Two nitrogen-fixing families exist

**Tags**: [REQ-001, botanical-family, validation, business-rule, nitrogen-fixing, happy-path, api]

---

### TC-REQ-001-018: PhRange validation -- min_ph must be <= max_ph

**Requirement**: REQ-001 -- Section 3 (PhRange: validate_ph_range)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- System is running

**Test Steps**:
1. Send `POST /api/v1/botanical-families` with `"name": "Ericaceae"` and `"soil_ph_preference": {"min_ph": 7.0, "max_ph": 4.5}` (inverted)
2. Send `POST /api/v1/botanical-families` with `"name": "Rosaceae"` and `"soil_ph_preference": {"min_ph": 6.0, "max_ph": 6.0}` (equal, valid)
3. Send `POST /api/v1/botanical-families` with `"name": "Poaceae"` and `"soil_ph_preference": {"min_ph": 5.5, "max_ph": 7.5}` (normal range)

**Expected Results**:
- Step 1: HTTP 422 -- error indicates max_ph must be >= min_ph
- Step 2: HTTP 201 -- equal values are accepted
- Step 3: HTTP 201 -- normal range accepted

**Postconditions**:
- Two valid families created (steps 2 and 3)

**Tags**: [REQ-001, botanical-family, validation, ph-range, boundary-value, api]

---

### TC-REQ-001-019: PhRange boundary values (3.0 to 9.0)

**Requirement**: REQ-001 -- Section 3 (PhRange: `min_ph: float = Field(ge=3.0, le=9.0)`, `max_ph: float = Field(ge=3.0, le=9.0)`)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- System is running

**Test Steps**:
1. Create family with `soil_ph_preference: {"min_ph": 3.0, "max_ph": 3.0}` -- expect HTTP 201
2. Create family with `soil_ph_preference: {"min_ph": 9.0, "max_ph": 9.0}` -- expect HTTP 201
3. Create family with `soil_ph_preference: {"min_ph": 2.9, "max_ph": 7.0}` -- expect HTTP 422
4. Create family with `soil_ph_preference: {"min_ph": 5.0, "max_ph": 9.1}` -- expect HTTP 422

**Expected Results**:
- Steps 1-2: HTTP 201 with exact boundary values persisted
- Steps 3-4: HTTP 422 with validation error for out-of-range pH

**Postconditions**:
- Two families with boundary pH values exist

**Tags**: [REQ-001, botanical-family, ph-range, boundary-value, edge-case, api]

---

### TC-REQ-001-020: List botanical families with pagination

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily CRUD)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- At least 9 botanical families exist (seed data)

**Test Steps**:
1. Send `GET /api/v1/botanical-families?offset=0&limit=5`
2. Send `GET /api/v1/botanical-families?offset=5&limit=5`

**Expected Results**:
- Step 1: Returns list of 5 families
- Step 2: Returns remaining families (up to 4 from 9 seed families)
- No duplicates between pages

**Postconditions**:
- No state change

**Tags**: [REQ-001, botanical-family, pagination, happy-path, api]

---

### TC-REQ-001-021: Update botanical family

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily CRUD)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- BotanicalFamily with key `solanaceae` exists

**Test Steps**:
1. Send `PUT /api/v1/botanical-families/solanaceae` with updated `common_diseases` list adding `"Verticillium"`
2. Send `GET /api/v1/botanical-families/solanaceae`

**Expected Results**:
- Step 1: HTTP 200, response contains updated `common_diseases` list
- Step 2: Confirms persistence of the update

**Postconditions**:
- Family document reflects updated diseases

**Tags**: [REQ-001, botanical-family, crud, update, happy-path, api]

---

### TC-REQ-001-022: Delete botanical family

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily CRUD)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- BotanicalFamily with key `test-delete` exists

**Test Steps**:
1. Send `DELETE /api/v1/botanical-families/test-delete`
2. Send `GET /api/v1/botanical-families/test-delete`

**Expected Results**:
- Step 1: HTTP 204 No Content
- Step 2: HTTP 404 Not Found

**Postconditions**:
- Family document removed

**Tags**: [REQ-001, botanical-family, crud, delete, happy-path, api]

---

### TC-REQ-001-023: Get non-existent botanical family returns 404

**Requirement**: REQ-001 -- Section 2 (BotanicalFamily), NFR-006
**Priority**: Medium
**Category**: Error Handling
**Preconditions**:
- No family with key `nonexistent-family` exists

**Test Steps**:
1. Send `GET /api/v1/botanical-families/nonexistent-family`

**Expected Results**:
- HTTP 404 Not Found

**Postconditions**:
- No state change

**Tags**: [REQ-001, botanical-family, error-handling, not-found, api]

---

## 3. Cultivar CRUD and Validation

### TC-REQ-001-024: Create a valid cultivar for a species

**Requirement**: REQ-001 -- Section 2 (Nodes: Cultivar, Edge: has_cultivar)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Species with key `tomato-01` exists

**Test Steps**:
1. Send `POST /api/v1/species/tomato-01/cultivars` with body:
   ```json
   {
     "name": "San Marzano",
     "species_key": "tomato-01",
     "breeder": "Italian Heritage",
     "breeding_year": 1926,
     "traits": ["heirloom", "disease_resistant"],
     "patent_status": "public_domain",
     "days_to_maturity": 80,
     "disease_resistances": ["Verticillium", "Fusarium"]
   }
   ```

**Expected Results**:
- HTTP 201 Created
- Response contains `key`, `name: "San Marzano"`, `species_key: "tomato-01"`
- `traits` contains `["heirloom", "disease_resistant"]`
- `days_to_maturity` equals 80

**Postconditions**:
- Cultivar document exists in `cultivars` collection
- `has_cultivar` edge connects `species/tomato-01` to the new cultivar

**Tags**: [REQ-001, cultivar, crud, happy-path, api]

---

### TC-REQ-001-025: Reject cultivar with invalid trait value

**Requirement**: REQ-001 -- Section 3 (CultivarDefinition: validate_traits, PlantTrait enum)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- Species with key `tomato-01` exists

**Test Steps**:
1. Send `POST /api/v1/species/tomato-01/cultivars` with body:
   ```json
   {
     "name": "Invalid Cultivar",
     "species_key": "tomato-01",
     "traits": ["disease_resistant", "super_power"]
   }
   ```

**Expected Results**:
- HTTP 422 Unprocessable Entity
- Error identifies `"super_power"` as an invalid trait value

**Postconditions**:
- No cultivar created

**Tags**: [REQ-001, cultivar, validation, enum, error-handling, api]

---

### TC-REQ-001-026: Days to maturity boundary values (1 to 365)

**Requirement**: REQ-001 -- Section 3 (CultivarDefinition: `days_to_maturity: Optional[int] = Field(None, ge=1, le=365)`)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- Species with key `tomato-01` exists

**Test Steps**:
1. Create cultivar with `days_to_maturity: 1` -- expect HTTP 201
2. Create cultivar with `days_to_maturity: 365` -- expect HTTP 201
3. Create cultivar with `days_to_maturity: 0` -- expect HTTP 422
4. Create cultivar with `days_to_maturity: 366` -- expect HTTP 422
5. Create cultivar with `days_to_maturity: null` -- expect HTTP 201

**Expected Results**:
- Steps 1, 2, 5: HTTP 201, values stored correctly (null for step 5)
- Steps 3, 4: HTTP 422, validation error

**Postconditions**:
- Three valid cultivars created

**Tags**: [REQ-001, cultivar, boundary-value, days-to-maturity, edge-case, api]

---

### TC-REQ-001-027: List cultivars for a species

**Requirement**: REQ-001 -- Section 2 (Cultivar, has_cultivar edge), Section 5 (DoD: min 3 cultivars per common species)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Species `tomato-01` has at least 3 cultivars ("San Marzano", "Roma", "Cherry")

**Test Steps**:
1. Send `GET /api/v1/species/tomato-01/cultivars`

**Expected Results**:
- HTTP 200
- Response is a list with at least 3 cultivar objects
- Each cultivar has `species_key: "tomato-01"`

**Postconditions**:
- No state change

**Tags**: [REQ-001, cultivar, list, acceptance-criteria, api]

---

### TC-REQ-001-028: Update a cultivar

**Requirement**: REQ-001 -- Section 2 (Cultivar CRUD)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Cultivar with key `san-marzano-01` exists under species `tomato-01`

**Test Steps**:
1. Send `PUT /api/v1/species/tomato-01/cultivars/san-marzano-01` with updated `traits: ["heirloom", "disease_resistant", "high_yield"]`
2. Send `GET /api/v1/species/tomato-01/cultivars/san-marzano-01`

**Expected Results**:
- Step 1: HTTP 200, response shows 3 traits
- Step 2: Confirms persistence

**Postconditions**:
- Cultivar document updated

**Tags**: [REQ-001, cultivar, crud, update, happy-path, api]

---

### TC-REQ-001-029: Delete a cultivar

**Requirement**: REQ-001 -- Section 2 (Cultivar CRUD)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Cultivar with key `delete-me-cv` exists under species `tomato-01`

**Test Steps**:
1. Send `DELETE /api/v1/species/tomato-01/cultivars/delete-me-cv`
2. Send `GET /api/v1/species/tomato-01/cultivars/delete-me-cv`

**Expected Results**:
- Step 1: HTTP 204 No Content
- Step 2: HTTP 404 Not Found

**Postconditions**:
- Cultivar removed, `has_cultivar` edge also removed

**Tags**: [REQ-001, cultivar, crud, delete, happy-path, api]

---

## 4. LifecycleConfig and Biennial/Perennial Logic

### TC-REQ-001-030: Create annual lifecycle configuration

**Requirement**: REQ-001 -- Section 2 (Nodes: LifecycleConfig), Section 3 (CycleType)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Species with key `basil-01` exists

**Test Steps**:
1. Send `POST /api/v1/species/basil-01/lifecycle` with body:
   ```json
   {
     "species_key": "basil-01",
     "cycle_type": "annual",
     "dormancy_required": false,
     "vernalization_required": false,
     "photoperiod_type": "short_day",
     "critical_day_length_hours": 14.0
   }
   ```

**Expected Results**:
- HTTP 201 Created
- `cycle_type: "annual"`, `dormancy_required: false`, `vernalization_required: false`
- `critical_day_length_hours: 14.0`

**Postconditions**:
- LifecycleConfig document exists, linked to species via `has_lifecycle` edge

**Tags**: [REQ-001, lifecycle, annual, crud, happy-path, api]

---

### TC-REQ-001-031: Reject biennial lifecycle without vernalization_required

**Requirement**: REQ-001 -- Section 3 (validate_biennial_vernalization: "Biennial plants must have vernalization_required=True")
**Priority**: Critical
**Category**: Error Handling
**Preconditions**:
- Species with key `parsley-01` exists

**Test Steps**:
1. Send `POST /api/v1/species/parsley-01/lifecycle` with body:
   ```json
   {
     "species_key": "parsley-01",
     "cycle_type": "biennial",
     "vernalization_required": false
   }
   ```

**Expected Results**:
- HTTP 422 Unprocessable Entity
- Error message: "Biennial plants must have vernalization_required=True"

**Postconditions**:
- No lifecycle config created

**Tags**: [REQ-001, lifecycle, biennial, vernalization, validation, error-handling, api]

---

### TC-REQ-001-032: Create valid biennial lifecycle with vernalization

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig), Section 3 (validate_biennial_vernalization)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Species with key `parsley-01` exists

**Test Steps**:
1. Send `POST /api/v1/species/parsley-01/lifecycle` with body:
   ```json
   {
     "species_key": "parsley-01",
     "cycle_type": "biennial",
     "vernalization_required": true,
     "vernalization_min_days": 45,
     "photoperiod_type": "long_day",
     "critical_day_length_hours": 14.0
   }
   ```

**Expected Results**:
- HTTP 201 Created
- `cycle_type: "biennial"`, `vernalization_required: true`, `vernalization_min_days: 45`

**Postconditions**:
- LifecycleConfig for biennial species persisted

**Tags**: [REQ-001, lifecycle, biennial, vernalization, happy-path, api]

---

### TC-REQ-001-033: Create perennial lifecycle with dormancy

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig), Section 1 (Perennial description)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Species with key `strawberry-01` exists

**Test Steps**:
1. Send `POST /api/v1/species/strawberry-01/lifecycle` with body:
   ```json
   {
     "species_key": "strawberry-01",
     "cycle_type": "perennial",
     "typical_lifespan_years": 5,
     "dormancy_required": true,
     "vernalization_required": false,
     "photoperiod_type": "day_neutral"
   }
   ```

**Expected Results**:
- HTTP 201 Created
- `cycle_type: "perennial"`, `dormancy_required: true`, `typical_lifespan_years: 5`

**Postconditions**:
- LifecycleConfig for perennial species persisted

**Tags**: [REQ-001, lifecycle, perennial, dormancy, happy-path, api]

---

### TC-REQ-001-034: Critical day length boundary values (0 to 24 hours)

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig: `critical_day_length_hours: Optional[float] = Field(None, ge=0, le=24)`)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- Species exists

**Test Steps**:
1. Create lifecycle with `critical_day_length_hours: 0.0` -- expect HTTP 201
2. Create lifecycle with `critical_day_length_hours: 24.0` -- expect HTTP 201
3. Create lifecycle with `critical_day_length_hours: -0.1` -- expect HTTP 422
4. Create lifecycle with `critical_day_length_hours: 24.1` -- expect HTTP 422

**Expected Results**:
- Steps 1-2: HTTP 201
- Steps 3-4: HTTP 422

**Postconditions**:
- Two valid configs created

**Tags**: [REQ-001, lifecycle, boundary-value, photoperiod, edge-case, api]

---

### TC-REQ-001-035: Update lifecycle configuration

**Requirement**: REQ-001 -- Section 2 (LifecycleConfig CRUD)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- LifecycleConfig with key `lc-01` exists for species `basil-01`, currently `photoperiod_type: "day_neutral"`

**Test Steps**:
1. Send `PUT /api/v1/species/basil-01/lifecycle/lc-01` with `"photoperiod_type": "short_day"`, `"critical_day_length_hours": 12.5`
2. Send `GET /api/v1/species/basil-01/lifecycle`

**Expected Results**:
- Step 1: HTTP 200, `photoperiod_type: "short_day"`
- Step 2: Confirms `critical_day_length_hours: 12.5`

**Postconditions**:
- LifecycleConfig updated

**Tags**: [REQ-001, lifecycle, crud, update, happy-path, api]

---

## 5. GrowthPhase Management

### TC-REQ-001-036: Create growth phases with correct sequence order

**Requirement**: REQ-001 -- Section 2 (Nodes: GrowthPhase, Edge: consists_of with sequence), Section 5 (DoD: min 3 GrowthPhases per LifecycleConfig)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- LifecycleConfig with key `lc-tomato` exists

**Test Steps**:
1. Send `POST /api/v1/growth-phases` with `"name": "germination"`, `"lifecycle_key": "lc-tomato"`, `"sequence_order": 0`, `"typical_duration_days": 10`
2. Send `POST /api/v1/growth-phases` with `"name": "vegetative"`, `"lifecycle_key": "lc-tomato"`, `"sequence_order": 1`, `"typical_duration_days": 30`
3. Send `POST /api/v1/growth-phases` with `"name": "flowering"`, `"lifecycle_key": "lc-tomato"`, `"sequence_order": 2`, `"typical_duration_days": 45`, `"is_terminal": false`, `"allows_harvest": false`
4. Send `POST /api/v1/growth-phases` with `"name": "harvest"`, `"lifecycle_key": "lc-tomato"`, `"sequence_order": 3`, `"typical_duration_days": 14`, `"is_terminal": true`, `"allows_harvest": true`
5. Send `GET /api/v1/growth-phases?lifecycle_key=lc-tomato`

**Expected Results**:
- Steps 1-4: HTTP 201 for each
- Step 5: Returns 4 phases, ordered by `sequence_order` (0, 1, 2, 3)
- Terminal phase (`harvest`) has `is_terminal: true` and `allows_harvest: true`

**Postconditions**:
- Four GrowthPhase documents linked to `lc-tomato` via `consists_of` edges

**Tags**: [REQ-001, growth-phase, crud, sequence, happy-path, api]

---

### TC-REQ-001-037: Reject growth phase with typical_duration_days < 1

**Requirement**: REQ-001 -- Section 2 (GrowthPhase: `typical_duration_days: int = Field(ge=1)`)
**Priority**: Medium
**Category**: Error Handling
**Preconditions**:
- LifecycleConfig exists

**Test Steps**:
1. Send `POST /api/v1/growth-phases` with `"typical_duration_days": 0`
2. Send `POST /api/v1/growth-phases` with `"typical_duration_days": -5`

**Expected Results**:
- Both: HTTP 422, validation error for minimum value of 1

**Postconditions**:
- No phases created

**Tags**: [REQ-001, growth-phase, validation, boundary-value, error-handling, api]

---

### TC-REQ-001-038: Update a growth phase

**Requirement**: REQ-001 -- Section 2 (GrowthPhase CRUD)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- GrowthPhase with key `gp-01` exists with `typical_duration_days: 30`

**Test Steps**:
1. Send `PUT /api/v1/growth-phases/gp-01` with `"typical_duration_days": 35`, `"stress_tolerance": "high"`
2. Send `GET /api/v1/growth-phases/gp-01`

**Expected Results**:
- Step 1: HTTP 200, updated values returned
- Step 2: Confirms `typical_duration_days: 35` and `stress_tolerance: "high"`

**Postconditions**:
- GrowthPhase document updated

**Tags**: [REQ-001, growth-phase, crud, update, happy-path, api]

---

### TC-REQ-001-039: Delete a growth phase

**Requirement**: REQ-001 -- Section 2 (GrowthPhase CRUD)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- GrowthPhase with key `gp-delete` exists

**Test Steps**:
1. Send `DELETE /api/v1/growth-phases/gp-delete`
2. Send `GET /api/v1/growth-phases/gp-delete`

**Expected Results**:
- Step 1: HTTP 204
- Step 2: HTTP 404

**Postconditions**:
- GrowthPhase and associated `consists_of` edge removed

**Tags**: [REQ-001, growth-phase, crud, delete, happy-path, api]

---

## 6. Companion Planting (Species-Level Edges)

### TC-REQ-001-040: Set species-level compatibility edge

**Requirement**: REQ-001 -- Section 2 (Edge: compatible_with, compatibility_score 0.0-1.0)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Species `tomato-01` and `basil-01` exist

**Test Steps**:
1. Send `POST /api/v1/companion-planting/compatible` with body:
   ```json
   {
     "from_species_key": "tomato-01",
     "to_species_key": "basil-01",
     "score": 0.9
   }
   ```
2. Send `GET /api/v1/companion-planting/species/tomato-01/compatible`

**Expected Results**:
- Step 1: HTTP 201, `{"status": "created"}`
- Step 2: Response includes basil with `score: 0.9`

**Postconditions**:
- `compatible_with` edge exists between tomato and basil in the graph

**Tags**: [REQ-001, companion-planting, compatible, species-level, happy-path, api, graph]

---

### TC-REQ-001-041: Set species-level incompatibility edge

**Requirement**: REQ-001 -- Section 2 (Edge: incompatible_with, reason: str)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Species `tomato-01` and `fennel-01` exist

**Test Steps**:
1. Send `POST /api/v1/companion-planting/incompatible` with body:
   ```json
   {
     "from_species_key": "tomato-01",
     "to_species_key": "fennel-01",
     "reason": "Allelopathic compounds inhibit tomato growth"
   }
   ```
2. Send `GET /api/v1/companion-planting/species/tomato-01/incompatible`

**Expected Results**:
- Step 1: HTTP 201
- Step 2: Response includes fennel with the allelopathy reason

**Postconditions**:
- `incompatible_with` edge exists

**Tags**: [REQ-001, companion-planting, incompatible, species-level, happy-path, api, graph]

---

### TC-REQ-001-042: Query compatible species for a species with no edges returns empty

**Requirement**: REQ-001 -- Section 2 (compatible_with edge)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- Species `isolated-01` exists with no `compatible_with` edges

**Test Steps**:
1. Send `GET /api/v1/companion-planting/species/isolated-01/compatible`

**Expected Results**:
- HTTP 200
- Response is an empty list `[]`

**Postconditions**:
- No state change

**Tags**: [REQ-001, companion-planting, empty-result, edge-case, api, graph]

---

## 7. Crop Rotation Edges

### TC-REQ-001-043: Set rotation successor between families

**Requirement**: REQ-001 -- Section 2 (Edge: rotation_after), Section 5 (DoD: min 16 rotation_after edges)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- BotanicalFamilies `fabaceae` and `solanaceae` exist

**Test Steps**:
1. Send `POST /api/v1/crop-rotation/successors` with body:
   ```json
   {
     "from_family_key": "fabaceae",
     "to_family_key": "solanaceae",
     "wait_years": 3
   }
   ```
2. Send `GET /api/v1/crop-rotation/families/solanaceae/successors`

**Expected Results**:
- Step 1: HTTP 201, `{"status": "created"}`
- Step 2: Response includes Fabaceae as a rotation successor after Solanaceae

**Postconditions**:
- `rotation_after` edge: Fabaceae -> Solanaceae (Fabaceae is good successor after Solanaceae)

**Tags**: [REQ-001, crop-rotation, rotation-after, happy-path, api, graph]

---

### TC-REQ-001-044: Query rotation successors for family with no edges returns empty

**Requirement**: REQ-001 -- Section 2 (rotation_after edge)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- BotanicalFamily `orphan-family` exists with no `rotation_after` edges

**Test Steps**:
1. Send `GET /api/v1/crop-rotation/families/orphan-family/successors`

**Expected Results**:
- HTTP 200
- Empty list or empty result set

**Postconditions**:
- No state change

**Tags**: [REQ-001, crop-rotation, empty-result, edge-case, api, graph]

---

## 8. Dormancy Trigger Logic (Engine/Calculator)

### TC-REQ-001-045: Temperature-triggered dormancy with sufficient cold days

**Requirement**: REQ-001 -- Section 3 (DormancyTrigger: is_triggered, trigger_type='temperature'), Section 5 (Szenario 3)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- DormancyTrigger configured: `trigger_type: "temperature"`, `temperature_threshold_c: 5.0`, `consecutive_days_required: 7`
- 7 sensor observations available, all with `temperature_c < 5.0`

**Test Steps**:
1. Call `DormancyTrigger.is_triggered(observations=[{"temperature_c": 3.0}, {"temperature_c": 2.5}, {"temperature_c": 4.0}, {"temperature_c": 1.0}, {"temperature_c": 3.5}, {"temperature_c": 4.5}, {"temperature_c": 2.0}], current_daylight_hours=9.0)`

**Expected Results**:
- Returns `(True, "Temperatur < 5.0 C fuer 7 Tage")` (or equivalent message)
- Dormancy is triggered

**Postconditions**:
- System should transition perennial plant to dormancy state

**Tags**: [REQ-001, dormancy, temperature-trigger, engine, happy-path, unit-test]

---

### TC-REQ-001-046: Temperature-triggered dormancy NOT triggered when one day is warm

**Requirement**: REQ-001 -- Section 3 (DormancyTrigger: consecutive_days_required)
**Priority**: High
**Category**: Edge Case
**Preconditions**:
- DormancyTrigger: `trigger_type: "temperature"`, `temperature_threshold_c: 5.0`, `consecutive_days_required: 7`
- 7 observations where 6 are below threshold but day 4 is 6.0 C (above threshold)

**Test Steps**:
1. Call `is_triggered(observations=[{"temperature_c": 3.0}, {"temperature_c": 2.5}, {"temperature_c": 4.0}, {"temperature_c": 6.0}, {"temperature_c": 3.5}, {"temperature_c": 4.5}, {"temperature_c": 2.0}], current_daylight_hours=9.0)`

**Expected Results**:
- Returns `(False, "Bedingungen nicht erfuellt")`
- Dormancy NOT triggered because not ALL consecutive days are below threshold

**Postconditions**:
- Plant remains in active state

**Tags**: [REQ-001, dormancy, temperature-trigger, edge-case, engine, unit-test]

---

### TC-REQ-001-047: Temperature-triggered dormancy with insufficient data

**Requirement**: REQ-001 -- Section 3 (DormancyTrigger: "Nicht genuegend Temperatur-Daten")
**Priority**: High
**Category**: Edge Case
**Preconditions**:
- DormancyTrigger: `trigger_type: "temperature"`, `consecutive_days_required: 7`
- Only 5 observations available

**Test Steps**:
1. Call `is_triggered(observations=[5 cold entries], current_daylight_hours=9.0)`

**Expected Results**:
- Returns `(False, "Nicht genuegend Temperatur-Daten")`

**Postconditions**:
- Dormancy not triggered; system waits for more data

**Tags**: [REQ-001, dormancy, insufficient-data, edge-case, engine, unit-test]

---

### TC-REQ-001-048: Photoperiod-triggered dormancy

**Requirement**: REQ-001 -- Section 3 (DormancyTrigger: trigger_type='photoperiod')
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- DormancyTrigger: `trigger_type: "photoperiod"`, `photoperiod_threshold_hours: 10.0`
- `current_daylight_hours: 9.5` (below threshold)

**Test Steps**:
1. Call `is_triggered(observations=[], current_daylight_hours=9.5)`

**Expected Results**:
- Returns `(True, "Tageslaenge < 10.0h")`

**Postconditions**:
- Dormancy triggered by short day length

**Tags**: [REQ-001, dormancy, photoperiod-trigger, happy-path, engine, unit-test]

---

### TC-REQ-001-049: Photoperiod dormancy NOT triggered when day is long enough

**Requirement**: REQ-001 -- Section 3 (DormancyTrigger: photoperiod_threshold_hours)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- DormancyTrigger: `trigger_type: "photoperiod"`, `photoperiod_threshold_hours: 10.0`
- `current_daylight_hours: 10.5`

**Test Steps**:
1. Call `is_triggered(observations=[], current_daylight_hours=10.5)`

**Expected Results**:
- Returns `(False, "Bedingungen nicht erfuellt")`

**Postconditions**:
- No dormancy triggered

**Tags**: [REQ-001, dormancy, photoperiod-trigger, edge-case, engine, unit-test]

---

### TC-REQ-001-050: Manual dormancy trigger always returns false

**Requirement**: REQ-001 -- Section 3 (DormancyTrigger: trigger_type='manual')
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- DormancyTrigger: `trigger_type: "manual"`

**Test Steps**:
1. Call `is_triggered(observations=[any data], current_daylight_hours=5.0)`

**Expected Results**:
- Returns `(False, "Manuelle Steuerung aktiv")`
- Manual triggers are controlled externally, not auto-triggered

**Postconditions**:
- No automatic dormancy transition

**Tags**: [REQ-001, dormancy, manual-trigger, happy-path, engine, unit-test]

---

### TC-REQ-001-051: DormancyTrigger validation -- temperature trigger requires threshold

**Requirement**: REQ-001 -- Section 3 (DormancyTrigger: validate_temp_trigger)
**Priority**: High
**Category**: Error Handling
**Preconditions**:
- None

**Test Steps**:
1. Construct `DormancyTrigger(trigger_type="temperature", temperature_threshold_c=None)`

**Expected Results**:
- Pydantic ValidationError raised
- Error: "Temperatur-Schwelle erforderlich fuer temperature-Trigger"

**Postconditions**:
- Object not created

**Tags**: [REQ-001, dormancy, validation, error-handling, unit-test]

---

### TC-REQ-001-052: Temperature threshold boundary values (-20 to 25)

**Requirement**: REQ-001 -- Section 3 (DormancyTrigger: `temperature_threshold_c: Optional[float] = Field(None, ge=-20, le=25)`)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- None

**Test Steps**:
1. Construct with `temperature_threshold_c: -20.0` -- expect success
2. Construct with `temperature_threshold_c: 25.0` -- expect success
3. Construct with `temperature_threshold_c: -20.1` -- expect ValidationError
4. Construct with `temperature_threshold_c: 25.1` -- expect ValidationError

**Expected Results**:
- Steps 1-2: Valid DormancyTrigger object created
- Steps 3-4: Pydantic ValidationError

**Postconditions**:
- Only valid objects exist

**Tags**: [REQ-001, dormancy, boundary-value, temperature, edge-case, unit-test]

---

## 9. Vernalization Tracker Logic

### TC-REQ-001-053: Vernalization completes after required cold days

**Requirement**: REQ-001 -- Section 3 (VernalizationTracker: update method), Section 5 (Szenario 2)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- VernalizationTracker: `required_days: 45`, `temperature_range: (0.0, 10.0)`, `accumulated_days: 0`

**Test Steps**:
1. Call `update(current_temp=5.0, observation_date=date(2026, 1, 1))` -- day 1
2. Repeat with temps in range [0.0, 10.0] for days 2-44, incrementing observation_date
3. Call `update(current_temp=7.0, observation_date=date(2026, 2, 14))` -- day 45

**Expected Results**:
- Steps 1-44: Returns `status: "in_progress"`, `progress_percent` increments from ~2.2% to ~97.8%
- Step 3 (day 45): Returns `status: "completed"`, `progress_percent: 100.0`, `completed_on: date(2026, 2, 14)`
- `start_date` set to `date(2026, 1, 1)`

**Postconditions**:
- Tracker shows completed state; biennial plant is ready for flowering phase

**Tags**: [REQ-001, vernalization, completion, happy-path, engine, unit-test]

---

### TC-REQ-001-054: Vernalization does not count warm days

**Requirement**: REQ-001 -- Section 3 (VernalizationTracker: temp_in_range check)
**Priority**: High
**Category**: Edge Case
**Preconditions**:
- VernalizationTracker: `required_days: 10`, `temperature_range: (0.0, 10.0)`, `accumulated_days: 5`

**Test Steps**:
1. Call `update(current_temp=15.0, observation_date=date(2026, 1, 6))` -- warm day

**Expected Results**:
- `status: "in_progress"`, `accumulated_days: 5` (unchanged), `remaining_days: 5`
- Warm day does not increment the counter

**Postconditions**:
- Tracker not advanced

**Tags**: [REQ-001, vernalization, warm-day, edge-case, engine, unit-test]

---

### TC-REQ-001-055: Vernalization already completed returns completed status

**Requirement**: REQ-001 -- Section 3 (VernalizationTracker: early return when completion_date set)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- VernalizationTracker: `completion_date: date(2026, 2, 14)`, `required_days: 45`, `accumulated_days: 45`

**Test Steps**:
1. Call `update(current_temp=5.0, observation_date=date(2026, 2, 15))` -- day after completion

**Expected Results**:
- Returns `status: "completed"`, `progress_percent: 100.0`, `completed_on: date(2026, 2, 14)`
- Does not advance `accumulated_days` beyond 45

**Postconditions**:
- No state change

**Tags**: [REQ-001, vernalization, already-completed, edge-case, engine, unit-test]

---

### TC-REQ-001-056: Vernalization progress percentage calculation

**Requirement**: REQ-001 -- Section 3 (VernalizationTracker: progress calculation)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- VernalizationTracker: `required_days: 100`, `accumulated_days: 0`

**Test Steps**:
1. Call `update(current_temp=5.0, ...)` -- first cold day
2. Verify progress after 1 day
3. Call updates for 49 more days (total 50)
4. Verify progress at halfway point

**Expected Results**:
- After day 1: `progress_percent: 1.0`
- After day 50: `progress_percent: 50.0`
- `remaining_days` equals `required_days - accumulated_days`

**Postconditions**:
- Tracker at 50% progress

**Tags**: [REQ-001, vernalization, progress, happy-path, engine, unit-test]

---

### TC-REQ-001-057: Vernalization with required_days=0 is immediately satisfied

**Requirement**: REQ-001 -- Section 3 (VernalizationTracker: edge case with 0 required days)
**Priority**: Low
**Category**: Edge Case
**Preconditions**:
- VernalizationTracker: `required_days: 0`, `accumulated_days: 0`

**Test Steps**:
1. Call `update(current_temp=5.0, observation_date=date(2026, 1, 1))`

**Expected Results**:
- Returns `status: "completed"` or `progress_percent: 100.0` (since accumulated_days >= required_days after one cold day increment, or progress calculation handles 0-division)
- Note: The spec shows `progress = (accumulated / required * 100) if required > 0 else 0`, so with required=0 and accumulated=0, progress is 0; but after one cold day, accumulated=1 >= required=0, so completion triggers.

**Postconditions**:
- Tracker completed

**Tags**: [REQ-001, vernalization, zero-days, edge-case, engine, unit-test]

---

### TC-REQ-001-058: Vernalization boundary -- temperature exactly at range boundaries

**Requirement**: REQ-001 -- Section 3 (VernalizationTracker: `temperature_range[0] <= current_temp <= temperature_range[1]`)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- VernalizationTracker: `required_days: 10`, `temperature_range: (0.0, 10.0)`, `accumulated_days: 0`

**Test Steps**:
1. Call `update(current_temp=0.0, ...)` -- lower boundary, inclusive
2. Call `update(current_temp=10.0, ...)` -- upper boundary, inclusive
3. Call `update(current_temp=-0.1, ...)` -- just below lower boundary
4. Call `update(current_temp=10.1, ...)` -- just above upper boundary

**Expected Results**:
- Steps 1-2: `accumulated_days` increments (boundaries are inclusive per `<=` operator)
- Steps 3-4: `accumulated_days` does NOT increment

**Postconditions**:
- Tracker shows `accumulated_days: 2` (only steps 1 and 2 counted)

**Tags**: [REQ-001, vernalization, boundary-value, temperature-range, edge-case, engine, unit-test]

---

## 10. Photoperiod Calculator Logic

### TC-REQ-001-059: Calculate day length for summer solstice at 50 N

**Requirement**: REQ-001 -- Section 3 (PhotoperiodCalculator: calculate_day_length, Forsythe formula)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- None (pure calculation)

**Test Steps**:
1. Call `PhotoperiodCalculator.calculate_day_length(latitude=50.0, observation_date=date(2026, 6, 21))`

**Expected Results**:
- Returns approximately 16.3-16.5 hours (summer solstice at 50 N latitude)
- Value is a float rounded to 2 decimal places

**Postconditions**:
- No state change (pure function)

**Tags**: [REQ-001, photoperiod, day-length, summer-solstice, happy-path, calculator, unit-test]

---

### TC-REQ-001-060: Calculate day length for winter solstice at 50 N

**Requirement**: REQ-001 -- Section 3 (PhotoperiodCalculator)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- None

**Test Steps**:
1. Call `calculate_day_length(latitude=50.0, observation_date=date(2026, 12, 21))`

**Expected Results**:
- Returns approximately 7.8-8.1 hours (winter solstice at 50 N)

**Postconditions**:
- No state change

**Tags**: [REQ-001, photoperiod, day-length, winter-solstice, happy-path, calculator, unit-test]

---

### TC-REQ-001-061: Polar night at extreme latitude

**Requirement**: REQ-001 -- Section 3 (PhotoperiodCalculator: `cos_hour_angle > 1` returns 0.0)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- None

**Test Steps**:
1. Call `calculate_day_length(latitude=85.0, observation_date=date(2026, 12, 21))`

**Expected Results**:
- Returns `0.0` (polar night -- no daylight)

**Postconditions**:
- No state change

**Tags**: [REQ-001, photoperiod, polar-night, edge-case, calculator, unit-test]

---

### TC-REQ-001-062: Midnight sun at extreme latitude

**Requirement**: REQ-001 -- Section 3 (PhotoperiodCalculator: `cos_hour_angle < -1` returns 24.0)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- None

**Test Steps**:
1. Call `calculate_day_length(latitude=85.0, observation_date=date(2026, 6, 21))`

**Expected Results**:
- Returns `24.0` (midnight sun -- continuous daylight)

**Postconditions**:
- No state change

**Tags**: [REQ-001, photoperiod, midnight-sun, edge-case, calculator, unit-test]

---

### TC-REQ-001-063: Equator has approximately 12 hours year-round

**Requirement**: REQ-001 -- Section 3 (PhotoperiodCalculator)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- None

**Test Steps**:
1. Call `calculate_day_length(latitude=0.0, observation_date=date(2026, 3, 20))` (equinox)
2. Call `calculate_day_length(latitude=0.0, observation_date=date(2026, 6, 21))` (solstice)
3. Call `calculate_day_length(latitude=0.0, observation_date=date(2026, 12, 21))` (solstice)

**Expected Results**:
- All three return approximately 12.0 hours (within +/- 0.2h tolerance)

**Postconditions**:
- No state change

**Tags**: [REQ-001, photoperiod, equator, happy-path, calculator, unit-test]

---

### TC-REQ-001-064: Critical photoperiod detection for short-day plant

**Requirement**: REQ-001 -- Section 3 (is_critical_photoperiod: short_day logic), Section 5 (Szenario 4)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Cannabis sativa: `photoperiod_type: "short_day"`, `critical_day_length: 14.0`

**Test Steps**:
1. Call `is_critical_photoperiod(current_day_length=13.5, photoperiod_type="short_day", critical_day_length=14.0)`
2. Call `is_critical_photoperiod(current_day_length=14.5, photoperiod_type="short_day", critical_day_length=14.0)`
3. Call `is_critical_photoperiod(current_day_length=14.0, photoperiod_type="short_day", critical_day_length=14.0)`

**Expected Results**:
- Step 1: `(True, "Tageslaenge 13.5h < kritisch 14.0h")` -- flower trigger active
- Step 2: `(False, "Tageslaenge 14.5h >= kritisch 14.0h")` -- still vegetative
- Step 3: `(False, ...)` -- exactly at threshold, NOT triggered (uses `<` not `<=`)

**Postconditions**:
- No state change (pure function)

**Tags**: [REQ-001, photoperiod, short-day, critical-photoperiod, happy-path, calculator, unit-test]

---

### TC-REQ-001-065: Critical photoperiod detection for long-day plant

**Requirement**: REQ-001 -- Section 3 (is_critical_photoperiod: long_day logic)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Long-day plant with `critical_day_length: 14.0`

**Test Steps**:
1. Call `is_critical_photoperiod(current_day_length=15.0, photoperiod_type="long_day", critical_day_length=14.0)`
2. Call `is_critical_photoperiod(current_day_length=13.0, photoperiod_type="long_day", critical_day_length=14.0)`
3. Call `is_critical_photoperiod(current_day_length=14.0, photoperiod_type="long_day", critical_day_length=14.0)`

**Expected Results**:
- Step 1: `(True, ...)` -- flower trigger active (day is long enough)
- Step 2: `(False, ...)` -- day too short
- Step 3: `(False, ...)` -- exactly at threshold, NOT triggered (uses `>` not `>=`)

**Postconditions**:
- No state change

**Tags**: [REQ-001, photoperiod, long-day, critical-photoperiod, happy-path, calculator, unit-test]

---

### TC-REQ-001-066: Day-neutral plant always returns True

**Requirement**: REQ-001 -- Section 3 (is_critical_photoperiod: day_neutral returns True)
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Day-neutral plant

**Test Steps**:
1. Call `is_critical_photoperiod(current_day_length=8.0, photoperiod_type="day_neutral", critical_day_length=None)`
2. Call `is_critical_photoperiod(current_day_length=16.0, photoperiod_type="day_neutral", critical_day_length=None)`

**Expected Results**:
- Both: `(True, "Tagneutrale Pflanze - Photoperiode irrelevant")`

**Postconditions**:
- No state change

**Tags**: [REQ-001, photoperiod, day-neutral, happy-path, calculator, unit-test]

---

### TC-REQ-001-067: Photoperiod with undefined critical day length

**Requirement**: REQ-001 -- Section 3 (is_critical_photoperiod: `critical_day_length is None`)
**Priority**: Medium
**Category**: Edge Case
**Preconditions**:
- Short-day plant with `critical_day_length: None`

**Test Steps**:
1. Call `is_critical_photoperiod(current_day_length=12.0, photoperiod_type="short_day", critical_day_length=None)`

**Expected Results**:
- Returns `(False, "Kritische Tageslaenge nicht definiert")`

**Postconditions**:
- No state change

**Tags**: [REQ-001, photoperiod, missing-config, edge-case, calculator, unit-test]

---

## 11. Acceptance Scenarios from Specification Section 5

### TC-REQ-001-068: Annual plant full lifecycle (Szenario 1 -- Basilikum)

**Requirement**: REQ-001 -- Section 5 (Szenario 1: Einjaehrige Pflanze - Vollstaendiger Zyklus)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Species "Ocimum basilicum" (basil) exists as annual, short-day plant
- LifecycleConfig with `cycle_type: "annual"` linked to basil
- GrowthPhases: Germination (seq 0), Vegetative (seq 1), Flowering (seq 2), Seed (seq 3, is_terminal=true)
- No dormancy phase configured for this annual species

**Test Steps**:
1. Create basil species with annual lifecycle
2. Create 4 growth phases in sequence
3. Verify that no dormancy phase exists in the phase list
4. Verify `is_terminal: true` only on the final "seed" phase
5. Verify lifecycle has `dormancy_required: false`

**Expected Results**:
- Phase list contains exactly 4 phases ordered by `sequence_order`
- No phase named "dormancy" or similar
- Terminal phase marks end of lifecycle
- System can identify when lifecycle is complete (terminal phase reached)

**Postconditions**:
- Complete annual lifecycle template ready for plant instance usage

**Tags**: [REQ-001, acceptance-scenario, annual, basil, lifecycle-complete, e2e]

---

### TC-REQ-001-069: Biennial with vernalization tracking (Szenario 2 -- Petersilie)

**Requirement**: REQ-001 -- Section 5 (Szenario 2: Zweijaehrige mit Vernalisation)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Species "Petroselinum crispum" (parsley) exists as biennial
- LifecycleConfig: `cycle_type: "biennial"`, `vernalization_required: true`, `vernalization_min_days: 45`
- VernalizationTracker initialized with `required_days: 45`, `temperature_range: (0.0, 10.0)`

**Test Steps**:
1. Create parsley species and biennial lifecycle config
2. Initialize VernalizationTracker
3. Feed 45 days of cold observations (all within 0-10 C range)
4. Check tracker status after day 45

**Expected Results**:
- Lifecycle creation succeeds (biennial + vernalization_required=true)
- After 45 cold days: `status: "completed"`, `progress_percent: 100.0`
- System recognizes that parsley is ready for second-year flowering phase

**Postconditions**:
- Vernalization complete; flowering phase can be activated

**Tags**: [REQ-001, acceptance-scenario, biennial, parsley, vernalization, e2e]

See also: TC-REQ-001-053 for detailed vernalization unit tests

---

### TC-REQ-001-070: Perennial dormancy trigger (Szenario 3 -- Erdbeere)

**Requirement**: REQ-001 -- Section 5 (Szenario 3: Mehrjaehrige Dormanz)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Species "Fragaria x ananassa" (strawberry) exists as perennial
- LifecycleConfig: `cycle_type: "perennial"`, `dormancy_required: true`
- DormancyTrigger: `trigger_type: "temperature"`, `temperature_threshold_c: 5.0`, `consecutive_days_required: 7`

**Test Steps**:
1. Create strawberry species with perennial lifecycle
2. Configure DormancyTrigger
3. Provide 7 consecutive observations all below 5.0 C (November scenario)
4. Call `is_triggered()`

**Expected Results**:
- Returns `(True, "Temperatur < 5.0 C fuer 7 Tage")`
- System should pause watering/fertilizing tasks (cross-reference REQ-006)
- System should plan reactivation for spring (cross-reference to location climate zone)

**Postconditions**:
- Plant enters dormancy state

**Tags**: [REQ-001, acceptance-scenario, perennial, strawberry, dormancy, e2e]

See also: TC-REQ-001-045 for detailed dormancy trigger unit tests

---

### TC-REQ-001-071: Photoperiod-triggered flowering (Szenario 4 -- Cannabis)

**Requirement**: REQ-001 -- Section 5 (Szenario 4: Photoperiod-Bluete), CLAUDE.md (Plant phase state machine)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Species "Cannabis sativa" as short-day plant, `critical_day_length_hours: 14.0`
- Location at latitude 50 N
- Current date: late August 2026

**Test Steps**:
1. Create cannabis species with lifecycle: `photoperiod_type: "short_day"`, `critical_day_length_hours: 14.0`
2. Calculate day length for August 25 at 50 N using PhotoperiodCalculator
3. Check if critical photoperiod is reached

**Expected Results**:
- Day length on August 25 at 50 N is approximately 14.0-14.5h
- Around late August / early September, day length drops below 14h
- `is_critical_photoperiod()` returns `True` when day length < 14.0h
- This triggers the Vegetative -> Flowering phase transition (cross-reference REQ-003)

**Postconditions**:
- Flowering trigger detected; system can initiate phase transition

**Tags**: [REQ-001, acceptance-scenario, cannabis, photoperiod, flowering-trigger, e2e]

See also: TC-REQ-001-064 for critical photoperiod unit tests

---

### TC-REQ-001-072: Crop rotation CRITICAL warning for same family (Szenario 5)

**Requirement**: REQ-001 -- Section 5 (Szenario 5: Fruchtfolge-Validierung), Section 2 (AQL query 2)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Species "Solanum lycopersicum" (tomato) linked to BotanicalFamily "Solanaceae"
- Species "Solanum tuberosum" (potato) linked to BotanicalFamily "Solanaceae"
- `shares_pest_risk` self-edge on Solanaceae with `risk_level: "high"`

**Test Steps**:
1. Validate crop rotation: previous = "Solanum lycopersicum", planned = "Solanum tuberosum"
2. System checks if both belong to the same family

**Expected Results**:
- Status: `"CRITICAL"`
- Message contains: "Gleiche Familie (Solanaceae) -- Mindestabstand 3 Jahre"
- System recommends alternative families (e.g., Fabaceae, Brassicaceae)
- Pest risk flagged as `"high"` (self-incompatibility)

**Postconditions**:
- Warning presented to user; planting not blocked but strongly discouraged

**Tags**: [REQ-001, acceptance-scenario, crop-rotation, same-family, critical-warning, e2e]

---

### TC-REQ-001-073: Nitrogen rotation recommendation (Szenario 6)

**Requirement**: REQ-001 -- Section 5 (Szenario 6: Stickstoff-Rotation-Empfehlung), Section 2 (rotation_after seed data)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- BotanicalFamily "Brassicaceae" (heavy nutrient demand)
- BotanicalFamily "Fabaceae" (nitrogen_fixing=true, light demand)
- `rotation_after` edge: Fabaceae -> Brassicaceae with `benefit_score: 0.90`, `benefit_reason: "nitrogen_fixation"`

**Test Steps**:
1. Query rotation successors after Brassicaceae
2. Identify Fabaceae as recommended successor

**Expected Results**:
- Fabaceae appears in successor list with `benefit_score: 0.90`
- `benefit_reason: "nitrogen_fixation"`
- 3-year plan suggestion: Brassicaceae -> Fabaceae -> Solanaceae

**Postconditions**:
- Recommendation data available for UI display

**Tags**: [REQ-001, acceptance-scenario, crop-rotation, nitrogen-fixation, recommendation, e2e]

---

### TC-REQ-001-074: Family-level pest risk WARNING for different families (Szenario 7)

**Requirement**: REQ-001 -- Section 5 (Szenario 7: Familien-Level Pest-Warnung), Section 2 (shares_pest_risk edge)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Species "Solanum lycopersicum" (Solanaceae)
- Species "Cucumis sativus" (Cucurbitaceae)
- `shares_pest_risk` edge between Solanaceae and Cucurbitaceae: `shared_pests: ["Blattlaeuse", "Weisse Fliege"]`, `risk_level: "medium"`

**Test Steps**:
1. Validate rotation: previous = tomato (Solanaceae), planned = cucumber (Cucurbitaceae)
2. System detects different families but shared pest risk

**Expected Results**:
- Status: `"WARNING"` (not CRITICAL because different families)
- Message: "Gemeinsames Schaedlingsrisiko: Blattlaeuse, Weisse Fliege (medium)"
- Recommendation: "Schaedlingsmonitoring verstaerken oder Lamiaceae als Zwischenkultur"

**Postconditions**:
- Warning data available; planting allowed but with pest monitoring advisory

**Tags**: [REQ-001, acceptance-scenario, crop-rotation, pest-risk, warning, e2e]

---

### TC-REQ-001-075: Family-level companion planting fallback (Szenario 8)

**Requirement**: REQ-001 -- Section 5 (Szenario 8: Familien-Level Mischkultur-Fallback), Section 2 (AQL query 3)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Species "Capsicum annuum" (pepper, Solanaceae) with NO species-level `compatible_with` edge to "Phaseolus vulgaris" (bush bean, Fabaceae)
- `family_compatible_with` edge between Solanaceae and Fabaceae: `compatibility_score: 0.85`, `benefit_type: "nitrogen_fixation"`

**Test Steps**:
1. Query companion planting recommendations for Capsicum annuum
2. System finds no species-level matches
3. System falls back to family-level: checks `family_compatible_with` between Solanaceae and Fabaceae
4. System discovers Fabaceae species (including Phaseolus vulgaris) via family traversal

**Expected Results**:
- `match_level: "family"` (not "species")
- Recommended species includes Phaseolus vulgaris
- Score = 0.85 * 0.8 = 0.68 (20% family-level discount applied)
- `benefit_type: "nitrogen_fixation"` included in recommendation

**Postconditions**:
- Family-level fallback recommendations displayed

**Tags**: [REQ-001, acceptance-scenario, companion-planting, family-fallback, score-discount, e2e]

---

## 12. Seed Data Verification

### TC-REQ-001-076: Verify 9 seed botanical families with complete attributes

**Requirement**: REQ-001 -- Section 2 (Seed-Daten: BotanicalFamily), Section 5 (DoD: all 9 seed families with extended attributes)
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- System initialized with seed data

**Test Steps**:
1. Send `GET /api/v1/botanical-families?offset=0&limit=50`
2. For each of the 9 expected families (Solanaceae, Brassicaceae, Fabaceae, Cucurbitaceae, Apiaceae, Asteraceae, Poaceae, Lamiaceae, Cannabaceae), verify:
   a. `common_name_de` is non-empty
   b. `common_name_en` is non-empty
   c. `order` is set and ends with "-ales"
   d. `typical_nutrient_demand` matches seed data
   e. `nitrogen_fixing` matches (true only for Fabaceae)
   f. `typical_root_depth` matches
   g. `frost_tolerance` matches
   h. `pollination_type` is non-empty list

**Expected Results**:
- At least 9 families returned
- Fabaceae: `nitrogen_fixing: true`, `typical_nutrient_demand: "light"`
- Cannabaceae: `frost_tolerance: "sensitive"`, `typical_root_depth: "deep"`, `typical_nutrient_demand: "heavy"`, `pollination_type: ["wind"]`
- Poaceae: `frost_tolerance: "very_hardy"`, `typical_root_depth: "shallow"`
- All families have valid `order` ending in "-ales"

**Postconditions**:
- Seed data integrity confirmed

**Tags**: [REQ-001, seed-data, botanical-family, acceptance-criteria, e2e]

---

### TC-REQ-001-077: Verify seed rotation_after edges (minimum 16)

**Requirement**: REQ-001 -- Section 2 (Seed-Daten: rotation_after), Section 5 (DoD: min 16 directed rotation_after edges)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed data loaded including rotation_after edges

**Test Steps**:
1. For each of the 9 botanical families, query `GET /api/v1/crop-rotation/families/{key}/successors`
2. Count total distinct rotation_after edges across all families
3. Verify specific edges from seed data:
   a. Fabaceae -> Solanaceae (benefit_score: 0.95, reason: nitrogen_fixation)
   b. Brassicaceae -> Fabaceae (benefit_score: 0.85, reason: soil_structure)
   c. Apiaceae -> Brassicaceae (benefit_score: 0.80, reason: pest_break)

**Expected Results**:
- Total rotation_after edges >= 16
- Specific edges match seed data benefit_scores and reasons
- Edge directionality is correct: `(successor) -[:rotation_after]-> (predecessor)`

**Postconditions**:
- Crop rotation graph verified

**Tags**: [REQ-001, seed-data, rotation-after, graph-edges, acceptance-criteria, e2e]

---

### TC-REQ-001-078: Verify seed shares_pest_risk edges (minimum 7 bidirectional)

**Requirement**: REQ-001 -- Section 2 (Seed-Daten: shares_pest_risk), Section 5 (DoD: min 7 bidirectional edges)
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed data loaded including shares_pest_risk edges

**Test Steps**:
1. Query pest risk edges for Solanaceae -- expect self-edge (Solanaceae<->Solanaceae, risk_level: "high") and cross-edge to Cucurbitaceae (risk_level: "medium")
2. Query pest risk edges for Cannabaceae -- expect self-edge (risk_level: "high") and cross-edge to Cucurbitaceae (risk_level: "medium")
3. Verify bidirectionality: if Solanaceae shares pest risk with Cucurbitaceae, Cucurbitaceae also shows Solanaceae
4. Count total distinct bidirectional pairs >= 7

**Expected Results**:
- Solanaceae self-edge: `shared_pests: ["Kartoffelkaefer", "Blattlaeuse"]`, `shared_diseases: ["Kraut- und Braunfaeule", "Fusarium"]`, `risk_level: "high"`
- Solanaceae<->Cucurbitaceae: `shared_pests: ["Blattlaeuse", "Weisse Fliege"]`, `risk_level: "medium"`
- Cannabaceae self-edge: `shared_pests: ["Spinnmilben", "Thripse", "Trauermuecken"]`, `shared_diseases: ["Botrytis", "Mehltau", "Fusarium"]`, `risk_level: "high"`
- At least 7 bidirectional pairs total

**Postconditions**:
- Pest risk graph verified

**Tags**: [REQ-001, seed-data, pest-risk, graph-edges, acceptance-criteria, e2e]

---

## Coverage Summary

| Spec Section | Subsection | Test Cases | Coverage |
|---|---|---|---|
| 2. ArangoDB-Modellierung | Species Node | TC-001 to TC-011 | Full (CRUD + all field validations) |
| 2. ArangoDB-Modellierung | BotanicalFamily Node | TC-012 to TC-023 | Full (CRUD + naming + nitrogen + pH) |
| 2. ArangoDB-Modellierung | Cultivar Node | TC-024 to TC-029 | Full (CRUD + trait validation + boundaries) |
| 2. ArangoDB-Modellierung | LifecycleConfig Node | TC-030 to TC-035 | Full (annual/biennial/perennial + validation) |
| 2. ArangoDB-Modellierung | GrowthPhase Node | TC-036 to TC-039 | Full (CRUD + sequence + boundaries) |
| 2. ArangoDB-Modellierung | compatible_with / incompatible_with Edges | TC-040 to TC-042 | Full |
| 2. ArangoDB-Modellierung | rotation_after Edge | TC-043 to TC-044 | Full |
| 3. Technische Umsetzung | DormancyTrigger | TC-045 to TC-052 | Full (all trigger types + boundaries + validation) |
| 3. Technische Umsetzung | VernalizationTracker | TC-053 to TC-058 | Full (completion + warm days + boundaries) |
| 3. Technische Umsetzung | PhotoperiodCalculator | TC-059 to TC-067 | Full (day length + critical photoperiod + edge cases) |
| 5. Akzeptanzkriterien | Szenario 1 (Annual) | TC-068 | Full |
| 5. Akzeptanzkriterien | Szenario 2 (Biennial) | TC-069 | Full |
| 5. Akzeptanzkriterien | Szenario 3 (Perennial Dormancy) | TC-070 | Full |
| 5. Akzeptanzkriterien | Szenario 4 (Photoperiod) | TC-071 | Full |
| 5. Akzeptanzkriterien | Szenario 5 (Same-Family Rotation) | TC-072 | Full |
| 5. Akzeptanzkriterien | Szenario 6 (Nitrogen Rotation) | TC-073 | Full |
| 5. Akzeptanzkriterien | Szenario 7 (Pest Risk Warning) | TC-074 | Full |
| 5. Akzeptanzkriterien | Szenario 8 (Family Fallback) | TC-075 | Full |
| 2. Seed-Daten | BotanicalFamily Seed Data | TC-076 | Full |
| 2. Seed-Daten | rotation_after Seed Edges | TC-077 | Full |
| 2. Seed-Daten | shares_pest_risk Seed Edges | TC-078 | Full |

### MUSS-Requirements Coverage Check

| MUSS Requirement | Positive TC | Negative TC |
|---|---|---|
| Species binomial nomenclature | TC-001 | TC-002 |
| BotanicalFamily name ends "-aceae" | TC-012 | TC-013 |
| Order name ends "-ales" (if set) | TC-012 | TC-014 |
| nitrogen_fixing + heavy = invalid | TC-017 | TC-016 |
| Biennial requires vernalization | TC-032 | TC-031 |
| PhRange min <= max | TC-019 | TC-018 |
| Hardiness zone format | TC-001 | TC-003 |
| Allelopathy score range [-1, 1] | TC-004 | TC-004 (steps 4-5) |
| Days to maturity range [1, 365] | TC-026 | TC-026 (steps 3-4) |
| Valid GrowthHabit enum | TC-001 | TC-009 |
| Valid RootType enum | TC-001 | TC-010 |
| Valid PlantTrait enum | TC-024 | TC-025 |
| 3+ phases per lifecycle | TC-036 | -- |
| Family-level fallback score discount 20% | TC-075 | -- |
